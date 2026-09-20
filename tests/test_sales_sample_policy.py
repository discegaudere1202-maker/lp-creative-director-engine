from lp_engine.sales_sample_policy import FactRecord, PROVISIONAL, VERIFIED, classify_public_facts, replacement_manifest


def test_provisional_facts_are_replaceable():
    row = FactRecord("treatment.price", "60分 8,800円", PROVISIONAL, "treatment_price", True)
    report = replacement_manifest([row])
    assert report["status"] == "PASS"
    assert report["replacement_count"] == 1


def test_verified_facts_do_not_need_replacement():
    row = FactRecord("contact.instagram", "@happyfuture_02", VERIFIED)
    report = classify_public_facts([row], "公式Instagram @happyfuture_02")
    assert report["status"] == "PASS"


def test_forbidden_public_placeholder_is_detected():
    row = FactRecord("contact.instagram", "@happyfuture_02", VERIFIED)
    report = classify_public_facts([row], "料金は未確認です")
    assert report["status"] == "FAIL"
    assert "未確認" in report["forbidden_public_hits"]
