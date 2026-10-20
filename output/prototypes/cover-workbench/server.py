"""Local workbench server. No AI execution, hook installation, Git commit, or remote writes."""
import argparse
import base64
from copy import deepcopy
import hashlib
import json
import mimetypes
import subprocess
import sys
import threading
import uuid
import zipfile
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse
from zoneinfo import ZoneInfo

from background_workflow import prepare_handoff, read_result

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORK = HERE / 'workspace'
WORK.mkdir(exist_ok=True)
STATE = WORK / 'workbench-state.json'
LOCK = threading.Lock()
DEFAULT_BG = {
    'soft': ROOT / 'assets/backgrounds/partnership-soft-grid-light.png',
    'orange': ROOT / 'assets/backgrounds/partnership-orange-grid-light.png',
    'radial': ROOT / 'assets/backgrounds/radial-grid-symmetric-light.png',
}
BG = dict(DEFAULT_BG)
BRAND_PLACEHOLDER = HERE / 'demo-assets/brand-placeholder.png'
PARTNER_PLACEHOLDER = HERE / 'demo-assets/partner-placeholder.png'
BRAND_PACK_ROOT = None
BRAND_PACK_MANIFEST = None
PREVIEW_REVISION = 'nopic-generic-partner-v2'
KB = Path.home() / 'blocksec-product-knowledge'
CATEGORIES = {'brand': 'materials/brand', 'layout-reference': 'materials/references/layout',
              'background-reference': 'materials/references/background',
              'background': 'backgrounds', 'static': 'materials/existing-static',
              'other': 'materials/other'}
DEFAULT = {'mode': 'cover', 'background': 'soft', 'template': 'minimal',
           'title': 'Partnership Announcement', 'subtitle': 'Approved copy goes here.',
           'format': 'png', 'duration': 5, 'uploads': [], 'revision': 0,
           'finalized': False, 'preview': None, 'render_key': None,
           'session_handoff': None, 'logo_id': None, 'partner_logo_id': None}


def now():
    return datetime.now(ZoneInfo('Asia/Hong_Kong')).isoformat(timespec='seconds')


def configure_paths(project_root=None):
    global WORK, STATE
    if project_root:
        WORK = Path(project_root).expanduser().resolve() / '.nopic/workspace'
    else:
        WORK = HERE / 'workspace'
    WORK.mkdir(parents=True, exist_ok=True)
    STATE = WORK / 'workbench-state.json'


def pack_file(relative):
    if BRAND_PACK_ROOT is None:
        raise ValueError('No brand pack is active')
    path = (BRAND_PACK_ROOT / relative).resolve()
    if not path.is_relative_to(BRAND_PACK_ROOT.resolve()) or not path.is_file():
        raise ValueError(f'Brand pack asset is missing: {relative}')
    return path


def configure_brand_pack(pack_root=None):
    global BG, BRAND_PLACEHOLDER, PARTNER_PLACEHOLDER
    global BRAND_PACK_ROOT, BRAND_PACK_MANIFEST
    BG = dict(DEFAULT_BG)
    BRAND_PLACEHOLDER = HERE / 'demo-assets/brand-placeholder.png'
    PARTNER_PLACEHOLDER = HERE / 'demo-assets/partner-placeholder.png'
    BRAND_PACK_ROOT = None
    BRAND_PACK_MANIFEST = None
    DEFAULT['background'] = 'soft'
    DEFAULT['logo_id'] = None
    DEFAULT['partner_logo_id'] = None
    if not pack_root:
        return
    root = Path(pack_root).expanduser().resolve()
    manifest_file = root / 'manifest.json'
    if not root.is_dir() or not manifest_file.is_file():
        raise ValueError(f'Brand pack not found: {root}')
    manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
    if manifest.get('schema_version') != 1 or not manifest.get('id'):
        raise ValueError('Unsupported brand pack manifest')
    backgrounds = {}
    logos = {}
    for entry in manifest.get('backgrounds', []):
        if entry.get('reference_only') or entry.get('usable_as_background') is False:
            continue
        asset_id = entry.get('id')
        if not asset_id:
            continue
        backgrounds[asset_id] = (root / entry['file']).resolve()
        if not backgrounds[asset_id].is_file() or not backgrounds[asset_id].is_relative_to(root):
            raise ValueError(f'Brand pack background is missing: {entry.get("file")}')
    for entry in manifest.get('logos', []):
        if entry.get('reference_only') or entry.get('usable_as_standalone_logo') is False:
            continue
        asset_id = entry.get('id')
        if not asset_id:
            continue
        render_file = entry.get('render_file') or entry.get('file')
        path = (root / render_file).resolve()
        if not path.is_file() or not path.is_relative_to(root):
            raise ValueError(f'Brand pack logo is missing: {render_file}')
        logos[asset_id] = {'entry': entry, 'path': path}
    if not backgrounds:
        raise ValueError('Brand pack must contain at least one usable background')
    defaults = manifest.get('defaults', {})
    default_background = defaults.get('background') if defaults.get('background') in backgrounds else next(iter(backgrounds))
    default_logo = defaults.get('logo') if defaults.get('logo') in logos else next(iter(logos), None)
    partner_logo = defaults.get('partner_logo') if defaults.get('partner_logo') in logos else None
    BG = backgrounds
    BRAND_PACK_ROOT = root
    BRAND_PACK_MANIFEST = {'manifest': manifest, 'backgrounds': backgrounds, 'logos': logos,
                           'default_background': default_background, 'default_logo': default_logo,
                           'partner_logo': partner_logo}
    DEFAULT['background'] = default_background
    DEFAULT['logo_id'] = default_logo
    DEFAULT['partner_logo_id'] = partner_logo
    BRAND_PLACEHOLDER = logos[default_logo]['path'] if default_logo else BRAND_PLACEHOLDER
    PARTNER_PLACEHOLDER = logos[partner_logo]['path'] if partner_logo else PARTNER_PLACEHOLDER


def brand_pack_view():
    if not BRAND_PACK_MANIFEST:
        return None
    manifest = BRAND_PACK_MANIFEST['manifest']
    backgrounds = []
    for entry in manifest.get('backgrounds', []):
        asset_id = entry.get('id')
        if asset_id not in BRAND_PACK_MANIFEST['backgrounds']:
            continue
        relative = BRAND_PACK_MANIFEST['backgrounds'][asset_id].relative_to(BRAND_PACK_ROOT)
        backgrounds.append({'id': asset_id, 'name': entry.get('display_name') or entry.get('label') or asset_id,
                            'theme': entry.get('theme'), 'reference_only': bool(entry.get('reference_only')),
                            'url': '/brand-pack/' + quote(relative.as_posix(), safe='/')})
    logos = []
    for entry in manifest.get('logos', []):
        asset_id = entry.get('id')
        if asset_id not in BRAND_PACK_MANIFEST['logos']:
            continue
        relative = BRAND_PACK_MANIFEST['logos'][asset_id]['path'].relative_to(BRAND_PACK_ROOT)
        logos.append({'id': asset_id, 'name': entry.get('display_name') or asset_id,
                      'brand': entry.get('brand'), 'url': '/brand-pack/' + quote(relative.as_posix(), safe='/')})
    return {'id': manifest['id'], 'version': manifest.get('version'),
            'display_name': manifest.get('display_name') or manifest['id'],
            'root': str(BRAND_PACK_ROOT), 'default_background': BRAND_PACK_MANIFEST['default_background'],
            'default_logo': BRAND_PACK_MANIFEST['default_logo'],
            'partner_logo': BRAND_PACK_MANIFEST['partner_logo'],
            'backgrounds': backgrounds, 'logos': logos}


def read_state():
    state = {**deepcopy(DEFAULT), **(json.loads(STATE.read_text()) if STATE.exists() else {})}
    if BRAND_PACK_MANIFEST:
        if state['background'] not in BG:
            state['background'] = DEFAULT['background']
        logo_ids = set(BRAND_PACK_MANIFEST['logos'])
        if state.get('logo_id') not in logo_ids:
            state['logo_id'] = DEFAULT['logo_id']
        if state.get('partner_logo_id') not in logo_ids:
            state['partner_logo_id'] = DEFAULT['partner_logo_id']
    return state


def resolve_logo(asset_id, fallback):
    if BRAND_PACK_MANIFEST and asset_id in BRAND_PACK_MANIFEST['logos']:
        return BRAND_PACK_MANIFEST['logos'][asset_id]['path']
    return fallback


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temp.replace(path)


def inside(relative):
    path = (WORK / relative).resolve()
    if not path.is_relative_to(WORK.resolve()):
        raise ValueError('Invalid workspace path')
    return path


def pack_inside(relative):
    if BRAND_PACK_ROOT is None:
        raise ValueError('No brand pack is active')
    path = (BRAND_PACK_ROOT / relative).resolve()
    if not path.is_relative_to(BRAND_PACK_ROOT.resolve()):
        raise ValueError('Invalid brand pack path')
    return path


def state_view():
    state = read_state()
    return {**state, 'workspace': str(WORK), 'knowledge_root': str(KB),
            'knowledge_available': (KB / 'assets/video').is_dir(),
            'timezone': 'Asia/Hong_Kong', 'brand_pack': brand_pack_view()}


def update_draft(data):
    state = read_state()
    for key in ('mode', 'background', 'template', 'title', 'subtitle', 'format', 'duration',
                'logo_id', 'partner_logo_id'):
        if key in data:
            state[key] = data[key]
    if state['mode'] not in ('cover', 'background', 'motion'):
        raise ValueError('Unknown workflow')
    if state['background'] not in BG or state['template'] not in ('minimal', 'centered'):
        raise ValueError('Unknown preset')
    if BRAND_PACK_MANIFEST:
        logo_ids = set(BRAND_PACK_MANIFEST['logos'])
        if state.get('logo_id') not in logo_ids or (state.get('partner_logo_id') and state['partner_logo_id'] not in logo_ids):
            raise ValueError('Unknown brand pack logo')
    if state['format'] not in ('png', 'webp'):
        raise ValueError('PNG or WebP only in this prototype')
    if any(not isinstance(state[k], str) or len(state[k]) > 2000 for k in ('title', 'subtitle')):
        raise ValueError('Invalid copy')
    if type(state['duration']) not in (int, float) or not 1 <= state['duration'] <= 30:
        raise ValueError('Duration must be between 1 and 30 seconds')
    state['revision'] += 1
    state['updated_at'] = now()
    write_json(STATE, state)
    return state


def session_handoff_markdown(handoff):
    draft = handoff['draft']
    lines = [
        '# NoPic 会话任务',
        '',
        f"- 任务 ID：`{handoff['id']}`",
        f"- 创建时间：`{handoff['created_at']}`（Asia/Hong_Kong）",
        '- 来源：本地工作台上传界面',
        '',
        '## 制作说明',
        '',
        handoff['instruction'] or '请根据已上传素材和当前草稿继续制作封面图。',
        '',
        '## 当前草稿',
        '',
        f"- 流程：`{draft['mode']}`",
        f"- 模板：`{draft['template']}`",
        f"- 底图：`{draft['background']}`",
        f"- 标题：{draft['title'] or '（空）'}",
        f"- 副标题：{draft['subtitle'] or '（空）'}",
        f"- 输出：`{draft['format']}`",
        '',
        '## 已上传素材',
        '',
    ]
    if handoff['uploads']:
        for asset in handoff['uploads']:
            reference = '（仅参考）' if asset.get('reference_only') else ''
            lines.append(
                f"- `{asset['category']}`{reference}：`{asset['relative_path']}` "
                f"（原名：`{asset['original_name']}`）"
            )
    else:
        lines.append('- 暂无上传素材。')
    lines.extend([
        '',
        '## 执行约束',
        '',
        '- 保留用户原始素材，不覆盖同名文件。',
        '- 参考图只用于分析视觉方向，除非明确指定，不自动作为发布素材。',
        '- 默认复用已有底图；只有用户明确要求时才生成新背景。',
        '- 当前工作台通过文件桥接连接会话，不能直接向 Codex 注入消息。',
    ])
    return '\n'.join(lines) + '\n'


def render(data):
    state = update_draft(data)
    if state['mode'] == 'motion':
        return state_view()
    key_data = {k: state[k] for k in ('mode', 'background', 'template', 'title', 'subtitle',
                                      'logo_id', 'partner_logo_id')}
    key_data['preview_revision'] = PREVIEW_REVISION
    if BRAND_PACK_MANIFEST:
        key_data['brand_pack'] = (BRAND_PACK_MANIFEST['manifest']['id'],
                                  BRAND_PACK_MANIFEST['manifest'].get('version'))
    key = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()[:16]
    project = WORK / 'projects/partnership-demo/versions' / key
    if project.exists() and not (project / 'project.json').exists():
        project = project.with_name(key + '-retry-' + uuid.uuid4().hex[:6])
    if not (project / 'project.json').exists():
        if state['mode'] == 'background':
            project.parent.mkdir(parents=True, exist_ok=True)
            command = [sys.executable, str(ROOT / 'scripts/cover_project.py'), 'background',
                       '--project', str(project), '--background', str(BG[state['background']]), '--confirm-clean']
        else:
            project.mkdir(parents=True, exist_ok=True)
            content = {'layout': 'partnership-minimal' if state['template'] == 'minimal' else 'partnership-centered',
                       'theme': 'light', 'background': str(BG[state['background']]),
                       'background_id': state['background'],
                       'logo': str(resolve_logo(state.get('logo_id'), BRAND_PLACEHOLDER)),
                       'partner_logo': str(resolve_logo(state.get('partner_logo_id'), PARTNER_PLACEHOLDER)),
                       'title': state['title'] if state['template'] == 'centered' else '',
                       'subtitle': state['subtitle'] if state['template'] == 'centered' else '',
                       'eyebrow': '', 'footer': ''}
            if any('\u3400' <= char <= '\u9fff' for char in content['title'] + content['subtitle']):
                chinese_font = Path('/System/Library/Fonts/Hiragino Sans GB.ttc')
                if chinese_font.is_file():
                    content['font'] = content['font_bold'] = str(chinese_font)
            input_file = project / 'input.json'
            write_json(input_file, content)
            command = [sys.executable, str(ROOT / 'scripts/render_cover.py'), '--content',
                       str(input_file), '--project', str(project)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise ValueError(result.stderr.strip()[-1200:] or 'Render failed')
    manifest = json.loads((project / 'project.json').read_text())
    if state['mode'] == 'background':
        image = project / manifest['background']['master']
    else:
        image = project / 'cover.png'
    # Existing compositor output is the authority for preview and export.
    from PIL import Image
    for fmt in ('png', 'webp'):
        with Image.open(image) as im:
            target = project / ('download.' + fmt)
            if not target.exists():
                im.save(target, format=fmt.upper(), **({'quality': 95} if fmt == 'webp' else {}))
    if state.get('render_key') != key:
        state['finalized'] = False
        state.pop('submission', None)
    state.update(render_key=key, preview='/workspace/' + str(image.relative_to(WORK)),
                 current_project=str(project.relative_to(WORK)))
    write_json(STATE, state)
    return state_view()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(fmt % args, flush=True)

    def allowed(self):
        origin = self.headers.get('Origin')
        expected = f'http://{self.headers.get("Host", "")}'
        host = self.headers.get('Host', '').split(':')[0]
        return host in ('localhost', '127.0.0.1') and (not origin or origin == expected)

    def send_data(self, body, mime='application/json', status=200, download=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        if download:
            self.send_header('Content-Disposition', 'attachment; filename="' + download + '"')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.allowed():
            return self.send_data({'error': 'Local same-origin requests only'}, status=403)
        path = unquote(urlparse(self.path).path)
        try:
            if path == '/api/background-result':
                state = read_state()
                return self.send_data({'task_id': (state.get('background_handoff') or {}).get('id'),
                                       'result': read_result(WORK, state.get('background_handoff'))})
            if path == '/api/state':
                return self.send_data(state_view())
            if path == '/api/download':
                state = read_state()
                if not state.get('current_project') or state['mode'] == 'motion':
                    raise ValueError('Render a static preview first')
                fmt = state['format']
                file = inside(state['current_project']) / ('download.' + fmt)
                return self.send_data(file.read_bytes(), 'image/' + fmt,
                                      download='nopic-partnership.' + fmt)
            if path.startswith('/brand-pack/'):
                file = pack_inside(path.removeprefix('/brand-pack/'))
            elif path.startswith('/workspace/'):
                file = inside(path.removeprefix('/workspace/'))
            elif path in ('/', '/index.html', '/app.js', '/style.css', '/demo-assets.json'):
                file = HERE / ('index.html' if path == '/' else path[1:])
            else:
                return self.send_data({'error': 'Not found'}, status=404)
            if not file.is_file():
                return self.send_data({'error': 'Not found'}, status=404)
            mime = mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
            return self.send_data(file.read_bytes(), mime,
                                  download=file.name if file.suffix.lower() in ('.svg', '.html') and path.startswith('/workspace/') else None)
        except (OSError, ValueError) as exc:
            self.send_data({'error': str(exc)}, status=400)

    def do_POST(self):
        if not self.allowed() or self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.send_data({'error': 'Local JSON requests only'}, status=403)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 28 * 1024 * 1024:
                raise ValueError('Upload limit: 20 MB per file')
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError('Expected a JSON object')
            with LOCK:
                path = urlparse(self.path).path
                if path == '/api/render':
                    return self.send_data(render(data))
                if path == '/api/save':
                    update_draft(data)
                    return self.send_data(state_view())
                if path == '/api/upload':
                    category = data['category']
                    if category not in CATEGORIES:
                        raise ValueError('Choose an upload category')
                    original_name = data['name']
                    name = Path(original_name.replace('\\', '/')).name
                    if name in ('', '.', '..') or any(ord(c) < 32 for c in name):
                        raise ValueError('Invalid file name')
                    raw = base64.b64decode(data['data'], validate=True)
                    if len(raw) > 20 * 1024 * 1024:
                        raise ValueError('Upload limit: 20 MB per file')
                    sha = hashlib.sha256(raw).hexdigest()
                    state = read_state()
                    date = now()[:10]
                    parts = CATEGORIES[category].split('/')
                    path = WORK / 'inbox' / parts[0] / (date + '-partnership-demo')
                    path = path.joinpath(*parts[1:]) / sha[:12] / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if not path.exists():
                        path.write_bytes(raw)
                    record = {'id': uuid.uuid4().hex[:12], 'name': name, 'original_name': original_name,
                              'category': category, 'relative_path': str(path.relative_to(WORK)),
                              'sha256': sha, 'bytes': len(raw), 'uploaded_at': now(),
                              'reference_only': category in ('layout-reference', 'background-reference'),
                              'source': 'panel-upload'}
                    duplicate = next((x for x in state['uploads'] if x['sha256'] == sha and x['category'] == category and x['name'] == name), None)
                    if duplicate:
                        record = duplicate
                    else:
                        state['uploads'].append(record)
                    state['revision'] += 1
                    write_json(STATE, state)
                    write_json(WORK / 'inbox/materials-index.json', state['uploads'])
                    return self.send_data({'asset': record, 'state': state_view()})
                if path == '/api/background-handoff':
                    state = read_state()
                    request, receipt = prepare_handoff(data, state, WORK, now())
                    state['background_request'] = request
                    state['background_handoff'] = receipt
                    state['session_handoff'] = receipt
                    state['revision'] += 1
                    write_json(STATE, state)
                    return self.send_data({'handoff': receipt, 'state': state_view()})
                if path == '/api/request':
                    kind = data.get('kind')
                    if kind not in ('background', 'motion'):
                        raise ValueError('Unknown request kind')
                    file = WORK / 'requests' / (now()[:10] + '-' + kind + '-' + uuid.uuid4().hex[:8] + '.json')
                    write_json(file, {'kind': kind, 'brief': str(data.get('brief', ''))[:6000],
                                      'created_at': now(), 'status': 'saved-not-executed', 'draft': read_state()})
                    return self.send_data({'path': str(file), 'executed': False})
                if path == '/api/session-handoff':
                    state = read_state()
                    instruction = str(data.get('instruction', '')).strip()
                    if len(instruction) > 6000:
                        raise ValueError('会话说明不能超过 6000 个字符')
                    handoff_id = now()[:10] + '-cover-' + uuid.uuid4().hex[:8]
                    handoff = {
                        'id': handoff_id,
                        'created_at': now(),
                        'status': 'ready-for-codex',
                        'source': 'cover-workbench',
                        'instruction': instruction,
                        'draft': {key: state[key] for key in (
                            'mode', 'background', 'template', 'title', 'subtitle', 'format', 'duration')},
                        'uploads': state.get('uploads', []),
                        'workspace': str(WORK),
                    }
                    folder = WORK / 'session-handoffs'
                    json_file = folder / (handoff_id + '.json')
                    markdown_file = folder / (handoff_id + '.md')
                    write_json(json_file, handoff)
                    markdown_file.parent.mkdir(parents=True, exist_ok=True)
                    markdown_file.write_text(session_handoff_markdown(handoff))
                    write_json(folder / 'latest.json', handoff)
                    (folder / 'latest.md').write_text(session_handoff_markdown(handoff))
                    state['session_handoff'] = {
                        'id': handoff_id,
                        'status': handoff['status'],
                        'created_at': handoff['created_at'],
                        'json_path': str(json_file.relative_to(WORK)),
                        'markdown_path': str(markdown_file.relative_to(WORK)),
                        'latest_json_path': str((folder / 'latest.json').relative_to(WORK)),
                        'latest_markdown_path': str((folder / 'latest.md').relative_to(WORK)),
                    }
                    write_json(STATE, state)
                    prompt = (
                        '请读取本地工作台生成的会话任务文件：' + str(json_file) + '\n'
                        '根据其中的制作说明、当前草稿和已上传素材继续制作封面图。'
                    )
                    return self.send_data({
                        'handoff': {**state['session_handoff'], 'json_file': str(json_file),
                                    'markdown_file': str(markdown_file),
                                    'latest_json_file': str(folder / 'latest.json'),
                                    'latest_markdown_file': str(folder / 'latest.md'),
                                    'prompt': prompt},
                        'state': state_view(),
                    })
                if path == '/api/finalize':
                    state = read_state()
                    if not state.get('current_project') or state['mode'] == 'motion':
                        raise ValueError('Create a static preview first')
                    project = inside(state['current_project'])
                    revision = state['render_key']
                    candidate = WORK / 'submissions' / revision
                    candidate.mkdir(parents=True, exist_ok=True)
                    package = candidate / 'partnership-demo.zip'
                    files = [p for p in project.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name != 'input.json']
                    with zipfile.ZipFile(package, 'w', zipfile.ZIP_DEFLATED) as z:
                        for file in files:
                            z.write(file, 'project/' + str(file.relative_to(project)))
                    manifest = {'revision': revision, 'finalized_at': now(),
                                'target': 'assets/video/' + now()[:10] + '-partnership-demo',
                                'files': [str(p.relative_to(project)) for p in files],
                                'package': str(package.relative_to(WORK)),
                                'reference_uploads_included': False, 'git_committed': False, 'pushed': False}
                    write_json(candidate / 'manifest.json', manifest)
                    state.update(finalized=True, submission=manifest)
                    state.pop('dismissed_revision', None)
                    write_json(STATE, state)
                    return self.send_data(state_view())
                if path == '/api/dismiss':
                    state = read_state()
                    state['dismissed_revision'] = state.get('render_key')
                    write_json(STATE, state)
                    return self.send_data(state_view())
                return self.send_data({'error': 'Not found'}, status=404)
        except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as exc:
            self.send_data({'error': str(exc)}, status=400)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the local NoPic workbench.')
    parser.add_argument('port', nargs='?', type=int, default=0)
    parser.add_argument('--project-root')
    parser.add_argument('--brand-pack')
    args = parser.parse_args()
    configure_paths(args.project_root)
    configure_brand_pack(args.brand_pack)
    httpd = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'http://127.0.0.1:{httpd.server_port}', flush=True)
    httpd.serve_forever()
