"""Issue #74 renderer-level visual composition profiles.

Profiles are reusable form grammars selected from frozen customer decision jobs.
They alter rendered composition (not labels, colors, or metadata) and preserve
mobile fallback geometry.
"""
from __future__ import annotations
from html import escape
from pathlib import Path

RENDERER_PROFILES = {
    "diagnostic-route": {
        "hero": "split-diagnostic",
        "core": "evidence-rail",
        "closing": "route-cta",
        "media_cadence": "hero-large-core-offset-close-small",
    },
    "self-check-field": {
        "hero": "media-first-field",
        "core": "stacked-condition",
        "closing": "centered-next-step",
        "media_cadence": "hero-wide-core-wide-close-quiet",
    },
    "relationship-continuity": {
        "hero": "people-rail",
        "core": "continuity-timeline",
        "closing": "returning-visit",
        "media_cadence": "alternating-human-place",
    },
    "community-appointment": {
        "hero": "place-ledger",
        "core": "community-sequence",
        "closing": "appointment-rail",
        "media_cadence": "place-small-people-large",
    },
    "ritual-material-proof": {
        "hero": "ritual-split",
        "core": "material-spread",
        "closing": "ritual-quiet-close",
        "media_cadence": "material-large-proof-small",
    },
    "environment-lifestyle-fit": {
        "hero": "environment-wide",
        "core": "lifestyle-offset",
        "closing": "space-invitation",
        "media_cadence": "wide-space-object-detail",
    },
    "authorship-portfolio-investment": {
        "hero": "authorship-editorial",
        "core": "portfolio-index",
        "closing": "consultation-commit",
        "media_cadence": "craft-detail-portfolio-investment",
    },
    "program-fit-commitment": {
        "hero": "program-method",
        "core": "schedule-sequence",
        "closing": "trial-program",
        "media_cadence": "method-wide-schedule-detail",
    },
}

PROFILE_CSS = {
"diagnostic-route": """
body[data-issue74-profile="diagnostic-route"] main > .premium-scene:nth-child(1) .scene-full{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(240px,.85fr);align-items:end;gap:clamp(2rem,7vw,8rem)}
body[data-issue74-profile="diagnostic-route"] main > .premium-scene:nth-child(1) .scene-media{grid-column:2;grid-row:1;min-height:clamp(360px,45vw,620px)}
body[data-issue74-profile="diagnostic-route"] main > .premium-scene:nth-child(2) .scene-inset{grid-template-columns:minmax(0,.58fr) minmax(0,.42fr);border-left:8px solid var(--accent);padding-left:clamp(1rem,4vw,4rem)}
body[data-issue74-profile="diagnostic-route"] main > .premium-scene:nth-child(4){padding-top:clamp(6rem,12vw,12rem);border-top:0}
body[data-issue74-profile="diagnostic-route"] main > .premium-scene:nth-child(4) .scene-full{grid-template-columns:1fr auto;align-items:end;border-bottom:2px solid var(--ink);padding-bottom:2rem}
""",
"self-check-field": """
body[data-issue74-profile="self-check-field"] main > .premium-scene:nth-child(1) .scene-full{display:grid;grid-template-columns:1fr;gap:clamp(1.5rem,3vw,3rem)}
body[data-issue74-profile="self-check-field"] main > .premium-scene:nth-child(1) .scene-media{order:-1;min-height:clamp(300px,34vw,470px);border-radius:0 0 48% 0}
body[data-issue74-profile="self-check-field"] main > .premium-scene:nth-child(2) .scene-inset{grid-template-columns:1fr;max-width:48rem;margin:0 auto}
body[data-issue74-profile="self-check-field"] main > .premium-scene:nth-child(2) .scene-media{min-height:clamp(300px,38vw,520px);width:72%;justify-self:end}
body[data-issue74-profile="self-check-field"] main > .premium-scene .scene-layered{display:grid;grid-template-columns:minmax(0,.64fr) minmax(0,.36fr);align-items:stretch;min-height:420px}
body[data-issue74-profile="self-check-field"] main > .premium-scene .scene-layered-copy{position:static;grid-column:1;grid-row:1;align-self:center}
body[data-issue74-profile="self-check-field"] main > .premium-scene .scene-media{grid-column:2;grid-row:1;min-height:100%;border-radius:50% 0 0 50%}
body[data-issue74-profile="self-check-field"] main > .premium-scene:nth-child(4){text-align:center}
""",
"relationship-continuity": """
body[data-issue74-profile="relationship-continuity"] main > .premium-scene:nth-child(1) .scene-split{grid-template-columns:minmax(0,.44fr) minmax(0,.56fr);align-items:stretch}
body[data-issue74-profile="relationship-continuity"] main > .premium-scene:nth-child(1) .scene-media{min-height:clamp(380px,48vw,650px);border-radius:50% 0 50% 0}
body[data-issue74-profile="relationship-continuity"] main > .premium-scene:nth-child(2) .scene-layered{min-height:520px}
body[data-issue74-profile="relationship-continuity"] main > .premium-scene:nth-child(2) .scene-layered-copy{left:0;bottom:12%;max-width:48%;border-left:8px solid var(--accent)}
body[data-issue74-profile="relationship-continuity"] main > .premium-scene:nth-child(3) .scene-full{display:grid;grid-template-columns:.28fr 1fr;align-items:start}
body[data-issue74-profile="relationship-continuity"] main > .premium-scene:nth-child(4){max-width:60rem}
""",
"community-appointment": """
body[data-issue74-profile="community-appointment"] main > .premium-scene:nth-child(1) .scene-full{position:relative;min-height:clamp(480px,58vw,760px);display:block}
body[data-issue74-profile="community-appointment"] main > .premium-scene:nth-child(1) .scene-media{height:100%;min-height:480px}
body[data-issue74-profile="community-appointment"] main > .premium-scene:nth-child(1) h1,body[data-issue74-profile="community-appointment"] main > .premium-scene:nth-child(1) p{position:relative;z-index:2;background:var(--copy-surface);padding:.5rem 1rem;max-width:28rem;margin-top:-10rem}
body[data-issue74-profile="community-appointment"] main > .premium-scene:nth-child(2) .scene-sequence{border-left:0;border-top:10px solid var(--accent);padding:clamp(2rem,5vw,5rem) 0}
body[data-issue74-profile="community-appointment"] main > .premium-scene:nth-child(2) .scene-media{min-height:260px;width:60%;margin-left:auto}
body[data-issue74-profile="community-appointment"] main > .premium-scene:nth-child(3) .scene-split{grid-template-columns:1fr .55fr;align-items:end}
body[data-issue74-profile="community-appointment"] main > .premium-scene:nth-child(4) .scene-full{display:flex;justify-content:space-between;align-items:center;border-top:8px solid var(--ink);padding-top:2rem}
""",
"ritual-material-proof": """
body[data-issue74-profile="ritual-material-proof"] main > .premium-scene:nth-child(1) .scene-split{grid-template-columns:minmax(0,.62fr) minmax(0,.38fr);align-items:end}
body[data-issue74-profile="ritual-material-proof"] main > .premium-scene:nth-child(1) .scene-media{min-height:clamp(420px,54vw,700px);border-radius:0}
body[data-issue74-profile="ritual-material-proof"] main > .premium-scene:nth-child(2) .scene-inset{grid-template-columns:1fr;max-width:56rem}
body[data-issue74-profile="ritual-material-proof"] main > .premium-scene:nth-child(2) .scene-media{width:82%;min-height:300px}
body[data-issue74-profile="ritual-material-proof"] main > .premium-scene .scene-layered{min-height:360px}
body[data-issue74-profile="ritual-material-proof"] main > .premium-scene:nth-child(4){width:calc(100% - 12%);max-width:52rem;box-sizing:border-box;margin-left:12%;border-top:0;border-bottom:1px solid var(--line)}
body[data-issue74-profile="ritual-material-proof"] main > .premium-scene .scene-full,body[data-issue74-profile="ritual-material-proof"] main > .premium-scene .scene-split,body[data-issue74-profile="ritual-material-proof"] main > .premium-scene .scene-inset,body[data-issue74-profile="ritual-material-proof"] main > .premium-scene .scene-layered{min-width:0;max-width:100%;box-sizing:border-box}
""",
"environment-lifestyle-fit": """
body[data-issue74-profile="environment-lifestyle-fit"] main > .premium-scene:nth-child(1) .scene-full{display:grid;grid-template-columns:1fr;gap:1rem}
body[data-issue74-profile="environment-lifestyle-fit"] main > .premium-scene:nth-child(1) .scene-media{order:-1;min-height:clamp(300px,38vw,520px);border-radius:0}
body[data-issue74-profile="environment-lifestyle-fit"] main > .premium-scene:nth-child(2) .scene-split{grid-template-columns:.35fr .65fr;align-items:start}
body[data-issue74-profile="environment-lifestyle-fit"] main > .premium-scene:nth-child(2) .scene-media{min-height:480px}
body[data-issue74-profile="environment-lifestyle-fit"] main > .premium-scene:nth-child(3) .scene-inset{grid-template-columns:.7fr .3fr;border-top:2px solid var(--ink);padding-top:2rem}
body[data-issue74-profile="environment-lifestyle-fit"] main > .premium-scene:nth-child(4){padding-bottom:clamp(8rem,15vw,16rem);text-align:right}
""",
"authorship-portfolio-investment": """
body[data-issue74-profile="authorship-portfolio-investment"] main > .premium-scene:nth-child(1) .scene-layered{min-height:clamp(480px,58vw,760px)}
body[data-issue74-profile="authorship-portfolio-investment"] main > .premium-scene:nth-child(1) .scene-layered-copy{left:0;bottom:0;max-width:58%;border-top:8px solid var(--accent);border-radius:0}
body[data-issue74-profile="authorship-portfolio-investment"] main > .premium-scene:nth-child(2) .scene-full{display:grid;grid-template-columns:.2fr .8fr;align-items:start}
body[data-issue74-profile="authorship-portfolio-investment"] main > .premium-scene:nth-child(2) .scene-media{min-height:clamp(360px,44vw,600px)}
body[data-issue74-profile="authorship-portfolio-investment"] main > .premium-scene:nth-child(3) .scene-split{grid-template-columns:.75fr .25fr}
body[data-issue74-profile="authorship-portfolio-investment"] main > .premium-scene:nth-child(4) .scene-full{display:grid;grid-template-columns:1fr auto;align-items:end;border-left:10px solid var(--accent);padding-left:2rem}
""",
"program-fit-commitment": """
body[data-issue74-profile="program-fit-commitment"] main > .premium-scene:nth-child(1) .scene-full{display:grid;grid-template-columns:1fr;gap:0}
body[data-issue74-profile="program-fit-commitment"] main > .premium-scene:nth-child(1) .scene-media{min-height:clamp(360px,42vw,560px);order:-1;border-radius:50%}
body[data-issue74-profile="program-fit-commitment"] main > .premium-scene:nth-child(2) .scene-sequence{display:grid;grid-template-columns:.35fr .65fr;gap:2rem;border-left:0;border-top:2px solid var(--ink);padding:2rem 0}
body[data-issue74-profile="program-fit-commitment"] main > .premium-scene:nth-child(2) .scene-media{min-height:260px}
body[data-issue74-profile="program-fit-commitment"] main > .premium-scene:nth-child(3) .scene-inset{grid-template-columns:.44fr .56fr}
body[data-issue74-profile="program-fit-commitment"] main > .premium-scene:nth-child(4){max-width:44rem;margin-right:10%;border-top:0}
""",
}

def apply_visual_composition(html_path: str | Path, profile: str) -> dict[str, str]:
    if profile not in PROFILE_CSS:
        raise ValueError(f"unknown Issue 74 renderer profile: {profile}")
    path = Path(html_path)
    html = path.read_text(encoding="utf-8")
    marker = "data-issue74-profile"
    if marker in html:
        return {"profile": profile, "status": "already_applied"}
    css = PROFILE_CSS[profile]
    tag = f'<style data-issue74-profile="{escape(profile)}">{css}</style>'
    html = html.replace("<head>", f"<head>{tag}", 1)
    html = html.replace("<body ", f'<body data-issue74-profile="{escape(profile)}" ', 1)
    path.write_text(html, encoding="utf-8")
    return {"profile": profile, "status": "applied"}


F01_COMPOSITION_CSS = {
    "three": """
body[data-issue77-f01="three"] main > .premium-scene:nth-child(1) .scene-split{display:grid;grid-template-columns:minmax(0,.72fr) minmax(0,.28fr);align-items:stretch}
body[data-issue77-f01="three"] main > .premium-scene:nth-child(1) .scene-media{grid-column:1;grid-row:1;min-height:clamp(440px,60vw,820px)}
body[data-issue77-f01="three"] main > .premium-scene:nth-child(1) .scene-copy{grid-column:2;grid-row:1;align-self:end}
body[data-issue77-f01="three"] main > .premium-scene:nth-child(2){padding-top:clamp(3rem,8vw,8rem)}
body[data-issue77-f01="three"] main > .premium-scene:nth-child(2) .scene-inset{display:grid;grid-template-columns:minmax(0,.3fr) minmax(0,.7fr);gap:clamp(1rem,5vw,5rem);align-items:start}
body[data-issue77-f01="three"] main > .premium-scene:nth-child(3) .scene-layered{display:grid;grid-template-columns:minmax(0,.68fr) minmax(0,.32fr);min-height:clamp(360px,44vw,620px)}
body[data-issue77-f01="three"] main > .premium-scene:nth-child(3) .scene-layered-copy{position:static;grid-column:1;grid-row:1;align-self:center}
body[data-issue77-f01="three"] main > .premium-scene:nth-child(3) .scene-media{grid-column:2;grid-row:1;min-height:100%}
body[data-issue77-f01="three"] main > .premium-scene:nth-child(4){width:100%;max-width:none;margin:0;padding-top:clamp(4rem,10vw,10rem);border-top:0}
body[data-issue77-f01="three"] main > .premium-scene:nth-child(4) .scene-full{display:grid;grid-template-columns:minmax(0,.7fr) minmax(0,.3fr);align-items:end;border-top:2px solid var(--ink);padding-top:2rem}
body[data-issue77-f01="three"] main > .premium-scene .scene-full,body[data-issue77-f01="three"] main > .premium-scene .scene-split,body[data-issue77-f01="three"] main > .premium-scene .scene-inset,body[data-issue77-f01="three"] main > .premium-scene .scene-layered{min-width:0;max-width:100%;box-sizing:border-box}
@media (max-width:767px){body[data-issue77-f01="three"]{overflow-x:clip}body[data-issue77-f01="three"] main{max-width:100vw;overflow-x:clip}body[data-issue77-f01="three"] main > .premium-scene .scene-media{grid-column:auto!important;grid-row:auto!important}body[data-issue77-f01="three"] main > .premium-scene.scene-state-fit .scene-inset,body[data-issue77-f01="three"] main > .premium-scene.scene-state-fit .scene-split{display:block;min-height:0}body[data-issue77-f01="three"] main > .premium-scene.scene-state-fit .scene-inset>div,body[data-issue77-f01="three"] main > .premium-scene.scene-state-fit .scene-split>div,body[data-issue77-f01="three"] main > .premium-scene.scene-state-fit .scene-full{width:100%;max-width:none;min-width:0}body[data-issue77-f01="three"] main > .premium-scene.scene-state-fit h1,body[data-issue77-f01="three"] main > .premium-scene.scene-state-fit h2,body[data-issue77-f01="three"] main > .premium-scene.scene-state-fit p{width:100%;max-width:100%;word-break:keep-all;overflow-wrap:normal;white-space:normal}body[data-issue77-f01="three"] main > .premium-scene.scene-state-fit .scene-media{grid-column:auto;grid-row:auto;min-height:280px;width:100%;margin-top:2rem}}
""",
    "baum": """
body[data-issue77-f01="baum"] main > .premium-scene:nth-child(1) .scene-full{display:block;position:relative;min-height:clamp(500px,62vw,860px)}
body[data-issue77-f01="baum"] main > .premium-scene:nth-child(1) .scene-media{height:100%;min-height:500px;width:100%}
body[data-issue77-f01="baum"] main > .premium-scene:nth-child(1) .scene-copy{position:absolute;left:8%;bottom:8%;max-width:28rem;padding:1.25rem;background:var(--copy-surface)}
body[data-issue77-f01="baum"] main > .premium-scene:nth-child(2) .scene-split{display:grid;grid-template-columns:minmax(0,.65fr) minmax(0,.35fr);align-items:start}
body[data-issue77-f01="baum"] main > .premium-scene:nth-child(2) .scene-media{grid-column:1;min-height:clamp(300px,38vw,520px)}
body[data-issue77-f01="baum"] main > .premium-scene:nth-child(3) .scene-inset{display:grid;grid-template-columns:minmax(0,.42fr) minmax(0,.58fr);gap:clamp(1rem,4vw,4rem);align-items:center}
body[data-issue77-f01="baum"] main > .premium-scene .scene-media{min-height:clamp(320px,34vw,500px)}
body[data-issue77-f01="baum"] main > .premium-scene:nth-child(4){max-width:48rem;margin-left:auto;padding-bottom:clamp(6rem,12vw,12rem);border-top:0}
body[data-issue77-f01="baum"] main > .premium-scene:nth-child(4) .scene-full{display:block;border-left:10px solid var(--accent);padding-left:2rem}
body[data-issue77-f01="baum"] main > .premium-scene .scene-full,body[data-issue77-f01="baum"] main > .premium-scene .scene-split,body[data-issue77-f01="baum"] main > .premium-scene .scene-inset,body[data-issue77-f01="baum"] main > .premium-scene .scene-layered{min-width:0;max-width:100%;box-sizing:border-box}
""",
}

def apply_f01_composition(html_path: str | Path, company_id: str) -> dict[str, str]:
    if company_id not in F01_COMPOSITION_CSS:
        return {"company_id": company_id, "status": "not_required"}
    path = Path(html_path)
    html = path.read_text(encoding="utf-8")
    marker = "data-issue77-f01"
    if marker in html:
        return {"company_id": company_id, "status": "already_applied"}
    css = F01_COMPOSITION_CSS[company_id]
    tag = f'<style data-issue77-f01="{escape(company_id)}">{css}</style>'
    html = html.replace("</head>", f"{tag}</head>", 1)
    html = html.replace("<body ", f'<body data-issue77-f01="{escape(company_id)}" ', 1)
    path.write_text(html, encoding="utf-8")
    return {"company_id": company_id, "status": "applied"}
