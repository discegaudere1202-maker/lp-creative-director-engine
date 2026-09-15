import tempfile
import unittest
from pathlib import Path
import sys
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from lp_engine.visual_metrics import analyze_regions


class RegionMetricsTest(unittest.TestCase):
    def test_region_metrics_identify_density_change(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'sample.png'
            im = Image.new('RGB', (400, 1200), 'white')
            d = ImageDraw.Draw(im)
            for y in range(0, 560, 20):
                d.line((0, y, 399, y), fill='black', width=4)
            im.save(p)
            data = analyze_regions(p, [
                {'id':'dense', 'y_start_ratio':0.0, 'y_end_ratio':0.5},
                {'id':'quiet', 'y_start_ratio':0.5, 'y_end_ratio':1.0},
            ])
            rows = {x['id']:x for x in data['regions']}
            self.assertGreater(rows['dense']['edge_mean'], rows['quiet']['edge_mean'])
            self.assertGreater(rows['quiet']['quiet_score'], rows['dense']['quiet_score'])
            self.assertEqual(data['summary']['region_count'], 2)


if __name__ == '__main__':
    unittest.main()
