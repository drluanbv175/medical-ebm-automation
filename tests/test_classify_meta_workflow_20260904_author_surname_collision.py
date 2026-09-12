"""Hồi quy phát hiện MEDIUM của Workflow đối kháng đa-agent vòng 2 (2026-09-04).

`detect_official_org()` gọi `match_authority_source(journal, authors, title)`
— tham số `authors` nằm ở vị trí 1, tức lọt vào `primary_blob` (2 tham số
đầu) mà `match_authority_source()` coi là AN TOÀN cho bí danh viết tắt NGẮN/
mơ hồ (WHO, ESC, ASH, GOLD, ADA...). Nhưng `authors` là TÊN NGƯỜI, không
phải tên tổ chức — một tác giả có họ trùng ngẫu nhiên với bí danh (ví dụ họ
"Ash" — họ tiếng Anh có thật — trùng ASH/ISTH; họ "Gold" trùng GOLD) khiến
bài báo bị gán SAI nhãn tổ chức dù nội dung không liên quan gì tới tổ chức
đó. Hàm này hiện chưa được gọi ở production (chỉ infer_study_type được
dùng), nhưng match_authority_source() dùng chung logic này cũng được
app/scoring/evidence_quality.py::score_evidence_item() gọi trong tính điểm
chứng cứ THẬT — lỗi nằm ở logic lõi dùng chung, không phải chỉ ở một lời gọi
không ai dùng.

Vá: chèn None ở vị trí 1 khi gọi match_authority_source(), giữ journal là
trường DUY NHẤT nằm trong primary_blob (an toàn cho bí danh ngắn/mơ hồ);
authors + title vẫn được đối chiếu qua blob tổng hợp cho bí danh DÀI/không
mơ hồ (ví dụ tác giả tập thể "World Health Organization").

Nguyên tắc viết test: gọi thẳng hàm với dữ liệu tái hiện đúng ca lỗi, không
grep chuỗi trong mã nguồn.
"""
from app.sources.classify_meta import detect_official_org


def test_author_surname_ash_khong_con_bi_nham_thanh_ash_isth():
    """★★ Ca chính: tác giả họ 'Ash' (họ tiếng Anh có thật), bài về ung thư
    phổi — không liên quan huyết học. Trước bản vá: trả về 'ASH/ISTH'."""
    result = detect_official_org(
        title="Long-term outcomes of lung cancer screening in high-risk populations",
        journal="J Thorac Oncol",
        authors="Ash P, Nguyen T, Patel R",
    )
    assert result is None, result


def test_author_surname_gold_khong_con_bi_nham_thanh_gold():
    """Ca chính thứ hai: tác giả họ 'Gold', bài về viêm khớp dạng thấp —
    không liên quan COPD. Trước bản vá: trả về 'GOLD'."""
    result = detect_official_org(
        title="Effects of a novel biologic on rheumatoid arthritis disease activity",
        journal="Clin Rheumatol",
        authors="Gold M, Lee K",
    )
    assert result is None, result


def test_journal_gut_that_van_khop_dung():
    """Đối chứng: 'Gut' là TẠP CHÍ thật (ACG/AGA/ASGE) — bản vá không được
    làm mất khả năng nhận diện đúng khi bí danh ngắn nằm ở journal thật."""
    assert detect_official_org(title="x", journal="Gut", authors="Chen L") == "ACG/AGA/ASGE"


def test_journal_circulation_van_khop_aha():
    """Đối chứng: journal chứa bí danh (Circulation -> AHA) không đổi hành vi."""
    result = detect_official_org(title="x", journal="Circulation", authors="Smith J")
    assert result == "ACC/AHA"


def test_bug_13_08_title_chua_who_khong_tai_mo():
    """Đối chứng chống hồi quy bug ĐÃ VÁ 13/08/2026: title chứa từ 'who' như
    một phần câu tiếng Anh thường ('patients who...') không được khớp nhầm
    WHO khi journal hiện diện nhưng authors vắng mặt."""
    result = detect_official_org(
        journal="J Surg", authors=None, title="patients who underwent surgery",
    )
    assert result is None, result


def test_tac_gia_tap_the_ten_dai_van_khop_qua_blob_tong_hop():
    """Đối chứng: bí danh DÀI/không mơ hồ (đủ đặc hiệu để không trùng ngẫu
    nhiên) vẫn khớp được qua authors — bản vá chỉ chặn bí danh NGẮN/mơ hồ,
    không chặn hoàn toàn việc tra cứu trong trường authors."""
    result = detect_official_org(
        title="Global tuberculosis report",
        journal="Tech Report",
        authors="World Health Organization",
    )
    assert result == "WHO", result


def test_khong_authors_van_hoat_dong_binh_thuong():
    """Đối chứng: gọi không truyền authors (mặc định None) vẫn hoạt động
    đúng như trước bản vá."""
    assert detect_official_org("KDIGO 2024 guideline", "Kidney International") == "KDIGO"
