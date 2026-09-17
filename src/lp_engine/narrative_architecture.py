"""Narrative Architecture derived from a Creative Genome and approved truth."""
from __future__ import annotations
from typing import Any, Mapping, Sequence


def _text(value: Any) -> str:
    return str(value or "").strip()


def derive_narrative_architecture(genome: Mapping[str, Any], understanding: Mapping[str, Any], evidence: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    family = _text(genome.get("dominant_narrative")) or "discovery"
    tempo = _text(genome.get("emotional_tempo")) or "grounded"
    authority = list(genome.get("visual_authority_priority") or ["TYPOGRAPHY"])
    forms = list(genome.get("composition_logic") or ["editorial_split", "progressive_story", "human_dialogue", "asymmetric_editorial"])
    plans = {
        "craft": [("observe", "この場所や状態をどう見つめればよいか", "curious", "ESTABLISH_CONTEXT", "immersive_image"), ("read_material", "素材の違いはどこに表れるか", "attentive", "SHOW_DETAIL", "material_detail"), ("watch_hands", "どんな手順で整えていくか", "assured", "SHOW_CRAFT", "process_sequence"), ("imagine_change", "整ったあとの景色を想像できるか", "hopeful", "SHOW_TRANSFORMATION", "asymmetric_editorial"), ("consult", "自分の状態をどう伝えるか", "ready", "ENABLE_ACTION", "human_dialogue")],
        "sensory_experience": [("arrive", "どんな空気の中で過ごすのか", "open", "CREATE_DESIRE", "immersive_image"), ("settle", "静けさはどう深まるか", "calm", "CREATE_PAUSE", "sensory_pause"), ("feel_care", "どんな時間を受け取るのか", "trusting", "SHOW_EXPERIENCE", "human_dialogue"), ("choose_time", "自分の過ごし方を選べるか", "certain", "REDUCE_UNCERTAINTY", "progressive_story"), ("reserve", "いつ、その時間をつくるか", "ready", "ENABLE_ACTION", "asymmetric_editorial")],
        "participation": [("encounter", "何から始めると楽しそうか", "curious", "CREATE_DESIRE", "table_scene"), ("touch", "自分の手で試せるか", "engaged", "SHOW_PARTICIPATION", "human_dialogue"), ("make", "できていく過程を想像できるか", "energized", "SHOW_PROCESS", "process_sequence"), ("share", "できたものを誰と囲むか", "warm", "SHOW_TRANSFORMATION", "table_scene"), ("join", "次の回にどう参加するか", "ready", "ENABLE_ACTION", "asymmetric_editorial")],
        "mastery": [("notice", "選ぶ基準は何か", "curious", "ESTABLISH_CONTEXT", "editorial_split"), ("compare", "違いを見分けられるか", "focused", "SHOW_DETAIL", "material_detail"), ("specify", "条件をどう整理するか", "assured", "REDUCE_UNCERTAINTY", "process_sequence"), ("select", "自分に合うものを選べるか", "certain", "BUILD_TRUST", "asymmetric_editorial"), ("act", "どこから相談するか", "ready", "ENABLE_ACTION", "human_dialogue")],
    }
    template = plans.get(family, [("notice", "いま知りたいことは何か", "curious", "ESTABLISH_CONTEXT", forms[0]), ("understand", "何を知れば判断できるか", "attentive", "REDUCE_UNCERTAINTY", forms[1]), ("trust", "なぜここに相談するのか", "assured", "BUILD_TRUST", forms[2]), ("choose", "自分の次をどう選ぶか", "certain", "SHOW_PROCESS", forms[3]), ("act", "どこから始めるか", "ready", "ENABLE_ACTION", forms[0])])
    arc = []
    for index, (state, question, emotion, purpose, grammar) in enumerate(template):
        arc.append({"narrative_state": state, "user_question": question, "user_emotion": emotion, "section_purpose": purpose, "evidence_required": [item.get("evidence_id") for item in evidence[: max(1, min(2, index + 1))]] if purpose not in {"CREATE_DESIRE", "CREATE_PAUSE"} else [], "preferred_visual_authority": authority[index % len(authority)], "preferred_composition_grammar": grammar if grammar else forms[index % len(forms)], "copy_density": "low" if tempo in {"quiet", "gentle", "intimate"} else "medium", "cta_eligibility": "primary" if purpose == "ENABLE_ACTION" else "secondary" if index in {1, 2, 3} else "none"})
    return {"schema_version": "narrative_architecture_v1", "narrative_family": family, "narrative_arc": arc, "narrative_states": [item["narrative_state"] for item in arc], "section_purposes": [item["section_purpose"] for item in arc], "transition_logic": [f"{arc[i]['narrative_state']}→{arc[i+1]['narrative_state']}" for i in range(len(arc) - 1)], "emotional_progression": [item["user_emotion"] for item in arc], "visual_progression": [item["preferred_composition_grammar"] for item in arc], "evidence_progression": [item["evidence_required"] for item in arc], "cta_progression_mapping": list(genome.get("cta_progression") or []), "section_naming": _section_names(family, understanding, arc), "mobile_redirection": dict(genome.get("mobile_redirection") or {}), "derived_from": "Creative Genome + Company Truth + approved Evidence"}


def _section_names(family: str, understanding: Mapping[str, Any], arc: Sequence[Mapping[str, Any]]) -> list[str]:
    category = _text(understanding.get("service_category"))
    names = {
        "craft": ["家の輪郭を見つめる", "素材に触れて考える", "手仕事の順番を見る", "仕上がりを思い描く", "状態から相談する"],
        "sensory_experience": ["空間に入る", "静けさを感じる", "触れられる時間", "過ごし方を選ぶ", "その時間を予約する"],
        "participation": ["食材に出会う", "手を動かしてみる", "料理ができていく", "食卓を囲む", "参加を考える"],
        "mastery": ["選ぶ基準を知る", "違いを見分ける", "条件を整理する", "自分の一台を選ぶ", "相談を始める"],
    }
    chosen = names.get(family, [item["narrative_state"] for item in arc])
    return [f"{name}｜{category}" if index == 0 and category and family not in {"craft", "sensory_experience", "participation"} else name for index, name in enumerate(chosen)]


def narrative_gates(architecture: Mapping[str, Any], genome: Mapping[str, Any]) -> dict[str, Any]:
    arc = list(architecture.get("narrative_arc") or [])
    purposes = [item.get("section_purpose") for item in arc]
    grammars = [item.get("preferred_composition_grammar") for item in arc]
    ctas = list(architecture.get("cta_progression_mapping") or [])
    headings = list(architecture.get("section_naming") or [])
    generic = ("入口", "次の一手", "確認の順番", "サービスについて", "特徴", "メリット", "お問い合わせはこちら", "詳しく見る")
    violations = [heading for heading in headings if any(token in heading for token in generic)]
    return {"generic_heading_gate": {"status": "PASS" if not violations else "FAIL", "violations": violations}, "narrative_distinctness_gate": {"status": "PASS" if len(set(architecture.get("narrative_states") or [])) >= 4 and len(set(purposes)) >= 4 else "FAIL"}, "renderer_grammar_diversity_gate": {"status": "PASS" if len(set(grammars)) >= 3 else "FAIL", "unique_grammars": len(set(grammars))}, "emotional_continuity_gate": {"status": "PASS" if _text(genome.get("emotional_tempo")) and all(item.get("copy_density") for item in arc) else "FAIL"}, "cta_delta_gate": {"status": "PASS" if len({(item.get("stage"), item.get("action_reason")) for item in ctas}) == len(ctas) else "FAIL", "cta_count": len(ctas)}, "mobile_re_art_direction_gate": {"status": "PASS" if len(genome.get("mobile_redirection") or {}) >= 2 else "FAIL"}}
