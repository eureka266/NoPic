"""Synthetic fixtures verify shared projects and real local GIF/MP4 exports."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from cover_project import scaled_config
from project_assets import read_json, write_json
from render_cover import choose_font
from render_motion import prepare_frames
from template_parameters import resolve_template


def fixture(directory):
    """Test swatches only; never published as brand artwork or backgrounds."""
    size = (320, 180)
    base = Image.new('RGBA', size, '#101923')
    texture = Image.new('RGBA', size)
    draw = ImageDraw.Draw(texture)
    for x in range(0, size[0], 80):
        draw.rectangle((x, 0, x+3, size[1]-1), fill=(35, 83, 107, 255))
    combined = base.copy()
    combined.alpha_composite(texture)
    for name, image in (('base', base), ('texture', texture), ('background', combined)):
        image.save(directory / (name + '.png'))
    motion = {'schema_version': 1, 'engine': 'layer-loop', 'type': 'partnership-grid-flow',
              'style': 'preserve', 'source_size': list(size), 'base': 'base.png',
              'layers': [{'id': 'background-grid', 'file': 'texture.png', 'offset': [80, 0]}],
              'duration_seconds': 1, 'fps': 8, 'formats': ['gif']}
    write_json(directory / 'motion-input.json', motion)
    content = {'layout': 'hero', 'title': 'Approved title', 'size': [1600, 900],
               'font': choose_font('Approved title Revised'), 'background': str(directory / 'background.png')}
    resolve_template(content, 'hero', (1600, 900))
    content = scaled_config(content, size)
    write_json(directory / 'content-input.json', content)


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'Real encode tests need FFmpeg and ffprobe')
class MotionProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='blocksec-motion-test-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.project = self.directory / 'theme'
        fixture(self.directory)
        self.run_script('render_cover.py', '--content', self.directory / 'content-input.json', '--project', self.project)
        self.run_script('cover_project.py', 'motion', '--project', self.project, '--config', self.directory / 'motion-input.json')
        layouts = read_json(self.project / 'layout/platform-layouts.json')
        for platform in ('x', 'linkedin-horizontal'):
            layouts['variants'][platform] = {'size': [320, 180], 'motion_export': {'formats': ['gif'], 'fps': 8}}
        write_json(self.project / 'layout/platform-layouts.json', layouts)

    def run_script(self, script, *args, success=True, runtime=None):
        result = subprocess.run([sys.executable, str((runtime or ROOT / 'scripts') / script),
                                 *map(str, args)], text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, success, result.stderr)
        return result

    def test_exact_foreground_and_background_are_shared_between_static_and_motion(self):
        manifest = read_json(self.project / 'project.json')
        self.assertEqual(manifest['schema_version'], 2)
        self.assertEqual(manifest['presentations'], ['static', 'motion'])
        _, _, frame = prepare_frames(self.project, manifest)
        with Image.open(self.project / 'cover.png') as static:
            self.assertIsNone(ImageChops.difference(frame(0), static.convert('RGB')).getbbox())
        self.assertIsNone(ImageChops.difference(frame(0), frame(1)).getbbox())
        self.assertIsNotNone(ImageChops.difference(frame(0), frame(.5)).getbbox())
        with Image.open(self.project / manifest['foreground']) as foreground:
            opaque = foreground.getchannel('A').point(lambda n: 255 if n == 255 else 0)
        self.assertIsNone(ImageChops.multiply(ImageChops.difference(frame(0), frame(.5)),
                                             Image.merge('RGB', (opaque, opaque, opaque))).getbbox())

    def test_real_multiplatform_gif_and_mp4_export(self):
        self.run_script('cover_project.py', 'export', '--project', self.project,
                        '--platform', 'x', '--platform', 'linkedin-horizontal',
                        '--presentation', 'both', '--format', 'gif', '--format', 'mp4')
        for name in ('x', 'linkedin-horizontal'):
            for suffix in ('gif', 'mp4'):
                self.assertTrue((self.project / 'output/background-only' / (name + '.' + suffix)).is_file())
            with Image.open(self.project / 'output/background-only' / (name + '.gif')) as background_gif:
                self.assertEqual(background_gif.size, (320, 180))
                self.assertGreater(background_gif.n_frames, 1)
            with Image.open(self.project / 'output/final-covers' / (name + '.gif')) as gif:
                self.assertEqual(gif.size, (320, 180))
                self.assertEqual(gif.info['loop'], 0)
                self.assertGreater(gif.n_frames, 1)
            probe = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json',
                                    str(self.project / 'output/final-covers' / (name + '.mp4'))],
                                   capture_output=True, text=True, check=True)
            streams = json.loads(probe.stdout)['streams']
            self.assertEqual(len(streams), 1)
            self.assertEqual((streams[0]['width'], streams[0]['height']), (320, 180))
            self.assertEqual(streams[0]['nb_frames'], '8')
            child = self.project / 'variants/full-cover' / name
            record = read_json(child / 'motion/last-render.json')
            self.assertEqual(record['frames'], 8)
            self.assertEqual(set(record['files']), {
                'output/' + kind + '/default.' + suffix
                for kind in ('background-only', 'final-covers') for suffix in ('gif', 'mp4')})
            self.assertTrue((child / 'runtime/render_motion.py').exists())

    def test_copy_revision_refreshes_motion_foreground_and_survives_move(self):
        self.run_script('cover_project.py', 'rebuild', '--project', self.project,
                        '--presentation', 'both', '--format', 'gif')
        original = read_json(self.project / 'motion/last-render.json')
        self.run_script('cover_project.py', 'rebuild', '--project', self.project,
                        '--set', 'title=Revised', '--presentation', 'both', '--format', 'gif')
        revised = read_json(self.project / 'motion/last-render.json')
        self.assertEqual(original['source_background_sha256'], revised['source_background_sha256'])
        self.assertNotEqual(original['source_foreground_sha256'], revised['source_foreground_sha256'])
        moved = self.directory / 'moved'
        shutil.move(self.project, moved)
        self.project = moved
        self.run_script('cover_project.py', 'export', '--project', moved, '--platform', 'x',
                        '--presentation', 'both', runtime=moved / 'runtime')
        for container in [read_json(moved / 'motion/motion.json')]:
            self.assertFalse(Path(container['base']).is_absolute())
        self.assertTrue((moved / 'output/final-covers/x.gif').exists())

    def test_failed_motion_does_not_publish_copy_or_media_changes(self):
        self.run_script('cover_project.py', 'rebuild', '--project', self.project, '--presentation', 'both')
        paths = ['content.json', 'cover.png', 'output/final-covers/default.gif',
                 'output/background-only/default.gif']
        before = {name: (self.project / name).read_bytes() for name in paths}
        motion = read_json(self.project / 'motion/motion.json')
        motion['layers'][0]['offset'] = [37, 0]
        write_json(self.project / 'motion/motion.json', motion)
        self.run_script('cover_project.py', 'rebuild', '--project', self.project, '--set', 'title=Revised',
                        '--presentation', 'both', success=False)
        self.assertEqual(before, {name: (self.project / name).read_bytes() for name in paths})

    def test_background_only_motion_is_an_independent_asset_mode(self):
        project = self.directory / 'background-only'
        self.run_script('cover_project.py', 'background', '--project', project,
                        '--background', self.directory / 'background.png', '--confirm-clean')
        self.run_script('cover_project.py', 'motion', '--project', project, '--config', self.directory / 'motion-input.json')
        self.run_script('cover_project.py', 'rebuild', '--project', project, '--presentation', 'motion')
        self.assertTrue((project / 'output/background-only/default.gif').exists())
        self.assertFalse((project / 'content.json').exists())

    def test_static_rebuild_preserves_motion_and_legacy_project_migrates(self):
        manifest = read_json(self.project / 'project.json')
        for key in ('foreground', 'motion', 'presentations'):
            manifest.pop(key)
        manifest['schema_version'] = 1
        write_json(self.project / 'project.json', manifest)
        self.run_script('cover_project.py', 'rebuild', '--project', self.project)
        self.assertEqual(read_json(self.project / 'project.json')['schema_version'], 2)
        self.run_script('cover_project.py', 'motion', '--project', self.project, '--config', self.directory / 'motion-input.json')
        self.run_script('cover_project.py', 'rebuild', '--project', self.project, '--set', 'title=Revised')
        self.assertEqual(read_json(self.project / 'project.json')['motion'], 'motion/motion.json')
        self.assertTrue((self.project / 'motion/motion.json').exists())

    def test_missing_motion_or_mismatched_background_cannot_produce_fake_media(self):
        motion = read_json(self.project / 'motion/motion.json')
        # Source pixels remain unchanged, but the authoritative background is changed
        # to another existing fixture; the first-frame consistency check must fail.
        manifest = read_json(self.project / 'project.json')
        shutil.copyfile(self.directory / 'base.png', self.project / manifest['background']['master'])
        self.run_script('cover_project.py', 'export', '--project', self.project, '--platform', 'x',
                        '--presentation', 'motion', success=False)
        self.assertFalse((self.project / 'output/final-covers/x.gif').exists())

    def test_external_background_frames_use_the_same_foreground_and_export(self):
        # Stand-in frames verify the file interface; they do not claim that an
        # external HyperFrames installation was exercised by this test.
        with Image.open(self.directory / 'base.png') as original:
            base = original.convert('RGBA')
        with Image.open(self.directory / 'texture.png') as original:
            texture = original.convert('RGBA')
        files = []
        for index in range(9):
            frame = base.copy()
            frame.alpha_composite(ImageChops.offset(texture, index * 10, 0))
            path = self.directory / ('external-' + str(index) + '.png')
            frame.save(path)
            files.append(path.name)
        config = {'schema_version': 1, 'engine': 'background-frames',
                  'type': 'partnership-grid-flow', 'producer': 'test-fixture',
                  'source_size': [320, 180], 'duration_seconds': 1, 'fps': 8,
                  'frames': files, 'formats': ['gif']}
        write_json(self.directory / 'frames-input.json', config)
        self.run_script('cover_project.py', 'motion', '--project', self.project,
                        '--config', self.directory / 'frames-input.json')
        self.run_script('cover_project.py', 'rebuild', '--project', self.project,
                        '--set', 'title=Revised', '--presentation', 'both')
        self.assertEqual(read_json(self.project / 'motion/last-render.json')['engine'], 'background-frames')
        self.assertTrue((self.project / 'output/final-covers/default.gif').exists())
        self.assertEqual(read_json(self.project / 'content.json')['title'], 'Revised')
        saved = read_json(self.project / 'motion/motion.json')
        self.assertTrue(all((self.project / name).is_file() for name in saved['frames']))


if __name__ == '__main__':
    unittest.main()
