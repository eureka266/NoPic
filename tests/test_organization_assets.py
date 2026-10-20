"""Pack protocol boundaries, installation integrity and test-only resource lookup."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from synthetic_pack import make_pack, write_json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from install_brand_pack import install, validate_manifest
from organization_assets import asset_path, catalog_path, pack_root, read_catalog
from project_assets import catalog_asset
from template_parameters import load_template


class OrganizationAssetsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='nopic-pack-test-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name).resolve()
        self.pack = make_pack(self.directory/'test-only-pack')
        environment = dict(os.environ)
        environment.pop('NOPIC_BRAND_PACK', None)
        self.enterContext(patch.dict(os.environ, environment, clear=True))

    def manifest(self, **updates):
        path = self.pack/'manifest.json'
        value = json.loads(path.read_text())
        value.update(updates)
        write_json(path, value)

    def archive(self, root=None, name='test-only.zip'):
        root = root or self.pack
        archive = self.directory/name
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
            for file in sorted(root.rglob('*')):
                if file.is_file():
                    bundle.write(file, file.relative_to(root))
        return archive

    def test_no_active_pack_is_an_explicit_empty_state(self):
        self.assertIsNone(pack_root(start=self.directory, required=False))
        with self.assertRaisesRegex(ValueError, 'No organization asset pack'):
            pack_root(start=self.directory)
        with self.assertRaisesRegex(ValueError, 'No organization asset pack'):
            load_template('hero', start=self.directory)

    def test_environment_config_and_project_activation_precedence(self):
        other = make_pack(self.directory/'another-test-only-pack')
        project = self.directory/'project'
        write_json(project/'.nopic/active-brand-pack.json', {'pack_root': '../test-only-pack'})
        nested = project/'nested'
        nested.mkdir()
        self.assertEqual(pack_root(start=nested), self.pack)
        with patch.dict(os.environ, {'NOPIC_BRAND_PACK': str(other)}):
            self.assertEqual(pack_root(start=nested), other)
            self.assertEqual(pack_root({'brand_pack': str(self.pack)}, nested), self.pack)

    def test_invalid_explicit_pack_never_falls_back_to_active_project(self):
        write_json(self.directory/'.nopic/active-brand-pack.json', {'pack_root': str(self.pack)})
        with patch.dict(os.environ, {'NOPIC_BRAND_PACK': str(self.directory/'absent')}):
            with self.assertRaisesRegex(ValueError, 'manifest is missing'):
                pack_root(start=self.directory, required=False)

    def test_catalog_and_pack_relative_asset_resolution(self):
        config = {'brand_pack': str(self.pack)}
        self.assertEqual(catalog_path('templates', config), self.pack/'templates/index.json')
        self.assertEqual(read_catalog('templates', config)['templates'][0]['legacy_layout'], 'hero')
        self.assertEqual(asset_path('assets/marks/test-logo.png', config), self.pack/'assets/marks/test-logo.png')
        self.assertEqual(catalog_asset('hero.json', 'templates', config), self.pack/'templates/hero.json')
        self.assertEqual(load_template('hero', config)['display_name'], 'TEST ONLY: hero')

    def test_pack_can_declare_only_the_catalogs_it_uses(self):
        minimal = make_pack(self.directory/'minimal', catalogs=['templates'])
        self.assertEqual(validate_manifest(minimal)['catalogs'], {'templates': 'templates/index.json'})
        self.assertEqual(load_template('hero', {'brand_pack': str(minimal)})['legacy_layout'], 'hero')
        with self.assertRaisesRegex(ValueError, 'does not declare catalog'):
            catalog_path('backgrounds', {'brand_pack': str(minimal)})

    def test_empty_background_catalog_is_valid(self):
        empty = make_pack(self.directory/'empty', backgrounds=False)
        manifest = validate_manifest(empty)
        self.assertEqual(manifest['backgrounds'], [])
        self.assertEqual(read_catalog('backgrounds', {'brand_pack': str(empty)})['presets'], {})

    def test_catalog_paths_cannot_escape_pack(self):
        outside = self.directory/'outside.json'
        write_json(outside, {'templates': []})
        for relative in ('../outside.json', str(outside)):
            with self.subTest(relative=relative):
                self.manifest(catalogs={'templates': relative})
                with self.assertRaises(ValueError):
                    catalog_path('templates', {'brand_pack': str(self.pack)})
                with self.assertRaises(ValueError):
                    validate_manifest(self.pack)
        (self.pack/'linked.json').symlink_to(outside)
        self.manifest(catalogs={'templates': 'linked.json'})
        with self.assertRaises(ValueError):
            catalog_path('templates', {'brand_pack': str(self.pack)})
        with self.assertRaises(ValueError):
            validate_manifest(self.pack)

    def test_template_catalog_paths_cannot_escape_pack(self):
        outside = self.directory/'outside-template.json'
        write_json(outside, {'test_only': True})
        config = {'brand_pack': str(self.pack)}
        (self.pack/'templates/linked.json').symlink_to(outside)
        for relative in ('../../outside-template.json', str(outside), 'linked.json'):
            with self.subTest(relative=relative):
                write_json(self.pack/'templates/index.json', {
                    'templates': [dict(id='external-test', legacy_layout='hero', file=relative)]})
                with self.assertRaises(ValueError):
                    validate_manifest(self.pack)
                with self.assertRaises(ValueError):
                    load_template('hero', config)

    def test_asset_paths_reject_absolute_traversal_and_symlink_escape(self):
        outside = self.directory/'outside.png'
        outside.write_bytes(b'test-only external content')
        (self.pack/'linked.png').symlink_to(outside)
        for relative in ('../outside.png', str(outside), 'linked.png', 'missing.png'):
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                asset_path(relative, {'brand_pack': str(self.pack)})

    def test_manifest_requires_every_catalog_template_and_declared_file(self):
        required = ['catalogs/backgrounds.json', 'templates/hero.json',
                    'assets/marks/test-separator.png', 'assets/marks/test-logo.png']
        for relative in required:
            with self.subTest(relative=relative):
                path = self.pack/relative
                data = path.read_bytes()
                path.unlink()
                try:
                    with self.assertRaises(ValueError):
                        validate_manifest(self.pack)
                finally:
                    path.write_bytes(data)

    def test_manifest_validates_explicit_templates_and_files(self):
        for section, value in (('templates', [{'id': 'test-template', 'file': '../outside.json'}]),
                               ('templates', [{'file': 'absent.json'}]),
                               ('files', ['../outside.json']), ('files', ['absent.txt']),
                               ('files', {}), ('catalogs', [])):
            original = (self.pack/'manifest.json').read_bytes()
            with self.subTest(section=section, value=value):
                self.manifest(**{section: value})
                try:
                    with self.assertRaises(ValueError):
                        validate_manifest(self.pack)
                finally:
                    (self.pack/'manifest.json').write_bytes(original)

    def test_install_retains_all_catalogs_templates_and_declared_files(self):
        source = self.archive()
        target = self.directory/'project'
        receipt = install(source, target)
        installed = Path(receipt['pack_root'])
        manifest = validate_manifest(self.pack)
        for relative in ['manifest.json', *manifest['_validated_files']]:
            self.assertEqual((installed/relative).read_bytes(), (self.pack/relative).read_bytes(), relative)
        self.assertFalse(receipt['reused'])
        self.assertEqual(pack_root(start=target), installed)
        self.assertTrue(install(source, target)['reused'])

    def test_same_version_changes_in_manifest_catalog_template_or_asset_conflict(self):
        project = self.directory/'project'
        first = install(self.archive(), project)
        active_path = Path(first['active_config'])
        active_bytes = active_path.read_bytes()
        installed = Path(first['pack_root'])
        before = {str(p.relative_to(installed)): p.read_bytes() for p in installed.rglob('*') if p.is_file()}
        mutations = {
            'manifest.json': lambda data: json.dumps({**json.loads(data), 'display_name': 'TEST ONLY changed'}).encode(),
            'catalogs/backgrounds.json': lambda data: json.dumps({**json.loads(data), 'test_only_note': 'changed'}).encode(),
            'templates/hero.json': lambda data: json.dumps({**json.loads(data), 'display_name': 'TEST ONLY revised'}).encode(),
            'assets/marks/test-logo.png': lambda data: data+b'test-only-changed-bytes',
            'TEST-ONLY.txt': lambda data: data+b'changed',
        }
        for relative, mutate in mutations.items():
            path = self.pack/relative
            original = path.read_bytes()
            with self.subTest(relative=relative):
                path.write_bytes(mutate(original))
                try:
                    with self.assertRaisesRegex(ValueError, 'different contents'):
                        install(self.archive(name='changed.zip'), project)
                    self.assertEqual(active_path.read_bytes(), active_bytes)
                    self.assertEqual({str(p.relative_to(installed)): p.read_bytes()
                                      for p in installed.rglob('*') if p.is_file()}, before)
                finally:
                    path.write_bytes(original)

    def test_incomplete_install_never_activates_project(self):
        (self.pack/'templates/hero.json').unlink()
        project = self.directory/'uninitialized'
        with self.assertRaises(ValueError):
            install(self.archive(), project)
        self.assertFalse((project/'.nopic/active-brand-pack.json').exists())
        self.assertFalse((project/'.nopic/brand-packs').exists())

    def test_create_archive_includes_catalog_referenced_templates(self):
        output = self.directory/'created.zip'
        result = subprocess.run([sys.executable, str(ROOT/'scripts/create_brand_pack.py'),
                                 str(self.pack), str(output)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = set(validate_manifest(self.pack)['_validated_files']) | {'manifest.json'}
        with zipfile.ZipFile(output) as bundle:
            self.assertEqual(set(bundle.namelist()), expected)
            self.assertEqual(bundle.read('templates/hero.json'), (self.pack/'templates/hero.json').read_bytes())

    def test_builder_rejects_external_manifest_and_readme_symlinks(self):
        for name in ('manifest.json', 'README.md'):
            with self.subTest(name=name):
                path = self.pack / name
                original = path.read_bytes() if path.exists() else None
                outside = self.directory / ('outside-' + name)
                outside.write_bytes(original or b'private outside text')
                path.unlink(missing_ok=True)
                path.symlink_to(outside)
                try:
                    output = self.directory / ('unsafe-' + name + '.zip')
                    result = subprocess.run([sys.executable, str(ROOT/'scripts/create_brand_pack.py'),
                                             str(self.pack), str(output)], capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(output.exists())
                finally:
                    path.unlink()
                    if original is not None:
                        path.write_bytes(original)

    def test_readme_participates_in_version_identity_and_unlisted_files_are_not_installed(self):
        (self.pack/'README.md').write_text('approved pack guidance')
        (self.pack/'unlisted-private.txt').write_text('not a declared resource')
        project = self.directory/'readme-project'
        first = install(self.archive(), project)
        installed = Path(first['pack_root'])
        self.assertEqual((installed/'README.md').read_text(), 'approved pack guidance')
        self.assertFalse((installed/'unlisted-private.txt').exists())
        (self.pack/'README.md').write_text('different same-version guidance')
        with self.assertRaisesRegex(ValueError, 'different contents'):
            install(self.archive(name='readme-changed.zip'), project)
        self.assertEqual((installed/'README.md').read_text(), 'approved pack guidance')

    def test_template_resolution_cannot_be_shadowed_by_root_file(self):
        (self.pack/'hero.json').write_text('{"id":"wrong-root-template"}')
        with patch.dict(os.environ, {'NOPIC_BRAND_PACK': str(self.pack)}):
            template = load_template('hero')
        self.assertNotEqual(template['id'], 'wrong-root-template')
        self.assertEqual(template, json.loads((self.pack/'templates/hero.json').read_text()))

    def test_archive_traversal_and_symlinks_are_rejected(self):
        for kind in ('traversal', 'symlink'):
            output = self.directory/(kind+'.zip')
            with zipfile.ZipFile(output, 'w') as bundle:
                if kind == 'traversal':
                    bundle.writestr('../escaped.txt', 'test-only')
                else:
                    member = zipfile.ZipInfo('linked')
                    member.create_system = 3
                    member.external_attr = 0o120777 << 16
                    bundle.writestr(member, '../outside')
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                install(output, self.directory/'target')
        self.assertFalse((self.directory/'escaped.txt').exists())


if __name__ == '__main__':
    unittest.main()
