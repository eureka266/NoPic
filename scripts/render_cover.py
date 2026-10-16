"""Deterministic layer compositor. Python 3, Pillow, fontTools required."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageOps
from fontTools.ttLib import TTFont
from template_parameters import content_value, image_box, load_template, resolve_template, text_box
from project_assets import canvas_size, save_project

ROOT = Path(__file__).resolve().parents[1]
SIZE = (1600, 900)
TEXT_KEYS = {'title', 'subtitle', 'eyebrow', 'footer'}
ASSET_KEYS = {'image', 'logo', 'partner_logo', 'separator'}
PALETTES = {
    'dark': {'title': '#F6F7FA', 'body': '#B9BDC5', 'accent': '#FF7A1A'},
    'light': {'title': '#122337', 'body': '#556476', 'accent': '#B84D00'},
}
DEFAULT_FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_CANDIDATES = [
    '/System/Library/Fonts/PingFang.ttc',
    '/System/Library/Fonts/Supplemental/Arial.ttf',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
    DEFAULT_FONT,
    'C:/Windows/Fonts/msyh.ttc',
    'C:/Windows/Fonts/arial.ttf',
]



def read_bytes(source, base):
    if str(source).startswith('https://'):
        request = urllib.request.Request(str(source), headers={'User-Agent': 'BlockSecCover/1.0'})
        with urllib.request.urlopen(request, timeout=20) as response:
            if not response.url.startswith('https://'):
                raise ValueError('Asset redirected outside HTTPS')
            data = response.read(20 * 1024 * 1024 + 1)
        if len(data) > 20 * 1024 * 1024:
            raise ValueError('Remote asset exceeds 20 MiB')
        return data
    if '://' in str(source):
        raise ValueError('Only local paths and HTTPS assets are supported')
    return (base / str(source)).resolve().read_bytes()


def materialize(data, project, kind, suffix):
    rel = Path('assets') / (kind + '-' + hashlib.sha256(data).hexdigest()[:16] + suffix)
    (project / rel).parent.mkdir(parents=True, exist_ok=True)
    (project / rel).write_bytes(data)
    return str(rel)


def wrap(text, font, width):
    lines = []
    for paragraph in text.split('\n'):
        remaining = paragraph
        if not remaining:
            lines.append('')
        while remaining:
            end = 0
            while end < len(remaining) and font.getlength(remaining[:end+1]) <= width:
                end += 1
            if end == 0:
                raise ValueError('A single glyph exceeds the text box width')
            # Prefer an existing space when wrapping words; CJK can break at glyphs.
            if end < len(remaining):
                space = remaining.rfind(' ', 0, end + 1)
                if space > 0:
                    end = space
            lines.append(remaining[:end])
            remaining = remaining[end:]
            if remaining.startswith(' '):
                remaining = remaining[1:]
    return lines


def draw_text(canvas, value, box, font_path, color, align='left'):
    if not value:
        return
    x, y, width, height, maximum, minimum = box
    for size in range(maximum, minimum - 1, -1):
        font = ImageFont.truetype(font_path, size)
        lines = wrap(value, font, width)
        line_height = sum(font.getmetrics()) + max(4, int(size * .14))
        if len(lines) * line_height <= height:
            d = ImageDraw.Draw(canvas)
            for i, line in enumerate(lines):
                if align == 'center':
                    d.text((x+width/2, y+i*line_height), line, font=font, fill=color, anchor='mt')
                elif align == 'right':
                    d.text((x+width, y+i*line_height), line, font=font, fill=color, anchor='rt')
                else:
                    d.text((x, y + i * line_height), line, font=font, fill=color, anchor='lt')
            return
    raise ValueError('Text overflow; shorten copy or explicitly change layout: ' + value[:60])


def place(canvas, im, box):
    x, y, width, height = box
    fitted = ImageOps.contain(im, (width, height), Image.Resampling.LANCZOS)
    canvas.alpha_composite(fitted, (x + (width-fitted.width)//2, y + (height-fitted.height)//2))


def place_layer(canvas, im, layer):
    if layer.get('trim_transparent'):
        bounds = im.getbbox()
        if bounds is None:
            raise ValueError('Image has no visible pixels: ' + layer['display_name'])
        im = im.crop(bounds)
    x, y, width, height = image_box(layer)
    fitted = ImageOps.contain(im, (width, height), Image.Resampling.LANCZOS)
    horizontal = {'left': 0, 'center': (width-fitted.width)//2, 'right': width-fitted.width}
    vertical = {'top': 0, 'center': (height-fitted.height)//2, 'bottom': height-fitted.height}
    canvas.alpha_composite(fitted, (x+horizontal[layer['horizontal_align']],
                                  y+vertical[layer['vertical_align']]))


def validate_glyphs(path, text):
    with TTFont(path, fontNumber=0) as font:
        cmap = font.getBestCmap() or {}
    missing = sorted({ch for ch in text if not ch.isspace() and ord(ch) not in cmap})
    if missing:
        raise ValueError('Font lacks characters: ' + ''.join(missing[:20]) + '; provide font/font_bold')


def choose_font(text):
    for candidate in FONT_CANDIDATES:
        if Path(candidate).is_file():
            try:
                validate_glyphs(candidate, text)
                return candidate
            except ValueError:
                continue
    raise ValueError('No system font covers this copy; provide local font/font_bold paths')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--content', type=Path)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--set', action='append', default=[])
    p.add_argument('--asset', action='append', default=[])
    p.add_argument('--background')
    p.add_argument('--theme', choices=['dark', 'light'])
    p.add_argument('--layer', action='append', default=[], help='LAYER_ID.PROPERTY=VALUE in design pixels')
    p.add_argument('--reset-layer', action='append', default=[], help='Restore one layer to its saved template defaults')
    args = p.parse_args()
    project = args.project.resolve()
    src = args.content.resolve() if args.content else project / 'content.json'
    c = json.loads(src.read_text(encoding='utf-8'))
    size = canvas_size(c, SIZE)
    base = src.parent
    template_defaults = c.get('template') or load_template(c['layout'])
    if template_defaults.get('default_background_id'):
        c.setdefault('background_id', template_defaults['default_background_id'])
    previous_theme = c.get('theme', template_defaults.get('default_theme', 'dark'))
    c['theme'] = args.theme or previous_theme
    if c['theme'] not in PALETTES:
        raise ValueError('theme must be dark or light')
    if args.theme and args.theme != previous_theme:
        # Switching themes selects the paired preset; custom background needs an explicit replacement.
        c.pop('background', None)
        print('Theme changed: selecting paired preset unless --background is provided', file=sys.stderr)
    palette = PALETTES[c['theme']]
    for assignment in args.set:
        key, val = assignment.split('=', 1)
        if key not in TEXT_KEYS:
            raise ValueError('--set only supports title/subtitle/eyebrow/footer')
        c[key] = val
    for assignment in args.asset:
        key, val = assignment.split('=', 1)
        if key not in ASSET_KEYS:
            raise ValueError('--asset only supports image/logo/partner_logo/separator')
        c[key] = str(Path(val).resolve()) if val and not val.startswith('https://') else (val or None)
    layers = resolve_template(c, c['layout'], size, args.layer, args.reset_layer)
    if 'main-title' in layers and (not isinstance(c.get('title'), str) or not c['title'].strip()):
        raise ValueError('title must be a non-empty string')
    for key in TEXT_KEYS:
        if not isinstance(c.get(key, ''), str):
            raise ValueError(key + ' must be a string')
    if 'main-title' not in layers and any(c.get(key) for key in TEXT_KEYS):
        raise ValueError('This logo-only template has no text slots; use partnership-centered for copy')
    for key in c['template'].get('required_assets', []):
        if not c.get(key):
            raise ValueError('This partnership template requires both official logos; missing: ' + key)
    for layer in layers.values():
        if layer['type'] == 'image' and layer.get('default_asset') and not c.get(layer['asset_field']):
            c[layer['asset_field']] = str(ROOT / 'assets' / layer['default_asset'])
    if c['layout'].startswith('partnership') and c.get('image'):
        raise ValueError('partnership has no image slot; choose hero/quote or remove image')
    if args.background:
        source = args.background if args.background.startswith('https://') else str(Path(args.background).resolve())
        c['background_metadata'] = {'style': None, 'source': source, **c.get('background_metadata', {})}
    elif c.get('background'):
        source = c['background']
    else:
        manifest = json.loads((ROOT / 'assets/backgrounds.json').read_text())
        preset = manifest['presets'][c['background_id']]
        if preset.get('theme') and preset['theme'] != c['theme']:
            raise ValueError('This background preset only supports ' + preset['theme'] + '; provide --background for another theme')
        if c['theme'] == 'light' and 'themes' in preset:
            preset = preset['themes']['light']
        source = str(ROOT / 'assets' / preset['file'])
        if preset.get('public_url'):
            try:
                source = read_bytes(preset['public_url'], ROOT)
                with Image.open(io.BytesIO(source)) as remote:
                    remote.verify()
            except Exception as exc:
                print('Preset URL unavailable; using bundled background: ' + str(exc), file=sys.stderr)
                source = str(ROOT / 'assets' / preset['file'])
    data = source if isinstance(source, bytes) else read_bytes(source, base)
    with Image.open(io.BytesIO(data)) as im:
        if abs(im.width / im.height / (size[0] / size[1]) - 1) > .02:
            raise ValueError('Background must match the project aspect ratio; no implicit cropping')
        canvas = im.convert('RGBA').resize(size, Image.Resampling.LANCZOS)
    clean_background = canvas.copy()
    canvas = Image.new('RGBA', size, (0, 0, 0, 0))
    # Save only after the entire design validates; previous config and PNG stay intact on failure.
    fonts = {}
    font_data = {}
    all_text = '\n'.join(c.get(k, '') for k in TEXT_KEYS)
    for key in ['font', 'font_bold']:
        source_font = c.get(key) or c.get('font') or choose_font(all_text)
        path = (base / source_font).resolve()
        validate_glyphs(path, all_text)
        fonts[key] = str(path)
        font_data[key] = (path.read_bytes(), path.suffix)
    images = {}
    image_data = {}
    for key in ASSET_KEYS:
        if c.get(key):
            raw = read_bytes(c[key], base)
            with Image.open(io.BytesIO(raw)) as original:
                original.load()
                images[key] = ImageOps.exif_transpose(original).convert('RGBA')
            buf = io.BytesIO()
            images[key].save(buf, format='PNG')
            image_data[key] = buf.getvalue()
    if 'image' in images:
        place_layer(canvas, images['image'], layers['main-image'])
    for layer_id in ('blocksec-logo', 'partner-logo'):
        layer = layers[layer_id]
        if layer['asset_field'] in images:
            place_layer(canvas, images[layer['asset_field']], layer)
    if 'logo' in images and 'partner_logo' in images:
        layer = layers['partnership-separator']
        if layer['type'] == 'image':
            place_layer(canvas, images[layer['asset_field']], layer)
        else:
            ImageDraw.Draw(canvas).text((layer['x'], layer['y']), layer['text'],
                font=ImageFont.truetype(fonts[layer['font_role']], layer['font_size']),
                fill=palette[layer['color_role']], anchor=layer['anchor'])
    for layer_id in ('main-title', 'supporting-text', 'category-label', 'footer-note'):
        layer = layers.get(layer_id)
        if layer is None:
            continue
        draw_text(canvas, content_value(c, layer), text_box(layer), fonts[layer['font_role']],
                  palette[layer['color_role']], layer['align'])
    project.mkdir(parents=True, exist_ok=True)
    c['background'] = materialize(data, project, 'background', '.png')
    for key, (raw, suffix) in font_data.items():
        c[key] = materialize(raw, project, key, suffix)
    for key, raw in image_data.items():
        c[key] = materialize(raw, project, key, '.png')
    c['schema_version'] = 2
    c['size'] = list(size)
    final = clean_background.copy()
    final.alpha_composite(canvas)
    save_project(project, c, clean_background, final, 'render_cover.py', 'cover.png', foreground=canvas)
    print(json.dumps({'png': str(project / 'cover.png'), 'config': str(project / 'content.json')}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Render failed: ' + str(exc), file=sys.stderr)
        sys.exit(1)
