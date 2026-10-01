"""Phát hiện nguồn HỎNG KÉO DÀI qua nhiều lượt quét live (thêm 01/10/2026).

Vì sao: một nguồn hỏng ở MỌI lượt mà không ai thấy. RSS NEJM bị Cloudflare chặn từ lượt 07/09 tới 29/09 (9/9 lần gọi,
kho không nhận bài NEJM nào) — chỉ lộ ra khi đo tay ngày 30/09. Lý do: trạng thái lượt (PASS/PARTIAL/FAIL) cố ý không
đổi vì một feed lẻ hỏng (còn feed khác dự phòng), và không có gì so lượt này với các lượt trước. ECDC (chặn CloudFront)
và WHO IRIS (hết giờ mở kết nối) đang cùng kiểu từ 29/09.

Mô-đun này CHỈ ĐO và BÁO:
- đọc sức khoẻ từng nguồn đã lưu sẵn trong `pipeline_runs.stats["source_health"]["sources"]` của các lượt LIVE đã kết
  thúc (không thêm bảng, không ghi gì);
- một nguồn «hỏng kéo dài» khi health «unavailable» ở lượt hiện tại VÀ ở các lượt live liền trước — tổng ≥ `NGUONG_LUOT`
  lượt, trải ≥ `NGUONG_NGAY` ngày (bốn lượt chạy bù trong cùng một ngày không phải bốn tuần hỏng);
- chuỗi dừng ở lượt nguồn chạy được («ok»/«degraded»), hoặc VẮNG mặt / không được hỏi («not_queried»), hoặc là lượt
  mock: không đo được ≠ hỏng;
- KHÔNG đổi `status` của lượt chạy, không chặn gì. Nguồn đã có ghi chú chấp nhận trong lượt (vd Scopus bị Cloudflare
  chặn — bác sĩ chọn «ghi chú, không chặn» 29/09) vẫn được liệt kê kèm `da_co_ghi_chu` để người đọc tự xếp ưu tiên.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

NGUONG_LUOT = 3
NGUONG_NGAY = 7
SO_LUOT_DOC = 40


def _utc_tran(luc: Any) -> Optional[datetime]:
    """datetime về dạng UTC không múi giờ (cột `started_at` của SQLite lưu như vậy); chuỗi ISO cũng nhận."""
    if isinstance(luc, str):
        try:
            luc = datetime.fromisoformat(luc)
        except ValueError:
            return None
    if not isinstance(luc, datetime):
        return None
    if luc.tzinfo is not None:
        luc = luc.astimezone(timezone.utc).replace(tzinfo=None)
    return luc


def doc_lich_su_suc_khoe(so_luot: int = SO_LUOT_DOC) -> List[Dict[str, Any]]:
    """Sức khoẻ từng nguồn của tối đa `so_luot` lượt LIVE đã kết thúc gần nhất, MỚI → CŨ.

    Bỏ lượt không có số đo nguồn (lượt nạp sẵn bản ghi như lượt lấy bù, lượt kẹt «running» không có stats)."""
    from app.database import session_scope
    from app.models import PipelineRun

    ket_qua: List[Dict[str, Any]] = []
    with session_scope() as s:
        rows = (s.query(PipelineRun)
                .filter(PipelineRun.mode == "live", PipelineRun.finished_at.isnot(None))
                .order_by(PipelineRun.started_at.desc(), PipelineRun.id.desc())
                .limit(so_luot).all())
        for run in rows:
            sh = (run.stats or {}).get("source_health") if isinstance(run.stats, dict) else None
            nguon = (sh or {}).get("sources") if isinstance(sh, dict) else None
            if not isinstance(nguon, dict):
                continue
            ket_qua.append({"id": run.id, "luc": run.started_at,
                            "sources": {ten: {"health": (row or {}).get("health")}
                                        for ten, row in nguon.items() if isinstance(row, dict)}})
    return ket_qua


def _ghi_chu_cua(ten: str, ghi_chu: Iterable[str]) -> Optional[str]:
    tien_to = ten.upper() + "_"
    return next((g for g in ghi_chu if str(g).startswith(tien_to)), None)


def tinh_hong_keo_dai(hien_tai: Dict[str, Dict[str, Any]], lich_su: List[Dict[str, Any]], luc: Any, *,
                      ghi_chu: Iterable[str] = (), nguong_luot: int = NGUONG_LUOT,
                      nguong_ngay: int = NGUONG_NGAY) -> Dict[str, Dict[str, Any]]:
    """{nguồn: chi tiết} cho các nguồn hỏng kéo dài. Hàm thuần — `lich_su` MỚI → CŨ, không gồm lượt hiện tại.

    `hien_tai` là `source_health["sources"]` của lượt đang chạy; `luc` là thời điểm lượt này; `ghi_chu` là
    `mirror_notices` của lượt (ghi chú mang tiền tố TÊN_NGUỒN_)."""
    luc_nay = _utc_tran(luc)
    if luc_nay is None:
        return {}
    ghi_chu = list(ghi_chu or ())
    ket_qua: Dict[str, Dict[str, Any]] = {}
    for ten, row in sorted((hien_tai or {}).items()):
        if not isinstance(row, dict) or row.get("health") != "unavailable":
            continue
        cac_luc = [luc_nay]
        lan_chay_cuoi = None
        for luot in lich_su or []:
            health = ((luot.get("sources") or {}).get(ten) or {}).get("health")
            luc_luot = _utc_tran(luot.get("luc"))
            if health == "unavailable" and luc_luot is not None:
                cac_luc.append(luc_luot)
                continue
            if health in ("ok", "degraded") and luc_luot is not None:
                lan_chay_cuoi = luc_luot
            break
        bat_dau = min(cac_luc)
        so_ngay = (luc_nay - bat_dau).days
        if len(cac_luc) < nguong_luot or so_ngay < nguong_ngay:
            continue
        ket_qua[ten] = {
            "so_luot_lien": len(cac_luc),
            "hong_tu": bat_dau.date().isoformat(),
            "so_ngay": so_ngay,
            # None = trong cửa sổ đã đọc, nguồn chưa từng chạy được ngay trước chuỗi (mới thêm, hoặc hỏng lâu hơn).
            "lan_chay_duoc_cuoi": lan_chay_cuoi.date().isoformat() if lan_chay_cuoi else None,
            "kieu_duong_mang": dict(row.get("kieu_duong_mang") or {}),
            "loi_lan_nay": int(row.get("error") or 0),
            "da_co_ghi_chu": _ghi_chu_cua(ten, ghi_chu),
        }
    return ket_qua


def mo_ta_ngan(hong: Dict[str, Dict[str, Any]]) -> str:
    """Một dòng log: «feed_x từ 2026-09-07 (7 lượt/22 ngày, cloudflare-chan) · …»."""
    phan = []
    for ten, ct in sorted(hong.items(), key=lambda kv: (-kv[1]["so_ngay"], kv[0])):
        kieu = ",".join(sorted(ct.get("kieu_duong_mang") or {})) or "lỗi khác"
        them = f", đã có ghi chú {ct['da_co_ghi_chu']}" if ct.get("da_co_ghi_chu") else ""
        phan.append(f"{ten} từ {ct['hong_tu']} ({ct['so_luot_lien']} lượt/{ct['so_ngay']} ngày, {kieu}{them})")
    return " · ".join(phan)
