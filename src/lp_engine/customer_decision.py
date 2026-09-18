"""Customer Decision Model for the Maylynn prototype."""
from __future__ import annotations

from typing import Any


def build_customer_decision_model(snapshot: dict[str, Any], graph: dict[str, Any]) -> dict[str, Any]:
    answers = {
        "D01": ("これは自分が相談してよい内容か。", "外壁・屋根の塗装、修繕、改装を小山市中心に相談できる。", ["identity.brand", "place.primary_area", "offer.exterior_roof"]),
        "D02": ("何をしてくれるか。", "外壁・屋根を状態と希望に合わせて調査・修繕・塗装する。", ["offer.exterior_roof", "process.drone"]),
        "D03": ("どんな状態が相談対象か。", "ひび割れ、剥がれ、汚れ、色あせ、屋根の破損など。", ["problem.signs"]),
        "D04": ("どう調べるか。", "屋根・高所はドローンを用いた現地調査に対応する。", ["process.drone", "process.flow"]),
        "D05": ("どう進むか。", "現地調査、診断・見積、施工、品質チェックの順で進む。", ["process.flow"]),
        "D06": ("なぜ信じられるか。", "20年以上の経験、公開されている施工・レビュー・調査情報を確認できる。", ["people.experience", "proof.case", "proof.review", "process.drone"]),
        "D07": ("期間や保証は。", "一軒家は7〜9日が目安、保証は最長15年。", ["trust.duration", "trust.warranty"]),
        "D08": ("どの地域か。", "小山市を中心に周辺エリア。正確な住所は公開情報に競合があるため要確認。", ["place.primary_area", "address.official_old", "address.official_new"]),
        "D09": ("費用は。", "案件ごとに異なる。公開ケースとレビューは参考情報として提示し、標準料金は断定しない。", ["proof.case", "proof.review"]),
        "D10": ("次に何をするか。", "電話または公式問い合わせフォームで、見えている状態を伝える。", ["action.phone", "action.hours", "action.form"]),
    }
    rows = []
    conflicted = {fact_id for group in snapshot.get("conflicts", []) for fact_id in group.get("fact_ids", [])}
    for decision_id, (question, answer, evidence_ids) in answers.items():
        conflict = any(item in conflicted for item in evidence_ids)
        rows.append({"decision_id": decision_id, "question": question, "importance": "HIGH" if decision_id in {"D01", "D03", "D06", "D10"} else "MEDIUM", "answer": answer, "evidence_ids": evidence_ids, "confidence": "CONFLICTED" if conflict else ("MEDIUM" if decision_id in {"D06", "D09"} else "HIGH"), "required_before_action": decision_id in {"D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D10"}, "unknown": decision_id in {"D08", "D09"}, "hearing_needed": decision_id in {"D08", "D09"}, "hero_eligible": decision_id in {"D01", "D02", "D03"} and not conflict})
    return {"schema_version": "customer_decision_model_v1", "company_id": snapshot.get("company_id"), "decision_count": len(rows), "decisions": rows, "action_rule": "Only verified phone and official form create native actions; unknown price/address stays informational or hearing-needed."}
