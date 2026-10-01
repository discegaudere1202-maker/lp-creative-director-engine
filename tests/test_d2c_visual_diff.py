from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image, ImageDraw

from lp_engine.d2c.visual_diff import compare


class VisualDiffTest(unittest.TestCase):
    def test_detects_actual_region_change_without_promoting_human_quality(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            a = Image.new('RGB', (120, 90), '#eeeeee')
            b = a.copy()
            ImageDraw.Draw(b).rectangle((20, 15, 80, 60), fill='#111111')
            a.save(root/'expected.png');b.save(root/'actual.png')
            result=compare(root/'expected.png',root/'actual.png',root/'out',
                           viewport={'width':390,'height':844,'dpr':1},target_status='SYNTHETIC_ONLY')
            self.assertEqual(result['status'],'MEASURED')
            self.assertGreater(result['pixel_mae'],.1)
            self.assertGreater(result['perceptual_blur_mae'],.04)
            self.assertEqual(result['human_visible_quality'],'PENDING_SHUN_REVIEW')
            self.assertTrue((root/'out'/'diff.png').is_file())
            self.assertTrue((root/'out'/'side-by-side.jpg').is_file())

    def test_refuses_silent_resize(self):
        with TemporaryDirectory() as directory:
            root=Path(directory)
            Image.new('RGB',(120,90)).save(root/'expected.png')
            Image.new('RGB',(121,90)).save(root/'actual.png')
            result=compare(root/'expected.png',root/'actual.png',root/'out',
                           viewport={'width':1440,'height':900,'dpr':1},target_status='SYNTHETIC_ONLY')
            self.assertEqual(result['status'],'GEOMETRY_MISMATCH')
            self.assertNotIn('pixel_mae',result)


if __name__ == '__main__':unittest.main()
