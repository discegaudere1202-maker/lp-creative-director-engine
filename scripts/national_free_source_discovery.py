#!/usr/bin/env python3
import csv, json, re, time
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

def add(source_name, source_url, prefecture, name, address, phone, email, website=""):
    email=clean(email).lower().replace("mailto:","")
    m=EMAIL_RE.search(email)
    if not m: return
    email=m.group(0).lower()
    rows.append({"source_name":source_name,"source_url":source_url,"prefecture":prefecture,"business_name":clean(name),"address":clean(address),"phone":clean(phone),"email":email,"website":clean(website),"retrieved_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())})

def parse_jalc():
    source="一般社団法人日本造園建設業協会 公開会員紹介検索"
    # p_id follows JIS prefecture code 1..47.
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
    # Fallback: line-oriented public member pages.
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
    # Blocks are labelled consistently: 会社名 / 所在地 / TEL / EMAIL / ホームページURL.
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
    # Known pages are also discoverable via the public index; include common fallback list.
    links.update(["https://www.zouen.or.jp/kaiin/chiba_chuou.html","https://www.zouen.or.jp/kaiin/yotsukaido.html"])
    for u in sorted(links):
        parse_table_page(source,u,"千葉県")
        time.sleep(0.15)

def main():
    parse_jalc()
    parse_ibaraki()
    parse_table_page("一般社団法人広島市造園建設業協会 協会員","https://www.sizoukyo.or.jp/","広島県")
    parse_table_page("沖縄県緑化種苗協同組合 組合員一覧","https://okiryoku.org/member/","沖縄県")
    parse_table_page("一般社団法人秋田県造園協会 役員・会員名簿","https://akita-kenzokyo.com/memberlist","秋田県")
    crawl_chiba()

    # Exact-row dedupe only; source provenance is retained.
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
    stats={"raw_rows":len(rows),"dedup_rows":len(outrows),"unique_emails":len({r['email'] for r in outrows}),"prefectures":len({r['prefecture'] for r in outrows}),"sources":len({r['source_url'] for r in outrows}),"fetch_errors":sum(str(r['status'])=='ERROR' for r in logs)}
    (OUT/"source_discovery_stats.json").write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(stats,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
