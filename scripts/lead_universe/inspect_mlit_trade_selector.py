import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL='https://etsuran2.mlit.go.jp/TAKKEN/kensetuKensaku.do'
OUT=Path('artifacts/roof_selector_inventory')
OUT.mkdir(parents=True, exist_ok=True)

s=requests.Session()
s.headers.update({'User-Agent':'Mozilla/5.0 (compatible; RoofUniverseSelectorInventory/1.0; public-registry-research)','Accept-Language':'ja'})
r=s.get(URL, timeout=60)
r.raise_for_status()
html=r.content.decode('cp932', errors='replace')
(OUT/'initial_search_form.html').write_text(html, encoding='utf-8')
soup=BeautifulSoup(html,'html.parser')

inventory=[]
for sel in soup.find_all('select'):
    inventory.append({
        'tag':'select',
        'name':sel.get('name',''),
        'id':sel.get('id',''),
        'options':[{'value':o.get('value',''),'label':o.get_text(' ',strip=True),'selected':o.has_attr('selected')} for o in sel.find_all('option')]
    })
for inp in soup.find_all('input'):
    typ=(inp.get('type') or '').lower()
    if typ in ('radio','checkbox','hidden'):
        parent=inp.parent.get_text(' ',strip=True) if inp.parent else ''
        inventory.append({'tag':'input','type':typ,'name':inp.get('name',''),'id':inp.get('id',''),'value':inp.get('value',''),'context':parent[:300]})

interesting=[]
for line_no,line in enumerate(html.splitlines(),1):
    if any(k in line for k in ['屋根','>屋<','屋','塗装','>塗<','gyosyu','GYOSYU']):
        interesting.append({'line':line_no,'text':line[:1000]})

result={'url':URL,'select_count':len(soup.find_all('select')),'inventory':inventory,'interesting_lines':interesting}
(OUT/'selector_inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
