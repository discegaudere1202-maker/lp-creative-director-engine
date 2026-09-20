from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("round2h_d",ROOT/"scripts"/"run_round2h_d_nagi.py")
M=importlib.util.module_from_spec(SPEC); assert SPEC and SPEC.loader; SPEC.loader.exec_module(M)
def test_direction_copy_and_public_labels():
    meta={k:{"output":"assets/x.png","public_label":"service image"} for k in M.ASSETS}
    text=M.build_html(meta)
    assert "予約する前に、" in text and "知って選べる。" in text
    assert "受ける" in text and "学ぶ" in text and "ヒーリングを知る" in text
    assert "REPRESENTATIVE" not in text and "QUESTION MODE" not in text
def test_public_gate_fail_closed():
    good="<body>"+"".join(f'<section id="{x}"></section>' for x in ["top","entry","before-touch","treatment","school","healing","human","guide","faq","booking","closing"])+"<p>サービスイメージ</p></body>"
    assert M.static_gates(good,{})["status"]=="PASS"
    assert "REPRESENTATIVE" in M.static_gates(good.replace("サービスイメージ","REPRESENTATIVE"),{})["internal_label_leaks"]
def test_a02_crop_contract():
    assert M.ASSETS["A01"][0]==M.ASSETS["A02"][0]
