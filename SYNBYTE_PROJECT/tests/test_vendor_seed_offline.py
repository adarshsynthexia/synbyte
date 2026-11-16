"""SQLite seeding test without Flask; validates per-vendor independent starter inventory."""
import ast,json,sqlite3,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]
ROOT=ast.parse((P/'app.py').read_text(encoding='utf-8'))
CATALOG=ast.literal_eval(next(n.value for n in ROOT.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CATALOG' for t in n.targets)))
PHOTO_URLS=[r['url'] for r in json.loads((P/'PHOTO_MANIFEST.json').read_text())]
function=next(n for n in ROOT.body if isinstance(n,ast.FunctionDef) and n.name=='seed_vendor_catalog')
ns={'CATALOG':CATALOG,'PHOTO_URLS':PHOTO_URLS}
exec(compile(ast.Module(body=[function],type_ignores=[]),str(P/'app.py'),'exec'),ns)
seed=ns['seed_vendor_catalog']
class Inventory(unittest.TestCase):
 def test_new_vendor_gets_independent_32(self):
  c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON')
  c.executescript('''CREATE TABLE vendors(id INTEGER PRIMARY KEY,name TEXT,starter_seeded INTEGER DEFAULT 0);
    CREATE TABLE foods(id INTEGER PRIMARY KEY,vendor_id INTEGER,name TEXT,category TEXT,price INTEGER,description TEXT,image TEXT,active INTEGER DEFAULT 1);
    CREATE TABLE photo_credits(food_id INTEGER PRIMARY KEY,source TEXT,license TEXT,photographer TEXT);''')
  c.execute('INSERT INTO vendors(name) VALUES(?)',('Test Stall Alpha',))
  c.execute('INSERT INTO vendors(name) VALUES(?)',('Test Stall Beta',))
  seed(c,1);seed(c,2);c.commit()
  for v in (1,2):
   self.assertEqual(c.execute('SELECT COUNT(*) FROM foods WHERE vendor_id=?',(v,)).fetchone()[0],32)
   self.assertEqual(len({r['image'] for r in c.execute('SELECT image FROM foods WHERE vendor_id=?',(v,))}),32)
  fid=c.execute('SELECT id FROM foods WHERE vendor_id=1 ORDER BY id LIMIT 1').fetchone()[0]
  c.execute('UPDATE foods SET active=0 WHERE id=?',(fid,))
  seed(c,1);c.commit()
  self.assertEqual(c.execute('SELECT SUM(active) FROM foods WHERE vendor_id=1').fetchone()[0],31)
  self.assertEqual(c.execute('SELECT SUM(active) FROM foods WHERE vendor_id=2').fetchone()[0],32)
  c.close()
if __name__=='__main__':unittest.main()
