"""Giả lập ĐỊNH KỲ hệ nghiên cứu (R9, 15/11/2026) — tools/gia_lap_dinh_ky.py.

Kiểm logic của canary mà KHÔNG chạy cổng thật: tiến trình con (`chay`) và bộ chấm sống (`cham`) được thay bằng một
«thế giới giả» ghi đúng loại tệp mà cổng thật ghi (checkpoint, pipeline_run_report, KIEM_CHI_TIET_report). Mỗi khiếm
khuyết mà canary phải bắt (K4 query_en, N4 pipeline không chạy lại cổng, cổng cứng «đạt» khi chưa ký, dừng sai cổng,
thiết kế máy suy sai, crash, rò rỉ sang exports/ thật) có một phép thử riêng; phép so với lần trước và mã thoát 0/1/2
có phép thử riêng. Không mạng, không ký, không đụng exports/ hay state/ thật. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import gia_lap_dinh_ky as GL  # noqa: E402

FP = {"G0": "0" * 16, "G1": "1" * 16, "G3": "3" * 16}
KB_THU: Dict[str, Any] = {
    "study": "ZZCANARY-THU",
    "thiet_ke": "rct",
    "topic": "Chủ đề thử",
    "query_en": "sms AND hypertension",
    "cong_dung_mong_doi": "G5",
    "pi": {"G0": {"population": "P giả lập", "registry_manual_checked": {"ictrp": "<HOM_NAY>"}},
           "G1": {"design": "rct", "objectives": ["Mục tiêu"]},
           "G3": {"effect_size": 1.5, "effect_type": "RR"}},
    "xac_nhan": {"G0": {"pico_confirmed": True, "reviewed_by_role": "PI"},
                 "G1": {"reviewed_by_role": "methodologist"}, "G3": {"reviewed_by_role": "STATISTICIAN"}},
}


def _doc(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _ghi(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8", newline="\n")


class TheGioi:
    """Cổng + pipeline GIẢ. Cờ mô phỏng khiếm khuyết: dich_lac (K4: máy dịch chủ đề thành truy vấn khác query_en),
    n4 (pipeline không chạy lại G3 sau khi PI đổi tham số), g1_can_chay_lai (G1-AUTO-07 cho tới khi G1 chạy lại),
    thiet_ke (máy suy ở G1), cong_dung (cổng pipeline dừng), cung_dat (cổng cứng «đạt» dù chưa ký), crash,
    g0_r1b (G0 bị guardrail R1B chặn — nguồn giả lập/mất mạng)."""

    def __init__(self, **co):
        self.co = {"dich_lac": True, "n4": True, "g1_can_chay_lai": False, "thiet_ke": "rct", "cong_dung": "G5",
                   "cung_dat": (), "crash": False, "g0_r1b": False, "r1b_sau_query_en": False, "kct_do": ("G1/④",),
                   **co}
        self.lenh = []

    # ── trạng thái
    @staticmethod
    def _meta(out: Path) -> dict:
        return _doc(out / "study_meta.json")

    def _gp(self, out: Path, gate: str) -> dict:
        return (self._meta(out).get("gate_params") or {}).get(gate) or {}

    def _xong_noi_dung(self, out: Path, gate: str) -> bool:
        return all(self._gp(out, gate).get(k) == v for k, v in GL._thay_hom_nay(KB_THU["pi"][gate]).items())

    # ── tiến trình con giả
    def chay(self, cmd, cwd, env, timeout=900):
        ten = Path(cmd[2]).name
        self.lenh.append(ten)
        study = cmd[cmd.index("--study") + 1]
        out = Path(cwd) / "exports" / study
        out.mkdir(parents=True, exist_ok=True)
        if self.co["crash"] and ten == "run_pipeline.py":
            return {"ma": 1, "ra": "Traceback (most recent call last):\n  ValueError", "crash": True}
        if ten == "run_pipeline.py":
            self._pipeline(out, cmd)
        elif ten == "run_g3_auto.py":
            cp = _doc(out / "G3_checkpoint.json")
            cp.update({"effect_val": self._gp(out, "G3").get("effect_size"), "chay_lai": True})
            _ghi(out / "G3_checkpoint.json", cp)
        elif ten == "run_g1_auto.py":
            cp = _doc(out / "G1_checkpoint.json")
            cp["a2_theo_noi_dung"] = True
            _ghi(out / "G1_checkpoint.json", cp)
        elif ten == "kiem_chi_tiet_he_nghien_cuu.py":
            _ghi(out / "KIEM_CHI_TIET_report.json", {
                "tong": {"xanh": 40, "vang": 30, "do": len(self.co["kct_do"]), "trang": 1},
                "muc": [{"cong": o.split("/")[0], "truc": o.split("/")[1], "muc": "🔴"} for o in self.co["kct_do"]]})
        return {"ma": 1, "ra": "ok", "crash": False}

    def _pipeline(self, out: Path, cmd) -> None:
        meta = self._meta(out)
        if "--topic" in cmd and not (out / "G0_checkpoint.json").exists():
            meta.update({"topic": cmd[cmd.index("--topic") + 1]})
            _ghi(out / "study_meta.json", meta)
            base = "hypertension treatment" if self.co["dich_lac"] else KB_THU["query_en"]
            cp0 = {"base_query": base, "n_pmids": 0 if self.co["g0_r1b"] else 5,
                   "guardrail": {"errors": ["R1B 🔴 truy vấn lỗi"] if self.co["g0_r1b"] else []}}
            _ghi(out / "G0_checkpoint.json", cp0)
            _ghi(out / "G0_pubmed_raw.json", {"n": 5})
        cp0 = _doc(out / "G0_checkpoint.json")
        if meta.get("query_en") and cp0.get("base_query") != meta["query_en"]:
            cp0["base_query"] = meta["query_en"]  # K5: tra lại vì đầu vào đổi
            if self.co["r1b_sau_query_en"]:  # tra lại hỏng giữa chừng (NCBI chặn) — base_query vẫn ghi truy vấn mới
                cp0.update({"n_pmids": 0, "guardrail": {"errors": ["R1B 🔴 truy vấn lỗi"]}})
            _ghi(out / "G0_checkpoint.json", cp0)
        ket = {"G0": "blocked_missing_input"}
        if self.cham("G0", "", out, None)["status"].startswith("PASS"):
            if not (out / "G1_checkpoint.json").exists():
                _ghi(out / "G1_checkpoint.json", {"design": {"internal_code": self.co["thiet_ke"]}})
            if not (out / "G3_checkpoint.json").exists() or not self.co["n4"]:
                cp3 = _doc(out / "G3_checkpoint.json")
                cp3["effect_val"] = self._gp(out, "G3").get("effect_size")
                _ghi(out / "G3_checkpoint.json", cp3)
            ket = {"G0": "skipped_fresh", "G1": "du_thao", "G2": "du_thao", "G3": "du_thao", "G4": "du_thao"}
            dung = self.co["cong_dung"]
            ket[dung] = "blocked_missing_input"
            for g in [f"G{i}" for i in range(int(dung[1:]) + 1, 11)]:
                ket.pop(g, None)
        _ghi(out / "pipeline_run_report.json", {"gate_results": [{"gate": g, "status": s} for g, s in ket.items()]})

    # ── bộ chấm sống giả
    def cham(self, gate, study, out, repo):
        out = Path(out)
        if gate in ("G2", "G4"):
            return {"status": "PASS_GX" if gate in self.co["cung_dat"] else "DRAFT_NEEDS_HUMAN"}
        if not (out / f"{gate}_checkpoint.json").exists():
            return {"status": "KHONG_DO_DUOC"}
        gp = self._gp(out, gate)
        auto, human = [], []
        if gate == "G1" and self.co["g1_can_chay_lai"] and not _doc(out / "G1_checkpoint.json").get("a2_theo_noi_dung"):
            auto.append({"id": "G1-AUTO-07", "status": "REVIEW", "evidence": "A2 còn trống", "action": ""})
        if gate == "G3" and gp.get("effect_size") is not None and \
                _doc(out / "G3_checkpoint.json").get("effect_val") != gp.get("effect_size"):
            auto.append({"id": "G3-AUTO-18", "status": "REVIEW", "evidence": "ghim ≠ checkpoint", "action": ""})
        if not self._xong_noi_dung(out, gate):
            human.append({"id": f"{gate}-HUMAN-01", "status": "REVIEW", "evidence": "thiếu nội dung", "action": ""})
        if gp.get("dau_van_tay_chot") != FP[gate]:
            human.append({"id": f"{gate}-HUMAN-07", "status": "REVIEW", "evidence": "chưa gắn dấu",
                          "action": f'Đặt reviewed_at và dau_van_tay_chot="{FP[gate]}" (dấu nội dung).'})
        if not auto and not human:
            return {"status": f"PASS_{gate}_CONFIRMED", "automatic_criteria": [], "human_criteria": []}
        return {"status": "DRAFT_READY_NEEDS_HUMAN_REVIEW", "automatic_criteria": auto, "human_criteria": human}


def _chay_kb(tmp_path, the_gioi: TheGioi, truc_tuyen=True, nen=None):
    repo = tmp_path / "repo"
    (repo / "exports").mkdir(parents=True, exist_ok=True)
    gl = GL.GiaLap("thu", KB_THU, repo, truc_tuyen, chay=the_gioi.chay, cham=the_gioi.cham,
                   nen_g0_dir=nen or (tmp_path / "nen"))
    return gl, gl.chay_kich_ban()


def _loai(kq):
    return [(c["cong"], c["loai"]) for c in kq["can_thiep"]]


# ═══════════════════════════════════════════════════════════════════════════════════ PI giả lập + khiếm khuyết
def test_luong_day_du_dem_can_thiep_va_khoa_khiem_khuyet(tmp_path):
    tg = TheGioi()
    _gl, kq = _chay_kb(tmp_path, tg)
    assert kq["do_duoc"] and kq["g0_do_duoc"]
    assert _loai(kq) == [("G0", "khai_query_en"), ("G0", "dien_noi_dung"), ("G0", "xac_nhan_dau_van_tay"),
                         ("G1", "dien_noi_dung"), ("G1", "xac_nhan_dau_van_tay"),
                         ("G3", "dien_noi_dung"), ("G3", "tu_chay_cong"), ("G3", "xac_nhan_dau_van_tay")]
    assert kq["so_can_thiep_do_may"] == 2 and kq["cong_dung"] == "G5" and kq["thiet_ke_may_suy"] == "rct"
    assert kq["khiem_khuyet"] == ["thu:can_thiep_do_may:G0:khai_query_en", "thu:can_thiep_do_may:G3:tu_chay_cong",
                                  "thu:kiem_chi_tiet_do:G1/④"]
    meta = _doc(tmp_path / "repo" / "exports" / "ZZCANARY-THU" / "study_meta.json")
    assert meta["gate_params"]["G0"]["dau_van_tay_chot"] == FP["G0"]
    assert meta["gate_params"]["G0"]["registry_manual_checked"]["ictrp"] != "<HOM_NAY>"
    assert all(x["nhan"] == GL.NHAN for x in meta["gia_lap_pi_dien"])
    assert "run_g3_auto.py" in tg.lenh


def test_he_da_sua_k4_n4_thi_khong_con_can_thiep_do_may(tmp_path):
    _gl, kq = _chay_kb(tmp_path, TheGioi(dich_lac=False, n4=False, kct_do=()))
    assert kq["so_can_thiep_do_may"] == 0
    assert kq["khiem_khuyet"] == []


def test_g1_khong_chay_lai_sau_noi_dung_la_can_thiep_do_may(tmp_path):
    _gl, kq = _chay_kb(tmp_path, TheGioi(dich_lac=False, n4=False, g1_can_chay_lai=True, kct_do=()))
    assert ("G1", "tu_chay_cong") in _loai(kq)
    assert kq["khiem_khuyet"] == ["thu:can_thiep_do_may:G1:tu_chay_cong"]


@pytest.mark.parametrize("co, khoa", [
    ({"cong_dung": "G2"}, "thu:dung_sai:G2"),
    ({"thiet_ke": "cross_sectional"}, "thu:thiet_ke_may_suy_sai:cross_sectional"),
    ({"cung_dat": ("G4",)}, "thu:cong_cung_dat_khi_chua_ky:G4"),
    ({"crash": True}, "thu:crash:pipeline"),
])
def test_moi_loai_khiem_khuyet_co_khoa_rieng(tmp_path, co, khoa):
    _gl, kq = _chay_kb(tmp_path, TheGioi(dich_lac=False, n4=False, kct_do=(), **co))
    assert khoa in kq["khiem_khuyet"], kq["khiem_khuyet"]


def test_dien_lap_lai_la_khiem_khuyet_can_thiep_lap():
    kq = {"do_duoc": True, "ma": "x", "thiet_ke": "rct", "cong_dung": "G5", "cong_dung_mong_doi": "G5",
          "can_thiep": [{"cong": "G1", "loai": "dien_noi_dung", "do_may": False},
                        {"cong": "G1", "loai": "dien_noi_dung", "do_may": False}]}
    assert GL.khiem_khuyet_kich_ban(kq) == ["x:can_thiep_lap:G1:dien_noi_dung"]


def test_khong_do_duoc_thi_khong_sinh_khoa_khiem_khuyet():
    assert GL.khiem_khuyet_kich_ban({"do_duoc": False, "ma": "x", "ket": "G0:abc", "crash": ["p"]}) == []


# ═══════════════════════════════════════════════════════════════════════════════════ thời gian trôi giữa hai lượt PI
def test_lui_thoi_gian_lui_moi_tep_dung_so_giay_va_giu_thu_tu(tmp_path):
    import os
    d = tmp_path / "de_tai"
    (d / "con").mkdir(parents=True)
    tep = {d / "G1_checkpoint.json": 1_000_000.0, d / "G3_checkpoint.json": 1_000_050.0,
           d / "con" / "a.md": 1_000_100.0}
    for p, t in tep.items():
        p.write_text("{}", encoding="utf-8", newline="\n")
        os.utime(p, (t, t))
    assert GL.lui_thoi_gian(d, 600) == 3
    for p, t in tep.items():
        assert p.stat().st_mtime == pytest.approx(t - 600), p.name
    # thứ tự và khoảng cách giữa các tệp không đổi ⇒ không tạo ra «cũ/mới» giả giữa các cổng
    assert (d / "G3_checkpoint.json").stat().st_mtime - (d / "G1_checkpoint.json").stat().st_mtime == \
        pytest.approx(50.0)
    assert GL.lui_thoi_gian(tmp_path / "khong-co", 600) == 0
    assert GL.GIAY_GIUA_HAI_LUOT_PI > 120, "phải lớn hơn hẳn dung sai «cùng đợt» 120 s của pipeline_freshness"


def test_moi_luot_pi_deu_lui_thoi_gian_truoc_khi_pi_lam(tmp_path, monkeypatch):
    """Dây nối: trước MỖI lượt PI (kể cả lượt cuối PI không còn việc) đề tài tạm được lùi thời gian một lần."""
    repo = tmp_path / "repo"
    (repo / "exports").mkdir(parents=True)
    tg = TheGioi()
    gl = GL.GiaLap("thu", KB_THU, repo, True, chay=tg.chay, cham=tg.cham, nen_g0_dir=tmp_path / "nen")
    goi: list = []

    def gian_diep(thu_muc, giay=GL.GIAY_GIUA_HAI_LUOT_PI):
        assert Path(thu_muc) == gl.out
        goi.append(len(gl.can_thiep))
        return 0

    monkeypatch.setattr(GL, "lui_thoi_gian", gian_diep)
    kq = gl.chay_kich_ban()
    assert kq["so_can_thiep"] == 8
    assert goi == list(range(kq["so_can_thiep"] + 1))


# ═══════════════════════════════════════════════════════════════════════════════════ G0 ngoại tuyến + nền G0
def test_ngoai_tuyen_chua_co_nen_g0_thi_kich_ban_khong_do_duoc(tmp_path):
    tg = TheGioi()
    _gl, kq = _chay_kb(tmp_path, tg, truc_tuyen=False)
    assert not kq["do_duoc"] and not kq["g0_do_duoc"]
    assert "run_pipeline.py" not in tg.lenh  # ngoại tuyến không chạy G0 bằng nguồn giả rồi gọi là đo
    assert any("ngoại tuyến" in g for g in kq["ghi_chu"])


def test_truc_tuyen_luu_nen_roi_ngoai_tuyen_dung_lai_nen(tmp_path):
    nen = tmp_path / "nen"
    _chay_kb(tmp_path / "lan1", TheGioi(), truc_tuyen=True, nen=nen)
    thong_tin = _doc(nen / "thu" / "_nen.json")
    assert thong_tin["base_query"] == KB_THU["query_en"] and (nen / "thu" / "G0_checkpoint.json").is_file()
    tg = TheGioi()
    _gl, kq = _chay_kb(tmp_path / "lan2", tg, truc_tuyen=False, nen=nen)
    assert kq["do_duoc"] and not kq["g0_do_duoc"] and kq["cong_dung"] == "G5"
    assert ("G0", "khai_query_en") not in _loai(kq)  # nền đã mang query_en PI khai
    assert any("nền lưu" in g for g in kq["ghi_chu"])


def test_truc_tuyen_g0_bi_r1b_thi_dung_nen_cu_va_ghi_khong_do_duoc(tmp_path):
    nen = tmp_path / "nen"
    _chay_kb(tmp_path / "lan1", TheGioi(), truc_tuyen=True, nen=nen)
    _gl, kq = _chay_kb(tmp_path / "lan2", TheGioi(g0_r1b=True), truc_tuyen=True, nen=nen)
    assert kq["do_duoc"] and not kq["g0_do_duoc"]
    assert any("mạng" in g for g in kq["ghi_chu"])


def test_nen_g0_khong_luu_khi_g0_bi_r1b(tmp_path):
    nen = tmp_path / "nen"
    _chay_kb(tmp_path, TheGioi(g0_r1b=True), truc_tuyen=True, nen=nen)
    assert not (nen / "thu" / "_nen.json").exists()


def test_tra_lai_theo_query_en_hong_thi_g0_khong_do_duoc_va_khong_luu_nen(tmp_path):
    """Tra lần đầu được, tra LẠI theo query_en bị NCBI chặn: lỗi mạng không được thành khiếm khuyết của hệ."""
    nen = tmp_path / "nen"
    _gl, kq = _chay_kb(tmp_path / "lan1", TheGioi(r1b_sau_query_en=True), truc_tuyen=True, nen=nen)
    assert not kq["do_duoc"] and not kq["g0_do_duoc"] and kq["khiem_khuyet"] == []
    assert any("tra lại theo query_en" in g for g in kq["ghi_chu"])
    assert not (nen / "thu" / "_nen.json").exists(), "không lưu nền G0 hỏng"
    # có nền cũ ⇒ dùng nền, vẫn đo được G1–G4 (G0 không đo được)
    _chay_kb(tmp_path / "lan2", TheGioi(), truc_tuyen=True, nen=nen)
    _gl, kq = _chay_kb(tmp_path / "lan3", TheGioi(r1b_sau_query_en=True), truc_tuyen=True, nen=nen)
    assert kq["do_duoc"] and not kq["g0_do_duoc"] and kq["cong_dung"] == "G5"
    assert not any(k.startswith("thu:ket:G0") or k == "thu:cong_mem_chua_dat:G0" for k in kq["khiem_khuyet"])


def test_luu_nen_g0_tu_choi_checkpoint_bi_r1b_hoac_khong_pmid(tmp_path):
    """Chốt trong luu_nen_g0 (phòng thủ thêm lớp — kể cả khi bị gọi thẳng): nền hỏng không bao giờ được lưu."""
    repo = tmp_path / "repo"
    gl = GL.GiaLap("thu", KB_THU, repo, True, nen_g0_dir=tmp_path / "nen")
    _ghi(gl.out / "study_meta.json", {"topic": "t", "query_en": "q"})
    for cp in ({"base_query": "q", "n_pmids": 5, "guardrail": {"errors": ["R1B 🔴 truy vấn lỗi"]}},
               {"base_query": "q", "n_pmids": 0}):
        _ghi(gl.out / "G0_checkpoint.json", cp)
        gl.luu_nen_g0()
        assert not (tmp_path / "nen" / "thu").exists(), cp
    _ghi(gl.out / "G0_checkpoint.json", {"base_query": "q", "n_pmids": 5, "guardrail": {"errors": []}})
    gl.luu_nen_g0()
    assert _doc(tmp_path / "nen" / "thu" / "_nen.json")["query_en"] == "q"


def test_moi_truong_ngoai_tuyen_bat_nguon_gia_lap_va_bo_bien_pytest(monkeypatch):
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw0")
    monkeypatch.setenv("USE_MOCK_SOURCES", "false")
    env = GL.moi_truong(truc_tuyen=False)
    assert env["USE_MOCK_SOURCES"] == "true" and env["PYTHONDONTWRITEBYTECODE"] == "1"
    assert not any(k.startswith("PYTEST_") for k in env)
    assert "USE_MOCK_SOURCES" not in GL.moi_truong(truc_tuyen=True)


# ═══════════════════════════════════════════════════════════════════════════════════ bản sao tạm
def test_ban_sao_la_ban_chep_that_khong_symlink_va_exports_rong(tmp_path):
    goc = tmp_path / "goc"
    (goc / "tools" / "__pycache__").mkdir(parents=True)
    (goc / "tools" / "run_pipeline.py").write_text("# giả\n", encoding="utf-8", newline="\n")
    (goc / "tools" / "__pycache__" / "x.pyc").write_bytes(b"\0")
    (goc / "app").mkdir()
    (goc / "app" / "a.py").write_text("", encoding="utf-8", newline="\n")
    (goc / "exports" / "de-tai-that").mkdir(parents=True)
    repo = GL.dung_ban_sao(goc, tmp_path / "tam")
    assert (repo / "tools" / "run_pipeline.py").is_file() and not (repo / "tools").is_symlink()
    assert not (repo / "tools" / "__pycache__").exists()
    assert list((repo / "exports").iterdir()) == []
    assert (repo / "tools" / "run_pipeline.py").resolve().parents[1] == repo.resolve()


def test_ro_ri_exports_that_la_khiem_khuyet(tmp_path):
    (tmp_path / "exports" / "ZZCANARY-RCT-NHI-PHAN").mkdir(parents=True)
    (tmp_path / "exports" / "de-tai-that").mkdir()
    assert GL._de_tai_canary_trong_exports(tmp_path) == ["ZZCANARY-RCT-NHI-PHAN"]
    bc = GL.tong_hop({}, {"do_duoc": True, "khiem_khuyet": []}, {}, "ngoai_tuyen", None, ["ZZCANARY-RCT-NHI-PHAN"],
                     du_kien=[])
    assert bc["moi"] == ["he:ro_ri_exports_that:ZZCANARY-RCT-NHI-PHAN"] and bc["ma_thoat"] == 1


# ═══════════════════════════════════════════════════════════════════════════════════ pytest + kiem_chi_tiet
def _chay_pytest_gia(noi_dung_xml):
    def chay(cmd, cwd, env, timeout=900):
        if noi_dung_xml is not None:
            duong = next(x.split("=", 1)[1] for x in cmd if x.startswith("--junitxml="))
            Path(duong).write_text(noi_dung_xml, encoding="utf-8", newline="\n")
        assert "-p" in cmd and "no:cacheprovider" in cmd and "-B" in cmd
        return {"ma": 1, "ra": "", "crash": False}
    return chay


def test_pytest_doc_junit_tung_test_hong_va_loi(tmp_path):
    xml = ('<testsuites><testsuite><testcase name="t[rct]"/><testcase name="t[cohort]"><failure/></testcase>'
           '<testcase name="t[qualitative]"><error/></testcase><testcase name="u"><skipped/></testcase>'
           '</testsuite></testsuites>')
    kq = GL.chay_pytest(tmp_path, tmp_path, chay=_chay_pytest_gia(xml))
    assert kq["do_duoc"] and kq["dat"] == 1 and kq["bo_qua"] == ["u"]
    assert kq["khiem_khuyet"] == ["pytest:hong:t[cohort]", "pytest:hong:t[qualitative]"]


def test_pytest_khong_co_junit_hoac_bo_qua_het_la_khong_do_duoc(tmp_path):
    assert not GL.chay_pytest(tmp_path, tmp_path, chay=_chay_pytest_gia(None))["do_duoc"]
    xml = '<testsuites><testsuite><testcase name="u"><skipped/></testcase></testsuite></testsuites>'
    assert not GL.chay_pytest(tmp_path, tmp_path, chay=_chay_pytest_gia(xml))["do_duoc"]


def test_dem_kiem_chi_tiet_theo_khuon_bao_cao_that():
    bao = {"tong": {"xanh": 40, "vang": 31, "do": 1, "trang": 1},
           "muc": [{"cong": "G1", "truc": "④", "muc": "🔴"}, {"cong": "G0", "truc": "①", "muc": "🟢"}]}
    assert GL.dem_kiem_chi_tiet(bao) == {"xanh": 40, "vang": 31, "do": 1, "trang": 1, "o_do": ["G1/④"]}


# ═══════════════════════════════════════════════════════════════════════════════════ so sánh + mã thoát + state
def _kb_kq(ma, khiem, do_duoc=True, g0=True):
    return {"ma": ma, "do_duoc": do_duoc, "g0_do_duoc": g0, "khiem_khuyet": khiem, "thiet_ke": "rct"}


def test_lan_dau_moi_khiem_khuyet_la_moi_lan_sau_chi_bao_cai_moi():
    pk = {"do_duoc": True, "khiem_khuyet": []}
    bc1 = GL.tong_hop({"a": _kb_kq("a", ["a:k1"])}, pk, {}, "truc_tuyen", None, [], du_kien=["a"])
    assert bc1["lan_dau"] and bc1["moi"] == ["a:k1"] and bc1["ma_thoat"] == 1
    bc2 = GL.tong_hop({"a": _kb_kq("a", ["a:k1"])}, pk, bc1, "truc_tuyen", None, [], du_kien=["a"])
    assert bc2["moi"] == [] and bc2["ma_thoat"] == 0
    bc3 = GL.tong_hop({"a": _kb_kq("a", ["a:k1", "a:k2"])}, pk, bc2, "truc_tuyen", None, [], du_kien=["a"])
    assert bc3["moi"] == ["a:k2"] and bc3["ma_thoat"] == 1
    bc4 = GL.tong_hop({"a": _kb_kq("a", [])}, pk, bc3, "truc_tuyen", None, [], du_kien=["a"])
    assert bc4["da_het"] == ["a:k1", "a:k2"] and bc4["ma_thoat"] == 0


def test_moc_tach_theo_che_do():
    pk = {"do_duoc": True, "khiem_khuyet": []}
    bc1 = GL.tong_hop({"a": _kb_kq("a", ["a:k1"])}, pk, {}, "truc_tuyen", None, [])
    bc2 = GL.tong_hop({"a": _kb_kq("a", ["a:k1"], g0=False)}, pk, bc1, "ngoai_tuyen", None, [])
    assert bc2["lan_dau"] and bc2["moi"] == ["a:k1"]
    assert set(bc2["theo_che_do"]) == {"truc_tuyen", "ngoai_tuyen"}


def test_phan_khong_do_duoc_giu_khoa_cu_khong_coi_la_da_het():
    pk = {"do_duoc": True, "khiem_khuyet": []}
    ab = ["a", "b"]
    bc1 = GL.tong_hop({"a": _kb_kq("a", ["a:k1"]), "b": _kb_kq("b", ["b:k9"])}, pk, {}, "truc_tuyen", None, [],
                      du_kien=ab)
    bc2 = GL.tong_hop({"a": _kb_kq("a", [], do_duoc=False), "b": _kb_kq("b", ["b:k9"])}, pk, bc1, "truc_tuyen",
                      None, [], du_kien=ab)
    assert bc2["da_het"] == [] and "a" in bc2["khong_do_duoc"] and bc2["ma_thoat"] == 2
    assert "a:k1" in bc2["theo_che_do"]["truc_tuyen"]["khiem_khuyet"]
    bc3 = GL.tong_hop({"a": _kb_kq("a", ["a:k1"]), "b": _kb_kq("b", ["b:k9"])}, pk, bc2, "truc_tuyen", None, [],
                      du_kien=ab)
    assert bc3["moi"] == [] and bc3["ma_thoat"] == 0  # đo lại được: khoá cũ không bị báo «mới»


@pytest.mark.parametrize("moi, khong_do, ma", [([], [], 0), (["x"], [], 1), ([], ["pytest"], 2),
                                               (["x"], ["pytest"], 1)])
def test_ma_thoat_moi_uu_tien_hon_khong_do_duoc(moi, khong_do, ma):
    assert GL.ma_thoat(moi, khong_do) == ma


def test_g0_ngoai_tuyen_va_bo_pytest_la_khong_do_duoc():
    bc = GL.tong_hop({"a": _kb_kq("a", [], g0=False)}, None, {}, "ngoai_tuyen", None, [], du_kien=["a"])
    assert bc["khong_do_duoc"] == ["a.G0", "pytest"] and bc["ma_thoat"] == 2


def test_doc_state_vang_hop_le_hong_thi_bao_loi(tmp_path):
    assert GL.doc_state(tmp_path / "khong-co.json") == ({}, None)
    p = tmp_path / "s.json"
    p.write_text("{hỏng", encoding="utf-8", newline="\n")
    st, loi = GL.doc_state(p)
    assert st == {} and "không đọc được" in loi


def test_main_ghi_state_va_doi_tep_hong(tmp_path, monkeypatch, capsys):
    state = tmp_path / "state" / "gia-lap.json"
    state.parent.mkdir()
    state.write_text("{hỏng", encoding="utf-8", newline="\n")
    monkeypatch.setattr(GL, "REPO_ROOT", tmp_path)

    class GiaLapGia:
        def __init__(self, ma, kb, repo, truc_tuyen, **kw):
            self.ma, self.kb = ma, kb

        def chay_kich_ban(self):
            return {"ma": self.ma, "thiet_ke": self.kb["thiet_ke"], "do_duoc": True, "g0_do_duoc": True,
                    "khiem_khuyet": [f"{self.ma}:can_thiep_do_may:G3:tu_chay_cong"], "can_thiep": [],
                    "so_can_thiep": 0, "so_can_thiep_do_may": 0, "cong_dung": "G5", "cong_dung_mong_doi": "G5",
                    "crash": [], "kiem_chi_tiet": {"do_duoc": False}, "ghi_chu": [], "buoc": []}

    monkeypatch.setattr(GL, "GiaLap", GiaLapGia)
    monkeypatch.setattr(GL, "chay_pytest", lambda goc, tam: {"do_duoc": True, "dat": 9, "hong": [],
                                                             "khiem_khuyet": []})
    tham = ["--truc-tuyen", "--state", str(state)]
    assert GL.main(tham) == 1
    assert list(state.parent.glob("gia-lap.hong-*.json")), "tệp state hỏng phải được dời, không ghi đè mất"
    bc = _doc(state)
    assert bc["moi"] == sorted(f"{ma}:can_thiep_do_may:G3:tu_chay_cong" for ma in GL.KICH_BAN) and bc["loi_moc"]
    assert GL.main(tham) == 0  # lần hai: không có gì mới
    assert "không có khiếm khuyết mới" in capsys.readouterr().out


# ─────────────────────────── thẩm định PR #259 (15/11/2026): «không đo được» không bao giờ thành «đã hết»/«xanh»
def test_thuoc_phan_cong_chi_lay_khoa_phu_thuoc_cong_cua_dung_kich_ban():
    phan = "rct.G0"
    for k in ("rct:can_thiep_do_may:G0:khai_query_en", "rct:kiem_chi_tiet_do:G0/①", "rct:cong_mem_chua_dat:G0",
              "rct:ket:G0:G0-HUMAN-07", "rct:dung_sai:G0"):
        assert GL.thuoc_phan(k, phan), k
    for k in ("rct:can_thiep_do_may:G3:tu_chay_cong", "rct:kiem_chi_tiet_do:G1/④", "cat:can_thiep_do_may:G0:x",
              "rct:dung_sai:G05", "rct:ket:G10:x"):
        assert not GL.thuoc_phan(k, phan), k
    assert GL.thuoc_phan("rct:bat_ky", "rct") and GL.thuoc_phan("pytest:hong:t", "pytest")
    assert not GL.thuoc_phan("rct2:x", "rct")


def test_g0_dung_nen_cu_thi_khoa_k4_giu_nguyen_qua_ba_luot(tmp_path):
    """Vấn đề cao của thẩm định: L1 trực tuyến có K4 → L2 G0 hỏng vì mạng (R1B), dùng nền cũ nên K4 không thể xuất hiện
    → L3 mạng tốt lại. Trước bản sửa: L2 in «✔️ đã hết» K4 và xoá khỏi mốc, L3 báo lại «🆕» (mã 1, 🛎 hồi quy giả)."""
    nen = tmp_path / "nen"
    pk = {"do_duoc": True, "khiem_khuyet": []}
    k4 = "thu:can_thiep_do_may:G0:khai_query_en"
    _g, kq1 = _chay_kb(tmp_path / "l1", TheGioi(n4=False, kct_do=()), True, nen)
    bc1 = GL.tong_hop({"thu": kq1}, pk, {}, "truc_tuyen", None, [], du_kien=["thu"])
    assert bc1["moi"] == [k4] and bc1["ma_thoat"] == 1
    _g, kq2 = _chay_kb(tmp_path / "l2", TheGioi(n4=False, kct_do=(), g0_r1b=True), True, nen)
    assert kq2["do_duoc"] and not kq2["g0_do_duoc"] and k4 not in kq2["khiem_khuyet"]
    bc2 = GL.tong_hop({"thu": kq2}, pk, bc1, "truc_tuyen", None, [], du_kien=["thu"])
    assert bc2["da_het"] == [] and bc2["ma_thoat"] == 2 and "thu.G0" in bc2["khong_do_duoc"]
    assert k4 in bc2["giu_lai"] and k4 in bc2["theo_che_do"]["truc_tuyen"]["khiem_khuyet"]
    _g, kq3 = _chay_kb(tmp_path / "l3", TheGioi(n4=False, kct_do=()), True, nen)
    bc3 = GL.tong_hop({"thu": kq3}, pk, bc2, "truc_tuyen", None, [], du_kien=["thu"])
    assert bc3["moi"] == [] and bc3["ma_thoat"] == 0


def test_g0_khong_do_duoc_van_bao_da_het_khoa_g1_g4_do_duoc():
    """Giữ khoá phụ thuộc G0 KHÔNG được che phần đo được: khoá G3 biến mất vẫn là «đã hết» khi G0 dùng nền."""
    pk = {"do_duoc": True, "khiem_khuyet": []}
    bc1 = GL.tong_hop({"a": _kb_kq("a", ["a:can_thiep_do_may:G0:khai_query_en", "a:can_thiep_do_may:G3:tu_chay_cong"])},
                      pk, {}, "truc_tuyen", None, [], du_kien=["a"])
    bc2 = GL.tong_hop({"a": _kb_kq("a", [], g0=False)}, pk, bc1, "truc_tuyen", None, [], du_kien=["a"])
    assert bc2["da_het"] == ["a:can_thiep_do_may:G3:tu_chay_cong"]
    assert bc2["giu_lai"] == ["a:can_thiep_do_may:G0:khai_query_en"]


def test_kich_ban_khong_chay_luot_nay_la_khong_do_duoc_va_giu_khoa():
    """Vấn đề vừa: mốc đủ {rct:k1, cat:k2} → chạy riêng rct. Trước bản sửa: mã 0 (xanh giả), da_het=['cat:k2']."""
    pk = {"do_duoc": True, "khiem_khuyet": []}
    du = ["rct", "cat"]
    bc1 = GL.tong_hop({"rct": _kb_kq("rct", ["rct:k1"]), "cat": _kb_kq("cat", ["cat:k2"])}, pk, {}, "truc_tuyen",
                      None, [], du_kien=du)
    bc2 = GL.tong_hop({"rct": _kb_kq("rct", ["rct:k1"])}, pk, bc1, "truc_tuyen", None, [], du_kien=du)
    assert bc2["ma_thoat"] == 2 and bc2["da_het"] == [] and bc2["khong_chay_luot_nay"] == ["cat"]
    assert "cat" in bc2["khong_do_duoc"] and "cat:k2" in bc2["theo_che_do"]["truc_tuyen"]["khiem_khuyet"]
    bc3 = GL.tong_hop({"rct": _kb_kq("rct", ["rct:k1"]), "cat": _kb_kq("cat", ["cat:k2"])}, pk, bc2, "truc_tuyen",
                      None, [], du_kien=du)
    assert bc3["moi"] == [] and bc3["ma_thoat"] == 0
    # mặc định du_kien = cả KICH_BAN thật
    assert set(GL.tong_hop({}, pk, {}, "truc_tuyen", None, [])["khong_chay_luot_nay"]) == set(GL.KICH_BAN)


class _GiaLapGia:
    """Thay GiaLap trong main: mỗi kịch bản trả một khoá cố định; `loi` = tập kịch bản ném lỗi nội bộ."""
    loi: set = set()

    def __init__(self, ma, kb, repo, truc_tuyen, **kw):
        self.ma, self.kb = ma, kb

    def chay_kich_ban(self):
        if self.ma in self.loi:
            raise TypeError("_recover_params() takes 2 positional arguments but 3 were given")
        return {"ma": self.ma, "thiet_ke": self.kb["thiet_ke"], "do_duoc": True, "g0_do_duoc": True,
                "khiem_khuyet": [f"{self.ma}:k"], "can_thiep": [], "so_can_thiep": 0, "so_can_thiep_do_may": 0,
                "cong_dung": "G5", "cong_dung_mong_doi": "G5", "crash": [], "kiem_chi_tiet": {"do_duoc": False},
                "ghi_chu": [], "buoc": []}


@pytest.fixture
def main_gia(tmp_path, monkeypatch):
    monkeypatch.setattr(GL, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(GL, "GiaLap", _GiaLapGia)
    monkeypatch.setattr(_GiaLapGia, "loi", set())
    monkeypatch.setattr(GL, "chay_pytest", lambda goc, tam: {"do_duoc": True, "dat": 9, "hong": [],
                                                             "khiem_khuyet": []})
    return tmp_path / "state" / "gl.json"


def test_main_chay_tap_con_tra_ma_2_va_giu_khoa_kich_ban_khong_chay(main_gia, capsys):
    tham = ["--truc-tuyen", "--state", str(main_gia)]
    assert GL.main(tham) == 1  # mốc đầu, đủ kịch bản
    assert GL.main(tham + ["--kich-ban", "rct_nhi_phan"]) == 2
    bc = _doc(main_gia)
    # 15/11/2026: KICH_BAN đủ 8 thiết kế — mọi kịch bản trừ rct_nhi_phan là «không chạy lượt này»
    assert bc["da_het"] == [] and set(bc["khong_chay_luot_nay"]) == set(GL.KICH_BAN) - {"rct_nhi_phan"}
    assert "cat_ngang_mo_ta:k" in bc["theo_che_do"]["truc_tuyen"]["khiem_khuyet"]
    assert "cat_ngang_mo_ta (không chạy lượt này)" in capsys.readouterr().out
    assert GL.main(tham) == 0  # chạy đủ lại: không có gì «🆕»


def test_loi_noi_bo_trong_kich_ban_la_khong_do_duoc_ma_2_khong_phai_1(main_gia, capsys):
    """Vấn đề thấp: ngoại lệ chưa bắt trong GiaLap từng làm Python thoát mã 1 = «khiếm khuyết MỚI» (🛎 giả)."""
    tham = ["--truc-tuyen", "--state", str(main_gia)]
    assert GL.main(tham) == 1
    _GiaLapGia.loi = {"cat_ngang_mo_ta"}
    assert GL.main(tham) == 2
    bc = _doc(main_gia)
    kq = bc["kich_ban"]["cat_ngang_mo_ta"]
    assert not kq["do_duoc"] and "TypeError" in kq["loi_noi_bo"] and bc["da_het"] == []
    assert "cat_ngang_mo_ta:k" in bc["theo_che_do"]["truc_tuyen"]["khiem_khuyet"]
    ra = capsys.readouterr().out
    assert "⚪ KHÔNG ĐO ĐƯỢC: cat_ngang_mo_ta — lỗi nội bộ của canary (TypeError" in ra


def test_loi_noi_bo_pytest_va_loi_ngoai_kich_ban_deu_tra_ma_2(main_gia, monkeypatch, capsys):
    def nem_loi(*a, **k):
        raise RuntimeError("hỏng")

    tham = ["--truc-tuyen", "--state", str(main_gia)]
    assert GL.main(tham) == 1
    monkeypatch.setattr(GL, "chay_pytest", nem_loi)
    assert GL.main(tham) == 2 and "pytest" in _doc(main_gia)["khong_do_duoc"]
    monkeypatch.setattr(GL, "tong_hop", nem_loi)
    assert GL.chay_an_toan(tham) == 2
    assert "⚪ KHÔNG ĐO ĐƯỢC: lỗi nội bộ của canary (RuntimeError: hỏng)" in capsys.readouterr().out
    nguon = (ROOT / "tools" / "gia_lap_dinh_ky.py").read_text(encoding="utf-8")
    assert "raise SystemExit(chay_an_toan())" in nguon.split('if __name__ == "__main__":', 1)[1]


def test_crash_dung_ngay_khong_chay_tiep_va_ghi_cong_mem_chua_dat(tmp_path):
    """Lỗ phủ D4: bỏ `if self.crash: break` thì vòng PI chạy tiếp sau crash và sinh khoá nhiễu `ket:G0:…`.
    Lỗ phủ D1: crash để lại cổng mềm chưa đạt mà PI không kẹt ⇒ phải có khoá `cong_mem_chua_dat`."""
    tg = TheGioi(dich_lac=False, n4=False, kct_do=(), crash=True)
    _gl, kq = _chay_kb(tmp_path, tg)
    assert tg.lenh.count("run_pipeline.py") == 1, tg.lenh  # không bước pipeline nào sau crash
    assert kq["can_thiep"] == [] and kq["ket"] is None
    assert not any(":ket:" in k for k in kq["khiem_khuyet"]), kq["khiem_khuyet"]
    assert {"thu:crash:pipeline", "thu:cong_mem_chua_dat:G0", "thu:cong_mem_chua_dat:G1",
            "thu:cong_mem_chua_dat:G3"} <= set(kq["khiem_khuyet"])


def test_cong_mem_khong_dat_cuoi_luot_ma_pi_khong_ket_la_khiem_khuyet(tmp_path):
    """Lỗ phủ D1: cổng mềm kịch bản không có nội dung PI (PI giả lập bỏ qua) kết thúc chưa đạt, ket rỗng — chỉ khoá
    `cong_mem_chua_dat` báo được."""
    kb = {**KB_THU, "pi": {g: v for g, v in KB_THU["pi"].items() if g != "G3"},
          "xac_nhan": {g: v for g, v in KB_THU["xac_nhan"].items() if g != "G3"}}
    tg = TheGioi(dich_lac=False, n4=False, kct_do=())
    repo = tmp_path / "repo"
    (repo / "exports").mkdir(parents=True)
    kq = GL.GiaLap("thu", kb, repo, True, chay=tg.chay, cham=tg.cham, nen_g0_dir=tmp_path / "nen").chay_kich_ban()
    assert kq["ket"] is None and kq["cham_song_cuoi"]["G3"] != "PASS"
    assert kq["khiem_khuyet"] == ["thu:cong_mem_chua_dat:G3"]


# ═══════════════════════════════════════════════════════════════════════════════════ ranh giới
def test_cong_cu_khong_goi_ky_cong_hay_danh_dau_synthetic():
    """Chốt trên DÒNG THI HÀNH: không hằng chuỗi nào (ngoài docstring) nhắc approve_gate/mark_study_synthetic."""
    cay = ast.parse((ROOT / "tools" / "gia_lap_dinh_ky.py").read_text(encoding="utf-8"))
    doc = {id(n.value) for n in ast.walk(cay) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)}
    chuoi = [n.value for n in ast.walk(cay) if isinstance(n, ast.Constant) and isinstance(n.value, str)
             and id(n) not in doc]
    assert not [s for s in chuoi if "approve_gate" in s or "mark_study_synthetic" in s or ".ebm-secrets" in s]


def test_kich_ban_du_khung_va_dung_ma_thiet_ke():
    assert {"rct_nhi_phan", "cat_ngang_mo_ta"} <= set(GL.KICH_BAN)
    for ma, kb in GL.KICH_BAN.items():
        assert kb["thiet_ke"] in GL.THIET_KE_TAM, ma
        assert kb["study"].startswith(GL.TIEN_TO_DE_TAI), ma
        assert set(kb["pi"]) <= set(GL.CONG_MEM) and set(kb["xac_nhan"]) == set(kb["pi"]), ma
        assert "dau_van_tay_chot" not in json.dumps(kb["pi"]), "dấu vân tay phải chép từ cổng lúc chạy"


# ─────────────────────────── giả lập 8 thiết kế (15/11/2026): tự chạy cổng không đổi gì · bộ biến nộp cùng G3
class TheGioiTieuChiKet(TheGioi):
    """G3 có một tiêu chí máy KHÔNG BAO GIỜ đạt (vd G3-AUTO-19 thiếu bộ biến): tự chạy cổng không đổi được gì."""

    def cham(self, gate, study, out, repo):
        bao = super().cham(gate, study, out, repo)
        if gate == "G3" and (Path(out) / "G3_checkpoint.json").exists():
            bao = dict(bao, status="DRAFT_READY_NEEDS_HUMAN_REVIEW",
                       automatic_criteria=[*(bao.get("automatic_criteria") or []),
                                           {"id": "G3-AUTO-19", "status": "REVIEW", "evidence": "thiếu ma trận",
                                            "action": ""}])
        return bao


def test_tu_chay_cong_khong_doi_tieu_chi_khong_tinh_la_loi_may_va_tieu_chi_ket_duoc_ghi(tmp_path):
    _gl, kq = _chay_kb(tmp_path, TheGioiTieuChiKet(dich_lac=False, n4=False, kct_do=()))
    loai = _loai(kq)
    assert ("G3", "tu_chay_cong_khong_doi") in loai and ("G3", "tu_chay_cong") not in loai, loai
    assert not any(k.endswith(":G3:tu_chay_cong") or "tu_chay_cong_khong_doi" in k for k in kq["khiem_khuyet"]), \
        kq["khiem_khuyet"]
    assert "thu:ket:G3:G3-AUTO-19" in kq["khiem_khuyet"] or "thu:cong_mem_chua_dat:G3" in kq["khiem_khuyet"], \
        kq["khiem_khuyet"]


def test_pi_nop_bo_bien_va_ma_tran_cung_noi_dung_g3(tmp_path):
    kb = dict(KB_THU, ho_so_bien={
        "bo_bien": [("record_id", "text", "Mã", "", "", "Phiếu"), ("kc", "radio", "Kết cục", "0, Không | 1, Có", "",
                                                                     "Phiếu")],
        "ma_tran": [("1", "Kết cục", "ket_cuc_chinh", "kc", "nhi_phan", "C1", "Phiếu", "§4")]})
    repo = tmp_path / "repo"
    (repo / "exports").mkdir(parents=True)
    tg = TheGioi(dich_lac=False, n4=False, kct_do=())
    gl = GL.GiaLap("thu", kb, repo, True, chay=tg.chay, cham=tg.cham, nen_g0_dir=tmp_path / "nen")
    out = repo / "exports" / kb["study"]
    out.mkdir(parents=True)
    assert not gl._noi_dung_da_dien("G3")
    gl._dien_noi_dung("G3")
    bo = (out / "_bo-bien-rieng.csv").read_text(encoding="utf-8").splitlines()
    mt = (out / "_ma-tran-muc-tieu-bien.csv").read_text(encoding="utf-8").splitlines()
    assert bo[0].startswith("Variable / Field Name,Form Name") and bo[2].startswith("kc,phieu,Phiếu,radio")
    assert mt[0] == ",".join(GL.COT_MA_TRAN) and mt[1].startswith("1,Kết cục,ket_cuc_chinh,kc,nhi_phan")


def test_moi_kich_ban_that_co_ho_so_bien_va_dung_mot_ket_cuc_chinh_tru_tong_quan():
    for ma, kb in GL.KICH_BAN.items():
        hs = kb.get("ho_so_bien")
        assert hs and hs["bo_bien"] and hs["ma_tran"], ma
        ten_bien = {b[0] for b in hs["bo_bien"]}
        assert all(d[3] in ten_bien for d in hs["ma_tran"]), ma  # ma trận chỉ trỏ biến có trong bộ biến
