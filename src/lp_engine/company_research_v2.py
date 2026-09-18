"""Round 2C company research IR.

The snapshot is intentionally source-locked: public facts are preserved as
individual nodes, while conflicting address strings remain conflicted instead
of being silently normalised into a false single address.
"""
from __future__ import annotations

from datetime import date
from typing import Any


CHECKED_AT = "2026-09-18"


def _fact(
    fact_id: str,
    category: str,
    value: str,
    source: str,
    source_type: str,
    confidence: str,
    decision_relevance: list[str],
    *,
    freshness: str = "PUBLIC_SNAPSHOT",
    public_private: str = "PUBLIC",
    claim_safety: str = "VERIFIED_PUBLIC",
    visualizable: bool = False,
    rights_status: str = "NOT_APPLICABLE",
    conflict_group: str = "",
    allowed_usage: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "fact_id": fact_id,
        "category": category,
        "value": value,
        "source": source,
        "source_type": source_type,
        "checked_at": CHECKED_AT,
        "confidence": confidence,
        "freshness": freshness,
        "public_private": public_private,
        "claim_safety": claim_safety,
        "visualizable": visualizable,
        "decision_relevance": decision_relevance,
        "rights_status": rights_status,
        "conflict_group": conflict_group,
        "allowed_usage": allowed_usage or ["RESEARCH", "PROTOTYPE_COPY"],
    }


def build_maylynn_research_snapshot() -> dict[str, Any]:
    sources = [
        {"source_id": "official_hands_home", "tier": "A", "source_type": "OFFICIAL_SITE", "url": "https://maylynnhands.com/", "checked_at": CHECKED_AT},
        {"source_id": "official_hands_about", "tier": "A", "source_type": "OFFICIAL_SITE", "url": "https://maylynnhands.com/about/", "checked_at": CHECKED_AT},
        {"source_id": "official_paint_home", "tier": "A", "source_type": "OFFICIAL_SITE", "url": "https://maylynnpaint.com/", "checked_at": CHECKED_AT},
        {"source_id": "zehitomo_profile", "tier": "B", "source_type": "BUSINESS_MANAGED_PROFILE", "url": "https://www.zehitomo.com/profile/%E3%83%A1%E3%82%A4%E3%83%AA%E3%83%B3%E3%83%8F%E3%83%B3%E3%82%BA%E6%A0%AA%E5%BC%8F%E4%BC%9A%E7%A4%BE-Fl1fVSUE3/pro", "checked_at": CHECKED_AT},
        {"source_id": "rehome_review", "tier": "C", "source_type": "INDEPENDENT_REVIEW_PLATFORM", "url": "https://rehome-navi.com/shops/5865", "checked_at": CHECKED_AT},
    ]
    facts = [
        _fact("identity.brand", "Identity", "メイリン塗装工務店", "official_hands_home", "OFFICIAL_SITE", "A", ["D01", "D02"], allowed_usage=["HERO", "FOOTER", "IDENTITY"]),
        _fact("identity.company", "Identity", "メイリンハンズ株式会社", "rehome_review", "INDEPENDENT_REVIEW_PLATFORM", "B", ["D06"], allowed_usage=["ABOUT", "PROOF_CARD"]),
        _fact("identity.representative", "People", "廣瀬 佑輔", "official_hands_about", "OFFICIAL_SITE", "A", ["D06"], allowed_usage=["ABOUT", "PROOF_CARD"]),
        _fact("place.primary_area", "Place", "栃木県小山市を中心に周辺エリア", "official_hands_home", "OFFICIAL_SITE", "A", ["D01", "D08"], visualizable=True, allowed_usage=["HERO", "ACTION", "FACT_RAIL"]),
        _fact("offer.exterior_roof", "Offer", "外壁・屋根の塗装、修繕、改装", "official_paint_home", "OFFICIAL_SITE", "A", ["D01", "D02", "D03"], visualizable=True, allowed_usage=["HERO", "SCOPE", "ACTION"]),
        _fact("problem.signs", "Problem", "外壁のひび割れ・剥がれ・汚れ・色あせ、屋根の破損・経年劣化", "official_paint_home", "OFFICIAL_SITE", "A", ["D01", "D03"], visualizable=True, allowed_usage=["SIGNS", "HERO_LEAD"]),
        _fact("process.drone", "Process", "屋根・高所はドローンを用いた現地調査に対応", "official_paint_home", "OFFICIAL_SITE", "A", ["D04", "D06"], visualizable=True, allowed_usage=["PROOF", "PROCESS"]),
        _fact("process.flow", "Process", "現地調査・診断・見積・施工・品質チェックを自社社員で行う", "zehitomo_profile", "BUSINESS_MANAGED_PROFILE", "B", ["D04", "D05", "D06"], visualizable=True, allowed_usage=["PROCESS", "PROOF_CARD"]),
        _fact("trust.warranty", "Proof", "最長15年の保証", "official_paint_home", "OFFICIAL_SITE", "A", ["D06", "D07"], visualizable=True, allowed_usage=["PROOF", "FAQ", "ACTION_SUPPORT"]),
        _fact("trust.duration", "Time", "一軒家は7〜9日が目安", "official_paint_home", "OFFICIAL_SITE", "A", ["D05", "D07"], visualizable=True, allowed_usage=["PROOF", "FAQ"]),
        _fact("trust.colors", "Offer", "日塗工色見本帳654色から選択可能", "official_paint_home", "OFFICIAL_SITE", "A", ["D02", "D07"], visualizable=True, allowed_usage=["MATERIAL", "FAQ"]),
        _fact("people.experience", "People", "20年以上の経験を持つ職人", "official_hands_about", "OFFICIAL_SITE", "A", ["D06"], visualizable=False, allowed_usage=["PROCESS", "PROOF_CARD"]),
        _fact("action.phone", "Action", "0800-8080-886", "official_hands_home", "OFFICIAL_SITE", "A", ["D10"], allowed_usage=["ACTION"]),
        _fact("action.hours", "Availability", "受付10:00〜19:00", "official_hands_home", "OFFICIAL_SITE", "A", ["D07", "D10"], allowed_usage=["FAQ", "ACTION"]),
        _fact("action.form", "Action", "公式問い合わせフォーム", "official_hands_home", "OFFICIAL_SITE", "A", ["D10"], allowed_usage=["ACTION"]),
        _fact("proof.case", "Proof", "築40年住宅の塗装工事／料金5万円〜程度／工期1〜2日程度", "official_hands_home", "OFFICIAL_SITE", "A", ["D06", "D07"], allowed_usage=["EVIDENCE_CARD"]),
        _fact("proof.review", "Proof", "公開レビュー1件：2025年施工完了、築45年戸建、外壁塗装、68万円、15日", "rehome_review", "INDEPENDENT_REVIEW_PLATFORM", "C", ["D06", "D07"], allowed_usage=["EVIDENCE_CARD"]),
        _fact("address.official_old", "Place", "栃木県小山市ひととのや1871-358", "official_paint_home", "OFFICIAL_SITE", "A", ["D08"], conflict_group="current_office_address", allowed_usage=["INTERNAL_CONFLICT_ONLY"]),
        _fact("address.official_new", "Place", "栃木県小山市駅南町2-8-6", "official_hands_home", "OFFICIAL_SITE", "A", ["D08"], conflict_group="current_office_address", allowed_usage=["INTERNAL_CONFLICT_ONLY"]),
    ]
    conflicts = [{"conflict_group": "current_office_address", "status": "CONFLICTED", "fact_ids": ["address.official_old", "address.official_new"], "resolution": "Prototypeは市区町村までに限定し、正確な住所はHearingへ送る。"}]
    return {
        "schema_version": "company_research_v2",
        "research_snapshot_date": CHECKED_AT,
        "company_id": "maylynn_paint",
        "company_name": "メイリン塗装工務店",
        "legal_entity": "メイリンハンズ株式会社",
        "research_scope": "small_local_trade_premium_prototype",
        "sources": sources,
        "facts": facts,
        "conflicts": conflicts,
        "unknowns": [
            "最新総施工件数", "最新staff人数", "全資格", "保険", "正確な保証適用条件",
            "標準料金表", "現在の納期", "payment condition", "actual staff photo rights",
            "actual case photo reuse rights", "before / after rights", "exact current office address",
        ],
        "hearing_gaps": [
            "最新施工実績", "before / after", "worker photos", "customer reviews利用許諾",
            "exact warranty", "current address", "service area", "pricing examples", "insurance / licenses", "payment", "available dates",
        ],
        "primary_display_policy": "小山市を中心に周辺エリア。競合する正確な住所は表示しない。",
    }


def validate_research_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    required = {"fact_id", "category", "value", "source", "source_type", "checked_at", "confidence", "freshness", "public_private", "claim_safety", "visualizable", "decision_relevance", "rights_status", "conflict_group", "allowed_usage"}
    missing = [fact.get("fact_id") for fact in snapshot.get("facts", []) if required - set(fact)]
    return {"status": "PASS" if not missing and snapshot.get("conflicts") else "FAIL", "fact_count": len(snapshot.get("facts", [])), "missing_fields": missing, "conflict_count": len(snapshot.get("conflicts", [])), "checked_at": snapshot.get("research_snapshot_date")}
