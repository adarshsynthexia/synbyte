"""Offline checks; no Flask required. Run with Python."""
import unittest,ast,re,hashlib
from pathlib import Path
from jinja2 import Environment,FileSystemLoader
P=Path(__file__).resolve().parents[1]
class Structure(unittest.TestCase):
 def test_templates(self):
  e=Environment(loader=FileSystemLoader(str(P/'templates')))
  for f in (P/'templates').glob('*.html'):e.parse(f.read_text(encoding='utf8'))
  self.assertGreaterEqual(len(list((P/'templates').glob('*.html'))),40)
 def test_page_gate_and_brand(self):
  t=(P/'templates/index.html').read_text(encoding='utf8')
  self.assertIn('SYNBYTE',t)
  self.assertIn('SYNTHEXIA GROUP',t)
  for bad in ('_food-card.html','featured=','A taste of','card(food','Margherita Pizza','my orders'):
   self.assertNotIn(bad,t)
  code=(P/'app.py').read_text(encoding='utf8')
  self.assertRegex(code,r"@app\.get\('/menu'\)\s+@require\('student'\)")
  self.assertRegex(code,r"@app\.get\('/food/<int:food_id>'\)\s+@require\('student'\)")
 def test_images_and_catalogue(self):
  import json
  sources=json.loads((P/'PHOTO_MANIFEST.json').read_text())
  self.assertEqual(len(sources),32)
  self.assertEqual(len({r['url'] for r in sources}),32)
  s=(P/'app.py').read_text(); a=ast.parse(s)
  nodes=[x for x in a.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CATALOG' for t in x.targets)]
  values=ast.literal_eval(nodes[0].value)
  self.assertEqual(len(values),32)
 def test_separate_required_pages(self):
  for f in ['index','role-selection','student-login','vendor-login','food-menu','cart','checkout','payment','payment-result','pickup-token','order-tracking','my-orders','vendor-dashboard','vendor-orders','vendor-kitchen','vendor-verify-token']:
   self.assertTrue((P/'templates'/(f+'.html')).is_file(),f)
 def test_launcher(self):self.assertTrue((P/'START_SYNBYTE.bat').exists())
if __name__=='__main__':unittest.main()
