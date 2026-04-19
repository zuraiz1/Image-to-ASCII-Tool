# ASCII Image Generator

A Python tool that converts images (from a URL or local file) into coloured ASCII art using BT.601 luminance mapping, directional edge detection, and Pillow rendering.

---

## Example Output

```
@@@@####BBSS%%??**++;;::,,...   
@@##BBB%%??**++;;::,,....       
##BB%%??**++;;::,,...           
```
*(actual output rendered as a `.png` image with colour)*

---

## Features

- **BT.601 luma transform** — industry-standard greyscale conversion
- **Directional edge detection** — Scharr filter with angle bucketing gives `|`, `—`, `/`, `\` edge characters that follow the actual contour of shapes
- **Per-character colour sampling** — each character is drawn in the colour of its corresponding pixel from the original image
- **Saturation boost** — compensates for colour loss during downscaling
- **Font-aware aspect ratio correction** — resizes the image using the actual character cell dimensions of the chosen font so the output isn't squished
- **Dark/light mode toggle** — inverts luminance mapping to suit dark or light backgrounds
- **URL and file input** — load images directly from the web or from disk

---

## Installation

```bash
pip install pillow numpy scipy
```

---

## Usage

```python
from Image_to_ASCII import Convert_to_ASCII

# From a URL
Convert_to_ASCII("URL", "https://example.com/image.jpg")

# From a local file (raw string recommended for Windows paths)
Convert_to_ASCII("File", r"C:\Users\You\Pictures\photo.png")
```

### Keyword Arguments

All settings have sensible defaults and are passed as keyword arguments:

| Argument | Type | Default | Description |
|---|---|---|---|
| `DARK_MODE` | `bool` | `True` | Invert luminance for dark backgrounds |
| `FONT_SIZE` | `int` | `16` | Font size in points |
| `SCALE_FACTOR` | `float` | `0.25` | Downscale factor (lower = more detail, slower) |
| `EDGE_DETECTION` | `bool` | `True` | Enable directional edge detection |
| `EDGE_THRESHOLD` | `float` | `60` | Edge sensitivity — lower detects more edges |
| `FONT_PATH` | `str` | `C:/Windows/Fonts/cour.ttf` | Path to a monospace `.ttf` font |
| `SATURATION` | `float` | `2.5` | Colour saturation boost (1.0 = original) |

```python
Convert_to_ASCII(
    "URL", "https://example.com/image.jpg",
    DARK_MODE=False,
    FONT_SIZE=12,
    SCALE_FACTOR=1/6,
    EDGE_THRESHOLD=40,
    SATURATION=3.0
)
```

---

## How It Works

1. **Load** — image is fetched from a URL or local path
2. **Resize** — scaled down using `SCALE_FACTOR`, with height adjusted for the font's actual character cell ratio to prevent stretching
3. **Luminance** — converted to greyscale using the BT.601 luma formula: `Y = 0.299R + 0.587G + 0.114B`
4. **Rectify** — luminance values clamped to 0–255
5. **Character mapping** — each pixel's luminance maps to a character in the charset, dark to light: `@ # B S % ? * + ; : , . space`
6. **Edge detection** — Scharr convolution finds edge magnitude and angle; pixels above the threshold get a directional character (`|`, `—`, `/`, `\`) based on their gradient angle
7. **Render** — characters are drawn onto a canvas in the sampled colour of their original pixel, with saturation boosted beforehand

---

## Notes

- A **monospace font is required** — proportional fonts will misalign the character grid. Courier New (`cour.ttf`) is the default. DejaVu Sans Mono and Noto Mono also work well and support Unicode block characters.
- On **Linux/Mac** change `FONT_PATH` to something like `/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf`
- For **very large images** reduce `SCALE_FACTOR` — the render loop is per-character so larger grids take longer
- The output is saved as `output.png` in the working directory and opened automatically

---

## Dependencies

| Package | Purpose |
|---|---|
| `Pillow` | Image loading, drawing, font rendering |
| `NumPy` | Vectorised luminance and character mapping |
| `SciPy` | Scharr convolution for edge detection |
