"""G0/G1 nối hợp đồng ô trống chung (03–04/10/2026).

Khoá: (1) marker CŨ của G0/G1 vẫn bắt nguyên ngữ nghĩa (chuỗi con trên value.upper()); (2) ô mẫu khuôn sinh và nhãn
nháp trong GIÁ TRỊ TRƯỜNG không còn tới PASS (đo 03/10: novelty_justification của C1a mở đầu bằng «[DỰ THẢO — CHỜ
BÁC SĨ…]» mà G0 vẫn PASS_G0_CONFIRMED); (3) giá trị hợp lệ không bị báo nhầm («[Đã pin bởi bác sĩ — …]», «N/A — lý
do», «...» trong văn xuôi) và một đề tài điền thật VẪN tới PASS. Chỉ ĐỌC dữ liệu C1a đã vào git (chép sang tmp,
write=False). """
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import g0_quality_gate as G0  # noqa: E402
import g1_quality_gate as G1  # noqa: E402

STUDY = "hai-long-benh-nhan-C1a-BVQY175"
C1A = ROOT / "exports" / STUDY
CU_G0 = ("[CẦN", "[REQUIRE_HUMAN", "CHƯA XÁC NHẬN", "[TODO", "___", "SUY RA TỪ TOPIC", "XXX")


# ── G0: vị từ trường ──────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("dau", CU_G0)
def test_g0_marker_cu_van_bat_ca_chu_thuong(dau):
    assert G0._present(f"Nội dung {dau} còn") is False
    assert G0._present(f"Nội dung {dau.lower()} còn") is False      # bản cũ so trên value.upper()


@pytest.mark.parametrize("v", ["[DỰ THẢO — CHỜ BÁC SĨ ĐỌC] Tính mới…", "Ở [P — điền]", "[xem §3 bên dưới]",
                               "tại [nơi thực hiện]", "[TO BE COMPLETED]", "[TBD]", "<CẦN PMID>",
                               "[XÁC NHẬN THỦ CÔNG NGOÀI HỆ THỐNG]", "……", "?", "-", "☐ tăng ☐ giảm"])
def test_g0_o_mau_khong_con_la_noi_dung(v):
    assert G0._present(v) is False, v
    assert G0._con_o_trong(v) is True, v


@pytest.mark.parametrize("v", ["Điểm hài lòng trung bình 5 mức đo ... tại thời điểm ra về",
                               "Không có nhóm so sánh — mô tả",
                               "Người bệnh ngoại trú ≥ 18 tuổi"])
def test_g0_van_xuoi_hop_le(v):
    assert G0._present(v) is True, v


def test_g0_danh_sach_doi_moi_phan_tu_that():
    assert G0._present(["Tử vong tim mạch", "[CẦN BÁC SĨ ẤN ĐỊNH]"]) is False
    assert G0._present(["Tử vong tim mạch", "Nhập viện"]) is True
    assert G0._present([]) is False


def _ban_sao_c1a(tmp_path: Path) -> Path:
    d = tmp_path / STUDY
    d.mkdir()
    for ten in ("G0_checkpoint.json", "study_meta.json", f"G0_A1_PICO_FINER_{STUDY}.md"):
        shutil.copy2(C1A / ten, d / ten)
    # 11/10/2026: hai tệp agent G0-T3/T4 là một phần hồ sơ — checkpoint ghi danh mục đọc bổ sung lúc dựng A1 và
    # G0-AUTO-05 đối chiếu nó với G0_TONG_HOP_BANG_CHUNG; bản sao thiếu tệp này là bản sao SAI (A1 «lệch danh mục»).
    for ten in (f"G0_TONG_HOP_BANG_CHUNG_{STUDY}.json", f"G0_KHOANG_TRONG_{STUDY}.json"):
        if (C1A / ten).is_file():
            shutil.copy2(C1A / ten, d / ten)
    return d


NHAN_NHAP = "[DỰ THẢO — CHỜ BÁC SĨ ĐỌC 12 PMID Ở §3 CỦA A1 RỒI CHỐT]"


def _ban_sao_c1a_nhan_nhap(tmp_path: Path) -> Path:
    """Bản sao C1a mà tính mới MANG nhãn nháp như đo ngày 03/10 — chèn trên bản sao, không phụ thuộc trạng thái sống.

    11/10/2026: PI đã chốt G0 thật (bỏ nhãn) ⇒ hai test đọc thẳng dữ liệu sống vỡ (CI #117). Đồ gá tự tạo đúng tình
    huống cần khoá thay vì giả định đề tài thật dừng mãi ở đó."""
    d = _ban_sao_c1a(tmp_path)
    p = d / "study_meta.json"
    meta = json.loads(p.read_text(encoding="utf-8"))
    g0 = meta["gate_params"]["G0"]
    if not str(g0.get("novelty_justification") or "").lstrip().startswith("[DỰ THẢO"):
        g0["novelty_justification"] = f"{NHAN_NHAP} {g0.get('novelty_justification') or ''}".strip()
    p.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    return d


@pytest.mark.skipif(not C1A.is_dir(), reason="thư mục C1a không có trong checkout này")
def test_g0_c1a_nhan_nhap_o_tinh_moi_khong_con_pass(tmp_path):
    d = _ban_sao_c1a_nhan_nhap(tmp_path)
    r = G0.evaluate_study(STUDY, d, write=False)
    h6 = next(c for c in r["human_criteria"] if c["id"] == "G0-HUMAN-06")
    assert r["status"] == "DRAFT_READY_NEEDS_HUMAN_REVIEW", r["status"]
    assert h6["status"] == "REVIEW" and "còn ô trống/nhãn nháp" in h6["evidence"]
    assert "Gỡ hết nhãn nháp" in h6["action"]


@pytest.mark.skipif(not C1A.is_dir(), reason="thư mục C1a không có trong checkout này")
def test_g0_c1a_dien_that_van_toi_pass(tmp_path):
    """Không tạo báo nhầm vĩnh viễn: bác sĩ làm ĐÚNG các việc cổng đòi thì G0 của C1a lại PASS.

    04/10/2026 (soát từng cổng): ngoài bỏ nhãn nháp ở tính mới, một lần chốt hợp lệ nay cần lý do cho từng tiêu chí
    FINER (C1a đang để True trơn — G0-03), ngày PI tự tra WHO ICTRP (G0-HUMAN-08, QĐ-17) và dấu vân tay của nội dung
    đang chốt (G0-07). Dấu tính SAU cùng, trên đúng nội dung đã sửa (mọi giá trị ở đây là của test, không ghi C1a)."""
    import g0_quality_gate as G0Q

    d = _ban_sao_c1a_nhan_nhap(tmp_path)
    meta = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
    g0 = meta["gate_params"]["G0"]
    g0["novelty_justification"] = g0["novelty_justification"].split("]", 1)[1].strip()
    for k in ("finer_feasible", "finer_interesting", "finer_novel", "finer_ethical", "finer_relevant"):
        g0[k] = "Đạt — lý do do bác sĩ viết (giá trị của test)"
    g0["registry_manual_checked"] = {"ictrp": "2026-08-15", "prospero": None}
    cp = json.loads((d / "G0_checkpoint.json").read_text(encoding="utf-8"))
    # 14/10/2026: lượt tra lại ClinicalTrials.gov của C1a ra thử nghiệm đang tuyển ⇒ cổng đòi thêm đánh giá chồng lấn
    # (G0-HUMAN-08) — đó cũng là việc bác sĩ phải làm, không phải nới điều kiện PASS.
    if isinstance((cp.get("registry_check") or {}).get("n_active"), int) and cp["registry_check"]["n_active"] > 0:
        g0["registry_overlap_assessment"] = "Không chồng lấn — nhận định của bác sĩ (giá trị của test)"
    g0["dau_van_tay_chot"] = G0Q.dau_van_tay_g0(cp, meta)
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    r = G0.evaluate_study(STUDY, d, write=False)
    assert r["status"] == "PASS_G0_CONFIRMED", [c for c in r["human_criteria"] if c["status"] != "PASS"]


# ── G1: _present giữ any() để chọn nguồn; _filled đòi mọi phần tử thật ──────────────────────────────────────────────
@pytest.mark.parametrize("dau", ("[CẦN", "[REQUIRE_HUMAN", "CHƯA XÁC NHẬN"))
def test_g1_marker_cu_van_bat(dau):
    assert G1._present(f"x {dau.lower()} y") is False


def test_g1_filled_chat_hon_present():
    assert G1._present(["Khoa A", "___"]) is True             # chọn nguồn: giữ any() cũ
    assert G1._filled(["Khoa A", "___"]) is False              # chấm tiêu chí: mọi phần tử
    assert G1._filled("Khoa Nội [TỪ §2 Bias Control]") is False
    assert G1._filled("Ngày [DD/MM/YYYY]") is False
    assert G1._filled("Tỷ lệ [tỷ lệ/trung bình]") is False


@pytest.mark.parametrize("v", ["[Đã pin bởi bác sĩ — cross_sectional]",
                               "N/A — thiết kế mô tả cắt ngang, không can thiệp",
                               "Tiêu đề thật có karyotype 47,XXX"])
def test_g1_khong_bao_nham(v):
    if "47,XXX" in v:
        assert G1._present(v) is True                           # _present dựng chữ artifact — không bị XXX chặn
    else:
        assert G1._filled(v) is True, v


def test_g1_list_complete_doi_moi_muc():
    assert G1._list_complete(["Tiêu chí A", "[CẦN BỔ SUNG]"]) is False
    assert G1._list_complete(["Tiêu chí A", "Tiêu chí B"]) is True
    assert G1._list_complete([]) is False
