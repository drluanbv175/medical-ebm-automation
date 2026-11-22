#!/usr/bin/env python3
"""Hồ sơ gửi Hội đồng Đạo đức SAU khi đề cương được chấp thuận: đề nghị thay đổi đề cương · báo cáo tiến độ · báo cáo
kết quả nghiên cứu (22/11/2026). Dùng qua lệnh con `sau-chap-thuan` của `tools/ho_so_hdd_bvqy175.py`.

Mẫu và căn cứ (đã tra 22/11/2026)
---------------------------------
- Thông tư 43/2024/TT-BYT (12/12/2024, hiệu lực 01/02/2025) chỉ kèm Phụ lục I–VI là giấy chứng nhận/thông báo do Hội
  đồng ban hành và văn bản thông báo thành lập Hội đồng — KHÔNG có mẫu do nghiên cứu viên nộp cho đề nghị thay đổi đề
  cương, báo cáo tiến độ hay báo cáo kết quả (Điều 17: Hội đồng tự ban hành hướng dẫn và quy cách biểu mẫu).
- Bộ mẫu Hội đồng Đạo đức BVQY175 (thư mục «Mau HDDD BV175») chỉ gồm hồ sơ ĐĂNG KÝ (tệp 1–8), không có mẫu sau chấp
  thuận.
- Vì vậy ba văn bản ở đây dựng theo NỘI DUNG Thông tư 43 yêu cầu: Điều 6 khoản 1 điểm a (hồ sơ đề nghị thay đổi đề
  cương; báo cáo kết quả nghiên cứu); Điều 18 khoản 2 điểm a–đ (nội dung thẩm định nghiên cứu đang triển khai: tuân thủ
  đề cương; bảo vệ quyền, sức khỏe, an toàn người tham gia; biến cố bất lợi; vi phạm đề cương và khắc phục; sửa đổi đề
  cương); Điều 18 khoản 3 điểm a–c (báo cáo kết quả: tuân thủ đề cương; toàn vẹn, chính xác, tin cậy của dữ liệu; tính
  khoa học của báo cáo); Phụ lục I mục 6 khoản 3–6 (trình thay đổi trước khi áp dụng trừ khi để loại trừ nguy cơ trực
  tiếp; báo cáo tiến độ hằng năm; báo cáo đột xuất; thông báo ngừng/kết thúc trước hạn kèm lý do).

Ô chưa điền dùng cùng ba loại của `ho_so_nguon_chung.py`: dữ kiện chỉ có khi triển khai (số quyết định chấp thuận, số
người đã tuyển, biến cố trong kỳ, kết quả…) là «dữ kiện cần nhập» có cấu trúc; chữ ký/ngày ký thuộc gói ký. Khi đề tài
đã có tạo phẩm G5/G6 (khoá dữ liệu, kết quả phân tích) thì đọc từ đó.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import ho_so_nguon_chung as HSC

TEN_JSON = "SAU_CHAP_THUAN_BVQY175.json"
LOAI = {
    "sua_doi": ("ĐƠN ĐỀ NGHỊ XEM XÉT THAY ĐỔI ĐỀ CƯƠNG NGHIÊN CỨU", "HDD_DE_NGHI_THAY_DOI_DE_CUONG"),
    "tien_do": ("BÁO CÁO TIẾN ĐỘ NGHIÊN CỨU", "HDD_BAO_CAO_TIEN_DO"),
    "ket_qua": ("BÁO CÁO KẾT QUẢ NGHIÊN CỨU", "HDD_BAO_CAO_KET_QUA"),
}
CAN_CU = {
    "sua_doi": "Thông tư 43/2024/TT-BYT, Điều 6 khoản 1 điểm a; Điều 18 khoản 2 điểm đ; Phụ lục I mục 6 khoản 3.",
    "tien_do": "Thông tư 43/2024/TT-BYT, Điều 18 khoản 2 điểm a–đ; Phụ lục I mục 6 khoản 4 và 5.",
    "ket_qua": "Thông tư 43/2024/TT-BYT, Điều 6 khoản 1 điểm a; Điều 18 khoản 3 điểm a–c; Phụ lục I mục 6 khoản 6.",
}
CHUAN_BAO_CAO = {"cross_sectional": "STROBE", "cohort": "STROBE", "case_control": "STROBE", "rct": "CONSORT 2025",
                 "diagnostic": "STARD 2015", "sr_ma": "PRISMA 2020", "prediction": "TRIPOD+AI",
                 "qualitative": "COREQ/SRQR"}


def _json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    except (OSError, ValueError):
        return {}


def _tien_do(n: HSC.NguonDeTai) -> list[dict]:
    """Các mốc tiến độ của đề cương nộp — cùng bộ tách VÀ cùng bước áp khối `m21_hang` với thuyết minh đề tài cơ sở,
    để thời gian từng mốc trong báo cáo gửi Hội đồng Đạo đức trùng thuyết minh (một bản sự thật)."""
    try:
        import ho_so_dtcs_bvqy175 as DTCS  # noqa: PLC0415 - nạp trễ, tránh vòng nhập

        dong, ds = DTCS.tach_muc(n.de_cuong)
        td, _ = DTCS.tien_do(dong, ds, "")
        tam = {"thuyet_minh": {"m21_tien_do": td}}
        DTCS.ap_khoi_dtcs(tam, n, {}, [], set())
        td = tam["thuyet_minh"]["m21_tien_do"]
        return [{"noi_dung": h["noi_dung"], "thoi_gian": h["thoi_gian"]} for h in td if HSC.co(h.get("noi_dung"))]
    except Exception:  # noqa: BLE001 - không tách được ⇒ để dữ kiện cần nhập
        return []


def trich(exports_root: Path, study: str, so: dict | None = None) -> dict:
    """Dữ kiện ba văn bản sau chấp thuận — từ nguồn chung + tạo phẩm G5/G6 khi có; còn lại là dữ kiện cần nhập."""
    n = HSC.NguonDeTai(exports_root, study, so)
    g2 = n.gp("G2")
    qd = HSC.co(g2.get("qd_chap_thuan_so"))
    chung = {
        "ten_de_tai": n.ten_de_tai or "[CẦN BỔ SUNG]",
        "ma_so": HSC.can_nhap("mã số đề tài do Phòng Khoa học Quân sự cấp"),
        "chu_nhiem": n.chu_nhiem or "[CẦN BỔ SUNG]",
        "don_vi_chu_tri": n.don_vi_chu_tri or "[CẦN BỔ SUNG]",
        "kinh_gui": f"Chủ tịch {n.hoi_dong}" if n.hoi_dong else "Chủ tịch Hội đồng Đạo đức trong nghiên cứu y sinh học",
        "quyet_dinh_chap_thuan": qd or HSC.can_nhap("số và ngày quyết định chấp thuận đề cương của Hội đồng — có"
                                                     " sau khi Hội đồng chấp thuận"),
        "phien_ban_de_cuong": HSC.co(n.gp("G1").get("protocol_version")) or HSC.co(g2.get("protocol_version")),
        "thoi_gian": f"Từ {n.thoi_gian[0]} đến {n.thoi_gian[1]}" if n.thoi_gian else "[CẦN BỔ SUNG]",
        "co_mau": HSC.so_viet(n.co_mau) if n.co_mau else "[CẦN BỔ SUNG]",
    }
    sua = g2.get("sua_doi_de_cuong") if isinstance(g2.get("sua_doi_de_cuong"), list) else []
    sua_doi = {
        "thay_doi": [{k: HSC.co(x.get(k)) or HSC.can_nhap(f"{nhan} của thay đổi")
                      for k, nhan in (("muc", "mục"), ("noi_dung_cu", "nội dung cũ"), ("noi_dung_moi", "nội dung mới"),
                                      ("ly_do", "lý do"))} for x in sua if isinstance(x, dict)]
                     or [{"muc": HSC.can_nhap("mục đề cương thay đổi"),
                          "noi_dung_cu": HSC.can_nhap("nội dung đã duyệt"),
                          "noi_dung_moi": HSC.can_nhap("nội dung đề nghị"), "ly_do": HSC.can_nhap("lý do thay đổi")}],
        "anh_huong": HSC.can_nhap("ảnh hưởng của thay đổi tới nguy cơ, lợi ích và bản thông tin cho người tham gia"),
        "tai_lieu_kem": ["Đề cương sửa đổi (đánh dấu các thay đổi so với bản đã chấp thuận).",
                         "Bản thông tin và phiếu đồng ý sửa đổi (nếu thay đổi ảnh hưởng người tham gia)."],
        "cam_ket": ("Thay đổi chỉ được áp dụng sau khi Hội đồng chấp thuận, trừ trường hợp phải thay đổi ngay để loại"
                    " trừ nguy cơ trực tiếp cho người tham gia; khi đó nhóm nghiên cứu báo cáo Hội đồng ngay sau khi"
                    " áp dụng."),
    }
    # Ngày khoá dữ liệu (G5) đọc từ study_meta; nhãn trạng thái máy của checkpoint G5 («PENDING …», «LOCKED_…»)
    # KHÔNG đưa vào văn bản nộp.
    khoa = n.meta.get("data_lock_date")
    du_lieu_khoa = (f"Cơ sở dữ liệu đã khoá ngày {khoa}." if HSC.co(khoa) else
                    HSC.can_nhap("ngày khoá cơ sở dữ liệu và biên bản khoá — có khi khoá dữ liệu"))
    khdl = n.ke_hoach_du_lieu
    quy_trinh_dl = [f"{k}: {v}" for k, v in khdl.items() if HSC.co(v)]
    g6 = _json(n.thu_muc / "G6_checkpoint.json")
    ket_qua_g6 = HSC.co(g6.get("tom_tat_ket_qua") or g6.get("summary"))
    coi = n.coi
    giam_sat = HSC.co((g2.get("coi") or {}).get("monitor"))
    tien_do = {
        "ky_bao_cao": HSC.can_nhap("kỳ báo cáo (từ ngày … đến ngày …, tính từ ngày chấp thuận)"),
        "ke_hoach": _tien_do(n),
        "thuc_hien": HSC.can_nhap("tình trạng thực hiện từng mốc trong kỳ (đã xong / đang làm / chưa đến hạn)"),
        "tuyen_chon": {"ke_hoach": chung["co_mau"],
                       "da_tuyen": HSC.can_nhap("số người đã mời, đồng ý, từ chối và rút lui trong kỳ")},
        "a_tuan_thu": HSC.can_nhap("việc tuân thủ đề cương đã chấp thuận trong kỳ"),
        "b_bao_ve": HSC.can_nhap("biện pháp bảo vệ quyền, sức khỏe, an toàn người tham gia đã thực hiện trong kỳ"),
        "c_bien_co": HSC.can_nhap("biến cố bất lợi, biến cố bất lợi nghiêm trọng ghi nhận và xử trí trong kỳ (ghi"
                                  " «Không có» nếu không có)"),
        "d_vi_pham": HSC.can_nhap("vi phạm đề cương trong kỳ và việc khắc phục, phòng ngừa (ghi «Không có» nếu"
                                  " không có)"),
        "dd_sua_doi": (f"{len(sua)} thay đổi đề cương đã trình Hội đồng (xem đơn đề nghị thay đổi đề cương)." if sua
                       else HSC.can_nhap("thay đổi đề cương trong kỳ (ghi «Không có» nếu không có)")),
        "du_lieu": du_lieu_khoa if HSC.co(khoa) else HSC.can_nhap("tình trạng thu thập và quản lý dữ liệu trong"
                                                                   " kỳ"),
        "giam_sat_xung_dot": ([giam_sat, HSC.goi_ky("biên bản giám sát của người giám sát độc lập trong kỳ (ký) —"
                                                    " nộp kèm báo cáo tiến độ")] if giam_sat else []),
    }
    ket_qua = {
        "tom_tat_thuc_hien": HSC.can_nhap("tóm tắt quá trình thực hiện: thời gian thực tế, số người tham gia, tỷ lệ"
                                          " đáp ứng"),
        "a_tuan_thu": HSC.can_nhap("tuân thủ đề cương trong toàn bộ quá trình triển khai, các thay đổi đã được chấp"
                                   " thuận"),
        "b_du_lieu": [du_lieu_khoa] + quy_trinh_dl,
        "c_bao_cao": [f"Báo cáo theo hướng dẫn {CHUAN_BAO_CAO.get(n.thiet_ke_ma, 'của thiết kế')} cho thiết kế"
                      f" {n.thiet_ke.lower() if n.thiet_ke else 'đã chốt'}; phân tích theo kế hoạch phân tích thống kê"
                      " đã khoá trước khi xem dữ liệu.",
                      ket_qua_g6 or HSC.can_nhap("kết quả chính theo từng mục tiêu — có sau khi phân tích dữ liệu đã"
                                                 " khoá")],
        "xung_dot": (coi.get("tom_tat", "").rstrip(".") + "." if coi.get("tom_tat") else ""),
        "ket_thuc_som": HSC.can_nhap("ngừng hoặc kết thúc trước thời hạn dự kiến và lý do (ghi «Không» nếu kết"
                                     " thúc đúng kế hoạch)"),
    }
    ky = {k: HSC.goi_ky(f"chữ ký, họ tên và ngày ký của chủ nhiệm đề tài — {LOAI[k][0].lower()}") for k in LOAI}
    return {"phien_ban_schema": "1.0", "meta": {"study": study, "ngay_trich": datetime.now(timezone.utc).strftime(
        "%Y-%m-%d"), "dau_nguon": n.dau_nguon()}, "chung": chung, "sua_doi": sua_doi, "tien_do": tien_do,
        "ket_qua": ket_qua, "ky": ky, "can_cu": CAN_CU}


def _docx_moi():
    import docx  # noqa: PLC0415
    from docx.shared import Pt  # noqa: PLC0415

    tai_lieu = docx.Document()
    st = tai_lieu.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(13)
    return tai_lieu


def _dong(tai_lieu, text: str, bold: bool = False, italic: bool = False, canh: int | None = None):
    p = tai_lieu.add_paragraph()
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    if canh is not None:
        p.alignment = canh
    return p


def dung(d: dict, loai: str, out: Path) -> Path:
    """Dựng MỘT văn bản (`sua_doi` | `tien_do` | `ket_qua`)."""
    tai_lieu = _docx_moi()
    c = d["chung"]
    for t in ("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", "Độc lập – Tự do – Hạnh phúc"):
        _dong(tai_lieu, t, bold=True, canh=1)
    _dong(tai_lieu, LOAI[loai][0], bold=True, canh=1)
    _dong(tai_lieu, f"Kính gửi: {c['kinh_gui']}")
    for nhan, k in (("Tên đề tài", "ten_de_tai"), ("Mã số", "ma_so"), ("Chủ nhiệm đề tài", "chu_nhiem"),
                    ("Đơn vị chủ trì", "don_vi_chu_tri"), ("Quyết định chấp thuận đề cương", "quyet_dinh_chap_thuan"),
                    ("Phiên bản đề cương đã chấp thuận", "phien_ban_de_cuong"), ("Thời gian thực hiện", "thoi_gian")):
        if HSC.co(c.get(k)) or HSC.mo_ta_dau(str(c.get(k))):
            _dong(tai_lieu, f"{nhan}: {c[k]}")
    _dong(tai_lieu, f"Căn cứ: {d['can_cu'][loai]}", italic=True)
    if loai == "sua_doi":
        s = d["sua_doi"]
        _dong(tai_lieu, "1. Nội dung đề nghị thay đổi", bold=True)
        bang = tai_lieu.add_table(rows=1, cols=4)
        bang.style = "Table Grid"
        for o, t in zip(bang.rows[0].cells, ("Mục đề cương", "Nội dung đã chấp thuận", "Nội dung đề nghị", "Lý do")):
            o.text = t
        for x in s["thay_doi"]:
            hang = bang.add_row().cells
            for o, k in zip(hang, ("muc", "noi_dung_cu", "noi_dung_moi", "ly_do")):
                o.text = str(x.get(k, ""))
        _dong(tai_lieu, "2. Ảnh hưởng tới người tham gia", bold=True)
        _dong(tai_lieu, s["anh_huong"])
        _dong(tai_lieu, "3. Tài liệu kèm theo", bold=True)
        for t in s["tai_lieu_kem"]:
            _dong(tai_lieu, f"– {t}")
        _dong(tai_lieu, "4. Cam kết", bold=True)
        _dong(tai_lieu, s["cam_ket"])
    elif loai == "tien_do":
        t = d["tien_do"]
        _dong(tai_lieu, f"Kỳ báo cáo: {t['ky_bao_cao']}")
        _dong(tai_lieu, "1. Tiến độ so với kế hoạch đã chấp thuận", bold=True)
        for h in t["ke_hoach"]:
            _dong(tai_lieu, f"– {h['noi_dung'].rstrip('.')}: {h['thoi_gian'].rstrip('.')}.")
        _dong(tai_lieu, f"Tình trạng thực hiện: {t['thuc_hien']}")
        _dong(tai_lieu, f"2. Tuyển chọn người tham gia: cỡ mẫu theo đề cương {t['tuyen_chon']['ke_hoach']}; trong kỳ:"
                        f" {t['tuyen_chon']['da_tuyen']}", bold=False)
        for so, (nhan, k) in enumerate((("Tuân thủ đề cương đã chấp thuận", "a_tuan_thu"),
                                        ("Bảo vệ quyền, sức khỏe, an toàn người tham gia", "b_bao_ve"),
                                        ("Biến cố bất lợi", "c_bien_co"),
                                        ("Vi phạm đề cương và khắc phục, phòng ngừa", "d_vi_pham"),
                                        ("Sửa đổi, bổ sung đề cương", "dd_sua_doi"),
                                        ("Thu thập và quản lý dữ liệu", "du_lieu")), 3):
            _dong(tai_lieu, f"{so}. {nhan}", bold=True)
            _dong(tai_lieu, str(t[k]))
        if t.get("giam_sat_xung_dot"):
            _dong(tai_lieu, "9. Giám sát kế hoạch quản lý xung đột lợi ích", bold=True)
            for x in t["giam_sat_xung_dot"]:
                _dong(tai_lieu, x)
    else:
        k = d["ket_qua"]
        _dong(tai_lieu, "1. Tóm tắt quá trình thực hiện", bold=True)
        _dong(tai_lieu, k["tom_tat_thuc_hien"])
        _dong(tai_lieu, "2. Tuân thủ đề cương trong quá trình triển khai", bold=True)
        _dong(tai_lieu, k["a_tuan_thu"])
        _dong(tai_lieu, "3. Tính toàn vẹn, chính xác, tin cậy của dữ liệu", bold=True)
        for x in k["b_du_lieu"]:
            _dong(tai_lieu, f"– {x}")
        _dong(tai_lieu, "4. Tính khoa học, chính xác của báo cáo kết quả", bold=True)
        for x in k["c_bao_cao"]:
            _dong(tai_lieu, f"– {x}")
        if k.get("xung_dot"):
            _dong(tai_lieu, "5. Xung đột lợi ích", bold=True)
            _dong(tai_lieu, k["xung_dot"])
        _dong(tai_lieu, "6. Ngừng hoặc kết thúc trước thời hạn", bold=True)
        _dong(tai_lieu, k["ket_thuc_som"])
    _dong(tai_lieu, "Chủ nhiệm đề tài", bold=True, canh=2)
    _dong(tai_lieu, "(Ký và ghi rõ họ tên)", italic=True, canh=2)
    _dong(tai_lieu, d["ky"][loai], canh=2)
    out.parent.mkdir(parents=True, exist_ok=True)
    tai_lieu.save(str(out))
    return out


def ten_tep(loai: str, study: str) -> str:
    return f"{LOAI[loai][1]}_{study}.docx"


def chay(exports_root: Path, study: str, cac_loai: list[str], ghi: bool) -> tuple[int, list[str]]:
    """(mã thoát, dòng báo cáo). Mã 0 khi (a) = 0 trên các văn bản đã chọn."""
    so = HSC.doc_so()
    d = trich(exports_root, study, so)
    ba = HSC.dem_ba_loai({k: d[k] for k in ("chung", "ky", *cac_loai)}, HSC.ham_so_co(so))
    dong = [f"Hồ sơ sau chấp thuận — {study}: {', '.join(LOAI[k][0].lower() for k in cac_loai)}",
            f"Ô chưa điền: (a) suy được từ nguồn đã chốt {len(ba['a'])} · (b) gói ký {len(ba['b'])} · (c) dữ kiện cần"
            f" nhập {len(ba['c'])}",
            "Mẫu: Thông tư 43/2024/TT-BYT và bộ mẫu BVQY175 không có mẫu nghiên cứu viên nộp sau chấp thuận — văn bản"
            " dựng theo nội dung Điều 6 khoản 1 điểm a, Điều 18 khoản 2–3, Phụ lục I mục 6."]
    dong += [f"  (a) {p}: {v[:100]}" for p, v in ba["a"]]
    if not ghi:
        dong.append("(chạy khô — thêm --ghi để dựng Word)")
        return (1 if ba["a"] else 0), dong
    ra = exports_root / study / "ho_so_hdd" / "sau_chap_thuan"
    ra.mkdir(parents=True, exist_ok=True)
    (ra / TEN_JSON).write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    can_nhap: dict[str, list[str]] = {}
    goi_ky: list[str] = []
    loi_vet: list[str] = []
    for k in cac_loai:
        p = dung(d, k, ra / ten_tep(k, study))
        kq = HSC.hoan_thien_docx(p, so)
        for x in kq["can_nhap"]:
            can_nhap.setdefault(x, []).append(p.name)
        goi_ky += [x for x in kq["goi_ky"] if x not in goi_ky]
        dong.append(f"  - {p.name}")
        vet = dau_vet_may(p)
        if vet:
            loi_vet.append(f"{p.name}: {'; '.join(vet[:6])}")
    dm = [f"# Hồ sơ gửi Hội đồng Đạo đức sau chấp thuận — {study}", "",
          f"Đề tài: {d['chung']['ten_de_tai']}", "", "## Văn bản", ""]
    dm += [f"- {LOAI[k][0].capitalize()}: `{ten_tep(k, study)}` — căn cứ {CAN_CU[k]}" for k in cac_loai]
    dm += ["", "## Gói ký", ""] + [f"{i}. {x[0].upper() + x[1:]}." for i, x in enumerate(goi_ky, 1)]
    dm += ["", "## Dữ kiện cần nhập (có khi triển khai)", ""]
    dm += [f"- {x[0].upper() + x[1:]} (tệp {', '.join(sorted(set(t)))})" for x, t in can_nhap.items()]
    dm += ["", "Mẫu: Thông tư 43/2024/TT-BYT (Phụ lục I–VI là văn bản của Hội đồng) và bộ mẫu Hội đồng Đạo đức"
           " BVQY175 (hồ sơ đăng ký, tệp 1–8) không có mẫu do nghiên cứu viên nộp sau chấp thuận; văn bản dựng theo"
           " nội dung Thông tư 43 yêu cầu (Điều 6 khoản 1 điểm a; Điều 18 khoản 2, 3; Phụ lục I mục 6)."]
    (ra / f"DANH_MUC_SAU_CHAP_THUAN_{study}.md").write_text("\n".join(dm) + "\n", encoding="utf-8", newline="\n")
    if loi_vet:
        dong += ["DẤU VẾT MÁY trong văn bản nộp — sửa tại nguồn rồi dựng lại:"] + [f"  ✗ {x}" for x in loi_vet]
    return (1 if ba["a"] or loi_vet else 0), dong


#: Nhãn trạng thái máy (checkpoint/cổng) không được xuất hiện trong văn bản nộp Hội đồng.
_NHAN_TRANG_THAI_MAY = re.compile(r"(?<![A-Za-z])(?:PENDING|LOCKED|UNLOCKED|BLOCKED|PASS|FAIL|READY|DRAFT|TODO)"
                                  r"(?:_[A-Z0-9_]+)?(?![A-Za-z])")


def dau_vet_may(p: Path) -> list[str]:
    """Dấu vết máy trong một văn bản đã dựng: luật chung của bộ hồ sơ đề tài cơ sở + nhãn trạng thái máy + dấu nội
    bộ («[GÓI KÝ: …]», «[CẦN …]») còn sót."""
    import ho_so_dtcs_bvqy175 as DTCS  # noqa: PLC0415
    import ho_so_hdd_bvqy175 as HDD  # noqa: PLC0415

    van = "\n".join(HDD._van_ban_docx(p))
    ra = [f"{loai} «{doan}»" for loai, doan in DTCS.tim_dau_vet_may(van)]
    ra += [f"nhãn trạng thái máy «{m.group(0)}»" for m in _NHAN_TRANG_THAI_MAY.finditer(van)]
    ra += [f"dấu nội bộ «{m.group(0)[:40]}»" for m in HSC.DAU_DANH_DAU.finditer(van)]
    ra += ["dấu nội bộ «[CẦN …]»"] if "[CẦN" in van else []
    return ra


def co_dau_noi_bo(p: Path) -> bool:
    import ho_so_hdd_bvqy175 as HDD  # noqa: PLC0415

    return bool(re.search(HSC.DAU_DANH_DAU.pattern, "\n".join(HDD._van_ban_docx(p))))
