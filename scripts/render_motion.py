"""Loop existing separated image layers and composite the shared static foreground.

No background drawing, extraction, or generation. FFmpeg encodes actual GIF/MP4.
"""
import copy
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from PIL import Image, ImageChops
from project_assets import canvas_size, copy_runtime, read_json, write_json


def asset_fields(config):
    if config.get('engine') == 'background-frames':
        for index in range(len(config['frames'])):
            yield config['frames'], index
        return
    yield config, 'base'
    for layer in config['layers']:
        yield layer, 'file'
        if layer.get('mask'):
            yield layer, 'mask'


def validate_config(config):
    if config.get('schema_version') != 1 or config.get('engine') not in ('layer-loop', 'background-frames'):
        raise ValueError('Motion needs schema_version=1 and engine=layer-loop or background-frames')
    if config.get('type') != 'partnership-grid-flow':
        raise ValueError('No executable recipe for this motion type')
    style = config.get('style', 'preserve')
    if not isinstance(style, str) or not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', style):
        raise ValueError('Motion style must be a descriptive lowercase id; source assets define colors')
    size = canvas_size({'size': config.get('source_size')}, (0, 0))
    duration, fps = config.get('duration_seconds', 5), config.get('fps', 30)
    if type(duration) not in (int, float) or not 0 < duration <= 60:
        raise ValueError('duration_seconds must be > 0 and <= 60')
    if type(fps) is not int or not 1 <= fps <= 60:
        raise ValueError('fps must be an integer between 1 and 60')
    if abs(duration * fps - round(duration * fps)) > 1e-6 or duration * fps < 2:
        raise ValueError('duration_seconds * fps must be an integer of at least 2 frames')
    if config['engine'] == 'background-frames':
        frames = config.get('frames')
        if not isinstance(frames, list) or len(frames) != round(duration * fps) + 1:
            raise ValueError('Background frames require duration_seconds * fps + 1 actual frames, including the cycle endpoint')
        for container, key in asset_fields(config):
            if not isinstance(container[key], str) or not container[key]:
                raise ValueError('Missing actual background frame')
        formats = config.get('formats', ['mp4'])
        if not isinstance(formats, list) or not formats or any(fmt not in ('mp4', 'gif') for fmt in formats):
            raise ValueError('Motion formats must contain mp4 or gif')
        return size
    layers = config.get('layers')
    if not isinstance(layers, list) or not layers:
        raise ValueError('Motion requires actual separated texture layers')
    names = set()
    for layer in layers:
        if not isinstance(layer, dict) or not isinstance(layer.get('id'), str) or not layer['id'] or layer['id'] in names:
            raise ValueError('Each motion layer needs a unique id')
        names.add(layer['id'])
        offset = layer.get('offset')
        if (not isinstance(offset, list) or len(offset) != 2 or
                any(type(n) is not int for n in offset) or offset == [0, 0]):
            raise ValueError('Layer offset must contain two integers and a nonzero displacement')
    for container, key in asset_fields(config):
        if not isinstance(container.get(key), str) or not container[key]:
            raise ValueError('Missing actual motion asset: ' + key)
    formats = config.get('formats', ['mp4'])
    if not isinstance(formats, list) or not formats or any(fmt not in ('mp4', 'gif') for fmt in formats):
        raise ValueError('Motion formats must contain mp4 or gif')
    return size


def attach_motion(project, source, refresh_runtime=True):
    """Import a real recipe and preserve asset bytes inside the shared cover project."""
    config = copy.deepcopy(read_json(source))
    validate_config(config)
    prepared = []
    for container, key in asset_fields(config):
        path = (source.parent / container[key]).resolve()
        raw = path.read_bytes()
        with Image.open(path) as image:
            image.verify()
        relative = 'motion/assets/' + hashlib.sha256(raw).hexdigest()[:16] + path.suffix.lower()
        container[key] = relative
        prepared.append((relative, raw))
    manifest = read_json(project / 'project.json')
    for relative, raw in prepared:
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    # Paths in motion.json are relative to the cover project, not motion/.
    write_json(project / 'motion/motion.json', config)
    manifest.update(schema_version=2, motion='motion/motion.json', presentations=['static', 'motion'])
    manifest.setdefault('foreground', None)
    write_json(project / 'project.json', manifest)
    if refresh_runtime:
        copy_runtime(project)


def copy_motion(source_project, target_project, source_file=None):
    manifest = read_json(source_project / 'project.json')
    path = source_project / (source_file or manifest.get('motion') or '')
    if not source_file and not manifest.get('motion'):
        return
    config = copy.deepcopy(read_json(path))
    for container, key in asset_fields(config):
        container[key] = str((source_project / container[key]).resolve())
    # attach_motion consumes a config whose paths are relative to that input JSON.
    with tempfile.TemporaryDirectory(prefix='cover-motion-import-') as temp:
        source = Path(temp) / 'motion.json'
        write_json(source, config)
        attach_motion(target_project, source, refresh_runtime=False)


def _difference(left, right):
    return max(high for low, high in ImageChops.difference(left.convert('RGB'), right.convert('RGB')).getextrema())


def prepare_frames(project, manifest):
    if not manifest.get('motion'):
        raise ValueError('Attach an actual motion configuration before requesting motion export')
    config = read_json(project / manifest['motion'])
    source_size = validate_config(config)
    with Image.open(project / manifest['background']['master']) as original:
        master = original.convert('RGBA')
    size = master.size
    if abs((size[0]/size[1]) / (source_size[0]/source_size[1]) - 1) > .001:
        raise ValueError('Motion aspect ratio differs: provide a platform motion_file with matching separated layers')
    scale = size[0] / source_size[0]

    def read_image(relative, kind='RGBA'):
        with Image.open(project / relative) as original:
            if original.size != source_size:
                raise ValueError('Motion source asset must match source_size: ' + relative)
            return original.convert(kind).resize(size, Image.Resampling.LANCZOS)

    if config['engine'] == 'background-frames':
        if _difference(read_image(config['frames'][0]), read_image(config['frames'][-1])):
            raise ValueError('Background frame cycle endpoint differs from its first frame')

        def background_frame(phase):
            count = len(config['frames']) - 1
            return read_image(config['frames'][min(count, round(phase * count))])
    else:
        base = read_image(config['base'])
        layers = []
        for layer in config['layers']:
            texture = read_image(layer['file'])
            if texture.getchannel('A').getextrema()[0] != 0 or texture.getbbox() is None:
                raise ValueError('Moving texture needs genuine transparency; do not move a flattened poster')
            offset = tuple(round(n * scale) for n in layer['offset'])
            delta = ImageChops.difference(texture, ImageChops.offset(texture, *offset))
            if offset == (0, 0) or any(high for low, high in delta.getextrema()):
                raise ValueError('Motion offset must equal a repeating texture period at this size')
            mask = read_image(layer['mask'], 'L') if layer.get('mask') else None
            layers.append((texture, offset, mask))

        def background_frame(phase):
            canvas = base.copy()
            for texture, offset, mask in layers:
                moved = ImageChops.offset(texture, *(round(n * phase) for n in offset))
                if mask is not None:
                    moved.putalpha(ImageChops.multiply(moved.getchannel('A'), mask))
                canvas.alpha_composite(moved)
            return canvas
    foreground = None
    if manifest['mode'] == 'full-cover':
        if not manifest.get('foreground'):
            raise ValueError('Rebuild the existing cover to save an exact independent foreground')
        with Image.open(project / manifest['foreground']) as image:
            foreground = image.convert('RGBA')
        if foreground.size != size:
            raise ValueError('Foreground size differs from current cover')

    def frame(phase, include_foreground=True):
        canvas = background_frame(phase)
        if include_foreground and foreground is not None:
            canvas.alpha_composite(foreground)
        return canvas.convert('RGB')

    if _difference(frame(0, False), master) > 2:
        raise ValueError('Separated layers do not reproduce the current background; keep the approved master and supply matching layers')
    if _difference(frame(0), frame(1)):
        raise ValueError('Motion cycle has a discontinuity')
    return config, size, frame


def render_motion(project, formats=None):
    """Stage media and publish only after every requested encode succeeds."""
    manifest = read_json(project / 'project.json')
    config, size, frame = prepare_frames(project, manifest)
    formats = formats or config.get('formats', ['mp4'])
    if not formats or any(fmt not in ('mp4', 'gif') for fmt in formats):
        raise ValueError('Unsupported motion format')
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise ValueError('Motion encoding requires FFmpeg; static project and source layers remain available')
    if 'mp4' in formats and any(n % 2 for n in size):
        raise ValueError('MP4 yuv420p requires even dimensions; choose explicit platform dimensions')
    fps, duration = config.get('fps', 30), config.get('duration_seconds', 5)
    total = round(duration * fps)
    with tempfile.TemporaryDirectory(prefix='cover-motion-render-') as temp:
        stage = Path(temp)
        kinds = ['background-only']
        if manifest['mode'] != 'background-only':
            kinds.append('final-covers')
        for kind in kinds:
            (stage / kind).mkdir()
        first, changed = frame(0), False
        for index in range(total):
            current = frame(index / total)
            changed = changed or bool(_difference(first, current))
            filename = str(index).zfill(6) + '.png'
            for kind in kinds:
                pixels = current if kind == 'final-covers' else frame(index / total, False)
                pixels.save(stage / kind / filename)
        # An unchanged result is not an animation, even if a recipe was attached.
        if not changed:
            raise ValueError('Configured motion produces no visible change')
        outputs = []
        for kind in kinds:
            for fmt in dict.fromkeys(formats):
                output = stage / kind / ('default.' + fmt)
                command = [ffmpeg, '-nostdin', '-y', '-v', 'error', '-framerate', str(fps),
                           '-i', str(stage / kind / '%06d.png'), '-an']
                if fmt == 'mp4':
                    command += ['-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart']
                else:
                    command += ['-filter_complex', '[0:v]split[a][b];[a]palettegen[p];[b][p]paletteuse', '-loop', '0']
                result = subprocess.run(command + [str(output)], capture_output=True, text=True, timeout=180)
                if result.returncode or not output.is_file() or output.stat().st_size == 0:
                    raise ValueError('Motion encoding failed: ' + result.stderr[-1500:])
                outputs.append((kind, output))
        for kind, output in outputs:
            directory = project / 'output' / kind
            directory.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(output, directory / output.name)
        frame(0).save(project / 'motion/poster.png')
        record = {'schema_version': 1, 'engine': config['engine'], 'size': list(size),
                  'duration_seconds': duration, 'fps': fps, 'frames': total, 'formats': formats,
                  'source_background_sha256': hashlib.sha256((project / manifest['background']['master']).read_bytes()).hexdigest(),
                  'source_foreground_sha256': hashlib.sha256((project / manifest['foreground']).read_bytes()).hexdigest() if manifest.get('foreground') else None,
                  'files': [str(Path('output') / kind / output.name) for kind, output in outputs]}
        write_json(project / 'motion/last-render.json', record)
    return record
