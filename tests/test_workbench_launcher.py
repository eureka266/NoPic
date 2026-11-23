"""A launcher must never borrow another project's organization or workspace."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import start_workbench
from synthetic_pack import make_pack
from install_brand_pack import validate_manifest, pack_fingerprint


class WorkbenchLauncherTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='nopic-launch-test-')
        self.addCleanup(self.directory.cleanup)
        self.project = Path(self.directory.name).resolve() / 'project'
        self.project.mkdir()
        self.argv = ['start_workbench.py', '--project-root', str(self.project), '--port', '59180']

    def test_reuses_only_matching_project_and_empty_pack(self):
        existing = {'workspace': str(self.project / '.nopic/workspace'), 'brand_pack': None}
        output = StringIO()
        with patch.object(sys, 'argv', self.argv), \
                patch.object(start_workbench, 'discover_project_root') as discover, \
                patch.object(start_workbench, 'active_brand_pack', return_value=None), \
                patch.object(start_workbench, 'workbench_state', return_value=existing), \
                patch.object(start_workbench.subprocess, 'Popen') as spawn, redirect_stdout(output):
            self.assertEqual(start_workbench.main(), 0)
        discover.assert_not_called()
        spawn.assert_not_called()
        receipt = json.loads(output.getvalue())
        self.assertEqual(receipt['project_root'], str(self.project))
        self.assertTrue(receipt['reused'])

    def test_does_not_reuse_a_foreign_project_or_stop_its_process(self):
        existing = {'workspace': str(self.project.parent / 'other/.nopic/workspace'), 'brand_pack': None}
        with patch.object(sys, 'argv', self.argv), \
                patch.object(start_workbench, 'active_brand_pack', return_value=None), \
                patch.object(start_workbench, 'workbench_state', return_value=existing), \
                patch.object(start_workbench, 'port_is_open', return_value=True), \
                patch.object(start_workbench, 'stop_process') as stop:
            with self.assertRaisesRegex(RuntimeError, '端口'):
                start_workbench.main()
        stop.assert_not_called()

    def test_same_version_at_a_different_root_does_not_reuse_the_service(self):
        pack = make_pack(self.project.parent/'new-pack')
        manifest = validate_manifest(pack)
        existing = {'workspace': str(self.project / '.nopic/workspace'),
                    'brand_pack': {'id': manifest['id'], 'version': manifest['version'],
                                   'root': str(self.project.parent/'old-pack'),
                                   'content_fingerprint': pack_fingerprint(pack, manifest)}}
        with patch.object(sys, 'argv', self.argv), \
                patch.object(start_workbench, 'active_brand_pack', return_value=pack), \
                patch.object(start_workbench, 'workbench_state', return_value=existing), \
                patch.object(start_workbench, 'port_is_open', return_value=True):
            with self.assertRaisesRegex(RuntimeError, '端口'):
                start_workbench.main()

    def test_missing_active_pack_does_not_reuse_a_previously_loaded_pack(self):
        existing = {'workspace': str(self.project / '.nopic/workspace'),
                    'brand_pack': {'id': 'previous-team', 'version': '1.0'}}
        with patch.object(sys, 'argv', self.argv), \
                patch.object(start_workbench, 'active_brand_pack', return_value=None), \
                patch.object(start_workbench, 'workbench_state', return_value=existing), \
                patch.object(start_workbench, 'port_is_open', return_value=True):
            with self.assertRaisesRegex(RuntimeError, '端口'):
                start_workbench.main()


if __name__ == '__main__':
    unittest.main()
