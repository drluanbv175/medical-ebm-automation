"""Làm sạch abstract: gỡ thẻ XML/HTML cấu trúc + giải mã ký tự, KHÔNG đổi nội dung."""
from app.utils.text import clean_text

DIRTY = ('<sec><st>Background</st><p>Drug X is an inhibitor. Symptoms BASDAI &ge;4 '
         'despite &ge;2 NSAIDs.</p></sec>'
         '<sec><st>Results</st><p>ASAS20 51.2% vs 48.8% (p&lt;0.05).</p></sec>'
         '<sec><st>Registration</st><p><A HREF="NCT04947579">NCT04947579</A>.</p></sec>')


def test_strips_structural_tags():
    out = clean_text(DIRTY)
    assert "<sec>" not in out and "<st>" not in out and "<p>" not in out
    assert "<A" not in out and "HREF" not in out
    # Không còn cặp thẻ <...>
    import re
    assert not re.search(r"<[^>]+>", out)


def test_decodes_entities():
    out = clean_text(DIRTY)
    assert "&ge;" not in out and "≥4" in out and "≥2" in out
    assert "&lt;" not in out and "p<0.05" in out  # p<0.05 giữ đúng dấu nhỏ hơn


def test_keeps_content_verbatim():
    out = clean_text(DIRTY)
    for must in ("Drug X is an inhibitor", "51.2%", "48.8%", "NCT04947579", "NSAIDs"):
        assert must in out, f"Mất nội dung gốc: {must}"


def test_section_titles_become_readable():
    out = clean_text(DIRTY)
    assert "Background:" in out and "Results:" in out and "Registration:" in out


def test_no_translation_artifact_source():
    """Không còn '</sec>' để dịch máy biến thành '</giây>'."""
    out = clean_text(DIRTY)
    assert "sec>" not in out.lower() and "giây" not in out.lower()


def test_empty_and_none():
    assert clean_text("") == ""
    assert clean_text(None) is None


def test_plain_text_unchanged():
    plain = "Empagliflozin reduced the risk (HR 0.72, 95% CI 0.64-0.82)."
    assert clean_text(plain) == plain


def test_bilingual_drops_chinese_keeps_english():
    """Abstract song ngữ (Anh + Trung) -> bỏ phần Trung trùng lặp, giữ tiếng Anh."""
    import re
    bil = ("This guideline offers 11 recommendations clarifying vaccination indications "
           "and rational antibacterial use for respiratory specialists and GPs. "
           "本指南聚焦流感预防、临床识别与筛查，明确慢性气道疾病患者年度流感疫苗接种指征。")
    out = clean_text(bil)
    assert not re.search(r"[一-鿿]", out), "Vẫn còn ký tự Trung"
    assert "11 recommendations" in out


def test_chinese_only_kept_for_translation():
    """Chỉ tiếng Trung (không có tiếng Anh đáng kể) -> GIỮ nguyên để dịch ZH->VI."""
    import re
    zh = "本指南聚焦流感预防、临床识别与筛查，明确慢性气道疾病患者年度流感疫苗接种指征。" * 2
    out = clean_text(zh)
    assert re.search(r"[一-鿿]", out), "Không nên bỏ khi chỉ có tiếng Trung"


def test_degenerate_translation_detected():
    from app.services.translate import _is_degenerate
    assert _is_degenerate("Bạn có thể làm được điều đó. " * 8)
    assert not _is_degenerate(
        "Ức chế MK2 không đủ mang lại lợi ích lâm sàng trong viêm cột sống dính khớp.")
