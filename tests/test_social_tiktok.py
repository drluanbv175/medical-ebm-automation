"""Test sinh nội dung TikTok: gác độ tin cậy + KHÔNG bịa (nguyên văn truy vết được)."""
import re

from app.social.content import build_post, eligible_for_post, render_caption

ABS = ("This randomized trial enrolled 6609 patients with chronic kidney disease. "
       "Empagliflozin reduced the risk of the primary outcome (hazard ratio 0.72; "
       "95% CI 0.64 to 0.82; p<0.001). "
       "The risk of bleeding was increased; serious adverse events were monitored. "
       "We recommend dose adjustment in severe hepatic impairment.")


def _row(**over):
    base = {
        "id": 1, "title": "Empagliflozin in chronic kidney disease",
        "abstract": ABS, "clinical_area": "Thận", "source": "NEJM",
        "study_type": "randomized_controlled_trial", "reliability_tier": "A",
        "classification": "actionable", "is_actionable": True,
        "operational_evidence_level": "High", "evidence_level": "High",
        "doi": "10.1056/abc", "pmid": "123456", "url": "https://example.org/x",
        "synthesis": {"doi_tuong_ap_dung": "Người bệnh CKD",
                      "hanh_dong_de_xuat": "Cân nhắc theo guideline",
                      "canh_bao_can_trong": "Theo dõi an toàn"},
    }
    base.update(over)
    return base


def _norm(s):
    return re.sub(r"\s+", " ", s or "").strip()


def test_eligibility_strong_is_recommendation():
    assert eligible_for_post(_row())["kind"] == "recommendation"


def test_eligibility_weak_is_watch():
    e = eligible_for_post(_row(study_type="preprint", reliability_tier="D",
                               classification="watch_only", is_actionable=False))
    assert e["kind"] == "watch"


def test_excluded_not_eligible():
    assert eligible_for_post(_row(classification="excluded"))["ok"] is False
    assert build_post(_row(classification="excluded")) is None


def test_build_post_structure():
    post = build_post(_row())
    assert post is not None
    assert post["kind"] == "recommendation"
    assert post["point_slides"], "Phải có slide điểm chính"
    assert post["ids"] and any("DOI" in i for i in post["ids"])


def test_no_fabrication_every_bullet_is_verbatim():
    # Mọi câu tiếng Anh trên slide PHẢI là chuỗi con của abstract gốc.
    post = build_post(_row())
    src = _norm(ABS)
    for sl in post["point_slides"]:
        for b in sl["bullets"]:
            assert _norm(b["en"]) in src, f"Câu không khớp nguồn (bịa?): {b['en']}"


def test_caption_has_source_and_disclaimer():
    cap = render_caption(build_post(_row()))
    assert "Nguồn" in cap
    assert "tham khảo" in cap.lower()
    assert cap.strip().endswith("#suckhoe") or "#" in cap  # có hashtag


def test_post_without_extractable_points_is_none():
    # Abstract không có câu tín hiệu lâm sàng -> không đủ nội dung đáng tin -> None.
    assert build_post(_row(abstract="Hello world. This is short text only.")) is None


# --- Video (TTS + ffmpeg) ---------------------------------------------------
def test_video_narration_aligns_with_slides_and_strips_emoji():
    from app.social import video as v
    post = build_post(_row())
    nar = v._slide_narrations(post)
    # mỗi slide ảnh (cover + điểm + nguồn) có đúng 1 câu đọc.
    assert len(nar) == 2 + len(post["point_slides"])
    joined = " ".join(nar)
    assert "👤" not in joined and "✅" not in joined  # emoji bị loại khỏi lời đọc
    assert post["source_name"] in joined               # có đọc nguồn


def test_video_availability_is_boolean():
    from app.social import video as v
    assert isinstance(v.available(), bool)
    assert isinstance(v.tts_available(), bool)


# --- Doodle y khoa ----------------------------------------------------------
def test_doodles_mapping_by_area_and_keyword():
    from app.social import doodles as dd
    assert "heart" in dd.doodles_for("Tim mạch", "Suy tim cập nhật")
    assert "kidney" in dd.doodles_for("Thận", "CKD")
    assert "bars" in dd.doodles_for("Khác", "Nghịch lý chi phí học")  # từ khoá 'chi phí'
    assert dd.doodles_for("Khác", "")  # luôn có fallback, không rỗng


def test_doodles_registry_all_drawable():
    from PIL import Image, ImageDraw

    from app.social import doodles as dd
    img = Image.new("RGB", (200, 200), (255, 255, 255))
    d = ImageDraw.Draw(img)
    for name in dd.REGISTRY:
        assert dd.draw(d, name, 100, 100, 150, (0, 0, 0)) is True


# --- Tự soạn nội dung -------------------------------------------------------
def test_parse_manual_content_blocks_to_slides():
    from app.social.package import parse_manual_content
    txt = "Tiêu đề A\nÝ 1\nÝ 2\n\nTiêu đề B\nÝ 3"
    slides = parse_manual_content(txt)
    assert len(slides) == 2
    assert slides[0]["heading"] == "Tiêu đề A" and slides[0]["bullets"] == ["Ý 1", "Ý 2"]
    assert slides[1]["bullets"] == ["Ý 3"]


def test_build_manual_post_structure():
    from app.social.content import build_manual_post
    post = build_manual_post("Huyết áp tại nhà",
                             [{"heading": "Vì sao?", "bullets": ["Chính xác hơn"]}],
                             area="Tim mạch", source="ESC 2024")
    assert post is not None
    assert post["title"]["en"] == "Huyết áp tại nhà"
    assert post["point_slides"][0]["bullets"][0]["en"] == "Chính xác hơn"
    assert post["source_name"] == "ESC 2024"
    assert post["point_slides"][0]["bullets"][0]["vi"] is None  # không tự dịch


def test_build_manual_post_empty_is_none():
    from app.social.content import build_manual_post
    assert build_manual_post("", []) is None


# --- Hiệu ứng vẽ tay (draw-on) ---------------------------------------------
def test_animate_detects_content_band():
    import numpy as np

    from app.social import animate
    bg = np.full((animate.H, animate.W, 3), 250, np.uint8)
    final = bg.copy()
    final[300:360, 100:500] = 20  # khối mực
    bands = animate._content_bands(final, bg)
    assert len(bands) == 1
    y0, y1, x0, x1 = bands[0]
    assert y0 <= 300 and y1 >= 360 and x0 <= 100 and x1 >= 500


def test_speak_clean_and_narration_pauses():
    from app.social.video import _sentence, _speak_clean, default_narrations
    assert _speak_clean("135/85 mmHg") == "135 trên 85 mmHg"
    assert _speak_clean("An toàn / Thận trọng") == "An toàn và Thận trọng"
    assert _sentence("Xin chào")[-1] == "."        # tự thêm dấu để ngắt nghỉ
    from app.social.content import build_manual_post
    post = build_manual_post("Tiêu đề", [{"heading": "Vì sao?",
                                          "bullets": ["Ý một", "Ý hai"]}], area="Thận")
    narr = default_narrations(post)
    assert len(narr) == 2 + len(post["point_slides"])
    assert all(n.strip()[-1] in ".!?…" for n in narr if n.strip())


def test_preview_manual_returns_narrations(tmp_path):
    from app.social import render
    if not render.whiteboard_available():
        import pytest
        pytest.skip("Không có font whiteboard")
    from app.social.package import preview_manual
    pv = preview_manual("Đo huyết áp", "Vì sao?\nChính xác hơn", area="Tim mạch",
                        style="whiteboard")
    assert pv["ok"] and pv["n_slides"] >= 2
    assert len(pv["narrations"]) == pv["n_slides"]
    assert pv["post"]["point_slides"]  # có post để tạo video sau khi sửa


def test_animate_frame_count_and_shape(tmp_path):
    from app.social import animate, render
    if not render.whiteboard_available():
        import pytest
        pytest.skip("Không có font whiteboard")
    from PIL import Image
    arr = animate._bg_array().copy()
    arr[400:470, 120:600] = 30  # 1 khối mực giả
    p = tmp_path / "s.png"
    Image.fromarray(arr).save(p)
    frames = list(animate.slide_frames(p, dur=1.0, fps=10))
    assert len(frames) == 10
    assert frames[0].shape == (animate.H, animate.W, 3)
