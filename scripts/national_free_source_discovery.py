#!/usr/bin/env python3
import csv, json, re, time, unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

OUT = Path("artifacts/national-source-discovery")
OUT.mkdir(parents=True, exist_ok=True)
UA = "WEBIT-LP-list-enrichment/1.0 (public-data research; no paid API)"
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "ja,en;q=0.5"})
EMAIL_RE = re.compile(r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9-]+(?:\.[A-Z0-9-]+)+", re.I)
PREFS = ["北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県","茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県","新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県","静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県","鳥取県","島根県","岡山県","広島県","山口県","徳島県","香川県","愛媛県","高知県","福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"]
FREE = {"gmail.com","googlemail.com","yahoo.co.jp","yahoo.com","outlook.com","outlook.jp","hotmail.com","hotmail.co.jp","live.com","live.jp","icloud.com","me.com","mac.com","aol.com","proton.me","protonmail.com"}
PUBLIC_BASES = {"ocn.ne.jp","plala.or.jp","dion.ne.jp","eonet.ne.jp","eo-net.ne.jp","so-net.ne.jp","biglobe.ne.jp","nifty.ne.jp","nifty.com","zaq.ne.jp","odn.ne.jp","ybb.ne.jp","jcom.home.ne.jp","jcom.zaq.ne.jp","asahi-net.or.jp","wakwak.com","t-com.ne.jp","ucom.ne.jp","pikara.ne.jp","bbexcite.jp","dream.jp","infoweb.ne.jp","mesh.ad.jp","mopera.net","hi-ho.ne.jp","bekkoame.ne.jp","e-mail.jp","ecnet.jp","rim.or.jp","saganet.ne.jp","if-n.ne.jp","home.ne.jp","dti.ne.jp","ztv.ne.jp","magma.jp","mrr.jp","aitai.ne.jp","technowave.ne.jp","tigers-net.com","alpha-net.ne.jp","jomon.ne.jp","tp1.jp","bai.ne.jp","cty-net.ne.jp","amigo.ne.jp","itkeeper.ne.jp","tkcnet.ne.jp","c-able.ne.jp","alles.or.jp","mco.ne.jp","nsknet.or.jp","wind.jp","sopia.or.jp","bbiq.jp","tiki.ne.jp","wainet.ne.jp","netwave.or.jp","enjoy.ne.jp","broba.cc","commufa.jp","auone-net.jp","ccnw.ne.jp","iij4u.or.jp","poporo.ne.jp"}

rows=[]
logs=[]

def fetch(url, source_name):
    t=time.time()
    try:
        r=S.get(url, timeout=30)
        logs.append({"source_name":source_name,"source_url":url,"status":r.status_code,"bytes":len(r.content),"elapsed":round(time.time()-t,3),"error":""})
        r.raise_for_status()
        r.encoding = r.apparent_encoding or r.encoding
        return r.text
    except Exception as e:
        logs.append({"source_name":source_name,"source_url":url,"status":"ERROR","bytes":0,"elapsed":round(time.time()-t,3),"error":repr(e)})
        return ""

def clean(v):
    return re.sub(r"\s+"," ",(v or "").replace("\u3000"," ")).strip()

def norm(v):
    s=unicodedata.normalize("NFKC",v or "").lower()
    return re.sub(r"[^0-9a-z一-龠ぁ-んァ-ヶ]+","",s)

def norm_business(v):
    s=norm(v)
    for t in ["株式会社","有限会社","合同会社","一般社団法人","一般財団法人"]:
        s=s.replace(t,"")
    return s

def digits(v):
    return re.sub(r"\D","",v or "")

def add(source_name, source_url, prefecture, name, address, phone, email, website=""):
    email=clean(email).lower().replace("mailto:","")
    m=EMAIL_RE.search(email)
    if not m: return
    email=m.group(0).lower()
    rows.append({"source_name":source_name,"source_url":source_url,"prefecture":prefecture,"business_name":clean(name),"address":clean(address),"phone":clean(phone),"email":email,"website":clean(website),"retrieved_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())})

def parse_jalc():
    source="一般社団法人日本造園建設業協会 公開会員紹介検索"
    pat=re.compile(r"会社名\s*(?P<name>.*?)\s*代表者\s*(?P<rep>.*?)\s*住所\s*〒?\s*(?P<zip>\d{7})?\s*(?P<address>.*?)\s*電話番号\s*(?P<phone>[0-9()（）\-－ー\s]+)\s*url\s*(?P<website>.*?)\s*FAX番号\s*(?P<fax>[0-9()（）\-－ー\s]+)\s*email\s*(?P<email>[^\s]+)\s*業務内容", re.S|re.I)
    for code,pref in enumerate(PREFS,1):
        url=f"https://jalc.kktcs.co.jp/jalcmember/public/member_results.jsp?-Op=cn&category=1&cname=&kana=&p_id={code}"
        html=fetch(url,source)
        if not html: continue
        text=BeautifulSoup(html,"lxml").get_text(" ",strip=True)
        n=0
        for m in pat.finditer(text):
            add(source,url,pref,m.group("name"),m.group("address"),m.group("phone"),m.group("email"),m.group("website"))
            n+=1
        logs.append({"source_name":source,"source_url":url,"status":"PARSED","bytes":len(html.encode('utf-8',errors='ignore')),"elapsed":0,"error":f"rows={n}"})
        time.sleep(0.2)

def parse_table_page(source, url, prefecture):
    html=fetch(url,source)
    if not html: return
    soup=BeautifulSoup(html,"lxml")
    found=0
    for tr in soup.find_all("tr"):
        cells=[clean(c.get_text(" ",strip=True)) for c in tr.find_all(["td","th"])]
        joined=" | ".join(cells)
        em=EMAIL_RE.search(joined)
        if not em: continue
        name=cells[0] if cells else ""
        address=next((c for c in cells if "〒" in c or prefecture.replace("県","") in c),"")
        phone=next((c for c in cells if re.search(r"\d{2,4}[-(]\d",c)),"")
        website=next((c for c in cells if re.search(r"https?://|www\.",c,re.I)),"")
        add(source,url,prefecture,name,address,phone,em.group(0),website)
        found+=1
    if found==0:
        lines=[clean(x) for x in soup.get_text("\n",strip=True).splitlines() if clean(x)]
        for i,line in enumerate(lines):
            em=EMAIL_RE.search(line)
            if not em: continue
            window=lines[max(0,i-6):i+4]
            name=window[0] if window else ""
            address=next((x for x in window if "〒" in x),"")
            phone=next((x for x in window if re.search(r"\d{2,4}[-(]\d",x)),"")
            website=next((x for x in window if re.search(r"https?://|www\.",x,re.I)),"")
            add(source,url,prefecture,name,address,phone,em.group(0),website)

def parse_ibaraki():
    source="一般社団法人茨城県造園建設業協会 協会員紹介"
    url="https://www.zouenkyo.or.jp/page7"
    html=fetch(url,source)
    if not html: return
    text=BeautifulSoup(html,"lxml").get_text("\n",strip=True)
    pat=re.compile(r"会社名\s*\n(?P<name>[^\n]+).*?所在地\s*\n(?P<address>[^\n]+).*?TEL\s*\n(?P<phone>[^\n]+).*?EMAIL\s*\n(?P<email>[^\n]+).*?ホームページURL\s*(?:\n(?P<website>[^\n]+))?",re.S|re.I)
    for m in pat.finditer(text):
        add(source,url,"茨城県",m.group("name"),m.group("address"),m.group("phone"),m.group("email"),m.group("website") or "")

def crawl_chiba():
    source="一般社団法人千葉県造園緑化協会 会員紹介"
    root="https://www.zouen.or.jp/"
    html=fetch(root,source)
    if not html: return
    soup=BeautifulSoup(html,"lxml")
    links=set()
    for a in soup.find_all("a",href=True):
        u=urljoin(root,a["href"])
        if urlparse(u).netloc.endswith("zouen.or.jp") and "/kaiin/" in urlparse(u).path:
            links.add(u)
    links.update(["https://www.zouen.or.jp/kaiin/chiba_chuou.html","https://www.zouen.or.jp/kaiin/yotsukaido.html"])
    for u in sorted(links):
        parse_table_page(source,u,"千葉県")
        time.sleep(0.15)

def is_provider(domain):
    d=(domain or "").lower().strip(".")
    return d in FREE or any(d==b or d.endswith("."+b) for b in PUBLIC_BASES)

def municipality_fragment(address):
    a=norm(address)
    # keep a short locality fragment after prefecture. It is corroborative only.
    for p in PREFS:
        pn=norm(p)
        if a.startswith(pn):
            a=a[len(pn):]
            break
    return a[:8]

def fetch_domain(domain):
    last_error=""
    for scheme in ("https","http"):
        url=f"{scheme}://{domain}/"
        try:
            r=requests.get(url,headers={"User-Agent":UA,"Accept-Language":"ja,en;q=0.5"},timeout=8,allow_redirects=True)
            ctype=(r.headers.get("content-type") or "").lower()
            text=""
            title=""
            if "html" in ctype or not ctype:
                r.encoding=r.apparent_encoding or r.encoding
                html=r.text[:500000]
                soup=BeautifulSoup(html,"lxml")
                title=clean(soup.title.get_text(" ",strip=True) if soup.title else "")
                text=clean(soup.get_text(" ",strip=True))[:200000]
            return {"domain":domain,"requested_url":url,"final_url":r.url,"http_status":r.status_code,"content_type":ctype,"title":title,"text":text,"error":""}
        except Exception as e:
            last_error=repr(e)
    return {"domain":domain,"requested_url":f"https://{domain}/","final_url":"","http_status":"","content_type":"","title":"","text":"","error":last_error}

def domain_precheck(outrows):
    domain_rows={}
    for r in outrows:
        if "@" not in r["email"]: continue
        d=r["email"].rsplit("@",1)[1].lower().strip(".")
        if is_provider(d): continue
        domain_rows.setdefault(d,[]).append(r)
    results={}
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs={ex.submit(fetch_domain,d):d for d in domain_rows}
        for fut in as_completed(futs):
            d=futs[fut]
            try: results[d]=fut.result()
            except Exception as e: results[d]={"domain":d,"requested_url":f"https://{d}/","final_url":"","http_status":"","content_type":"","title":"","text":"","error":repr(e)}
    detail=[]
    for d,rs in domain_rows.items():
        net=results[d]
        page=norm((net.get("title") or "")+" "+(net.get("text") or ""))
        page_digits=digits(net.get("text") or "")
        for r in rs:
            bn=norm_business(r["business_name"])
            phone=digits(r["phone"])
            loc=municipality_fragment(r["address"])
            name_match=bool(bn and len(bn)>=4 and bn in page)
            phone_match=bool(phone and len(phone)>=9 and phone in page_digits)
            locality_match=bool(loc and len(loc)>=4 and loc in page)
            identity_match=phone_match or name_match or (len(bn)>=3 and bn in page and locality_match)
            if not net.get("final_url"):
                status="NO_RESPONSE"
                ev=net.get("error") or "No HTTP response"
            elif identity_match:
                status="LIVE_IDENTITY_MATCH"
                ev=";".join(x for x,ok in [("BUSINESS_NAME",name_match),("PHONE",phone_match),("LOCALITY",locality_match)] if ok)
            else:
                status="LIVE_UNCONFIRMED"
                ev="Live domain but business identity not machine-confirmed"
            detail.append({
                "source_name":r["source_name"],"source_url":r["source_url"],"prefecture":r["prefecture"],"business_name":r["business_name"],"address":r["address"],"phone":r["phone"],"email":r["email"],"email_domain":d,
                "requested_url":net.get("requested_url",""),"final_url":net.get("final_url",""),"http_status":net.get("http_status",""),"title":net.get("title",""),"domain_status":status,"identity_match":"YES" if identity_match else "NO","evidence":ev
            })
    fields=["source_name","source_url","prefecture","business_name","address","phone","email","email_domain","requested_url","final_url","http_status","title","domain_status","identity_match","evidence"]
    with open(OUT/"domain_http_source_results.csv","w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(detail)
    return detail

def main():
    parse_jalc()
    parse_ibaraki()
    parse_table_page("一般社団法人広島市造園建設業協会 協会員","https://www.sizoukyo.or.jp/","広島県")
    parse_table_page("沖縄県緑化種苗協同組合 組合員一覧","https://okiryoku.org/member/","沖縄県")
    parse_table_page("一般社団法人秋田県造園協会 役員・会員名簿","https://akita-kenzokyo.com/memberlist","秋田県")
    crawl_chiba()
    uniq={}
    for r in rows:
        k=(r["source_url"],r["business_name"],r["address"],r["email"])
        uniq[k]=r
    outrows=list(uniq.values())
    outrows.sort(key=lambda r:(r["prefecture"],r["source_name"],r["business_name"],r["email"]))
    fields=["source_name","source_url","prefecture","business_name","address","phone","email","website","retrieved_at"]
    with open(OUT/"public_email_source_rows.csv","w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(outrows)
    with open(OUT/"source_fetch_log.csv","w",encoding="utf-8-sig",newline="") as f:
        fields2=["source_name","source_url","status","bytes","elapsed","error"]
        w=csv.DictWriter(f,fieldnames=fields2); w.writeheader(); w.writerows(logs)
    domain_detail=domain_precheck(outrows)
    dc={}
    for r in domain_detail: dc[r["domain_status"]]=dc.get(r["domain_status"],0)+1
    stats={"raw_rows":len(rows),"dedup_rows":len(outrows),"unique_emails":len({r['email'] for r in outrows}),"prefectures":len({r['prefecture'] for r in outrows}),"sources":len({r['source_url'] for r in outrows}),"fetch_errors":sum(str(r['status'])=='ERROR' for r in logs),"domain_result_rows":len(domain_detail),"domain_status":dc}
    (OUT/"source_discovery_stats.json").write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(stats,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
