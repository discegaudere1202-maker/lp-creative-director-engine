import tempfile
import unittest
from pathlib import Path
import sys

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from lp_engine.rhythm_compare import extract_rhythm_features, compare_rhythm


class RhythmCompareTest(unittest.TestCase):
    def test_alternating_bands_have_more_transition_than_flat(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            flat = td / 'flat.png'
            dynamic = td / 'dynamic.png'

            Image.new('RGB', (400, 2400), (238, 238, 238)).save(flat)
            im = Image.new('RGB', (400, 2400), 'white')
            d = ImageDraw.Draw(im)
            for i in range(12):
                y0 = i * 200
                fill = (25, 25, 25) if i % 2 == 0 else (245, 245, 245)
                d.rectangle([0, y0, 399, y0 + 199], fill=fill)
                if i % 2 == 0:
                    d.rectangle([40, y0 + 40, 360, y0 + 150], outline=(255, 255, 255), width=6)
            im.save(dynamic)

            f = extract_rhythm_features(flat, bands=24)
            g = extract_rhythm_features(dynamic, bands=24)
            self.assertGreater(g.transition_energy, f.transition_energy)
            self.assertGreaterEqual(g.alternation_count, f.alternation_count)

    def test_compare_is_observation_only(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            a = td / 'a.png'
            b = td / 'b.png'
            Image.new('RGB', (200, 1000), 'white').save(a)
            Image.new('RGB', (200, 1000), 'black').save(b)
            result = compare_rhythm(a, b, bands=10)
            self.assertEqual(result['status'], 'OBSERVATION_ONLY')
            self.assertIn('normalized_density_distance', result)


if __name__ == '__main__':
    unittest.main()
