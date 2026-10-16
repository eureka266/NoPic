"""Maintenance-only: compose fixed 3:4 backgrounds from existing base and native layers.
Never run as part of an ordinary quote/summary render; existing files are preserved.
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SIZE = (1200, 1600)
SCALE = 2


def layer_shape(canvas, box, color):
    layer = Image.new('RGBA', canvas.size)
    ImageDraw.Draw(layer).ellipse(tuple(round(v * SCALE) for v in box), fill=color)
    canvas.alpha_composite(layer)


def glow(canvas, center, radius, color):
    layer = Image.new('RGBA', canvas.size)
    x, y = center
    ImageDraw.Draw(layer).ellipse(tuple(round(v * SCALE) for v in
                                    (x-radius, y-radius, x+radius, y+radius)), fill=color)
    layer = layer.filter(ImageFilter.GaussianBlur(radius * SCALE * .6))
    canvas.alpha_composite(layer)


def build(style):
    with Image.open(ROOT / 'assets/backgrounds/soft-satin.png') as base:
        canvas = ImageOps.fit(base.convert('RGBA'), tuple(v*SCALE for v in SIZE),
                              Image.Resampling.LANCZOS)
    # Separate calm scrim layer; the source image is never modified or overwritten.
    canvas.alpha_composite(Image.new('RGBA', canvas.size, (5, 6, 9, 155)))
    if style == 'speaker-blue-orbit':
        glow(canvas, (1130, 1160), 330, (36, 139, 204, 48))
        layer_shape(canvas, (770, 780, 1630, 1850), (15, 64, 96, 255))
        layer_shape(canvas, (825, 825, 1635, 1855), (20, 82, 121, 255))
        layer_shape(canvas, (905, 915, 1620, 1845), (25, 105, 155, 255))
        draw = ImageDraw.Draw(canvas)
        for inset in range(0, 58, 14):
            box = tuple(round(v*SCALE) for v in (685-inset, 690-inset, 1620+inset, 1830+inset))
            draw.arc(box, 176, 254, fill=(25, 68, 94, 255), width=2*SCALE)
        draw.arc(tuple(round(v*SCALE) for v in (778, 788, 1622, 1842)),
                 242, 254, fill=(255, 122, 26, 210), width=3*SCALE)
    elif style == 'speaker-orange-horizon':
        glow(canvas, (1090, 1530), 230, (255, 122, 26, 46))
        glow(canvas, (60, 1450), 130, (36, 139, 204, 24))
        layer_shape(canvas, (785, 890, 1665, 1840), (140, 64, 21, 255))
        layer_shape(canvas, (793, 880, 1635, 1815), (12, 35, 53, 255))
        layer_shape(canvas, (925, 1040, 1710, 1830), (17, 51, 76, 255))
        draw = ImageDraw.Draw(canvas)
        draw.arc(tuple(round(v*SCALE) for v in (785, 890, 1665, 1840)),
                 108, 181, fill=(255, 122, 26, 220), width=3*SCALE)
        for inset in (30, 60):
            draw.arc(tuple(round(v*SCALE) for v in (785-inset, 890-inset, 1665+inset, 1840+inset)),
                     110, 175, fill=(57, 37, 29, 255), width=SCALE)
    elif style == 'speaker-quiet-contours':
        glow(canvas, (1110, 1120), 280, (36, 139, 204, 28))
        draw = ImageDraw.Draw(canvas)
        for inset in range(0, 180, 18):
            box = tuple(round(v*SCALE) for v in (960-inset, 730-inset*.25,
                                                 1485+inset, 1630+inset*.25))
            draw.rounded_rectangle(box, radius=215*SCALE, outline=(17, 40, 55, 255), width=SCALE)
        draw.arc(tuple(round(v*SCALE) for v in (1000, 1070, 1400, 1690)),
                 72, 111, fill=(181, 84, 24, 255), width=2*SCALE)
    else:
        raise ValueError('Unknown background style')
    return canvas.convert('RGB').resize(SIZE, Image.Resampling.LANCZOS)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=ROOT/'assets/backgrounds')
    args = p.parse_args()
    styles = ('speaker-blue-orbit', 'speaker-orange-horizon', 'speaker-quiet-contours')
    targets = [args.output / (name+'.png') for name in styles]
    if any(path.exists() for path in targets):
        raise ValueError('Existing presets are preserved; choose a new --output directory')
    args.output.mkdir(parents=True, exist_ok=True)
    for style, target in zip(styles, targets):
        build(style).save(target)
        print(target)


if __name__ == '__main__':
    main()
