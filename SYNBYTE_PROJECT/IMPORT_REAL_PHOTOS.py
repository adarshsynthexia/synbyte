"""Validate and optionally install 32 individually licensed real food photographs.
This script cannot determine visual dish correctness automatically; check generated sheet.
"""
import argparse, csv, hashlib, io, sqlite3, sys
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont
BASE=Path(__file__).resolve().parent
MANIFEST=BASE/'PHOTO_SOURCES.csv'
SRC=BASE/'photos_to_import'
TARGET=BASE/'static/images/food'
DB=BASE/'instance/synbyte.sqlite3'
REPORT=BASE/'REAL_PHOTO_VALIDATION.txt'

def dhash(im):
    im=ImageOps.grayscale(im).resize((9,8),Image.Resampling.LANCZOS)
    p=list(im.getdata())
    return sum(1<<(8*y+x) for y in range(8) for x in range(8) if p[9*y+x]>p[9*y+x+1])

def validate():
    with MANIFEST.open(newline='',encoding='utf8') as f: entries=list(csv.DictReader(f))
    errors=[];results=[];hashed={};perceptual=[]
    if len(entries)!=32:errors.append('Expected exactly 32 manifest entries; found '+str(len(entries)))
    for rec in entries:
        filename=Path(rec.get('local_file','')).name
        if not filename or filename != rec.get('local_file',''):
            errors.append('Unsafe or blank filename');continue
        path=SRC/filename
        if not path.exists():
            errors.append('Missing: '+filename);continue
        if not all(rec.get(field,'').strip() for field in ('source_url','photographer','license')):
            errors.append('Fill source URL, photographer and license: '+filename);continue
        if not rec['source_url'].startswith('https://'):
            errors.append('Source URL must be HTTPS: '+filename);continue
        try:
            original=path.read_bytes()
            exact=hashlib.sha256(original).hexdigest()
            if exact in hashed:
                errors.append('Duplicate source file: '+filename+' / '+hashed[exact]);continue
            with Image.open(io.BytesIO(original)) as im:
                im.load()
                if min(im.size)<320:
                    errors.append('Too small: '+filename);continue
                image=ImageOps.exif_transpose(im).convert('RGB')
            fp=dhash(image)
            near=[name for name,h in perceptual if (fp^h).bit_count()<=8]
            if near:
                errors.append('Potential visual duplicate: '+filename+' / '+', '.join(near));continue
            hashed[exact]=filename;perceptual.append((filename,fp))
            results.append((rec,image))
        except Exception as ex:
            errors.append('Invalid image '+filename+': '+str(ex))
    W=1240;w=286;h=186;gap=16
    canvas=Image.new('RGB',(W,8*244+65),'white');d=ImageDraw.Draw(canvas)
    try:
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
    except OSError:font=ImageFont.load_default()
    d.text((20,18),'Real Photo Contact Sheet - VISUAL DISH REVIEW REQUIRED',font=font,fill='#ad0b27')
    for i,(rec,img) in enumerate(results):
        x=22+(i%4)*(w+gap);y=65+(i//4)*244
        thumb=ImageOps.fit(img,(w,h),method=Image.Resampling.LANCZOS)
        canvas.paste(thumb,(x,y))
        d.text((x,y+h+7),rec['dish_name'][:35],font=font,fill='#171717')
        d.text((x,y+h+29),rec['local_file'][:38],font=font,fill='#888')
    canvas.save(BASE/'REAL_PHOTO_REVIEW_SHEET.jpg',quality=87)
    summary=[f'{len(results)}/32 distinct image candidates loaded','Automatic image/content-name verification is IMPOSSIBLE — inspect contact sheet yourself.',*errors]
    REPORT.write_text('\n'.join(summary)+'\n',encoding='utf8')
    return entries,results,errors

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');ap.add_argument('--apply',action='store_true');ap.add_argument('--confirmed-reviewed',action='store_true')
    args=ap.parse_args()
    if not args.check and not args.apply:ap.error('Specify --check or --apply --confirmed-reviewed')
    entries,results,errors=validate()
    print(f'{len(results)}/32 valid photos; {len(errors)} issues. See REAL_PHOTO_VALIDATION.txt and REAL_PHOTO_REVIEW_SHEET.jpg')
    if errors or len(results)!=32:
        print('Site unchanged; images must all pass before installing.')
        sys.exit(1)
    if not args.apply:
        print('Now visually review each of the 32 dishes and verify licensing. If correct, rerun with --apply --confirmed-reviewed.')
        return
    if not args.confirmed_reviewed:ap.error('--confirmed-reviewed is required for installation')
    if not DB.exists():sys.exit('Database missing. Start the Flask app once before running this installer.')
    TARGET.mkdir(exist_ok=True)
    with sqlite3.connect(DB) as db:
        db.execute('PRAGMA foreign_keys=ON')
        for rec,image in results:
            food_id=int(rec['food_id'])
            row=db.execute('SELECT id,name FROM foods WHERE id=?',(food_id,)).fetchone()
            if not row or row[1]!=rec['dish_name']:raise RuntimeError('Dish changed; abort without updating database: '+rec['dish_name'])
        # Images use new, never-overwritten filenames. Old artworks remain as rollback resources.
        for rec,image in results:
            food_id=int(rec['food_id'])
            fname=f'{food_id:02d}-{hashlib.sha256((SRC/rec["local_file"]).read_bytes()).hexdigest()[:14]}.webp'
            path=TARGET/fname
            if not path.exists():ImageOps.fit(image,(1100,720),Image.Resampling.LANCZOS).save(path,'WEBP',quality=87)
            db.execute('UPDATE foods SET image=? WHERE id=?',(f'food/{fname}',food_id))
            db.execute('INSERT OR REPLACE INTO photo_credits(food_id,source,license,photographer) VALUES(?,?,?,?)',
                       (food_id,rec['source_url'],rec['license'],rec['photographer']))
    print('SUCCESS: installed 32 local real-photo files. Restart or refresh SYNBYTE.')

if __name__=='__main__':main()
