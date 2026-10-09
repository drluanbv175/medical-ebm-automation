# -*- coding: utf-8 -*-
"""Bộ sinh/bộ ghi G0 theo phán quyết hội đồng BD-G0-T1 / BD-G0-T2 (đề tài C1a, 07/10/2026) — vá 09/10/2026.

① run_pipeline gặp G0 chặn CHỈ vì chờ người (MISSING_PICO) trên nền bằng chứng đã có ⇒ chỉ CHẤM LẠI bằng
  g0_quality_gate.py, không chạy lại run_g0_auto.py (tra lại PubMed, đổi tập PMID và dấu vân tay, sinh lại A1).
② gate_status + pending_doctor_actions của checkpoint G0 lấy từ KẾT QUẢ CHẤM (trước đây in cứng «điền PICO…» mãi mãi).
③ needs_input nói đúng mục còn chờ: câu hỏi (HUMAN-01..04) đã đạt thì không bảo «PICO còn trống».
④ G0_pubmed_raw.json mang chiến lược tìm tái lập được (PRISMA-S): CSDL, ngày tra, chuỗi hiệu lực, bộ lọc, trần.
Ngoại tuyến; số liệu định danh là GIẢ.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import g0_quality_gate as G0Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g0_auto as G0A  # noqa: E402
import run_g8_auto as G8A  # noqa: E402
import run_pipeline as RP  # noqa: E402
from test_g0_quality_gate_20260728 import _artifact_text, _checkpoint, _confirmed_g0_meta  # noqa: E402


def _cham(g0: dict) -> dict:
    return G0Q.evaluate_g0_quality(checkpoint=_checkpoint(), meta={"gate_params": {"G0": g0}},
                                   artifact_text=_artifact_text(), registry_check=_checkpoint().get("registry_check"))


def _cau_hoi_xong_cho_pi() -> dict:
    """HUMAN-01..04 đạt; bỏ FINER + xác nhận ⇒ chỉ còn việc của PI."""
    g0 = copy.deepcopy(_confirmed_g0_meta())
    for k in ("finer_feasible", "finer_interesting", "finer_novel", "finer_ethical", "finer_relevant",
              "pico_confirmed", "reviewed_by_role", "reviewed_at", "dau_van_tay_chot"):
        g0.pop(k, None)
    return g0


# ── ③ thông điệp needs_input ──────────────────────────────────────────────────────────────────────────────────────
def test_cau_hoi_da_dat_thi_thong_diep_khong_bao_pico_con_trong():
    r = _cham(_cau_hoi_xong_cho_pi())
    con = [x["id"] for x in r["human_criteria"] if x["status"] != "PASS"]
    assert r["status"] == G0Q.STATUS_DRAFT_READY and con and not set(con) & set(G0Q._G0_HUMAN_CAU_HOI), con
    msg = r["needs_input"]["human_message"]
    assert "ĐÃ" in msg and "còn trống" not in msg and "Không cần tra lại PubMed" in msg
    assert all(i in msg for i in con), (con, msg)
    assert r["needs_input"]["reason_code"] == GC.REASON_MISSING_PICO, "mã lý do giữ nguyên — nơi khác gỡ cờ theo nó"


def test_pico_chua_xong_thi_thong_diep_noi_chua_chot_va_liet_ke_muc():
    g0 = _cau_hoi_xong_cho_pi()
    g0.pop("population")
    r = _cham(g0)
    msg = r["needs_input"]["human_message"]
    assert "chưa được" in msg and "G0-HUMAN-01" in msg and "ĐÃ" not in msg


# ── ② đồng bộ gate_status / pending_doctor_actions ───────────────────────────────────────────────────────────────
def test_dong_bo_draft_liet_ke_dung_muc_con_cho_va_lenh_cham_lai():
    r = _cham(_cau_hoi_xong_cho_pi())
    cp: dict = {"guardrail": {"passed": True}}
    G0Q.dong_bo_trang_thai_checkpoint(cp, r, "S")
    con = [x["id"] for x in r["human_criteria"] if x["status"] != "PASS"]
    assert cp["gate_status"] == "DRAFT — CHỜ BÁC SĨ: " + ", ".join(con)
    assert cp["pending_doctor_actions"][:-1] == r["pending_actions"]
    assert cp["pending_doctor_actions"][-1] == "Chạy: python tools/g0_quality_gate.py --study S"


def test_dong_bo_confirmed_thi_khong_con_viec():
    r = _cham(_confirmed_g0_meta())
    assert r["status"] == G0Q.STATUS_CONFIRMED
    cp = {"guardrail": {"passed": True}, "gate_status": "DRAFT — CHỜ BÁC SĨ CHỐT PICO trong study_meta.json",
          "pending_doctor_actions": ["Điền PICO 4 thành phần vào study_meta.json → gate_params.G0"]}
    G0Q.dong_bo_trang_thai_checkpoint(cp, r, "S")
    assert cp["gate_status"].startswith(G0Q.STATUS_CONFIRMED) and cp["pending_doctor_actions"] == []


def test_dong_bo_ly_do_nang_hon_giu_uu_tien():
    r = _cham(_confirmed_g0_meta())
    cp = {"guardrail": {"passed": True},
          "needs_input": {"blocked": True, "reason_code": GC.REASON_MISSING_PUBMED}}
    G0Q.dong_bo_trang_thai_checkpoint(cp, r, "S")
    assert cp["gate_status"].startswith("BLOCKED — thiếu bằng chứng thật")
    cp = {"guardrail": {"passed": False}}
    G0Q.dong_bo_trang_thai_checkpoint(cp, r, "S")
    assert cp["gate_status"] == "BLOCKED — guardrail liêm chính chưa sạch"
    cp = {"guardrail": {"passed": True}}
    G0Q.dong_bo_trang_thai_checkpoint(cp, {"status": G0Q.STATUS_BLOCKED, "pending_actions": ["x"]}, "S")
    assert cp["gate_status"].startswith("BLOCKED — kiểm tự động")


def test_refresh_checkpoint_thay_danh_sach_in_cung_cu(tmp_path):
    """Đúng ca C1a: checkpoint mang danh sách 6 việc in cứng từ lượt chạy đầu; chấm lại ghi danh sách THẬT."""
    p = tmp_path / "G0_checkpoint.json"
    p.write_text(json.dumps({
        "gate": "G0", "study": "S", "guardrail": {"passed": True},
        "gate_status": "DRAFT — CHỜ BÁC SĨ CHỐT PICO trong study_meta.json (gate_params.G0)",
        "pending_doctor_actions": ["Điền PICO 4 thành phần vào study_meta.json → gate_params.G0"],
    }), encoding="utf-8", newline="\n")
    r = _cham(_cau_hoi_xong_cho_pi())
    G0Q.refresh_checkpoint(study="S", out_dir=tmp_path, report=r)
    cp = json.loads(p.read_text(encoding="utf-8"))
    assert "Điền PICO 4 thành phần vào study_meta.json → gate_params.G0" not in cp["pending_doctor_actions"]
    assert cp["gate_status"].startswith("DRAFT — CHỜ BÁC SĨ: G0-HUMAN-")


def test_run_g0_auto_goi_ham_dong_bo_o_dong_thi_hanh():
    """Đường CHẠY TRỌN G0 cũng phải đi qua cùng hàm — nút gọi thật trong cây cú pháp, không khớp bình luận."""
    import ast
    cay = ast.parse((ROOT / "tools" / "run_g0_auto.py").read_text(encoding="utf-8"))
    main = next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == "main")
    assert any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
               and c.func.attr == "dong_bo_trang_thai_checkpoint" for c in ast.walk(main))


def test_g8_doc_g0_khong_con_viec_khi_danh_sach_rong_nhung_cong_khac_giu_mac_dinh():
    cp = {"_file_exists": True, "pending_doctor_actions": []}
    assert G8A._gate_pending_actions(cp, "G0") == "Khong con viec cua bac si theo checkpoint"
    assert G8A._gate_pending_actions({"_file_exists": True}, "G0") == "Xac nhan PICO + ket cuc chinh", \
        "checkpoint CŨ không có khoá ⇒ giữ câu mặc định"
    assert G8A._gate_pending_actions(cp, "G1") == "Bac si chon thiet ke cuoi"


# ── ④ chiến lược tìm trong G0_pubmed_raw.json ────────────────────────────────────────────────────────────────────
class _BanGhi:
    def __init__(self, pmid):
        self.pmid, self.title, self.publication_date = pmid, f"T{pmid}", "2025"
        self.journal_or_organization, self.url = "J", f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"


def test_run_pubmed_searches_ghi_chien_luoc_tung_nhanh(monkeypatch):
    goi: list = []

    class _Client:
        def search(self, q, max_results=0, pubtype_filter=None):
            goi.append((q, pubtype_filter))
            return [_BanGhi(str(10000000 + len(goi)))]

        def count_hits(self, q, pubtype_filter=None):
            return 42

    monkeypatch.setattr(G0A, "PubMedClient", _Client)
    monkeypatch.setattr(G0A.time, "sleep", lambda s: None)
    queries = {"base": "b", "broad": "b", "sr_ma": "b AND sr", "rct": "b AND rct", "guideline": "b AND g",
               "observational": "b", "recent_5yr": "b AND 2021:2026[dp]"}
    kq = G0A.run_pubmed_searches(queries, max_per_query=7)
    pv = kq["provenance"]
    assert set(pv) == {"sr_ma", "rct", "guideline", "observational", "recent_5yr"}
    o = pv["observational"]
    assert o["bo_loc"] == G0A.PM_OBSERVATIONAL_FILTER and o["tran_so_bai"] == 7
    assert o["chuoi_hieu_luc"] == f"({queries['observational']}) AND {G0A.PM_OBSERVATIONAL_FILTER}"
    assert pv["guideline"]["tran_so_bai"] == 5 and pv["recent_5yr"]["loai_trung_pmid"] is False
    assert all(v["so_hit_that"] == 42 and v["so_bai_lay_ve"] == 1 and len(v["pmid_lay_ve"]) == 1 for v in pv.values())
    assert [(v["truy_van"], v["bo_loc"]) for v in pv.values()] == goi, "chuỗi ghi lại phải đúng chuỗi đã gửi"


def test_raw_json_co_khoi_search_provenance_o_dong_thi_hanh():
    import ast
    cay = ast.parse((ROOT / "tools" / "run_g0_auto.py").read_text(encoding="utf-8"))
    khoa = {k.value for n in ast.walk(cay) if isinstance(n, ast.Dict) for k in n.keys if isinstance(k, ast.Constant)}
    assert {"search_provenance", "co_so_du_lieu", "ngay_tra", "truy_van_goc", "nhanh"} <= khoa


# ── ① run_pipeline chỉ chấm lại G0 khi chặn vì chờ người ─────────────────────────────────────────────────────────
def _de_tai(tmp_path: Path, *, ly_do=GC.REASON_MISSING_PICO, n_pmids=12, co_raw=True) -> Path:
    out = tmp_path / "exports" / "S"
    out.mkdir(parents=True)
    (out / "G0_checkpoint.json").write_text(json.dumps({
        "gate": "G0", "study": "S", "topic": "chủ đề", "n_pmids": n_pmids, "guardrail": {"passed": True},
        "needs_input": {"blocked": True, "reason_code": ly_do, "human_message": "chờ"},
    }), encoding="utf-8", newline="\n")
    if co_raw:
        (out / "G0_pubmed_raw.json").write_text("{}", encoding="utf-8", newline="\n")
    return out


def _chay(tmp_path, monkeypatch, start_gate=None, stale=()):
    lenh: list = []

    def gia(cmd, out_dir):
        lenh.append(cmd)
        return {"exit_code": GC.EXIT_BLOCKED, "stdout_tail": "", "stderr_tail": ""}

    monkeypatch.setattr(RP, "BASE", tmp_path)
    monkeypatch.setattr(RP, "_run_gate_once", gia)
    monkeypatch.setattr(RP.FRESH, "stale_report", lambda out_dir: {
        "stale_gates": list(stale), "orphan_gates": [], "fresh": not stale})
    bao_cao = RP.orchestrate("S", None, 1, start_gate, False)
    return lenh, bao_cao


def test_pipeline_g0_chi_cho_nguoi_thi_chi_cham_lai(tmp_path, monkeypatch):
    _de_tai(tmp_path)
    lenh, bc = _chay(tmp_path, monkeypatch)
    assert len(lenh) == 1 and Path(lenh[0][1]).name == "g0_quality_gate.py", lenh
    assert "--exports-dir" in lenh[0] and "run_g0_auto.py" not in " ".join(lenh[0])
    g0 = bc["gate_results"][0]
    assert g0["status"] == "blocked_missing_input" and g0["detail"].startswith("chỉ CHẤM LẠI G0")


def test_pipeline_ep_from_g0_hoac_g0_cu_van_chay_tron(tmp_path, monkeypatch):
    _de_tai(tmp_path)
    lenh, _ = _chay(tmp_path, monkeypatch, start_gate="G0")
    assert Path(lenh[0][1]).name == "run_g0_auto.py", "--from G0 là ý muốn dựng lại nền bằng chứng"
    lenh, _ = _chay(tmp_path, monkeypatch, stale=("G0",))
    assert Path(lenh[0][1]).name == "run_g0_auto.py"


def test_pipeline_khong_co_nen_bang_chung_hoac_ly_do_khac_thi_chay_tron(tmp_path, monkeypatch):
    for i, kw in enumerate(({"ly_do": GC.REASON_MISSING_PUBMED}, {"n_pmids": 0}, {"co_raw": False})):
        goc = tmp_path / str(i)
        goc.mkdir()
        _de_tai(goc, **kw)
        lenh, _ = _chay(goc, monkeypatch)
        assert Path(lenh[0][1]).name == "run_g0_auto.py", kw
