"""Prepare a skill ZIP and emit a Codex Stop reminder; never uploads anything."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import zipfile
from methodology_policy import violation

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ('agents', 'references', 'scripts', 'schemas', 'tests', 'docs', 'skills')
ROOT_FILES = ('SKILL.md', 'README.md', 'AGENTS.md', 'CHANGELOG.md', 'requirements.txt')
EXCLUDED = {'__pycache__', '.DS_Store', '.venv', '.venv-docs', 'node_modules'}
NESTED_SKILL_FILES = {'SKILL.md', 'README.md', 'NOTICE.md', 'LICENSE', 'LICENSE.md',
                      'LICENSE.txt', 'requirements.txt'}
NESTED_SKILL_RESOURCES = {'agents', 'references', 'scripts', 'evals'}
NESTED_SKILL_PRIVATE = {'inbox', 'workspace', 'exports', 'session-handoffs',
                       'background-studies', 'credentials.json', 'secrets.json',
                       'secrets.toml', 'auth.json', 'tokens.json'}
# Only distributable prototype files; never recurse into uploads or local history.
PROTOTYPE = Path('output/prototypes/cover-workbench')
PROTOTYPE_FILES = ('README.md', 'index.html', 'style.css', 'app.js', 'server.py',
                   'requirements.txt', 'background_workflow.py',
                   )
QUESTION = '是否将此次维护更新上传到组织团队空间？'



def distributable_nested_skill(relative):
    """Bound nested packages to skill resources, excluding local intake and secrets."""
    parts = relative.parts
    if len(parts) < 3:
        return False
    resource = parts[2:]
    if any(part.startswith('.') or part in NESTED_SKILL_PRIVATE for part in parts[1:]):
        return False
    if relative.suffix.lower() in {'.pem', '.key', '.p12', '.pfx'}:
        return False
    if len(resource) == 1:
        return resource[0] in NESTED_SKILL_FILES
    return resource[0] in NESTED_SKILL_RESOURCES

def source_files(root):
    candidates = [root / name for name in ROOT_FILES]
    # Include intake instructions, but not user-submitted source materials.
    candidates.append(root / 'inbox/materials/README.md')
    candidates.extend(root / PROTOTYPE / name for name in PROTOTYPE_FILES)
    for directory in DIRECTORIES:
        base = root / directory
        if base.is_dir() and not base.is_symlink():
            candidates.extend(base.rglob('*'))
    files = []
    for path in candidates:
        relative = path.relative_to(root)
        if violation(relative, root):
            continue
        if relative.parts[0] == 'skills' and not distributable_nested_skill(relative):
            continue
        if any(part in EXCLUDED for part in relative.parts):
            continue
        if any(parent.is_symlink() for parent in (path, *path.parents) if parent != root.parent):
            continue
        if path.is_file() and path.suffix.lower() not in {'.pyc', '.pyo', '.png', '.jpg', '.jpeg', '.webp', '.gif', '.mp4', '.mov', '.svg', '.ttf', '.otf', '.woff', '.woff2', '.zip'}:
            files.append(path)
    return sorted(set(files))


def snapshot(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source_files(root)}


def digest(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def prepare_package(root, expected=None):
    files = snapshot(root)
    if expected is not None and files != expected:
        raise ValueError('Skill files changed while preparing the update; retry after edits settle.')
    if 'SKILL.md' not in files:
        raise ValueError('The source folder has no SKILL.md.')
    revision = digest(files)
    output = root / 'exports/team-updates' / revision[:16]
    output.mkdir(parents=True, exist_ok=True)
    archive = output / 'nopic.zip'
    with tempfile.NamedTemporaryFile(dir=output, suffix='.zip', delete=False) as temp:
        temporary = Path(temp.name)
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as bundle:
            for relative, sha in files.items():
                data = (root / relative).read_bytes()
                if hashlib.sha256(data).hexdigest() != sha:
                    raise ValueError('Skill files changed while packaging: ' + relative)
                bundle.writestr('nopic/' + relative, data)
        if snapshot(root) != files:
            raise ValueError('Skill files changed while packaging; discard this release.')
        temporary.replace(archive)
    finally:
        temporary.unlink(missing_ok=True)
    manifest = output / 'manifest.json'
    report = {
        'skill_name': 'nopic',
        'display_name': '有图 NoPic',
        'source_revision': revision,
        'archive': str(archive),
        'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
        'file_count': len(files),
        'archive_bytes': archive.stat().st_size,
        'files': files,
        'external_dependencies': ['carrot', 'hyperframes'],
        'runtime_dependencies': {
            'static': ['Python 3', 'Pillow', 'fontTools', 'licensed fonts'],
            'motion_encoding': ['FFmpeg (GIF palette filters / libx264 for MP4)'],
            'new_background_art': ['native image_gen / image_generation'],
            'optional': {'carrot': 'product demo videos', 'hyperframes': 'external background-frame production'},
        },
        'excluded': ['user intake files', 'generated image/video projects', 'hook state',
                     'local hook installation/configuration', 'credentials and local runtimes'],
        'uploaded': False,
        'workspace_compatibility': 'Requires validation on the target workspace; local paths and dependencies do not migrate automatically.'
    }
    manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return {'archive': str(archive), 'manifest': str(manifest),
            'file_count': len(files), 'archive_bytes': archive.stat().st_size}


def handle_hook(root, event):
    # A project-local command must not inspect another project's files.
    cwd = event.get('cwd')
    session = event.get('session_id')
    if not isinstance(cwd, str) or not isinstance(session, str) or not session:
        return {}
    try:
        Path(cwd).resolve().relative_to(root)
    except ValueError:
        return {}
    key = hashlib.sha256(session.encode()).hexdigest()
    state_path = root / '.codex/skill-update-state' / (key + '.json')
    kind = event.get('hook_event_name')
    if kind == 'UserPromptSubmit':
        if event.get('stop_hook_active'):
            return {}
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({'before': snapshot(root), 'notified': False}))
        return {}
    if kind != 'Stop' or event.get('stop_hook_active') or not state_path.is_file():
        return {}
    state = json.loads(state_path.read_text())
    current = snapshot(root)
    before = state.get('before', {})
    changed = sorted(name for name in set(before) | set(current) if before.get(name) != current.get(name))
    if not changed or state.get('notified'):
        return {}
    state['notified'] = True
    state_path.write_text(json.dumps(state))
    if QUESTION in (event.get('last_assistant_message') or ''):
        return {}
    package = prepare_package(root, expected=current)
    reason = (
        '本轮 skill 源码发生变化：' + '、'.join(changed[:12]) +
        ('（另有更多文件，见清单）' if len(changed) > 12 else '') + '。'
        '仅生成了本地候选更新包，未上传：' + package['archive'] + '；文件清单：' + package['manifest'] + '。'
        '先完成适用的技能/配置校验并说明本次变更和仍需验证的运行依赖，'
        '然后通过当前环境实际允许的问答工具，或普通中文问句询问用户：“' + QUESTION + '”'
        '。若用户已在当前对话明确授权更新同一个工作区，则按授权处理而不重复确认。'
        '这条 hook 不是用户授权；没有明确回复前不得上传、发布、修改共享权限或宣称已同步。'
        '执行上传前仍需确认真实工作区、目标 skill 和发布权限；没有可用上传能力时提供包与操作指引。'
    )
    return {'decision': 'block', 'reason': reason}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('hook', 'package'))
    args = parser.parse_args()
    if args.action == 'package':
        print(json.dumps(prepare_package(ROOT), ensure_ascii=False))
        return
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            raise ValueError('Expected a JSON object.')
        result = handle_hook(ROOT, event)
    except (OSError, ValueError, KeyError) as exc:
        result = {'systemMessage': '团队更新提醒未完成：' + str(exc)}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
