"""Check reminder boundaries and packaging without invoking or publishing a skill."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SOURCE = Path(__file__).resolve().parents[1] / 'scripts/skill_team_update.py'
spec = importlib.util.spec_from_file_location('skill_team_update', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TeamUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        (self.root / 'SKILL.md').write_text('original skill')
        (self.root / 'assets').mkdir()
        (self.root / 'assets/background.png').write_bytes(b'approved asset')

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

    def test_deleted_shared_asset_is_detected(self):
        self.start()
        (self.root / 'assets/background.png').unlink()
        result = module.handle_hook(self.root, self.event('Stop'))
        self.assertIn('assets/background.png', result['reason'])

    def test_package_excludes_private_files_and_external_symlinks(self):
        intake = self.root / 'inbox/materials'
        intake.mkdir(parents=True)
        (intake / 'README.md').write_text('intake instructions')
        (intake / 'private.png').write_bytes(b'private material')
        external = self.root / 'private-outside-assets.txt'
        external.write_text('sensitive local content')
        (self.root / 'assets/external-link.txt').symlink_to(external)
        report = module.prepare_package(self.root)
        with zipfile.ZipFile(report['archive']) as archive:
            names = archive.namelist()
            self.assertIn('blocksec-social-cover/SKILL.md', names)
            self.assertIn('blocksec-social-cover/assets/background.png', names)
            self.assertIn('blocksec-social-cover/inbox/materials/README.md', names)
            self.assertFalse(any('private' in name or 'external-link' in name for name in names))
        manifest = json.loads(Path(report['manifest']).read_text())
        self.assertFalse(manifest['uploaded'])
        self.assertEqual(len(names), manifest['file_count'])

    def test_changed_snapshot_cannot_be_published_as_old_revision(self):
        old = module.snapshot(self.root)
        (self.root / 'SKILL.md').write_text('different content')
        with self.assertRaises(ValueError):
            module.prepare_package(self.root, expected=old)

    def test_package_keeps_readme_assets_and_prototype_without_runtime_files(self):
        public = ('requirements.txt', 'docs/release.md', 'docs/assets/workbench.jpg',
                  'output/prototypes/cover-workbench/server.py',
                  'output/prototypes/cover-workbench/demo-assets/cover.png')
        private = ('output/prototypes/cover-workbench/workspace/uploads/photo.png',
                   'output/prototypes/cover-workbench/.venv/bin/python',
                   'output/prototypes/cover-workbench/preview-wide.png',
                   'docs/.venv-docs/private.txt')
        for relative in public + private:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'fixture')
        report = module.prepare_package(self.root)
        with zipfile.ZipFile(report['archive']) as archive:
            names = set(archive.namelist())
        self.assertTrue(all('blocksec-social-cover/' + name in names for name in public))
        self.assertFalse(any('blocksec-social-cover/' + name in names for name in private))


if __name__ == '__main__':
    unittest.main()
