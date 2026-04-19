# region Steps to take:
    ## 1. Load in image (With Url)
    ## 2. Down size the image
    ## 3. Take luminance
    ## 4. Rectify the luminance of each pixel
    ## 5. Make a key of charecters
    ## 6. Map the key onto the image
    ## 7. Output the image.

    ## 8. Add border lines
#endregion

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from urllib.request import urlopen
from scipy.ndimage import convolve
import numpy as np
from typing import Literal
from os import path

# ─── Private Helpers ──────────────────────────────────────────────────────────

def __fetch_image(url: str):
    return urlopen(url)

def __load_image(img_path) -> Image.Image:
    return Image.open(img_path)

def __take_luminance(img: Image.Image) -> np.ndarray:
    grey = img.convert(mode="L")
    return np.array(grey, dtype=np.float32)  # shape: (H, W), values 0-255

def __rectify_luminance(luma: np.ndarray) -> np.ndarray:
    return np.clip(luma, 0, 255).astype(np.uint8)  # clamp to valid range

def __detect_edges_directional(luma: np.ndarray, threshold: float = 50):
    # Scharr kernels (more accurate than Sobel on diagonals)
    Kx = np.array([[-3,   0,  3],
                   [-10,  0, 10],
                   [-3,   0,  3]], dtype=np.float32)
    Ky = np.array([[-3, -10, -3],
                   [ 0,   0,  0],
                   [ 3,  10,  3]], dtype=np.float32)

    sx = convolve(luma.astype(np.float32), Kx)
    sy = convolve(luma.astype(np.float32), Ky)

    magnitude = np.hypot(sx, sy)
    magnitude = magnitude / magnitude.max() * 255

    # Angle in degrees, 0-180
    angle = np.degrees(np.arctan2(sy, sx)) % 180

    edge_mask = magnitude > threshold
    return edge_mask, angle

def __apply_edges_directional(chars: np.ndarray, edges: np.ndarray, angles: np.ndarray) -> np.ndarray:
    result = chars.copy()
    y_coords, x_coords = np.where(edges)  # only iterate edge pixels

    for y, x in zip(y_coords, x_coords):
        a = angles[y, x]
        if a < 22.5 or a >= 157.5:
            result[y, x] = '—'   # horizontal
        elif 22.5 <= a < 67.5:
            result[y, x] = '/'   # diagonal right
        elif 67.5 <= a < 112.5:
            result[y, x] = '|'   # vertical
        else:
            result[y, x] = '\\'  # diagonal left

    return result

def __map_to_chars(luma: np.ndarray, charset: tuple, invert: bool = False) -> np.ndarray:
    charset_array = np.array(list(charset))
    adjusted = (255 - luma) if invert else luma
    indices = (adjusted / 255 * (len(charset) - 1)).astype(np.int32)
    return charset_array[indices]

def __get_char_size(font_path: str, font_size: int) -> tuple:
    font = ImageFont.truetype(font_path, font_size)
    bbox = font.getbbox("A")
    char_w = bbox[2] - bbox[0]
    char_h = bbox[3] - bbox[1]
    return char_w, char_h

def __resize_by_scale(img: Image.Image, factor: float, char_w: int, char_h: int) -> Image.Image:
    w = int(img.size[0] * factor)
    h = int(img.size[1] * factor * (char_w / char_h))  # actual font ratio, not hardcoded 0.5
    return img.resize((w, h))

def __render_onto_image(image: Image.Image):
    image.show()

def __turn_to_image(chars: np.ndarray, original: Image.Image, font_size: int = 10, font_path: str = "C:/Windows/Fonts/cour.ttf", saturation: float = 2.0) -> Image.Image:
    font = ImageFont.truetype(font_path, font_size)

    char_w, char_h = __get_char_size(font_path, font_size)

    rows, cols = chars.shape
    canvas = Image.new("RGB", (cols * char_w, rows * char_h), color=(0, 0, 0))  # type: ignore
    draw = ImageDraw.Draw(canvas)

    # Boost saturation before sampling
    color_source = original.convert("RGB").resize((cols, rows))
    color_source = ImageEnhance.Color(color_source).enhance(saturation)
    color_array = np.array(color_source)

    for y in range(rows):
        for x in range(cols):
            char = chars[y, x]
            color = tuple(color_array[y, x])
            draw.text((x * char_w, y * char_h), char, fill=color, font=font)

    return canvas

# ─── Public API ───────────────────────────────────────────────────────────────

def Convert_to_ASCII(
    mode : Literal["URL", "File"],
    file : str,
    **kwargs
):
    """
    Keyword Arguments:
        dark_mode      (bool)  = True
        font_size      (int)   = 16
        scale_factor   (float) = 1/4
        edge_detection (bool)  = True
        edge_threshold (float) = 60
        font_path      (str)   = "C:/Windows/Fonts/cour.ttf"
        saturation     (float) = 2.5
    """

    dark_mode      = kwargs.get("dark_mode",      True)
    font_size      = kwargs.get("font_size",       16)
    scale_factor   = kwargs.get("scale_factor",    1/4)
    edge_detection = kwargs.get("edge_detection",  True)
    edge_threshold = kwargs.get("edge_threshold",  60)
    font_path      = kwargs.get("font_path",       "C:/Windows/Fonts/cour.ttf")
    saturation     = kwargs.get("saturation",      2.5)

    if mode != 'File' and mode != 'URL':
        quit("Error: Invalid Mode")

    if not file or not file.strip():
        quit("Error: No file path or URL provided.")

    charset = ('@', '#', 'B', 'S', '%', '?', '*', '+', ';', ':', ',', '.', ' ')

    char_w, char_h = __get_char_size(font_path, font_size)

    try:
        if mode == "URL":
            image = __load_image(__fetch_image(file))
        elif mode == "File":
            image = __load_image(path.normpath(file))
    except Exception as e:
        quit(f"Could not find the image: {e}")

    image = __resize_by_scale(image, scale_factor, char_w, char_h)
    luma  = __take_luminance(image)
    luma  = __rectify_luminance(luma)
    chars = __map_to_chars(luma, charset, invert=dark_mode)

    if edge_detection:
        edges, angles = __detect_edges_directional(luma, threshold=edge_threshold)
        chars = __apply_edges_directional(chars, edges, angles)

    pic = __turn_to_image(chars, image, font_size=font_size, font_path=font_path, saturation=saturation)

    __render_onto_image(pic)

# region MAIN
if __name__ == "__main__":
    pass
# endregion