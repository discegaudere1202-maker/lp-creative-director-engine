import json
import requests
from bs4 import BeautifulSoup

URL='https://etsuran2.mlit.go.jp/TAKKEN/kensetuKensaku.do'

def decode_best(content):
    candidates=[]
    for enc in ('utf-8','cp932','shift_jis','euc_jp'):
        try:
            text=content.decode(enc,errors='replace')
        except Exception:
            continue
        score=text.count('\ufffd')*100
        for token in ('許可番号','商号','所在地','国土交通省'):
            if token in text: score-=1000
        candidates.append((score,enc,text))
    return min(candidates,key=lambda x:x[0])

def base_payload(s):
    r=s.get(URL,timeout=60); r.raise_for_status(); _,enc,text=decode_best(r.content)
    soup=BeautifulSoup(text,'html.parser'); form=soup.find('form'); payload={}
    for inp in form.find_all(['input','select']):
        name=inp.get('name')
        if not name: continue
        if inp.name=='input' and inp.get('type','text') in ('hidden','text'):
            payload[name]=inp.get('value','')
        elif inp.name=='select':
            opt=inp.find('option',selected=True) or inp.find('option'); payload[name]=opt.get('value','') if opt else ''
    return payload

def search(ken, gyotype):
    s=requests.Session(); s.headers.update({'User-Agent':'Mozilla/5.0'})
    payload=base_payload(s)
    payload.update({'CMD':'search','rdoSelect':'2','rdoSelectJoken':'1','choice':'1','kenCode':ken,'gyosyu':'23','gyosyuType':str(gyotype),'keyWord':'','sortValue':'2','rdoSelectSort':'1','dispCount':'50'})
    r=s.post(URL,data=payload,timeout=120); r.raise_for_status(); score,enc,text=decode_best(r.content)
    soup=BeautifulSoup(text,'html.parser')
    hidden={i.get('name'):i.get('value','') for i in soup.find_all('input',{'type':'hidden'}) if i.get('name')}
    table=soup.find('table'); sample=[]
    if table:
        for tr in table.find_all('tr')[1:4]: sample.append([c.get_text(' ',strip=True) for c in tr.find_all(['th','td'])])
    return {'ken':ken,'gyosyuType':gyotype,'encoding':enc,'decode_score':score,'resultCount':int(hidden.get('resultCount') or 0),'pageCount':int(hidden.get('pageCount') or 0),'sample':sample}

out={}
for ken in ('06','13','40'):
    g=search(ken,1); s=search(ken,2); out[ken]={'general':g,'special':s,'sum':g['resultCount']+s['resultCount']}
print(json.dumps(out,ensure_ascii=False,indent=2))
