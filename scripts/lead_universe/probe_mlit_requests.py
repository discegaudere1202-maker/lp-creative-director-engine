import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup

URL='https://etsuran2.mlit.go.jp/TAKKEN/kensetuKensaku.do'
OUT=Path('artifacts/landscape_universe_requests_probe'); OUT.mkdir(parents=True,exist_ok=True)
s=requests.Session(); s.headers.update({'User-Agent':'Mozilla/5.0'})
r=s.get(URL,timeout=60); r.raise_for_status()
soup=BeautifulSoup(r.text,'html.parser')
form=soup.find('form')
payload={}
for inp in form.find_all(['input','select']):
    name=inp.get('name')
    if not name: continue
    if inp.name=='input':
        t=inp.get('type','text')
        if t in ('hidden','text'):
            payload[name]=inp.get('value','')
    elif inp.name=='select':
        opt=inp.find('option',selected=True) or inp.find('option')
        payload[name]=opt.get('value','') if opt else ''
payload.update({
 'CMD':'search','rdoSelect':'2','rdoSelectJoken':'1','licenseNoKbn':'','licenseNoFrom':'','licenseNoTo':'',
 'choice':'1','kenCode':'06','gyosyu':'23','gyosyuType':'','keyWord':'','sortValue':'2','rdoSelectSort':'1','dispCount':'50'
})
r2=s.post(URL,data=payload,timeout=120,allow_redirects=True); r2.raise_for_status()
(OUT/'result.html').write_text(r2.text,encoding='utf-8')
s2=BeautifulSoup(r2.text,'html.parser')
result={
 'status':r2.status_code,'url':r2.url,'title':s2.title.get_text(strip=True) if s2.title else '',
 'hidden':{i.get('name'):i.get('value','') for i in s2.find_all('input',{'type':'hidden'}) if i.get('name')},
 'tables':[[[c.get_text(' ',strip=True) for c in tr.find_all(['th','td'])] for tr in t.find_all('tr') if tr.get_text(strip=True)] for t in s2.find_all('table')],
 'links':[{'text':a.get_text(' ',strip=True),'href':a.get('href'),'onclick':a.get('onclick')} for a in s2.find_all('a')]
}
(OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'url':result['url'],'hidden':result['hidden'],'tables':result['tables'][:10],'links':result['links'][-30:]},ensure_ascii=False,indent=2))
