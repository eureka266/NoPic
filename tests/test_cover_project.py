"""Observable dual-deliverable, migration and platform export behavior."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from render_cover import choose_font
from cover_project import scaled_config
from template_parameters import resolve_template


class CoverProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='blocksec-project-test-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.project = self.directory / 'theme'
        self.background = ROOT / 'assets/backgrounds/hex-outline.png'

    def run_script(self, name, *args, success=True, script_dir=None):
        result = subprocess.run([sys.executable, str((script_dir or ROOT/'scripts') / name),
                                 *map(str, args)], capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stderr)
        return result

    def load(self, relative):
        return json.loads((self.project / relative).read_text())

    def full_cover(self):
        source = self.directory / 'approved.json'
        source.write_text(json.dumps({'layout': 'hero', 'title': 'Approved title',
                                     'background': str(self.background), 'font': choose_font('Approved title Revised')}))
        self.run_script('render_cover.py', '--project', self.project, '--content', source)

    def test_background_only_needs_no_copy_or_fonts_and_retains_original(self):
        self.run_script('cover_project.py', 'background', '--project', self.project,
                        '--background', self.background, '--confirm-clean')
        manifest = self.load('project.json')
        self.assertEqual(manifest['mode'], 'background-only')
        self.assertIsNone(manifest['content'])
        self.assertFalse((self.project / 'content.json').exists())
        self.assertFalse((self.project / 'output/final-covers').exists())
        self.assertEqual((self.project / 'background/original' / self.background.name).read_bytes(), self.background.read_bytes())
        meta = self.load(manifest['background']['config'])
        self.assertIsNone(meta['seed'])
        self.assertEqual(meta['sha256'], hashlib.sha256((self.project / manifest['background']['master']).read_bytes()).hexdigest())
        with Image.open(self.background) as original, Image.open(self.project / 'output/background-only/default.webp') as output:
            self.assertEqual(original.convert('RGB').tobytes(), output.convert('RGB').tobytes())
        self.run_script('cover_project.py', 'background', '--project', self.project,
                        '--background', self.background, '--confirm-clean', success=False)

    def test_full_cover_preserves_clean_master_after_copy_edit(self):
        self.full_cover()
        manifest = self.load('project.json')
        master = self.project / manifest['background']['master']
        original = master.read_bytes()
        meta = (self.project / manifest['background']['config']).read_bytes()
        final_before = (self.project / 'cover.png').read_bytes()
        self.assertNotEqual(original, final_before)
        self.run_script('cover_project.py', 'rebuild', '--project', self.project, '--set', 'title=Revised')
        self.assertEqual(master.read_bytes(), original)
        self.assertEqual((self.project / manifest['background']['config']).read_bytes(), meta)
        self.assertNotEqual((self.project / 'cover.png').read_bytes(), final_before)
        self.assertEqual((self.project / 'cover.png').read_bytes(), (self.project / 'output/final-covers/default.png').read_bytes())
        self.assertEqual(self.load('content.json')['title'], 'Revised')

    def test_portable_runtime_rebuilds_and_exports_after_project_move(self):
        self.full_cover()
        moved = self.directory / 'moved'
        shutil.move(self.project, moved)
        self.project = moved
        self.run_script('cover_project.py', 'rebuild', '--project', moved, '--set', 'title=Revised', script_dir=moved/'runtime')
        self.run_script('cover_project.py', 'export', '--project', moved, '--platform', 'x',
                        '--platform', 'linkedin-horizontal', script_dir=moved/'runtime')
        child = moved / 'variants/full-cover/x'
        self.run_script('cover_project.py', 'rebuild', '--project', child,
                        '--set', 'title=Approved title', script_dir=child/'runtime')
        self.assertTrue((moved / 'output/final-covers/linkedin-horizontal.webp').exists())
        self.assertEqual(self.load('content.json')['title'], 'Revised')
        for key in ('background', 'font', 'font_bold'):
            self.assertFalse(Path(self.load('content.json')[key]).is_absolute())

    def test_failed_batch_keeps_existing_successful_outputs(self):
        self.full_cover()
        self.run_script('cover_project.py', 'export', '--project', self.project, '--platform', 'x')
        before = (self.project / 'output/final-covers/x.png').read_bytes()
        layouts = (self.project / 'layout/platform-layouts.json').read_bytes()
        self.run_script('cover_project.py', 'rebuild', '--project', self.project, '--set', 'title=Revised')
        result = self.run_script('cover_project.py', 'export', '--project', self.project,
                                 '--platform', 'x', '--platform', 'wechat-square', '--fit', 'cover', success=False)
        self.assertIn('explicit platform template', result.stderr)
        self.assertEqual(before, (self.project / 'output/final-covers/x.png').read_bytes())
        self.assertEqual(layouts, (self.project / 'layout/platform-layouts.json').read_bytes())

    def test_explicit_square_template_renders_layers_in_target_canvas(self):
        self.full_cover()
        layouts = self.load('layout/platform-layouts.json')
        template = self.load('content.json')['template']
        template['canvas'].update(width=1200, height=1200)
        # This test explicitly places the existing slots; it does not crop a final cover.
        for layer in template['layers'].values():
            layer['x'] = round(layer['x'] * .7)
            if 'width' in layer:
                layer['width'] = round(layer['width'] * .7)
        layouts['variants']['wechat-square'] = {'template': template, 'background_fit': 'cover'}
        (self.project / 'layout/platform-layouts.json').write_text(json.dumps(layouts))
        self.run_script('cover_project.py', 'export', '--project', self.project, '--platform', 'wechat-square')
        with Image.open(self.project / 'output/final-covers/wechat-square.png') as image:
            self.assertEqual(image.size, (1200, 1200))
        child = self.load('variants/full-cover/wechat-square/content.json')
        self.assertEqual(child['template']['canvas']['height'], 1200)
        self.assertEqual(child['title'], 'Approved title')
        self.assertEqual(child['size'], [1200, 1200])

    def test_background_export_cannot_overwrite_full_cover_child(self):
        self.full_cover()
        self.run_script('cover_project.py', 'export', '--project', self.project, '--platform', 'x')
        child = self.project / 'variants/full-cover/x/content.json'
        before = child.read_bytes()
        self.run_script('cover_project.py', 'export', '--project', self.project, '--platform', 'x', '--mode', 'background-only')
        self.assertEqual(before, child.read_bytes())
        self.assertEqual(self.load('variants/background-only/x/project.json')['mode'], 'background-only')

    def test_no_implicit_background_crop_and_explicit_crop_keeps_master(self):
        self.run_script('cover_project.py', 'background', '--project', self.project,
                        '--background', self.background, '--confirm-clean')
        master = self.project / self.load('project.json')['background']['master']
        before = master.read_bytes()
        self.run_script('cover_project.py', 'export', '--project', self.project, '--platform', 'wechat-square', success=False)
        self.run_script('cover_project.py', 'export', '--project', self.project,
                        '--platform', 'wechat-square', '--fit', 'cover')
        self.assertEqual(master.read_bytes(), before)
        with Image.open(self.project / 'output/background-only/wechat-square.png') as image:
            self.assertEqual(image.size, (1200, 1200))

    def test_same_ratio_layout_scaling_includes_local_edits(self):
        self.full_cover()
        content = self.load('content.json')
        content['layer_overrides']['main-title'] = {'x': 120}
        result = scaled_config(content, [800, 450])
        self.assertEqual(result['layer_overrides']['main-title']['x'], 60)
        self.assertEqual(result['template']['layers']['main-title']['width'], round(835*.5))
        self.assertEqual(content['template']['canvas']['width'], 1600)

    def test_scaled_summary_keeps_editable_section_pattern(self):
        content = {'layout': 'seminar-summary', 'size': [1200, 1600],
                   'sections': [{'body': 'First'}, {'body': 'Second'}]}
        original = resolve_template(content, 'seminar-summary', (1200, 1600))
        first = content['sections'][0]['id']
        result = scaled_config(content, [600, 800])
        layers = resolve_template(result, 'seminar-summary', (600, 800))
        self.assertEqual(layers[first + '-body']['y'], round(original[first + '-body']['y'] * .5))
        result['sections'].append({'body': 'New approved point'})
        layers = resolve_template(result, 'seminar-summary', (600, 800))
        self.assertIn(result['sections'][-1]['id'] + '-body', layers)

    def test_replacement_background_does_not_inherit_old_generation_metadata(self):
        self.full_cover()
        content = self.load('content.json')
        content['background_metadata'] = {'seed': 123, 'prompt': 'Original known prompt'}
        (self.project / 'content.json').write_text(json.dumps(content))
        self.run_script('cover_project.py', 'rebuild', '--project', self.project)
        self.assertEqual(self.load('background/background-config.json')['seed'], 123)
        self.assertNotIn('background_metadata', self.load('content.json'))
        self.run_script('render_cover.py', '--project', self.project, '--background',
                        ROOT / 'assets/backgrounds/hex-glow.png')
        self.assertIsNone(self.load('background/background-config.json')['seed'])
        self.assertIsNone(self.load('background/background-config.json')['prompt'])

    def test_platform_specific_background_has_its_own_provenance(self):
        self.full_cover()
        meta = self.load('background/background-config.json')
        meta.update(seed=123, prompt='Original known prompt')
        (self.project / 'background/background-config.json').write_text(json.dumps(meta))
        layouts = self.load('layout/platform-layouts.json')
        alternate = 'assets/alternate.png'
        shutil.copyfile(ROOT / 'assets/backgrounds/hex-glow.png', self.project / alternate)
        layouts['variants']['x'] = {'background_file': alternate}
        (self.project / 'layout/platform-layouts.json').write_text(json.dumps(layouts))
        self.run_script('cover_project.py', 'export', '--project', self.project, '--platform', 'x')
        variant_meta = self.load('variants/full-cover/x/background/background-config.json')
        self.assertIsNone(variant_meta['seed'])
        self.assertIsNone(variant_meta['prompt'])
        self.assertNotIn('parent_sha256', variant_meta)


if __name__ == '__main__':
    unittest.main()
