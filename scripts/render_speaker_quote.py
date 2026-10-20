"""Compose fixed-background 3:4 speaker quote/summary cards; validate real PNG alpha.
Background removal is performed by the session's native image editor, not this script.
Requires Python 3, Pillow and fontTools, as does render_cover.py.
"""
import argparse
import io
import json
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
from template_parameters import content_value, resolve_template, text_box
from render_cover import choose_font, materialize, place, place_layer, read_bytes, resolve_palette, validate_glyphs
from project_assets import canvas_size, catalog_asset, save_project
from organization_assets import asset_path, read_catalog

def choose_speaker_font(text):
    try:
        return choose_font(text)
    except ValueError:
        for candidate in ('/System/Library/Fonts/Hiragino Sans GB.ttc',
                          '/System/Library/Fonts/STHeiti Medium.ttc'):
            if Path(candidate).is_file():
                try:
                    validate_glyphs(candidate, text)
                    return candidate
                except ValueError:
                    pass
        raise ValueError('No system font covers this copy; provide font/font_bold paths')


SIZE = (1200, 1600)
TEXT_KEYS = {'quote', 'quote_body', 'speaker_name', 'speaker_role', 'organization',
             'event', 'event_date', 'title', 'footer'}
ASSET_KEYS = {'portrait', 'logo', 'photo_original'}
PALETTE = {'background': '#050609', 'text': '#F6F7FA', 'muted': '#B9BDC5',
           'blue': '#AAB4C2', 'orange': '#D2D6DC'}


def cutout(raw):
    with Image.open(io.BytesIO(raw)) as source:
        if source.format != 'PNG' or 'A' not in source.getbands():
            raise ValueError('portrait must be a PNG with a real alpha channel; remove background first')
        im = ImageOps.exif_transpose(source).convert('RGBA')
        alpha = im.getchannel('A')
        low, high = alpha.getextrema()
        if low != 0 or high < 128:
            raise ValueError('portrait needs fully transparent background and visible subject pixels')
        histogram = alpha.histogram()
        if histogram[0] / (im.width * im.height) < .005:
            raise ValueError('portrait has too little fully transparent background; inspect the cutout')
        return im


def png_bytes(image):
    out = io.BytesIO()
    image.save(out, format='PNG')
    return out.getvalue()


def bounded_wrap(text, font, width, max_lines):
    """Find wraps with bounded prefix searches; stop once the text box cannot fit."""
    lines = []
    for paragraph in text.split('\n'):
        remaining = paragraph
        if not remaining:
            lines.append('')
        while remaining:
            if len(lines) >= max_lines:
                return None
            high = 1
            while high < len(remaining) and font.getlength(remaining[:high]) <= width:
                high = min(high*2, len(remaining))
            low = 0
            while low < high:
                mid = (low+high+1)//2
                if font.getlength(remaining[:mid]) <= width:
                    low = mid
                else:
                    high = mid-1
            end = low
            if end == 0:
                raise ValueError('A single glyph exceeds the text box width')
            if end < len(remaining):
                space = remaining.rfind(' ', 0, end+1)
                if space > 0:
                    end = space
            lines.append(remaining[:end])
            remaining = remaining[end:]
            if remaining.startswith(' '):
                remaining = remaining[1:]
        if len(lines) > max_lines:
            return None
    return lines


def highlighted_text(canvas, value, box, path, palette, highlights, align='left'):
    """Draw exact copy in independently colored runs, preserving wraps and punctuation."""
    if not value:
        return
    x, y, width, height, maximum, minimum = box
    mask = [False] * len(value)
    for phrase in highlights:
        start = 0
        while True:
            start = value.find(phrase, start)
            if start < 0:
                break
            mask[start:start+len(phrase)] = [True] * len(phrase)
            start += len(phrase)
    for size in range(maximum, minimum-1, -1):
        font = ImageFont.truetype(path, size)
        line_height = sum(font.getmetrics()) + max(4, round(size*.14))
        lines = bounded_wrap(value, font, width, height//line_height)
        if lines is not None:
            break
    else:
        raise ValueError('Text overflow; shorten approved copy or change layout: '+value[:60])
    draw = ImageDraw.Draw(canvas)
    cursor = 0
    for row, line in enumerate(lines):
        start = value.find(line, cursor) if line else cursor
        if start < 0:
            raise ValueError('Cannot locate wrapped text in original copy')
        line_x = x
        if align == 'center':
            line_x += (width-font.getlength(line))/2
        elif align == 'right':
            line_x += width-font.getlength(line)
        index = 0
        while index < len(line):
            end = index+1
            emphasized = mask[start+index]
            while end < len(line) and mask[start+end] == emphasized:
                end += 1
            color = palette['orange'] if emphasized else palette['text']
            draw.text((line_x+font.getlength(line[:index]), y+row*line_height),
                      line[index:end], font=font, fill=color, anchor='lt')
            index = end
        cursor = start+len(line)


def draw_text(canvas, value, box, path, color):
    highlighted_text(canvas, value, box, path, {'text': color, 'orange': color}, [])


def background(config, base, palette, size=SIZE):
    source = config.get('background')
    if not source:
        manifest = read_catalog('backgrounds', config, base)
        defaults = manifest['portrait_presets']
        default_key = 'default_summary' if config.get('layout') == 'seminar-summary' else 'default'
        preset_id = config.get('background_id') or defaults.get(default_key, defaults.get('default'))
        preset = defaults['presets'].get(preset_id)
        if not preset:
            raise ValueError('Unknown 3:4 background_id: '+str(preset_id))
        config['background_id'] = preset_id
        source = str(catalog_asset(preset['file'], 'backgrounds', config, base))
    raw = read_bytes(source, base)
    with Image.open(io.BytesIO(raw)) as im:
        image = ImageOps.exif_transpose(im).convert('RGBA')
        fit = config.get('background_fit', 'contain')
        if fit == 'cover':
            canvas = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
        elif fit == 'contain':
            if abs((image.width/image.height)/(size[0]/size[1])-1) > .02:
                raise ValueError('Background must be 3:4; use background_fit=cover only for approved cropping')
            canvas = Image.new('RGBA', size, palette['background'])
            place(canvas, image, (0, 0, *size))
        else:
            raise ValueError('background_fit must be contain or cover')
    return canvas, raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--content', type=Path)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--set', action='append', default=[])
    parser.add_argument('--asset', action='append', default=[])
    parser.add_argument('--background')
    parser.add_argument('--background-id', help='Explicitly switch to another organization 3:4 preset')
    parser.add_argument('--draft', action='store_true', help='Allow missing logo, with explicit draft label')
    parser.add_argument('--cutout-only', action='store_true')
    parser.add_argument('--layer', action='append', default=[], help='LAYER_ID.PROPERTY=VALUE in design pixels')
    parser.add_argument('--reset-layer', action='append', default=[], help='Restore one layer to its saved template defaults')
    parser.add_argument('--portrait', type=Path, help='Already edited transparent PNG, for --cutout-only')
    args = parser.parse_args()
    project = args.project.resolve()
    if args.cutout_only:
        if not args.portrait:
            raise ValueError('--cutout-only requires --portrait CUTOUT.png')
        image = cutout(args.portrait.resolve().read_bytes())
        raw = png_bytes(image)
        project.mkdir(parents=True, exist_ok=True)
        asset = materialize(raw, project, 'portrait', '.png')
        (project/'speaker-cutout.png').write_bytes(raw)
        (project/'cutout.json').write_text(json.dumps({'portrait': asset, 'size': image.size,
                                                     'alpha_verified': True}, indent=2)+'\n')
        print(json.dumps({'cutout': str(project/'speaker-cutout.png')}, ensure_ascii=False))
        return
    if args.portrait:
        raise ValueError('--portrait is for cutout-only; full cards use --asset portrait=PATH')
    src = args.content.resolve() if args.content else project/'content.json'
    config = json.loads(src.read_text(encoding='utf-8'))
    size = canvas_size(config, SIZE)
    base = src.parent
    layout = config.setdefault('layout', 'speaker-quote')
    if layout not in ('speaker-quote', 'seminar-summary'):
        raise ValueError('layout must be speaker-quote or seminar-summary')
    for assignment in args.set:
        key, value = assignment.split('=', 1)
        if key not in TEXT_KEYS:
            raise ValueError('Unsupported --set field: '+key)
        config[key] = value
    for assignment in args.asset:
        key, value = assignment.split('=', 1)
        if key not in ASSET_KEYS:
            raise ValueError('Unsupported --asset field: '+key)
        config[key] = str(Path(value).resolve()) if value and not value.startswith('https://') else value or None
    if args.background and args.background_id:
        raise ValueError('Choose --background or --background-id, not both')
    if args.background_id:
        config['background_id'] = args.background_id
        config.pop('background', None)
        config['background_fit'] = 'contain'
    if args.background:
        config['background'] = (args.background if args.background.startswith('https://')
                                else str(Path(args.background).resolve()))
        config['background_metadata'] = {'style': None, 'source': config['background'],
                                         **config.get('background_metadata', {})}
    for key in TEXT_KEYS:
        if not isinstance(config.get(key, ''), str):
            raise ValueError(key+' must be a string')
    if layout == 'speaker-quote':
        for key in ('quote', 'speaker_name'):
            if not config.get(key, '').strip():
                raise ValueError(key+' is required')
        if not config.get('portrait'):
            raise ValueError('speaker-quote requires a transparent portrait PNG')
    else:
        if not config.get('title', '').strip():
            raise ValueError('seminar-summary requires title')
        sections = config.get('sections', [])
        if not isinstance(sections, list) or not 1 <= len(sections) <= 4:
            raise ValueError('seminar-summary requires 1 to 4 sections')
        for section in sections:
            if not isinstance(section, dict) or not isinstance(section.get('body'), str) or not section['body'].strip():
                raise ValueError('Each summary section needs a non-empty body string')
            if not isinstance(section.get('heading', ''), str):
                raise ValueError('Section heading must be a string')
        if config.get('portrait'):
            raise ValueError('seminar-summary has no portrait slot; use speaker-quote for a guest portrait')
    layers = resolve_template(config, layout, size, args.layer, args.reset_layer, start=base)
    for layer in layers.values():
        if layer['type'] == 'image' and layer.get('default_asset') and not config.get(layer['asset_field']):
            config[layer['asset_field']] = str(asset_path(layer['default_asset'], config, base))
    if not config.get('logo') and not args.draft:
        raise ValueError('Provide an approved organization logo, or use --draft for a marked preview')
    palette = resolve_palette(config, PALETTE)
    if not config.get('background') and config['template'].get('default_background_id'):
        config.setdefault('background_id', config['template']['default_background_id'])
    config.setdefault('background_fit', 'contain')
    canvas, background_raw = background(config, base, palette, size)
    clean_background = canvas.copy()
    canvas = Image.new('RGBA', size, (0, 0, 0, 0))
    copy = '\n'.join(config.get(key, '') for key in sorted(TEXT_KEYS))
    if layout == 'seminar-summary':
        copy += '\n'+'\n'.join(s.get('heading', '')+'\n'+s['body'] for s in sections)
    fonts, font_raw = {}, {}
    for key in ('font', 'font_bold'):
        path = (base/(config.get(key) or config.get('font') or choose_speaker_font(copy+'“'))).resolve()
        validate_glyphs(path, copy+'“')
        fonts[key] = str(path)
        font_raw[key] = (path.read_bytes(), path.suffix)
    images, image_raw = {}, {}
    for key in ('portrait', 'logo'):
        if config.get(key):
            raw = read_bytes(config[key], base)
            if key == 'portrait':
                image = cutout(raw)
            else:
                with Image.open(io.BytesIO(raw)) as im:
                    image = ImageOps.exif_transpose(im).convert('RGBA')
                    if image.getchannel('A').getextrema()[0] != 0 or not image.getbbox():
                        raise ValueError('logo must have actual transparent background and visible artwork')
            images[key] = image
            image_raw[key] = png_bytes(image)
    original_raw = None
    if config.get('photo_original'):
        original_raw = read_bytes(config['photo_original'], base)
        with Image.open(io.BytesIO(original_raw)) as original:
            original.verify()
    highlights = config.get('highlights', [])
    if not isinstance(highlights, list) or any(not isinstance(p, str) or not p for p in highlights):
        raise ValueError('highlights must be a list of non-empty exact phrases')
    full_quote = config.get('quote', '')+'\n'+config.get('quote_body', '')
    stale = [phrase for phrase in highlights if phrase not in full_quote]
    if stale and not any(x.split('=', 1)[0] in ('quote', 'quote_body') for x in args.set):
        raise ValueError('Highlight phrase not present in copy: '+stale[0])
    config['highlights'] = [phrase for phrase in highlights if phrase not in stale]
    if stale:
        print('Removed obsolete highlights after copy edit: '+', '.join(stale), file=sys.stderr)
    def draw_layer_text(layer_id, values=config, emphasized=False):
        layer = layers[layer_id]
        color = palette[layer['color_role']]
        colors = {'text': color, 'orange': palette['orange'] if emphasized else color}
        highlighted_text(canvas, content_value(values, layer), text_box(layer),
                         fonts[layer['font_role']], colors,
                         config['highlights'] if emphasized else [], layer['align'])

    if 'logo' in images:
        place_layer(canvas, images['logo'], layers['brand-logo'])
    draw_layer_text('event-details')
    if layout == 'speaker-quote':
        layer = layers['quote-mark']
        ImageDraw.Draw(canvas).text((layer['x'], layer['y']), layer['text'],
            font=ImageFont.truetype(fonts[layer['font_role']], layer['font_size']),
            fill=palette[layer['color_role']], anchor=layer['anchor'])
        draw_layer_text('main-quote', emphasized=True)
        # Crop invisible margins only; keep all visible face, clothing and body pixels.
        place_layer(canvas, images['portrait'], layers['speaker-portrait'])
        draw_layer_text('supporting-quote', emphasized=True)
        draw_layer_text('speaker-name')
        draw_layer_text('speaker-attribution')
    else:
        draw_layer_text('main-title')
        for section in sections:
            prefix = section['id'] + '-'
            accent = layers[prefix + 'accent']
            ImageDraw.Draw(canvas).line((accent['x'], accent['y'], accent['x']+accent['width'], accent['y']),
                fill=palette[accent['color_role']], width=accent['line_width'])
            draw_layer_text(prefix + 'heading', section)
            draw_layer_text(prefix + 'body', section)
        draw_layer_text('footer-note')
    if args.draft:
        draw = ImageDraw.Draw(canvas)
        sx, sy = size[0]/SIZE[0], size[1]/SIZE[1]
        draw.rectangle((round(655*sx), round(192*sy), round(1116*sx), round(246*sy)), fill='#050609')
        draw.text((round(670*sx), round(205*sy)), 'DRAFT / REVIEW REQUIRED',
                  font=ImageFont.truetype(fonts['font'], max(1, round(23*min(sx, sy)))),
                  fill=palette['orange'], anchor='lt')
    # Complete validation before writing the project, so failed renders preserve the previous output.
    project.mkdir(parents=True, exist_ok=True)
    config['background'] = materialize(background_raw, project, 'background', '.png')
    for key, (raw, suffix) in font_raw.items():
        config[key] = materialize(raw, project, key, suffix)
    for key, raw in image_raw.items():
        config[key] = materialize(raw, project, key, '.png')
    if original_raw:
        # Keep the original bytes and source extension for non-destructive reuse.
        suffix = Path(config['photo_original']).suffix or '.image'
        config['photo_original'] = materialize(original_raw, project, 'photo-original', suffix)
    config.update({'schema_version': 2, 'layout': layout, 'size': list(size), 'draft': args.draft})
    if 'portrait' in image_raw:
        (project/'speaker-cutout.png').write_bytes(image_raw['portrait'])
    filename = 'speaker-quote.png' if layout == 'speaker-quote' else 'seminar-summary.png'
    final = clean_background.copy()
    final.alpha_composite(canvas)
    save_project(project, config, clean_background, final, 'render_speaker_quote.py', filename, foreground=canvas, start=base)
    result = {'png': str(project/filename), 'config': str(project/'content.json'), 'draft': args.draft}
    if 'portrait' in image_raw:
        result['cutout'] = str(project/'speaker-cutout.png')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Render failed: '+str(exc), file=sys.stderr)
        sys.exit(1)
