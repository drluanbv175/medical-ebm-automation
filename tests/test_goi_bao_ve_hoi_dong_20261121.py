"""Gói chuẩn bị bảo vệ đề cương trước Hội đồng (21/11/2026) — `tools/goi_bao_ve_hoi_dong.py`.

Fixture tự soạn, ngoại tuyến, KHÔNG dùng nội dung đề tài thật (repo công khai): một đề cương nộp đủ mục, bốn biên bản
tranh biện (một lượt cũ, một lượt «sửa kết luận» có biên bản xử lý, một «chuyển bác sĩ», một chỉ có phản đối nội bộ),
một tệp biên bản hỏng và hai báo cáo phản biện (bản mới mang cả hai khuôn đang có). Mỗi luật S1–S2, Q1–Q4, P1 có ít
nhất một ca kiểm hành vi."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (REPO_ROOT, REPO_ROOT / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import goi_bao_ve_hoi_dong as G  # noqa: E402

MA = "de-tai-thu-bao-ve"
DC = f"DE_CUONG_NOP_HOI_DONG_{MA}.md"
MAU_SUA = "**Mục tiêu 2 – đại lượng cần ước lượng.**"

DE_CUONG = f"""# ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC

## KHẢO SÁT THỬ NGHIỆM TẠI KHOA MẪU

## THÔNG TIN CHUNG VỀ ĐỀ TÀI

| Mục | Nội dung |
|---|---|
| Chủ nhiệm đề tài | ……… |

# 1. ĐẶT VẤN ĐỀ

Câu mở đoạn một nêu bối cảnh của khoa mẫu. Câu thứ hai của đoạn một không được chọn.

Câu mở đoạn hai nêu vấn đề chính [1]. Câu sau của đoạn hai.

Đề tài có các mục tiêu sau:

1. Mục tiêu nằm trong đặt vấn đề không lên slide đặt vấn đề.

# 2. MỤC TIÊU NGHIÊN CỨU

## 2.1. Mục tiêu

1. Xác định tỷ lệ hài lòng tại khoa mẫu.
2. Phân tích yếu tố liên quan đến hài lòng.

## 2.3. Giả thuyết nghiên cứu

Mục tiêu 1 không đặt giả thuyết kiểm định. Với mục tiêu 2, giả thuyết H0 là tỷ số chênh bằng 1.

# 3. TỔNG QUAN TÀI LIỆU

## 3.2. Công cụ đo lường trong y văn

Câu tổng quan về công cụ của y văn không thuộc phương pháp.

## 3.5. Khoảng trống nghiên cứu và đóng góp của đề tài

Giới hạn của chiến lược tìm kiếm: chưa tra luận văn trong nước.

**Khoảng trống.** Chưa có số liệu tại khoa mẫu. Ngoài ra còn một câu phụ.

**Đóng góp của đề tài.** Đề tài cung cấp số liệu nền cho khoa mẫu.

# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU

## 4.1. Thiết kế nghiên cứu

Nghiên cứu mô tả cắt ngang có phân tích.

## 4.2. Địa điểm và thời gian nghiên cứu

Địa điểm là khoa mẫu. Thời gian từ tháng 01/2027 đến tháng 12/2027.

## 4.3. Đối tượng nghiên cứu

### 4.3.1. Tiêu chuẩn lựa chọn

- Người bệnh từ đủ 18 tuổi;
- Đồng ý tham gia nghiên cứu.

### 4.3.2. Tiêu chuẩn loại trừ

- Người bệnh từ chối tham gia.

## 4.4. Cỡ mẫu và phương pháp chọn mẫu

### 4.4.1. Cỡ mẫu

Áp dụng công thức ước lượng một tỷ lệ:

Trong đó Z bằng 1,96 và p bằng 0,5. Sai số tuyệt đối d bằng 0,05.
Kết quả n₀ bằng 385. Khoa có 50 bàn khám. Mỗi bàn có 4 khung giờ.
Cỡ mẫu cuối cùng của đề tài là 1.000 phiếu hợp lệ.

### 4.4.2. Phương pháp chọn mẫu

Chọn mẫu hệ thống phân tầng. Điểm bắt đầu được chọn ngẫu nhiên.

## 4.5. Công cụ thu thập số liệu

Công cụ thu thập là phiếu khảo sát tự điền.

## 4.6. Biến số nghiên cứu

Biến kết cục là mức hài lòng chung.

## 4.8. Sai số và biện pháp khống chế sai số

**Bảng 4.1. Các nguồn sai lệch và biện pháp khống chế**

| Nguồn sai lệch | Biểu hiện | Biện pháp khống chế |
|---|---|---|
| Sai lệch chọn mẫu | Điều tra viên tự chọn | Chọn mẫu hệ thống có điểm bắt đầu ngẫu nhiên |
| Sai lệch nhớ lại | Quên chi tiết | Khảo sát ngay sau lượt khám |

## 4.10. Xử lý và phân tích số liệu

Phân tích bằng phần mềm R. {MAU_SUA} Quần thể là người đã khám xong.

## 4.11. Đạo đức trong nghiên cứu

Đề tài chỉ tiến hành sau khi Hội đồng phê duyệt.

## 4.12. Hạn chế của nghiên cứu và phạm vi suy rộng kết quả

Kết quả chỉ áp dụng cho người bệnh đã hoàn thành lượt khám.

# 5. DỰ KIẾN KẾT QUẢ

Kết quả trình bày theo từng mục tiêu.

# 6. KẾ HOẠCH THỰC HIỆN

## 6.1. Nhân lực và phân công nhiệm vụ

Chủ nhiệm điều phối nhóm nghiên cứu.

## 6.2. Tiến độ thực hiện

Không thu thập số liệu trước khi được phê duyệt.

## 6.3. Dự trù kinh phí

Nguồn kinh phí là tự túc.

## 6.6. Kế hoạch phổ biến và ứng dụng kết quả

Báo cáo kết quả cho lãnh đạo bệnh viện.

# PHỤ LỤC B. BẢN THÔNG TIN VÀ PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU

Nội dung phiếu đồng ý.
"""

P_BAC = "Phản đối khoa học về quần thể bị trọng tài bác."
P_NOI_BO = ("run_g1_auto.py ghi checkpoint sai, study_meta lệch gate_params, cờ --khong-tra-pubmed chưa dùng, "
            "agent dieu-phoi-g1 phải chạy lại.")
L_GIU = "Luận điểm đề xuất L2: quần thể phân tích đã được định nghĩa ở mục 4.3."


def _ld(ma: str, noi_dung: str, **kw) -> dict:
    return {"ma": ma, "noi_dung": noi_dung, "can_cu": [{"loai": "tieu_chi", "gia_tri": "G1-HUMAN-02"}], **kw}


def _tb(gate: str, dp: str, moc: str, duoi: str, phan_bien: List[dict], tung: List[dict], ket_qua: str,
        **pq) -> dict:
    return {"schema": "hoi_dong_cong/v2", "study": MA, "gate": gate, "loai": "tranh_bien",
            "id": f"{gate}-TB-{moc.replace('-', '').replace(':', '')[:15]}-{duoi}", "thoi_diem": f"{moc}+07:00",
            "diem_quyet_dinh": {"ma": dp}, "tai_lieu_xet": [],
            "vong": [{"so": 1, "ben": "de_xuat", "luan_diem": [_ld("L1", "Luận điểm đề xuất L1 về thiết kế."),
                                                                _ld("L2", L_GIU)]},
                     {"so": 1, "ben": "phan_bien", "luan_diem": phan_bien}],
            "phan_quyet": {"tung_luan_diem": tung, "ket_qua": ket_qua, "ket_luan_cuoi": f"Kết luận cuối {duoi}.",
                           **pq}}


def _dung(goc: Path, *, bien_ban: bool = True, de_cuong: str = DE_CUONG, n_g3: int = 1000,
          them_pii: str = "") -> Path:
    """Dựng exports/<MA>/ đầy đủ; trả thư mục exports gốc."""
    d = goc / MA
    d.mkdir(parents=True)
    (d / DC).write_text(de_cuong, encoding="utf-8", newline="\n")
    (d / "G3_checkpoint.json").write_text(json.dumps({"confirmed_n": n_g3}) + "\n", encoding="utf-8", newline="\n")
    sha = hashlib.sha256((d / DC).read_bytes()).hexdigest()
    (d / f"PHAN_BIEN_DE_CUONG_NOP_20261001_{MA}.md").write_text(
        "# Báo cáo cũ\n\n## 9. CÂU HỎI CHO TÁC GIẢ\n\n1. Câu hỏi của bản cũ không được dùng?\n", encoding="utf-8",
        newline="\n")
    (d / f"PHAN_BIEN_DE_CUONG_NOP_20261101_{MA}.md").write_text(f"""# PHẢN BIỆN ĐỘC LẬP

| Mục | Nội dung |
|---|---|
| Mã sha256 lúc bắt đầu đọc | `{sha}` |

## 2. BẢNG TỔNG HỢP

| Mức | Số lượng | Ý nghĩa |
|---|---|---|
| 🔴 Phải sửa | 1 | Thiếu nguồn |

## 3. LỖI 🔴 — PHẢI SỬA TRƯỚC KHI NỘP

### Đ1. Con số không có nguồn

- **Vị trí:** dòng 12 (mục 4.10).
- **Trích:** «một câu trích».
- **Vấn đề:** con số 15,3% không dẫn nguồn.
  1. Ý phụ thứ nhất của vấn đề.
- **Căn cứ kiểm được:** truy nguồn sổ chứng cứ.
  - 15,32%: một bài trong nước.
- **Đề xuất:** thêm trích dẫn cho con số.

## 4. LỖI 🟠 — NÊN SỬA

### Lăng kính ① — Phương pháp

**O1. Mẫu số bất đối xứng**
- Vị trí: Phụ lục B.
- Vấn đề: mẫu số bị chọn theo kết quả.
- Đề xuất: báo song song hai cách tính.

## 5. GÓP Ý 🟢 — GỢI Ý

| # | Vị trí | Góp ý |
|---|---|---|
| G1 | Dòng 3 | Cân nhắc trích thêm hai trường. |

## 7. ĐỐI CHIẾU STROBE

| Mục | Nội dung phải định trước | Tình trạng | Ghi chú |
|---|---|---|---|
| STROBE 4 | Thiết kế | Đạt | Dòng 1 |

## 8. Bảng phát hiện

| STT | Mức | Vị trí | Vấn đề | Căn cứ | Đề xuất sửa |
|---|---|---|---|---|---|
| 1 | 🔴 (có điều kiện) | DE_CUONG:5 | Ô ngày ký còn trống. | Ghi chú | Điền ngày ký. |

## 9. CÂU HỎI CHO TÁC GIẢ

1. Xét nghiệm nội trú có được tính (mục 4.4.1)?
2. Ai là thống kê viên?

---

**Câu hỏi cho chủ nhiệm**
- Khoa có làm thứ Bảy không?

Đoạn kết không phải câu hỏi.
""", encoding="utf-8", newline="\n")
    if bien_ban:
        hd = d / "hoi_dong"
        for g in ("G0", "G1", "G3"):
            (hd / g).mkdir(parents=True)
        cu = _tb("G1", "DP-G1-2", "2026-11-01T10:00:00", "aaaa0001",
                 [_ld("P1", "Phản đối ở lượt cũ về estimand.", phan_doi="L1")],
                 [{"ma": "P1", "ket": "chap_nhan", "ly_do": "Lý do lượt cũ."}], "sua_ket_luan",
                 viec_sua=["Việc sửa lượt cũ."])
        moi = _tb("G1", "DP-G1-2", "2026-11-10T10:00:00", "aaaa0002",
                  [_ld("P1", "MT2 chưa có câu estimand-like." + them_pii, phan_doi="L1"),
                   _ld("P2", "Bên phản biện nhường điểm này.", phan_doi="L2", nhuong=True),
                   _ld("P3", P_BAC, phan_doi="L2"),
                   _ld("P4", P_NOI_BO, phan_doi="L1")],
                  [{"ma": "P1", "ket": "chap_nhan", "ly_do": "Căn cứ khớp, cần câu estimand-like."},
                   {"ma": "P2", "ket": "chap_nhan", "ly_do": "Nhường."},
                   {"ma": "P3", "ket": "bac", "ly_do": "Quần thể đã định nghĩa đủ."},
                   {"ma": "P4", "ket": "chap_nhan", "ly_do": "Đúng về công cụ."}],
                  "sua_ket_luan",
                  viec_sua=["Thêm câu estimand-like cho mục tiêu 2 vào đề cương.",
                            "Sửa run_g1_auto.py để checkpoint đồng bộ study_meta, chạy --khong-tra-pubmed, agent "
                            "dieu-phoi-g1 làm."],
                  giai_phap_tot_nhat={"phuong_an": "Thêm một câu estimand-like vào mục phân tích."})
        xl = {"schema": "hoi_dong_cong/v2", "study": MA, "gate": "G1", "loai": "xu_ly_viec_sua",
              "id": "G1-XL-20261112T100000-bbbb0001", "thoi_diem": "2026-11-12T10:00:00+07:00",
              "bien_ban_goc": moi["id"],
              "viec": [{"nguon": "viec_sua:1", "noi_dung": "Thêm câu estimand-like.", "cach_xu_ly": "da_sua",
                        "mo_ta": "Đã thêm đoạn vào mục phân tích.",
                        "can_cu": [{"loai": "tep", "gia_tri": f"{DC}:999", "mau": MAU_SUA},
                                   {"loai": "tep", "gia_tri": f"{DC}:999", "mau": "đại lượng cần ước lượng"},
                                   {"loai": "tep", "gia_tri": DC, "khong_chua": "câu sai đã gỡ"},
                                   {"loai": "tep", "gia_tri": f"{DC}:5", "mau": "chuỗi không còn trong đề cương"}]},
                       {"nguon": "viec_sua:2", "noi_dung": "Sửa công cụ.", "cach_xu_ly": "da_sua",
                        "mo_ta": "Mô tả việc sửa công cụ.",
                        "can_cu": [{"loai": "tep", "gia_tri": "G1_A2_PROTOCOL_DESIGN_x.md:3", "mau": "x"}]},
                       {"nguon": "giam-khao-cong:RQ1", "noi_dung": "Việc của đánh giá chéo.", "cach_xu_ly": "da_sua",
                        "can_cu": []}]}
        chuyen = _tb("G3", "DP-G3-2", "2026-11-11T10:00:00", "aaaa0003",
                     [_ld("P1", "Bộ biến rút gọn ô kết quả có thể phân loại sai.", phan_doi="L1")],
                     [{"ma": "P1", "ket": "chap_nhan", "ly_do": "Đúng, cần giới hạn."}], "chuyen_bac_si",
                     chuyen_bac_si=[{"van_de": "Giữ cách rút gọn ô hay ghi mọi kết quả?", "vi_sao": "PI quyết."},
                                    {"van_de": "Gắn cờ định danh cho trường ngày?", "vi_sao": "PI quyết."}])
        noi_bo = _tb("G0", "BD-G0-T1", "2026-11-05T10:00:00", "aaaa0004",
                     [_ld("P1", "g0_quality_gate.py ghi needs_input vào checkpoint; run_pipeline chạy lại G0-T1 với "
                                "cờ --topic, agent thu-thu-tai-lieu, tệp G0_pubmed_raw.json.", phan_doi="L1")],
                     [{"ma": "P1", "ket": "chap_nhan", "ly_do": "Đúng."}], "sua_ket_luan")
        for bb in (cu, moi, xl, noi_bo, chuyen):
            (hd / bb["gate"] / f"{bb['id']}.json").write_text(json.dumps(bb, ensure_ascii=False), encoding="utf-8",
                                                               newline="\n")
        (hd / "G3" / "quyet_dinh_bac_si.json").write_text(json.dumps({f"{chuyen['id']}#1": {
            "bien_ban": chuyen["id"], "van_de_so": 1, "loi_bac_si": "Giữ rút gọn, ghi giới hạn.",
            "thoi_diem": "2026-11-12T08:00:00+07:00"}}, ensure_ascii=False), encoding="utf-8", newline="\n")
        (hd / "G1" / "G1-TB-20261102T000000-hong.json").write_text("{không phải JSON", encoding="utf-8", newline="\n")
    return goc


def _anh_chup(d: Path) -> Dict[str, str]:
    return {p.relative_to(d).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(d.rglob("*")) if p.is_file()}


def _nguon(goc: Path) -> str:
    """Toàn bộ văn bản nguồn (đề cương + biên bản JSON dạng giải mã + báo cáo) — để kiểm «nguyên văn»."""
    d = goc / MA
    phan = [(d / DC).read_text(encoding="utf-8")]
    for p in sorted(d.rglob("*.json")):
        try:
            phan.append(json.dumps(json.loads(p.read_text(encoding="utf-8")), ensure_ascii=False))
        except ValueError:
            pass
    phan += [p.read_text(encoding="utf-8") for p in sorted(d.glob("PHAN_BIEN_DE_CUONG_NOP*.md"))]
    return "\n".join(phan)


def _goi(goc: Path) -> dict:
    return G.dung_goi(MA, goc / MA)


@pytest.fixture()
def goc(tmp_path: Path) -> Path:
    return _dung(tmp_path / "exports")


# ── Chạy khô / ghi / mã thoát ────────────────────────────────────────────────────────────────────────────────────────

def test_chay_kho_mac_dinh_khong_ghi_gi(goc: Path, capsys) -> None:
    truoc = _anh_chup(goc / MA)
    assert G.main(["--study", MA, "--exports-root", str(goc)]) == 0
    assert _anh_chup(goc / MA) == truoc
    assert "CHẠY KHÔ" in capsys.readouterr().out


def test_ghi_chi_tao_hai_tep_moi_khong_dong_cham_nguon(goc: Path) -> None:
    truoc = _anh_chup(goc / MA)
    assert G.main(["--study", MA, "--exports-root", str(goc), "--ghi", "--khong-word"]) == 0
    sau = _anh_chup(goc / MA)
    moi = sorted(set(sau) - set(truoc))
    assert moi == sorted([f"GOI_BAO_VE_CAU_HOI_{MA}.md", f"GOI_BAO_VE_DAN_SLIDE_{MA}.md"])
    assert {k: v for k, v in sau.items() if k in truoc} == truoc  # nguồn (đề cương, biên bản, báo cáo) giữ nguyên


def test_thu_muc_ra_ghi_ra_ngoai_exports(goc: Path, tmp_path: Path) -> None:
    truoc = _anh_chup(goc / MA)
    ra = tmp_path / "xem-thu"
    assert G.main(["--study", MA, "--exports-root", str(goc), "--ghi", "--khong-word", "--thu-muc-ra", str(ra)]) == 0
    assert sorted(p.name for p in ra.iterdir()) == sorted([f"GOI_BAO_VE_CAU_HOI_{MA}.md",
                                                           f"GOI_BAO_VE_DAN_SLIDE_{MA}.md"])
    assert _anh_chup(goc / MA) == truoc


def test_thieu_de_cuong_ma_2(tmp_path: Path) -> None:
    (tmp_path / MA).mkdir()
    assert G.main(["--study", MA, "--exports-root", str(tmp_path)]) == 2


def test_ma_de_tai_khong_hop_le_ma_3(goc: Path) -> None:
    assert G.main(["--study", "../ngoai", "--exports-root", str(goc)]) == 3


def test_json_tom_tat(goc: Path, capsys) -> None:
    assert G.main(["--study", MA, "--exports-root", str(goc), "--json"]) == 0
    t = json.loads(capsys.readouterr().out)
    assert t["slide"]["so"] == len(G.KHUON_SLIDE)
    assert t["cau_hoi"]["A_bien_ban"] == 4 and t["cau_hoi"]["N_noi_bo"] == 2
    assert t["cau_hoi"]["B_tep"] == f"PHAN_BIEN_DE_CUONG_NOP_20261101_{MA}.md"
    assert t["pii"] == []


# ── Dàn slide (S1, S2) ───────────────────────────────────────────────────────────────────────────────────────────────

def test_slide_nguyen_van_tro_dung_dong_va_khung_thoi_luong(goc: Path) -> None:
    dong = DE_CUONG.splitlines()
    slides, ten = G.dung_slide(dong, goc / MA)
    assert ten == "KHẢO SÁT THỬ NGHIỆM TẠI KHOA MẪU"
    assert 10 <= sum(s.phut for s in slides) <= 15
    cau = [c for s in slides for _n, ds in s.khoi for c in ds]
    assert len(cau) > 20
    for c in cau:  # mỗi câu là đoạn NGUYÊN VĂN của đúng dòng nó khai
        assert c.van in dong[c.dong - 1], (c.dong, c.van)
        assert not c.phu or c.phu in dong[c.dong - 1]
    for s in slides:
        assert s.nguon and all("dòng" in x for x in s.nguon), s.tieu_de
    md = G.render_slide(slides, ten, DC, len(dong), "a" * 64)
    assert md.count("## Slide ") == len(G.KHUON_SLIDE) and G.LOI_DAN in md


def _slide(goc: Path, khoa: str, de_cuong: str = DE_CUONG) -> G.Slide:
    slides, _ = G.dung_slide(de_cuong.splitlines(), goc / MA)
    return next(s for s in slides if s.khoa == khoa)


def _van(sl: G.Slide) -> List[str]:
    return [c.van for _n, ds in sl.khoi for c in ds]


def test_slide_co_mau_bo_sung_cau_mang_n_da_chot(goc: Path) -> None:
    v = _van(_slide(goc, "co_mau"))
    assert any("1.000 phiếu" in x for x in v)  # câu thứ 6 có số — vẫn được thêm vì mang N của G3
    assert "Áp dụng công thức ước lượng một tỷ lệ:" not in v  # câu treo ở dấu hai chấm bị đẩy lùi


def test_slide_co_mau_canh_bao_khi_de_cuong_khong_co_n(tmp_path: Path) -> None:
    goc = _dung(tmp_path / "e", n_g3=777)
    sl = _slide(goc, "co_mau")
    assert any("777" in c and "không có trong mục cỡ mẫu" in c for c in sl.canh_bao)


def test_slide_muc_vang_ghi_ro_khong_tu_viet(tmp_path: Path) -> None:
    dc = DE_CUONG.replace("## 4.11. Đạo đức trong nghiên cứu\n\nĐề tài chỉ tiến hành sau khi Hội đồng phê duyệt.\n", "")
    goc = _dung(tmp_path / "e", de_cuong=dc)
    sl = _slide(goc, "dao_duc", dc)
    assert _van(sl) == [] and any("không tìm thấy mục" in c for c in sl.canh_bao)


def test_slide_khoang_trong_uu_tien_va_bang_sai_so(goc: Path) -> None:
    v = _van(_slide(goc, "khoang_trong"))
    assert any(x.startswith("**Khoảng trống.**") for x in v) and any(x.startswith("**Đóng góp") for x in v)
    assert not any(x.startswith("Giới hạn") for x in v)
    ss = _slide(goc, "sai_so")
    hang = ss.khoi[0][1]
    assert [c.van for c in hang] == ["Sai lệch chọn mẫu", "Sai lệch nhớ lại"]
    assert hang[0].phu == "Chọn mẫu hệ thống có điểm bắt đầu ngẫu nhiên"


def test_chon_cau_day_lui_cau_treo_va_nhan_dam_nhung_khong_bo() -> None:
    ds = [G.Cau("Dẫn vào bảng:", 1, dau_doan=True), G.Cau("**Quần thể phân tích.**", 2, dau_doan=True),
          G.Cau("Câu một.", 3, dau_doan=True), G.Cau("Câu hai.", 4, dau_doan=True)]
    assert [c.van for c in G.chon_cau(ds, "dau", 2)] == ["Câu một.", "Câu hai."]
    assert [c.van for c in G.chon_cau(ds, "dau", 3)] == ["Dẫn vào bảng:", "Câu một.", "Câu hai."]  # thiếu thì vẫn lấy


def test_slide_dat_van_de_va_cong_cu_dung_muc(goc: Path) -> None:
    dvd = _van(_slide(goc, "dat_van_de"))
    assert dvd[:2] == ["Câu mở đoạn một nêu bối cảnh của khoa mẫu.", "Câu mở đoạn hai nêu vấn đề chính [1]."]
    assert not any("Mục tiêu nằm trong đặt vấn đề" in x for x in dvd)
    bs = _van(_slide(goc, "bien_so"))
    assert "Công cụ thu thập là phiếu khảo sát tự điền." in bs
    assert not any("y văn" in x for x in bs)  # không khớp nhầm mục 3.2 của tổng quan


# ── Câu hỏi từ biên bản (Q1–Q3) ──────────────────────────────────────────────────────────────────────────────────────

def _nhom(goc: Path):
    return G.cau_hoi_bien_ban(goc / MA, DE_CUONG.splitlines(), DC)


def test_chi_lay_phan_doi_cua_ben_phan_bien_bo_luan_diem_nhuong(goc: Path) -> None:
    nhom, dem = _nhom(goc)
    assert dem == {"tranh_bien": 4, "xu_ly": 1, "hong": 1}
    moi = next(n for n in nhom if n.id.endswith("aaaa0002"))
    van = [c.chat_van for c in moi.cau]
    assert van == ["MT2 chưa có câu estimand-like.", P_BAC, P_NOI_BO]
    assert moi.so_nhuong == 1
    assert not any("Luận điểm đề xuất" in c.chat_van for n in nhom for c in n.cau)


def test_phan_doi_noi_bo_tach_sang_nhom_n(goc: Path) -> None:
    md = _goi(goc)["cau_hoi_md"]
    phan_a, phan_n = md.split("## N. ")[0], md.split("## N. ")[1]
    assert P_NOI_BO in phan_n and P_NOI_BO not in phan_a
    assert "g0_quality_gate.py" in phan_n and "g0_quality_gate.py" not in phan_a
    assert P_BAC in phan_a
    nhom, _ = _nhom(goc)
    assert G.la_noi_bo(P_NOI_BO) and not G.la_noi_bo(P_BAC)
    assert "Sửa run_g1_auto.py" not in phan_a  # việc sửa nội bộ không chép vào phần chung
    assert "1 việc sửa khác thiên về quy trình nội bộ" in phan_a


def test_sua_ket_luan_kem_phan_da_sua_da_xac_minh(goc: Path) -> None:
    nhom, _ = _nhom(goc)
    moi = next(n for n in nhom if n.id.endswith("aaaa0002"))
    dong_sua = next(i for i, d in enumerate(DE_CUONG.splitlines(), 1) if MAU_SUA in d)
    xm = [g for g in moi.chung if g.nhan == f"Đề cương hiện hành, dòng {dong_sua}:"]
    assert len(xm) == 1  # hai mẫu rơi vào cùng một câu ⇒ in MỘT lần
    assert MAU_SUA in xm[0].trich and "Phân tích bằng phần mềm R." not in xm[0].trich  # đúng câu chứa mẫu
    assert any(g.canh_bao and "chuỗi không còn trong đề cương" in g.nhan for g in moi.chung)
    assert any(g.trich == "câu sai đã gỡ" and "không còn trong đề cương hiện hành" in g.nhan for g in moi.chung)
    assert any("G1_A2_PROTOCOL_DESIGN_x.md" in g.nhan and "không thuộc đề cương nộp" in g.nhan for g in moi.chung)
    assert not any("Việc của đánh giá chéo" in g.trich for g in moi.chung)  # chỉ việc sửa của trọng tài


def test_sua_ket_luan_chua_co_bien_ban_xu_ly_thi_canh_bao(goc: Path) -> None:
    nhom, _ = _nhom(goc)
    nb = next(n for n in nhom if n.id.endswith("aaaa0004"))
    assert any(g.canh_bao and "Chưa có biên bản xử lý" in g.nhan for g in nb.chung)


def test_bac_kem_lap_luan_duoc_giu_chap_nhan_tro_phan_chung(goc: Path) -> None:
    nhom, _ = _nhom(goc)
    moi = next(n for n in nhom if n.id.endswith("aaaa0002"))
    bac = next(c for c in moi.cau if c.chat_van == P_BAC)
    assert any(g.trich == "Quần thể đã định nghĩa đủ." for g in bac.goi_y)
    assert any(g.trich == L_GIU for g in bac.goi_y)
    nhan = next(c for c in moi.cau if c.chat_van.startswith("MT2"))
    assert not any(g.trich == L_GIU or "Luận điểm đề xuất L1" in g.trich for g in nhan.goi_y)


def test_chuyen_bac_si_kem_quyet_dinh_va_canh_bao_van_de_chua_quyet(goc: Path) -> None:
    nhom, _ = _nhom(goc)
    ch = next(n for n in nhom if n.id.endswith("aaaa0003"))
    assert any(g.trich == "Giữ rút gọn, ghi giới hạn." for g in ch.chung)
    so_canh_bao = [g for g in ch.chung if g.canh_bao and "Chưa có quyết định ghi sổ" in g.nhan]
    assert len(so_canh_bao) == 1


def test_luot_cu_vao_muc_rieng(goc: Path) -> None:
    nhom, _ = _nhom(goc)
    cu = next(n for n in nhom if n.id.endswith("aaaa0001"))
    moi = next(n for n in nhom if n.id.endswith("aaaa0002"))
    assert cu.cu_hon == moi.id and moi.cu_hon is None and cu.chung == []
    md = _goi(goc)["cau_hoi_md"]
    assert md.index("Phản đối ở lượt cũ về estimand.") > md.index("### Phản đối ở các lượt tranh biện cũ hơn")


def test_chua_co_bien_ban_ghi_ro_va_dung_de_cuong(tmp_path: Path) -> None:
    goc = _dung(tmp_path / "e", bien_ban=False)
    goi = _goi(goc)
    md = goi["cau_hoi_md"]
    assert "CHƯA CÓ BIÊN BẢN HỘI ĐỒNG CỔNG" in md and "## C. Từ chính đề cương" in md
    assert "Kết quả chỉ áp dụng cho người bệnh đã hoàn thành lượt khám." in md
    assert goi["tom_tat"]["cau_hoi"]["C_de_cuong"] >= 1
    assert "## C. " not in _goi(_dung(tmp_path / "f"))["cau_hoi_md"]  # có biên bản ⇒ không trộn nhóm C


# ── Báo cáo phản biện (hai khuôn) ────────────────────────────────────────────────────────────────────────────────────

def test_bao_cao_doc_ca_hai_khuon_va_cau_hoi_tac_gia(goc: Path) -> None:
    bc = G.tim_bao_cao(goc / MA, MA)
    assert bc is not None and bc.tep.name.endswith(f"20261101_{MA}.md")
    assert bc.tep_khac == [f"PHAN_BIEN_DE_CUONG_NOP_20261001_{MA}.md"]
    ph = {p.ma: p for p in bc.phat_hien}
    assert set(ph) == {"Đ1", "O1", "G1", "1"}  # bảng tổng hợp và bảng STROBE không phải phát hiện
    assert ph["Đ1"].muc_do == "🔴" and ph["O1"].muc_do == "🟠" and ph["G1"].muc_do == "🟢" and ph["1"].muc_do == "🔴"
    assert ph["Đ1"].van_de == "con số 15,3% không dẫn nguồn. 1. Ý phụ thứ nhất của vấn đề."
    assert ph["Đ1"].de_xuat == "thêm trích dẫn cho con số." and "15,32%" not in ph["Đ1"].van_de
    assert ph["O1"].vi_tri == "Phụ lục B." and ph["G1"].van_de == "Cân nhắc trích thêm hai trường."
    assert [c for c, _d in bc.cau_hoi] == ["Xét nghiệm nội trú có được tính (mục 4.4.1)?", "Ai là thống kê viên?",
                                           "Khoa có làm thứ Bảy không?"]
    cau = G.cau_hoi_bao_cao(bc, G.doc_muc(DE_CUONG.splitlines()), bc.sha_doc or "")
    d1 = next(c for c in cau if c.tieu_de.startswith("🔴 Đ1."))
    assert any("trùng bản phản biện đã đọc" in g.nhan for g in d1.goi_y)
    assert any("mục 4.10 «Xử lý và phân tích số liệu»" in g.nhan for g in d1.goi_y)
    assert any(c.tieu_de == "🟢 phát hiện «G1» của báo cáo" for c in cau)


# ── Bất biến «không bịa» + PII ───────────────────────────────────────────────────────────────────────────────────────

def _kt(s: str) -> str:
    """Gộp khoảng trắng: trường nhiều dòng của báo cáo được nối một dòng — chỉ khoảng trắng đổi, chữ giữ nguyên."""
    return " ".join(s.split())


def test_moi_doan_nguyen_van_deu_co_trong_nguon(goc: Path) -> None:
    nguon = _nguon(goc)
    nguon_kt = _kt(nguon)
    dong = DE_CUONG.splitlines()
    nhom, _ = _nhom(goc)
    bc = G.tim_bao_cao(goc / MA, MA)
    cau = [c for n in nhom for c in n.cau] + G.cau_hoi_bao_cao(bc, G.doc_muc(dong), "") + G.cau_hoi_de_cuong(dong)
    goi_y = [g for c in cau for g in c.goi_y] + [g for n in nhom for g in n.chung]
    assert cau and goi_y
    for c in cau:
        assert _kt(c.chat_van) in nguon_kt, c.chat_van
        if c.nhom == "A":  # biên bản: nguyên văn tuyệt đối, kể cả khoảng trắng
            assert c.chat_van in nguon
    for g in goi_y:
        assert g.trich == "" or _kt(g.trich) in nguon_kt, g.trich
    md = _goi(goc)["cau_hoi_md"]
    for c in cau[:len([c for n in nhom for c in n.cau])]:
        assert f"«{c.chat_van}»" in md


def test_pii_trong_dau_ra_thi_khong_ghi_ma_3(tmp_path: Path) -> None:
    goc = _dung(tmp_path / "e", them_pii=" Liên hệ lien.he@vi-du.vn để hỏi.")
    truoc = _anh_chup(goc / MA)
    assert G.main(["--study", MA, "--exports-root", str(goc), "--ghi", "--khong-word"]) == 3
    assert _anh_chup(goc / MA) == truoc


def test_quet_pii_khong_nuot_so_cccd_va_bo_dung_ma_bam(goc: Path) -> None:
    assert G.quet_pii("Số định danh 000000000000 trong câu.")  # bimat-mien: số GIẢ toàn 0 để kiểm bộ quét PII
    assert G.quet_pii("doi:10.1000/111111111111 và PMID 41201884") == []
    assert G.quet_pii("mã băm 111111111111 tự in", ("111111111111",)) == []  # bimat-mien: số GIẢ kiểm bỏ qua mã băm


# ── Xuất Word qua công cụ của repo gốc ───────────────────────────────────────────────────────────────────────────────

def test_word_goi_cong_cu_goc_dung_che_do_de_cuong(goc: Path, tmp_path: Path, monkeypatch) -> None:
    gia = tmp_path / "md_sang_docx_times.py"
    so = tmp_path / "goi.json"
    gia.write_text("import json, sys\nfrom pathlib import Path\n"
                   f"p = Path({str(so)!r})\nds = json.loads(p.read_text()) if p.exists() else []\n"
                   "ds.append(sys.argv[1:])\np.write_text(json.dumps(ds))\n"
                   "Path(sys.argv[1]).with_suffix('.docx').write_bytes(b'PK')\n", encoding="utf-8", newline="\n")
    monkeypatch.setattr(G, "tim_cong_cu_word", lambda: gia)
    assert G.main(["--study", MA, "--exports-root", str(goc), "--ghi"]) == 0
    goi = json.loads(so.read_text())
    assert len(goi) == 2 and all(g[1:] == ["--co-chu", "13", "--trang-de-cuong"] for g in goi)
    assert (goc / MA / f"GOI_BAO_VE_DAN_SLIDE_{MA}.docx").is_file()


def test_word_thieu_cong_cu_goc_ma_1_van_giu_md(goc: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(G, "tim_cong_cu_word", lambda: None)
    assert G.main(["--study", MA, "--exports-root", str(goc), "--ghi"]) == 1
    assert (goc / MA / f"GOI_BAO_VE_CAU_HOI_{MA}.md").is_file()
    assert "không tìm thấy tools/md_sang_docx_times.py" in capsys.readouterr().out
