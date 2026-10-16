"""Local prototype. No AI execution, hook installation, Git commit, or remote writes."""
import base64
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
from urllib.parse import unquote, urlparse
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORK = HERE / 'workspace'
WORK.mkdir(exist_ok=True)
STATE = WORK / 'workbench-state.json'
LOCK = threading.Lock()
BG = {
    'soft': ROOT / 'assets/backgrounds/partnership-soft-grid-light.png',
    'orange': ROOT / 'assets/backgrounds/partnership-orange-grid-light.png',
    'radial': ROOT / 'assets/backgrounds/radial-grid-symmetric-light.png',
}
BRAND_PLACEHOLDER = HERE / 'demo-assets/brand-placeholder.png'
PARTNER_PLACEHOLDER = HERE / 'demo-assets/partner-placeholder.png'
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
           'session_handoff': None}


def now():
    return datetime.now(ZoneInfo('Asia/Hong_Kong')).isoformat(timespec='seconds')


def read_state():
    return {**DEFAULT, **(json.loads(STATE.read_text()) if STATE.exists() else {})}


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


def state_view():
    state = read_state()
    return {**state, 'workspace': str(WORK), 'knowledge_root': str(KB),
            'knowledge_available': (KB / 'assets/video').is_dir(),
            'timezone': 'Asia/Hong_Kong'}


def update_draft(data):
    state = read_state()
    for key in ('mode', 'background', 'template', 'title', 'subtitle', 'format', 'duration'):
        if key in data:
            state[key] = data[key]
    if state['mode'] not in ('cover', 'background', 'motion'):
        raise ValueError('Unknown workflow')
    if state['background'] not in BG or state['template'] not in ('minimal', 'centered'):
        raise ValueError('Unknown preset')
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
    key_data = {k: state[k] for k in ('mode', 'background', 'template', 'title', 'subtitle')}
    key_data['preview_revision'] = PREVIEW_REVISION
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
                       'background_id': 'partnership-soft-grid',
                       'logo': str(BRAND_PLACEHOLDER),
                       'partner_logo': str(PARTNER_PLACEHOLDER),
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
            if path.startswith('/workspace/'):
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
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    httpd = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print(f'http://127.0.0.1:{httpd.server_port}', flush=True)
    httpd.serve_forever()
