"""run_pipeline báo TRUNG THỰC theo chấm sống + độ tươi theo NỘI DUNG (14/11/2026 — giả lập đề tài RCT, K2/K5/K7).

Ba khiếm khuyết đo được khi giả lập đề tài «tin nhắn nhắc uống thuốc — RCT» (báo cáo BAO-CAO-GIA-LAP-20261114.md):
  • K2 — pipeline in «✅ ok» cho G1–G4 chỉ vì mã thoát 0 + guardrail sạch, dù chấm sống là DỰ THẢO và đã có LỆCH CỨNG
    xuyên cổng (descriptive_precision ≠ superiority) — rồi dựng tiếp G2/G3/G4 trên nền lệch.
  • K7 — G1 (A2 «N tối thiểu …») và G2 (TRDS mục 17) CHÉP số N của G3 nhưng chạy trước G3; G3 đổi N 482→218 thì G2 vẫn
    «⏭️ đã tươi» và cùng một báo cáo in «✅ TƯƠI» lẫn «🔴 co_mau [218, 482]».
  • K5 — PI khai query_en rồi chạy run_pipeline thường: G0 (đang chờ PICO) chỉ được CHẤM LẠI, nền bằng chứng giữ truy
    vấn tự dịch lạc đề.

Mọi phép thử chạy trên thư mục tạm, KHÔNG mạng, KHÔNG chạy cổng thật: bước gọi cổng con (`_run_gate_once`) được thay
bằng cổng GIẢ mô phỏng đúng tác dụng lên tệp (ghi checkpoint, chép N…). Không ký gì, không đụng exports/ thật.
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import cong_song as CS  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_pipeline as RP  # noqa: E402

STUDY = "ZZTEST-PIPE-TRUNG-THUC"


# ───────────────────────────────────────────────────────────────────────────────────────────── đồ gá
def _ghi(p: Path, obj) -> None:
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def _thu_muc(tmp_path: Path) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    return out


def _cp(out: Path, gate: str, **kw) -> None:
    _ghi(out / f"{gate}_checkpoint.json", {"gate": gate, "study": STUDY, "guardrail": {"passed": True}, **kw})


def _trds17(out: Path, gia_tri) -> None:
    _ghi(out / f"G2_REGISTRATION_DRAFT_{STUDY}.json",
         {"items": [{"number": 17, "label": "Target Sample Size", "value": gia_tri}]})


def _a2(out: Path, n_min=None, n_hl=None) -> None:
    if n_min is None:
        than = "- Cỡ mẫu và power chính thức: [CẦN TÍNH Ở G3]\n"
    else:
        than = (f"Cỡ mẫu dự kiến: theo G3 (`G3_A4_SAMPLE_SIZE`, G3_checkpoint) — N tối thiểu {n_min}"
                + (f", N hiệu lực {n_hl}" if n_hl else "") + " (số lấy từ G3_checkpoint lúc sinh tệp)\n")
    (out / f"G1_A2_PROTOCOL_DESIGN_{STUDY}.md").write_text("# A2\n" + than, encoding="utf-8", newline="\n")


def _song(muc: str) -> dict:
    status = {"PASS": "PASS_GX_CONFIRMED", "DRAFT": "DRAFT_READY_NEEDS_HUMAN_REVIEW", "READY": "READY_FOR_SIGNATURE",
              "BLOCKED": "BLOCKED", RP.KHONG_DO_DUOC: RP.KHONG_DO_DUOC}[muc]
    return {"status": status, "muc": muc, "nguon": "song", "ly_do": "giả",
            "chan": ["GX-AUTO-02d: thiết kế trái loại câu hỏi"] if muc == "BLOCKED" else [],
            "cho": ["GX-AUTO-07"] if muc in ("DRAFT", "READY") else []}


def _cong_cua(cmd) -> str:
    ten = Path(cmd[1]).name
    if ten == "g0_quality_gate.py":
        return "G0-cham-lai"
    if ten == "run_g10_assemble.py":
        return "G10"
    return ten.replace("run_", "").replace("_auto.py", "").upper()


class _CongGia:
    """Cổng con GIẢ: ghi lại lệnh, mô phỏng tác dụng lên tệp theo kịch bản {cổng: hàm(out) -> mã thoát | mã thoát}.
    Cổng không có trong kịch bản ⇒ mã 2 (chờ input) — dừng chuỗi như cổng thật thiếu dữ kiện."""

    def __init__(self, out: Path, kich_ban: dict):
        self.out, self.kb, self.lenh, self.cmd = out, kich_ban, [], []

    def __call__(self, cmd, out_dir):
        gate = _cong_cua(cmd)
        self.lenh.append(gate)
        self.cmd.append(list(cmd))
        hd = self.kb.get(gate, GC.EXIT_BLOCKED)
        ma = hd(self.out) if callable(hd) else hd
        return {"exit_code": GC.EXIT_BLOCKED if ma is None else ma, "stdout_tail": f"giả {gate}", "stderr_tail": ""}


def _chay(tmp_path, monkeypatch, out, kich_ban, *, song=None, stale=(), topic=None, start=None):
    """Chạy orchestrate với cổng giả + freshness mtime cố định + (tuỳ chọn) chấm sống giả theo cổng."""
    gia = _CongGia(out, kich_ban)
    monkeypatch.setattr(RP, "BASE", tmp_path)
    monkeypatch.setattr(RP, "_run_gate_once", gia)
    monkeypatch.setattr(RP.FRESH, "stale_report", lambda out_dir: {
        "stale_gates": list(stale), "orphan_gates": [], "fresh": not stale, "issues": [],
        "checkpoints_present": []})
    if song is not None:
        monkeypatch.setattr(RP, "_cham_song", lambda gate, study, out_dir: _song(song.get(gate, "DRAFT")))
    bc = RP.orchestrate(STUDY, topic, 1, start, False)
    return gia, bc


def _theo_cong(bc) -> dict:
    """Kết quả CUỐI của từng cổng (lượt sau đè lượt trước)."""
    return {r["gate"]: r for r in bc["gate_results"]}


def _ghi_cp(gate, **kw):
    def hd(out):
        _cp(out, gate, **kw)
        return GC.EXIT_OK
    return hd


# ───────────────────────────────────────────────────────────────────────────────────────────── K2
def test_k2_ok_chi_khi_cham_song_pass_du_thao_in_dung_nhan(tmp_path, monkeypatch, capsys):
    out = _thu_muc(tmp_path)
    _cp(out, "G0", topic="chủ đề", base_query="q")
    gia, bc = _chay(tmp_path, monkeypatch, out,
                    {"G1": _ghi_cp("G1"), "G2": _ghi_cp("G2"), "G3": _ghi_cp("G3")},
                    song={"G0": "PASS", "G1": "DRAFT", "G2": "READY", "G3": "PASS"}, start="G1")
    kq = _theo_cong(bc)
    assert gia.lenh == ["G1", "G2", "G3", "G4"]
    assert kq["G1"]["status"] == "du_thao" and kq["G2"]["status"] == "du_thao", "exit 0 + guardrail sạch ≠ «đạt»"
    assert kq["G3"]["status"] == "ok"
    assert bc["n_ran"] == 3 and bc["n_dat"] == 1 and bc["n_du_thao"] == 2
    RP.print_summary(bc)
    ra = capsys.readouterr().out
    assert "☑️ G1: DỰ THẢO — cần người duyệt — DRAFT_READY_NEEDS_HUMAN_REVIEW" in ra
    assert "☑️ G2: sẵn sàng ký — chờ người ký" in ra
    assert "✅ G3: đạt" in ra
    assert "✅ G1" not in ra and "G1: ok" not in ra


def test_k2_cham_song_bi_chan_thi_dung_khong_dung_tiep(tmp_path, monkeypatch, capsys):
    out = _thu_muc(tmp_path)
    _cp(out, "G0", topic="chủ đề", base_query="q")
    gia, bc = _chay(tmp_path, monkeypatch, out, {"G1": _ghi_cp("G1"), "G2": _ghi_cp("G2")},
                    song={"G1": "BLOCKED"}, start="G1")
    kq = _theo_cong(bc)
    assert gia.lenh == ["G1"], "G1 chấm sống BLOCKED ⇒ không dựng G2 trên nền bị chặn"
    assert kq["G1"]["status"] == "chan_song" and "GX-AUTO-02d" in kq["G1"]["detail"]
    assert bc["n_blocked"] == 1
    RP.print_summary(bc)
    assert "🚧 G1: BỊ CHẶN theo chấm sống" in capsys.readouterr().out


def test_k2_cong_da_tuoi_ma_cham_song_bi_chan_thi_khong_chay_cong_sau(tmp_path, monkeypatch):
    out = _thu_muc(tmp_path)
    _cp(out, "G0", topic="chủ đề", base_query="q")
    _cp(out, "G1")
    gia, bc = _chay(tmp_path, monkeypatch, out, {"G2": _ghi_cp("G2")}, song={"G0": "PASS", "G1": "BLOCKED"})
    kq = _theo_cong(bc)
    assert gia.lenh == []
    assert kq["G1"]["status"] == "skipped_fresh" and kq["G1"]["song"]["muc"] == "BLOCKED"
    assert kq["G2"]["status"] == "dung_nen_bi_chan" and "G1" in kq["G2"]["detail"]


def test_k2_khong_do_duoc_khong_bao_gio_la_ok(tmp_path, monkeypatch):
    out = _thu_muc(tmp_path)
    _cp(out, "G0", topic="chủ đề", base_query="q")

    def hong(*a, **k):
        raise RuntimeError("bộ chấm hỏng")

    monkeypatch.setattr(CS, "trang_thai_song", hong)
    gia, bc = _chay(tmp_path, monkeypatch, out, {"G1": _ghi_cp("G1")}, start="G1")
    kq = _theo_cong(bc)
    assert kq["G1"]["status"] == "khong_do_duoc" and kq["G1"]["song"]["muc"] == RP.KHONG_DO_DUOC
    assert gia.lenh == ["G1", "G2"], "không đo được ≠ có vấn đề: chuỗi vẫn đi tiếp (nhưng không in «đạt»)"
    assert bc["n_dat"] == 0


def test_k2_cham_song_doc_dung_cong_song_va_tom_tieu_chi(tmp_path, monkeypatch):
    goi = {}

    def gia(gate, study, out_dir, repo_root=None):
        goi.update(gate=gate, study=study, repo_root=repo_root)
        return {"status": "BLOCKED", "muc": "BLOCKED", "nguon": "song", "ly_do": "chấm sống",
                "bao_cao": {"automatic_criteria": [
                    {"id": "G1-AUTO-02d", "status": "BLOCK", "label": "thiết kế trái loại câu hỏi đã chốt"},
                    {"id": "G1-AUTO-07", "status": "REVIEW", "label": "x"}],
                    "human_criteria": [{"id": "G1-HUMAN-01", "status": "PASS"}]}}

    monkeypatch.setattr(RP, "BASE", tmp_path)
    monkeypatch.setattr(CS, "trang_thai_song", gia)
    s = RP._cham_song("G1", STUDY, tmp_path)
    assert goi == {"gate": "G1", "study": STUDY, "repo_root": tmp_path}
    assert s["muc"] == "BLOCKED" and s["chan"] == ["G1-AUTO-02d: thiết kế trái loại câu hỏi đã chốt"]
    assert s["cho"] == ["G1-AUTO-07"]
    assert RP._trang_thai_theo_song(s) == "chan_song"
    assert [RP._trang_thai_theo_song({"muc": m}) for m in ("PASS", "DRAFT", "READY", RP.KHONG_DO_DUOC, None)] == [
        "ok", "du_thao", "du_thao", "khong_do_duoc", "khong_do_duoc"]


def test_k2_lech_cung_xuyen_cong_o_cong_truoc_thi_dung_truoc_khi_chay(tmp_path, monkeypatch, capsys):
    """PI ghim design_code=rct nhưng G1 (đã tươi theo mtime) vẫn mang thiết kế cắt ngang ⇒ KHÔNG dựng G2 trên nền đó.
    Dùng nhat_quan_xuyen_cong THẬT."""
    out = _thu_muc(tmp_path)
    _ghi(out / "study_meta.json", {"design_code": "rct"})
    _cp(out, "G0", topic="chủ đề", base_query="q")
    _cp(out, "G1", design={"internal_code": "cross_sectional"})
    gia, bc = _chay(tmp_path, monkeypatch, out, {"G2": _ghi_cp("G2", design_code="rct")},
                    song={"G0": "PASS", "G1": "PASS"})
    kq = _theo_cong(bc)
    assert gia.lenh == [], "lệch cứng ở các cổng phía trước ⇒ không chạy G2"
    assert kq["G2"]["status"] == "dung_lech_xuyen_cong"
    assert [k["ma"] for k in kq["G2"]["lech"]] == ["thiet_ke"]
    assert bc["n_blocked"] == 1 and bc["converged_fresh"] is False
    RP.print_summary(bc)
    ra = capsys.readouterr().out
    assert "⛔ DỪNG trước G2" in ra and "thiet_ke" in ra and "✅ TƯƠI" not in ra


def test_k2_lech_chi_dinh_cong_sap_dung_lai_thi_khong_dung(tmp_path, monkeypatch):
    """Lệch có dính cổng ≥ cổng sắp chạy (G3 cũ mang thiết kế khác) thì CHƯA chặn: G3 sắp được dựng lại."""
    out = _thu_muc(tmp_path)
    _ghi(out / "study_meta.json", {"design_code": "rct"})
    _cp(out, "G0", topic="chủ đề", base_query="q")
    _cp(out, "G1", design={"internal_code": "rct"})
    _cp(out, "G3", design_code="cross_sectional")
    gia, bc = _chay(tmp_path, monkeypatch, out, {"G2": _ghi_cp("G2", design_code="rct")},
                    song={"G0": "PASS", "G1": "PASS"})
    assert gia.lenh == ["G2", "G3"], "nền G0–G2 nhất quán ⇒ G3 được chạy lại (dù G3 cũ đang lệch)"
    assert not any(r["status"] == "dung_lech_xuyen_cong" for r in bc["gate_results"])


def test_k2_lech_cung_truoc_chi_xet_nguon_truoc_vi_tri():
    ket = {"thong_so": [{"ma": "co_mau", "muc": "lech_cung", "ghi_chu": "2 giá trị",
                         "nguon": [{"cong": "G2", "noi": "TRDS 17", "gia_tri": 482},
                                   {"cong": "G3", "noi": "G3_checkpoint.n_adjusted", "gia_tri": 218},
                                   {"cong": "G4", "noi": "SAP §12", "gia_tri": 218}]}]}
    assert RP._lech_cung_truoc(ket, RP.GATE_ORDER.index("G3")) == [], "trước G3 chỉ còn một nguồn"
    assert [k["ma"] for k in RP._lech_cung_truoc(ket, RP.GATE_ORDER.index("G4"))] == ["co_mau"]
    ket2 = {"thong_so": [{"ma": "co_mau", "muc": "lech_cung", "ghi_chu": "",
                          "nguon": [{"cong": "G3", "noi": "a", "gia_tri": 218},
                                    {"cong": "G3", "noi": "b", "gia_tri": 218},
                                    {"cong": "G4", "noi": "SAP §12", "gia_tri": 482}]}]}
    assert RP._lech_cung_truoc(ket2, RP.GATE_ORDER.index("G4")) == [], "lệch chỉ ở SAP (G4 sắp dựng lại)"
    assert RP._lech_cung_truoc(None, 5) == [], "không đo được ⇒ không báo đỏ giả"


# ───────────────────────────────────────────────────────────────────────────────────────────── K7
def test_k7_bang_phu_thuoc_noi_dung_co_g1_va_g2():
    assert set(RP.PHU_THUOC_CO_MAU_G3) == {"G1", "G2"}


def test_k7_phat_hien_ban_chep_n_lech_g3(tmp_path):
    out = _thu_muc(tmp_path)
    _cp(out, "G3", n_adjusted=218)
    _trds17(out, 482)
    _a2(out, 482)
    lech = RP._lech_co_mau_g3(out, STUDY)
    assert set(lech) == {"G1", "G2"}
    assert "482" in lech["G2"] and "218" in lech["G2"] and "482" in lech["G1"]
    _trds17(out, 218)
    _a2(out, 218)
    assert RP._lech_co_mau_g3(out, STUDY) == {}
    # confirmed_n: G2 phải chép N hiệu lực; A2 phải có «N hiệu lực».
    _cp(out, "G3", n_adjusted=218, confirmed_n=240)
    assert set(RP._lech_co_mau_g3(out, STUDY)) == {"G1", "G2"}
    _trds17(out, 240)
    _a2(out, 218, 240)
    assert RP._lech_co_mau_g3(out, STUDY) == {}


def test_k7_o_mau_va_g3_chan_khong_bao_nham(tmp_path):
    out = _thu_muc(tmp_path)
    _cp(out, "G3", n_adjusted=218)
    _trds17(out, "[CẦN — chờ kết quả G3]")   # chữ số «3» của «G3» không phải cỡ mẫu
    _a2(out)                                  # A2 sinh trước G3: «[CẦN TÍNH Ở G3]»
    assert RP._lech_co_mau_g3(out, STUDY) == {}
    _trds17(out, "482")
    assert set(RP._lech_co_mau_g3(out, STUDY)) == {"G2"}, "chuỗi số thuần vẫn đem so"
    _cp(out, "G3", n_adjusted=218, needs_input={"blocked": True, "reason_code": "X", "human_message": "chờ"})
    assert RP._lech_co_mau_g3(out, STUDY) == {}, "G3 đang chặn ⇒ không có N sống để so"
    assert RP._so_nguyen_duong("1.000") == 1000 and RP._so_nguyen_duong("[CẦN — từ G3]") is None


def _g3_ghi(n):
    def hd(out):
        _cp(out, "G3", n_adjusted=n)
        return GC.EXIT_OK
    return hd


def _g1_chep(out):
    _a2(out, json.loads((out / "G3_checkpoint.json").read_text(encoding="utf-8"))["n_adjusted"])
    _cp(out, "G1")
    return GC.EXIT_OK


def _g2_chep(out):
    _trds17(out, json.loads((out / "G3_checkpoint.json").read_text(encoding="utf-8"))["n_adjusted"])
    _cp(out, "G2")
    return GC.EXIT_OK


def _ba_cong_dau(out, n):
    _cp(out, "G0", topic="chủ đề", base_query="q")
    _cp(out, "G1")
    _cp(out, "G2")
    _cp(out, "G3", n_adjusted=n)


def test_k7_ban_chep_lech_truoc_luot_thi_cong_do_cu_va_duoc_chay_lai(tmp_path, monkeypatch, capsys):
    out = _thu_muc(tmp_path)
    _ba_cong_dau(out, 218)
    _trds17(out, 482)
    _a2(out, 482)
    gia, bc = _chay(tmp_path, monkeypatch, out, {"G1": _g1_chep, "G2": _g2_chep, "G3": _g3_ghi(218)},
                    song={"G0": "PASS"})
    assert gia.lenh == ["G1", "G2", "G3", "G4"], "mtime nói «tươi» nhưng bản chép N lệch ⇒ G1 cũ, chạy lại"
    g1 = _theo_cong(bc)["G1"]
    assert "482" in g1["ly_do_chay_lai"] and "218" in g1["ly_do_chay_lai"]
    assert bc["lech_co_mau_g3"] == {} and not any(r["status"] == "quay_lai_dong_bo_n" for r in bc["gate_results"])
    RP.print_summary(bc)
    assert "↳ chạy lại vì: bản chép N lệch G3" in capsys.readouterr().out


def test_k7_g3_doi_n_giua_luot_thi_quay_lai_dong_bo_mot_lan(tmp_path, monkeypatch):
    out = _thu_muc(tmp_path)
    _ba_cong_dau(out, 482)
    _trds17(out, 482)
    _a2(out, 482)
    gia, bc = _chay(tmp_path, monkeypatch, out, {"G1": _g1_chep, "G2": _g2_chep, "G3": _g3_ghi(218)},
                    song={"G0": "PASS"}, stale=("G3",))
    assert gia.lenh == ["G3", "G1", "G2", "G3", "G4"]
    assert [r["status"] for r in bc["gate_results"]].count("quay_lai_dong_bo_n") == 1
    assert _theo_cong(bc)["G1"]["vong"] == 2
    assert bc["lech_co_mau_g3"] == {}
    assert "N tối thiểu 218" in (out / f"G1_A2_PROTOCOL_DESIGN_{STUDY}.md").read_text(encoding="utf-8")


def test_k7_quay_lai_toi_da_mot_lan_roi_dung_neu_van_lech(tmp_path, monkeypatch, capsys):
    """Cổng chép N không cập nhật được (vd giữ hồ sơ đã biên tập) ⇒ quay lại ĐÚNG một lần, rồi DỪNG trước G4 vì lệch
    cứng xuyên cổng (nhat_quan_xuyen_cong thật) — báo cáo không in «TƯƠI»."""
    out = _thu_muc(tmp_path)
    _ba_cong_dau(out, 482)
    _trds17(out, 482)
    _a2(out, 482)
    gia, bc = _chay(tmp_path, monkeypatch, out, {"G1": _ghi_cp("G1"), "G2": _ghi_cp("G2"), "G3": _g3_ghi(218)},
                    song={"G0": "PASS"}, stale=("G3",))
    assert gia.lenh == ["G3", "G1", "G2", "G3"], "không vòng lặp: chỉ một lượt quay lại"
    assert [r["status"] for r in bc["gate_results"]].count("quay_lai_dong_bo_n") == 1
    g4 = _theo_cong(bc)["G4"]
    assert g4["status"] == "dung_lech_xuyen_cong" and [k["ma"] for k in g4["lech"]] == ["co_mau"]
    assert set(bc["lech_co_mau_g3"]) == {"G1", "G2"}
    assert bc["converged_fresh"] is False
    loai = {i["kind"] for i in bc["do_tuoi_tong_hop"]["issues"]}
    assert {"lech_noi_dung", "lech_cung_xuyen_cong"} <= loai
    RP.print_summary(bc)
    ra = capsys.readouterr().out
    assert "✅ TƯƠI" not in ra and "CHƯA TƯƠI" in ra


def test_k7_do_tuoi_tong_hop_khong_tuoi_khi_lech_cung_du_mtime_tuoi(capsys):
    tuoi = {"fresh": True, "issues": [], "stale_gates": [], "orphan_gates": [], "checkpoints_present": ["G3"]}
    nq = {"tong": {"lech_cung": 1}, "lech": [{"ma": "co_mau", "muc": "lech_cung", "ghi_chu": "[218, 482]"}]}
    th = RP._do_tuoi_tong_hop(tuoi, {}, None, nq)
    assert th["fresh"] is False and th["issues"][0]["kind"] == "lech_cung_xuyen_cong"
    RP._in_do_tuoi(th, "Freshness sau")
    ra = capsys.readouterr().out
    assert "✅ TƯƠI" not in ra and "co_mau" in ra
    assert RP._do_tuoi_tong_hop(tuoi, {}, None, {"tong": {}, "lech": []})["fresh"] is True
    assert RP._do_tuoi_tong_hop(tuoi, {"G2": "TRDS 17 ghi N=482"}, None, {})["fresh"] is False
    # THAY ĐỔI ĐẶC TẢ CÓ CHỦ Ý (thẩm định PR #247, CLAUDE.md §0.2): bản đầu khẳng định NQ không đo được vẫn fresh=True
    # và in «✅ TƯƠI» kèm chú thích ⚪ — tức «không đo được» bị báo xanh (mã thoát 0). Nay: fresh=False, ket_luan
    # «khong_ket_luan», in «⚪ CHƯA KẾT LUẬN ĐƯỢC», không «TƯƠI»; cũng không thành «vấn đề» (không báo đỏ giả).
    khong_do = RP._do_tuoi_tong_hop(tuoi, {}, None, {"loi": "hỏng"})
    assert khong_do["fresh"] is False and khong_do["nhat_quan_do_duoc"] is False
    assert khong_do["ket_luan"] == "khong_ket_luan" and khong_do["issues"] == []
    RP._in_do_tuoi(khong_do, "Freshness sau")
    ra = capsys.readouterr().out
    assert "⚪ CHƯA KẾT LUẬN ĐƯỢC" in ra and "hỏng" in ra and "✅ TƯƠI" not in ra
    # Có vấn đề thật + NQ không đo được ⇒ «CHƯA TƯƠI» và vẫn nêu phần ⚪.
    ca_hai = RP._do_tuoi_tong_hop(tuoi, {"G2": "TRDS 17 ghi N=482"}, None, {"loi": "hỏng"})
    assert ca_hai["ket_luan"] == "chua_tuoi"
    RP._in_do_tuoi(ca_hai, "Freshness sau")
    ra = capsys.readouterr().out
    assert "CHƯA TƯƠI" in ra and "KHÔNG ĐO ĐƯỢC" in ra


def test_k7_check_only_bao_ban_chep_lech_va_ma_thoat_1(tmp_path, monkeypatch, capsys):
    out = _thu_muc(tmp_path)
    _ba_cong_dau(out, 218)
    _a2(out, 482)
    monkeypatch.setattr(RP, "BASE", tmp_path)
    monkeypatch.setattr(RP.FRESH, "stale_report", lambda out_dir: {
        "stale_gates": [], "orphan_gates": [], "fresh": True, "issues": [], "checkpoints_present": ["G0", "G3"]})
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "--study", STUDY, "--check-only"])
    assert RP.main() == 1
    ra = capsys.readouterr().out
    assert "lech_noi_dung" in ra and "✅ TƯƠI" not in ra


# ───────────────────────────────────────────────────────────────────────────────────────────── K5
def _g0_cho_pico(out: Path, base_query="hypertension treatment", topic="Tin nhắn nhắc uống thuốc ở người THA"):
    _cp(out, "G0", topic=topic, base_query=base_query, n_pmids=57,
        needs_input={"blocked": True, "reason_code": GC.REASON_MISSING_PICO, "human_message": "chờ PICO"})
    (out / "G0_pubmed_raw.json").write_text("{}", encoding="utf-8", newline="\n")


def test_k5_query_en_doi_thi_tra_lai_pubmed_khong_chi_cham_lai(tmp_path, monkeypatch):
    out = _thu_muc(tmp_path)
    _g0_cho_pico(out)
    moi = '("text messaging"[tiab] OR SMS[tiab]) AND hypertension[MeSH]'
    _ghi(out / "study_meta.json", {"query_en": moi})
    gia, bc = _chay(tmp_path, monkeypatch, out, {})
    assert gia.lenh == ["G0"], "query_en đổi ⇒ chạy trọn run_g0_auto.py, không phải g0_quality_gate.py"
    cmd = gia.cmd[0]
    assert cmd[cmd.index("--query-en") + 1] == moi
    assert "query_en" in bc["gate_results"][0]["ly_do_chay_lai"]


def test_k5_gate_params_g0_query_en_uu_tien_va_bo_o_mau(tmp_path):
    assert RP._query_en_mong_muon({"query_en": "Y", "gate_params": {"G0": {"query_en": "X"}}}) == (
        "X", "study_meta.gate_params.G0.query_en")
    assert RP._query_en_mong_muon({"query_en": "Y", "gate_params": {"G0": {"query_en": "<từ khóa PubMed>"}}}) == (
        "Y", "study_meta.query_en")
    assert RP._query_en_mong_muon({"query_en": "[CẦN BÁC SĨ]"}) == (None, "")
    out = _thu_muc(tmp_path)
    _g0_cho_pico(out)
    assert "gate_params.G0.query_en" in RP._g0_lech_dau_vao(out, None, {"gate_params": {"G0": {"query_en": "X"}}})
    cmd = RP._build_cmd("G0", STUDY, out, None, {"gate_params": {"G0": {"query_en": "X"}}})
    assert cmd[cmd.index("--query-en") + 1] == "X"


def test_k5_query_en_trung_chi_khac_khoang_trang_van_chi_cham_lai(tmp_path, monkeypatch):
    out = _thu_muc(tmp_path)
    _g0_cho_pico(out, base_query='("text messaging"[tiab]) AND hypertension')
    _ghi(out / "study_meta.json", {"query_en": '  ("text messaging"[tiab])   AND\nhypertension '})
    gia, bc = _chay(tmp_path, monkeypatch, out, {})
    assert gia.lenh == ["G0-cham-lai"], "cùng truy vấn ⇒ giữ nền bằng chứng, chỉ chấm lại"
    assert RP._g0_lech_dau_vao(out, None, _load(out)) is None


def _load(out: Path) -> dict:
    return json.loads((out / "study_meta.json").read_text(encoding="utf-8"))


def test_k5_topic_moi_thi_tra_lai_topic_cu_thi_khong(tmp_path, monkeypatch):
    out = _thu_muc(tmp_path)
    _g0_cho_pico(out)
    gia, bc = _chay(tmp_path, monkeypatch, out, {}, topic="Tin nhắn nhắc uống thuốc ở người THA")
    assert gia.lenh == ["G0-cham-lai"]
    gia, bc = _chay(tmp_path, monkeypatch, out, {}, topic="Ứng dụng điện thoại nhắc thuốc ở người THA")
    assert gia.lenh == ["G0"]
    assert gia.cmd[0][gia.cmd[0].index("--topic") + 1] == "Ứng dụng điện thoại nhắc thuốc ở người THA"
    assert "--topic mới" in bc["gate_results"][0]["ly_do_chay_lai"]


def test_k5_g0_da_chot_ma_query_en_doi_cung_tra_lai(tmp_path, monkeypatch):
    out = _thu_muc(tmp_path)
    _cp(out, "G0", topic="chủ đề", base_query="old query")
    _ghi(out / "study_meta.json", {"query_en": "new query"})
    gia, _bc = _chay(tmp_path, monkeypatch, out, {}, song={"G0": "PASS"})
    assert gia.lenh == ["G0"], "G0 không chặn, mtime tươi — nhưng truy vấn đã đổi ⇒ tra lại"


@pytest.mark.parametrize("meta", [{}, {"query_en": "<từ khóa PubMed tiếng Anh>"},
                                  {"query_en": "hypertension treatment"}])
def test_k5_khong_khai_hoac_trung_thi_khong_tra_lai(tmp_path, meta):
    out = _thu_muc(tmp_path)
    _g0_cho_pico(out)
    assert RP._g0_lech_dau_vao(out, None, meta) is None


def test_k7_cong_cung_da_ky_khong_tu_sinh_lai_chi_bao(tmp_path, monkeypatch, capsys):
    """G2 đã ký (chấm sống PASS) mà TRDS 17 lệch N mới của G3 ⇒ KHÔNG tự sinh lại G2 (luật mới không hạ cấp quyết định
    đã ký); báo «bản chép N lệch — cổng ĐÃ KÝ», không in «TƯƠI», và không dựng G4 trên nền lệch."""
    assert "G2" in GC._GATE_REQUIRED_STAKEHOLDERS
    out = _thu_muc(tmp_path)
    _ba_cong_dau(out, 218)
    _trds17(out, 482)
    _a2(out, 218)
    gia, bc = _chay(tmp_path, monkeypatch, out, {"G2": _g2_chep, "G4": _ghi_cp("G4")},
                    song={"G0": "PASS", "G1": "PASS", "G2": "PASS", "G3": "PASS"})
    assert "G2" not in gia.lenh, "cổng cứng đã ký không bị luật K7 tự sinh lại"
    assert "ĐÃ KÝ" in bc["lech_co_mau_g3"]["G2"]
    assert bc["converged_fresh"] is False
    assert _theo_cong(bc)["G4"]["status"] == "dung_lech_xuyen_cong"
    RP.print_summary(bc)
    ra = capsys.readouterr().out
    assert "ĐÃ KÝ" in ra and "✅ TƯƠI" not in ra
    # Cùng tình huống nhưng G2 CHƯA ký (dự thảo) ⇒ được tự chạy lại.
    gia2, _bc2 = _chay(tmp_path, monkeypatch, out, {"G2": _g2_chep, "G3": _g3_ghi(218)},
                       song={"G0": "PASS", "G1": "PASS", "G2": "DRAFT", "G3": "PASS"})
    assert gia2.lenh[0] == "G2"


# ─────────────────────────────────────── Sửa sau thẩm định PR #247 — rào cổng ĐÃ KÝ phải giữ qua đường dây chuyền
# Thẩm định đo: G2 ĐÃ KÝ (chấm sống PASS) + TRDS 17 lệch + A2 CŨNG lệch (hai bản chép thường lệch cùng nhau vì cùng chép
# N lúc sinh) ⇒ G1 (cổng mềm) được chạy lại ⇒ dirty ⇒ run_g2_auto chạy lại trên G2 đã ký, ghi đè hồ sơ đã ký (TRDS 17
# thành 218). Rào cũ chỉ loại chính G2 khỏi stale_set nên bị vượt qua đường dây chuyền. Nay: cổng CỨNG đã ký KHÔNG bị
# sinh lại vì bất kỳ lý do TỰ ĐỘNG nào (dây chuyền, cũ theo mtime, bản chép N) — chỉ khi người gọi `--from` ĐÚNG
# cổng đó.
def _trds17_hien(out: Path):
    return json.loads((out / f"G2_REGISTRATION_DRAFT_{STUDY}.json").read_text(encoding="utf-8"))["items"][0]["value"]


_SONG_G2_DA_KY = {"G0": "PASS", "G1": "PASS", "G2": "PASS", "G3": "PASS"}


def test_k7_rao_da_ky_a_a2_cung_lech_g2_khong_bi_chay_lai_qua_day_chuyen(tmp_path, monkeypatch, capsys):
    """(a) G2 PASS + TRDS17 lệch + A2 lệch, mtime tươi: G1 chạy lại (A2) nhưng G2 đã ký KHÔNG có trong lệnh cổng con."""
    out = _thu_muc(tmp_path)
    _ba_cong_dau(out, 218)
    _trds17(out, 482)
    _a2(out, 482)
    gia, bc = _chay(tmp_path, monkeypatch, out,
                    {"G1": _g1_chep, "G2": _g2_chep, "G3": _g3_ghi(218), "G4": _ghi_cp("G4")}, song=_SONG_G2_DA_KY)
    assert "G2" not in gia.lenh, "cổng cứng đã ký không bị sinh lại qua dây chuyền G1 → G2"
    assert gia.lenh == ["G1", "G3"]
    assert _trds17_hien(out) == 482, "hồ sơ đã ký giữ nguyên"
    kq = _theo_cong(bc)
    assert kq["G2"]["status"] == "giu_cong_da_ky" and "ĐÃ KÝ" in kq["G2"]["detail"]
    assert "--from G2" in kq["G2"]["detail"], "nêu đường sinh lại CÓ CHỦ Ý cho PI"
    assert kq["G4"]["status"] == "dung_lech_xuyen_cong", "không dựng G4 trên nền G2(482) ≠ G3(218)"
    assert bc["n_giu_da_ky"] == 1 and bc["converged_fresh"] is False
    assert "giu_cong_da_ky" in {i["kind"] for i in bc["do_tuoi_tong_hop"]["issues"]}
    RP.print_summary(bc)
    ra = capsys.readouterr().out
    assert "🔏 G2: GIỮ — cổng ĐÃ KÝ" in ra and "✅ TƯƠI" not in ra
    assert "PI/IRB" in ra and f"--study {STUDY} --from G2" in ra, "lệnh sinh lại có chủ ý không bị cắt khỏi báo cáo"


def test_k7_rao_da_ky_b_nhanh_quay_lai_khong_chay_g2_da_ky(tmp_path, monkeypatch):
    """(b) G3 đổi N giữa lượt ⇒ quay lại G1 (dây chuyền vòng 2) — G2 đã ký vẫn không bị chạy."""
    out = _thu_muc(tmp_path)
    _ba_cong_dau(out, 482)
    _trds17(out, 482)
    _a2(out, 482)
    gia, bc = _chay(tmp_path, monkeypatch, out,
                    {"G1": _g1_chep, "G2": _g2_chep, "G3": _g3_ghi(218), "G4": _ghi_cp("G4")},
                    song=_SONG_G2_DA_KY, stale=("G3",))
    assert "G2" not in gia.lenh
    assert gia.lenh == ["G3", "G1", "G3"]
    assert [r["status"] for r in bc["gate_results"]].count("quay_lai_dong_bo_n") == 1
    kq = _theo_cong(bc)
    assert kq["G2"]["status"] == "giu_cong_da_ky" and kq["G2"]["vong"] == 2
    assert _trds17_hien(out) == 482
    assert kq["G4"]["status"] == "dung_lech_xuyen_cong"
    assert bc["converged_fresh"] is False


def test_k7_rao_da_ky_c_luot_sau_g2_cu_theo_mtime_van_khong_chay(tmp_path, monkeypatch, capsys):
    """(c) Lượt run_pipeline KẾ TIẾP sau khi G1 đã chạy lại: pipeline_freshness báo G2 cũ theo mtime (G2←G1) — G2 đã
    ký vẫn không bị sinh lại; báo cáo không «TƯƠI», mã thoát ≠ 0."""
    out = _thu_muc(tmp_path)
    _ba_cong_dau(out, 218)
    _trds17(out, 482)
    _a2(out, 218)
    gia, bc = _chay(tmp_path, monkeypatch, out,
                    {"G1": _g1_chep, "G2": _g2_chep, "G3": _g3_ghi(218), "G4": _ghi_cp("G4")},
                    song=_SONG_G2_DA_KY, stale=("G2",))
    assert "G2" not in gia.lenh
    assert gia.lenh == [], "cổng bị GIỮ không tính là «đã sinh» với phía sau: G3 tươi không bị kéo chạy lại"
    assert _trds17_hien(out) == 482
    kq = _theo_cong(bc)
    assert kq["G2"]["status"] == "giu_cong_da_ky"
    assert bc["converged_fresh"] is False and bc["n_giu_da_ky"] == 1
    RP.print_summary(bc)
    ra = capsys.readouterr().out
    assert "ĐÃ KÝ" in ra and "✅ TƯƠI" not in ra


def test_k7_rao_da_ky_chi_from_dung_cong_moi_sinh_lai(tmp_path, monkeypatch):
    """Sinh lại cổng đã ký là việc CÓ CHỦ Ý của người: `--from G2` (đúng cổng) ⇒ chạy; `--from G1` (dây chuyền)
    ⇒ giữ."""
    out = _thu_muc(tmp_path)
    _ba_cong_dau(out, 218)
    _trds17(out, 482)
    _a2(out, 218)
    kb = {"G1": _g1_chep, "G2": _g2_chep, "G3": _g3_ghi(218)}
    gia, bc = _chay(tmp_path, monkeypatch, out, kb, song=_SONG_G2_DA_KY, start="G1")
    assert gia.lenh[:2] == ["G1", "G3"] and "G2" not in gia.lenh
    assert _theo_cong(bc)["G2"]["status"] == "giu_cong_da_ky"
    gia, bc = _chay(tmp_path, monkeypatch, out, kb, song=_SONG_G2_DA_KY, start="G2")
    assert gia.lenh[:2] == ["G2", "G3"], "--from G2: người gọi chủ động sinh lại cổng đã ký"
    assert _trds17_hien(out) == 218


def test_k7_rao_da_ky_cong_cung_chua_ky_van_chay_theo_day_chuyen(tmp_path, monkeypatch):
    """Rào chỉ áp cho cổng cứng ĐÃ KÝ: G2 dự thảo (chấm sống DRAFT) vẫn chạy lại theo dây chuyền như trước."""
    out = _thu_muc(tmp_path)
    _ba_cong_dau(out, 218)
    _trds17(out, 482)
    _a2(out, 482)
    gia, _bc = _chay(tmp_path, monkeypatch, out, {"G1": _g1_chep, "G2": _g2_chep, "G3": _g3_ghi(218)},
                     song={"G0": "PASS", "G1": "PASS", "G2": "DRAFT", "G3": "PASS"})
    assert gia.lenh[:3] == ["G1", "G2", "G3"]
    assert _trds17_hien(out) == 218


# ─────────────────────────────────────── Sửa sau thẩm định PR #247 — «không đo được» nhất quán xuyên cổng ≠ «TƯƠI»
def _nq_hong(monkeypatch):
    import nhat_quan_xuyen_cong as NQ

    def hong(*a, **k):
        raise RuntimeError("bộ đối chiếu hỏng")

    monkeypatch.setattr(NQ, "doi_chieu", hong)


def test_nq_khong_do_duoc_check_only_chua_ket_luan_ma_thoat_khac_0(tmp_path, monkeypatch, capsys):
    out = _thu_muc(tmp_path)
    _ba_cong_dau(out, 218)
    _a2(out, 218)
    _nq_hong(monkeypatch)
    monkeypatch.setattr(RP, "BASE", tmp_path)
    monkeypatch.setattr(RP.FRESH, "stale_report", lambda out_dir: {
        "stale_gates": [], "orphan_gates": [], "fresh": True, "issues": [], "checkpoints_present": ["G0", "G3"]})
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "--study", STUDY, "--check-only"])
    assert RP.main() != 0, "không đo được ≠ ổn"
    ra = capsys.readouterr().out
    assert "⚪ CHƯA KẾT LUẬN ĐƯỢC" in ra and "✅ TƯƠI" not in ra and "bộ đối chiếu hỏng" in ra


def test_nq_khong_do_duoc_che_do_chay_khong_hoi_tu_tuoi(tmp_path, monkeypatch, capsys):
    out = _thu_muc(tmp_path)
    _cp(out, "G0", topic="chủ đề", base_query="q")
    _nq_hong(monkeypatch)
    gia, bc = _chay(tmp_path, monkeypatch, out, {"G1": _ghi_cp("G1")}, song={"G0": "PASS", "G1": "PASS"}, start="G1")
    assert gia.lenh == ["G1", "G2"], "không đo được ≠ có vấn đề: chuỗi không bị chặn giả"
    assert bc["converged_fresh"] is False
    assert bc["do_tuoi_tong_hop"]["ket_luan"] == "khong_ket_luan"
    RP.print_summary(bc)
    ra = capsys.readouterr().out
    assert "⚪ CHƯA KẾT LUẬN ĐƯỢC" in ra and "✅ TƯƠI" not in ra
