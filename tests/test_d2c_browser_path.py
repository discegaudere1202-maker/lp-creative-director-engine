import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock, patch

from lp_engine.d2c.browser_visual_qa import first_visible_interactive, line_break_risks, run


def fixture(root):
    dist=root/'dist';dist.mkdir()
    (dist/'index.html').write_text('<section class="section" id="hero">Fixture</section>')
    (dist/'production_manifest.json').write_text(json.dumps({'fixture_status':'MOCK','scenes':[{'scene_id':'hero'}]}))
    (dist/'qa_report.json').write_text(json.dumps({'static_gate':'PASS','browser_gate':'NOT_RUN','visual_diff':'NOT_RUN'}))
    return dist


def fake_runtime():
    manager=MagicMock();p=manager.__enter__.return_value
    p.chromium.executable_path='/approved/chromium'
    browser=p.chromium.launch.return_value
    browser.version='test-version'
    browser.new_page.return_value.locator.return_value.count.return_value=1
    return manager,p,browser


class BrowserPathTest(TestCase):
    def test_intermediate_orphan_and_chunk_split_are_detected(self):
        headings=[{'scene':'ingredients','tag':'H2','lines':['シンプルだからこ','そ、','ひとつずつ丁寧','に。'],'split_chunks':[]},
                  {'scene':'story','tag':'H2','lines':['肌に触れる数分','を、','自分へ戻る時間に。'],'split_chunks':[]},
                  {'scene':'final','tag':'H2','lines':['肌を通して、','自分をもう少し','好きになれる','ように。'],'split_chunks':[]}]
        risks=line_break_risks(headings)
        self.assertEqual([(r['scene'],r['line_index'],r['line']) for r in risks],
                         [('ingredients',1,'そ、'),('ingredients',3,'に。'),('story',1,'を、')])
        headings[2]['split_chunks']=['好きになれる']
        self.assertEqual(line_break_risks(headings)[-1]['reason'],'SEMANTIC_CHUNK_SPLIT')
        self.assertEqual(line_break_risks([{'scene':'faq','tag':'H2','lines':['知っておきたい','こと。']}])[0]['reason'],
                         'SHORT_ISOLATED_LINE')

    def test_absent_reference_does_not_prevent_browser_launch_path(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);dist=fixture(root)
            manager,p,_=fake_runtime()
            p.chromium.launch.side_effect=RuntimeError('synthetic browser unavailable')
            with patch('playwright.sync_api.sync_playwright',return_value=manager):
                result=run(dist,None,root/'evidence')
            self.assertEqual(result['browser_gate'],'HOLD')
            self.assertEqual(result['visual_diff'],'HOLD_NO_APPROVED_TARGET')
            self.assertIsNone(result['inputs']['reference_sha256'])
            self.assertEqual(result['blockers'][0]['code'],'BROWSER_LAUNCH_FAILED')

    def test_mobile_navigation_skips_hidden_header_link(self):
        page=MagicMock();hidden,hero=MagicMock(),MagicMock()
        hidden.is_visible.return_value=False
        hero.is_visible.return_value=True;hero.is_enabled.return_value=True
        page.locator.return_value.all.return_value=[hidden,hero]
        self.assertIs(first_visible_interactive(page,'a[href="#concept"]'),hero)
        hidden.is_enabled.assert_not_called()

    def test_width_failure_is_preserved_and_following_width_is_measured(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);dist=fixture(root)
            manager,_,_=fake_runtime()
            def capture(_,__,width,*args,**kwargs):
                if width==320:raise RuntimeError('synthetic layout capture failure')
                return {'scrollWidth':width,'overflow':[],'textClips':[],'lineBreakRisks':[],'console_errors':[],
                        'http_errors':[],'brokenAnchors':[],'overlaps':[],'boundaryOwners':[],
                        'faq_keyboard_expands':True,'navigation_reached_target':True,
                        'images':[],'scenes':[{'id':'hero'}],'animation':'none'}
            with patch('playwright.sync_api.sync_playwright',return_value=manager), patch('lp_engine.d2c.browser_visual_qa.capture',side_effect=capture):
                result=run(dist,None,root/'evidence',Path('/approved/chromium'))
            self.assertEqual(result['browser_gate'],'FAIL')
            self.assertEqual(result['width_results']['320']['status'],'FAIL')
            self.assertEqual(result['width_results']['360']['status'],'MEASURED')
            self.assertEqual(len(result['width_results']),9)
            self.assertEqual(json.loads((root/'evidence'/'browser_qa.json').read_text())['browser_gate'],'FAIL')

    def test_administrator_denial_stops_before_width_loop(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);dist=fixture(root)
            manager,_,browser=fake_runtime()
            browser.new_page.return_value.goto.side_effect=RuntimeError('net::ERR_BLOCKED_BY_ADMINISTRATOR')
            with patch('playwright.sync_api.sync_playwright',return_value=manager), patch('lp_engine.d2c.browser_visual_qa.capture') as capture:
                result=run(dist,None,root/'evidence')
            self.assertEqual(result['browser_gate'],'HOLD')
            self.assertEqual(result['blockers'][0]['code'],'PAGE_LOAD_RESTRICTED')
            self.assertEqual(result['width_results'],{})
            capture.assert_not_called()
