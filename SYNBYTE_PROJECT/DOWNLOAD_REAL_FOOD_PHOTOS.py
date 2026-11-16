"""Download the 32 independent real-photo sources into static/images/food.
Keeps website and database unchanged until every image can be fetched and checked.
Run only with an internet connection: py DOWNLOAD_REAL_FOOD_PHOTOS.py
Verify visually that every photo matches its dish before claiming photo audit passed.
"""
import hashlib,json,sqlite3,time,sys
from pathlib import Path
from io import BytesIO
import requests
from PIL import Image,ImageOps,ImageDraw,ImageFont
BASE=Path(__file__).resolve().parent
MANIFEST=json.loads((BASE/'PHOTO_MANIFEST.json').read_text(encoding='utf8'))
OUT=BASE/'static/images/food';OUT.mkdir(parents=True,exist_ok=True)
STATUS=BASE/'PHOTO_DOWNLOAD_RESULTS.json'
SESSION=requests.Session()
SESSION.headers.update({'User-Agent':'SynbyteFoodPhotoDownload/1.0 (education project; https://commons.wikimedia.org/wiki/Main_Page)'})

def dhash(im):
  pixels=list(ImageOps.grayscale(im).resize((9,8)).getdata())
  return sum(1<<(y*8+x) for y in range(8) for x in range(8) if pixels[y*9+x]>pixels[y*9+x+1])

def valid(path):
 try:
  with Image.open(path) as im:
   im.load()
   if min(im.size)<300:raise ValueError('Too small')
   return (hashlib.sha256(path.read_bytes()).hexdigest(),dhash(im))
 except Exception:return None

saved=[]; hashes=[]; errors=[]
for i,item in enumerate(MANIFEST,1):
 path=OUT/item['local_filename']
 if valid(path) is None:
  try:
   print(f'[{i:02d}/32] {item["dish"]}...',flush=True)
   response=SESSION.get(item['url'],timeout=30)
   if response.status_code==429:
    print('  Source rate-limited. Stop now; retry later.',flush=True)
    errors.append(item['dish']+' : HTTP 429');break
   response.raise_for_status()
   if not response.headers.get('content-type','').startswith('image/'):
    raise ValueError('Source did not return an image')
   if len(response.content)>15_000_000:raise ValueError('File exceeds max size')
   with Image.open(BytesIO(response.content)) as im:
    im=ImageOps.exif_transpose(im.convert('RGB'))
    if min(im.size)<300:raise ValueError('Image too small')
    im.thumbnail((1100,850),Image.Resampling.LANCZOS)
    im.save(path,format='WEBP',quality=84)
   time.sleep(1.3)
  except Exception as exc:
   path.unlink(missing_ok=True)
   errors.append(item['dish']+' : '+str(exc))
   continue
 result=valid(path)
 if result is None:errors.append(item['dish']+' : invalid image');continue
 sha,phash=result
 if any(sha==other[0] or (phash^other[1]).bit_count()<4 for other in hashes):
  errors.append(item['dish']+' : possible repeated image; review required')
  continue
 hashes.append(result)
 saved.append(item)
STATUS.write_text(json.dumps(dict(downloaded=len(saved),total=len(MANIFEST),errors=errors),indent=2))
print(f'Photo downloads present and distinct by hash: {len(saved)}/32')
if errors:
 for msg in errors:print('CHECK:',msg)
 print('Website database unchanged. Existing external photos remain usable online.')
 sys.exit(2)
if len(saved)!=32:
 print('INCOMPLETE. No database changes.');sys.exit(2)
# Make visual contact sheet with names. Manual review remains essential.
font=ImageFont.load_default();sheet=Image.new('RGB',(4*280,8*230),'white');d=ImageDraw.Draw(sheet)
for idx,item in enumerate(MANIFEST):
 with Image.open(OUT/item['local_filename']) as im:
  im=ImageOps.fit(im.convert('RGB'),(260,180));x=(idx%4)*280+10;y=(idx//4)*230+8
  sheet.paste(im,(x,y));d.text((x,y+185),item['dish'][:33],fill='black',font=font)
sheet.save(BASE/'REAL_FOOD_PHOTO_CONTACT_SHEET.jpg',quality=85)
# Update only provided demo-photo URLs, never vendor-customized photos.
DB=BASE/'instance/synbyte.sqlite3'
if DB.exists():
 with sqlite3.connect(DB) as c:
  for item in MANIFEST:
   c.execute('UPDATE foods SET image=? WHERE image=?',('food/'+item['local_filename'],item['url']))
print('32 real photos downloaded locally and mapped. CHECK THE CONTACT SHEET before public use.')
