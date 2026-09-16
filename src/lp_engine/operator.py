"""Private static operator interface."""
from html import escape
def render(summary):
    cards=[("Candidates",summary.get("candidates",0)),("Projects",summary.get("projects",0)),("Queue",summary.get("queue_size",0)),("Errors",summary.get("errors",0))]
    body="".join(f"<div class='card'><small>{escape(str(k))}</small><strong>{escape(str(v))}</strong></div>" for k,v in cards)
    return "<!doctype html><meta charset='utf-8'><title>LP Production Operations</title><style>body{font:16px system-ui;margin:32px;background:#f7f7f2}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.card{background:white;border:1px solid #ddd;padding:18px;border-radius:10px}.card strong{display:block;font-size:32px}</style><h1>LP Production Operations</h1><p>Private operator view. External sales and public publish are disabled.</p><div class='grid'>"+body+"</div><h2>Safety boundary</h2><p>External sales: 0 / Public publish: 0 / Manual LP edit: 0</p>"
