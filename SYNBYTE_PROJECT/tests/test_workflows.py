"""Integration tests to run on any Python install with requirements.txt installed."""
import os,sys,tempfile,unittest,sqlite3
from pathlib import Path
from urllib.parse import urlparse

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))
TEMP=tempfile.TemporaryDirectory(prefix='synbyte-tests-')
os.environ['SYNBYTE_DB']=str(Path(TEMP.name)/'test.sqlite3')
os.environ['SECRET_KEY']='only-a-testing-secret-1234'
os.environ['PAYMENT_PROVIDER']='demo'
os.environ['SEED_DEMO']='1'
from app import app,DB_PATH,CATALOG

class SynbyteFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.client=app.test_client()
    def setUp(self):
        self.client=app.test_client()
        with app.app_context():
            with sqlite3.connect(DB_PATH) as c:
                c.execute('DELETE FROM notifications');c.execute('DELETE FROM payment_events');c.execute('DELETE FROM payments');c.execute('DELETE FROM status_history');c.execute('DELETE FROM order_items');c.execute('DELETE FROM orders');c.execute('DELETE FROM carts');c.execute('DELETE FROM favorites')
    def csrf(self):
        self.client.get('/')
        with self.client.session_transaction() as s:return s['_csrf']
    def login(self,role,email):
        resp=self.client.post('/auth/login/'+role,data={'_csrf':self.csrf(),'email':email,'password':'SynbyteDemo!2026'},follow_redirects=False)
        self.assertEqual(resp.status_code,302,resp.data[:200]);return resp
    def logout(self):
        r=self.client.post('/logout',data={'_csrf':self.csrf()})
        self.assertEqual(r.status_code,302)
    def place_unpaid(self):
        csrf=self.csrf()
        r=self.client.post('/cart/items',data={'_csrf':csrf,'food_id':'1','change':'1'})
        self.assertEqual(r.status_code,302)
        page=self.client.get('/checkout')
        self.assertEqual(page.status_code,200)
        with self.client.session_transaction() as s:nonce=s['checkout_nonce']
        r=self.client.post('/checkout/confirm',data={'_csrf':self.csrf(),'nonce':nonce},follow_redirects=False)
        self.assertEqual(r.status_code,302)
        order_id=int(r.headers['Location'].rstrip('/').split('/')[-1]);return order_id
    def dbrow(self,oid):
        with sqlite3.connect(DB_PATH) as c:
            c.row_factory=sqlite3.Row
            return dict(c.execute('SELECT * FROM orders WHERE id=?',(oid,)).fetchone())
    def test_public_pages_and_32_distinct_photo_sources(self):
        self.assertEqual(len(CATALOG),32)
        import json
        sources=json.loads((PROJECT/'PHOTO_MANIFEST.json').read_text())
        self.assertEqual(len(sources),32)
        self.assertEqual(len({r['url'] for r in sources}),32)
        for page in ('/','/choose','/student/login','/student/register','/vendor/login','/vendor/register','/forgot-password','/help','/photo-credits'):
            r=self.client.get(page)
            self.assertEqual(r.status_code,200,(page,r.data[:300]))
        self.assertNotIn(b'Welcome Back',self.client.get('/').data)
    def test_student_order_payment_token_vendor_ready_collection(self):
        self.login('student','student@synbyte.test')
        self.assertEqual(self.client.get('/menu').status_code,200)
        self.assertEqual(self.client.get('/vendor/dashboard').status_code,403)
        oid=self.place_unpaid()
        self.assertIsNone(self.dbrow(oid)['token'])
        with sqlite3.connect(DB_PATH) as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM notifications').fetchone()[0],0)
        # Failed simulation cannot create a valid token
        self.client.post(f'/payment/{oid}/demo',data={'_csrf':self.csrf(),'action':'fail'})
        self.assertIsNone(self.dbrow(oid)['token'])
        self.assertEqual(self.dbrow(oid)['payment_state'],'Failed')
        self.client.post(f'/payment/{oid}/demo',data={'_csrf':self.csrf(),'action':'success'})
        token=self.dbrow(oid)['token'];self.assertTrue(token and token.startswith('CX-'))
        self.assertEqual(self.dbrow(oid)['payment_state'],'Paid')
        self.assertEqual(self.client.get(f'/order/token/{oid}').status_code,200)
        self.assertEqual(self.client.get(f'/order/tracking/{oid}').status_code,200)
        self.assertEqual(self.client.get('/notifications').status_code,200)
        # Repeated demo success must not double-issue tokens
        self.client.post(f'/payment/{oid}/demo',data={'_csrf':self.csrf(),'action':'success'})
        self.assertEqual(self.dbrow(oid)['token'],token)
        self.logout()
        self.login('vendor','pizzapoint@synbyte.test')
        self.assertEqual(self.client.get(f'/vendor/orders/{oid}').status_code,200)
        self.assertEqual(self.client.get('/menu').status_code,403)
        for status in ('Accepted','Preparing','Ready'):
            r=self.client.post(f'/vendor/orders/{oid}/status',data={'_csrf':self.csrf(),'status':status})
            self.assertEqual(r.status_code,302)
            self.assertEqual(self.dbrow(oid)['status'],status)
        r=self.client.post('/vendor/verify-token',data={'_csrf':self.csrf(),'token':token})
        self.assertEqual(r.status_code,302)
        self.assertEqual(self.dbrow(oid)['status'],'Collected')
        r=self.client.post('/vendor/verify-token',data={'_csrf':self.csrf(),'token':token})
        self.assertEqual(r.status_code,302)
        self.assertEqual(self.dbrow(oid)['status'],'Collected')
        self.logout();self.login('student','student@synbyte.test')
        r=self.client.get('/api/notifications')
        self.assertEqual(r.status_code,200)
        self.assertTrue(any(row['title']=='Food ready for pickup' for row in r.get_json()))
    def test_cross_vendor_cart_and_access(self):
        self.login('student','student@synbyte.test')
        self.client.post('/cart/items',data={'_csrf':self.csrf(),'food_id':1,'change':1})
        r=self.client.post('/cart/items',data={'_csrf':self.csrf(),'food_id':6,'change':1},follow_redirects=True)
        self.assertIn(b'one vendor',r.data.lower())
        with sqlite3.connect(DB_PATH) as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM carts').fetchone()[0],1)
    def test_csrf(self):
        self.login('student','student@synbyte.test')
        r=self.client.post('/cart/items',data={'food_id':1,'change':1})
        self.assertEqual(r.status_code,400)
    def test_self_register_live_vendor_and_independent_menu(self):
        self.client.post('/vendor/register',data={'_csrf':self.csrf(),'vendor_name':'Fresh Test Stall','name':'New Manager',
             'contact':'1234567890','email':'freshvendor@example.test','password':'TestPassword123!','confirm':'TestPassword123!'})
        with sqlite3.connect(DB_PATH) as c:
            vid=c.execute('SELECT id FROM vendors WHERE name=?',('Fresh Test Stall',)).fetchone()[0]
            self.assertEqual(c.execute('SELECT approved FROM vendors WHERE id=?',(vid,)).fetchone()[0],1)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM foods WHERE vendor_id=? AND active=1',(vid,)).fetchone()[0],32)
            first=c.execute('SELECT id FROM foods WHERE vendor_id=? ORDER BY id LIMIT 1',(vid,)).fetchone()[0]
        # The vendor account is already active and can control only its own food.
        self.client.post('/auth/login/vendor',data={'_csrf':self.csrf(),'email':'freshvendor@example.test','password':'TestPassword123!'},follow_redirects=False)
        response=self.client.post(f'/vendor/food/{first}/visibility',data={'_csrf':self.csrf(),'active':'0'})
        self.assertEqual(response.status_code,302)
        with sqlite3.connect(DB_PATH) as c:
            self.assertEqual(c.execute('SELECT active FROM foods WHERE id=?',(first,)).fetchone()[0],0)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM foods WHERE vendor_id=? AND active=1',(vid,)).fetchone()[0],31)
        self.logout()
        self.login('student','student@synbyte.test')
        page=self.client.get('/vendors')
        self.assertEqual(page.status_code,200)
        self.assertIn(b'Fresh Test Stall',page.data)
        self.assertEqual(self.client.get(f'/vendors/{vid}/menu').status_code,200)

if __name__=='__main__':unittest.main()
