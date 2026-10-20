"""Observable reference intake, file handoff, and AI-result boundaries."""
import base64
from io import BytesIO
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image
from synthetic_pack import make_pack

WORKBENCH = Path(__file__).resolve().parents[1] / 'output/prototypes/cover-workbench'
sys.path.insert(0, str(WORKBENCH))
import server


class BackgroundWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.url = f'http://127.0.0.1:{cls.httpd.server_port}'
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='nopic-background-test-')
        self.addCleanup(self.directory.cleanup)
        server.configure_paths(self.directory.name)
        self.work = server.WORK
        self.enterContext(patch.dict(os.environ, {'NOPIC_BRAND_PACK': ''}))
        server.configure_brand_pack()
        self.addCleanup(server.configure_brand_pack)

    def api(self, path, data=None, status=200, origin=None):
        headers = {'Content-Type': 'application/json'}
        if origin:
            headers['Origin'] = origin
        request = Request(self.url + path, headers=headers,
                          data=json.dumps(data).encode() if data is not None else None)
        try:
            response = urlopen(request)
        except HTTPError as error:
            response = error
        with response:
            body = json.loads(response.read())
            self.assertEqual(response.status, status, body)
            return body

    def upload(self, name='含文字的海报.png', color='orange', category='background-reference'):
        buf = BytesIO()
        Image.new('RGB', (32, 24), color).save(buf, 'PNG')
        raw = buf.getvalue()
        response = self.api('/api/upload', dict(name=name, category=category,
                                               data=base64.b64encode(raw).decode()))
        self.assertEqual((self.work / response['asset']['relative_path']).read_bytes(), raw)
        return response['asset']

    def task(self, **kwargs):
        response = self.api('/api/background-handoff', kwargs)
        receipt = response['handoff']
        task = json.loads((self.work / receipt['json_path']).read_text())
        self.assertEqual(task, json.loads((self.work / 'session-handoffs/latest.json').read_text()))
        self.assertTrue((self.work / receipt['markdown_path']).is_file())
        return receipt, task

    def write_result(self, receipt, **overrides):
        result = dict(task_id=receipt['id'], summary='暖橙柔光', palette='浅橙',
                      material='细网格', lighting='柔和', composition='左侧留白',
                      prompt='暖橙色柔和光影，无字无标志的背景', negative_prompt='文字，Logo，二维码',
                      generated_file=None)
        result.update(overrides)
        (self.work / receipt['result_path']).write_text(json.dumps(result))
        return result

    def test_chat_reference_allows_empty_brief_and_never_changes_selected_background(self):
        before = self.api('/api/state')
        receipt, task = self.task()
        self.assertEqual(task['kind'], 'background-style')
        self.assertEqual(task['request']['intent'], 'analyze')
        self.assertEqual(task['request']['reference_source'], 'chat')
        self.assertEqual(task['references'], [])
        self.assertIn('随本条消息粘贴', receipt['prompt'])
        after = self.api('/api/state')
        for field in ('background', 'mode', 'title', 'preview'):
            self.assertEqual(before[field], after[field])
        self.assertIsNone(self.api('/api/background-result')['result'])
        self.assertFalse((self.work / 'projects').exists())

    def test_panel_uses_only_explicitly_selected_reference_images(self):
        selected = self.upload()
        self.upload('unselected.png', 'blue', 'layout-reference')
        self.upload('logo.png', 'black', 'brand')
        receipt, task = self.task(reference_source='panel', reference_ids=[selected['id']],
                                  brief='保留光感，画面更干净', intent='generate',
                                  aspect_ratio='3:4', text_space='top')
        self.assertEqual([asset['id'] for asset in task['references']], [selected['id']])
        self.assertTrue(task['references'][0]['reference_only'])
        self.assertEqual(task['request']['aspect_ratio'], '3:4')
        self.assertEqual(task['request']['intent'], 'generate')
        self.assertIn('原生图像生成工具', receipt['prompt'])
        self.assertEqual(self.api('/api/state')['background_request'], task['request'])

    def test_invalid_selection_and_options_fail_without_creating_tasks(self):
        logo = self.upload('logo.png', category='brand')
        for data in (dict(reference_source='panel'),
                     dict(reference_source='panel', reference_ids=['missing']),
                     dict(reference_source='panel', reference_ids=[logo['id']]),
                     dict(intent='auto'), dict(aspect_ratio='99:1'),
                     dict(text_space='invalid'), dict(brief=3), dict(brief='a'*6001),
                     dict(reference_ids='not-a-list'), dict(text_space=[]),
                     dict(aspect_ratio={}), ['not-an-object']):
            self.api('/api/background-handoff', data, status=400)
        self.assertFalse((self.work / 'session-handoffs').exists())
        self.assertNotIn('background_request', self.api('/api/state'))

    def test_same_name_different_contents_keeps_both_originals(self):
        one, two = self.upload(), self.upload(color='blue')
        self.assertNotEqual(one['relative_path'], two['relative_path'])
        self.assertTrue((self.work / one['relative_path']).is_file())
        self.assertTrue((self.work / two['relative_path']).is_file())
        self.assertEqual(len(self.api('/api/state')['uploads']), 2)

    def test_missing_reference_file_is_reported(self):
        asset = self.upload()
        (self.work / asset['relative_path']).unlink()
        self.api('/api/background-handoff', dict(reference_source='panel', reference_ids=[asset['id']]), status=400)

    def test_readback_accepts_only_complete_results_for_current_task(self):
        receipt, _ = self.task()
        valid = self.write_result(receipt)
        self.assertEqual(self.api('/api/background-result')['result'], valid)
        self.write_result(receipt, task_id='another-task')
        self.assertIn('error', self.api('/api/background-result')['result'])
        self.write_result(receipt, prompt='')
        self.assertIn('error', self.api('/api/background-result')['result'])
        (self.work / receipt['result_path']).write_text('{unfinished')
        self.assertIn('error', self.api('/api/background-result')['result'])
        new, _ = self.task(intent='generate')
        self.assertNotEqual(receipt['id'], new['id'])
        self.assertIsNone(self.api('/api/background-result')['result'])

    def test_generated_claim_requires_a_real_image_inside_workspace(self):
        receipt, _ = self.task(intent='generate')
        for path in ('../outside.png', 'missing.png', 'not-an-image.png'):
            (self.work / 'not-an-image.png').write_text('not a generated image')
            self.write_result(receipt, generated_file=path)
            self.assertIn('error', self.api('/api/background-result')['result'])
        image = self.work / 'generated.png'
        Image.new('RGB', (24, 32)).save(image)
        self.write_result(receipt, generated_file='generated.png')
        self.assertEqual(self.api('/api/background-result')['result']['generated_file'], 'generated.png')

    def test_fresh_workspaces_do_not_inherit_each_others_uploads(self):
        self.upload()
        server.configure_paths(Path(self.directory.name) / 'another-project')
        self.assertEqual(self.api('/api/state')['uploads'], [])

    def test_cross_origin_cannot_create_background_tasks(self):
        self.api('/api/background-handoff', {}, status=403, origin='https://example.org')
        self.assertFalse((self.work / 'session-handoffs').exists())

    def test_general_handoff_and_motion_requests_still_work(self):
        self.api('/api/session-handoff', dict(instruction='继续制作'))
        self.assertIsNone(self.api('/api/background-result')['result'])
        request = self.api('/api/request', dict(kind='motion', brief='慢慢动起来'))
        self.assertFalse(request['executed'])
        self.assertTrue(Path(request['path']).exists())


    def test_pack_root_change_invalidates_preview_even_with_the_same_version(self):
        first = make_pack(self.work.parent/'first-pack')
        second = make_pack(self.work.parent/'second-pack')
        server.configure_brand_pack(first)
        before = self.api('/api/render', {'mode': 'background'})
        self.assertTrue(before['preview'])
        server.configure_brand_pack(second)
        state = self.api('/api/state')
        self.assertIsNone(state['preview'])
        after = self.api('/api/render', {'mode': 'background'})
        self.assertNotEqual(before['render_key'], after['render_key'])

    def test_no_pack_has_no_implicit_background_template_or_preview(self):
        state = self.api('/api/state')
        self.assertIsNone(state['brand_pack'])
        self.assertIsNone(state['background'])
        self.assertIsNone(state['template'])
        self.assertIsNone(state['preview'])
        self.assertEqual(server.BG, {})
        self.assertEqual(server.TEMPLATES, {})
        result = self.api('/api/render', {}, status=400)
        self.assertIn('error', result)
        self.assertFalse((self.work/'projects').exists())
        asset = self.upload('test-only-input.png')
        receipt, task = self.task(reference_source='panel', reference_ids=[asset['id']])
        self.assertEqual(task['references'][0]['id'], asset['id'])
        self.assertTrue(receipt['id'])
        self.api('/api/session-handoff', {'instruction': 'Test-only empty-state handoff'})

    def test_empty_background_pack_still_allows_upload_and_handoff(self):
        pack = make_pack(Path(self.directory.name)/'empty-test-pack', backgrounds=False)
        server.configure_brand_pack(pack)
        state = self.api('/api/state')
        self.assertEqual(state['brand_pack']['id'], 'test-only-pack')
        self.assertEqual(state['brand_pack']['backgrounds'], [])
        self.assertIsNone(state['background'])
        self.assertEqual(server.BG, {})
        self.api('/api/render', {}, status=400)
        self.assertFalse((self.work/'projects').exists())
        asset = self.upload('test-only-reference.png')
        _, task = self.task(reference_source='panel', reference_ids=[asset['id']])
        self.assertEqual(task['references'][0]['id'], asset['id'])
        self.api('/api/session-handoff', {'instruction': 'Test-only empty-pack handoff'})

    def test_pack_state_uses_only_manifest_assets_and_catalog_templates(self):
        pack = make_pack(Path(self.directory.name)/'loaded-test-pack')
        server.configure_brand_pack(pack)
        state = self.api('/api/state')
        self.assertEqual(set(server.BG), {entry['id'] for entry in
                                       json.loads((pack/'manifest.json').read_text())['backgrounds']})
        self.assertIn(state['background'], server.BG)
        self.assertIn(state['template'], server.TEMPLATES)
        expected = {entry['id'] for entry in json.loads((pack/'templates/index.json').read_text())['templates']}
        self.assertEqual(set(server.TEMPLATES), expected)
        for file in server.BG.values():
            self.assertTrue(file.is_relative_to(pack))
        self.api('/api/render', {'mode': 'background'})
        rendered = self.api('/api/state')
        self.assertIsNotNone(rendered['preview'])


if __name__ == '__main__':
    unittest.main()
