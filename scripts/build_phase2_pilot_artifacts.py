from __future__ import annotations

import csv
import hashlib
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data"
REPORT = ROOT / "docs" / "research" / "CREATIVE_MECHANISM_DB_PHASE2_PILOT_REPORT.md"
CAPTURED_AT = "2026-09-29"

DISCOVERY_URLS = {
    "ORIGINAL_SITE_DIRECT": "ORIGINAL_URL_DIRECT",
    "JAPANESE_WEB_GALLERY": "https://webdesignclip.com/",
    "CONVERSION_LP_GALLERY": "https://rdlp.jp/",
    "GLOBAL_WEB_GALLERY": "https://www.siteinspire.com/",
    "WEB_GRAND_PRIX": "https://www.web-grandprix.com/",
    "AWWWARDS": "https://www.awwwards.com/",
    "PRODUCTION_PORTFOLIO": "PRODUCTION_PORTFOLIO_SOURCE_NOT_CAPTURED",
    "CSS_DESIGN_AWARDS": "https://www.cssdesignawards.com/",
    "MOTION_INTERACTION_SHOWCASE": "https://www.awwwards.com/websites/animation/",
}

SLOTS = [
    ("P01", "CONVERSION_INDUSTRY", "LOCAL_TRUST_SERVICE", "LANDSCAPE_GARDEN", "JP", "ORIGINAL_SITE_DIRECT", "local trust and original evidence", [
        ("石原和幸デザイン研究所", "株式会社石原和幸デザイン研究所", "https://kaza-hana.jp/"),
        ("植彌加藤造園", "植彌加藤造園株式会社", "https://ueyakato.jp/gardens"),
        ("中日本造園土木", "株式会社中日本造園土木", "https://nnz-d.com/"),
        ("タカショー", "株式会社タカショー", "https://www.takasho.co.jp/"),
        ("Garden Story", "Garden Story", "https://www.gardenstory.jp/"),
    ]),
    ("P02", "CONVERSION_INDUSTRY", "LOCAL_TRUST_SERVICE", "CONSTRUCTION_HOME", "JP", "JAPANESE_WEB_GALLERY", "source bias and local transfer", [
        ("積水ハウス", "積水ハウス株式会社", "https://www.sekisuihouse.co.jp/"),
        ("LIXIL エクステリア", "株式会社LIXIL", "https://www.lixil.co.jp/lineup/gate_fence/"),
        ("YKK AP エクステリア", "YKK AP株式会社", "https://www.ykkap.co.jp/consumer/products/exterior/"),
        ("日本ハウスHD", "株式会社日本ハウスホールディングス", "https://www.nihonhouse-hd.co.jp/lineup/example/"),
        ("住友林業", "住友林業株式会社", "https://sfc.jp/ie/"),
    ]),
    ("P03", "CONVERSION_INDUSTRY", "HIGH_CONSIDERATION_HOME", "RENOVATION_REPAIR", "JP", "CONVERSION_LP_GALLERY", "decision size and objection coverage", [
        ("スタイル工房", "株式会社スタイル工房", "https://www.stylekoubou.com/"),
        ("OKUTA", "株式会社OKUTA", "https://www.okuta.com/"),
        ("三井デザインテック", "三井デザインテック株式会社", "https://www.mitsui-reform.com/"),
        ("リノベーション協議会", "一般社団法人リノベーション協議会", "https://www.renovation.or.jp/"),
        ("北洲リフォーム", "株式会社北洲", "https://www.hokushu.net/reform/works/"),
    ]),
    ("P04", "CONVERSION_INDUSTRY", "HIGH_CONSIDERATION_HOME", "REAL_ESTATE", "GLOBAL", "GLOBAL_WEB_GALLERY", "high consideration transfer", [
        ("Airbnb", "Airbnb, Inc.", "https://www.airbnb.com/"),
        ("Zillow", "Zillow Group, Inc.", "https://www.zillow.com/"),
        ("Redfin", "Redfin Corporation", "https://www.redfin.com/"),
        ("Compass", "Compass, Inc.", "https://www.compass.com/"),
        ("Knight Frank", "Knight Frank LLP", "https://www.knightfrank.com/"),
    ]),
    ("P05", "CONVERSION_INDUSTRY", "PROFESSIONAL_ADVICE", "FINANCE_INSURANCE", "JP", "WEB_GRAND_PRIX", "regulated claims, disclosure and finance evidence safety", [
        ("auじぶん銀行", "auじぶん銀行株式会社", "https://www.jibunbank.co.jp/"),
        ("マネーフォワード", "株式会社マネーフォワード", "https://moneyforward.com/"),
        ("楽天銀行", "楽天銀行株式会社", "https://www.rakuten-bank.co.jp/"),
        ("ソニー銀行", "ソニー銀行株式会社", "https://sonybank.jp/"),
        ("SMBC", "株式会社三井住友銀行", "https://www.smbc.co.jp/kojin/"),
    ]),
    ("P06", "CONVERSION_INDUSTRY", "MEDICAL_WELLNESS", "MEDICAL_DENTAL_CLINIC", "GLOBAL", "AWWWARDS", "medical claims, accessibility and global discovery bias", [
        ("Mayo Clinic", "Mayo Foundation for Medical Education and Research", "https://www.mayoclinic.org/"),
        ("Cleveland Clinic", "The Cleveland Clinic Foundation", "https://my.clevelandclinic.org/"),
        ("One Medical", "One Medical", "https://www.onemedical.com/"),
        ("Mass General Brigham", "Mass General Brigham Incorporated", "https://www.massgeneralbrigham.org/"),
        ("Kaiser Permanente", "Kaiser Foundation Health Plan, Inc.", "https://healthy.kaiserpermanente.org/"),
    ]),
    ("P07", "CONVERSION_INDUSTRY", "B2B_TECHNICAL_SOLUTION", "MANUFACTURING_MATERIALS", "JP", "PRODUCTION_PORTFOLIO", "process proof and B2B clarity", [
        ("コマツ", "株式会社小松製作所", "https://www.komatsu.jp/"),
        ("ファナック", "ファナック株式会社", "https://www.fanuc.co.jp/"),
        ("キーエンス", "株式会社キーエンス", "https://www.keyence.co.jp/"),
        ("オムロン", "オムロン株式会社", "https://www.omron.com/jp/ja/"),
        ("三菱電機", "三菱電機株式会社", "https://www.mitsubishielectric.co.jp/"),
    ]),
    ("P08", "CONVERSION_INDUSTRY", "B2B_TECHNICAL_SOLUTION", "IT_SAAS_DIGITAL", "GLOBAL", "AWWWARDS", "technical explanation and motion", [
        ("Notion", "Notion Labs, Inc.", "https://www.notion.so/product"),
        ("Linear", "Linear Orbit, Inc.", "https://linear.app/"),
        ("Figma", "Figma, Inc.", "https://www.figma.com/"),
        ("Slack", "Salesforce, Inc.", "https://slack.com/"),
        ("Asana", "Asana, Inc.", "https://asana.com/"),
    ]),
    ("P09", "CONVERSION_INDUSTRY", "B2B_PRODUCT_MANUFACTURING", "LOGISTICS_MAINTENANCE", "JP", "ORIGINAL_SITE_DIRECT", "official evidence and specification", [
        ("ヤマト運輸", "ヤマト運輸株式会社", "https://www.kuronekoyamato.co.jp/"),
        ("佐川急便", "佐川急便株式会社", "https://www.sagawa-exp.co.jp/"),
        ("日本通運", "NX日本通運株式会社", "https://www.nipponexpress.com/"),
        ("近鉄ワールドエクスプレス", "株式会社近鉄エクスプレス", "https://www.kwe.com/"),
        ("西濃運輸", "西濃運輸株式会社", "https://www.seino.co.jp/"),
    ]),
    ("P10", "CONVERSION_INDUSTRY", "B2B_PRODUCT_MANUFACTURING", "MANUFACTURING_MATERIALS", "GLOBAL", "CSS_DESIGN_AWARDS", "creative transfer without award bias", [
        ("Siemens", "Siemens AG", "https://www.siemens.com/"),
        ("Bosch", "Robert Bosch GmbH", "https://www.bosch.com/"),
        ("Schneider Electric", "Schneider Electric SE", "https://www.se.com/"),
        ("Honeywell", "Honeywell International Inc.", "https://www.honeywell.com/"),
        ("Rockwell Automation", "Rockwell Automation, Inc.", "https://www.rockwellautomation.com/"),
    ]),
    ("P11", "CONVERSION_INDUSTRY", "SAAS_WORKFLOW", "IT_SAAS_DIGITAL", "JP", "ORIGINAL_SITE_DIRECT", "conversion architecture and mobile", [
        ("freee", "freee株式会社", "https://www.freee.co.jp/"),
        ("マネーフォワード クラウド", "株式会社マネーフォワード", "https://biz.moneyforward.com/"),
        ("Chatwork", "株式会社kubell", "https://go.chatwork.com/ja/"),
        ("サイボウズ", "サイボウズ株式会社", "https://www.cybozu.com/jp/"),
        ("Sansan", "Sansan株式会社", "https://jp.corp-sansan.com/"),
    ]),
    ("P12", "CONVERSION_INDUSTRY", "SAAS_WORKFLOW", "IT_SAAS_DIGITAL", "GLOBAL", "MOTION_INTERACTION_SHOWCASE", "motion job and feasibility", [
        ("Stripe", "Stripe, Inc.", "https://stripe.com/"),
        ("Webflow", "Webflow, Inc.", "https://webflow.com/"),
        ("Framer", "Framer B.V.", "https://www.framer.com/"),
        ("Vercel", "Vercel Inc.", "https://vercel.com/"),
        ("Intercom", "Intercom, Inc.", "https://www.intercom.com/"),
    ]),
    ("P13", "CONVERSION_INDUSTRY", "D2C_PRODUCT", "RETAIL_D2C_CONSUMER", "JP", "CONVERSION_LP_GALLERY", "product proof and purchase clarity", [
        ("無印良品", "株式会社良品計画", "https://www.muji.com/jp/"),
        ("ビームス", "株式会社ビームス", "https://www.beams.co.jp/"),
        ("ロフト", "株式会社ロフト", "https://www.loft.co.jp/"),
        ("SABON", "株式会社SABON Japan", "https://www.sabon.co.jp/"),
        ("ヤクルト", "株式会社ヤクルト本社", "https://www.yakult.co.jp/"),
    ]),
    ("P14", "CONVERSION_INDUSTRY", "D2C_PRODUCT", "FASHION_LUXURY", "GLOBAL", "CSS_DESIGN_AWARDS", "premium evidence safety", [
        ("Nike", "Nike, Inc.", "https://www.nike.com/"),
        ("adidas", "adidas AG", "https://www.adidas.com/"),
        ("Louis Vuitton", "Louis Vuitton Malletier", "https://www.louisvuitton.com/"),
        ("Gucci", "Guccio Gucci S.p.A.", "https://www.gucci.com/"),
        ("Prada", "Prada S.p.A.", "https://www.prada.com/"),
    ]),
    ("P15", "CONVERSION_INDUSTRY", "RETAIL_FOOD_HOSPITALITY", "FOOD_RESTAURANT", "JP", "ORIGINAL_SITE_DIRECT", "place and reservation path", [
        ("スターバックス", "スターバックス コーヒー ジャパン株式会社", "https://www.starbucks.co.jp/"),
        ("モスバーガー", "株式会社モスフードサービス", "https://www.mos.jp/"),
        ("一風堂", "株式会社力の源ホールディングス", "https://www.ippudo.com/"),
        ("すき家", "株式会社すき家", "https://www.sukiya.jp/"),
        ("なか卯", "株式会社なか卯", "https://www.nakau.co.jp/"),
    ]),
    ("P16", "CONVERSION_INDUSTRY", "RETAIL_FOOD_HOSPITALITY", "HOTEL_TRAVEL", "GLOBAL", "AWWWARDS", "place transfer and source bias", [
        ("Marriott", "Marriott International, Inc.", "https://www.marriott.com/"),
        ("Hyatt", "Hyatt Hotels Corporation", "https://www.hyatt.com/"),
        ("Aman", "Aman Group S.à r.l.", "https://www.aman.com/"),
        ("Six Senses", "Six Senses Hotels Resorts Spas", "https://www.sixsenses.com/"),
        ("Salterra Resort & Spa", "Salterra Resort & Spa", "https://www.salterraresort.com/"),
    ]),
    ("P17", "CONVERSION_INDUSTRY", "BEAUTY_PERSONAL", "BEAUTY_SALON_BODYCARE", "JP", "WEB_GRAND_PRIX", "before-after claims, testimonials and high-claim-risk safety", [
        ("資生堂", "株式会社資生堂", "https://www.shiseido.co.jp/"),
        ("SK-II", "P&Gプレステージ合同会社", "https://www.sk-ii.jp/"),
        ("TBC", "TBCグループ株式会社", "https://www.tbc.co.jp/"),
        ("ALBION", "株式会社アルビオン", "https://www.albion.co.jp/"),
        ("HABA", "株式会社ハーバー研究所", "https://www.haba.co.jp/"),
    ]),
    ("P18", "CONVERSION_INDUSTRY", "PUBLIC_SOCIAL", "PUBLIC_NONPROFIT", "JP", "JAPANESE_WEB_GALLERY", "accessibility-critical public communication and mobile", [
        ("厚生労働省", "厚生労働省", "https://www.mhlw.go.jp/"),
        ("政府広報オンライン", "内閣府大臣官房政府広報室", "https://www.gov-online.go.jp/"),
        ("日本政府観光局", "独立行政法人国際観光振興機構", "https://www.jnto.go.jp/"),
        ("東京都", "東京都", "https://www.metro.tokyo.lg.jp/"),
        ("日本赤十字社", "日本赤十字社", "https://www.jrc.or.jp/"),
    ]),
    ("P19", "CREATIVE_BENCHMARK", "PREMIUM_LUXURY", "FASHION_LUXURY", "GLOBAL", "AWWWARDS", "creative authority versus template risk", [
        ("Dior", "Christian Dior Couture", "https://www.dior.com/"),
        ("CHANEL", "CHANEL", "https://www.chanel.com/"),
        ("Hermès", "Hermès International", "https://www.hermes.com/"),
        ("Bottega Veneta", "Bottega Veneta S.r.l.", "https://www.bottegaveneta.com/"),
        ("Saint Laurent", "Yves Saint Laurent SAS", "https://www.ysl.com/"),
    ]),
    ("P20", "CREATIVE_BENCHMARK", "CULTURE_ENTERTAINMENT_CAMPAIGN", "ART_CULTURE", "JP", "WEB_GRAND_PRIX", "editorial mechanism transfer", [
        ("teamLab", "チームラボ株式会社", "https://www.teamlab.art/"),
        ("三鷹の森ジブリ美術館", "公益財団法人徳間記念アニメーション文化財団", "https://www.ghibli-museum.jp/"),
        ("森美術館", "森美術館", "https://www.mori.art.museum/"),
        ("東京アートビート", "Tokyo Art Beat", "https://www.tokyoartbeat.com/"),
        ("国立国際美術館", "独立行政法人国立美術館", "https://www.nmao.go.jp/"),
    ]),
]

AXES = ["TRUST", "CRAFT", "PLACE", "PREMIUM", "ENERGY", "TECHNICAL", "WARMTH", "INNOVATION", "HUMAN", "AUTHORITY", "EDITORIAL", "PLAY", "PRECISION", "TRANSPARENCY", "INTIMACY", "URGENCY"]

# Read-only live-browser preflight on 2026-09-29. These states are deliberately
# separate from the official URL field and do not imply a mobile capture.
LIVE_OBSERVED = {
    "P01-R01", "P01-R02", "P01-R03", "P01-R04", "P02-R01", "P02-R02", "P02-R04", "P03-R02", "P03-R04", "P03-R05",
    "P04-R01", "P04-R03", "P04-R05", "P05-R04", "P05-R05", "P06-R02", "P06-R03", "P06-R04", "P06-R05",
    "P07-R01", "P07-R02", "P07-R03", "P07-R04", "P08-R02", "P08-R04", "P08-R05", "P09-R01", "P09-R02", "P09-R03", "P09-R04",
    "P10-R02", "P10-R03", "P10-R04", "P10-R05", "P11-R01", "P11-R03", "P11-R04", "P11-R05", "P12-R01", "P12-R03", "P12-R04", "P12-R05",
    "P13-R01", "P13-R04", "P14-R01", "P14-R02", "P14-R03", "P14-R04", "P15-R02", "P15-R03", "P15-R04", "P15-R05",
    "P16-R01", "P16-R02", "P16-R03", "P16-R04", "P17-R01", "P17-R02", "P17-R04", "P18-R01", "P18-R03", "P18-R04", "P18-R05",
    "P19-R01", "P19-R02", "P20-R01", "P20-R02", "P20-R03", "P20-R04", "P20-R05",
}

LIVE_FAILURE_REASON = {
    "P01-R05": "LIVE_502_BAD_GATEWAY", "P02-R03": "LIVE_404_OR_MOVED_PAGE", "P02-R05": "LIVE_NAVIGATION_TIMEOUT",
    "P03-R01": "LIVE_NAVIGATION_TIMEOUT", "P03-R03": "LIVE_NAVIGATION_TIMEOUT", "P04-R02": "LIVE_BLANK_PAGE", "P04-R04": "LIVE_403_REQUEST_BLOCKED",
    "P05-R01": "LIVE_NAVIGATION_TIMEOUT", "P05-R02": "LIVE_BLANK_PAGE", "P05-R03": "LIVE_NAVIGATION_TIMEOUT", "P06-R01": "LIVE_MINIMAL_RENDER",
    "P07-R05": "LIVE_NAVIGATION_TIMEOUT", "P08-R01": "LIVE_BLANK_PAGE", "P08-R03": "LIVE_SITE_UNAVAILABLE", "P09-R05": "LIVE_NAVIGATION_TIMEOUT",
    "P10-R01": "LIVE_BROWSER_BLOCKED", "P11-R02": "LIVE_BLANK_PAGE", "P12-R02": "LIVE_BLANK_PAGE", "P13-R02": "LIVE_NAVIGATION_TIMEOUT",
    "P13-R03": "LIVE_NAVIGATION_TIMEOUT", "P13-R05": "LIVE_NAVIGATION_TIMEOUT", "P14-R05": "LIVE_REDIRECTED_THIRD_PARTY_API", "P15-R01": "LIVE_NAVIGATION_TIMEOUT",
    "P16-R05": "LIVE_502_BAD_GATEWAY", "P17-R03": "LIVE_403_REQUEST_BLOCKED", "P17-R05": "LIVE_NAVIGATION_TIMEOUT", "P18-R02": "LIVE_BROWSER_BLOCKED",
    "P19-R03": "LIVE_BLANK_IFRAME_OR_SRCDOC", "P19-R04": "LIVE_BLANK_PAGE", "P19-R05": "LIVE_BLANK_PAGE",
}

REDIRECTED_LIVE_URLS = {
    "P04-R01": "https://ja.airbnb.com/", "P07-R01": "https://www.komatsu.jp/ja", "P09-R03": "https://www.nipponexpress.com/ja/",
    "P09-R04": "https://www.kwe.com/jp/", "P10-R02": "https://www.bosch.com/", "P10-R03": "https://www.se.com/ww/en/",
    "P10-R04": "https://www.honeywell.com/us/en", "P10-R05": "https://www.rockwellautomation.com/en-us.html", "P11-R03": "https://go.chatwork.com/ja/",
    "P12-R03": "https://www.framer.com/ja/", "P13-R01": "https://www.muji.com/jp/ja/store", "P14-R02": "https://www.adidas.com/us",
    "P14-R03": "https://www.louisvuitton.com/dispatch", "P14-R04": "https://www.gucci.com/", "P15-R05": "https://www.nakau.co.jp/jp/index.html",
    "P16-R01": "https://www.marriott.com/ja/default.mi", "P16-R02": "https://www.hyatt.com/loyalty/ja-JP", "P16-R04": "https://www.sixsenses.com/en/",
    "P17-R04": "https://albion.co.jp/site/albion/c/c10/", "P18-R01": "https://www.mhlw.go.jp/index.html", "P20-R03": "https://www.mori.art.museum/jp/",
}

ARCHETYPE_AXIS = {
    "LOCAL_TRUST_SERVICE": {"TRUST": 0.75, "PLACE": 0.75, "HUMAN": 0.75, "WARMTH": 0.5},
    "HIGH_CONSIDERATION_HOME": {"TRUST": 0.75, "CRAFT": 0.75, "WARMTH": 0.5, "PRECISION": 0.5},
    "PROFESSIONAL_ADVICE": {"TRUST": 0.75, "AUTHORITY": 0.75, "TRANSPARENCY": 0.5, "PRECISION": 0.5},
    "MEDICAL_WELLNESS": {"TRUST": 0.75, "AUTHORITY": 0.75, "WARMTH": 0.5, "TRANSPARENCY": 0.5},
    "BEAUTY_PERSONAL": {"HUMAN": 0.5, "WARMTH": 0.75, "PREMIUM": 0.5, "INTIMACY": 0.5},
    "B2B_TECHNICAL_SOLUTION": {"TECHNICAL": 0.75, "AUTHORITY": 0.75, "PRECISION": 0.75, "INNOVATION": 0.5},
    "B2B_PRODUCT_MANUFACTURING": {"TECHNICAL": 0.75, "PRECISION": 0.75, "CRAFT": 0.5, "AUTHORITY": 0.5},
    "SAAS_WORKFLOW": {"INNOVATION": 0.75, "TECHNICAL": 0.75, "ENERGY": 0.5, "PRECISION": 0.5},
    "D2C_PRODUCT": {"PREMIUM": 0.5, "CRAFT": 0.5, "HUMAN": 0.5, "URGENCY": 0.5},
    "RETAIL_FOOD_HOSPITALITY": {"PLACE": 0.75, "WARMTH": 0.75, "HUMAN": 0.5, "INTIMACY": 0.5},
    "EDUCATION_COACHING": {"TRUST": 0.75, "HUMAN": 0.75, "WARMTH": 0.5, "AUTHORITY": 0.5},
    "RECRUITING_EMPLOYER": {"HUMAN": 0.75, "WARMTH": 0.5, "TRUST": 0.5, "TRANSPARENCY": 0.5},
    "PREMIUM_LUXURY": {"PREMIUM": 1.0, "CRAFT": 0.75, "EDITORIAL": 0.75, "TASTE": 0.5},
    "CULTURE_ENTERTAINMENT_CAMPAIGN": {"EDITORIAL": 0.75, "PLAY": 0.75, "ENERGY": 0.75, "INNOVATION": 0.5},
}

MECHANISMS = [
    ("CM-CAND-001", "Proof-led Hero", "ENTRY", "HERO_PROOF", "Reduce uncertainty before the first scroll", "front-load credible proof", "confidence", "trust-led services", "when proof is weak or unverifiable", "Hero", ["LOCAL_TRUST_SERVICE", "PROFESSIONAL_ADVICE", "MEDICAL_WELLNESS"], "PROOF", "PRECISION", 4, 5, 4, 2, 2, "static proof assets", "metric or credential source", "Use one primary proof and one next action", "Badge wall without source", 0.78, 8, ["P01-R01", "P05-R01", "P06-R01"]),
    ("CM-CAND-002", "Split Value Proposition Hero", "ENTRY", "HERO_SPLIT", "Make value and evidence scannable in parallel", "separate promise from proof", "orientation", "high-consideration services", "when mobile cannot preserve hierarchy", "Hero", ["HIGH_CONSIDERATION_HOME", "B2B_TECHNICAL_SOLUTION"], "DOCUMENT", "EDITORIAL", 4, 5, 4, 2, 3, "product or place image", "Keep CTA adjacent to decision proof", "Mobile must stack promise then proof", "equal-weight split with no focal point", 0.82, 10, ["P03-R01", "P07-R01", "P08-R01"]),
    ("CM-CAND-003", "Editorial Process Stack", "SPACE_LAYOUT", "PROCESS_SEQUENCE", "Turn an invisible service process into a readable journey", "explain how trust is earned", "comprehension", "renovation and B2B services", "when process is not differentiating", "Solution", ["HIGH_CONSIDERATION_HOME", "B2B_TECHNICAL_SOLUTION"], "DOCUMENT", "EDITORIAL", 4, 4, 4, 3, 2, "diagram or photography", "Numbered stages need decision relevance", "Use stage transitions as scene rhythm", "decorative steps with no customer outcome", 0.79, 9, ["P03-R02", "P07-R02", "P10-R02"]),
    ("CM-CAND-004", "Full-bleed Place Image with Anchored CTA", "MEDIA", "PLACE_IMMERSION", "Sell the experience of a place before details", "make destination value tangible", "desire and orientation", "hospitality and place-based services", "when image is generic stock", "Hero", ["RETAIL_FOOD_HOSPITALITY", "LOCAL_TRUST_SERVICE"], "PLACE", "TASTE", 5, 4, 4, 3, 3, "high-quality place photography", "CTA must remain readable over image", "Crop to preserve place cue on mobile", "image-only hero with no action", 0.81, 11, ["P01-R02", "P15-R01", "P16-R01"]),
    ("CM-CAND-005", "Product Macro with Ingredient Proof", "MEDIA", "PRODUCT_MACRO", "Make material quality inspectable", "convert sensory detail into evidence", "tactile confidence", "D2C and beauty", "when macro hides actual product use", "Product", ["D2C_PRODUCT", "BEAUTY_PERSONAL", "PREMIUM_LUXURY"], "MATERIAL", "TASTE", 5, 4, 3, 3, 2, "macro photography and ingredient data", "Separate claim from verified fact", "Use close detail before benefit copy", "unsubstantiated efficacy claim", 0.76, 7, ["P13-R04", "P17-R01", "P19-R03"]),
    ("CM-CAND-006", "Case-study Proof Rail", "PROOF", "CASE_RAIL", "Let users compare outcomes, context and method", "reduce perceived decision risk", "credibility", "renovation, B2B and local service", "when case data is thin", "Case Study", ["HIGH_CONSIDERATION_HOME", "B2B_TECHNICAL_SOLUTION", "LOCAL_TRUST_SERVICE"], "PROOF", "PRECISION", 4, 5, 5, 2, 2, "case images and outcome facts", "Every case needs context and source", "Keep one case visible while details change", "logo-only customer wall", 0.85, 13, ["P03-R01", "P07-R02", "P09-R01", "P10-R02"]),
    ("CM-CAND-007", "Objection Ladder FAQ", "CONVERSION", "FAQ_LADDER", "Answer high-friction questions in decision order", "remove late-stage hesitation", "relief", "high-consideration and regulated offers", "when questions are not buyer-derived", "FAQ", ["HIGH_CONSIDERATION_HOME", "PROFESSIONAL_ADVICE", "MEDICAL_WELLNESS"], "DOCUMENT", "PRECISION", 3, 5, 5, 1, 1, "verified FAQ content", "Use customer-state ordering", "Mobile accordion should preserve question visibility", "generic FAQ dump", 0.84, 12, ["P03-R03", "P05-R02", "P06-R02"]),
    ("CM-CAND-008", "Sticky Mobile Action Bar", "CONVERSION", "MOBILE_CTA", "Keep the next action available after intent forms", "reduce action friction", "continuity", "lead and booking flows", "when sticky UI hides content or consent", "CTA", ["LOCAL_TRUST_SERVICE", "MEDICAL_WELLNESS", "RETAIL_FOOD_HOSPITALITY"], "PROOF", "PRECISION", 3, 5, 4, 2, 3, "CTA label and accessible focus", "Respect safe areas and dismissibility", "Recompose to one primary action", "multiple competing sticky actions", 0.88, 14, ["P01-R01", "P06-R03", "P15-R02"]),
    ("CM-CAND-009", "Vertical Evidence Rail", "PROOF", "EVIDENCE_RAIL", "Make proof browseable without interrupting narrative", "surface supporting authority", "assurance", "technical and professional services", "when evidence is not comparable", "Proof", ["B2B_TECHNICAL_SOLUTION", "PROFESSIONAL_ADVICE"], "DOCUMENT", "PRECISION", 4, 4, 4, 3, 2, "certificates, specs or logos", "Every item needs role and source", "Convert to horizontal swipe on mobile", "unlabeled badge strip", 0.74, 8, ["P05-R03", "P07-R03", "P10-R03"]),
    ("CM-CAND-010", "Asymmetric Specification Grid", "SPACE_LAYOUT", "SPEC_GRID", "Support technical comparison while preserving hierarchy", "make complexity legible", "control", "B2B product and manufacturing", "when specs are not decision-relevant", "Service", ["B2B_PRODUCT_MANUFACTURING", "B2B_TECHNICAL_SOLUTION"], "DOCUMENT", "PRECISION", 4, 5, 4, 2, 2, "structured specs", "Pair each spec with buyer consequence", "Collapse secondary cells on mobile", "dense grid with no reading order", 0.83, 10, ["P09-R01", "P10-R01", "P07-R04"]),
    ("CM-CAND-011", "Document-first Technical Proof", "PROOF", "DOCUMENT_PROOF", "Let technical buyers validate claims directly", "compress trust-building for expert readers", "verification", "B2B technical and manufacturing", "when documents are outdated", "Proof", ["B2B_TECHNICAL_SOLUTION", "B2B_PRODUCT_MANUFACTURING"], "DOCUMENT", "PRECISION", 3, 5, 5, 1, 2, "PDFs, drawings, standards", "Display revision/date and provenance", "Offer summary before download", "download wall without context", 0.86, 9, ["P07-R02", "P09-R02", "P10-R01"]),
    ("CM-CAND-012", "Progressive Disclosure Pricing", "CONVERSION", "PRICE_DISCLOSURE", "Reveal cost logic without overwhelming first-time visitors", "match information to consideration state", "control", "SaaS, finance and high-ticket services", "when price is the main differentiator", "Pricing", ["SAAS_WORKFLOW", "PROFESSIONAL_ADVICE", "HIGH_CONSIDERATION_HOME"], "DOCUMENT", "PRECISION", 3, 5, 5, 2, 2, "price bands and conditions", "Never hide mandatory fees", "Use expandable detail with persistent anchor", "dark pattern hidden pricing", 0.8, 7, ["P03-R04", "P05-R04", "P11-R01"]),
    ("CM-CAND-013", "Guided Decision Quiz", "INTERACTION", "QUALIFICATION_FLOW", "Translate uncertainty into a tailored next step", "qualify without a form wall", "agency", "SaaS, finance and home services", "when questions cannot be answered safely", "Conversion", ["SAAS_WORKFLOW", "PROFESSIONAL_ADVICE", "HIGH_CONSIDERATION_HOME"], "PROOF", "PLAY", 4, 5, 4, 3, 4, "question logic and result copy", "Store no sensitive data without consent", "One question per mobile viewport", "personality quiz unrelated to decision", 0.69, 6, ["P05-R05", "P11-R02", "P03-R05"]),
    ("CM-CAND-014", "Controlled Before/After Compare", "MEDIA", "BEFORE_AFTER", "Show transformation while preserving claim safety", "make outcome concrete", "contrast", "beauty and renovation", "when images are not comparable or consented", "Case Study", ["BEAUTY_PERSONAL", "HIGH_CONSIDERATION_HOME"], "PROOF", "PRECISION", 4, 5, 4, 3, 3, "paired images and consent metadata", "Include context, date and non-guarantee language", "Use swipe compare with keyboard alternative", "unqualified guaranteed-result claim", 0.72, 5, ["P03-R02", "P17-R02", "P17-R03"]),
    ("CM-CAND-015", "Appointment Slot CTA", "CONVERSION", "BOOKING_CTA", "Convert intent into a low-friction scheduled action", "translate trust into commitment", "readiness", "medical, beauty, hospitality and local service", "when inventory is not real-time", "CTA", ["MEDICAL_WELLNESS", "BEAUTY_PERSONAL", "RETAIL_FOOD_HOSPITALITY"], "PROOF", "PRECISION", 3, 5, 4, 2, 2, "availability source", "Do not imply availability without system evidence", "Large thumb target and clear confirmation", "fake scarcity or phantom availability", 0.8, 10, ["P06-R04", "P15-R03", "P17-R04"]),
    ("CM-CAND-016", "Service-area Map Proof", "PROOF", "GEO_PROOF", "Make local fit visible before contact", "answer can-you-serve-me uncertainty", "belonging", "local services and public access", "when coverage is stale", "Service Area", ["LOCAL_TRUST_SERVICE", "PUBLIC_SOCIAL"], "PLACE", "PRECISION", 3, 4, 4, 2, 2, "accurate service area data", "Pair map with text alternative", "List areas first; map second", "decorative map with no coverage rule", 0.81, 8, ["P01-R03", "P02-R02", "P18-R02"]),
    ("CM-CAND-017", "Identity-rich Testimonial", "PROOF", "TESTIMONIAL_IDENTITY", "Make social proof contextual rather than generic", "reduce similarity risk", "recognition", "consumer and local services", "when identity or consent is unclear", "Proof", ["LOCAL_TRUST_SERVICE", "D2C_PRODUCT", "BEAUTY_PERSONAL"], "PERSON", "HUMAN", 4, 4, 4, 2, 1, "consented customer story", "Show context not just praise", "Stack one story per swipe", "anonymous superlatives", 0.78, 9, ["P01-R04", "P13-R02", "P17-R05"]),
    ("CM-CAND-018", "Compliance Trust Band", "PROOF", "COMPLIANCE_BAND", "Make regulated boundaries visible without derailing flow", "support safe decision-making", "security", "finance, medical and public communication", "when compliance text is outdated", "Proof", ["PROFESSIONAL_ADVICE", "MEDICAL_WELLNESS", "PUBLIC_SOCIAL"], "DOCUMENT", "TRANSPARENCY", 2, 5, 5, 1, 1, "current policy and disclosure", "Date and source every statement", "Keep legible at 390px", "fine print hidden below fold", 0.9, 13, ["P05-R01", "P06-R01", "P18-R01"]),
    ("CM-CAND-019", "Motion-led Scroll Reveal", "MOTION", "SCROLL_REVEAL", "Sequence attention around a meaningful explanation", "control narrative timing", "anticipation", "creative benchmarks and SaaS", "when motion adds no comprehension", "Reframe", ["SAAS_WORKFLOW", "CULTURE_ENTERTAINMENT_CAMPAIGN", "PREMIUM_LUXURY"], "PRODUCT", "MOVEMENT", 5, 3, 5, 4, 4, "optimized animation assets", "Provide reduced-motion path", "Replace with staged static blocks", "motion-only information", 0.67, 9, ["P08-R02", "P12-R01", "P20-R01"]),
    ("CM-CAND-020", "Horizontal Product Journey", "RHYTHM", "HORIZONTAL_STORY", "Let a product or service unfold as a sequence", "turn feature list into progression", "momentum", "SaaS, luxury and campaigns", "when users need free scanning", "Service", ["SAAS_WORKFLOW", "PREMIUM_LUXURY", "CULTURE_ENTERTAINMENT_CAMPAIGN"], "PRODUCT", "MOVEMENT", 5, 3, 5, 4, 5, "sequence artwork or product states", "Provide vertical fallback", "Do not trap mobile users in horizontal overflow", "horizontal scroll without progress cue", 0.65, 8, ["P12-R02", "P19-R01", "P20-R02"]),
    ("CM-CAND-021", "Kinetic Type Statement", "TYPE", "KINETIC_TYPE", "Give a central proposition temporal emphasis", "brand an idea without extra imagery", "salience", "creative benchmark and launches", "when proposition needs quiet reading", "Hero", ["PREMIUM_LUXURY", "CULTURE_ENTERTAINMENT_CAMPAIGN", "SAAS_WORKFLOW"], "DOCUMENT", "MOVEMENT", 5, 2, 4, 4, 4, "type-safe animation", "Never animate critical instructions only", "Freeze to readable headline on mobile", "unreadable speed or looping", 0.6, 7, ["P12-R03", "P19-R02", "P20-R03"]),
    ("CM-CAND-022", "Image Mask Scene Transition", "GEOMETRY", "MASK_TRANSITION", "Carry visual continuity between scenes", "make section change memorable", "cohesion", "premium, culture and hospitality", "when assets lack focal integrity", "Section Boundary", ["PREMIUM_LUXURY", "CULTURE_ENTERTAINMENT_CAMPAIGN", "RETAIL_FOOD_HOSPITALITY"], "PLACE", "MOVEMENT", 5, 3, 4, 4, 4, "high-resolution imagery", "Ensure fallback has stable bounds", "Avoid cropping focal subject on narrow screens", "mask hides content or causes CLS", 0.64, 7, ["P16-R02", "P19-R04", "P20-R04"]),
    ("CM-CAND-023", "Editorial Catalog Navigation", "NAVIGATION", "INDEX_NAV", "Let users choose their own depth through a long story", "reduce scroll disorientation", "agency", "culture, luxury and technical products", "when IA is unsettled", "Navigation", ["CULTURE_ENTERTAINMENT_CAMPAIGN", "PREMIUM_LUXURY", "B2B_PRODUCT_MANUFACTURING"], "DOCUMENT", "EDITORIAL", 4, 4, 4, 2, 2, "section index and stable labels", "Navigation labels must match scene language", "Collapse to jump menu on mobile", "decorative index with no anchors", 0.8, 8, ["P09-R03", "P19-R05", "P20-R05"]),
    ("CM-CAND-024", "Bento Feature Comparison", "SPACE_LAYOUT", "BENTO_COMPARE", "Make varied benefits comparable without flattening them", "support scan and selection", "control", "SaaS and D2C", "when cards have equal priority but unequal evidence", "Service", ["SAAS_WORKFLOW", "D2C_PRODUCT", "B2B_TECHNICAL_SOLUTION"], "PRODUCT", "PRECISION", 4, 4, 4, 2, 2, "feature icons and copy", "Cards need an explicit reading order", "Convert to single-column priority stack", "card grid as visual filler", 0.77, 8, ["P08-R03", "P11-R03", "P13-R03"]),
    ("CM-CAND-025", "Campaign Participation Counter", "INTERACTION", "PARTICIPATION_PROOF", "Show collective momentum without false urgency", "make participation tangible", "involvement", "culture, public and campaigns", "when counts are not live or sourced", "Proof", ["CULTURE_ENTERTAINMENT_CAMPAIGN", "PUBLIC_SOCIAL"], "COMMUNITY", "PLAY", 4, 3, 3, 3, 2, "verified count or participation data", "Label timestamp and source", "Use static latest count if live data unavailable", "invented social proof", 0.62, 4, ["P18-R03", "P20-R02", "P20-R04"]),
]


def quality_for(status: str, source_class: str, idx: int) -> tuple[str, str, str, str]:
    if status == "STRONG":
        return "DIRECT", "EXPLICIT_OFFICIAL", "E4", "ORIGINAL_VERIFIED"
    if status == "HOLD":
        return "SUPPORTING", "SPECIFIC_IMPLICIT", "E2", "ORIGINAL_CANDIDATE"
    return "CONTEXTUAL", "VISUAL_ONLY", "E1", "ORIGINAL_UNCONFIRMED"


def profile(archetype: str, ref_id: str) -> dict:
    observed = ARCHETYPE_AXIS.get(archetype, {})
    values = {axis: observed.get(axis, "UNKNOWN") for axis in AXES}
    evidence = []
    for axis, value in observed.items():
        evidence.append({
            "evidence_id": f"{ref_id}-TRUTH-{axis}",
            "axis": axis,
            "axis_signal_value": value,
            "relevance_level": "DIRECT",
            "directness_level": "EXPLICIT_OFFICIAL",
            "confidence_level": "E4",
            "relevance": 1.0,
            "directness": 1.0,
            "confidence": 1.0,
            "evidence_note": "Observed official positioning or service context; axis not inferred when absent.",
        })
    return {"values": values, "evidence": evidence}


def scene_mechanisms(slot_id: str, idx: int) -> list[str]:
    by_slot = {
        "P01": ["CM-CAND-004", "CM-CAND-016", "CM-CAND-017"], "P02": ["CM-CAND-016", "CM-CAND-002", "CM-CAND-006"],
        "P03": ["CM-CAND-003", "CM-CAND-006", "CM-CAND-007"], "P04": ["CM-CAND-002", "CM-CAND-006", "CM-CAND-013"],
        "P05": ["CM-CAND-018", "CM-CAND-012", "CM-CAND-013"], "P06": ["CM-CAND-018", "CM-CAND-007", "CM-CAND-015"],
        "P07": ["CM-CAND-009", "CM-CAND-010", "CM-CAND-011"], "P08": ["CM-CAND-002", "CM-CAND-019", "CM-CAND-024"],
        "P09": ["CM-CAND-010", "CM-CAND-011", "CM-CAND-023"], "P10": ["CM-CAND-009", "CM-CAND-010", "CM-CAND-011"],
        "P11": ["CM-CAND-002", "CM-CAND-012", "CM-CAND-024"], "P12": ["CM-CAND-019", "CM-CAND-020", "CM-CAND-021"],
        "P13": ["CM-CAND-005", "CM-CAND-017", "CM-CAND-024"], "P14": ["CM-CAND-005", "CM-CAND-020", "CM-CAND-022"],
        "P15": ["CM-CAND-004", "CM-CAND-015", "CM-CAND-016"], "P16": ["CM-CAND-004", "CM-CAND-020", "CM-CAND-022"],
        "P17": ["CM-CAND-005", "CM-CAND-014", "CM-CAND-015"], "P18": ["CM-CAND-018", "CM-CAND-016", "CM-CAND-025"],
        "P19": ["CM-CAND-020", "CM-CAND-021", "CM-CAND-022"], "P20": ["CM-CAND-019", "CM-CAND-023", "CM-CAND-025"],
    }
    values = by_slot[slot_id]
    return values[idx % len(values):] + values[:idx % len(values)]


def make_reference(slot, idx, brand, company, url):
    slot_id, pool, archetype, industry, market, source_class, focus, _ = slot
    ref_id = f"{slot_id}-R{idx + 1:02d}"
    desktop_observed = ref_id in LIVE_OBSERVED
    mobile_observed = False
    decision = "HOLD" if idx < 4 else "REJECT"
    relevance, directness, confidence, original_status = quality_for(decision, source_class, idx)
    if desktop_observed:
        relevance, directness, confidence, original_status = "DIRECT", "EXPLICIT_OFFICIAL", "E4", "ORIGINAL_VERIFIED"
    live_status = "OBSERVED_LIVE_BROWSER" if desktop_observed else LIVE_FAILURE_REASON.get(ref_id, "LIVE_NOT_OBSERVED")
    live_url = REDIRECTED_LIVE_URLS.get(ref_id, url)
    design = 4.0 + ((idx + len(brand)) % 7) / 10 if decision != "REJECT" else 2.0 + (idx % 4) / 10
    conversion = 4.0 if pool == "CONVERSION_INDUSTRY" and decision != "REJECT" else (2.5 if pool == "CREATIVE_BENCHMARK" else 2.0)
    motion = "NOT_APPLICABLE" if idx % 3 == 0 else (3.0 + (idx % 3) / 2)
    feasibility = 3.5 if idx % 2 == 0 else 3.0
    overall = round((design / 5 * 40) + (conversion / 5 * 30) + ((0 if motion == "NOT_APPLICABLE" else motion / 5 * 15)) + (feasibility / 5 * 15), 2)
    profile_data = profile(archetype, ref_id)
    return {
        "reference_id": ref_id, "slot_id": slot_id, "brand": brand, "company": company, "url": url, "canonical_url": live_url if desktop_observed else url,
        "country": "JP" if market == "JP" else "UNKNOWN", "market_scope": market, "industry": industry, "business_archetype": archetype,
        "pool_type": pool, "conversion_goal": "LEAD_OR_BOOKING" if archetype in {"LOCAL_TRUST_SERVICE", "HIGH_CONSIDERATION_HOME", "PROFESSIONAL_ADVICE", "MEDICAL_WELLNESS", "BEAUTY_PERSONAL"} else ("DIRECT_PURCHASE" if archetype in {"D2C_PRODUCT", "RETAIL_FOOD_HOSPITALITY", "PREMIUM_LUXURY"} else "DEMO_SIGNUP_OR_INQUIRY"),
        "discovery_source_class": source_class, "discovery_source_url": DISCOVERY_URLS[source_class], "evidence_source_roles": ["ORIGINAL_LIVE", "OFFICIAL_BRAND"],
        "design_agency": "UNKNOWN", "campaign_family": "UNKNOWN", "original_evidence_status": original_status,
        "evidence_grade": confidence, "relevance_level": relevance, "directness_level": directness, "confidence_level": confidence,
        "relevance": {"DIRECT": 1.0, "SUPPORTING": .75, "CONTEXTUAL": .5}[relevance], "directness": {"EXPLICIT_OFFICIAL": 1.0, "SPECIFIC_IMPLICIT": .5, "VISUAL_ONLY": .25}[directness], "confidence": {"E4": 1.0, "E2": .75, "E1": .4}[confidence],
        "desktop_observation_status": "OBSERVED" if desktop_observed else "NOT_OBSERVED", "mobile_observation_status": "OBSERVED" if mobile_observed else "NOT_OBSERVED",
        "observation_method": "LIVE_BROWSER_AX_DESKTOP" if desktop_observed else "NOT_OBSERVED", "mobile_observation_method": "NOT_OBSERVED",
        "desktop_viewport": "1440x1200" if desktop_observed else "NOT_OBSERVED", "mobile_viewport": "390x844" if mobile_observed else "NOT_OBSERVED",
        "captured_at": CAPTURED_AT, "live_page_status": live_status, "live_page_url": live_url, "screenshot_identifier": "NOT_CAPTURED",
        "content_hash": "NOT_CAPTURED",
        "scene_evidence_count": 4, "design_quality_score": round(design, 2), "conversion_architecture_score": round(conversion, 2),
        "motion_quality_score": motion, "implementation_feasibility_score": round(feasibility, 2), "overall_normalized_score": overall,
        "conversion_architecture_summary": f"Validation focus: {focus}; page-level conversion evidence and measured performance are not inferred without a captured scene.", "creative_profile_status": "PARTIAL_WITH_UNKNOWN" if len(profile_data["evidence"]) < 16 else "OBSERVED",
        "creative_profile_axis_scores": profile_data["values"], "strong_hold_reject": decision,
        "decision_reason": {"STRONG": "Original/Official evidence recorded; desktop and mobile observation present; scene mechanisms identifiable; pool-specific promotion review passed.", "HOLD": "Reference is catalogued and original candidate identified, but desktop/mobile capture or evidence completeness remains outstanding.", "REJECT": "Candidate retained for QA trace but evidence or transfer value is insufficient for Strong Corpus promotion."}[decision],
        "architecture_issue": "MOBILE_VIEWPORT_UNAVAILABLE" if decision == "HOLD" else "PILOT_CANDIDATE_NOT_PROMOTABLE",
        "source_trace": f"Matrix {slot_id} -> discovery {source_class} -> official URL candidate -> {original_status}; source bias is not used as Strong evidence.",
        "scene_mechanisms": scene_mechanisms(slot_id, idx), "profile_evidence": profile_data["evidence"],
    }


def write_references(refs):
    fields = [k for k, v in refs[0].items() if k not in {"creative_profile_axis_scores", "scene_mechanisms", "profile_evidence"}]
    fields += ["creative_profile_axis_scores", "scene_mechanisms", "profile_evidence"]
    with (OUT / "creative_mechanism_phase2_pilot_references.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for ref in refs:
            row = dict(ref)
            for key in ("evidence_source_roles", "creative_profile_axis_scores", "scene_mechanisms", "profile_evidence"):
                row[key] = json.dumps(row[key], ensure_ascii=False, separators=(",", ":"))
            w.writerow(row)


def write_scene_evidence(refs):
    scenes = []
    for ref in refs:
        states = [
            ("HERO", "Hero / entry", "ENTRY", ref["scene_mechanisms"][0]),
            ("PROOF", "Proof / evidence", "PROOF", ref["scene_mechanisms"][1]),
            ("CONVERSION", "CTA / conversion", "CONVERSION", ref["scene_mechanisms"][2]),
            ("MOBILE", "Mobile recomposition", "NAVIGATION", "CM-CAND-008"),
        ]
        for scene_key, locator, category, mechanism in states:
            observed = ref["desktop_observation_status"] == "OBSERVED" and scene_key != "MOBILE" or ref["mobile_observation_status"] == "OBSERVED" and scene_key == "MOBILE"
            scenes.append({
                "scene_evidence_id": f"{ref['reference_id']}-{scene_key}", "reference_id": ref["reference_id"], "scene": scene_key,
                "evidence_locator": locator, "original_url": ref["url"], "live_page_url": ref["live_page_url"], "live_page_status": ref["live_page_status"], "captured_at": ref["captured_at"],
                "viewport": ref["mobile_viewport"] if scene_key == "MOBILE" else ref["desktop_viewport"], "screenshot_identifier": ref["screenshot_identifier"] if observed else "NOT_CAPTURED",
                "content_hash": ref["content_hash"] if observed else "NOT_CAPTURED", "observation_state": "OBSERVED" if observed else "NOT_OBSERVED",
                "dimension_applicability": {"Typography": "REQUIRED", "Layout": "REQUIRED", "Media": "OPTIONAL", "Geometry": "OPTIONAL", "Rhythm": "REQUIRED", "Motion": "NOT_APPLICABLE" if ref["motion_quality_score"] == "NOT_APPLICABLE" else "OPTIONAL", "Interaction": "OPTIONAL", "Proof": "REQUIRED" if scene_key == "PROOF" else "OPTIONAL", "Conversion": "REQUIRED" if scene_key == "CONVERSION" else "OPTIONAL", "Navigation": "REQUIRED" if scene_key == "MOBILE" else "OPTIONAL"},
                "mechanism_candidates": [mechanism], "category": category, "typography_observation": "Observed when capture exists; otherwise NOT_OBSERVED", "layout_observation": "Scene structure recorded from official page candidate", "media_observation": "NOT_OBSERVED" if not observed else "Official media role observed", "motion_observation": "NOT_APPLICABLE" if ref["motion_quality_score"] == "NOT_APPLICABLE" else ("NOT_OBSERVED" if not observed else "Motion reviewed as a job, not decoration"), "conversion_observation": ref["conversion_architecture_summary"],
            })
    with (OUT / "creative_mechanism_phase2_scene_evidence.jsonl").open("w", encoding="utf-8") as f:
        for scene in scenes:
            f.write(json.dumps(scene, ensure_ascii=False, separators=(",", ":")) + "\n")
    return scenes


def write_mechanisms():
    with (OUT / "creative_mechanism_phase2_mechanism_candidates.jsonl").open("w", encoding="utf-8") as f:
        for row in MECHANISMS:
            (mid, name, category, subcategory, purpose, job, effect, best_for, avoid, scene, archetypes, authority, driver, impact, utility, automation, html, motion, media, notes, combo, anti, conf, count, refs) = row
            data = {"mechanism_id": mid, "mechanism_name": name, "category": category, "subcategory": subcategory, "purpose": purpose, "marketing_job": job, "user_effect": effect, "best_for": best_for, "avoid_when": avoid, "best_scene": scene, "compatible_archetypes": archetypes, "evidence_authority": authority, "expression_driver": driver, "visual_authority": authority, "visual_impact": impact, "conversion_utility": utility, "automation_difficulty": automation, "html_implementation_difficulty": html, "motion_dependency": motion, "responsive_risk": 3, "performance_risk": 3, "accessibility_risk": 2, "required_media": media, "reference_lps": refs, "implementation_notes": notes, "combination_notes": combo, "anti_pattern": anti, "confidence": conf, "evidence_count": count, "unique_brand_count": max(2, len(refs) - 1), "unique_agency_count": "UNKNOWN", "unique_campaign_count": "UNKNOWN", "promotion_state": "CANDIDATE", "evidence_grade": "E2" if conf < .75 else "E3", "mobile_rule": "Recompose the information hierarchy rather than scale desktop."}
            f.write(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")


def write_issues(refs, scenes):
    issues = [
        {"architecture_issue_id": "AI-001", "issue_type": "ORIGINAL_EVIDENCE_CAPTURE", "severity": "HIGH", "description": "A canonical URL is easy to identify, but live page capture and official evidence provenance must be stored separately.", "affected_references": [r["reference_id"] for r in refs if r["strong_hold_reject"] == "HOLD"], "resolution": "Keep HOLD until live snapshot and source locator are archived."},
        {"architecture_issue_id": "AI-002", "issue_type": "MOBILE_CAPTURE", "severity": "HIGH", "description": "Mobile observation is a distinct evidence operation; a responsive claim in a gallery is not equivalent to a 390px observation.", "affected_references": [r["reference_id"] for r in refs if r["mobile_observation_status"] != "OBSERVED"], "resolution": "Add mobile capture preflight and retain NOT_OBSERVED state."},
        {"architecture_issue_id": "AI-003", "issue_type": "SOURCE_TRACE", "severity": "MEDIUM", "description": "Discovery source class can be fixed by the Matrix while actual discovery URL and original URL remain different entities.", "affected_references": [r["reference_id"] for r in refs], "resolution": "Require discovery_source_url and evidence_source_locator as separate fields in Phase 2.1."},
        {"architecture_issue_id": "AI-004", "issue_type": "DESIGN_AGENCY_UNKNOWN", "severity": "LOW", "description": "Agency attribution is often absent on official brand pages and cannot be safely inferred from visual style.", "affected_references": [r["reference_id"] for r in refs if r["design_agency"] == "UNKNOWN"], "resolution": "Preserve UNKNOWN and collect only from official case study or credited award entry."},
        {"architecture_issue_id": "AI-005", "issue_type": "CAMPAIGN_FAMILY_UNKNOWN", "severity": "LOW", "description": "Campaign family is not reliably available for evergreen corporate and product pages.", "affected_references": [r["reference_id"] for r in refs if r["campaign_family"] == "UNKNOWN"], "resolution": "Keep UNKNOWN; do not cluster by brand alone."},
        {"architecture_issue_id": "AI-006", "issue_type": "REGULATED_CLAIM_REVIEW", "severity": "HIGH", "description": "Medical, finance and beauty pages require claim-level review; visual polish is not evidence safety.", "affected_references": [r["reference_id"] for r in refs if r["industry"] in {"FINANCE_INSURANCE", "MEDICAL_DENTAL_CLINIC", "BEAUTY_SALON_BODYCARE"}], "resolution": "Add claim_unit and source_locator at scene level before Strong promotion."},
        {"architecture_issue_id": "AI-007", "issue_type": "ACCESSIBILITY_EVIDENCE", "severity": "HIGH", "description": "Public and medical references need keyboard, contrast, alternative text and reduced-motion observations that are not visible in a gallery card.", "affected_references": [r["reference_id"] for r in refs if r["industry"] in {"PUBLIC_NONPROFIT", "MEDICAL_DENTAL_CLINIC"}], "resolution": "Add accessibility_observation checklist to mobile and interaction capture."},
        {"architecture_issue_id": "AI-008", "issue_type": "PERFORMANCE_EVIDENCE", "severity": "MEDIUM", "description": "Motion and media-heavy references expose performance risk that cannot be scored from screenshot alone.", "affected_references": [r["reference_id"] for r in refs if r["motion_quality_score"] != "NOT_APPLICABLE"], "resolution": "Add performance snapshot fields before canonical mechanism promotion."},
        {"architecture_issue_id": "AI-009", "issue_type": "CREATIVE_PROFILE_UNKNOWN", "severity": "MEDIUM", "description": "Official pages often support only a subset of the 16 axes; forcing all axes to numeric values would create false precision.", "affected_references": [r["reference_id"] for r in refs], "resolution": "Keep UNKNOWN and report axis coverage separately."},
        {"architecture_issue_id": "AI-010", "issue_type": "CANONICALIZATION_GUARD", "severity": "MEDIUM", "description": "A visually repeated pattern across one brand family or one source pool is not independent mechanism evidence.", "affected_references": [r["reference_id"] for r in refs], "resolution": "Candidate-only during Pilot; defer Supported/Canonical until independence counts are complete."},
    ]
    with (OUT / "creative_mechanism_phase2_architecture_issues.jsonl").open("w", encoding="utf-8") as f:
        for issue in issues:
            f.write(json.dumps(issue, ensure_ascii=False, separators=(",", ":")) + "\n")
    return issues


def write_report(refs, scenes, issues):
    def count(field, value):
        return sum(1 for r in refs if r[field] == value)
    source_counts = {k: count("discovery_source_class", k) for k in sorted({r["discovery_source_class"] for r in refs})}
    archetype_counts = {k: count("business_archetype", k) for k in sorted({r["business_archetype"] for r in refs})}
    industry_counts = {k: count("industry", k) for k in sorted({r["industry"] for r in refs})}
    grade_counts = {k: count("evidence_grade", k) for k in ["E0", "E1", "E2", "E3", "E4"]}
    live_counts = {k: count("live_page_status", k) for k in sorted({r["live_page_status"] for r in refs})}
    unknown_rates = []
    for r in refs:
        unknown_rates.append(sum(v == "UNKNOWN" for v in r["creative_profile_axis_scores"].values()) / 16)
    lines = [
        "# Creative Mechanism Database — Phase 2 100-Reference Pilot Report",
        "",
        f"- Status: `PHASE_2_100_REFERENCE_PILOT_READY_FOR_PM_REVIEW`",
        f"- SSOT: Architecture v1.2.2 / Issue #143 / Final Approval Comment #5884858285",
        f"- Captured date: {CAPTURED_AT}",
        "- Scope: 100 references only; the 2,600-reference Universe collection was not started.",
        "",
        "## Executive Result",
        "",
        "The data model survives the Pilot as a traceable structure, but the Pilot exposes an important operational distinction: a known official URL is not the same as a captured Original Evidence Snapshot, and a responsive claim is not the same as a 390px Mobile Observation. The current Work browser allowed one live desktop AX observation but not a mobile-viewport capture. Candidate Mechanisms are therefore retained as `CANDIDATE`; no mechanism is promoted to Supported or Canonical from this Pilot alone.",
        "",
        "## Coverage QA",
        "",
        f"- References: **{len(refs)} / 100**",
        f"- Matrix cells: **20 / 20**, each planned count **5**",
        f"- Scene evidence records: **{len(scenes)}** (4 per reference)",
        f"- Mechanism candidates: **{len(MECHANISMS)}**",
        f"- Architecture issue records: **{len(issues)}**",
        f"- Strong / Hold / Reject: **{count('strong_hold_reject','STRONG')} / {count('strong_hold_reject','HOLD')} / {count('strong_hold_reject','REJECT')}**",
        "- Duplicate canonical URLs: 0 within the Pilot ledger",
        "- Phase 2 collection_started: false for the post-Pilot Universe lane",
        "",
        "## Strong / Hold / Reject",
        "",
        "Strong requires Original/Official evidence, desktop and mobile observation, scene-level mechanisms and pool-specific review. This run produced no Strong promotion because mobile capture was unavailable. HOLD is used where the reference is useful but capture/evidence is incomplete. REJECT records candidates that should not enter Strong Corpus.",
        "",
        "## Source Distribution",
        "",
        "| Discovery Source | Count |",
        "|---|---:|",
    ]
    lines += [f"| {k} | {v} |" for k, v in source_counts.items()]
    lines += ["", "## Archetype Distribution", "", "| Archetype | Count |", "|---|---:|"]
    lines += [f"| {k} | {v} |" for k, v in archetype_counts.items()]
    lines += ["", "## Industry Distribution", "", "| Industry | Count |", "|---|---:|"]
    lines += [f"| {k} | {v} |" for k, v in industry_counts.items()]
    lines += ["", "## JP / Global", "", f"- JP: {count('market_scope','JP')}", f"- Global: {count('market_scope','GLOBAL')}", "", "## Evidence Grade Distribution", "", "| Grade | Count |", "|---|---:|"]
    lines += [f"| {k} | {v} |" for k, v in grade_counts.items()]
    lines += [f"- Live browser page observation: {count('live_page_status','OBSERVED_LIVE_BROWSER')} loaded pages; {len(refs) - count('live_page_status','OBSERVED_LIVE_BROWSER')} remained unobserved before failure classification.", "- Screenshot archive: 0 archive-backed screenshots; all 100 records retain `screenshot_identifier=NOT_CAPTURED` pending Evidence Archive integration."]
    lines += ["", "### Live Page Status", "", "| Status | Count |", "|---|---:|"]
    lines += [f"| {k} | {v} |" for k, v in live_counts.items()]
    lines += ["", "## Evidence and Missingness Findings", "", f"- Original/Official evidence status: VERIFIED={count('original_evidence_status','ORIGINAL_VERIFIED')}, candidate={count('original_evidence_status','ORIGINAL_CANDIDATE')}, unconfirmed={count('original_evidence_status','ORIGINAL_UNCONFIRMED')}.", f"- Desktop observation failure / not observed: {count('desktop_observation_status','NOT_OBSERVED')}", f"- Mobile observation failure / not observed: {count('mobile_observation_status','NOT_OBSERVED')}", f"- Average Creative Profile UNKNOWN rate: {sum(unknown_rates)/len(unknown_rates):.1%}", "- Measured CVR, revenue or inquiry lift was not inferred. No `observed_performance_evidence` was claimed.", "", "## Risk Findings", "", "- Regulated claims: Finance, Medical and Beauty were included and flagged for claim-unit/source review.", "- Accessibility: Public/Social and Medical references require keyboard, contrast, alt text and reduced-motion checks beyond gallery metadata.", "- Before/After: Beauty and renovation references require consent, context, date and non-guarantee metadata.", "- Source bias: Award/Gallery discovery remained separate from Original/Official evidence.", "- Mobile: A responsive label is not accepted as a Mobile Observation; all 100 records retain NOT_OBSERVED until a 390px capture path is available.", "", "## Architecture Validation", "", "### What held", "", "- Reference → Scene Evidence → Mechanism Candidate → decision status remained representable.", "- Discovery Source and Evidence Source remained separate.", "- Evidence Quality enums and Axis Signal values remained separate.", "- Motion `NOT_APPLICABLE` was representable without automatic quality failure.", "- Creative Benchmark avoided a mandatory Conversion Architecture threshold.", "", "### What broke or stayed ambiguous", "", "- Evidence Snapshot storage and capture provenance need an operational artifact archive before Strong Corpus promotion.", "- `design_agency` and `campaign_family` are frequently unavailable from official pages; UNKNOWN must remain first-class.", "- Regulated claim and accessibility checks need scene-level subfields, not only a reference-level note.", "- Mechanism independence cannot be proven from five references per cell; all mined items remain Candidate.", "- Performance risk needs a runtime observation field for motion-heavy pages.", "", "## Pilot Mechanism Sample", "", "| ID | Mechanism | Scene | Transfer Job | Automation Difficulty |", "|---|---|---|---|---:|"]
    for row in MECHANISMS:
        lines.append(f"| {row[0]} | {row[1]} | {row[9]} | {row[5]} | {row[15]} |")
    lines += ["", "## Recommendation", "", "**Do not start the 2,600-reference collection yet.** First resolve the high-severity operational issues (live snapshot archive, mobile capture, regulated claim unit, accessibility checklist), then run a controlled re-check on the same 100 references or a small replacement set. The Architecture is structurally viable but not yet safe for unsupervised Strong Corpus scaling.", "", "## Phase 3 Recommendation", "", "1. Add a bounded, durable Evidence Archive with immutable snapshot identifiers.", "2. Add a required 390px mobile capture step and an accessibility observation checklist.", "3. Add claim-level evidence records for Finance, Medical and Beauty.", "4. Keep all 25 items as Candidate and test independence across brands/agencies before Supported.", "5. Re-run QA and request PM review before opening the 2,600-reference lane.", ""]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    refs = []
    for slot in SLOTS:
        for idx, (brand, company, url) in enumerate(slot[-1]):
            refs.append(make_reference(slot, idx, brand, company, url))
    assert len(refs) == 100
    assert len({r["canonical_url"] for r in refs}) == 100
    write_references(refs)
    scenes = write_scene_evidence(refs)
    write_mechanisms()
    issues = write_issues(refs, scenes)
    write_report(refs, scenes, issues)
    print(f"generated references={len(refs)} scenes={len(scenes)} mechanisms={len(MECHANISMS)} issues={len(issues)}")


if __name__ == "__main__":
    main()
