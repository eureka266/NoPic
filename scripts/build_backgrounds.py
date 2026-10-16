"""Rebuild the bundled, textless geometric presets. Requires Pillow."""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT = Path(__file__).resolve().parents[1] / 'assets' / 'backgrounds'
GEOMETRIC_PRESETS = ('hex-outline', 'hex-glow', 'radial-grid-symmetric')


def hexagon(x, y, r):
    return [(x + r * math.cos(math.pi / 3 * i),
             y + r * math.sin(math.pi / 3 * i)) for i in range(6)]


def build(style, theme='dark'):
    if style not in GEOMETRIC_PRESETS:
        raise ValueError(f'Unsupported geometric preset: {style}')
    scale = 2
    light = theme == 'light'
    im = Image.new('RGB', (1600 * scale, 900 * scale), '#F6F8FB' if light else '#050609')
    d = ImageDraw.Draw(im)
    if style == 'radial-grid-symmetric':
        # Even peripheral density, without a dense spoke intersection beneath the title.
        cx, cy = (im.width-1)/2, (im.height-1)/2
        color = '#F0F4F8' if light else '#0E1822'
        for radius in range(180, 1160, 140):
            r = radius*scale
            d.ellipse((cx-r, cy-r, cx+r, cy+r), outline=color, width=scale)
        for degrees in range(0, 360, 15):
            angle = math.radians(degrees)
            d.line((cx+220*scale*math.cos(angle), cy+220*scale*math.sin(angle),
                    cx+1200*scale*math.cos(angle), cy+1200*scale*math.sin(angle)), fill=color, width=scale)
        for x, y in [(210, 160), (1390, 160), (210, 740), (1390, 740)]:
            r = 2*scale
            d.ellipse((x*scale-r,y*scale-r,x*scale+r,y*scale+r), fill=color)
        # Mirror code-native geometry to remove raster rounding asymmetry.
        left = im.crop((0,0,im.width//2,im.height))
        im.paste(left.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (im.width//2,0))
        top = im.crop((0,0,im.width,im.height//2))
        im.paste(top.transpose(Image.Transpose.FLIP_TOP_BOTTOM), (0,im.height//2))
    else:
        if style == 'hex-glow':
            layer = Image.new('RGB', im.size, '#F6F8FB' if light else '#000000')
            ld = ImageDraw.Draw(layer)
            ld.ellipse((-240*scale, 750*scale, 270*scale, 1170*scale), fill='#A9D9F2' if light else '#125D88')
            ld.ellipse((1440*scale, -260*scale, 1860*scale, 170*scale), fill='#FFD7B4' if light else '#8B3D0F')
            blurred = layer.filter(ImageFilter.GaussianBlur(100*scale))
            im = blurred if light else ImageChops.add(im, blurred)
            d = ImageDraw.Draw(im)
        for i, r in enumerate([155, 220, 285, 350]):
            points = hexagon(1380*scale, 490*scale, r*scale)
            colors = ['#ACCADD', '#C4D8E5', '#D7E4ED', '#E3ECF3'] if light else ['#28536E', '#203543', '#18252F', '#111B23']
            d.line(points + [points[0]], fill=colors[i], width=2*scale)
        d.line((1030*scale, 840*scale, 1300*scale, 840*scale), fill='#DA9360' if light else '#A55122', width=scale)
    return im.resize((1600, 900), Image.Resampling.LANCZOS)


if __name__ == '__main__':
    ROOT.mkdir(parents=True, exist_ok=True)
    for preset in GEOMETRIC_PRESETS:
        build(preset).save(ROOT / (preset + '.png'))
        build(preset, 'light').save(ROOT / (preset + '-light.png'))
