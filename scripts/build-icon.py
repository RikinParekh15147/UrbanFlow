"""Rasterize the existing favicon's geometric mark for the Windows executable."""

from pathlib import Path

from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
scale = 32
image = Image.new("RGBA", (40 * scale, 40 * scale), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
green, ink = "#e1ed92", "#123d32"


def box(values):
    return tuple(round(value * scale) for value in values)


draw.rounded_rectangle(box((0, 0, 40, 40)), radius=10 * scale, fill=green)
width = round(2.2 * scale)
draw.line(box((13, 28, 26, 28)), fill=ink, width=width)
draw.arc(box((20, 16, 32, 28)), -90, 90, fill=ink, width=width)
draw.line(box((14, 16, 26, 16)), fill=ink, width=width)
draw.arc(box((9, 6, 19, 16)), 90, 270, fill=ink, width=width)
draw.line(box((14, 6, 25, 6)), fill=ink, width=width)
for x, y in ((12, 28), (27, 6)):
    draw.ellipse(box((x - 3, y - 3, x + 3, y + 3)), fill=green, outline=ink, width=width)
output = root / "apps/desktop/assets"
output.mkdir(parents=True, exist_ok=True)
image.resize((256, 256), Image.Resampling.LANCZOS).save(
    output / "icon.ico",
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
