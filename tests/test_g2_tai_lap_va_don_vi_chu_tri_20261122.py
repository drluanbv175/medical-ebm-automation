"""Hồ sơ G2 tái lập được khi sinh lại · đơn vị chủ trì tách khỏi đơn vị công tác của chủ nhiệm (22/11/2026).

1. `administrative.pi_unit` từng mang hai nghĩa: đơn vị công tác của chủ nhiệm (hồ sơ G2, bảng cán bộ) và Khoa chủ trì
   (khối ký bìa phụ, K19, bìa G10). Ca BTM: chủ nhiệm công tác tại Khoa C1a thuộc Trung tâm C1, đề tài do Khoa Khám bệnh
   chủ trì (trực thuộc bệnh viện) ⇒ điền `pi_unit` làm K19 đòi «GIÁM ĐỐC TRUNG TÂM». Nay `don_vi_chu_tri` thắng.
2. Nguyên tắc «tính tái lập»: `run_g2_auto --regenerate` ra trạng thái khác bản đang nộp vì nhiều ô điền tay không có
   khoá nguồn. Nay văn bản đã soạn/dữ kiện nguyên văn nằm ở study_meta (`tools/ho_so_g2_da_soan.py`) và đi THẲNG vào
   hồ sơ, không qua bộ chuẩn hoá văn phong (bộ này đổi «—» thành dấu phẩy/chấm).

Fixture tự soạn, ngoại tuyến, không dữ liệu thật."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _p in (ROOT, ROOT / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import ho_so_g2_da_soan as HSG  # noqa: E402
import khuon_de_cuong_bvqy175 as K  # noqa: E402
import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: E402
import run_g10_assemble as A  # noqa: E402
import vn_prose_style as VN  # noqa: E402
import xung_dot_loi_ich as XDLI  # noqa: E402
from run_g2_auto import RISK_PROFILES, generate_g2_full_package, thu_gon_icf_khi_xin_mien  # noqa: E402

from tests.test_khoi_ky_theo_don_vi_20261122 import DV_TRUC_THUOC, DV_TRUNG_TAM, _cu  # noqa: E402

DV_CHU_TRI = DV_TRUC_THUOC  # Khoa chủ trì trực thuộc bệnh viện
DV_CONG_TAC = DV_TRUNG_TAM  # chủ nhiệm công tác ở Khoa thuộc Trung tâm


# ── 1. đơn vị chủ trì ────────────────────────────────────────────────────────────────────────────────────────────────

def test_don_vi_ho_so_uu_tien_don_vi_chu_tri():
    assert K.don_vi_ho_so({"administrative": {"pi_unit": DV_CONG_TAC, "don_vi_chu_tri": DV_CHU_TRI}}) == DV_CHU_TRI
    assert K.don_vi_ho_so({"administrative": {"pi_unit": DV_CONG_TAC}}) == DV_CONG_TAC  # vắng ⇒ như cũ
    assert K.don_vi_ho_so({"administrative": {"pi_unit": DV_CONG_TAC, "don_vi_chu_tri": "[CẦN — đơn vị]"}}) == \
        DV_CONG_TAC


def test_k19_dung_don_vi_chu_tri_khong_dung_don_vi_cong_tac(tmp_path):
    ma = "de-tai-chu-tri-thu"
    d = tmp_path / ma
    d.mkdir()
    md = K.chuyen(_cu(DV_CHU_TRI), nam=2026).md  # bìa phụ hai khối ký (Khoa trực thuộc bệnh viện)
    (d / f"DE_CUONG_NOP_HOI_DONG_{ma}.md").write_text(md, encoding="utf-8", newline="\n")
    (d / "study_meta.json").write_text(json.dumps({"administrative": {"pi_unit": DV_CONG_TAC}}, ensure_ascii=False),
                                       encoding="utf-8", newline="\n")
    assert any("GIÁM ĐỐC TRUNG TÂM" in x for x in KDN.kiem(d, ma) if x.startswith("K19"))  # lỗi cũ của ca BTM
    (d / "study_meta.json").write_text(json.dumps({"administrative": {"pi_unit": DV_CONG_TAC,
                                                                      "don_vi_chu_tri": DV_CHU_TRI}},
                                                  ensure_ascii=False), encoding="utf-8", newline="\n")
    assert not [x for x in KDN.kiem(d, ma) if x.startswith("K19")]
    assert K.chay(ma, d, ghi=False)["doi"] is False  # khuôn bìa không đổi byte


def test_bia_g10_ghi_don_vi_chu_tri(tmp_path):
    meta = {"administrative": {"principal_investigator": "Bác sĩ Thử", "pi_unit": DV_CONG_TAC,
                               "don_vi_chu_tri": DV_CHU_TRI}, "document_date": "2026-11-22"}
    A.bo_sung_tu_nguon_da_chot(meta, {}, tmp_path)
    assert meta["org_lines"] == ["Bệnh viện Mẫu 175", "Khoa Khám Thử C9"]


def test_g2_don_vi_cong_tac_o_don_va_khai_bao_don_vi_chu_tri_o_phieu_dong_y():
    meta = {"administrative": {"principal_investigator": "Bác sĩ Thử", "pi_unit": DV_CONG_TAC,
                               "don_vi_chu_tri": DV_CHU_TRI},
            "gate_params": {"G1": {"setting": "Khoa Khám Thử C9"}}}
    doc = _gen(meta=meta)
    assert f"Đơn vị: {DV_CONG_TAC}" in doc  # Tài liệu 1/8: đơn vị công tác của chủ nhiệm
    assert f"Nghiên cứu do {DV_CHU_TRI} thực hiện" in doc  # phiếu đồng ý: đơn vị chủ trì


# ── 2. tái lập: văn bản đã soạn đi thẳng vào hồ sơ ──────────────────────────────────────────────────────────────────

def _gen(design="cross_sectional", meta=None, quy_trinh=None, bao_ve=None, registry=None) -> str:
    return generate_g2_full_package(
        topic="Đề tài thử", study_name="THU", design_code=design, design_primary="Cắt ngang",
        reporting_std="STROBE", n_sr=0, n_rct=0, evidence_level="", registry=registry,
        risk=copy.deepcopy(RISK_PROFILES[design]), run_date="2026-11-22 08:00", meta=meta, quy_trinh=quy_trinh,
        bao_ve=bao_ve)


def _quy_trinh_main(meta, design="cross_sectional", registry=None) -> str:
    """Đúng chuỗi của main(): sinh (giữ mã) → thu gọn ICF → chuẩn hoá văn phong → chèn văn bản đã soạn."""
    bv = HSG.BaoVe()
    doc = _gen(design=design, meta=meta, bao_ve=bv, registry=registry)
    doc = thu_gon_icf_khi_xin_mien(doc, design, meta)
    return bv.chen(VN.clean_generated_prose(doc))


KHOI = {
    "tl1_dang_ky": "OSF Registries — đăng ký TRƯỚC người tham gia đầu tiên; mã cập nhật sau khi đăng ký",
    "tl2_van_de": " VẤN-ĐỀ — câu đã soạn",
    "tl2_bang_chung": " Bằng chứng — đã sàng lọc: 0 SR/MA\n Khảo sát — 12 nghiên cứu quan sát",
    "tl2_quy_trinh": " Quy trình: phát phiếu — tự điền",
    "tl2_bao_mat": " Bảo mật — dòng một\n   dòng hai thụt ba dấu cách",
    "tl3_bang_rui_ro": ("| # | Rủi ro | Xác suất | Mức độ | Biện pháp |\n|---|---|---|---|---|\n"
                        "| 1 | A — b | Thấp | Nhẹ | C — d |"),
    "tl6_loai_du_lieu": " ☑ Kết quả khảo sát — không dùng hồ sơ",
    "tl6_cong_cu": " ☑ Phiếu giấy (nặc danh — tự điền)",
    "tl6_khu_dinh_danh": " Phương pháp: GIẢ DANH HÓA — mã nghiên cứu",
    "tl6_chia_se_ghi_chu": " Lựa chọn của chủ nhiệm (03/10/2026): chia sẻ — theo yêu cầu",
    "tl6_cuoi_nghien_cuu": " ∎ Bảng đối chiếu — hủy trong 30 ngày",
    "tl7_du_lieu_thu_cap": "☐ [Dữ liệu thứ cấp]: Văn bản chấp thuận — Bệnh viện đồng ý",
    "tl9_khong_nop": "> Chủ nhiệm quyết — KHÔNG xin miễn phiếu đồng ý",
}

META_DA_SOAN = {
    "administrative": {"principal_investigator": "Bác sĩ Thử", "irb_name": "Hội đồng Y đức Bệnh viện Mẫu 175",
                       "sponsor": "Không có tài trợ bên ngoài — tự túc"},
    "gate_params": {"G1": {"objectives": ["MT1 (mô tả): xác định tỷ lệ — kết cục chính"]}, "G2": {
        "ngay_phien_ban": "2026-07-31", "tap_chi_du_kien": "Tạp chí Thử — 175",
        "loi_ich_truc_tiep": "Không có — chỉ hỏi ý kiến", "loi_ich_cong_dong": "Tỷ lệ — căn cứ cải tiến",
        "rui_ro_xac_nhan": "Chủ nhiệm đã rà và xác nhận bảng rủi ro theo đề cương (03/10/2026).",
        "so_ban_nop": "02", "ai": {"co_su_dung": True, "cong_cu_khac": "Không dùng công cụ AI nào khác",
                                   "nguoi_kiem_tra": "Bác sĩ Thử (chủ nhiệm đề tài)"},
        "tra_dang_ky_khac": "WHO ICTRP: đã tự tra — không trùng",
        "tl1_kem_theo_extra": ["Phụ lục B1 — phiếu pha phát triển"],
        "da_soan": dict(KHOI, khoi_go_sai="x"),
        "trds_md": {"4": " None — self-funded", "11": " Vietnam (VN) — Ho Chi Minh City",
                    "24": " Plan to share de-identified IPD: Yes — controlled access"},
    }},
    "data_governance": {"sharing_choice": "theo_yeu_cau", "breach_procedure": "theo qui định của đơn vị",
                        "breach_internal": "người giữ dữ liệu báo ngay — báo cáo nội bộ trong 24 giờ",
                        "breach_extra": ["Thông báo người tham gia bị ảnh hưởng ngay khi xác nhận"]},
}


def test_khoi_da_soan_vao_nguyen_van_sau_chuan_hoa():
    doc = _quy_trinh_main(copy.deepcopy(META_DA_SOAN))
    for ten, van in KHOI.items():
        assert van in doc, ten  # từng ký tự, kể cả «—» và thụt lề
    # dữ kiện ngữ nghĩa nguyên văn
    for x in ("Tạp chí mục tiêu: Tạp chí Thử — 175", "| Trực tiếp với NTG | Không có — chỉ hỏi ý kiến |",
              "| Cộng đồng/y tế | Tỷ lệ — căn cứ cải tiến |", "SỐ BẢN NỘP: 02", "· Không dùng công cụ AI nào khác",
              "Người kiểm tra đầu ra: Bác sĩ Thử (chủ nhiệm đề tài)",
              "không có API mở. WHO ICTRP: đã tự tra — không trùng",
              "☐ Phụ lục B1 — phiếu pha phát triển", "Nguồn tài trợ: Không có tài trợ bên ngoài — tự túc",
              "2.1 MT1 (mô tả): xác định tỷ lệ — kết cục chính", " None — self-funded",
              " Vietnam (VN) — Ho Chi Minh City", " Plan to share de-identified IPD: Yes — controlled access",
              "Ethics committee: Hội đồng Đạo đức Nghiên cứu Y sinh — Hội đồng Y đức Bệnh viện Mẫu 175",
              "Quy trình: theo qui định của đơn vị", "Phát hiện vi phạm → người giữ dữ liệu báo ngay — báo cáo nội bộ",
              "∎ Thông báo người tham gia bị ảnh hưởng ngay khi xác nhận", "cho Hội đồng Y đức khi phát sinh"):
        assert x in doc, x
    # chia sẻ đã quyết: đúng ô, không còn ô chờ chọn
    assert "☑ Chia sẻ theo yêu cầu hợp lý (DTA cần ký trước)" in doc and "[CẦN BÁC SĨ CHỌN VÀ BIỆN MINH]" not in doc
    # AI: «Có sử dụng» được đánh dấu theo khoá
    assert "☑ Có sử dụng:" in doc and "☐ Không sử dụng công cụ AI nào" in doc
    # ngày phiên bản thay ngày chạy ở các văn bản có ngày phiên bản
    assert "(DRAFT Phiên bản 1.0, 2026-07-31)" in doc or "(DRAFT Phiên bản 1.0 — 2026-07-31)" in doc
    assert "Ngày khai báo: 31/07/2026" in doc and "Ngày chuẩn bị: 2026-07-31" in doc
    # Tài liệu 9 ghi quyết định KHÔNG xin miễn — không in đơn xin miễn có ô xác nhận
    assert "## TÀI LIỆU 9. ĐỀ NGHỊ MIỄN ICF — KHÔNG NỘP" in doc and "YÊU CẦU MIỄN THỦ TỤC" not in doc
    assert "\x02" not in doc and "\x03" not in doc  # không sót mã giữ chỗ


def test_vang_khoa_thi_khuon_cu_va_o_cho_dien_giu_nguyen():
    doc = _quy_trinh_main({})
    for x in ("[CẦN BỔ SUNG tạp chí/hội nghị mục tiêu]", "[CẦN BÁC SĨ LIỆT KÊ CỤ THỂ theo đề tài]",
              "SỐ BẢN NỘP: [CẦN XÁC NHẬN", "[CẦN BÁC SĨ CHỌN VÀ BIỆN MINH]", "[CẦN BÁC SĨ TỰ TRA]",
              "Ethics committee: [CẦN mã/tên đơn vị"):
        assert x in doc, x
    assert "\x02" not in doc


def test_goi_truc_tiep_khong_truyen_bao_ve_tu_chen():
    doc = _gen(meta=copy.deepcopy(META_DA_SOAN))
    assert KHOI["tl6_cong_cu"] in doc and "\x02" not in doc


def test_ten_khoi_la_bi_bao_va_bo_qua():
    assert HSG.khoi_la(META_DA_SOAN) == ["khoi_go_sai"]
    assert "khoi_go_sai" not in HSG.khoi_da_soan(META_DA_SOAN)


def test_phieu_dong_y_da_soan_thay_tron_than_tai_lieu_4_5():
    m = copy.deepcopy(META_DA_SOAN)
    m["gate_params"]["G2"]["da_soan"] = {"tl4": "```\nPHIẾU ĐÃ SOẠN — bản Việt\n```",
                                         "tl5": "```\nCONSENT AS WRITTEN — English\n```"}
    doc = _quy_trinh_main(m)
    tl4 = doc[doc.index("## TÀI LIỆU 4"):doc.index("## TÀI LIỆU 5")]
    tl5 = doc[doc.index("## TÀI LIỆU 5"):doc.index("## TÀI LIỆU 6")]
    assert "PHIẾU ĐÃ SOẠN — bản Việt" in tl4 and "PHẦN THÔNG TIN CHO NGƯỜI THAM GIA" not in tl4
    assert "CONSENT AS WRITTEN — English" in tl5 and "[TO BE COMPLETED" not in tl5


def test_lap_luan_ba_dieu_kien_mien_dong_thuan():
    m = {"gate_params": {"G2": {"icf_waiver_requested": True, "mien_icf_lap_luan": {
        "i_khong_kha_thi": "Xin đồng ý làm mất tính đại diện — sai lệch chọn",
        "ii_gia_tri_xa_hoi": "Số liệu nền cho cải tiến", "iii_nguy_co_toi_thieu": "Không tiếp xúc người bệnh"}}}}
    doc = _quy_trinh_main(m)
    tl9 = " ".join(doc[doc.index("## TÀI LIỆU 9"):doc.index("ĐĂNG KÝ NGHIÊN CỨU", doc.index("## TÀI LIỆU 9"))].split())
    assert "[CẦN LẬP LUẬN]" not in tl9
    assert "— Lập luận: Xin đồng ý làm mất tính đại diện — sai lệch chọn" in tl9
    assert "— Lập luận: Không tiếp xúc người bệnh" in tl9


def test_ap_trds_chi_thay_truong_da_soan():
    van = "Trường 4  — Source:\n            [CẦN]\n\nTrường 5  — Sponsor:\n            [CẦN X]\n"
    bv = HSG.BaoVe()
    ra = bv.chen(HSG.ap_trds(van, {4: " None — tự túc"}, bv))
    assert "Trường 4  — Source:\n None — tự túc\n\nTrường 5" in ra and "[CẦN X]" in ra and "[CẦN]\n" not in ra


def test_bao_ve_giu_dau_gach_sinh_gop_khoang_trang():
    bv = HSG.BaoVe()
    van = f"A — b {bv.nguyen_van('X — y')} {bv.sinh('   P  —  q')}"
    ra = bv.chen(VN.clean_generated_prose(van))
    assert ra.endswith("X — y  P — q") or ra.endswith("X — y P — q")
    assert "A, b" in ra or "A. B" in ra  # phần khuôn vẫn qua chuẩn hoá như cũ


def test_ngay_phien_ban_va_ten_ngan_hoi_dong():
    assert HSG.ngay_phien_ban({"gate_params": {"G2": {"ngay_phien_ban": "2026-07-31"}}}, "2026-11-22 08:00") == \
        ("2026-07-31", "31/07/2026")
    assert HSG.ngay_phien_ban({}, "2026-11-22 08:00") == ("2026-11-22", "22/11/2026")
    assert HSG.ten_ngan_hoi_dong("Hội đồng Y đức Bệnh viện Quân y 175") == "Hội đồng Y đức"
    assert HSG.ten_ngan_hoi_dong("[TÊN ĐƠN VỊ — CẦN BỔ SUNG]") == "Hội đồng Đạo đức"
    assert HSG.ten_ngan_hoi_dong("Bệnh viện Quân y 175") == "Hội đồng Đạo đức"


def test_dung_lai_ket_qua_tra_dang_ky_da_luu():
    cp = {"clinicaltrials": {"registry": "ClinicalTrials.gov", "checked": True, "query": "q", "n_trials": 1,
                             "n_active": 0, "checked_at": "2026-11-20T21:04:22",
                             "samples": [{"nct_id": "NCT0000001", "title": "T", "status": "COMPLETED", "url": "u"}]}}
    reg = HSG.dang_ky_tu_checkpoint(cp)
    assert reg["checked"] and reg["checked_at"].startswith("2026-11-20") and reg["trials"][0]["status"] == "COMPLETED"
    assert HSG.dang_ky_tu_checkpoint({"clinicaltrials": {"checked": False}}) is None
    doc = _quy_trinh_main({}, registry=reg)
    assert "ĐÃ TRA THẬT ngày 2026-11-20" in doc and "NCT0000001" in doc


def test_chia_se_va_vi_pham_noi_bo():
    k = XDLI.doc({"data_governance": {"sharing_choice": "khong"}})
    assert XDLI.dong_chia_se(k).splitlines()[0] == "   ☑ Không chia sẻ"
    assert "[CẦN BÁC SĨ CHỌN" in XDLI.dong_chia_se(XDLI.doc({"data_governance": {"sharing_choice": "la"}}))
    v = XDLI.dong_vi_pham(XDLI.doc({}), "HẠN", "NỘI DUNG")
    assert "người phát hiện báo ngay cho chủ nhiệm đề tài" in v and "24 giờ" not in v


# ── đầu–cuối main(): sinh lại hai lần ra cùng hồ sơ; kết quả tra đăng ký đã lưu được dùng lại ─────────────────────────

def test_main_sinh_lai_tai_lap_va_dung_lai_tra_dang_ky(tmp_path):
    import subprocess  # noqa: PLC0415

    sys.path.insert(0, str(ROOT / "tests"))
    from _chuoi_da_chot import dung_g0_g1_da_chot  # noqa: PLC0415

    study = "PYTEST-G2-TAI-LAP-20261122"
    d = tmp_path / "exports" / study
    dung_g0_g1_da_chot(d, study, thiet_ke="cross_sectional")
    meta = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
    meta["gate_params"].setdefault("G2", {}).update({"so_ban_nop": "02 — bản giấy", "ngay_phien_ban": "2026-07-31",
                                      "da_soan": {"tl6_cong_cu": " ☑ Phiếu giấy (nặc danh — tự điền)"}})
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    (d / "G2_checkpoint.json").write_text(json.dumps({"clinicaltrials": {
        "registry": "ClinicalTrials.gov", "checked": True, "query": "q", "n_trials": 0, "n_active": 0,
        "checked_at": "2026-11-20T21:04:22", "samples": []}}), encoding="utf-8", newline="\n")

    def _chay() -> str:
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "run_g2_auto.py"), "--study", study,
                            "--design", "cross_sectional", "--skip-registry", "--regenerate",
                            "--repo-root", str(tmp_path)], cwd=ROOT, capture_output=True, text=True, timeout=240)
        assert r.returncode in (0, 2), r.stdout[-1500:] + r.stderr[-800:]
        return (d / f"G2_A3_ETHICS_PACKAGE_{study}.md").read_text(encoding="utf-8")

    lan1 = _chay()
    assert " ☑ Phiếu giấy (nặc danh — tự điền)" in lan1 and "SỐ BẢN NỘP: 02 — bản giấy" in lan1
    assert "ĐÃ TRA THẬT ngày 2026-11-20" in lan1 and "CHƯA TRA ĐƯỢC ClinicalTrials.gov" not in lan1
    lan2 = _chay()
    bo_gio = (lambda v: "\n".join(x for x in v.split("\n") if not x.startswith("> Tạo tự động:")))  # noqa: E731
    assert bo_gio(lan1) == bo_gio(lan2)  # tái lập: chỉ khác dòng giờ sinh
