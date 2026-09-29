from pathlib import Path

p = Path('painting_public_email_production.py')
txt = p.read_text(encoding='utf-8')

needle = " {'source_id':'PAINT-SRC-KUMAMOTO-COOP','source_name':'熊本県塗装防水仕上業協同組合','source_type':'塗装・防水協同組合','source_url':'https://www.kumamoto-tosou.jp/','prefecture':'熊本県','coverage_scope':'PREFECTURE','estimated_members':'','public_email_field':'DISCOVER','public_website_field':'DISCOVER','phone_field':'DISCOVER','address_field':'DISCOVER','representative_field':'DISCOVER','access_method':'HTML_CRAWL','join_keys':'normalized_business_name+address; phone','production_status':'DISCOVERY'},\n]"
replacement = """ {'source_id':'PAINT-SRC-KUMAMOTO-COOP','source_name':'熊本県塗装防水仕上業協同組合','source_type':'塗装・防水協同組合','source_url':'https://www.kumamoto-tosou.jp/','prefecture':'熊本県','coverage_scope':'PREFECTURE','estimated_members':'','public_email_field':'DISCOVER','public_website_field':'DISCOVER','phone_field':'DISCOVER','address_field':'DISCOVER','representative_field':'DISCOVER','access_method':'HTML_CRAWL','join_keys':'normalized_business_name+address; phone','production_status':'DISCOVERY'},
 {'source_id':'PAINT-SRC-NIIGATA-NITTOSO','source_name':'日本塗装工業会 新潟県支部 会員紹介','source_type':'業界団体・都道府県支部','source_url':'https://niigata-nittoso.jp/introduction/','prefecture':'新潟県','coverage_scope':'PREFECTURE','estimated_members':'','public_email_field':'YES','public_website_field':'PARTIAL','phone_field':'YES','address_field':'YES','representative_field':'YES','access_method':'HTML_TABLE','join_keys':'normalized_business_name+address; phone; representative','production_status':'ACTIVE'},
 {'source_id':'PAINT-SRC-SHIZUOKA-COOP','source_name':'静岡県塗装看板業協同組合 組合員一覧','source_type':'塗装看板協同組合','source_url':'https://seitokyo.com/member-list/','prefecture':'静岡県','coverage_scope':'PREFECTURE','estimated_members':'209','public_email_field':'YES','public_website_field':'YES','phone_field':'YES','address_field':'YES','representative_field':'YES','access_method':'HTML_TABLE','join_keys':'normalized_business_name+address; phone; representative','production_status':'ACTIVE'},
 {'source_id':'PAINT-SRC-GUNMA-COOP','source_name':'群馬県塗装看板協同組合 組合員一覧','source_type':'塗装看板協同組合','source_url':'https://guntokan.com/category/kumiaiin/','prefecture':'群馬県','coverage_scope':'PREFECTURE','estimated_members':'82','public_email_field':'YES','public_website_field':'PARTIAL','phone_field':'YES','address_field':'YES','representative_field':'YES','access_method':'HTML_TABLE','join_keys':'normalized_business_name+address; phone; representative','production_status':'ACTIVE'},
]"""
if needle not in txt:
    raise SystemExit('seed insertion anchor not found')
txt = txt.replace(needle, replacement, 1)

start = txt.index('def extract_nittoso_pdf(source):')
end = txt.index('\n# --- Generic HTML extraction ---', start)
newfunc = r'''def extract_nittoso_pdf(source):
    """Extract the structured 8-column Nittoso national member table."""
    out=[]; pdf_path=OUT/'nittoso_member.pdf'
    r=get(source['source_url'],45)
    if not r or r.status_code!=200: return out, {'error':'download_failed'}
    pdf_path.write_bytes(r.content)
    page_debug=[]; total_business_rows=0
    with pdfplumber.open(str(pdf_path)) as pdf:
        for pno,page in enumerate(pdf.pages,1):
            tables=page.extract_tables() or []
            page_rows=0; page_email_rows=0
            for tab in tables:
                for raw in tab:
                    if not raw: continue
                    cells=[nfkc(x or '') for x in raw]
                    if not cells or any('会社名' in x for x in cells): continue
                    if len(cells)<7: continue
                    zipi=next((i for i,x in enumerate(cells) if re.fullmatch(r'\d{3}-?\d{4}',x.replace('〒','').strip())), -1)
                    if zipi<2 or zipi+4>=len(cells): continue
                    company=cells[zipi-2]; rep=cells[zipi-1]; address=cells[zipi+1]; tel=cells[zipi+2]
                    email_cell=cells[zipi+4] if zipi+4<len(cells) else ''
                    url=cells[zipi+5] if zipi+5<len(cells) else ''
                    total_business_rows += 1; page_rows += 1
                    em=norm_email(email_cell)
                    if not em: continue
                    if not company or not any(pref in address for pref in PREFS): continue
                    out.append(source_row(source,company,address,tel,rep,em,url,email_cell))
                    page_email_rows += 1
            page_debug.append({'page':pno,'business_rows':page_rows,'email_rows':page_email_rows})
    return out, {'pages':len(page_debug),'business_rows':total_business_rows,'page_rows':page_debug,'email_rows':len(out)}
'''
txt = txt[:start] + newfunc + txt[end:]
p.write_text(txt, encoding='utf-8')
print('patched runner bytes', p.stat().st_size)
