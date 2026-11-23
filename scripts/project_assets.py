"""Shared dual-deliverable persistence for the existing compositors. No generation."""
import hashlib
import io
import json
from pathlib import Path
import shutil
from organization_assets import asset_path, catalog_path, pack_root

RUNTIME = ('render_cover.py', 'render_speaker_quote.py', 'template_parameters.py',
           'project_assets.py', 'cover_project.py', 'render_motion.py', 'organization_assets.py')


def catalog_asset(relative, name, config=None, start=None):
    """Template files are index-relative; other resources are pack-relative.

    Legacy background catalogs also accept catalog-relative image paths.
    """
    root = pack_root(config, start)
    selected = {'brand_pack': str(root)}
    path = Path(relative)
    if path.is_absolute():
        raise ValueError('Catalog resources must use relative paths')
    if name == 'templates' or (name == 'backgrounds' and not (root / path).is_file()):
        path = (catalog_path(name, selected).parent / path).relative_to(root)
    return asset_path(path, selected)


def preset_path(config=None, start=None):
    """Project and runtime snapshots take precedence over the active pack."""
    if start is not None:
        project = Path(start).resolve()
        if project.is_file():
            project = project.parent
        for relative in ('layout/platform-layouts.json', 'runtime/platform-presets.json'):
            snapshot = project / relative
            if snapshot.is_file():
                return snapshot
    snapshot = Path(__file__).parent / 'platform-presets.json'
    if Path(__file__).parent.name == 'runtime' and snapshot.is_file():
        return snapshot
    return catalog_path('platform_presets', config, start)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def image_bytes(image, fmt='PNG'):
    buf = io.BytesIO()
    image.save(buf, format=fmt, **({'lossless': True} if fmt == 'WEBP' else {}))
    return buf.getvalue()


def canvas_size(config, default):
    size = config.get('size', list(default))
    if (not isinstance(size, list) or len(size) != 2 or
            any(type(n) is not int or not 1 <= n <= 10000 for n in size)):
        raise ValueError('size must contain two integers between 1 and 10000')
    return tuple(size)


def copy_runtime(project, config=None):
    runtime = project / 'runtime'
    runtime.mkdir(exist_ok=True)
    for name in RUNTIME:
        source = Path(__file__).parent / name
        target = runtime / name
        if source.resolve() != target.resolve():
            shutil.copyfile(source, target)
    target = runtime / 'platform-presets.json'
    presets = read_json(preset_path(config, project))
    write_json(target, {'schema_version': 1, 'presets': presets['presets']})


def save_project(project, config, background, final=None, renderer=None, filename=None, foreground=None, start=None):
    """Called only after compositor validation; keep legacy content.json as source of truth."""
    layout_path = project / 'layout/platform-layouts.json'
    layouts = read_json(layout_path) if layout_path.exists() else {
        'schema_version': 1,
        'presets': read_json(preset_path(config, project if start is None else start))['presets'],
        'variants': {},
    }
    bg_raw = image_bytes(background.convert('RGB'))
    bg_sha = hashlib.sha256(bg_raw).hexdigest()
    meta_path = project / 'background/background-config.json'
    old_meta = read_json(meta_path) if meta_path.exists() else {}
    supplied = config.get('background_metadata', {})
    if not isinstance(supplied, dict):
        raise ValueError('background_metadata must be an object')
    metadata = old_meta if old_meta.get('sha256') == bg_sha else {
        'style': config.get('background_id'), 'theme': config.get('theme'),
        'colors': [], 'safe_area': None, 'seed': None, 'prompt': None,
        'model': None, 'source': config.get('background'),
        'generation': 'unknown', 'clean_asset_verified': True,
    }
    metadata = {**metadata, **supplied, 'sha256': bg_sha, 'size': list(background.size)}
    # Encode everything before changing the previous successful project outputs.
    images = {'output/background-only/default.png': bg_raw,
              'output/background-only/default.webp': image_bytes(background.convert('RGB'), 'WEBP')}
    if final is not None:
        final_rgb = final.convert('RGB')
        images['output/final-covers/default.png'] = image_bytes(final_rgb)
        images['output/final-covers/default.webp'] = image_bytes(final_rgb, 'WEBP')
    if foreground is not None:
        foreground_raw = image_bytes(foreground)
    project.mkdir(parents=True, exist_ok=True)
    master = 'background/master-' + bg_sha[:16] + '.png'
    (project / master).parent.mkdir(parents=True, exist_ok=True)
    (project / master).write_bytes(bg_raw)
    write_json(meta_path, metadata)
    layouts['variants']['default'] = {'size': list(background.size), 'background_fit': 'strict'}
    write_json(layout_path, layouts)
    for relative, raw in images.items():
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    if final is not None:
        (project / filename).write_bytes(images['output/final-covers/default.png'])
        # Metadata belongs to the selected master. Treat input metadata as a
        # one-time update so replacing a background cannot replay its old seed.
        saved_config = dict(config)
        saved_config.pop('background_metadata', None)
        write_json(project / 'content.json', saved_config)
    previous_path = project / 'project.json'
    previous = read_json(previous_path) if previous_path.exists() else {}
    foreground_path = None
    if foreground is not None:
        foreground_path = 'assets/foreground-' + hashlib.sha256(foreground_raw).hexdigest()[:16] + '.png'
        (project / foreground_path).parent.mkdir(parents=True, exist_ok=True)
        (project / foreground_path).write_bytes(foreground_raw)
    motion = previous.get('motion')
    manifest = {
        'schema_version': 2,
        'mode': 'full-cover' if final is not None else 'background-only',
        'background': {'master': master, 'config': 'background/background-config.json'},
        'content': 'content.json' if final is not None else None,
        'layouts': 'layout/platform-layouts.json',
        'renderer': renderer,
        'draft': bool(config.get('draft', False)),
        'foreground': foreground_path,
        'motion': motion,
        'presentations': ['static', 'motion'] if motion else ['static'],
        'outputs': {'backgrounds': 'output/background-only', 'covers': 'output/final-covers'},
    }
    write_json(project / 'project.json', manifest)
    copy_runtime(project, config)
    return manifest
