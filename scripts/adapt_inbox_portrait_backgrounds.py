"""Maintenance only: recompose supplied raster backgrounds into fixed 3:4 canvases.
Source layers keep their aspect ratios. No new geometric motifs or AI image edits.
The raw sources and all existing presets remain untouched.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageStat

ROOT = Path(__file__).resolve().parents[1]
SIZE = (1200, 1600)
RECIPES = [
    {'id': 'portrait-data-glow', 'label': '蓝橙点阵',
     'source': 'inbox/backgrounds/#U8d44#U6e90 7 1.png', 'cap_fraction': .52,
     'sample': (.38, .08, .62, .22), 'top_fade': 150, 'bottom_fade': 160},
    {'id': 'portrait-diagonal-light', 'label': '斜切光影',
     'source': 'inbox/backgrounds/#U8d44#U6e90 1 8.jpg', 'cap_fraction': .63,
     'sample': (.38, .30, .64, .48), 'top_fade': 140, 'bottom_fade': 150},
    {'id': 'portrait-gradient-spheres', 'label': '蓝橙渐变圆形',
     'source': 'inbox/backgrounds/exec-90481eac-175b-4110-954b-db1f3a033839.png', 'cap_fraction': .52,
     'sample': (.36, .33, .66, .58), 'top_fade': 100, 'bottom_fade': 100},
]


def fade_cap(image, edge, distance):
    alpha = Image.new('L', image.size, 255)
    draw = ImageDraw.Draw(alpha)
    for offset in range(distance):
        # Smooth transition to the independently extended empty background field.
        t = offset / max(1, distance-1)
        opacity = round(255*t*t*(3-2*t))
        row = image.height-1-offset if edge == 'bottom' else offset
        draw.line((0, row, image.width, row), fill=opacity)
    layer = image.convert('RGBA')
    layer.putalpha(alpha)
    return layer


def compose(recipe):
    with Image.open(ROOT/recipe['source']) as im:
        original = ImageOps.exif_transpose(im).convert('RGB')
        box = tuple(round(v*(original.width if i%2 == 0 else original.height))
                    for i, v in enumerate(recipe['sample']))
        calm = tuple(round(v) for v in ImageStat.Stat(original.crop(box)).mean)
        # Only proportional resizing of the supplied source: circles stay round,
        # diagonal panels and the source's real gradients retain their proportions.
        height = round(original.height*SIZE[0]/original.width)
        source = original.resize((SIZE[0], height), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', SIZE, calm+(255,))
    cap_height = round(height*recipe['cap_fraction'])
    top = fade_cap(source.crop((0, 0, SIZE[0], cap_height)), 'bottom', recipe['top_fade'])
    bottom = fade_cap(source.crop((0, height-cap_height, SIZE[0], height)), 'top', recipe['bottom_fade'])
    canvas.alpha_composite(top)
    canvas.alpha_composite(bottom, (0, SIZE[1]-cap_height))
    # Independent dark veil across content zones. The perimeter still shows
    # the original uploaded gradient/dot material; no source pixels are redrawn.
    mask = Image.new('L', SIZE)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((52, 44, 1134, 174), radius=36, fill=160)
    draw.rounded_rectangle((46, 264, 1118, 662), radius=60, fill=115)
    draw.rounded_rectangle((45, 690, 595, 1565), radius=45, fill=115)
    mask = mask.filter(ImageFilter.GaussianBlur(36))
    veil = Image.new('RGBA', SIZE, calm+(255,))
    veil.putalpha(mask)
    canvas.alpha_composite(veil)
    return canvas.convert('RGB')


def board(paths, output):
    font = '/System/Library/Fonts/Hiragino Sans GB.ttc'
    canvas = Image.new('RGB', (1680, 1010), '#EEF1F5')
    draw = ImageDraw.Draw(canvas)
    draw.text((60, 36), 'BlockSec · 3:4 长图底图 · 基于上传原图适配',
              font=ImageFont.truetype(font, 32), fill='#122337')
    for i, (recipe, path) in enumerate(zip(RECIPES, paths)):
        x = 60+i*540
        with Image.open(path) as image:
            canvas.paste(image.resize((480, 640), Image.Resampling.LANCZOS), (x, 116))
        draw.text((x, 784), chr(65+i)+'  '+recipe['label'],
                  font=ImageFont.truetype(font, 28), fill='#122337')
        draw.text((x, 832), '1200 × 1600 · 固定 PNG · 保留原图材质',
                  font=ImageFont.truetype(font, 19), fill='#556476')
    canvas.save(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'assets/backgrounds')
    parser.add_argument('--preview', type=Path, default=ROOT/'assets/references/portrait-background-options-v2.png')
    args = parser.parse_args()
    targets = [args.output/(recipe['id']+'.png') for recipe in RECIPES]
    if any(p.exists() for p in targets) or args.preview.exists():
        raise ValueError('Do not overwrite existing assets. Use a new --output and --preview.')
    args.output.mkdir(parents=True, exist_ok=True)
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for recipe, path in zip(RECIPES, targets):
        compose(recipe).save(path)
        records.append({**recipe, 'output': str(path),
                        'source_sha256': hashlib.sha256((ROOT/recipe['source']).read_bytes()).hexdigest()})
    board(targets, args.preview)
    print(json.dumps({'outputs': records, 'preview': str(args.preview)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
