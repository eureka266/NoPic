"""Behavioral checks for portable templates and preserving local geometry edits."""
import json
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import template_parameters as templates
from render_speaker_quote import choose_speaker_font


class TemplateSnapshotTests(unittest.TestCase):
    def test_saved_defaults_work_without_the_template_library(self):
        config = {'layout': 'hero'}
        before = templates.resolve_template(config, 'hero', (1600, 900))
        saved = json.loads(json.dumps(config))
        with patch.object(templates, 'load_template', side_effect=AssertionError('Unexpected library read')):
            after = templates.resolve_template(saved, 'hero', (1600, 900))
        self.assertEqual(before, after)
        self.assertEqual(config, saved)

    def test_reordering_sections_keeps_overrides_bound_to_the_same_takeaway(self):
        config = {'sections': [{'heading': 'First', 'body': 'First point'}, {'heading': 'Second', 'body': 'Second point'}]}
        templates.resolve_template(config, 'seminar-summary', (1200, 1600))
        first_id = config['sections'][0]['id']
        templates.resolve_template(config, 'seminar-summary', (1200, 1600), [first_id+'-body.x=120'])
        config['sections'].reverse()
        layers = templates.resolve_template(config, 'seminar-summary', (1200, 1600))
        self.assertEqual(config['sections'][1]['heading'], 'First')
        self.assertEqual(layers[first_id+'-body']['x'], 120)
        self.assertEqual(layers[first_id+'-body']['section_id'], first_id)
        self.assertGreater(layers[first_id+'-body']['y'], layers[config['sections'][0]['id']+'-body']['y'])

    def test_deleting_and_adding_sections_cannot_transfer_an_old_override(self):
        config = {'sections': [{'body': 'Keep'}, {'body': 'Delete'}]}
        templates.resolve_template(config, 'seminar-summary', (1200, 1600))
        deleted_id = config['sections'][1]['id']
        templates.resolve_template(config, 'seminar-summary', (1200, 1600), [deleted_id+'-body.x=120'])
        config['sections'][1] = {'body': 'New'}
        layers = templates.resolve_template(config, 'seminar-summary', (1200, 1600))
        self.assertNotEqual(config['sections'][1]['id'], deleted_id)
        self.assertNotIn(deleted_id+'-body', config['layer_overrides'])
        self.assertEqual(layers[config['sections'][1]['id']+'-body']['x'], 84)

    def test_duplicate_section_ids_are_rejected(self):
        config = {'sections': [{'id': 'risk-monitoring', 'body': 'First'}, {'id': 'risk-monitoring', 'body': 'Second'}]}
        with self.assertRaises(ValueError):
            templates.resolve_template(config, 'seminar-summary', (1200, 1600))

    def test_project_changes_never_modify_shared_defaults(self):
        original = templates.load_template('hero')
        config = {'layout': 'hero'}
        changed = templates.resolve_template(config, 'hero', (1600, 900), ['main-image.x=950'])
        self.assertEqual(changed['main-image']['x'], 950)
        self.assertEqual(config['template']['layers']['main-image']['x'], 1000)
        self.assertEqual(templates.load_template('hero'), original)

    def test_invalid_geometry_and_unknown_layers_are_rejected(self):
        for assignment in ('main-image.x=2000', 'main-image.width=-1', 'main-image.x=NaN',
                           'main-title.font_size_min=100', 'main-title.align=diagonal',
                           'main-title.x=true', 'unknown-person.x=100', 'main-image.asset_field=logo'):
            with self.subTest(assignment=assignment), self.assertRaises(ValueError):
                templates.resolve_template({'layout': 'hero'}, 'hero', (1600, 900), [assignment])


class RenderPersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='blocksec-template-tests-')
        cls.directory = Path(cls.temp.name)
        cls.font = choose_speaker_font('Approved quote “ 中文标题')
        for name, size in [('landscape', (1600, 900)), ('portrait-background', (1200, 1600))]:
            Image.new('RGB', size, '#101923').save(cls.directory / (name+'.png'))
        subject = Image.new('RGBA', (500, 900), (0, 0, 0, 0))
        ImageDraw.Draw(subject).rectangle((30, 30, 470, 870), fill='#C45DCC')
        subject.save(cls.directory / 'subject.png')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def render(self, script, project, flags=(), source=None, success=True):
        command = [sys.executable, str(ROOT/'scripts'/script), '--project', str(project), *flags]
        if source is not None:
            content = project.parent/(project.name+'-source.json')
            content.write_text(json.dumps(source, ensure_ascii=False), encoding='utf-8')
            command += ['--content', str(content)]
        result = subprocess.run(command, capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def speaker_source(self):
        return dict(layout='speaker-quote', background=str(self.directory/'portrait-background.png'),
                    font=self.font, portrait=str(self.directory/'subject.png'),
                    quote='Approved quote', quote_body='Supporting quote',
                    speaker_name='Speaker Name', event='Web3 Seminar')

    def test_minimal_partnership_preserves_geometry_and_packages_separator(self):
        project = self.directory/'minimal-pair'
        logo = self.directory/'test-logo.png'
        partner = self.directory/'test-partner.png'
        # These solid swatches are test fixtures, not official company logos.
        swatch = Image.new('RGBA', (600, 160), (0, 0, 0, 0))
        ImageDraw.Draw(swatch).rectangle((40, 40, 560, 120), fill='#122337')
        swatch.save(logo)
        Image.new('RGBA', (400, 100), '#248BCC').save(partner)
        source = dict(layout='partnership-minimal', logo=str(logo), partner_logo=str(partner))
        self.render('render_cover.py', project,
                    ['--layer', 'partner-logo.x=880'], source)
        saved = json.loads((project/'content.json').read_text())
        self.assertEqual(saved['theme'], 'light')
        self.assertEqual(saved['background_id'], 'partnership-soft-grid')
        self.assertEqual(saved['template_id'], 'partnership-announcement-minimal')
        self.assertTrue((project/saved['separator']).is_file())
        self.assertEqual(saved['template']['layers']['partner-logo']['x'], 920)
        with Image.open(project/'cover.png') as image:
            self.assertLess(image.getpixel((800, 450))[0], 100)
            self.assertEqual(image.getpixel((880, 450)), (36, 139, 204))
        self.render('render_cover.py', project, ['--asset', 'partner_logo='+str(partner)])
        after = json.loads((project/'content.json').read_text())
        for key in ('layer_overrides', 'template', 'background', 'separator'):
            self.assertEqual(saved[key], after[key])
        self.render('render_cover.py', project, ['--reset-layer', 'partner-logo'])
        reset = json.loads((project/'content.json').read_text())
        self.assertNotIn('partner-logo', reset['layer_overrides'])
        # Project must remain renderable after being separated from bundled defaults/assets.
        detached = self.directory/'minimal-detached-scripts'
        shutil.copytree(project/'runtime', detached)
        result = subprocess.run([sys.executable, str(detached/'render_cover.py'),
                                 '--project', str(project)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        original_config = (project/'content.json').read_bytes()
        original_png = (project/'cover.png').read_bytes()
        for flags in (['--set', 'title=Must not silently disappear'],
                      ['--asset', 'partner_logo='], ['--theme', 'dark'],
                      ['--layer', 'partnership-separator.width=900']):
            self.render('render_cover.py', project, flags, success=False)
            self.assertEqual((project/'content.json').read_bytes(), original_config)
            self.assertEqual((project/'cover.png').read_bytes(), original_png)

    def test_minimal_partnership_orange_variant_uses_registered_background(self):
        project = self.directory/'minimal-orange'
        logo = self.directory/'orange-logo.png'
        partner = self.directory/'orange-partner.png'
        Image.new('RGBA', (500, 140), '#122337').save(logo)
        Image.new('RGBA', (500, 140), '#FF7A1A').save(partner)
        source = dict(layout='partnership-minimal', background_id='partnership-orange-grid',
                      style_variant='warm-orange-grid', logo=str(logo), partner_logo=str(partner))
        self.render('render_cover.py', project, source=source)
        saved = json.loads((project/'content.json').read_text())
        self.assertEqual(saved['background_id'], 'partnership-orange-grid')
        with Image.open(project/'cover.png') as image:
            self.assertEqual(image.size, (1600, 900))
            self.assertGreater(image.getpixel((1500, 80))[0], image.getpixel((800, 450))[0])

    def test_minimal_partnership_missing_or_empty_logo_cannot_create_final_cover(self):
        for label, source in (
            ('missing', dict(layout='partnership-minimal')),
            ('transparent', dict(layout='partnership-minimal',
                                 logo=str(self.directory/'empty-logo.png'),
                                 partner_logo=str(self.directory/'subject.png')))):
            Image.new('RGBA', (100, 100), (0, 0, 0, 0)).save(self.directory/'empty-logo.png')
            project = self.directory/('minimal-'+label)
            self.render('render_cover.py', project, source=source, success=False)
            self.assertFalse((project/'cover.png').exists())

    def test_moving_person_then_editing_copy_preserves_the_rendered_position(self):
        project = self.directory/'speaker'
        self.render('render_speaker_quote.py', project, ['--draft', '--layer', 'speaker-portrait.x=620'], self.speaker_source())
        before = json.loads((project/'content.json').read_text())
        with Image.open(project/'speaker-quote.png') as image:
            self.assertEqual(image.getpixel((660, 1000)), (196, 93, 204))
        self.render('render_speaker_quote.py', project, ['--draft', '--set', 'quote=Approved 中文标题'])
        after = json.loads((project/'content.json').read_text())
        self.assertEqual(before['layer_overrides'], after['layer_overrides'])
        self.assertEqual(before['template'], after['template'])
        self.assertEqual(before['portrait'], after['portrait'])
        self.assertEqual(before['background'], after['background'])
        with Image.open(project/'speaker-quote.png') as image:
            self.assertEqual(image.getpixel((660, 1000)), (196, 93, 204))
        self.render('render_speaker_quote.py', project, ['--draft', '--reset-layer', 'speaker-portrait'])
        reset = json.loads((project/'content.json').read_text())
        self.assertNotIn('speaker-portrait', reset['layer_overrides'])
        with Image.open(project/'speaker-quote.png') as image:
            self.assertEqual(image.getpixel((660, 1000)), (16, 25, 35))

    def test_editing_title_keeps_cover_geometry_and_bad_edits_preserve_files(self):
        project = self.directory/'cover'
        source = dict(layout='hero', title='Approved title', font=self.font,
                      background=str(self.directory/'landscape.png'), image=str(self.directory/'subject.png'))
        self.render('render_cover.py', project, ['--layer', 'main-image.x=950'], source)
        before = json.loads((project/'content.json').read_text())
        with Image.open(project/'cover.png') as image:
            pixels = image.crop((950, 200, 1600, 790)).tobytes()
        self.render('render_cover.py', project, ['--set', 'title=Revised title'])
        after = json.loads((project/'content.json').read_text())
        self.assertEqual(before['layer_overrides'], after['layer_overrides'])
        self.assertEqual(before['template'], after['template'])
        with Image.open(project/'cover.png') as image:
            self.assertEqual(image.crop((950, 200, 1600, 790)).tobytes(), pixels)
        config_bytes = (project/'content.json').read_bytes()
        image_bytes = (project/'cover.png').read_bytes()
        self.render('render_cover.py', project, ['--layer', 'main-image.x=2000'], success=False)
        self.assertEqual((project/'content.json').read_bytes(), config_bytes)
        self.assertEqual((project/'cover.png').read_bytes(), image_bytes)

    def test_legacy_summary_migrates_and_can_render_outside_the_skill_folder(self):
        project = self.directory/'summary'
        source = dict(schema_version=1, layout='seminar-summary', title='Approved summary', font=self.font,
                      background=str(self.directory/'portrait-background.png'),
                      sections=[{'heading': 'First', 'body': 'First point'}, {'body': 'Second point'}])
        self.render('render_speaker_quote.py', project, ['--draft'], source)
        saved = json.loads((project/'content.json').read_text())
        self.assertEqual(saved['schema_version'], 2)
        self.assertEqual(saved['template_id'], 'seminar-summary-portrait')
        self.assertEqual(len({s['id'] for s in saved['sections']}), 2)
        self.assertIn(saved['sections'][0]['id']+'-body', saved['template']['layers'])
        detached = self.directory/'detached-scripts'
        shutil.copytree(project/'runtime', detached)
        result = subprocess.run([sys.executable, str(detached/'render_speaker_quote.py'),
                                 '--project', str(project), '--draft', '--set', 'title=Revised summary'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((project/'content.json').read_text())['template'], saved['template'])


if __name__ == '__main__':
    unittest.main()
