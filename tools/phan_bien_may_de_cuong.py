#!/usr/bin/env python3
"""Phản biện MÁY đề cương nộp Hội đồng bằng Claude API — lớp đọc bổ sung sau bộ kiểm tất định K1–K8.

VÌ SAO (17/11/2026, bác sĩ chọn «Phản biện máy đề cương nộp» khi kết nối API Claude): bộ sinh đề cương có chốt tất định
cho dấu vết máy và trục xuyên cổng, nhưng các lỗi người đọc Hội đồng hay bắt — cùng một con số khác nhau ở hai chương,
câu cụt sau biên tập tay, mục tiêu không có phân tích tương ứng — chỉ lộ khi có người đọc trọn văn bản. Công cụ gửi
TOÀN VĂN (đánh số dòng) cho Claude một lượt, rồi MÁY kiểm lại từng phát hiện: «trích» phải có NGUYÊN VĂN trong đề
cương (cả chỗ đối chiếu với lỗi mâu thuẫn) — không có thì phát hiện bị gạt sang «máy không xác minh được», không trình
như lỗi. Phần tất định chạy cả khi chạy khô: số trích dẫn không có trong danh mục, tài liệu không được trích, thứ tự
xuất hiện lần đầu sai luật Vancouver.

Ranh giới: TƯ VẤN — không sửa đề cương, không mở/chặn cổng, không thay phản biện người (G8). Không đánh giá lại lựa chọn
khoa học thuộc thẩm quyền chủ nhiệm. CHẠY KHÔ mặc định; `--goi-api` mới gọi (tính phí) và ghi báo cáo vào
exports/<mã>/kiem_may_api/.

Mã thoát: 0 không có phát hiện mức cao/vừa · 1 có · 2 không kiểm được (thiếu khoá/API) · 3 tham số sai.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parents[1]
for _d in (REPO, REPO / "tools"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import api_claude_nc as API  # noqa: E402
import kiem_noi_dung_trich_dan as KND  # noqa: E402

LOAI = ("mau_thuan_so", "mau_thuan_noi_dung", "cau_cut", "dau_vet_may", "thuat_ngu", "logic", "trinh_bay")
TEN_LOAI = {
    "mau_thuan_so": "mâu thuẫn số liệu",
    "mau_thuan_noi_dung": "mâu thuẫn nội dung",
    "cau_cut": "câu cụt/vỡ",
    "dau_vet_may": "dấu vết phần mềm",
    "thuat_ngu": "thuật ngữ không thống nhất",
    "logic": "mục tiêu–phân tích không khớp",
    "trinh_bay": "trình bày",
    "trich_dan": "trích dẫn (máy tất định)",
}
MUC = ("cao", "vua", "thap")
TRAN_TOKEN_VAO = 180_000
TOI_DA_PHAT_HIEN = 40

HE_THONG = (
    "Bạn là người phản biện đề cương (vai binh-duyet) đọc BẢN NỘP Hội đồng khoa học và đạo đức của một bệnh viện Việt "
    "Nam. Tìm lỗi TRÌNH BÀY và NHẤT QUÁN mà thành viên Hội đồng sẽ bắt. KHÔNG đánh giá lại lựa "
    "chọn khoa học thuộc thẩm "
    "quyền chủ nhiệm (thiết kế, cỡ mẫu, giả định, công cụ đo) trừ khi chính văn bản tự mâu thuẫn. Loại phát hiện:\n"
    "- mau_thuan_so: cùng một đại lượng (cỡ mẫu, tỷ lệ bỏ cuộc, alpha, lực mẫu, thời gian, mốc "
    "ngày, kinh phí, số biến, "
    "ngưỡng) mang giá trị khác nhau ở hai chỗ;\n"
    "- mau_thuan_noi_dung: hai chỗ nói khác nhau về cùng một điều (thiết kế, quần thể, kết cục chính, phương pháp phân "
    "tích, tiêu chuẩn chọn/loại);\n"
    "- cau_cut: câu bị cắt, thiếu vế, lặp chữ, ngoặc hay bảng vỡ;\n"
    "- dau_vet_may: chuỗi chỉ có nghĩa với phần mềm lọt vào văn bản nộp (tên tệp, mã nội bộ, khoá JSON, nhãn «[CẦN…]», "
    "«bản nháp», «máy sinh», ghi chú dành cho người soạn);\n"
    "- thuat_ngu: một khái niệm gọi nhiều tên, hoặc chữ viết tắt dùng mà không định nghĩa;\n"
    "- logic: mục tiêu – câu hỏi – biến số – phân tích không ăn khớp (vd kết cục chính không có phân tích tương ứng);\n"
    "- trinh_bay: đánh số mục/bảng sai, định dạng làm khó đọc.\n"
    # 18/11/2026 — bác sĩ gắn nhãn 12 phát hiện: 6 là báo nhầm, theo các kiểu dưới đây.
    "Trước khi ghi một phát hiện, tự kiểm: (1) mau_thuan_so — cộng/đối chiếu lại; số khớp thì KHÔNG ghi; (2) mâu "
    "thuẫn phải có hai chỗ NÓI KHÁC NHAU — một chỗ chỉ chi tiết hơn chỗ kia, hay thiết kế của MỘT NGHIÊN CỨU ĐƯỢC "
    "TRÍCH khác thiết kế của đề tài, thì không phải mâu thuẫn; (3) không cho một giá trị (phiên bản phần mềm, mã, số "
    "liệu) là «không có thật» khi văn bản không tự mâu thuẫn — bạn không kiểm được điều đó; (4) cỡ mẫu cần trích khác "
    "kích thước khung mẫu/quần thể nguồn; (5) cột mã biến đặt cạnh nội dung tiếng Việt trong phiếu thu thập hay từ "
    "điển dữ liệu là trình bày chuẩn, không phải dau_vet_may; (6) chỉ báo thiếu chữ viết tắt sau khi đã đối chiếu bảng "
    "viết tắt — cụm từ thường không phải chữ viết tắt.\n"
    "Văn bản được đánh số dòng dạng «123| nội dung». Mỗi phát hiện gồm: loai; muc (cao = Hội đồng có thể trả hồ sơ, "
    "vua = nên sửa trước khi nộp, thap = tuỳ chọn); dong (số dòng); trich (NGUYÊN VĂN ≤ 25 từ chép đúng từng chữ từ "
    'dòng đó, KHÔNG kèm số dòng); doi_chieu (chỉ với mâu thuẫn: {"dong": n, "trich": nguyên văn ≤ 25 từ chỗ kia}); '
    "van_de (≤ 40 từ, tiếng Việt); goi_y (≤ 40 từ, cách sửa cụ thể). Không chắc thì không ghi — "
    "không bịa phát hiện cho "
    f"có. Tối đa {TOI_DA_PHAT_HIEN} phát hiện, xếp từ cao xuống thấp. Trả DUY NHẤT JSON "
    '{"phat_hien":[{"loai":"…","muc":"…","dong":1,"trich":"…","doi_chieu":null,"van_de":"…","goi_y":"…"}]}.'
)


def danh_so_dong(van: str) -> str:
    return "\n".join(f"{i}| {d}" for i, d in enumerate(van.splitlines(), 1))


def _bo_so_dong(s: str) -> str:
    return re.sub(r"^\s*\d+\|\s?", "", str(s or "")).strip().strip('«»"')


def kiem_trich_dan_tat_dinh(van: str) -> List[Dict[str, Any]]:
    """Ba luật đếm được, không cần model: [n] không có trong danh mục; tài liệu không được trích; số được trích LẦN ĐẦU
    không theo thứ tự 1, 2, 3… (Vancouver đánh số theo thứ tự xuất hiện)."""
    tltk = KND.tach_tltk(van)
    cau = KND.tach_cau_khang_dinh(van)
    ra: List[Dict[str, Any]] = []
    da_trich: List[int] = []
    for c in cau:
        for n in c.so:
            if n not in da_trich:
                da_trich.append(n)
    thieu = sorted(set(da_trich) - set(tltk))
    if thieu:
        ra.append(
            {
                "loai": "trich_dan",
                "muc": "cao",
                "van_de": f"Trích dẫn không có trong danh mục tài liệu: {thieu}",
                "goi_y": "Thêm tài liệu vào danh mục hoặc sửa số trích dẫn.",
            }
        )
    khong_trich = sorted(set(tltk) - set(da_trich))
    if khong_trich:
        ra.append(
            {
                "loai": "trich_dan",
                "muc": "vua",
                "van_de": f"Tài liệu có trong danh mục nhưng không được trích: {khong_trich}",
                "goi_y": "Trích ở chỗ phù hợp hoặc bỏ khỏi danh mục.",
            }
        )
    sai = [(i + 1, n) for i, n in enumerate(da_trich) if n != i + 1]
    if sai and tltk:
        vt, n = sai[0]
        ra.append(
            {
                "loai": "trich_dan",
                "muc": "vua",
                "van_de": f"Thứ tự xuất hiện lần đầu không theo Vancouver: tài "
                f"liệu thứ {vt} được trích lần đầu là [{n}] ({len(sai)} vị trí lệch).",
                "goi_y": "Đánh số lại theo thứ tự xuất hiện lần đầu trong văn bản.",
            }
        )
    return ra


def kiem_phat_hien(dl: Any, van: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """(phát hiện đã xác minh nguyên văn, phát hiện máy không xác minh được). Không bao giờ trình phát hiện mà trích
    dẫn không có trong đề cương."""
    dong = van.splitlines()
    dat: List[Dict[str, Any]] = []
    khong: List[Dict[str, Any]] = []
    for p in ((dl.get("phat_hien") if isinstance(dl, dict) else None) or [])[:TOI_DA_PHAT_HIEN]:
        if not isinstance(p, dict):
            continue
        loai, muc = str(p.get("loai") or ""), str(p.get("muc") or "")
        trich = _bo_so_dong(p.get("trich"))
        ra = {
            "loai": loai,
            "muc": muc,
            "dong": p.get("dong"),
            "trich": trich,
            "van_de": str(p.get("van_de") or "")[:400],
            "goi_y": str(p.get("goi_y") or "")[:400],
        }
        ly_do = []
        if loai not in LOAI:
            ly_do.append(f"loại lạ «{loai}»")
        if muc not in MUC:
            ly_do.append(f"mức lạ «{muc}»")
        if not API.co_nguyen_van(trich, van):
            ly_do.append("trích không có nguyên văn trong đề cương")
        else:
            so = p.get("dong")
            dung_dong = isinstance(so, int) and 1 <= so <= len(dong) and API.co_nguyen_van(trich, dong[so - 1])
            if not dung_dong:  # model ghi lệch số dòng ⇒ máy đặt lại về dòng ĐẦU TIÊN chứa nguyên văn
                ra["dong"] = next((i for i, d in enumerate(dong, 1) if API.co_nguyen_van(trich, d)), ra["dong"])
        dc = p.get("doi_chieu")
        if isinstance(dc, dict) and dc.get("trich"):
            dct = _bo_so_dong(dc.get("trich"))
            ra["doi_chieu"] = {"dong": dc.get("dong"), "trich": dct}
            if not API.co_nguyen_van(dct, van):
                ly_do.append("trích đối chiếu không có nguyên văn trong đề cương")
        elif loai.startswith("mau_thuan"):
            ly_do.append("mâu thuẫn mà không nêu chỗ đối chiếu")
        if ly_do:
            ra["ly_do_khong_xac_minh"] = "; ".join(ly_do)
            khong.append(ra)
        else:
            dat.append(ra)
    thu_tu = {m: i for i, m in enumerate(MUC)}
    dat.sort(key=lambda x: (thu_tu.get(x["muc"], 9), x.get("dong") or 0))
    return dat, khong


def _o(s: Any) -> str:
    return str(s or "").replace("|", "/").replace("\n", " ").strip()


def bao_cao_md(
    study: str,
    tep: Path,
    tat_dinh: List[Dict[str, Any]],
    dat: List[Dict[str, Any]],
    khong: List[Dict[str, Any]],
    model: str,
    kq: Optional[API.KetQuaGoi],
    luc: str,
) -> str:
    dem = {m: sum(1 for p in dat if p["muc"] == m) for m in MUC}
    dong = [
        f"# Phản biện máy đề cương nộp — {study}",
        "",
        f"- Tệp: `{tep.name}` · lúc {luc} · model `{model}`"
        + (f" · {API.in_chi_phi(kq.token_vao, kq.token_ra, model)}" if kq else ""),
        f"- Phát hiện đã xác minh nguyên văn: cao {dem['cao']} · vừa {dem['vua']} · thấp {dem['thap']} · "
        f"máy không xác minh được {len(khong)} (không trình như lỗi) · trích dẫn tất định {len(tat_dinh)}",
        "",
        "Mỗi phát hiện dưới đây có đoạn trích đã được máy đối chiếu NGUYÊN VĂN với đề cương. Đây là lớp đọc bổ sung, "
        "không thay phản biện người và không đánh giá lại lựa chọn khoa học của chủ nhiệm.",
        "",
        "## Trích dẫn (máy tất định)",
        "",
    ]
    dong += [f"- [{p['muc']}] {p['van_de']} — {p['goi_y']}" for p in tat_dinh] or ["- Không có."]
    dong += [
        "",
        "## Phát hiện",
        "",
        "| # | Mức | Loại | Dòng | Trích | Vấn đề | Đối chiếu | Gợi ý sửa |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i, p in enumerate(dat, 1):
        dc = p.get("doi_chieu") or {}
        dong.append(
            f"| {i} | {p['muc']} | {TEN_LOAI.get(p['loai'], p['loai'])} | {p.get('dong') or ''} | "
            f"{_o(p['trich'])} | {_o(p['van_de'])} | "
            f"{(_o(dc.get('dong')) + ': ' + _o(dc.get('trich'))) if dc else ''} | {_o(p['goi_y'])} |"
        )
    if not dat:
        dong.append("| — | — | — | — | — | Không có phát hiện đã xác minh | — | — |")
    dong += ["", "## Máy không xác minh được (để tham khảo, không phải lỗi đã xác nhận)", ""]
    dong += [f"- dòng {p.get('dong')}: {_o(p['van_de'])} ({p['ly_do_khong_xac_minh']})" for p in khong] or [
        "- Không có."
    ]
    dong += ["", API.DISCLAIMER, ""]
    return "\n".join(dong)


def main(argv: Optional[Sequence[str]] = None, client: Any = None, goc: Path = REPO) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--study", required=True)
    ap.add_argument("--tep", help="tệp Markdown (mặc định: đề cương nộp Hội đồng của đề tài)")
    ap.add_argument("--goi-api", action="store_true", help="GỌI Claude API (tính phí) + ghi báo cáo")
    ap.add_argument("--model", default=None)
    ap.add_argument("--effort", default="medium", choices=("low", "medium", "high"))
    ap.add_argument("--ra", help="thư mục ghi báo cáo (mặc định exports/<mã>/kiem_may_api/)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9._-]+", a.study):
        print("❌ --study chỉ nhận chữ/số/._-")
        return 3
    tep = Path(a.tep) if a.tep else goc / "exports" / a.study / f"DE_CUONG_NOP_HOI_DONG_{a.study}.md"
    if not tep.is_file():
        print(f"❌ Không thấy tệp {tep}")
        return 3
    try:
        model = API.chon_model(a.model)
    except API.LoiApi as exc:
        print(f"❌ {exc}")
        return 3
    van = tep.read_text(encoding="utf-8")
    tat_dinh = kiem_trich_dan_tat_dinh(van)
    loi_nhan = "ĐỀ CƯƠNG NỘP HỘI ĐỒNG (đánh số dòng):\n\n" + danh_so_dong(van)
    vao = API.uoc_token(HE_THONG) + API.uoc_token(loi_nhan)
    if vao > TRAN_TOKEN_VAO:
        print(f"❌ Văn bản quá dài (~{vao:,} token > {TRAN_TOKEN_VAO:,}) — tách phần bằng --tep.")
        return 3
    if not a.goi_api:
        kh = {
            "study": a.study,
            "tep": str(tep),
            "so_dong": len(van.splitlines()),
            "trich_dan_tat_dinh": tat_dinh,
            "uoc_tinh": API.in_chi_phi(vao, 8000, model),
        }
        if a.json:
            print(json.dumps(kh, ensure_ascii=False, indent=1))
        else:
            print(
                f"CHẠY KHÔ — {a.study}: {kh['so_dong']} dòng. Trích dẫn (tất định): "
                + ("; ".join(f"[{p['muc']}] {p['van_de']}" for p in tat_dinh) or "không có vấn đề")
                + "."
            )
            print(f"Sẽ gọi 1 lượt · ước {kh['uoc_tinh']}. Gọi thật: thêm --goi-api (tính phí).")
        return 0
    try:
        kq = API.goi(loi_nhan, he_thong=HE_THONG, model=model, effort=a.effort, client=client,
                     nguon="phan_bien_may_de_cuong")
        dat, khong = kiem_phat_hien(API.doc_json(kq.van_ban), van)
    except API.ThieuKhoa as exc:
        print(f"⚪ {exc}")
        API.ghi_nhat_ky_api("skipped", str(exc), 0, "phan_bien_may_de_cuong")
        return 2
    except API.HetNganSach as exc:  # lỗi phía máy — khoá vẫn sống, không ghi nhật ký sức khoẻ
        print(f"⛔ {exc}")
        return 2
    except API.KetQuaHong as exc:  # API vẫn sống (khoá dùng được) — chỉ câu trả lời hỏng
        print(f"⚪ Không phản biện được: {exc}")
        API.ghi_nhat_ky_api("ok", f"kết quả hỏng: {exc}", 0, "phan_bien_may_de_cuong")
        return 2
    except API.LoiApi as exc:
        print(f"⚪ Không phản biện được: {exc}")
        API.ghi_nhat_ky_api("error", str(exc), 0, "phan_bien_may_de_cuong")
        return 2
    luc = dt.datetime.now().isoformat(timespec="seconds")
    ra_dir = Path(a.ra) if a.ra else goc / "exports" / a.study / "kiem_may_api"
    ra_dir.mkdir(parents=True, exist_ok=True)
    md = ra_dir / f"PHAN_BIEN_MAY_{a.study}.md"
    md.write_text(bao_cao_md(a.study, tep, tat_dinh, dat, khong, model, kq, luc), encoding="utf-8", newline="\n")
    (ra_dir / f"PHAN_BIEN_MAY_{a.study}.json").write_text(
        json.dumps(
            {
                "schema": "phan_bien_may_de_cuong/v1",
                "study": a.study,
                "tep": tep.name,
                "tep_sha256": hashlib.sha256(van.encode("utf-8")).hexdigest(),  # đề cương đổi ⇒ báo cáo cũ
                "luc": luc,
                "model": kq.model,
                # 18/11/2026: đo độ đúng theo TỪNG phiên bản lời dặn
                "loi_dan_sha256": hashlib.sha256(HE_THONG.encode("utf-8")).hexdigest()[:12],
                "token": {"vao": kq.token_vao, "ra": kq.token_ra},
                "usd": API.uoc_chi_phi(kq.token_vao, kq.token_ra, kq.model),
                "trich_dan_tat_dinh": tat_dinh,
                "phat_hien": dat,
                "khong_xac_minh": khong,
                "luu_y": API.DISCLAIMER,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    API.ghi_nhat_ky_api("ok", "", len(dat), "phan_bien_may_de_cuong")
    nang = [p for p in dat if p["muc"] in ("cao", "vua")] + [p for p in tat_dinh if p["muc"] in ("cao", "vua")]
    print(
        f"{'🟠' if nang else '🟢'} {len(nang)} phát hiện mức cao/vừa · {len(khong)} không xác minh được · báo cáo {md}"
    )
    return 1 if nang else 0


if __name__ == "__main__":
    sys.exit(main())
