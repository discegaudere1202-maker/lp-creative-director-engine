from lp_engine.round2g_fidelity_gates import motion_reality_gate, public_label_gate, screenshot_delta_gate, spec_actual_gate


def test_public_taxonomy_gate_rejects_required_negative_fixtures_and_clean_copy():
    report = public_label_gate("いつもの家に、気になるところがある。外壁・屋根・修繕・塗装")
    assert report["status"] == "PASS"
    assert report["leak_count"] == 0
    assert all(item["status"] == "PASS" for item in report["fixtures"])


def test_motion_gate_requires_real_intermediate_progression():
    samples = [{"timestamp_ms": i * 100, "state": "intermediate" if 2 <= i <= 7 else "transition", "transform_progress": i / 10, "mask_progress": i / 10} for i in range(12)]
    assert motion_reality_gate(samples)["status"] == "PASS"
    assert motion_reality_gate([{ "timestamp_ms": 0, "state": "transition", "transform_progress": 0, "mask_progress": 0 }, { "timestamp_ms": 100, "state": "transition", "transform_progress": 1, "mask_progress": 1 }])["status"] == "FAIL"


def test_delta_requires_mandatory_axes():
    before = {"topology": "split", "media_occupancy": .45, "dominant_colors": ["beige"], "typography_voice": "mono", "text_block_occupancy": .25, "motion_grammar": "fade", "rhythm": "dense"}
    after = {"topology": "full-bleed", "media_occupancy": .90, "dominant_colors": ["deep-field"], "typography_voice": "jp-display", "text_block_occupancy": .08, "motion_grammar": "cut-viewpoint", "rhythm": "observe-cut-pause"}
    assert screenshot_delta_gate(before, after)["status"] == "PASS"


def test_spec_actual_gate_rejects_two_column_v03():
    observed = {"hero_ratio": .9, "signs": 4, "craft": 3, "v03_media_ratio": 1, "v03_two_column": False, "motion_source": "V03", "motion_target": "V04", "motion_intermediate": "crop-scale-rise", "motion_transform": "translateY+scale", "cards": 0}
    assert spec_actual_gate(observed)["status"] == "PASS"
    observed["v03_two_column"] = True
    assert spec_actual_gate(observed)["status"] == "FAIL"
