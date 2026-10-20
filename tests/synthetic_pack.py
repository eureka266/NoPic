"""Test-only synthetic resource packs; never artwork or production templates.

Every resource is authored here from solid swatches and minimal protocol structures.
Nothing is copied from an organization pack or from repository production assets.
"""
from contextlib import contextmanager
import json
import os
from pathlib import Path
from unittest.mock import patch
from PIL import Image, ImageDraw


BACKGROUND_ID = 'test-neutral'
ALTERNATE_BACKGROUND_ID = 'test-warm'


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def text(field, x, y, width, height, maximum=48, minimum=18, role='title'):
    return dict(type='text', display_name='Test-only text', content_field=field,
                x=x, y=y, width=width, height=height, font_size_max=maximum,
                font_size_min=minimum, align='left', font_role='font', color_role=role)


def image(field, x, y, width, height):
    return dict(type='image', display_name='Test-only image', asset_field=field,
                x=x, y=y, width=width, height=height,
                horizontal_align='center', vertical_align='center', trim_transparent=True)


def template(layout):
    """Minimal engineering geometry, deliberately not a production layout."""
    portrait = layout in ('speaker-quote', 'seminar-summary')
    result = dict(schema_version=1, id=layout+'-test', version=1,
                  display_name='TEST ONLY: '+layout, legacy_layout=layout,
                  canvas=dict(width=1200 if portrait else 1600,
                              height=1600 if portrait else 900, unit='px'),
                  layers={})
    layers = result['layers']
    layers['brand-logo'] = image('logo', 60, 30, 220, 90)
    if not portrait:
        layers['partner-logo'] = image('partner_logo', 920, 400, 400, 100)
        layers['partnership-separator'] = image('separator', 780, 390, 40, 120)
        layers['partnership-separator']['default_asset'] = 'assets/marks/test-separator.png'
        if layout != 'partnership-minimal':
            layers['main-title'] = text('title', 80, 220, 835, 230, maximum=64)
            layers['supporting-text'] = text('subtitle', 80, 500, 800, 120, role='body')
            layers['main-image'] = image('image', 1000, 200, 550, 590)
        else:
            layers['brand-logo'] = image('logo', 80, 400, 600, 100)
            result.update(default_theme='light', default_background_id=BACKGROUND_ID,
                          required_assets=['logo', 'partner_logo'])
        return result
    layers['event-details'] = text('event', 80, 140, 1000, 80, role='muted')
    if layout == 'speaker-quote':
        layers['quote-mark'] = dict(type='glyph', display_name='Test-only glyph', x=80, y=300,
                                    font_size=60, text='“', anchor='lt', font_role='font', color_role='orange')
        layers['main-quote'] = text('quote', 80, 400, 900, 240, role='text')
        layers['supporting-quote'] = text('quote_body', 80, 650, 900, 150, role='text')
        layers['speaker-portrait'] = image('portrait', 700, 850, 400, 700)
        layers['speaker-name'] = text('speaker_name', 80, 900, 500, 100, role='text')
        layers['speaker-attribution'] = text(['speaker_title', 'speaker_company'], 80, 1020, 500, 180, role='muted')
    else:
        layers['main-title'] = text('title', 80, 270, 1000, 160, role='text')
        layers['footer-note'] = text('footer', 80, 1500, 1000, 60, maximum=24, role='muted')
        heading = text('heading', 84, 0, 1000, 60, maximum=32, role='text')
        heading.update(y_offset=25)
        heading.pop('y')
        body = text('body', 84, 0, 1000, 100, maximum=30, role='text')
        body.update(y_offset=100, height_inset=115)
        body.pop('y')
        body.pop('height')
        accent = dict(type='line', display_name='Test-only accent {number}', x=84,
                      y_offset=8, width=100, line_width=3, color_role='orange')
        result['section_pattern'] = dict(min_count=1, max_count=4, top=470, total_height=980,
                                         layers={'heading': heading, 'body': body, 'accent': accent})
    return result


def make_pack(root, *, catalogs=None, backgrounds=True):
    """Generate a fully disposable virtual brand from test-only protocol examples."""
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root/'TEST-ONLY.txt').write_text('Engineering fixture only. Not a production brand pack.\n')
    for name, size, color in [('test-neutral', (1600, 900), '#101923'),
                              ('test-alternate', (1600, 900), '#253B52'),
                              ('test-warm', (1600, 900), '#F0B060'),
                              ('test-portrait', (1200, 1600), '#101923')]:
        path = root/'assets/swatches'/(name+'.png')
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new('RGB', size, color).save(path)
    mark = root/'assets/marks/test-separator.png'
    mark.parent.mkdir(parents=True, exist_ok=True)
    Image.new('RGBA', (40, 120), '#122337').save(mark)
    logo = Image.new('RGBA', (240, 100), (0, 0, 0, 0))
    ImageDraw.Draw(logo).rectangle((20, 20, 220, 80), fill='#2080C0')
    logo.save(root/'assets/marks/test-logo.png')
    entries = []
    for layout in ('hero', 'quote', 'partnership', 'partnership-centered',
                   'partnership-minimal', 'speaker-quote', 'seminar-summary'):
        value = template(layout)
        write_json(root/'templates'/(layout+'.json'), value)
        entries.append(dict(id=value['id'], legacy_layout=layout, file=layout+'.json'))
    write_json(root/'templates/index.json', dict(schema_version=1, templates=entries))
    bg = {'presets': {}, 'portrait_presets': {'default': 'test-portrait', 'presets': {}}}
    if backgrounds:
        bg['presets'] = {
            BACKGROUND_ID: dict(file='assets/swatches/test-neutral.png', theme='light'),
            ALTERNATE_BACKGROUND_ID: dict(file='assets/swatches/test-warm.png', theme='light')}
        bg['portrait_presets']['presets'] = {'test-portrait': dict(file='assets/swatches/test-portrait.png')}
    write_json(root/'catalogs/backgrounds.json', bg)
    presets = {name: dict(size=size) for name, size in (
        ('x', [1600, 900]), ('linkedin-horizontal', [1600, 900]), ('wechat-square', [1200, 1200]))}
    write_json(root/'catalogs/platforms.json', dict(schema_version=1, presets=presets))
    logo_entry = dict(id='test-logo', brand='Test-only virtual brand',
                      file='assets/marks/test-logo.png', render_file='assets/marks/test-logo.png')
    write_json(root/'catalogs/logos.json', dict(logos=[logo_entry], brand_defaults={}))
    write_json(root/'catalogs/media.json', dict(assets=[]))
    catalog_map = dict(backgrounds='catalogs/backgrounds.json', templates='templates/index.json',
                       platform_presets='catalogs/platforms.json', logos='catalogs/logos.json',
                       media_kit='catalogs/media.json')
    if catalogs is not None:
        catalog_map = {key: catalog_map[key] for key in catalogs}
    manifest = dict(schema_version=1, id='test-only-pack', version='1.0',
                    display_name='TEST ONLY: Virtual brand', catalogs=catalog_map,
                    backgrounds=[dict(id=BACKGROUND_ID, file='assets/swatches/test-neutral.png')] if backgrounds else [],
                    logos=[logo_entry], files=['TEST-ONLY.txt', 'assets/marks/test-separator.png',
                                             'assets/swatches/test-alternate.png', 'assets/swatches/test-warm.png',
                                             'assets/swatches/test-portrait.png'])
    write_json(root/'manifest.json', manifest)
    return root


def activate_pack(case, root):
    pack = make_pack(Path(root)/'test-only-pack')
    case.enterContext(patch.dict(os.environ, {'NOPIC_BRAND_PACK': str(pack)}))
    return pack


def disconnected_env():
    """An invalid explicit pack also prevents discovery of a real ancestor pack."""
    return {**os.environ, 'NOPIC_BRAND_PACK': str(Path('/nonexistent/nopic-test-only-disconnected-pack'))}


@contextmanager
def disconnected_pack(pack):
    """Physically unplug the external pack while exercising a saved project."""
    pack = Path(pack)
    offline = pack.with_name(pack.name+'-offline')
    pack.rename(offline)
    try:
        with patch.dict(os.environ, {'NOPIC_BRAND_PACK': str(pack)}):
            yield
    finally:
        offline.rename(pack)
