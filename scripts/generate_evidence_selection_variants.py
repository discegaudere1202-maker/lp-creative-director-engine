from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
proto = ROOT / "examples" / "prototypes"


def write_variant(source_name: str, target_name: str, marker: str, replacement: str) -> None:
    source = (proto / source_name).read_text(encoding="utf-8")
    if marker not in source:
        raise SystemExit(f"marker not found: {source_name}")
    target = source.replace(marker, replacement, 1)
    (proto / target_name).write_text(target, encoding="utf-8")


core_p10 = (proto / "p10_customer_state_transition_core_v1.html").read_text(encoding="utf-8")
marker_p10 = '<span>個人の相談は無料です。</span><span class="process">相談では、モヤモヤを聞き、価値観を整理します。</span>'
write_variant(
    "p10_customer_state_transition_core_v1.html",
    "p10_customer_state_transition_accountability_v1.html",
    marker_p10,
    '<span>個人の相談は無料です。</span><span class="accountability">公式プロフィール掲載：宮原 彩乃（キャリアコンサルタント）。</span><span class="process">相談では、モヤモヤを聞き、価値観を整理します。</span>',
)
write_variant(
    "p10_customer_state_transition_core_v1.html",
    "p10_customer_state_transition_continuity_v1.html",
    marker_p10,
    '<span>個人の相談は無料です。</span><span class="continuity">つぶだてるで転職した方には、転職後も無料でキャリアに伴走します。</span><span class="process">相談では、モヤモヤを聞き、価値観を整理します。</span>',
)
write_variant(
    "p10_customer_state_transition_core_v1.html",
    "p10_customer_state_transition_business_model_v1.html",
    marker_p10,
    '<span>個人の相談は無料です。</span><span class="business-model">企業からの紹介手数料で運営されています。</span><span class="process">相談では、モヤモヤを聞き、価値観を整理します。</span>',
)

baseline_p02 = (proto / "p02_customer_world_translation_v3.html").read_text(encoding="utf-8")
marker_p02 = '<span class="proof-line">20年 / 300社以上の支援経験</span>制度名が分からなくても大丈夫です。<br>お困りごとの状況を、そのままお聞かせください。<span class="process">状況を聞く → 必要な制度を整理する</span>'
write_variant(
    "p02_customer_world_translation_v3.html",
    "p02_customer_world_translation_process_v1.html",
    marker_p02,
    '<span class="proof-line">20年 / 300社以上の支援経験</span>制度名が分からなくても大丈夫です。<br>お困りごとの状況を、そのままお聞かせください。<span class="process">お問い合わせ → 内容を伺う → サービス説明・見積<br>納得いただいた段階で契約へ。</span>',
)
write_variant(
    "p02_customer_world_translation_v3.html",
    "p02_customer_world_translation_authority_v1.html",
    marker_p02,
    '<span class="proof-line">緒方 幸一 / 社会保険労務士｜20年勤務・300社以上を支援</span>制度名が分からなくても大丈夫です。<br>お困りごとの状況を、そのままお聞かせください。',
)
