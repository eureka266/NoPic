"""Rebuild the generic brand demo using existing backgrounds and text layers."""
import base64
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from render_cover import draw_text


def data_url(path):
    return 'data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode()


def main():
    example = ROOT / 'assets/examples/partnership-redotpay-minimal'
    source = json.loads((example / 'content.json').read_text())
    assets = HERE / 'demo-assets'
    assets.mkdir(exist_ok=True)
    font = example / source['font_bold']

    # This is explicitly a text placeholder, not an official or invented logo.
    layer = Image.new('RGBA', (1040, 180))
    draw_text(layer, 'YOUR BRAND', (0, 0, 1040, 180, 128, 64),
              str(font), '#122337', align='center')
    placeholder = assets / 'brand-placeholder.png'
    layer.save(placeholder)

    backgrounds = {
        'soft': ROOT / 'assets/backgrounds/partnership-soft-grid-light.png',
        'orange': ROOT / 'assets/backgrounds/partnership-orange-grid-light.png',
        'radial': ROOT / 'assets/backgrounds/radial-grid-symmetric-light.png',
    }
    with tempfile.TemporaryDirectory(prefix='nopic-preview-') as temp:
        temp = Path(temp)
        content = {
            'layout': 'partnership-minimal', 'theme': 'light',
            'background': str(backgrounds['soft']),
            'logo': str(placeholder),
            'partner_logo': str(example / source['partner_logo']),
            'font': str(example / source['font']),
            'font_bold': str(font),
            'title': '', 'subtitle': '', 'eyebrow': '', 'footer': '',
        }
        config = temp / 'input.json'
        config.write_text(json.dumps(content, ensure_ascii=False))
        project = temp / 'project'
        subprocess.run([sys.executable, str(ROOT / 'scripts/render_cover.py'),
                        '--content', str(config), '--project', str(project)],
                       check=True, capture_output=True, text=True)
        cover = assets / 'cover.png'
        cover.write_bytes((project / 'cover.png').read_bytes())

    demo = {
        'logo': data_url(placeholder),
        'partner': data_url(example / source['partner_logo']),
        'cover': data_url(cover),
        'backgrounds': {key: data_url(path) for key, path in backgrounds.items()},
    }
    payload = json.dumps(demo, ensure_ascii=False)
    (HERE / 'demo-assets.json').write_text(payload + '\n')
    index_path = HERE / 'index.html'
    index = re.sub(r'(<script id="demo-data" type="application/json">).*?(</script>)',
                   lambda match: match[1] + payload + match[2],
                   index_path.read_text(), flags=re.S)
    index_path.write_text(index)
    preview = index.replace('<link rel="stylesheet" href="style.css">',
                            '<style>\n' + (HERE / 'style.css').read_text() + '\n</style>')
    preview = preview.replace('<script src="app.js"></script>',
                              '<script>\n' + (HERE / 'app.js').read_text() + '\n</script>')
    (HERE / 'preview.html').write_text(preview)
    print('Updated generic brand assets, index.html and standalone preview.html')


if __name__ == '__main__':
    main()
