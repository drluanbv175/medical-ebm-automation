#!/usr/bin/env python3
"""Bộ hồ sơ chấm độ giá trị nội dung (CVI) của phiếu trích — đề tài btm-dtd2-ngoai-tru-BVQY175 (đề cương §4.6, bước 1).

Hai lệnh:

  dung   Sinh hồ sơ gửi hội đồng chuyên gia từ dữ kiện đã chốt của đề tài:
           - pha_cong_cu/HO_SO_CHAM_CVI_<mã>.md + .docx: thư mời, hướng dẫn, thang chấm, bảng 43 trường nhập tay (định
             nghĩa vận hành = nhãn + phương án mã hoá + quy tắc trích của từ điển REDCap) và 18 biến phái sinh (định
             nghĩa + công thức), hai câu hỏi mở;
           - pha_cong_cu/PHIEU_CHAM_CVI_<mã>.xlsx: phiếu chấm Excel (ô điểm chỉ nhận số nguyên 1–4), mỗi chuyên gia lưu
             một bản «PHIEU_CHAM_CVI_CG0x.xlsx».
         Danh sách mục lấy từ pha_cong_cu/phieu_cvi.csv và phieu_cvi_bien_phai_sinh.csv (đúng 61 mục đã chọn ở phiếu
         đề xuất G1-T4 §2.2) — không tự thêm/bớt mục.
  nhap   Đọc các phiếu Excel chuyên gia gửi lại (thư mục --vao), ghép điểm vào phieu_cvi.csv,
         phieu_cvi_bien_phai_sinh.csv, thông tin chuyên gia + câu hỏi mở vào phieu_cvi_hoi_dong.csv và góp ý từng mục
         vào gop_y_cvi.csv. Chạy khô mặc định; `--ap-dung` mới ghi (sao lưu trước). Không ghi đè điểm đã có của một
         chuyên gia trừ khi `--ghi-de`. Sau đó tính bằng công cụ chuẩn:
           python tools/pha_phat_trien_cong_cu.py cvi exports/<mã>/pha_cong_cu/phieu_cvi.csv

Không chứa và không nhận thông tin định danh: chuyên gia chỉ mang mã CG01–CG05; họ tên giữ ở danh sách riêng của chủ
nhiệm. Chỉ dùng thư viện chuẩn + openpyxl. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MA = "btm-dtd2-ngoai-tru-BVQY175"
GOC = Path(__file__).resolve().parents[1]          # exports/<mã>
MA_CG = ("CG01", "CG02", "CG03", "CG04", "CG05")
NHOM = ("lam_sang", "quan_ly_chat_luong", "phuong_phap_thong_ke", "khac")
THANG = (("1", "Không phù hợp"), ("2", "Chỉ phù hợp nếu sửa nhiều"),
         ("3", "Phù hợp, cần sửa nhỏ câu chữ hoặc quy tắc"), ("4", "Phù hợp và rõ ràng"))
CAU_HOI = ("Định nghĩa vận hành của trường/biến này (dữ kiện lấy ở đâu trên eHospital, tính thế nào, mã hoá ra sao) phù "
           "hợp đến mức nào với khái niệm cần đo theo KDIGO 2022, KDIGO 2024, ADA 2026 và mục tiêu nghiên cứu?")
KM1 = ("Trong từng phần của phiếu (A–F), còn dữ kiện nào trên eHospital cần để xác định kết cục theo KDIGO/ADA mà phiếu "
       "chưa trích, hoặc tình huống nào trong hồ sơ mà quy tắc hiện tại chưa nói cách ghi? (ghi phần + dữ kiện/tình huống)")
KM2 = ("Ngoài các phần hiện có, còn thông tin nào cần cho ba mục tiêu (phát hiện bệnh thận mạn, điều trị bảo vệ thận, yếu "
       "tố liên quan) mà phiếu chưa đề cập?")
DAI_DIEN = {"creat_1_ngay": "đại diện khối 6 ô kết quả creatinin", "uacr_1_ngay": "đại diện khối 4 ô kết quả UACR"}
LICH = {"gui": "23/11/2026", "han_vong1": "30/11/2026", "vong2": "02–09/12/2026", "chot": "11/12/2026"}


class LoiDauVao(Exception):
    pass


def _doc_csv(p: Path) -> tuple[list[str], list[dict[str, str]]]:
    tho = p.read_text(encoding="utf-8-sig")
    rd = csv.DictReader(io.StringIO(tho))
    return list(rd.fieldnames or []), [dict(r) for r in rd]


def _ghi_csv(p: Path, cot: list[str], dong: list[dict[str, str]]) -> None:
    """Ghi CSV qua tệp tạm rồi thay (không bao giờ để tệp rỗng nửa chừng); giữ BOM nếu tệp gốc có."""
    bom = p.read_bytes()[:3] == b"\xef\xbb\xbf" if p.exists() else False
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cot, lineterminator="\n")
    w.writeheader()
    w.writerows(dong)
    tam = p.with_suffix(p.suffix + ".tam")
    tam.write_text(("﻿" if bom else "") + buf.getvalue(), encoding="utf-8", newline="\n")
    tam.replace(p)


def _gon(s: object) -> str:
    # «∈» không có trong Times New Roman (phông bắt buộc của hồ sơ) ⇒ viết bằng chữ.
    return re.sub(r"\s+", " ", str(s or "").replace("∈", " thuộc ")).strip()


def _muc_phieu1(goc: Path) -> list[dict[str, str]]:
    """43 trường nhập tay theo thứ tự phieu_cvi.csv, kèm định nghĩa vận hành từ từ điển REDCap."""
    _, ds = _doc_csv(goc / "pha_cong_cu" / "phieu_cvi.csv")
    _, tu_dien = _doc_csv(goc / "_bo-bien-rieng.csv")
    td = {r["Variable / Field Name"]: r for r in tu_dien}
    _, tx = _doc_csv(goc / "pha_cong_cu" / "bang_truy_xuat_cau_hoi.csv")
    phan = {r["muc"]: r.get("phan_linh_vuc", "") for r in tx}
    ra = []
    for r in ds:
        m = r["muc"]
        if m not in td:
            raise LoiDauVao(f"mục {m} của phieu_cvi.csv không có trong _bo-bien-rieng.csv")
        d = td[m]
        lua_chon = " · ".join(_gon(x) for x in str(d.get("Choices, Calculations, OR Slider Labels") or "").split("|")
                              if _gon(x))
        quy_tac = _gon(d.get("Field Note"))
        if m in DAI_DIEN:
            quy_tac = (quy_tac + " " if quy_tac else "") + f"(Mục {DAI_DIEN[m]}.)"
        ra.append({"muc": m, "phan": _gon(phan.get(m, "")).split(" (")[0], "noi_dung": _gon(d.get("Field Label")),
                   "lua_chon": lua_chon, "quy_tac": quy_tac})
    return ra


def _muc_phieu2(goc: Path) -> list[dict[str, str]]:
    _, ds = _doc_csv(goc / "pha_cong_cu" / "phieu_cvi_bien_phai_sinh.csv")
    _, ps = _doc_csv(goc / "_bien-phai-sinh.csv")
    p = {r["ten_bien"]: r for r in ps}
    ra = []
    for r in ds:
        m = r["muc"]
        if m not in p:
            raise LoiDauVao(f"biến {m} của phieu_cvi_bien_phai_sinh.csv không có trong _bien-phai-sinh.csv")
        ra.append({"muc": m, "noi_dung": _gon(p[m].get("nhan")), "dinh_nghia": _gon(p[m].get("dinh_nghia")),
                   "cong_thuc": _gon(p[m].get("cong_thuc"))})
    return ra


def _o(s: str) -> str:
    """Ô bảng Markdown: bỏ ký tự «|» làm vỡ cột."""
    return _gon(s).replace("|", "/") or "—"


def dung_md(goc: Path) -> str:
    p1, p2 = _muc_phieu1(goc), _muc_phieu2(goc)
    dong = [
        "# HỒ SƠ CHẤM ĐỘ GIÁ TRỊ NỘI DUNG CỦA PHIẾU TRÍCH HỒ SƠ",
        "",
        "**Đề tài:** Thực trạng phát hiện và điều trị bảo vệ thận ở bệnh nhân đái tháo đường típ 2 điều trị ngoại trú tại "
        "Bệnh viện Quân y 175 theo KDIGO 2022, KDIGO 2024 và ADA 2026",
        "",
        "**Mã chuyên gia:** CG0__ (ghi mã chủ nhiệm đã gửi kèm; không ghi họ tên trên hồ sơ này)",
        "",
        "## 1. Thư mời",
        "",
        "Kính gửi Quý chuyên gia,",
        "",
        "Nhóm nghiên cứu trân trọng mời Quý chuyên gia tham gia hội đồng 5 chuyên gia thẩm định độ giá trị nội dung của "
        "phiếu trích hồ sơ bệnh án điện tử (eHospital) dùng trong đề tài trên. Phiếu ghi lại dữ kiện có sẵn trong hồ sơ "
        "(lượt khám, mã ICD-10, kết quả xét nghiệm, đơn thuốc) để đo ba mục tiêu: thực trạng phát hiện bệnh thận mạn, "
        "điều trị bảo vệ thận và một số yếu tố liên quan với việc không được xét nghiệm đủ. Việc chấm không dùng dữ liệu "
        "người bệnh và không cần truy cập eHospital.",
        "",
        f"Thời hạn: nhận hồ sơ {LICH['gui']}; gửi lại phiếu chấm trước {LICH['han_vong1']}. Mục được sửa sau vòng 1 sẽ "
        f"gửi lại để chấm vòng 2 ({LICH['vong2']}); kết quả chốt trước {LICH['chot']}, trước khi nộp Hội đồng Khoa học, "
        "Đạo đức.",
        "",
        "## 2. Cách chấm",
        "",
        f"Với từng mục, xin Quý chuyên gia trả lời câu hỏi: «{CAU_HOI}»",
        "",
        "| Điểm | Ý nghĩa |",
        "|---|---|",
        *[f"| {d} | {n} |" for d, n in THANG],
        "",
        "- Chấm độc lập, không trao đổi với chuyên gia khác trước khi gửi phiếu.",
        "- Mục chấm 1, 2 hoặc 3: xin ghi góp ý cụ thể (câu chữ đề nghị, dữ kiện cần thêm, tình huống chưa có quy tắc).",
        "- Cách tính: điểm 3–4 được coi là phù hợp; chỉ số giá trị nội dung mức mục (I-CVI) = số chuyên gia chấm 3–4 / số "
        "chuyên gia đã chấm. Mục có I-CVI dưới 0,78 được sửa và chấm lại, tối đa hai vòng.",
        "- Có thể chấm trên bảng dưới đây hoặc trên tệp Excel gửi kèm (ô điểm chỉ nhận 1–4). Nếu dùng Excel, lưu tên tệp "
        "theo mã chuyên gia, ví dụ PHIEU_CHAM_CVI_CG01.xlsx.",
        "",
        "Tài liệu gửi kèm: phiếu thu thập số liệu (5 phần A–F), bộ biến số (bảng biến, biến phái sinh, danh mục mã), "
        "bảng truy xuất nguồn gốc từng câu hỏi; đoạn định nghĩa liên quan của KDIGO 2022, KDIGO 2024 và ADA 2026 do chủ "
        "nhiệm trích.",
        "",
        "## 3. Thông tin chuyên gia",
        "",
        "| Mục | Trả lời |",
        "|---|---|",
        "| Mã chuyên gia | CG0__ |",
        "| Nhóm chuyên môn | ☐ Lâm sàng (nội tiết, thận học)  ☐ Quản lý chất lượng, mã hoá hồ sơ  ☐ Phương pháp, thống kê  "
        "☐ Khác (dược lâm sàng…): ……… |",
        "| Công tác tại Khoa Khám bệnh | ☐ Có  ☐ Không |",
        "| Ngày chấm | ……/……/2026 |",
        "",
        f"## 4. Phiếu 1 — {len(p1)} trường nhập tay của phiếu trích",
        "",
        "| STT | Phần | Mã | Nội dung | Phương án, mã hoá | Quy tắc trích | Điểm 1–4 | Góp ý |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(p1, 1):
        dong.append(f"| {i} | {_o(r['phan'])} | `{r['muc']}` | {_o(r['noi_dung'])} | {_o(r['lua_chon'])} | "
                    f"{_o(r['quy_tac'])} | | |")
    dong += ["", f"## 5. Phiếu 2 — {len(p2)} biến phái sinh định nghĩa kết cục", "",
             "| STT | Mã | Nội dung | Định nghĩa | Công thức | Điểm 1–4 | Góp ý |", "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(p2, 1):
        dong.append(f"| {i} | `{r['muc']}` | {_o(r['noi_dung'])} | {_o(r['dinh_nghia'])} | `{_o(r['cong_thuc'])}` | | |")
    dong += ["", "## 6. Câu hỏi mở", "", f"**Câu 1.** {KM1}", "", "………………………………………………………………", "",
             f"**Câu 2.** {KM2}", "", "………………………………………………………………", "",
             "Xin chân thành cảm ơn Quý chuyên gia.", ""]
    return "\n".join(dong)


def dung_xlsx(goc: Path, ra: Path) -> None:
    from openpyxl import Workbook  # noqa: PLC0415
    from openpyxl.styles import Alignment, Font, PatternFill  # noqa: PLC0415
    from openpyxl.worksheet.datavalidation import DataValidation  # noqa: PLC0415

    p1, p2 = _muc_phieu1(goc), _muc_phieu2(goc)
    wb = Workbook()
    hd = wb.active
    hd.title = "Huong_dan"
    for d in ["HỒ SƠ CHẤM ĐỘ GIÁ TRỊ NỘI DUNG CỦA PHIẾU TRÍCH HỒ SƠ", "", f"Câu hỏi cho mỗi mục: {CAU_HOI}", "",
              *[f"Điểm {d}: {n}" for d, n in THANG], "",
              "Điền mã chuyên gia ở trang Thong_tin; chấm ở cột «Điểm» của trang Phieu1 và Phieu2 (chỉ nhận số 1–4);",
              "mục chấm 1–3 xin ghi góp ý; trả lời hai câu hỏi mở ở trang Cau_hoi_mo.",
              f"Lưu tệp theo mã chuyên gia (ví dụ PHIEU_CHAM_CVI_CG01.xlsx) và gửi lại trước {LICH['han_vong1']}."]:
        hd.append([d])
    hd["A1"].font = Font(bold=True)
    hd.column_dimensions["A"].width = 120
    tt = wb.create_sheet("Thong_tin")
    for r in (("Mục", "Trả lời"), ("Mã chuyên gia", ""), ("Nhóm chuyên môn", ""),
              ("Công tác tại Khoa Khám bệnh (co/khong)", ""), ("Ngày chấm", "")):
        tt.append(list(r))
    tt["A1"].font = Font(bold=True)
    tt["B1"].font = Font(bold=True)
    tt.column_dimensions["A"].width = 42
    tt.column_dimensions["B"].width = 30
    for o, gt in (("B2", MA_CG), ("B3", NHOM), ("B4", ("co", "khong"))):
        dv = DataValidation(type="list", formula1='"' + ",".join(gt) + '"', allow_blank=True)
        tt.add_data_validation(dv)
        dv.add(o)
    vang = PatternFill("solid", fgColor="FFF2CC")

    def _trang(ten: str, tieu_de: list[str], dong: list[list[str]], cot_diem: int, rong: list[int]) -> None:
        ws = wb.create_sheet(ten)
        ws.append(tieu_de)
        for c in ws[1]:
            c.font = Font(bold=True)
        for d in dong:
            ws.append(d)
        for i, w in enumerate(rong, 1):
            ws.column_dimensions[chr(64 + i)].width = w
        for hang in ws.iter_rows(min_row=2):
            for c in hang:
                c.alignment = Alignment(wrap_text=True, vertical="top")
            hang[cot_diem - 1].fill = vang
        cot = chr(64 + cot_diem)
        dv = DataValidation(type="whole", operator="between", formula1="1", formula2="4", allow_blank=True,
                            showErrorMessage=True, errorTitle="Điểm 1–4", error="Chỉ nhận số nguyên từ 1 đến 4")
        ws.add_data_validation(dv)
        dv.add(f"{cot}2:{cot}{len(dong) + 1}")
        ws.freeze_panes = "D2"

    _trang("Phieu1", ["STT", "Phần", "Mã", "Nội dung", "Phương án, mã hoá", "Quy tắc trích", "Điểm (1–4)", "Góp ý"],
           [[str(i), r["phan"], r["muc"], r["noi_dung"], r["lua_chon"], r["quy_tac"], "", ""]
            for i, r in enumerate(p1, 1)], 7, [5, 22, 18, 40, 34, 40, 10, 40])
    _trang("Phieu2", ["STT", "Mã", "Nội dung", "Định nghĩa", "Công thức", "Điểm (1–4)", "Góp ý"],
           [[str(i), r["muc"], r["noi_dung"], r["dinh_nghia"], r["cong_thuc"], "", ""] for i, r in enumerate(p2, 1)],
           6, [5, 20, 40, 50, 36, 10, 40])
    km = wb.create_sheet("Cau_hoi_mo")
    km.append(["Câu", "Nội dung câu hỏi", "Trả lời"])
    km.append(["km1_khia_canh_thieu", KM1, ""])
    km.append(["km2_linh_vuc_thieu", KM2, ""])
    for c in km[1]:
        c.font = Font(bold=True)
    for w, col in ((22, "A"), (70, "B"), (70, "C")):
        km.column_dimensions[col].width = w
    for hang in km.iter_rows(min_row=2):
        for c in hang:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    tam = ra.with_suffix(".tam.xlsx")
    wb.save(tam)
    tam.replace(ra)


def lenh_dung(a: argparse.Namespace) -> int:
    goc = Path(a.goc) if a.goc else GOC
    md = dung_md(goc)
    ra_md = goc / "pha_cong_cu" / f"HO_SO_CHAM_CVI_{MA}.md"
    ra_xlsx = goc / "pha_cong_cu" / f"PHIEU_CHAM_CVI_{MA}.xlsx"
    tam = ra_md.with_suffix(".md.tam")
    tam.write_text(md, encoding="utf-8", newline="\n")
    tam.replace(ra_md)
    dung_xlsx(goc, ra_xlsx)
    print(f"✓ {ra_md.name} ({md.count(chr(10))} dòng) · {ra_xlsx.name}")
    if not a.khong_docx:
        repo = Path(a.repo) if a.repo else goc.parents[1]
        sys.path.insert(0, str(repo / "tools"))
        import md2docx_vn as M  # noqa: PLC0415

        M.markdown_to_docx(md, ra_md.with_suffix(".docx"))
        print(f"✓ {ra_md.with_suffix('.docx').name}")
    print("Cần bác sĩ kiểm chứng.")
    return 0


def _doc_xlsx(p: Path) -> dict:
    from openpyxl import load_workbook  # noqa: PLC0415

    wb = load_workbook(p, data_only=True)

    def _gt(v: object) -> str:
        if v is None:
            return ""
        if isinstance(v, float) and v.is_integer():
            v = int(v)
        return _gon(v)

    tt = {_gt(r[0].value): _gt(r[1].value) for r in wb["Thong_tin"].iter_rows(min_row=2) if r[0].value}
    ma = tt.get("Mã chuyên gia", "").upper()
    if ma not in MA_CG:
        raise LoiDauVao(f"{p.name}: «Mã chuyên gia» phải là một trong {', '.join(MA_CG)} (đang: «{ma or 'trống'}»)")
    diem, gop_y = {}, []
    for ten, cot_ma, cot_diem in (("Phieu1", 3, 7), ("Phieu2", 2, 6)):
        for r in wb[ten].iter_rows(min_row=2):
            m, d = _gt(r[cot_ma - 1].value), _gt(r[cot_diem - 1].value)
            if not m:
                continue
            if d and d not in {"1", "2", "3", "4"}:
                raise LoiDauVao(f"{p.name}, trang {ten}, mục {m}: điểm «{d}» không thuộc thang 1–4")
            diem[m] = d
            gy = _gt(r[cot_diem].value)
            if gy:
                gop_y.append({"ma_chuyen_gia": ma, "muc": m, "diem": d, "gop_y": gy})
    km = {_gt(r[0].value): _gt(r[2].value) for r in wb["Cau_hoi_mo"].iter_rows(min_row=2) if r[0].value}
    return {"ma": ma, "nhom": tt.get("Nhóm chuyên môn", ""),
            "thuoc": tt.get("Công tác tại Khoa Khám bệnh (co/khong)", "").lower(), "diem": diem, "gop_y": gop_y,
            "km1": km.get("km1_khia_canh_thieu", ""), "km2": km.get("km2_linh_vuc_thieu", "")}


def lenh_nhap(a: argparse.Namespace) -> int:
    goc = Path(a.goc) if a.goc else GOC
    pha = goc / "pha_cong_cu"
    tep = sorted(p for p in Path(a.vao).glob("*.xlsx") if not p.name.startswith("~$"))
    if not tep:
        raise LoiDauVao(f"không có tệp .xlsx trong {a.vao}")
    phieu = [_doc_xlsx(p) for p in tep]
    ma_ds = [x["ma"] for x in phieu]
    trung = sorted({m for m in ma_ds if ma_ds.count(m) > 1})
    if trung:
        raise LoiDauVao(f"mã chuyên gia trùng giữa các tệp: {', '.join(trung)}")
    ten_csv = {"p1": pha / "phieu_cvi.csv", "p2": pha / "phieu_cvi_bien_phai_sinh.csv",
               "hd": pha / "phieu_cvi_hoi_dong.csv", "gy": pha / "gop_y_cvi.csv"}
    cot1, d1 = _doc_csv(ten_csv["p1"])
    cot2, d2 = _doc_csv(ten_csv["p2"])
    coth, dh = _doc_csv(ten_csv["hd"])
    thay_doi, bo_qua = 0, []
    for x in phieu:
        for dong, ten in ((d1, "phieu_cvi"), (d2, "phieu_cvi_bien_phai_sinh")):
            for r in dong:
                moi = x["diem"].get(r["muc"], "")
                if not moi:
                    continue
                cu = r.get(x["ma"], "")
                if cu and cu != moi and not a.ghi_de:
                    bo_qua.append(f"{ten}:{r['muc']}:{x['ma']} (đang {cu}, phiếu {moi})")
                    continue
                if cu != moi:
                    r[x["ma"]] = moi
                    thay_doi += 1
        thieu = [r["muc"] for r in d1 + d2 if not x["diem"].get(r["muc"])]
        if thieu:
            print(f"  ⚠ {x['ma']}: chưa chấm {len(thieu)} mục ({', '.join(thieu[:6])}{'…' if len(thieu) > 6 else ''})")
        for r in dh:
            if r["ma_chuyen_gia"] == x["ma"]:
                for k, v in (("nhom", x["nhom"]), ("thuoc_don_vi_nghien_cuu", x["thuoc"]),
                             ("km1_khia_canh_thieu", x["km1"]), ("km2_linh_vuc_thieu", x["km2"])):
                    if v and (not r.get(k) or a.ghi_de):
                        r[k] = v
    gop_y = [g for x in phieu for g in x["gop_y"]]
    print(f"Phiếu đọc được: {len(phieu)} ({', '.join(ma_ds)}) · ô điểm mới: {thay_doi} · góp ý: {len(gop_y)}"
          + (f" · bỏ qua (đã có điểm khác, cần --ghi-de): {len(bo_qua)}" if bo_qua else ""))
    for b in bo_qua[:10]:
        print(f"    · {b}")
    if not a.ap_dung:
        print("Chạy khô — thêm --ap-dung để ghi. Cần bác sĩ kiểm chứng.")
        return 0
    sl = pha / "_sao_luu"
    sl.mkdir(exist_ok=True)
    gio = datetime.now().strftime("%Y%m%d-%H%M%S")
    for p in ten_csv.values():
        if p.exists():
            shutil.copy2(p, sl / f"{p.stem}.bak-{gio}{p.suffix}")
    _ghi_csv(ten_csv["p1"], cot1, d1)
    _ghi_csv(ten_csv["p2"], cot2, d2)
    _ghi_csv(ten_csv["hd"], coth, dh)
    cu_gy = _doc_csv(ten_csv["gy"])[1] if ten_csv["gy"].exists() else []
    khoa = {(g["ma_chuyen_gia"], g["muc"], g["gop_y"]) for g in cu_gy}
    _ghi_csv(ten_csv["gy"], ["ma_chuyen_gia", "muc", "diem", "gop_y"],
             cu_gy + [g for g in gop_y if (g["ma_chuyen_gia"], g["muc"], g["gop_y"]) not in khoa])
    print(f"✓ Đã ghi (sao lưu {gio}). Tính CVI:\n  python tools/pha_phat_trien_cong_cu.py cvi exports/{MA}/pha_cong_cu/"
          "phieu_cvi.csv\n  python tools/pha_phat_trien_cong_cu.py cvi exports/"
          f"{MA}/pha_cong_cu/phieu_cvi_bien_phai_sinh.csv\nCần bác sĩ kiểm chứng.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Bộ hồ sơ chấm CVI phiếu trích (đề cương §4.6)")
    p.add_argument("--goc", help=argparse.SUPPRESS)   # thư mục đề tài khác (thử trên bản sao)
    p.add_argument("--repo", help=argparse.SUPPRESS)  # repo chứa tools/md2docx_vn.py khi --goc nằm ngoài repo
    sub = p.add_subparsers(dest="lenh", required=True)
    d = sub.add_parser("dung", help="Sinh hồ sơ Word + phiếu chấm Excel gửi hội đồng chuyên gia")
    d.add_argument("--khong-docx", action="store_true", help="chỉ sinh .md và .xlsx")
    n = sub.add_parser("nhap", help="Ghép điểm từ các phiếu Excel chuyên gia gửi lại")
    n.add_argument("--vao", required=True, help="thư mục chứa các tệp PHIEU_CHAM_CVI_CG0x.xlsx đã chấm")
    n.add_argument("--ap-dung", action="store_true")
    n.add_argument("--ghi-de", action="store_true", help="cho ghi đè điểm/câu trả lời đã có")
    a = p.parse_args(argv)
    try:
        return lenh_dung(a) if a.lenh == "dung" else lenh_nhap(a)
    except LoiDauVao as e:
        print(f"✗ {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
