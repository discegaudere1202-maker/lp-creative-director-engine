"""Evidence graph IR for Round 2C."""
from __future__ import annotations

from typing import Any


def build_evidence_graph(snapshot: dict[str, Any]) -> dict[str, Any]:
    facts = snapshot.get("facts", [])
    conflicted = {fact_id for group in snapshot.get("conflicts", []) for fact_id in group.get("fact_ids", [])}
    nodes = []
    edges = []
    for fact in facts:
        fact_id = fact["fact_id"]
        node_status = "CONFLICTED" if fact_id in conflicted else "ACTIVE"
        nodes.append({"node_id": fact_id, "node_type": "FACT", "value": fact["value"], "category": fact["category"], "confidence": fact["confidence"], "status": node_status, "source": fact["source"], "allowed_usage": fact["allowed_usage"], "claim_safety": fact["claim_safety"]})
        for decision_id in fact.get("decision_relevance", []):
            edges.append({"from": fact_id, "to": decision_id, "relation": "SUPPORTS_DECISION", "eligible": node_status == "ACTIVE"})
    return {
        "schema_version": "evidence_graph_v2",
        "company_id": snapshot.get("company_id"),
        "nodes": nodes,
        "edges": edges,
        "conflict_policy": "CONFLICTED facts never enter Hero or Main proof; resolve only through Hearing.",
        "proxy_evidence_policy": "Generated/free imagery may explain context but never asserts a real result, person, place, or case.",
        "counts": {"fact_nodes": len(nodes), "decision_edges": len(edges), "conflicted_nodes": sum(node["status"] == "CONFLICTED" for node in nodes)},
    }


def active_facts(graph: dict[str, Any]) -> list[dict[str, Any]]:
    return [node for node in graph.get("nodes", []) if node.get("status") == "ACTIVE"]
