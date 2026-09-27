import json
import requests
from bs4 import BeautifulSoup

URL='https://etsuran2.mlit.go.jp/TAKKEN/kensetuKensaku.do'

def search(ken, gyotype):
    s=requests.Session(); s.headers.update({'User-Agent':'Mozilla/5.0'})
    r=s.get(URL,timeout=60); r.raise_for_status(); soup=BeautifulSoup(r.content,'html.parser',from_encoding='cp932')
    form=soup.find('form'); payload={}
    for inp in form.find_all(['input','select']):
        name=inp.get('name')
        if not name: continue
        if inp.name=='input' and inp.get('type','text') in ('hidden','text'):
            payload[name]=inp.get('value','')
        elif inp.name=='select':
            opt=inp.find('option',selected=True) or inp.find('option'); payload[name]=opt.get('value','') if opt else ''
    payload.update({'CMD':'search','rdoSelect':'2','rdoSelectJoken':'1','choice':'1','kenCode':ken,'gyosyu':'23','gyosyuType':str(gyotype),'keyWord':'','sortValue':'2','rdoSelectSort':'1','dispCount':'50'})
    r2=s.post(URL,data=payload,timeout=120); r2.raise_for_status(); soup2=BeautifulSoup(r2.content,'html.parser',from_encoding='cp932')
    hidden={i.get('name'):i.get('value','') for i in soup2.find_all('input',{'type':'hidden'}) if i.get('name')}
    table=soup2.find('table')
    rows=[]
    if table:
        for tr in table.find_all('tr')[1:]:
            cells=[c.get_text(' ',strip=True) for c in tr.find_all(['th','td'])]
            if len(cells)>=7: rows.append(cells)
    return {'ken':ken,'gyosyuType':gyotype,'resultCount':hidden.get('resultCount'),'pageCount':hidden.get('pageCount'),'sample':rows[:3]}

print(json.dumps({'general':search('06',1),'special':search('06',2)},ensure_ascii=False,indent=2))
