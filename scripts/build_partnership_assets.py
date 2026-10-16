"""Build the native SVG/PNG partnership background and transparent cross assets.

Optional rebuild dependencies: Pillow and resvg-py. Bundled PNGs need neither resvg-py
nor this script at render time. Existing assets are preserved unless --force is used.
"""
import argparse
from pathlib import Path
import resvg_py
from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / 'assets'
BACKGROUND = '''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">
  <title>BlockSec partnership soft grid — light</title>
  <desc>White logo-safe center, quiet grid, blue lower-left and apricot upper-right edge washes. No text or logos.</desc>
  <defs>
    <pattern id="grid" width="180" height="180" patternUnits="userSpaceOnUse">
      <path d="M180 0H0V180" fill="none" stroke="#EDF0F3" stroke-width="1" opacity=".6"/>
    </pattern>
    <radialGradient id="blue" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(70 855) scale(570 600)">
      <stop stop-color="#8CCCEF" stop-opacity=".65"/>
      <stop offset=".45" stop-color="#ACDAF4" stop-opacity=".46"/>
      <stop offset=".76" stop-color="#DBEFFA" stop-opacity=".25"/>
      <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="orange" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(1440 15) scale(510 360)">
      <stop stop-color="#FFBE8B" stop-opacity=".63"/>
      <stop offset=".4" stop-color="#FFD6B6" stop-opacity=".48"/>
      <stop offset=".72" stop-color="#FFEADB" stop-opacity=".3"/>
      <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="right-blue" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(1680 300) scale(180 270)">
      <stop stop-color="#BDE3F7" stop-opacity=".38"/>
      <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <path fill="#FFFFFF" d="M0 0H1600V900H0Z"/>
  <path fill="url(#grid)" d="M0 0H1600V900H0Z"/>
  <path fill="url(#blue)" d="M-160 270C110 280-65 670 190 670C405 630 585 650 610 940L-160 1100Z"/>
  <path fill="url(#orange)" d="M960-100H1740V360C1510 330 1530 210 1300 240C1120 270 1005 230 1015 120Z"/>
  <path fill="url(#right-blue)" d="M1430 0H1600V690H1430Z"/>
</svg>
'''
COLORS = {'ink': '#122337', 'white': '#FFFFFF', 'orange': '#FF7A1A'}

PARTNERSHIP_ORANGE_GRID = '''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">
  <title>BlockSec partnership orange gradient grid — light</title>
  <desc>White logo-safe center, faint grid, BlockSec orange and blue edge gradients. No text or logos.</desc>
  <defs>
    <pattern id="grid" width="180" height="180" patternUnits="userSpaceOnUse">
      <path d="M180 0H0V180" fill="none" stroke="#ECEFF2" stroke-width="1" opacity=".7"/>
    </pattern>
    <radialGradient id="warm-lower-left" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(20 900) scale(600 510)">
      <stop stop-color="#FF9E56" stop-opacity=".64"/>
      <stop offset=".42" stop-color="#FFC188" stop-opacity=".48"/>
      <stop offset=".75" stop-color="#FFE3C9" stop-opacity=".27"/>
      <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="amber-upper-right" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(1560 0) scale(560 380)">
      <stop stop-color="#FFB24D" stop-opacity=".62"/>
      <stop offset=".42" stop-color="#FFD27C" stop-opacity=".48"/>
      <stop offset=".78" stop-color="#FFE9BA" stop-opacity=".25"/>
      <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="cool-blue-edge" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(-10 420) scale(150 300)">
      <stop stop-color="#80C9EB" stop-opacity=".42"/>
      <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="soft-coral" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(1600 900) scale(280 250)">
      <stop stop-color="#FFB078" stop-opacity=".28"/>
      <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <path fill="#FFFFFF" d="M0 0H1600V900H0Z"/>
  <path fill="url(#grid)" d="M0 0H1600V900H0Z"/>
  <path fill="url(#warm-lower-left)" d="M-140 360C90 350 20 680 280 690C470 700 520 770 590 950H-140Z"/>
  <path fill="url(#amber-upper-right)" d="M990-120H1720V350C1510 330 1500 245 1310 245C1130 245 1030 205 1040 85Z"/>
  <path fill="url(#cool-blue-edge)" d="M-40 100H190C115 245 120 380 50 500C12 560-20 620-40 700Z"/>
  <path fill="url(#soft-coral)" d="M1360 900H1660V660C1510 700 1515 815 1360 900Z"/>
</svg>
'''


def cross_svg(color):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 64 64">
  <title>Partnership multiplication cross</title>
  <path d="M8 8L56 56M56 8L8 56" fill="none" stroke="{color}" stroke-width="3.5" stroke-linecap="butt"/>
</svg>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true', help='Explicitly replace generated assets')
    args = parser.parse_args()
    sources = {ROOT/'backgrounds/partnership-soft-grid-light.svg': BACKGROUND,
               ROOT/'backgrounds/partnership-orange-grid-light.svg': PARTNERSHIP_ORANGE_GRID}
    sources.update({ROOT/f'marks/partnership-cross-{name}.svg': cross_svg(color)
                    for name, color in COLORS.items()})
    outputs = [path.with_suffix(ext) for path in sources for ext in ('.svg', '.png')]
    existing = [str(path) for path in outputs if path.exists()]
    if existing and not args.force:
        parser.error('Assets already exist; use --force only for an intentional rebuild: ' + ', '.join(existing))
    for path, svg in sources.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg, encoding='utf-8')
        path.with_suffix('.png').write_bytes(resvg_py.svg_to_bytes(svg_string=svg))
        if 'backgrounds' in path.parts:
            with Image.open(path.with_suffix('.png')) as image:
                image.convert('RGB').save(path.with_suffix('.png'))
        print(path)
        print(path.with_suffix('.png'))


if __name__ == '__main__':
    main()
