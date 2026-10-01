import copy
import json
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from lp_engine.d2c.engine import build, validate


FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures/d2c_melt_skin/production_input.json'
ORIGINAL_HEADLINES = {
    'ingredients': 'シンプルだからこそ、\nひとつずつ丁寧に。',
    'product': '今日の肌に、\n迷わない選択を。',
    'story': '肌に触れる数分を、\n自分へ戻る時間に。',
    'final': '肌を通して、\n自分をもう少し\n好きになれるように。',
}


class HeadlineParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scene = None
        self.heading = False
        self.headlines = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'section':
            self.scene = attrs.get('id')
        if tag == 'h2' and self.scene in ORIGINAL_HEADLINES:
            self.heading = True
            self.headlines[self.scene] = ''

    def handle_endtag(self, tag):
        if tag == 'h2':
            self.heading = False

    def handle_data(self, data):
        if self.heading:
            self.headlines[self.scene] += data


class SemanticHeadlineTest(TestCase):
    def test_chunks_preserve_exact_authored_copy_and_rendered_order(self):
        data = json.loads(FIXTURE.read_text())
        for scene in data['scene_spec']:
            if scene['id'] in ORIGINAL_HEADLINES:
                self.assertEqual(scene['title'], ORIGINAL_HEADLINES[scene['id']])
                self.assertEqual([''.join(line) for line in scene['semantic_lines']], scene['title'].split('\n'))
        with TemporaryDirectory() as directory:
            dist = Path(directory) / 'dist'
            build(FIXTURE, dist)
            html = (dist / 'index.html').read_text()
            parsed = HeadlineParser()
            parsed.feed(html)
            self.assertEqual(parsed.headlines,
                             {scene: title.replace('\n', '') for scene, title in ORIGINAL_HEADLINES.items()})
            self.assertEqual(html.count('class="headline-chunk"'), 16)

    def test_invalid_chunk_must_block_generation(self):
        data = json.loads(FIXTURE.read_text())
        changed = copy.deepcopy(data)
        target = next(s for s in changed['scene_spec'] if s['id'] == 'ingredients')
        target['semantic_lines'][0][1] = 'だからこそ'
        findings = validate(changed, FIXTURE.parent)
        self.assertIn('SEMANTIC_HEADLINE_COPY_MISMATCH', [f['code'] for f in findings])
