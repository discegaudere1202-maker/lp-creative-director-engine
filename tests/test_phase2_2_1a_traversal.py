import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from capture_phase2_2_1a_replacements import traverse

class Page:
    def __init__(self,locked=False,growing=False):self.y=0;self.h=2000;self.locked=locked;self.growing=growing;self.samples=0
    def wait_for_timeout(self,n):pass
    def evaluate(self,code,arg=None):
        if code.startswith('y=>'):
            if not self.locked:self.y=min(arg,self.h-1000)
        elif '({scroll_y:' in code:
            self.samples+=1
            if self.growing and self.samples==3:self.h+=50
            return {'scroll_y':self.y,'document_height':self.h,'viewport_height':1000}
        elif code=='document.documentElement.scrollHeight':return self.h
        elif 'scrollTo(0,0)' in code:self.y=0
        else:raise AssertionError(code)

class TraversalTests(unittest.TestCase):
    def test_records_actual_clamped_position(self):
        r=traverse(Page());self.assertTrue(r['complete_to_bottom']);self.assertEqual(r['scroll_samples'][-1]['scroll_y'],1000)
    def test_scroll_locked_body_fails(self):self.assertFalse(traverse(Page(locked=True))['complete_to_bottom'])
    def test_late_height_growth_requires_new_bottom(self):
        r=traverse(Page(growing=True));self.assertTrue(r['complete_to_bottom']);self.assertEqual(r['final_height'],2050);self.assertEqual(r['scroll_samples'][-1]['scroll_y'],1050)

if __name__=='__main__':unittest.main()
