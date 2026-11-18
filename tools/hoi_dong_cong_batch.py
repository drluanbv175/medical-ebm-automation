#!/usr/bin/env python3
"""Hội đồng cổng G0–G10 qua Claude BATCH API — cùng biên bản, cùng luật với workflow `hoi-dong-cong.js`.

VÌ SAO (17/11/2026, bác sĩ chọn «Hội đồng cổng qua Batch API» khi kết nối API Claude): họp hội đồng bằng workflow cần
một phiên Claude Code mở và tốn token phiên (≈ 0,3 triệu token mỗi agent). Batch API rẻ một nửa, chạy không cần phiên,
hẹn lịch được. Công cụ dựng ĐÚNG các vai của workflow — người chấm chuyên môn + giám khảo độc lập cho mỗi đầu ra, rồi
tranh biện một vòng (điều phối cổng đề xuất → phản biện → trọng tài) cho DP và bất đồng — mỗi vai một yêu cầu với
system prompt là chính tệp agent `.claude/agents/<vai>.md`. Kết quả vào sổ bằng `hoi_dong_cong.ghi_bien_ban` — cùng bộ
luật từ chối ghi (thiếu căn cứ, căn cứ dòng ngoài tệp, PII, vượt thẩm quyền, thiếu giải pháp tốt nhất).

Khác workflow, có chủ ý:
- Model KHÔNG có công cụ: tệp đầu ra được dán kèm (đánh số dòng) và các lệnh chỉ đọc (`cham-song`, nhất quán xuyên
  cổng) được chạy SẴN rồi dán kết quả — căn cứ «lenh» chỉ được trỏ tới các lệnh đó.
- Tranh biện MỘT vòng (mỗi bước là một batch; hai vòng = sáu batch nối tiếp — không đáng thời gian chờ).
- Biên bản mang `nguon_may` (công cụ, model, id batch) và tranh biện mang `che_do: batch_api`.
- Tài liệu đổi sau khi khởi tạo ⇒ phần đó KHÔNG ghi (điểm chấm phải gắn đúng bản đã chấm).

Ranh giới: TƯ VẤN — không mở/chặn cổng, không ký, không ghi gate_params/sổ cái. Triệu tập (tính phí) là quyết định của
bác sĩ: mọi lệnh chạy khô mặc định; `buoc --goi-api` mới nộp/lấy batch; `ghi --ap-dung` mới ghi biên bản.

Dùng:
  hoi_dong_cong_batch.py uoc-tinh --study <mã> --gate GN        # 0 gọi API: số yêu cầu, token, USD
  hoi_dong_cong_batch.py buoc     --study <mã> --gate GN [--goi-api]   # lặp tới khi «xong» (mỗi lượt một batch)
  hoi_dong_cong_batch.py ghi      --study <mã> --gate GN [--ap-dung]   # kiểm luật biên bản, rồi ghi
Mã thoát: 0 xong bước · 1 có phần lỗi/không hợp lệ · 2 không gọi được API · 3 tham số sai · 4 batch đang xử lý.
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
import hoi_dong_cong as HDC  # noqa: E402

SCHEMA = "hoi_dong_cong_batch/v1"
CONG_CU = "tools/hoi_dong_cong_batch.py"
TRAN_KY_TU_TEP = 60_000
TRAN_KY_TU_YEU_CAU = 240_000
MAX_TOKENS = 16000
BUOC_TRANH = ("de_xuat", "phan_bien", "trong_tai")

QUY_TAC_API = (
    "\n\n## CHẾ ĐỘ BATCH API (thay cho mọi chỉ dẫn dùng công cụ ở trên)\n"
    "Bạn KHÔNG có công cụ: không chạy được lệnh, không đọc được tệp nào ngoài phần được dán trong tin nhắn. "
    "Căn cứ loại «tep» ghi đúng đường dẫn ở tiêu đề khối tệp, kèm «:dòng» hoặc «:dòng-dòng» là dòng CÓ THẬT (tệp đã "
    "đánh số dòng). Căn cứ loại «lenh» CHỈ được dùng các lệnh trong mục «LỆNH ĐÃ CHẠY SẴN», «ket_qua» chép nguyên văn "
    "đoạn kết quả liên quan. «tieu_chi» là mã tiêu chí cổng (vd G4-AUTO-09). Không bịa PMID/DOI, không ghi định danh "
    "người bệnh. Không viết kết luận như trạng thái cổng («đã ký», «đã duyệt», «PASS_…», «…_LOCKED»). Trả DUY NHẤT một "
    "đối tượng JSON đúng khuôn được yêu cầu, không lời dẫn, không rào ```."
)

_CAN_CU = '[{"loai": "tep|tieu_chi|pmid|doi|lenh", "gia_tri": "…", "ket_qua": "(chỉ với lenh)"}]'
_BAI_HOC = (
    '"bai_hoc_he_thong": [] (chỉ khi thấy lỗi của HỆ — công cụ/agent/điều phối/doctrine/quy trình hội đồng: '
    '{"pham_vi", "doi_tuong", "van_de", "de_xuat", "can_cu"}; không thấy thì để mảng rỗng, không bịa)'
)
KHUON = {
    "cham": (
        '{"tieu_chi": [{"ma": "RQ1", "muc": "dat|can_sua|loi_do|khong_ap_dung", "nhan_xet": "…", "can_cu": '
        + _CAN_CU
        + '}, … đủ RQ1–RQ8], "ket_luan": "dat|dat_co_luu_y|tra_ve_sua", '
        + _BAI_HOC
        + "}"
    ),
    "de_xuat": (
        '{"ket_luan_de_xuat": "…", "luan_diem": [{"ma": "L1", "noi_dung": "…", "can_cu": '
        + _CAN_CU
        + "}] (1–4 luận điểm)}"
    ),
    "phan_bien": (
        '{"luan_diem": [{"ma": "P1", "phan_doi": "L1", "noi_dung": "…", "can_cu": '
        + _CAN_CU
        + ', "nhuong": false}]} (không có phản đối có căn cứ ⇒ MỘT luận điểm nhuong=true)'
    ),
    "trong_tai": (
        '{"tung_luan_diem": [{"ma": "P1", "ket": "chap_nhan|bac|chua_du_can_cu", "ly_do": "…"}], "ket_qua": '
        '"giu_ket_luan|sua_ket_luan|chuyen_bac_si", "ket_luan_cuoi": "…", "viec_sua": ["…"], '
        '"chuyen_bac_si": [{"van_de": "…", "vi_sao": "…"}], "giai_phap_tot_nhat": {"phuong_an": "…", '
        '"can_cu": '
        + _CAN_CU
        + ', "phuong_an_khac": [{"phuong_an": "…", "vi_sao_khong_chon": "…"}]}, '
        + _BAI_HOC
        + "}"
    ),
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else ""


def _doc_agent(ten: str, goc: Path = REPO) -> str:
    p = goc / ".claude" / "agents" / f"{ten}.md"
    if not p.is_file():
        raise API.LoiCucBo(f"Thiếu tệp agent {p}")
    van = p.read_text(encoding="utf-8")
    if van.startswith("---"):
        van = van.split("---", 2)[-1]
    return van.strip()


def _muc_hdc(so: str, goc: Path = REPO) -> str:
    """Một mục «## <so>.» của _HOI-DONG-CONG.md (rubric §3, tranh biện §4) — để model chấm đúng bản chuẩn."""
    p = goc / ".claude" / "agents" / "_HOI-DONG-CONG.md"
    van = p.read_text(encoding="utf-8") if p.is_file() else ""
    m = re.search(rf"^## {re.escape(so)}\..*?(?=^## \d)", van, re.S | re.M)
    return m.group(0).strip() if m else ""


def he_thong(vai_agent: str, goc: Path = REPO) -> str:
    return _doc_agent(vai_agent, goc) + "\n\n" + _muc_hdc("3", goc) + "\n\n" + _muc_hdc("4", goc) + QUY_TAC_API


def khoi_tep(out_dir: Path, ds: Sequence[str], tran_tong: int = TRAN_KY_TU_YEU_CAU) -> Tuple[str, List[str]]:
    """Dán tệp (đánh số dòng). Quá trần ⇒ tệp sau bị BỎ và được liệt kê — không cắt im lặng."""
    khoi: List[str] = []
    bo: List[str] = []
    tong = 0
    for duong in ds:
        p = out_dir / duong
        if not p.is_file():
            bo.append(f"{duong} (không có)")
            continue
        dong = p.read_text(encoding="utf-8", errors="replace").splitlines()
        than = "\n".join(f"{i}| {d}" for i, d in enumerate(dong, 1))
        cat = ""
        if len(than) > TRAN_KY_TU_TEP:
            than = than[:TRAN_KY_TU_TEP]
            cat = f"\n… (CẮT ở {TRAN_KY_TU_TEP:,} ký tự — chỉ dùng căn cứ ở các dòng đã hiện)"
        if tong + len(than) > tran_tong:
            bo.append(f"{duong} (vượt trần {tran_tong:,} ký tự mỗi yêu cầu)")
            continue
        tong += len(than)
        khoi.append(f"### TỆP: {duong} ({len(dong)} dòng)\n{than}{cat}")
    if bo:
        khoi.append("### TỆP KHÔNG DÁN ĐƯỢC (không được viện dẫn): " + "; ".join(bo))
    return "\n\n".join(khoi), bo


def lenh_san(study: str, gate: str, out_dir: Path, nq: Any) -> str:
    """Hai lệnh chỉ đọc chạy SẴN — nguồn duy nhất cho căn cứ «lenh»."""
    try:
        song = HDC.cham_song(study, gate, out_dir)
        song = {k: v for k, v in song.items() if k != "_bao_cao"}
        song["chua_dat"] = (song.get("chua_dat") or [])[:40]
    except Exception as exc:  # trạng thái sống không đo được — nói thẳng, không bịa
        song = {"loi": f"KHÔNG ĐO ĐƯỢC: {type(exc).__name__}: {exc}"}
    return (
        "## LỆNH ĐÃ CHẠY SẴN (chỉ đọc)\n"
        f"$ python3 tools/hoi_dong_cong.py cham-song --study {study} --gate {gate}\n"
        + json.dumps(song, ensure_ascii=False)[:20000]
        + f"\n\n$ python3 tools/nhat_quan_xuyen_cong.py --study {study} --json  (lọc trục thuộc {gate})\n"
        + json.dumps(nq or [], ensure_ascii=False)[:12000]
    )


# ── Trạng thái ───────────────────────────────────────────────────────────────────────────────────────────────────
def tep_trang_thai(out_dir: Path, gate: str) -> Path:
    return out_dir / "kiem_may_api" / f"hoi_dong_{gate}.json"


def khoi_tao(study: str, gate: str, out_dir: Path, model: str) -> Dict[str, Any]:
    """Trạng thái mới từ hồ sơ máy (`ho_so_cong`, 0 agent). Ghi lại SHA-256 mọi tài liệu để chặn ghi điểm chấm lên
    bản đã đổi."""
    hs = HDC.ho_so_cong(study, gate, out_dir)
    cham: Dict[str, Any] = {}
    for n in hs["nhiem_vu"]:
        if n["can_cham"] and n.get("cham_chuyen_mon") and n["tai_lieu"]:
            cham[n["ma"]] = {
                "tac_gia": n["agent"],
                "chuyen_mon": n["cham_chuyen_mon"],
                "tai_lieu": n["tai_lieu"],
                "ket": {"chuyen_mon": None, "giam_khao": None},
                "loi": [],
            }
    tranh: Dict[str, Any] = {}
    for d in hs["dp"]:
        if d["can_tranh_bien"]:
            tranh[d["ma"]] = {
                "cau_hoi": d.get("cau_hoi"),
                "tham_quyen": d.get("tham_quyen"),
                "tai_lieu_xet": list(hs["tai_lieu_cong"]),
                "buoc": "de_xuat",
                "loi": [],
            }
    for b in hs["bat_dong_treo"]:
        tranh[b["ma"]] = {
            "nguon": b["nguon"],
            "nguon_id": b.get("nguon_id"),
            "cham": b.get("cham") or [],
            "tai_lieu_xet": list(b["tai_lieu_xet"]),
            "buoc": "de_xuat",
            "loi": [],
        }
    tl = sorted(
        {t for c in cham.values() for t in c["tai_lieu"]} | {t for x in tranh.values() for t in x["tai_lieu_xet"]}
    )
    return {
        "schema": SCHEMA,
        "study": study,
        "gate": gate,
        "model": model,
        "tao_luc": dt.datetime.now().isoformat(timespec="seconds"),
        "trang_thai_song": hs["trang_thai_song"],
        "khuyen_nghi": hs["khuyen_nghi"],
        "nhat_quan": hs.get("nhat_quan_xuyen_cong") or [],
        "sha": {t: _sha(out_dir / t) for t in tl},
        "cham": cham,
        "tranh": tranh,
        "batch": None,
        "lich_su": [],
    }


def _tai_lieu_doi(st: Dict[str, Any], out_dir: Path, ds: Sequence[str]) -> List[str]:
    return [t for t in ds if st["sha"].get(t) != _sha(out_dir / t)]


# ── Dựng yêu cầu ─────────────────────────────────────────────────────────────────────────────────────────────────
def _chung(st: Dict[str, Any]) -> str:
    return (
        f"Đề tài «{st['study']}», cổng {st['gate']} (trạng thái sống {st.get('trang_thai_song')}). Đường dẫn tệp "
        f"là tương đối thư mục exports/{st['study']}/. KHÔNG PII. Hội đồng là TƯ VẤN — không mở, không chặn cổng."
    )


def _loi_nhan(
    st: Dict[str, Any], out_dir: Path, tai_lieu: Sequence[str], viec: str, khuon: str
) -> Tuple[str, List[str]]:
    tep, bo = khoi_tep(out_dir, tai_lieu)
    nq = [k for k in st.get("nhat_quan") or []]
    return (
        f"{_chung(st)}\n\n{viec}\n\nKHUÔN JSON PHẢI TRẢ:\n{khuon}\n\n"
        f"{lenh_san(st['study'], st['gate'], out_dir, nq)}\n\n## TỆP\n\n{tep}"
    ), bo


def yeu_cau_tiep(
    st: Dict[str, Any], out_dir: Path, goc: Path = REPO, max_tokens: int = MAX_TOKENS
) -> List[Tuple[str, Dict[str, Any], Dict[str, Any]]]:
    """Mọi yêu cầu của bước KẾ TIẾP: (custom_id, tham số, nhãn). Phần đã xong/lỗi không dựng lại."""
    dp = HDC.dieu_phoi_cong(st["gate"])
    rq4 = (
        "RQ4 chấm TRÊN số đo nhất quán xuyên cổng ở mục LỆNH ĐÃ CHẠY SẴN: trục lech_cung ⇒ RQ4 loi_do; "
        "lech_mem/can_xem/chua_du ⇒ RQ4 can_sua (căn cứ loai=lenh); chỉ khi mọi trục khop mới được RQ4 dat."
    )
    ra: List[Tuple[str, Dict[str, Any], Dict[str, Any]]] = []
    for i, (ma, c) in enumerate(sorted(st["cham"].items())):
        if c["loi"]:
            continue
        doi = _tai_lieu_doi(st, out_dir, c["tai_lieu"])
        if doi:
            c["loi"].append(f"tài liệu đổi sau khi khởi tạo: {', '.join(doi)} — khởi tạo lại (--lam-lai)")
            continue
        for vai, ai, tien_to in (("chuyen_mon", c["chuyen_mon"], "cm"), ("giam_khao", HDC.GIAM_KHAO, "gk")):
            if c["ket"][vai] is not None:
                continue
            viec = (
                f"Bạn là người chấm «{ai}» (vai {vai}) cho ĐẦU RA nhiệm vụ {ma} của tác giả «{c['tac_gia']}». "
                f"Tệp: {', '.join(c['tai_lieu'])}. Chấm ĐỦ RQ1–RQ8 theo rubric §3. can_sua/loi_do bắt buộc có "
                "nhận xét + căn cứ; lỗi đỏ RQ3/RQ6/RQ7 ⇒ tra_ve_sua; khong_ap_dung phải nêu lý do. " + rq4
            )
            nd, _ = _loi_nhan(st, out_dir, c["tai_lieu"], viec, KHUON["cham"])
            ra.append(
                (
                    f"{tien_to}_{i:03d}",
                    API.tham_so(
                        nd, he_thong=he_thong(ai, goc), model=st["model"], max_tokens=max_tokens, effort="medium",
                        cache_he_thong=True,  # cùng tệp agent cho nhiều đầu ra ⇒ đọc từ cache
                    ),
                    {"loai": "cham", "ma": ma, "vai": vai},
                )
            )
    for i, (ma, t) in enumerate(sorted(st["tranh"].items())):
        if t["loi"] or t["buoc"] not in BUOC_TRANH:
            continue
        doi = _tai_lieu_doi(st, out_dir, t["tai_lieu_xet"])
        if doi:
            t["loi"].append(f"tài liệu đổi sau khi khởi tạo: {', '.join(doi)} — khởi tạo lại (--lam-lai)")
            continue
        if t["buoc"] == "de_xuat":
            if t.get("nguon"):
                viec = (
                    f"Bạn là {dp} (bên đề xuất). Hai người chấm BẤT ĐỒNG về đầu ra {t['nguon']}: "
                    f"{json.dumps(t.get('cham'), ensure_ascii=False)[:20000]}. Nêu kết luận dự kiến (đề xuất cho "
                    "người có thẩm quyền) và 1–4 luận điểm mã L1… có căn cứ."
                )
            else:
                viec = (
                    f"Bạn là {dp} ở bước soạn điểm quyết định {ma}: «{t.get('cau_hoi')}» (thẩm quyền "
                    f"{t.get('tham_quyen')}). Nêu kết luận dự kiến (đề xuất cho người có thẩm quyền) và 1–4 luận "
                    "điểm mã L1… mỗi luận điểm ≥ 1 căn cứ."
                )
            ai, khuon = dp, KHUON["de_xuat"]
        elif t["buoc"] == "phan_bien":
            viec = (
                f"Bạn là {HDC.PHAN_BIEN}, vòng 1. Điểm quyết định {ma}. Kết luận dự kiến: «{t['ket_luan_de_xuat']}». "
                f"Các bên đã nói: {json.dumps(t['vong'], ensure_ascii=False)}. Nêu phản đối MẠNH NHẤT có căn cứ "
                "(mã P…, phan_doi trỏ L…); không có thì MỘT luận điểm nhuong=true. Không bịa."
            )
            ai, khuon = HDC.PHAN_BIEN, KHUON["phan_bien"]
        else:
            viec = (
                f"Bạn là {HDC.TRONG_TAI} (ngữ cảnh mới). Điểm quyết định {ma}; kết luận dự kiến "
                f"«{t['ket_luan_de_xuat']}». Hồ sơ các vòng: {json.dumps(t['vong'], ensure_ascii=False)}. Kiểm căn "
                "cứ của từng bên rồi phán MỌI phản đối P… Đã chấp nhận phản đối thì KHÔNG giữ nguyên kết luận; "
                "tranh chấp thuộc thẩm quyền người ⇒ chuyen_bac_si. BẮT BUỘC giai_phap_tot_nhat có căn cứ; "
                "sua_ket_luan/chuyen_bac_si thêm ≥ 1 phuong_an_khac."
            )
            ai, khuon = HDC.TRONG_TAI, KHUON["trong_tai"]
        nd, _ = _loi_nhan(st, out_dir, t["tai_lieu_xet"], viec, khuon)
        ra.append(
            (
                f"{t['buoc'][:2]}_{i:03d}",
                API.tham_so(
                    nd, he_thong=he_thong(ai, goc), model=st["model"], max_tokens=max_tokens, effort="medium",
                    cache_he_thong=True,
                ),
                {"loai": "tranh", "ma": ma, "buoc": t["buoc"]},
            )
        )
    return ra


# ── Áp kết quả ───────────────────────────────────────────────────────────────────────────────────────────────────
def _hop_cham(dl: Any) -> Dict[str, Any]:
    if not (
        isinstance(dl, dict) and isinstance(dl.get("tieu_chi"), list) and dl.get("ket_luan") in HDC.KET_LUAN_DANH_GIA
    ):
        raise API.KetQuaHong("bản chấm sai khuôn (thiếu tieu_chi hoặc ket_luan lạ)")
    return dl


def _hop_luan_diem(dl: Any, can_kl: bool) -> Dict[str, Any]:
    ld = dl.get("luan_diem") if isinstance(dl, dict) else None
    if not (isinstance(ld, list) and ld and all(isinstance(x, dict) and x.get("ma") for x in ld)):
        raise API.KetQuaHong("luận điểm sai khuôn")
    if can_kl and not str(dl.get("ket_luan_de_xuat") or "").strip():
        raise API.KetQuaHong("thiếu ket_luan_de_xuat")
    return dl


def _hop_phan_quyet(dl: Any) -> Dict[str, Any]:
    if not (
        isinstance(dl, dict)
        and isinstance(dl.get("tung_luan_diem"), list)
        and dl.get("ket_qua") in HDC.KET_QUA_TRANH_BIEN
        and isinstance(dl.get("giai_phap_tot_nhat"), dict)
    ):
        raise API.KetQuaHong("phán quyết sai khuôn")
    return dl


def ap_ket_qua(st: Dict[str, Any], ket: Dict[str, Dict[str, Any]], max_tokens: int = MAX_TOKENS) -> Dict[str, int]:
    """Đưa kết quả batch vào trạng thái. Hỏng ⇒ phần đó ghi lỗi (không đoán), phần khác đi tiếp."""
    dem = {"ok": 0, "loi": 0, "vao": 0, "ra": 0, "cache_ghi": 0, "cache_doc": 0}
    yc = (st.get("batch") or {}).get("yeu_cau") or {}
    for cid, nhan in yc.items():
        kq = ket.get(cid) or {"loai": "thieu", "loi": "batch không trả custom_id này"}
        for k in ("vao", "ra", "cache_ghi", "cache_doc"):
            dem[k] += int(kq.get(k) or 0)
        try:
            dl = API.doc_json(API.van_ban_ket_qua_batch(kq, max_tokens))
            if nhan["loai"] == "cham":
                c = st["cham"][nhan["ma"]]
                ai = c["chuyen_mon"] if nhan["vai"] == "chuyen_mon" else HDC.GIAM_KHAO
                c["ket"][nhan["vai"]] = {**_hop_cham(dl), "nguoi_cham": ai, "vai": nhan["vai"]}
            else:
                t = st["tranh"][nhan["ma"]]
                if nhan["buoc"] == "de_xuat":
                    dl = _hop_luan_diem(dl, True)
                    t["ket_luan_de_xuat"] = str(dl["ket_luan_de_xuat"])
                    t["vong"] = [{"so": 1, "ben": "de_xuat", "luan_diem": dl["luan_diem"]}]
                    t["buoc"] = "phan_bien"
                elif nhan["buoc"] == "phan_bien":
                    t["vong"].append({"so": 1, "ben": "phan_bien", "luan_diem": _hop_luan_diem(dl, False)["luan_diem"]})
                    t["buoc"] = "trong_tai"
                else:
                    t["phan_quyet"] = {
                        "viec_sua": [],
                        "chuyen_bac_si": [],
                        **_hop_phan_quyet(dl),
                        "trong_tai": HDC.TRONG_TAI,
                    }
                    t["buoc"] = "xong"
            dem["ok"] += 1
        except (API.LoiApi, KeyError) as exc:
            dem["loi"] += 1
            muc = st["cham"].get(nhan["ma"]) if nhan["loai"] == "cham" else st["tranh"].get(nhan["ma"])
            if muc is not None:
                muc["loi"].append(f"{cid}: {str(exc)[:200]}")
    for ma, c in st["cham"].items():  # hai người chấm khác phía ⇒ tranh biện bất đồng BD-…
        k = c["ket"]
        if k["chuyen_mon"] and k["giam_khao"] and f"BD-{ma}" not in st["tranh"]:
            if len({x["ket_luan"] != "tra_ve_sua" for x in (k["chuyen_mon"], k["giam_khao"])}) == 2:
                st["tranh"][f"BD-{ma}"] = {
                    "nguon": ma,
                    "nguon_id": None,
                    "cham": [k["chuyen_mon"], k["giam_khao"]],
                    "tai_lieu_xet": list(c["tai_lieu"]),
                    "buoc": "de_xuat",
                    "loi": [],
                }
    return dem


# ── Biên bản ─────────────────────────────────────────────────────────────────────────────────────────────────────
def _nguon_may(st: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "cong_cu": CONG_CU,
        "model": st["model"],
        "batch": [h["batch_id"] for h in st.get("lich_su") or []],
        "luu_y": API.DISCLAIMER,
    }


def ban_nhap(st: Dict[str, Any]) -> List[Tuple[str, str, Dict[str, Any]]]:
    """[(loai, ma, biên bản nháp)] — đánh giá chéo TRƯỚC, tranh biện sau (BD cần id đánh giá chéo)."""
    ra: List[Tuple[str, str, Dict[str, Any]]] = []
    for ma, c in sorted(st["cham"].items()):
        if c.get("da_ghi") or c["loi"] or not (c["ket"]["chuyen_mon"] and c["ket"]["giam_khao"]):
            continue
        ra.append(
            (
                "danh_gia_cheo",
                ma,
                {
                    "loai": "danh_gia_cheo",
                    "dau_ra": {"ma_nhiem_vu": ma, "tac_gia": c["tac_gia"], "tai_lieu": c["tai_lieu"]},
                    "danh_gia": [c["ket"]["chuyen_mon"], c["ket"]["giam_khao"]],
                    "nguon_may": _nguon_may(st),
                },
            )
        )
    for ma, t in sorted(st["tranh"].items()):
        if t.get("da_ghi") or t["loi"] or t["buoc"] != "xong":
            continue
        bb = {
            "loai": "tranh_bien",
            "che_do": "batch_api",
            "diem_quyet_dinh": {"ma": ma},
            "tai_lieu_xet": t["tai_lieu_xet"],
            "ket_luan_de_xuat": t["ket_luan_de_xuat"],
            "vai": {"de_xuat": HDC.dieu_phoi_cong(st["gate"]), "phan_bien": HDC.PHAN_BIEN, "trong_tai": HDC.TRONG_TAI},
            "vong": t["vong"],
            "phan_quyet": t["phan_quyet"],
            "nguon_may": _nguon_may(st),
        }
        if t.get("nguon"):
            bb["nguon_bat_dong"] = t.get("nguon_id") or (st["cham"].get(t["nguon"]) or {}).get("da_ghi") or ""
        ra.append(("tranh_bien", ma, bb))
    return ra


def ghi(st: Dict[str, Any], out_dir: Path, ap_dung: bool, goc: Path = REPO) -> List[Dict[str, Any]]:
    kq: List[Dict[str, Any]] = []
    for loai, ma, bb in ban_nhap(st):
        muc = st["cham"][ma] if loai == "danh_gia_cheo" else st["tranh"][ma]
        tl = bb["dau_ra"]["tai_lieu"] if loai == "danh_gia_cheo" else bb["tai_lieu_xet"]
        doi = _tai_lieu_doi(st, out_dir, tl)
        if doi:
            kq.append(
                {"loai": loai, "ma": ma, "hop_le": False, "loi": [f"tài liệu đổi sau khi chấm: {', '.join(doi)}"]}
            )
            continue
        if loai == "tranh_bien" and "nguon_bat_dong" in bb and not bb["nguon_bat_dong"]:
            bb["nguon_bat_dong"] = (st["cham"].get(st["tranh"][ma].get("nguon")) or {}).get("da_ghi") or ""
        if not ap_dung:
            nhap = {
                **bb,
                "schema": HDC.SCHEMA,
                "study": st["study"],
                "gate": st["gate"],
                "tai_lieu_xet": HDC._bam_tai_lieu(tl, out_dir, []),
            }
            if loai == "tranh_bien" and not bb.get("nguon_bat_dong") and "nguon_bat_dong" in bb:
                nhap["nguon_bat_dong"] = "(id đánh giá chéo — điền khi ghi)"
            k = HDC.kiem_bien_ban(nhap, out_dir, goc, kiem_bam=False)
            kq.append({"loai": loai, "ma": ma, "hop_le": k["hop_le"], "loi": k["loi"]})
            continue
        p, k = HDC.ghi_bien_ban(st["study"], st["gate"], bb, out_dir, goc)
        if p is not None:
            muc["da_ghi"] = Path(p).stem  # tên tệp = id biên bản
        kq.append(
            {
                "loai": loai,
                "ma": ma,
                "hop_le": p is not None,
                "loi": k.get("loi", []),
                "tep": str(p) if p else None,
                "id": muc.get("da_ghi"),
            }
        )
    return kq


# ── Ước tính ─────────────────────────────────────────────────────────────────────────────────────────────────────
def uoc_tinh(st: Dict[str, Any], out_dir: Path, goc: Path = REPO) -> Dict[str, Any]:
    """Bước đầu dựng thật (đếm token đầu vào thật); bước tranh biện sau ước theo bước đầu; giả định không bất đồng."""
    yc = yeu_cau_tiep(json.loads(json.dumps(st)), out_dir, goc)
    vao = sum(API.uoc_token(p.get("system", "")) + API.uoc_token(p["messages"][0]["content"]) for _, p, _ in yc)
    so_dp = sum(1 for t in st["tranh"].values() if t["buoc"] == "de_xuat")
    tb_dp = (vao // max(len(yc), 1)) if yc else 0
    vao_tong = vao + 2 * so_dp * tb_dp
    ra_tong = (len(yc) + 2 * so_dp) * 3000
    return {
        "so_yeu_cau_buoc_1": len(yc),
        "so_dau_ra_cham": len(st["cham"]),
        "so_tranh_bien": len(st["tranh"]),
        "so_batch_toi_thieu": 3 if st["tranh"] else (1 if yc else 0),
        "uoc_tinh": API.in_chi_phi(vao_tong, ra_tong, st["model"], batch=True),
        "khuyen_nghi": st.get("khuyen_nghi"),
    }


def _in_chi_phi_that(dem: Dict[str, int], model: str) -> str:
    """Chi phí THẬT của một batch (giá Batch, gồm token cache) — số đã ghi vào sổ chi phí tháng."""
    usd = API.uoc_chi_phi(
        dem["vao"], dem["ra"], model, batch=True, cache_ghi=dem["cache_ghi"], cache_doc=dem["cache_doc"]
    )
    tien = "chưa ghi giá model" if usd is None else f"≈ {usd:.2f} USD"
    return (
        f"{dem['vao']:,} token vào + {dem['cache_ghi']:,} ghi cache + {dem['cache_doc']:,} đọc cache + "
        f"{dem['ra']:,} token ra {tien} ({model}, Batch API)"
    )


def _nhan_yc(yc: Sequence[Tuple[str, Dict[str, Any], Dict[str, Any]]]) -> str:
    return ", ".join(sorted({n["loai"] + ":" + (n.get("vai") or n.get("buoc") or "") for _, _, n in yc}))


def _doc_st(p: Path) -> Optional[Dict[str, Any]]:
    try:
        st = json.loads(p.read_text(encoding="utf-8"))
        return st if st.get("schema") == SCHEMA else None
    except (OSError, json.JSONDecodeError):
        return None


def _ghi_st(p: Path, st: Dict[str, Any]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(st, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def main(argv: Optional[Sequence[str]] = None, client: Any = None, goc: Path = REPO, goc_agent: Path = REPO) -> int:
    """`goc`: nơi có exports/ (thư mục dữ liệu); `goc_agent`: nơi có .claude/agents/ (mã) — tách để kiểm thử."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lenh", choices=("uoc-tinh", "buoc", "ghi", "trang-thai"))
    ap.add_argument("--study", required=True)
    ap.add_argument("--gate", required=True, choices=HDC.CONG)
    ap.add_argument("--goi-api", action="store_true", help="buoc: nộp/lấy batch THẬT (tính phí)")
    ap.add_argument("--ap-dung", action="store_true", help="ghi: ghi biên bản thật")
    ap.add_argument("--lam-lai", action="store_true", help="buoc: bỏ trạng thái cũ, khởi tạo lại từ hồ sơ máy")
    ap.add_argument(
        "--chi-lay",
        action="store_true",
        help="buoc --goi-api: CHỈ lấy kết quả batch đang chờ, KHÔNG nộp batch kế tiếp (bước sau tính phí)",
    )
    ap.add_argument("--model", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9._-]+", a.study):
        print("❌ --study chỉ nhận chữ/số/._-")
        return 3
    out_dir = goc / "exports" / a.study
    if not out_dir.is_dir():
        print(f"❌ Không thấy {out_dir}")
        return 3
    try:
        model = API.chon_model(a.model)
    except API.LoiApi as exc:
        print(f"❌ {exc}")
        return 3
    p = tep_trang_thai(out_dir, a.gate)
    st = None if a.lam_lai else _doc_st(p)
    in_ra = (lambda x: print(json.dumps(x, ensure_ascii=False, indent=1))) if a.json else None

    if a.lenh == "trang-thai":
        if st is None:
            print("Chưa có lượt hội đồng Batch API nào cho cổng này.")
            return 0
        tom = {
            "batch_dang_cho": (st.get("batch") or {}).get("id"),
            "cham": {
                m: {"xong": [v for v, k in c["ket"].items() if k], "loi": c["loi"], "da_ghi": c.get("da_ghi")}
                for m, c in st["cham"].items()
            },
            "tranh": {
                m: {"buoc": t["buoc"], "loi": t["loi"], "da_ghi": t.get("da_ghi")} for m, t in st["tranh"].items()
            },
            "lich_su": st.get("lich_su"),
        }
        (in_ra or (lambda x: print(json.dumps(x, ensure_ascii=False, indent=1))))(tom)
        return 0

    if st is None:
        st = khoi_tao(a.study, a.gate, out_dir, model)
    if a.lenh == "uoc-tinh":
        u = uoc_tinh(st, out_dir, goc_agent)
        if in_ra:
            in_ra(u)
        else:
            print(
                f"{a.gate}: {u['so_dau_ra_cham']} đầu ra chấm · {u['so_tranh_bien']} tranh biện · bước đầu "
                f"{u['so_yeu_cau_buoc_1']} yêu cầu · ≥ {u['so_batch_toi_thieu']} batch nối tiếp · ước {u['uoc_tinh']} "
                f"· khuyến nghị hồ sơ: {u['khuyen_nghi']}"
            )
        return 0

    if a.lenh == "ghi":
        kq = ghi(st, out_dir, a.ap_dung, goc)  # repo_root cho căn cứ «tep» tương đối repo
        if a.ap_dung:
            _ghi_st(p, st)
        for k in kq:
            print(
                f"{'✅' if k['hop_le'] else '⛔'} {k['loai']} {k['ma']}"
                + (f" → {k.get('id')}" if k.get("id") else "")
                + ("" if k["hop_le"] else f": {'; '.join(k['loi'])[:400]}")
            )
        if not kq:
            print("Không có biên bản nào đủ để ghi (chạy `buoc` tới khi xong).")
        if not a.ap_dung and kq:
            print("CHẠY KHÔ — chưa ghi. Ghi thật: thêm --ap-dung.")
        return 1 if any(not k["hop_le"] for k in kq) else 0

    # buoc
    if not a.goi_api:
        cho = (st.get("batch") or {}).get("id")
        yc = [] if cho else yeu_cau_tiep(json.loads(json.dumps(st)), out_dir, goc_agent)
        print(
            f"CHẠY KHÔ — {a.gate}: "
            + (
                f"batch {cho} đang chờ — `buoc --goi-api` để lấy kết quả."
                if cho
                else f"bước kế tiếp nộp {len(yc)} yêu cầu ({_nhan_yc(yc) or 'không còn gì'})."
            )
        )
        return 0
    try:
        if st.get("batch"):
            tt = API.trang_thai_batch(st["batch"]["id"], client)
            if tt["trang_thai"] != "ended":
                print(f"⏳ batch {tt['id']}: đang xử lý {tt['dang_xu_ly']} · xong {tt['xong']} · lỗi {tt['loi']}")
                _ghi_st(p, st)
                return 4
            ket = API.doc_ket_qua_batch(st["batch"]["id"], client, nguon=CONG_CU)
            dem = ap_ket_qua(st, ket)
            st["lich_su"].append(
                {
                    "batch_id": st["batch"]["id"],
                    "nop_luc": st["batch"]["nop_luc"],
                    "lay_luc": dt.datetime.now().isoformat(timespec="seconds"),
                    "so_yeu_cau": len(st["batch"]["yeu_cau"]),
                    "token_vao": dem["vao"],
                    "token_ra": dem["ra"],
                    "token_cache_ghi": dem["cache_ghi"],
                    "token_cache_doc": dem["cache_doc"],
                    "loi": dem["loi"],
                }
            )
            print(
                f"📥 batch {st['batch']['id']}: {dem['ok']} đạt khuôn · {dem['loi']} hỏng · "
                f"{_in_chi_phi_that(dem, st['model'])}"
            )
            st["batch"] = None
            API.ghi_nhat_ky_api(
                "ok",  # batch đã chạy ⇒ khoá sống; kết quả hỏng là chuyện câu trả lời, không phải sức khoẻ API
                f"{dem['loi']} kết quả hỏng",
                dem["ok"],
                "hoi_dong_cong_batch",
            )
        elif a.chi_lay:
            print("Không có batch nào đang chờ — `--chi-lay` không nộp gì.")
            return 0
        if a.chi_lay:  # bác sĩ chỉ cho lấy kết quả đã trả phí — bước kế tiếp (nộp batch mới) phải hỏi riêng
            _ghi_st(p, st)
            ban = json.loads(json.dumps(st))  # bản nháp: yeu_cau_tiep ghi lỗi «tài liệu đổi» vào đây, không vào sổ
            con = yeu_cau_tiep(ban, out_dir, goc_agent)
            ket_tac = [f"{m}: {x}" for m, c in ban["cham"].items() for x in c["loi"]]
            ket_tac += [f"{m}: {x}" for m, t in ban["tranh"].items() for x in t["loi"]]
            print(
                f"⏸ --chi-lay: KHÔNG nộp batch kế tiếp ({len(con)} yêu cầu: {_nhan_yc(con) or 'không còn gì'}). "
                "`ghi` để kiểm luật biên bản phần đã xong (chạy khô)."
            )
            if ket_tac:  # «không còn gì» không được che phần bị chặn
                print(f"⚠ {len(ket_tac)} phần KHÔNG đi tiếp được: " + " · ".join(ket_tac)[:1500])
            return 1 if ket_tac else 0
        yc = yeu_cau_tiep(st, out_dir, goc_agent)
        if not yc:
            _ghi_st(p, st)
            print("✅ Xong mọi bước có thể chạy — `ghi` để kiểm luật biên bản (chạy khô), `ghi --ap-dung` để ghi.")
            return 1 if any(c["loi"] for c in st["cham"].values()) or any(t["loi"] for t in st["tranh"].values()) else 0
        bid = API.nop_batch([(cid, prm) for cid, prm, _ in yc], client, nguon=CONG_CU)
        st["batch"] = {
            "id": bid,
            "nop_luc": dt.datetime.now().isoformat(timespec="seconds"),
            "yeu_cau": {cid: n for cid, _, n in yc},
        }
        _ghi_st(p, st)
        print(f"📤 Đã nộp batch {bid}: {len(yc)} yêu cầu. Chạy lại `buoc --goi-api` sau (thường < 1 giờ).")
        return 0
    except API.ThieuKhoa as exc:
        print(f"⚪ {exc}")
        API.ghi_nhat_ky_api("skipped", str(exc), 0, "hoi_dong_cong_batch")
        return 2
    except API.LoiCucBo as exc:  # lỗi phía máy — không phải sức khoẻ API, không ghi nhật ký
        _ghi_st(p, st)
        print(f"⛔ {exc}")
        return 2
    except API.LoiApi as exc:
        _ghi_st(p, st)
        print(f"⚪ Không gọi được Batch API: {exc}")
        API.ghi_nhat_ky_api("error", str(exc), 0, "hoi_dong_cong_batch")
        return 2


if __name__ == "__main__":
    sys.exit(main())
