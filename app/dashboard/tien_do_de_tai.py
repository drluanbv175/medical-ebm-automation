"""Tiến độ đề tài nghiên cứu trong Dashboard EBM (tab «6. Research») — 27/10/2026.

Bác sĩ giao: tích hợp bảng tiến độ (đang có ở Antifacts) vào ứng dụng «Dashboard EBM». Nguồn sự thật là sổ tiến độ của
từng đề tài `exports/<mã>/tien_do/TIEN_DO_<mã>.json` (schema `de_tai/so_tien_do/v1`) — cùng sổ mà Antifacts đọc.
Mô-đun này CHỈ ĐỌC sổ: không đổi trạng thái việc nào, không ghi gì. Cập nhật sổ làm trong phiên Claude.

Mỗi việc chưa xong có một câu «Tiếp tục mục …» để bác sĩ chép rồi dán vào Claude làm tiếp.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA_TIEN_DO = "de_tai/so_tien_do/v1"
TRANG_THAI_SO = frozenset({"xong", "dang", "cho_bs", "chua"})
# Nhãn hiển thị của trạng thái (đã tách «chua» thành «san» / «khoa»).
NHAN = {
    "xong": "✅ Xong",
    "dang": "🔵 Đang làm",
    "cho_bs": "🟡 Chờ bác sĩ",
    "san": "🟢 Làm được ngay",
    "khoa": "⚪ Chờ việc trước",
}
LAM_DUOC = ("dang", "cho_bs", "san")


def trang_thai_hien(viec: dict, theo_id: dict) -> str:
    """Trạng thái HIỂN THỊ của một việc: giữ xong/dang/cho_bs; «chua» thành «san» khi mọi việc phải xong trước đã
    xong, ngược lại thành «khoa»."""
    tt = viec.get("trang_thai")
    if tt != "chua":
        return tt
    truoc = viec.get("phu_thuoc") or []
    return "san" if all(theo_id.get(p, {}).get("trang_thai") == "xong" for p in truoc) else "khoa"


def so_hop_le(so: Any) -> bool:
    """Sổ đúng khuôn: schema đúng; có giai đoạn và việc; mỗi việc đủ khoá, trạng thái hợp lệ, thuộc giai đoạn có thật,
    phụ thuộc trỏ tới việc có thật. Sai một chỗ ⇒ bỏ CẢ sổ (thà không hiện còn hơn hiện tiến độ sai)."""
    if not isinstance(so, dict) or so.get("schema") != SCHEMA_TIEN_DO:
        return False
    gd, viec = so.get("giai_doan"), so.get("viec")
    if not isinstance(gd, list) or not gd or not isinstance(viec, list) or not viec:
        return False
    ma_gd = {g.get("id") for g in gd if isinstance(g, dict)}
    ma_viec = {v.get("id") for v in viec if isinstance(v, dict)}
    for v in viec:
        if not isinstance(v, dict):
            return False
        if not all(isinstance(v.get(k), str) and v.get(k) for k in ("id", "gd", "ten", "han")):
            return False
        if v.get("trang_thai") not in TRANG_THAI_SO or v["gd"] not in ma_gd:
            return False
        phu_thuoc = v.get("phu_thuoc", [])
        if not isinstance(phu_thuoc, list) or any(p not in ma_viec for p in phu_thuoc):
            return False
    return True


def cau_tiep_tuc(ma: str, viec: dict) -> str:
    """Câu bác sĩ dán vào Claude để làm tiếp đúng một việc (cùng câu với Antifacts và bảng trong khung chat)."""
    return f"Tiếp tục mục {viec['id']} «{viec['ten']}» của đề tài {ma}"


def doc_so_tien_do(exports_dir: Path) -> tuple[list[dict], list[str]]:
    """Đọc mọi sổ `exports/*/tien_do/TIEN_DO_*.json` → (danh sách đề tài, cảnh báo). Không ném lỗi."""
    de_tai: list[dict] = []
    canh_bao: list[str] = []
    if not exports_dir.is_dir():
        return de_tai, canh_bao
    for tep in sorted(exports_dir.glob("*/tien_do/TIEN_DO_*.json")):
        try:
            so = json.loads(tep.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            canh_bao.append(f"Bỏ qua sổ tiến độ không đọc được: {tep.name} ({e.__class__.__name__})")
            continue
        if not so_hop_le(so):
            canh_bao.append(f"Bỏ qua sổ tiến độ sai khuôn: {tep.name}")
            continue
        theo_id = {v["id"]: v for v in so["viec"]}
        nhan_ai = so.get("ai") if isinstance(so.get("ai"), dict) else {}
        viec = [{**v, "tt": trang_thai_hien(v, theo_id), "ai_nhan": nhan_ai.get(v.get("ai"), v.get("ai") or "")}
                for v in so["viec"]]
        giai_doan = []
        for g in so["giai_doan"]:
            cua_gd = [v for v in viec if v["gd"] == g["id"]]
            giai_doan.append({**g, "xong": sum(v["tt"] == "xong" for v in cua_gd), "tong": len(cua_gd)})
        # Cổng cứng = việc đo bằng sổ cái phê duyệt (approval_ledger G2/G4/G5/G8/G9/G10).
        cong = [v for v in viec if str(v.get("do_song", "")).startswith("approval_ledger")]
        de_tai.append({
            "ma": so.get("study") or tep.stem.replace("TIEN_DO_", ""),
            "ten": so.get("ten_de_tai") or so.get("study") or tep.stem,
            "tap_chi": so.get("tap_chi_dich", ""),
            "cap_nhat": so.get("cap_nhat", ""),
            "giai_doan": giai_doan,
            "viec": viec,
            "tong": len(viec),
            "xong": sum(v["tt"] == "xong" for v in viec),
            "cong_ky": sum(v["tt"] == "xong" for v in cong),
            "cong_tong": len(cong),
            "gd_hien": next((k for k, g in enumerate(giai_doan) if g["xong"] < g["tong"]), -1),
        })
    return de_tai, canh_bao


def mo_bang_trinh_duyet(path: Path) -> bool:
    """Mở tệp bằng trình duyệt mặc định (máy chủ Streamlit chạy ngay trên máy bác sĩ)."""
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        elif sys.platform.startswith("win"):
            import os
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(path)])
        return True
    except Exception:
        return False


def render_tien_do_de_tai(st: Any, exports_dir: Path, antifacts: Path | None = None) -> None:
    """Vẽ mục «Tiến độ đề tài» (chỉ đọc). `st` là mô-đun streamlit (truyền vào để test được)."""
    st.subheader("🧪 Tiến độ đề tài đang làm")
    de_tai, canh_bao = doc_so_tien_do(exports_dir)
    for c in canh_bao:
        st.warning(c)
    if antifacts is not None and antifacts.exists():
        if st.button("🌐 Mở Antifacts (tab Nghiên cứu cùng bảng này)", key="tdd_mo_antifacts"):
            ok = mo_bang_trinh_duyet(antifacts)
            (st.success if ok else st.error)(
                "Đã mở Antifacts trong trình duyệt." if ok
                else "Không mở được — mở tệp Antifacts.html ở thư mục «Claude AI».")
    if not de_tai:
        st.info("Chưa có sổ tiến độ đề tài nào (`exports/<mã>/tien_do/TIEN_DO_<mã>.json`).")
        return
    for p in de_tai:
        st.markdown(f"**{p['ten']}**  \n`{p['ma']}`" + (f" · đích: {p['tap_chi']}" if p["tap_chi"] else "")
                    + f" · sổ cập nhật {p['cap_nhat']}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Hoàn thành", f"{round(p['xong'] * 100 / p['tong'])}%", f"{p['xong']}/{p['tong']} việc",
                  delta_color="off")
        c2.metric("Cổng cứng đã ký", f"{p['cong_ky']}/{p['cong_tong']}")
        gd = p["giai_doan"][p["gd_hien"]] if p["gd_hien"] >= 0 else None
        c3.metric("Giai đoạn hiện tại", f"GĐ{p['gd_hien'] + 1}" if gd else "Xong", gd["ten"] if gd else None,
                  delta_color="off")
        st.progress(p["xong"] / p["tong"])

        chua_xong = [v for v in p["viec"] if v["tt"] != "xong"]
        lam_ngay = [v for v in p["viec"] if v["tt"] in LAM_DUOC]
        if lam_ngay:
            st.markdown("**Việc làm được ngay**")
            st.dataframe([{"Mục": v["id"], "Việc": v["ten"], "Ai": v["ai_nhan"], "Hạn": v["han"],
                           "Trạng thái": NHAN[v["tt"]]} for v in lam_ngay],
                         width="stretch", hide_index=True)
        if chua_xong:
            nhan_chon = [f"{x['id']} · {x['ten']} ({NHAN[x['tt']]})" for x in chua_xong]
            chon = st.selectbox("Chọn việc để làm tiếp", nhan_chon, key=f"tdd_chon_{p['ma']}")
            v = chua_xong[nhan_chon.index(chon)]
            st.caption("Bấm biểu tượng chép ở góc khung dưới, rồi dán vào Claude để làm tiếp việc này.")
            st.code(cau_tiep_tuc(p["ma"], v), language=None)
            if v["tt"] == "khoa":
                st.caption("⚪ Việc này còn chờ: " + ", ".join(v.get("phu_thuoc") or []))
        for k, g in enumerate(p["giai_doan"]):
            mo = k in (p["gd_hien"], p["gd_hien"] + 1)
            tieu_de = f"GĐ{k + 1} · {g['ten']} · {g.get('tu', '')} – {g.get('den', '')} · {g['xong']}/{g['tong']}"
            with st.expander(tieu_de, expanded=mo):
                st.dataframe([{"Mục": v["id"], "Việc": v["ten"], "Ai": v["ai_nhan"], "Hạn": v["han"],
                               "Trạng thái": NHAN[v["tt"]]} for v in p["viec"] if v["gd"] == g["id"]],
                             width="stretch", hide_index=True)
        st.caption("Chỉ đọc sổ tiến độ. Hạn là ước tính; việc gắn cổng chỉ chuyển «Xong» khi cổng đo đạt. "
                   "Cần bác sĩ kiểm chứng.")
