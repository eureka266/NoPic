"""Check reminder boundaries and packaging without invoking or publishing a skill."""
import importlib.util
import json
from pathlib import Path
import tempfile
import sys
import unittest
import zipfile

SOURCE = Path(__file__).resolve().parents[1] / 'scripts/skill_team_update.py'
sys.path.insert(0, str(SOURCE.parent))
spec = importlib.util.spec_from_file_location('skill_team_update', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TeamUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        (self.root / 'SKILL.md').write_text('original skill')
        (self.root / 'schemas').mkdir()
        (self.root / 'schemas/test-only.schema.json').write_text('{"description": "test-only protocol"}')

    def event(self, kind, **extra):
        return {'hook_event_name': kind, 'session_id': 'test-session',
                'cwd': str(self.root), **extra}

    def start(self):
        return module.handle_hook(self.root, self.event('UserPromptSubmit'))

    def test_read_only_turn_does_not_prompt(self):
        self.start()
        self.assertEqual({}, module.handle_hook(self.root, self.event('Stop')))

    def test_generated_files_and_intake_do_not_prompt(self):
        self.start()
        for relative in ('inbox/materials/private-photo.png', 'outputs/post.png'):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b'private output')
        self.assertEqual({}, module.handle_hook(self.root, self.event('Stop')))

    def test_maintenance_prepares_package_then_prompts_once(self):
        self.start()
        (self.root / 'SKILL.md').write_text('maintained skill')
        result = module.handle_hook(self.root, self.event('Stop'))
        self.assertEqual('block', result['decision'])
        self.assertIn(module.QUESTION, result['reason'])
        self.assertEqual(1, len(list((self.root / 'exports').rglob('*.zip'))))
        self.assertEqual({}, module.handle_hook(self.root, self.event('Stop')))

    def test_stop_continuation_does_not_loop(self):
        self.start()
        (self.root / 'SKILL.md').write_text('new version')
        self.assertEqual({}, module.handle_hook(self.root, self.event('Stop', stop_hook_active=True)))

    def test_other_project_is_ignored(self):
        event = self.event('UserPromptSubmit', cwd=str(self.root.parent))
        self.assertEqual({}, module.handle_hook(self.root, event))
        self.assertFalse((self.root / '.codex').exists())

    def test_existing_confirmation_is_not_repeated(self):
        self.start()
        (self.root / 'SKILL.md').write_text('new version')
        self.assertEqual({}, module.handle_hook(self.root, self.event('Stop', last_assistant_message=module.QUESTION)))

    def test_deleted_shared_schema_is_detected(self):
        self.start()
        (self.root / 'schemas/test-only.schema.json').unlink()
        result = module.handle_hook(self.root, self.event('Stop'))
        self.assertIn('schemas/test-only.schema.json', result['reason'])

    def test_package_excludes_private_files_and_external_symlinks(self):
        intake = self.root / 'inbox/materials'
        intake.mkdir(parents=True)
        (intake / 'README.md').write_text('intake instructions')
        (intake / 'private.png').write_bytes(b'private material')
        external = self.root / 'private-outside-assets.txt'
        external.write_text('sensitive local content')
        (self.root / 'schemas/external-link.txt').symlink_to(external)
        report = module.prepare_package(self.root)
        with zipfile.ZipFile(report['archive']) as archive:
            names = archive.namelist()
            self.assertIn('nopic/SKILL.md', names)
            self.assertIn('nopic/schemas/test-only.schema.json', names)
            self.assertIn('nopic/inbox/materials/README.md', names)
            self.assertFalse(any('private' in name or 'external-link' in name for name in names))
        manifest = json.loads(Path(report['manifest']).read_text())
        self.assertFalse(manifest['uploaded'])
        self.assertEqual(len(names), manifest['file_count'])

    def test_nested_quality_skill_is_complete_in_team_package(self):
        public = ('skills/nopic-design-quality/SKILL.md',
                  'skills/nopic-design-quality/NOTICE.md',
                  'skills/nopic-design-quality/references/design-baseline.md',
                  'skills/nopic-design-quality/references/quality-lenses.md',
                  'skills/nopic-design-quality/references/test-only-protocol.json',
                  'skills/nopic-design-quality/evals/cases.json')
        for relative in public:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{"description": "public test-only protocol"}' if path.suffix == '.json' else 'public skill resource')
        private_files = ('skills/nopic-design-quality/.venv/private.txt',
                         'skills/nopic-design-quality/.env',
                         'skills/nopic-design-quality/.env.production',
                         'skills/nopic-design-quality/inbox/materials/customer.png',
                         'skills/nopic-design-quality/references/inbox/customer.png',
                         'skills/nopic-design-quality/evals/workspace/customer.json',
                         'skills/nopic-design-quality/references/.env',
                         'skills/nopic-design-quality/assets/credentials.json',
                         'skills/nopic-design-quality/assets/client.key',
                         'skills/nopic-design-quality/local-notes.txt',
                         'skills/nopic-design-quality/assets/test-only-protocol.json',
                         'skills/nopic-design-quality/references/test-only-swatch.png',
                         'skills/nopic-design-quality/references/test-only-mark.svg',
                         'skills/.private/references/customer.png',
                         'skills/workspace/assets/customer.png')
        for relative in private_files:
            private = self.root / relative
            private.parent.mkdir(parents=True, exist_ok=True)
            private.write_text('private material')
        external = self.root / 'private-outside-skill.txt'
        external.write_text('private content')
        (self.root / 'skills/nopic-design-quality/external.txt').symlink_to(external)
        report = module.prepare_package(self.root)
        with zipfile.ZipFile(report['archive']) as archive:
            names = set(archive.namelist())
            self.assertTrue(all('nopic/' + item in names for item in public))
            self.assertFalse(any('private' in item or 'external.txt' in item for item in names))
            self.assertFalse(any('nopic/' + item in names for item in private_files))
        manifest = json.loads(Path(report['manifest']).read_text())
        self.assertTrue(set(private_files).isdisjoint(manifest['files']))
        self.assertIn(public[2], manifest['files'])
        self.assertFalse(manifest['uploaded'])

    def test_changed_snapshot_cannot_be_published_as_old_revision(self):
        old = module.snapshot(self.root)
        (self.root / 'SKILL.md').write_text('different content')
        with self.assertRaises(ValueError):
            module.prepare_package(self.root, expected=old)

    def test_package_keeps_protocols_and_workbench_without_production_assets_or_runtime_files(self):
        public = ('requirements.txt', 'docs/release.md', 'schemas/brand-pack.schema.json',
                  'output/prototypes/cover-workbench/server.py',
                  'output/prototypes/cover-workbench/background_workflow.py')
        private = ('output/prototypes/cover-workbench/demo-assets/content.json',
                  'output/prototypes/cover-workbench/demo-assets/partner-placeholder.png',
                  'output/prototypes/cover-workbench/demo-assets/cover.png',
                   'output/prototypes/cover-workbench/preview.html',
                   'assets/production-background.png',
                   'assets/templates/production.json',
                   'assets/logos/production.png',
                   'output/prototypes/cover-workbench/workspace/uploads/photo.png',
                   'output/prototypes/cover-workbench/.venv/bin/python',
                   'output/prototypes/cover-workbench/preview-wide.png',
                   'docs/.venv-docs/private.txt')
        for relative in public + private:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'{"description":"test-only protocol"}' if path.suffix == '.json' else b'fixture')
        report = module.prepare_package(self.root)
        with zipfile.ZipFile(report['archive']) as archive:
            names = set(archive.namelist())
        self.assertTrue(all('nopic/' + name in names for name in public))
        self.assertFalse(any('nopic/' + name in names for name in private))


    def test_distribution_excludes_media_in_every_public_resource_directory(self):
        extensions = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.mp4', '.mov',
                      '.ttf', '.otf', '.woff', '.woff2', '.svg', '.zip', '.PNG')
        directories = ('docs', 'references', 'scripts', 'schemas', 'tests',
                       'skills/nopic-design-quality/references',
                       'skills/nopic-design-quality/evals')
        media_files = []
        for directory in directories:
            for extension in extensions:
                relative = directory+'/test-only-media'+extension
                path = self.root/relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'TEST ONLY: synthetic excluded media marker')
                media_files.append(relative)
        public = self.root/'skills/nopic-design-quality/references/protocol.json'
        public.write_text('{"description": "TEST ONLY: public protocol"}')
        report = module.prepare_package(self.root)
        with zipfile.ZipFile(report['archive']) as archive:
            names = set(archive.namelist())
        self.assertIn('nopic/skills/nopic-design-quality/references/protocol.json', names)
        self.assertFalse(any('nopic/'+relative in names for relative in media_files))
        self.assertTrue(all(name.startswith('nopic/') for name in names))
        self.assertEqual(Path(report['archive']).name, 'nopic.zip')

    def test_all_resource_roots_exclude_private_text_and_production_json(self):
        private = {'references/.env': 'secret',
                   'references/.nopic/active-brand-pack.json': '{"pack_root":"private"}',
                   'scripts/workspace/workbench-state.json': '{"current_project":"private"}',
                   'references/templates/customer-production.json': '{"canvas":{},"layers":{}}',
                   'schemas/not-a-schema.json': '{"canvas":{},"layers":{}}',
                   'schemas/copied-project.json': '{"mode":"cover","background":{},"content":{},"layouts":{},"renderer":"private","outputs":[]}',
                   'schemas/copied-logo-index.json': '{"logos":[{"file":"private.png"}]}',
                   'schemas/reference-pack.json': '{"id":"private","version":"1","references":[{"file":"customer.png"}]}',
                   'references/session-handoffs/task.md': 'private user request',
                   'references/background-studies/task.md': 'private analysis'}
        for relative, text in private.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        report = module.prepare_package(self.root)
        with zipfile.ZipFile(report['archive']) as archive:
            self.assertTrue(all('nopic/' + path not in archive.namelist() for path in private))
        manifest = json.loads(Path(report['manifest']).read_text())
        self.assertTrue(set(private).isdisjoint(manifest['files']))

    def test_actual_methodology_source_list_contains_protocols_and_no_media(self):
        root = SOURCE.parents[1]
        files = {path.relative_to(root).as_posix() for path in module.source_files(root)}
        self.assertIn('scripts/organization_assets.py', files)
        self.assertTrue(any(name.startswith('schemas/') for name in files))
        self.assertIn('skills/nopic-design-quality/SKILL.md', files)
        forbidden = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.mp4', '.mov',
                     '.ttf', '.otf', '.woff', '.woff2', '.svg', '.zip'}
        self.assertFalse(any(name.startswith(('assets/', 'organization-assets/')) for name in files))
        self.assertFalse(any(Path(name).suffix.lower() in forbidden for name in files))
        self.assertFalse(any('/demo-assets/' in name or name.endswith('/preview.html') for name in files))
        self.assertFalse(any(name.startswith('skills/') and '/assets/' in name for name in files))


if __name__ == '__main__':
    unittest.main()
