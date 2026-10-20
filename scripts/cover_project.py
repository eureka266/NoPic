"""Create clean-background projects, export platform variants, or recompile saved covers."""
import argparse
import copy
import io
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from PIL import Image, ImageOps
from project_assets import canvas_size, read_json, save_project, write_json
from render_motion import attach_motion, copy_motion, render_motion, validate_config

SCRIPTS = Path(__file__).resolve().parent
ASSET_FIELDS = ('background', 'image', 'logo', 'partner_logo', 'separator', 'portrait',
                'photo_original', 'font', 'font_bold')
RENDERERS = {'render_cover.py', 'render_speaker_quote.py'}
SLUG = re.compile(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z')


def load_project(project):
    manifest = read_json(project / 'project.json')
    if manifest.get('schema_version') not in (1, 2) or manifest.get('mode') not in ('background-only', 'full-cover'):
        raise ValueError('Unsupported project manifest')
    if manifest.get('renderer') is not None and manifest['renderer'] not in RENDERERS:
        raise ValueError('Unknown project renderer')
    return manifest


def fit_background(image, size, fit):
    if fit not in ('strict', 'cover'):
        raise ValueError('background_fit must be strict or cover')
    if fit == 'cover':
        return ImageOps.fit(image, size, Image.Resampling.LANCZOS)
    if abs((image.width / image.height) / (size[0] / size[1]) - 1) > .001:
        raise ValueError('Aspect ratio differs: supply a platform background_file or explicitly approve background_fit=cover')
    return image.resize(size, Image.Resampling.LANCZOS)


def scaled_config(config, size, template=None):
    result = copy.deepcopy(config)
    old = config['size']
    if template is not None:
        result['template'] = copy.deepcopy(template)
        result['template_id'] = template['id']
        result['layer_overrides'] = {}
    elif tuple(size) != tuple(old):
        if abs((size[0] / size[1]) / (old[0] / old[1]) - 1) > .001:
            raise ValueError('Full-cover aspect ratio differs: save an explicit platform template; final PNGs cannot be stretched or cropped')
        scale = size[0] / old[0]
        template = result['template']
        groups = [template['layers'], result.get('layer_overrides', {})]
        groups.extend(template.get('logo_variants', {}).values())
        pattern = template.get('section_pattern')
        if pattern:
            for key in ('top', 'total_height'):
                pattern[key] = round(pattern[key] * scale)
            groups.append(pattern['layers'])
        for group in groups:
            for fields in group.values():
                for key in ('x', 'y', 'width', 'height', 'font_size_max', 'font_size_min',
                            'font_size', 'line_width', 'y_offset', 'height_inset'):
                    if key in fields:
                        fields[key] = max(0 if key in ('x', 'y', 'y_offset', 'height_inset') else 1,
                                          round(fields[key] * scale))
        template['canvas'].update(width=size[0], height=size[1])
    result['size'] = list(size)
    return result


def compile_cover(project, manifest, content=None, flags=()):
    renderer = manifest['renderer']
    if renderer not in RENDERERS:
        raise ValueError('Background-only project has no cover content; first create content.json using a matching template')
    command = [sys.executable, str(SCRIPTS / renderer), '--project', str(project)]
    if content:
        command += ['--content', str(content)]
    if manifest.get('draft'):
        command += ['--draft']
    command.extend(flags)
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.strip())


def export_project(project, platforms, fit=None, mode='both', presentation='static', formats=None):
    manifest = load_project(project)
    layouts = read_json(project / manifest['layouts'])
    content = read_json(project / manifest['content']) if manifest['content'] else None
    metadata = read_json(project / manifest['background']['config'])
    master = Image.open(project / manifest['background']['master']).convert('RGB')
    platforms = platforms or ['default']
    if len(set(platforms)) != len(platforms):
        raise ValueError('Duplicate platform names')
    # Stage every requested platform before publishing any: overflow or a missing
    # background/layout must leave the last successful batch untouched.
    with tempfile.TemporaryDirectory(prefix='cover-export-') as temp:
        stage = Path(temp)
        rendered = []
        for name in platforms:
            if not SLUG.fullmatch(name):
                raise ValueError('Invalid platform id: ' + name)
            spec = copy.deepcopy(layouts['presets'].get(name, {}))
            spec.update(layouts['variants'].get(name, {}))
            if not spec:
                raise ValueError('Unknown platform: ' + name)
            size = canvas_size(spec, master.size)
            bg_source = project / spec['background_file'] if spec.get('background_file') else None
            image = Image.open(bg_source).convert('RGB') if bg_source else master
            bg = fit_background(image, size, fit or spec.get('background_fit', 'strict'))
            variant_metadata = copy.deepcopy(metadata) if bg_source is None else {
                'style': None, 'theme': None, 'colors': [], 'seed': None, 'prompt': None,
                'model': None, 'source': spec['background_file'], 'generation': 'unknown',
                'clean_asset_verified': True,
            }
            if bg_source is None:
                variant_metadata['parent_sha256'] = metadata['sha256']
            variant_metadata.update(spec.get('background_metadata', {}))
            variant_metadata.update(safe_area=spec.get('safe_area'), platform=name,
                                    adaptation=fit or spec.get('background_fit', 'strict'))
            child = stage / name
            child.mkdir()
            write_json(child / 'layout/platform-layouts.json', {
                'schema_version': 1, 'presets': copy.deepcopy(layouts['presets']), 'variants': {},
            })
            if content is not None and mode == 'both':
                config = scaled_config(content, size, spec.get('template'))
                # Resolve original project paths before creating a detached child.
                for key in ASSET_FIELDS:
                    if config.get(key) and not str(config[key]).startswith('https://'):
                        config[key] = str((project / config[key]).resolve())
                bg_path = stage / (name + '-background.png')
                bg.save(bg_path)
                config['background'] = str(bg_path)
                config['background_fit'] = 'contain'
                config['background_metadata'] = variant_metadata
                if isinstance(spec.get('layer_overrides'), dict):
                    config['layer_overrides'].update(spec['layer_overrides'])
                config_path = stage / (name + '-content.json')
                write_json(config_path, config)
                compile_cover(child, manifest, config_path)
            else:
                save_project(child, {'background': str(bg_source or manifest['background']['master']),
                                     'background_metadata': variant_metadata}, bg)
            copy_motion(project, child, spec.get('motion_file'))
            if presentation in ('motion', 'both'):
                child_manifest = load_project(child)
                if not child_manifest.get('motion'):
                    raise ValueError('Attach an actual motion configuration before requesting motion export')
                motion_path = child / child_manifest['motion']
                motion_config = read_json(motion_path)
                overrides = spec.get('motion_export', {})
                if not isinstance(overrides, dict) or overrides.keys() - {'duration_seconds', 'fps', 'formats'}:
                    raise ValueError('motion_export supports only duration_seconds, fps and formats')
                motion_config.update(overrides)
                validate_config(motion_config)
                write_json(motion_path, motion_config)
                render_motion(child, formats)
            rendered.append((name, child, spec))
        for name, child, spec in rendered:
            # Per-platform projects retain editable layers and portable assets.
            variant_mode = 'full-cover' if content is not None and mode == 'both' else 'background-only'
            target = project / 'variants' / variant_mode / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(child, target)
            for kind in ('background-only', 'final-covers'):
                source = child / 'output' / kind
                if source.exists():
                    output = project / 'output' / kind
                    output.mkdir(parents=True, exist_ok=True)
                    for file in source.glob('default.*'):
                        shutil.copyfile(file, output / (name + file.suffix))
            spec['background_fit'] = fit or spec.get('background_fit', 'strict')
            layouts['variants'][name] = spec
        write_json(project / manifest['layouts'], layouts)
    return {'project': str(project), 'platforms': platforms, 'mode': mode, 'presentation': presentation}


def rebuild_project(project, flags=(), presentation='static', formats=None):
    manifest = load_project(project)
    if presentation == 'static':
        compile_cover(project, manifest, flags=flags)
        return
    # Stage updated static foreground and motion together; a failed motion pass
    # must not publish copy changes or overwrite the previous successful media.
    with tempfile.TemporaryDirectory(prefix='cover-rebuild-') as temp:
        stage = Path(temp) / 'project'

        def ignore(directory, names):
            return [name for name in names if name in ('__pycache__',) or
                    (Path(directory) == project and name in ('variants', 'output'))]

        shutil.copytree(project, stage, ignore=ignore)
        if manifest.get('content'):
            compile_cover(stage, manifest, flags=flags)
        elif flags:
            raise ValueError('Background-only project has no editable cover copy or asset slots')
        render_motion(stage, formats)
        shutil.copytree(stage, project, dirs_exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    init = sub.add_parser('background', help='Use an existing, visually verified clean image; never generate')
    init.add_argument('--project', type=Path, required=True)
    init.add_argument('--background', type=Path, required=True)
    init.add_argument('--confirm-clean', action='store_true', required=True)
    init.add_argument('--metadata', type=Path)
    export = sub.add_parser('export')
    export.add_argument('--project', type=Path, action='append', required=True)
    export.add_argument('--platform', action='append', default=[])
    export.add_argument('--fit', choices=('strict', 'cover'))
    export.add_argument('--mode', choices=('background-only', 'both'), default='both')
    export.add_argument('--presentation', choices=('static', 'motion', 'both'), default='static')
    export.add_argument('--format', action='append', choices=('mp4', 'gif'), default=[])
    rebuild = sub.add_parser('rebuild')
    rebuild.add_argument('--project', type=Path, required=True)
    rebuild.add_argument('--set', action='append', default=[])
    rebuild.add_argument('--asset', action='append', default=[])
    rebuild.add_argument('--presentation', choices=('static', 'motion', 'both'), default='static')
    rebuild.add_argument('--format', action='append', choices=('mp4', 'gif'), default=[])
    motion = sub.add_parser('motion', help='Attach actual separated motion assets to an existing cover project')
    motion.add_argument('--project', type=Path, required=True)
    motion.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    if getattr(args, 'format', None) and args.presentation == 'static':
        raise ValueError('--format gif/mp4 requires --presentation motion or both')
    if args.action == 'background':
        project = args.project.resolve()
        if project.exists():
            raise ValueError('New background project needs an unused directory; preserve the existing project')
        raw = args.background.resolve().read_bytes()
        with Image.open(io.BytesIO(raw)) as original:
            image = ImageOps.exif_transpose(original).convert('RGB')
        config = {'background': str(args.background.resolve()),
                  'background_metadata': read_json(args.metadata) if args.metadata else {}}
        save_project(project, config, image)
        original_dir = project / 'background/original'
        original_dir.mkdir()
        (original_dir / args.background.name).write_bytes(raw)
        print(project / 'project.json')
    elif args.action == 'motion':
        project = args.project.resolve()
        load_project(project)
        attach_motion(project, args.config.resolve())
        print(project / 'project.json')
    elif args.action == 'rebuild':
        project = args.project.resolve()
        manifest = load_project(project)
        flags = []
        for key in ('set', 'asset'):
            for value in getattr(args, key):
                flags.extend(['--' + key, value])
        rebuild_project(project, flags, args.presentation, args.format)
        print(project / 'project.json')
    else:
        import json
        for project in args.project:
            print(json.dumps(export_project(project.resolve(), args.platform, args.fit, args.mode,
                                            args.presentation, args.format), ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Project operation failed: ' + str(exc), file=sys.stderr)
        sys.exit(1)
