from lp_engine.round2g_fidelity_gates import duplicate_text_gate, header_contrast_gate, recording_evidence_gate


def test_duplicate_text_gate_rejects_same_position_copy():
    nodes = [
        {"text": "見る", "x": 10, "y": 10, "w": 80, "h": 40, "opacity": 1, "visibility": "visible", "display": "block"},
        {"text": "見る", "x": 10, "y": 10, "w": 80, "h": 40, "opacity": 1, "visibility": "visible", "display": "block"},
    ]
    assert duplicate_text_gate(nodes)["status"] == "FAIL"


def test_duplicate_text_gate_ignores_hidden_inactive_state():
    nodes = [
        {"text": "見る", "x": 10, "y": 10, "w": 80, "h": 40, "opacity": 1, "visibility": "visible", "display": "block"},
        {"text": "見る", "x": 10, "y": 10, "w": 80, "h": 40, "opacity": 0, "visibility": "hidden", "display": "none"},
    ]
    assert duplicate_text_gate(nodes)["status"] == "PASS"


def test_header_and_recording_gates_are_fail_closed():
    assert header_contrast_gate(7.2, {"V01": False, "V02": True, "V09": True})["status"] == "PASS"
    assert header_contrast_gate(2.1, {"V01": False, "V02": True})["status"] == "FAIL"
    assert recording_evidence_gate(.71, 16, [.8, .9])["status"] == "PASS"
    assert recording_evidence_gate(.99, 16, [.99, .99])["status"] == "FAIL"
