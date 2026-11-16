"""Offline assertions for SYNBYTE premium branding, login layout and vendor query."""
import unittest
from pathlib import Path
from jinja2 import Environment,FileSystemLoader
P=Path(__file__).resolve().parents[1]
class BrandingPolish(unittest.TestCase):
 def test_matching_login_panels(self):
  t=P/'templates';e=Environment(loader=FileSystemLoader(str(t)))
  self.assertTrue((t/'_premium-auth-art.html').exists())
  for role in ('student','vendor','admin'):
   s=(t/(role+'-login.html')).read_text()
   self.assertIn("include '_premium-auth-art.html'",s)
   self.assertIn('syn-login-form',s)
   e.parse(s)
 def test_landing_emblem_and_gate(self):
  s=(P/'templates/index.html').read_text()
  self.assertIn('synthexia-group-emblem.webp',s)
  self.assertNotIn('Margherita',s)
  self.assertIn('student_login',s)
  self.assertIn('vendor_login',s)
  self.assertTrue((P/'static/images/branding/synthexia-group-emblem.webp').is_file())
 def test_vendor_dashboard_sql_qualified(self):
  s=(P/'app.py').read_text()
  self.assertIn('WHERE o.vendor_id=? AND o.payment_state="Paid" ORDER BY o.id DESC LIMIT 8',s)
 def test_no_template_parse_errors(self):
  e=Environment(loader=FileSystemLoader(str(P/'templates')))
  for p in (P/'templates').glob('*.html'):e.parse(p.read_text())
if __name__=='__main__':unittest.main()
