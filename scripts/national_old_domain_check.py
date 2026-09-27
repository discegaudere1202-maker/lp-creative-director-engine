#!/usr/bin/env python3
import csv, glob, json, re, unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup

OUT=Path('artifacts/national-source-discovery')
OUT.mkdir(parents=True,exist_ok=True)
UA='WEBIT-LP-list-enrichment/1.0 (public-data research; no paid API)'
PREFS=['北海道','青森県','岩手県','宮城県','秋田県','山形県','福島県','茨城県','栃木県','群馬県','埼玉県','千葉県','東京都','神奈川県','新潟県','富山県','石川県','福井県','山梨県','長野県','岐阜県','静岡県','愛知県','三重県','滋賀県','京都府','大阪府','兵庫県','奈良県','和歌山県','鳥取県','島根県','岡山県','広島県','山口県','徳島県','香川県','愛媛県','高知県','福岡県','佐賀県','長崎県','熊本県','大分県','宮崎県','鹿児島県','沖縄県']

def clean(v): return re.sub(r'\s+',' ',(v or '').replace('\u3000',' ')).strip()
def norm(v):
    s=unicodedata.normalize('NFKC',v or '').lower()
    return re.sub(r'[^0-9a-z一-龠ぁ-んァ-ヶ]+','',s)
def norm_business(v):
    s=norm(v)
    for t in ['株式会社','有限会社','合同会社','一般社団法人','一般財団法人']:
        s=s.replace(t,'')
    return s
def digits(v): return re.sub(r'\D','',v or '')
def locality(address):
    a=norm(address)
    for p in PREFS:
        pn=norm(p)
        if a.startswith(pn): a=a[len(pn):]; break
    return a[:8]

def fetch_domain(domain):
    last=''
    for scheme in ('https','http'):
        url=f'{scheme}://{domain}/'
        try:
            r=requests.get(url,headers={'User-Agent':UA,'Accept-Language':'ja,en;q=0.5'},timeout=8,allow_redirects=True)
            ctype=(r.headers.get('content-type') or '').lower()
            title=text=''
            if 'html' in ctype or not ctype:
                r.encoding=r.apparent_encoding or r.encoding
                soup=BeautifulSoup(r.text[:500000],'lxml')
                title=clean(soup.title.get_text(' ',strip=True) if soup.title else '')
                text=clean(soup.get_text(' ',strip=True))[:200000]
            return {'requested_url':url,'final_url':r.url,'http_status':r.status_code,'content_type':ctype,'title':title,'text':text,'error':''}
        except Exception as e:
            last=repr(e)
    return {'requested_url':f'https://{domain}/','final_url':'','http_status':'','content_type':'','title':'','text':'','error':last}

def main():
    rows=[]
    for path in sorted(glob.glob('data/national_domain_targets/old_domain_targets_*.csv')):
        with open(path,encoding='utf-8-sig',newline='') as f:
            rows.extend(csv.DictReader(f))
    domains=sorted({r['email_domain'].lower().strip('.') for r in rows if r.get('email_domain')})
    net={}
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs={ex.submit(fetch_domain,d):d for d in domains}
        for fut in as_completed(futs):
            d=futs[fut]
            try: net[d]=fut.result()
            except Exception as e: net[d]={'requested_url':f'https://{d}/','final_url':'','http_status':'','content_type':'','title':'','text':'','error':repr(e)}
    out=[]
    for r in rows:
        d=r['email_domain'].lower().strip('.')
        n=net[d]
        page=norm((n.get('title') or '')+' '+(n.get('text') or ''))
        page_digits=digits(n.get('text') or '')
        bn=norm_business(r.get('business_name',''))
        ph=digits(r.get('phone',''))
        loc=locality(r.get('address',''))
        name_match=bool(bn and len(bn)>=4 and bn in page)
        phone_match=bool(ph and len(ph)>=9 and ph in page_digits)
        loc_match=bool(loc and len(loc)>=4 and loc in page)
        identity=phone_match or name_match or (len(bn)>=3 and bn in page and loc_match)
        if not n.get('final_url'):
            status='NO_RESPONSE'; ev=n.get('error') or 'No HTTP response'
        elif identity:
            status='LIVE_IDENTITY_MATCH'; ev=';'.join(x for x,ok in [('BUSINESS_NAME',name_match),('PHONE',phone_match),('LOCALITY',loc_match)] if ok)
        else:
            status='LIVE_UNCONFIRMED'; ev='Live domain but business identity not machine-confirmed'
        z=dict(r)
        z.update({'requested_url':n.get('requested_url',''),'final_url':n.get('final_url',''),'http_status':n.get('http_status',''),'title':n.get('title',''),'domain_status':status,'identity_match':'YES' if identity else 'NO','evidence':ev})
        out.append(z)
    fields=['canonical_entity_id','business_name','prefecture','address','phone','email_normalized','email_domain','requested_url','final_url','http_status','title','domain_status','identity_match','evidence']
    with open(OUT/'old_domain_http_results.csv','w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(out)
    counts={}
    for r in out: counts[r['domain_status']]=counts.get(r['domain_status'],0)+1
    stats={'targets':len(rows),'unique_domains':len(domains),'domain_status':counts}
    (OUT/'old_domain_http_stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(stats,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
