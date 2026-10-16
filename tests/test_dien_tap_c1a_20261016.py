"""DIỄN TẬP từng cổng trên BẢN SAO hồ sơ C1a (16/10/2026, bác sĩ: «Diễn tập từng cổng cho phù hợp giúp tôi»).

Chỉ chạy CỤC BỘ trong worktree có bản sao `exports/<C1a>/` (CI không có ⇒ bỏ qua). Mọi chữ ký dùng khoá GIẢ của
pytest (conftest) — không bao giờ chạm khoá thật; bản sao nằm trong worktree, không đụng thư mục đề tài thật.
Mỗi bước gọi ĐÚNG lệnh thật PI/thống kê viên sẽ gõ và ghi BIÊN BẢN (mã thoát + dòng chặn) — mục đích là TÌM chỗ hở
trước khi có dữ liệu thật, nên test không đỏ vì một bước bị chặn; chỉ đỏ khi không ghi được biên bản.
Chọn cổng: biến môi trường DIEN_TAP_CONG="G2,G4,G5" (mặc định G2,G4,G5).
"""
from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

ROOT = Path(__file__).resolve().parent.parent
STUDY = "hai-long-benh-nhan-C1a-BVQY175"
OUT = ROOT / "exports" / STUDY
NHOM = ("IRB", "STATISTICIAN", "PI", "DATA_MANAGER", "INDEPENDENT_PEER_REVIEWER")

pytestmark = pytest.mark.skipif(not (OUT / "study_meta.json").is_file(),
                                reason="diễn tập cục bộ: cần bản sao exports/<C1a>/ trong worktree")


def _chay(args: list[str]) -> dict:
    r = subprocess.run([sys.executable, *args], cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=dict(os.environ), timeout=900)
    dong = [x for x in (r.stdout + "\n" + r.stderr).splitlines() if x.strip()]
    chan = [x.strip() for x in dong if any(k in x for k in ("🚧", "⛔", "✗", "BLOCK", "LÝ DO", "Lỗi", "lỗi", "từ chối",
                                                           "CHƯA", "thiếu"))]
    return {"lenh": " ".join(args), "ma_thoat": r.returncode, "dong_chan": chan[:25], "cuoi": dong[-8:]}


def _khoa_vai(monkeypatch) -> None:
    """Khoá GIẢ cho từng nhóm vai, cạnh khoá giả chung của conftest."""
    goc = Path(os.environ["EBM_GATE_KEY_PATH"])
    for nhom in NHOM:
        p = goc.parent / f"{goc.name}_{nhom}"
        if not p.exists():
            p.write_text(secrets.token_hex(32), encoding="utf-8", newline="\n")


def _ky(gate: str, artifact: str, vai: str, ref: str, them: list[str] | None = None) -> dict:
    return _chay(["tools/approve_gate.py", "--study", STUDY, "--gate", gate,
                  "--artifact", f"exports/{STUDY}/{artifact}", "--reviewer-role", vai, "--reviewer-ref", ref,
                  "--scope", "DIỄN TẬP — khoá giả, bản sao",
                  *(them or [])])


_THAY_SAU_IRB = (  # mô phỏng PI điền ô «sau phê duyệt» khi nhận quyết định Hội đồng (giá trị GIẢ)
    ("[Phiên bản phê duyệt sẽ có số IRB, CẦN BỔ SUNG]", "Phiên bản phê duyệt: DT-001/2026"),
    ("[CẦN — sẽ có sau khi đăng ký trên OSF Registries: mã/URL đăng ký dạng osf.io/xxxxx]", "osf.io/dientap"),
    ("[CẦN — ngày đăng ký thành công]", "{hom_nay}"),
    ("Số phê duyệt IRB: [CẦN sau khi nhận]", "Số phê duyệt IRB: DT-001/2026"),
    ("[CẦN — chỉ tuyển sau phê duyệt và đăng ký: ___/___/2026]", "{tuyen}"),
    ("Approval date: [CẦN sau quyết định IRB]", "Approval date: {hom_nay}"),
    ("[CẦN — ngày hoàn tất dự kiến; cập nhật ngày thật khi kết thúc]", "2028-12-31 (dự kiến)"),
    ('"DRAFT, Điền trường còn [CẦN] trước khi gửi đăng ký."', ""),
)


def _mo_phong_sau_irb(hom_nay: date) -> list[str]:
    p = OUT / f"G2_A3_ETHICS_PACKAGE_{STUDY}.md"
    s = p.read_text(encoding="utf-8")
    thieu = []
    for cu, moi in _THAY_SAU_IRB:
        if cu not in s:
            thieu.append(cu)
        s = s.replace(cu, moi.format(hom_nay=hom_nay.isoformat(), tuyen=(hom_nay + timedelta(days=30)).isoformat()))
    p.write_text(s, encoding="utf-8", newline="\n")
    return thieu


def _du_lieu_mo_phong(n_ban: int = 50, moi_ban: int = 20, seed: int = 20261016, bo_checkbox: bool = False) -> Path:
    """1.000 phiếu GIẢ theo đúng từ điển REDCap G5 của đề tài (50 bàn × 20); không có dữ liệu người thật."""
    import csv
    import random
    rnd = random.Random(seed)
    tu_dien = list(csv.DictReader((OUT / f"G5_REDCap_dictionary_{STUDY}.csv").open(encoding="utf-8-sig")))
    cot, hang = [], []
    for f in tu_dien:
        ten, kieu = f["Variable / Field Name"], f["Field Type"]
        if kieu == "checkbox" and bo_checkbox:
            continue  # F6: công cụ làm sạch chưa mở rộng cột checkbox REDCap (___<mã>) — tạm bỏ để diễn tập cổng sau
        cot += [f"{ten}___{c.split(',')[0].strip()}" for c in f["Choices, Calculations, OR Slider Labels"].split("|")] \
            if kieu == "checkbox" else [ten]
    for i in range(n_ban * moi_ban):
        ban = i // moi_ban + 1
        r = {}
        for f in tu_dien:
            ten, kieu = f["Variable / Field Name"], f["Field Type"]
            lua = [c.split(",")[0].strip() for c in f["Choices, Calculations, OR Slider Labels"].split("|")
                   if c.strip()]
            vt, lo, hi = (f.get("Text Validation Type OR Show Slider Number") or "").strip(), \
                f.get("Text Validation Min") or "", f.get("Text Validation Max") or ""
            if ten == "record_id":
                r[ten] = f"DT{i + 1:04d}"
            elif ten == "ma_ban_kham":
                r[ten] = f"BK{ban:02d}"
            elif ten == "thoigian_cho":
                r[ten] = str(max(5, int(rnd.lognormvariate(3.6, 0.6))))
            elif kieu in ("radio", "dropdown", "yesno", "truefalse"):
                lua = lua or ["1", "0"]
                chinh = [x for x in lua if x in "12345"] or lua
                r[ten] = rnd.choice(chinh) if rnd.random() < 0.95 else rnd.choice(lua)
            elif kieu == "checkbox" and bo_checkbox:
                continue
            elif kieu == "checkbox":
                chon = set(rnd.sample(lua, k=min(2, len(lua))))
                for c in lua:
                    r[f"{ten}___{c}"] = "1" if c in chon else "0"
            elif kieu == "text" and vt in ("integer", "number") and lo and hi:
                r[ten] = str(rnd.randint(int(float(lo)), min(int(float(hi)), int(float(lo)) + 120)))
            else:
                r[ten] = ""
        hang.append(r)
    ra = OUT / "DIEN_TAP" / "du_lieu_mo_phong.csv"
    ra.parent.mkdir(parents=True, exist_ok=True)
    with ra.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cot)
        w.writeheader()
        w.writerows(hang)
    return ra


def _mo_phong_chot_dmp(hom_nay: date) -> None:
    """Mô phỏng PI/quản lý dữ liệu chốt DMP lúc khoá (bỏ nhãn DRAFT, điền ô khoá, đánh dấu checklist) — giá trị GIẢ."""
    import re  # noqa: PLC0415
    p = OUT / f"G5_A6_DATA_MGMT_{STUDY}.md"
    s = p.read_text(encoding="utf-8")
    import g5_quality_gate as G5Q  # noqa: PLC0415
    goc = G5Q._dmp_khoi_khoa(s)  # dùng đúng hàm tách mục của cổng
    if not goc:
        return
    khoi = re.sub(r"\[CẦN[^\]]*\]", f"DIỄN TẬP {hom_nay.isoformat()}", goc)
    khoi = re.sub(r"^(\s*[-*]\s+)\[\s\]", r"\1[x]", khoi, flags=re.MULTILINE)
    s = s.replace(goc, khoi, 1)
    # F10: phần «sống» của DMP còn ô trống + dòng khuôn không thuộc C1a — mô phỏng PI hoàn tất khi khoá
    s = "".join(d for d in s.splitlines(keepends=True) if "qol_score_baseline" not in d)
    s = re.sub(r"\*\*\[CẦN[^\]]*\]\*\*\s*", "", s)
    s = re.sub(r"\[CẦN[^\]]*\]", "DIỄN TẬP", s)
    s = s.replace("CHỜ BÁC SĨ ĐIỀN CÁC DIỄN TẬP VÀ XÁC NHẬN", "đã hoàn tất khi khoá (diễn tập)")
    dong = s.splitlines()
    for i, ln in enumerate(dong[:15]):
        if ln.startswith("# ") or "**Trạng thái:**" in ln:
            dong[i] = re.sub(r"\s*\(?\bDRAFT\b\)?", " (ĐÃ CHỐT KHI KHOÁ)", ln)
    p.write_text("\n".join(dong) + "\n", encoding="utf-8", newline="\n")


def _mo_phong_sua_g3() -> int:
    """F3 + F5 (mô phỏng trên bản sao): nhãn Likert 5 mức theo phiếu gốc bác sĩ chốt 15/10; mã 998 cho «không ước
    lượng được» như đề cương nộp. Trả số thay đổi."""
    p = OUT / "_bo-bien-rieng.csv"
    s = p.read_text(encoding="utf-8")
    n = s.count("2, Mức 2 | 3, Mức 3 | 4, Mức 4")
    s = s.replace("2, Mức 2 | 3, Mức 3 | 4, Mức 4", "2, Không hài lòng | 3, Bình thường/Không ý kiến | 4, Hài lòng")
    s = s.replace("Đề cương chỉ ghi neo mức 1 và 5 (C.2) — [CẦN BÁC SĨ đối chiếu nhãn mức 2-4 theo phiếu in trước khi "
                  "import REDCap]", "Nhãn 5 mức theo phiếu gốc của chủ nhiệm (chốt 15/10/2026)")
    s = s.replace('"8 = không nghĩ tới/không ước lượng được.', '"998 = không nghĩ tới/không ước lượng được (mã thiếu).')
    # F9: PI quyết 14/10 KHÔNG thu thập biến chuyên khoa (SAP §5 đã sửa) nhưng bộ biến G3 còn giữ — mô phỏng bỏ
    s = "".join(d for d in s.splitlines(keepends=True) if not d.startswith("chuyenkhoa,"))
    p.write_text(s, encoding="utf-8", newline="")
    return n


def test_dien_tap_c1a(monkeypatch):
    _khoa_vai(monkeypatch)
    # Khoá giả MỚI mỗi lượt pytest ⇒ chữ ký lượt trước không còn khớp: xoá sổ cái của BẢN SAO (worktree) rồi ký lại.
    assert "ebm-worktrees" in str(OUT), "chỉ diễn tập trên bản sao trong worktree"
    for ten in ("approval_ledger.json", "approval_ledger.seal.json"):
        (OUT / ten).unlink(missing_ok=True)
    cong = [c.strip() for c in os.environ.get("DIEN_TAP_CONG", "G2,G4,G5").split(",") if c.strip()]
    hom_nay = date.today()
    bien_ban: dict = {"study": STUDY, "ngay": hom_nay.isoformat(), "buoc": []}
    if "G3S" in cong:
        bien_ban["buoc"].append(("G3 mô phỏng sửa F3/F5", {"ma_thoat": 0, "lenh": "(sửa bản sao)", "cuoi": [],
                                                           "dong_chan": [f"đổi nhãn {_mo_phong_sua_g3()} câu Likert"]}))
        bien_ban["buoc"].append(("G3 chấm lại", _chay(["tools/g3_quality_gate.py", "--study", STUDY])))
    if "G4S" in cong:  # F11: SAP §2 đặt tên biến theo đề cương v1.0, bộ biến G3 dùng `g1` — mô phỏng thống kê viên sửa
        p_sap = OUT / f"G4_A5_SAP_FINAL_{STUDY}.md"
        t = p_sap.read_text(encoding="utf-8")
        n = t.count("(biến SHLNBChung_TrucTiep), Phần 3 phiếu")
        p_sap.write_text(t.replace("(biến SHLNBChung_TrucTiep), Phần 3 phiếu",
                                   "(biến SHLNBChung_TrucTiep), Phần 3 phiếu — trường dữ liệu `g1`"),
                         encoding="utf-8", newline="")
        bien_ban["buoc"].append(("G4 mô phỏng sửa F11", {"ma_thoat": 0, "lenh": "(sửa bản sao)", "cuoi": [],
                                                         "dong_chan": [f"đổi {n} chỗ tên biến kết cục chính"]}))
        # sửa SAP làm xác nhận cũ hết hiệu lực (G4-HUMAN-08) — mô phỏng PI đọc lại rồi xác nhận lại dấu vân tay mới
        import re as _re  # noqa: PLC0415
        r4 = _chay(["tools/g4_quality_gate.py", "--study", STUDY])
        m4 = _re.search(r"hiện tại ([0-9a-f]{16})", "\n".join(r4["dong_chan"] + r4["cuoi"]))
        if not m4:
            bc4 = (OUT / "G4_QUALITY_REPORT.md").read_text(encoding="utf-8")
            m4 = _re.search(r"hiện tại ([0-9a-f]{16})", bc4)
        if m4:
            p_meta = OUT / "study_meta.json"
            meta = json.loads(p_meta.read_text(encoding="utf-8"))
            meta["gate_params"]["G4"].update({"dau_van_tay_chot": m4.group(1), "reviewed_at": hom_nay.isoformat()})
            p_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        bien_ban["buoc"].append(("G4 mô phỏng PI xác nhận lại SAP",
                                 {"ma_thoat": 0 if m4 else 1, "lenh": "(sửa bản sao)", "cuoi": [],
                                  "dong_chan": [str(m4 and m4.group(1))]}))
    if "G2" in cong:
        bien_ban["buoc"].append(("G2 mô phỏng PI điền ô sau IRB", {"ma_thoat": 0,
                                                                   "dong_chan": _mo_phong_sau_irb(hom_nay),
                                                                   "cuoi": [], "lenh": "(sửa bản sao)"}))
        bien_ban["buoc"].append(("G2 ký IRB (giả)", _ky(
            "G2", f"G2_A3_ETHICS_PACKAGE_{STUDY}.md", "IRB", "DIEN-TAP-IRB",
            ["--g2-ethics-committee-ref", "DIEN-TAP-HOI-DONG", "--g2-approval-number", "DT-001/2026",
             "--g2-approval-date", hom_nay.isoformat(),
             "--g2-valid-until", (hom_nay + timedelta(days=730)).isoformat(),
             "--g2-protocol-version", "1.0", "--g2-icf-version", "1.0", "--g2-ethics-decision", "APPROVED",
             "--g2-recruitment-mode", "PROSPECTIVE_NEW_PARTICIPANTS", "--g2-registration-status", "REGISTERED",
             "--g2-registry", "OSF", "--g2-registration-id", "osf.io/dientap",
             "--g2-registration-date", hom_nay.isoformat(),
             "--g2-first-enrolment-date", (hom_nay + timedelta(days=30)).isoformat(),
             "--g2-approval-scope", "Toàn bộ đề cương v1.0 và phiếu đồng ý v1.0"])))
        bien_ban["buoc"].append(("G2 chấm", _chay(["tools/g2_quality_gate.py", "--study", STUDY])))
    if "G4" in cong:
        sap = f"G4_A5_SAP_FINAL_{STUDY}.md"
        bien_ban["buoc"].append(("G4 ký thống kê viên (giả)",
                                 _ky("G4", sap, "METHODS_STATISTICS_REVIEWER", "DIEN-TAP-TKV")))
        bien_ban["buoc"].append(("G4 ký PI (giả)", _ky("G4", sap, "PI", "DIEN-TAP-PI")))
        bien_ban["buoc"].append(("G4 chấm", _chay(["tools/g4_quality_gate.py", "--study", STUDY])))
    if "G5" in cong:
        bien_ban["buoc"].append(("G5 sinh bộ công cụ", _chay(["tools/run_g5_auto.py", "--study", STUDY])))
        bien_ban["buoc"].append(("G5 chấm", _chay(["tools/g5_quality_gate.py", "--study", STUDY])))
    if "G5D" in cong and not (OUT / f"G5_REDCap_dictionary_{STUDY}.csv").is_file():
        bien_ban["buoc"].append(("G5 dữ liệu — bỏ qua", {"ma_thoat": 1, "lenh": "", "cuoi": [],
                                                       "dong_chan": ["chưa có từ điển G5 (bước G5 trước bị chặn)"]}))
        cong = [c for c in cong if c not in ("G5D", "G6")]
    if "G5D" in cong:
        # mô phỏng người quản lý dữ liệu xác nhận hồ sơ vận hành (giá trị GIẢ)
        import g5_quality_gate as G5Q  # noqa: PLC0415
        p_ops = OUT / G5Q.OPERATIONAL_READINESS_JSON
        ops = json.loads(p_ops.read_text(encoding="utf-8")) if p_ops.is_file() else {}
        nay = hom_nay.isoformat()
        ops.update({"schema_version": G5Q.OPERATIONAL_SCHEMA_VERSION, "status": "VERIFIED",
                    "access_control_review": {"completed": True, "reviewed_at": nay, "least_privilege_confirmed": True,
                                              "evidence_ref": "DIEN-TAP-ACCESS"},
                    "backup_restore_test": {"completed": True, "tested_at": nay, "restore_verified": True,
                                            "checksum_verified": True, "evidence_ref": "DIEN-TAP-BACKUP"},
                    "retention_plan": {"confirmed": True, "retention_rule": "2 năm sau khi kết thúc (G2 TL6)"},
                    "protocol_deviations": {"reconciled": True, "open_count": 0, "log_ref": "DIEN-TAP-DEV"},
                    "audit_trail_review": {"completed": True, "reviewed_at": nay, "evidence_ref": "DIEN-TAP-AUDIT"},
                    "source_data_verification": {"method": "Kiểm ngẫu nhiên 10% phiếu so với phiếu giấy",
                                                 "fraction_or_n": "10%", "completed": True,
                                                 "evidence_ref": "DIEN-TAP-SDV"},
                    "reviewer_role": "DATA_GOVERNANCE_QA_REVIEWER", "reviewer_ref": "DIEN-TAP-DM"})
        p_ops.write_text(json.dumps(ops, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        du_lieu = _du_lieu_mo_phong(bo_checkbox=os.environ.get("DIEN_TAP_BO_CHECKBOX", "0") == "1")
        tu_dien = f"exports/{STUDY}/G5_REDCap_dictionary_{STUDY}.csv"  # tương đối như PI gõ (F7 đã sửa)
        bien_ban["buoc"].append(("G5 nạp dữ liệu", _chay(["tools/import_real_dataset.py", "--study", STUDY,
                                                          "--data", str(du_lieu)])))
        bien_ban["buoc"].append(("G5 làm sạch", _chay(["tools/clean_research_dataset.py", "--study", STUDY,
                                                       "--data", str(du_lieu), "--dictionary", tu_dien])))
        _mo_phong_chot_dmp(hom_nay)
        import clean_research_dataset as CLEAN  # noqa: PLC0415
        import lock_analysis_dataset as LAD  # noqa: PLC0415
        rep_clean = json.loads((OUT / CLEAN.REPORT_NAME).read_text(encoding="utf-8"))
        try:
            man = LAD.lock_dataset(
                STUDY, OUT / rep_clean["clean_dataset_path"], lock_date=hom_nay.isoformat(),
                reviewer_role="DATA_GOVERNANCE_QA_REVIEWER", reviewer_ref="DIEN-TAP-DM", sap_version="1.0",
                query_log=OUT / rep_clean["query_log"], dictionary_path=ROOT / tu_dien,
                cleaning_report_path=OUT / CLEAN.REPORT_NAME, exports_root=ROOT / "exports", repo_root=ROOT,
                confirm_deidentified=True, confirm_clean_copy=True, confirm_no_open_query=True, confirm_sap_locked=True,
                confirm_dictionary_crf_aligned=True, confirm_access_control_reviewed=True,
                confirm_backup_restore_tested=True, confirm_retention_plan=True,
                confirm_protocol_deviations_reconciled=True, confirm_audit_trail_reviewed=True)
            khoa = {"ma_thoat": 0 if man.get("status") == LAD.LOCKED_STATUS else 1, "lenh": "lock_dataset",
                    "dong_chan": [str(x)[:200] for x in (man.get("blockers") or [])], "cuoi": [str(man.get("status"))]}
        except Exception as e:  # noqa: BLE001 — diễn tập ghi lại mọi lỗi
            khoa = {"ma_thoat": 99, "lenh": "lock_dataset", "dong_chan": [f"{type(e).__name__}: {e}"[:300]], "cuoi": []}
        bien_ban["buoc"].append(("G5 khoá dữ liệu", khoa))
        bien_ban["buoc"].append(("G5 chấm sau khoá", _chay(["tools/g5_quality_gate.py", "--study", STUDY])))
        bien_ban["buoc"].append(("G5 ký quản lý dữ liệu (giả)", _ky("G5", "G5_checkpoint.json",
                                                                      "DATA_GOVERNANCE_QA_REVIEWER", "DIEN-TAP-DM")))
        bien_ban["buoc"].append(("G5 ký PI (giả)", _ky("G5", "G5_checkpoint.json", "PI", "DIEN-TAP-PI")))
        bien_ban["buoc"].append(("G5 chấm cuối", _chay(["tools/g5_quality_gate.py", "--study", STUDY])))
    if "G6" in cong:
        bien_ban["buoc"].append(("G6 sinh phân tích", _chay(["tools/run_g6_auto.py", "--study", STUDY])))
        bien_ban["buoc"].append(("G6 chấm", _chay(["tools/g6_quality_gate.py", "--study", STUDY])))
        # mô phỏng thống kê viên xác nhận script khớp SAP (gate_params.G6) với dấu vân tay chốt do cổng tính
        import re as _re  # noqa: PLC0415
        bc = json.loads((OUT / "G6_QUALITY_REPORT.json").read_text(encoding="utf-8"))
        h1 = next((c for c in bc.get("checks") or [] if c.get("id") == "G6-HUMAN-01"), {})
        m = _re.search(r'dau_van_tay_chot: \"?([0-9a-f]{8,})', str(h1.get("detail")))
        if m:
            p_meta = OUT / "study_meta.json"
            meta = json.loads(p_meta.read_text(encoding="utf-8"))
            meta.setdefault("gate_params", {})["G6"] = {"scripts_match_sap_confirmed": True,
                                                       "reviewed_by_role": "STATISTICIAN",
                                                       "reviewed_at": hom_nay.isoformat(),
                                                       "dau_van_tay_chot": m.group(1)}
            p_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
            bien_ban["buoc"].append(("G6 chấm sau xác nhận (giả)",
                                     _chay(["tools/g6_quality_gate.py", "--study", STUDY])))
    if "G6R" in cong:  # phân tích chính chạy THẬT trên dữ liệu mô phỏng đã khoá (đường Python)
        import glob  # noqa: PLC0415
        khoa = sorted(glob.glob(str(OUT / "**" / "*locked*.csv"), recursive=True))
        bien_ban["buoc"].append(("G6 phân tích chính (Python, ordinal + SE cụm)", _chay([
            "tools/run_stats_analysis.py", "--study", STUDY, "--data", khoa[-1] if khoa else "KHONG_CO_BAN_KHOA",
            "--outcome", "g1", "--outcome-type", "ordinal", "--cot-cum", "ma_ban_kham", "--group", "thoigian_cho",
            "--covariates", "tuoi,gioitinh,noicutru,cobhyt,lydokham,khunggio_kham,ngay_trong_tuan,"
                            "suckhoe_tudanhgia,duoc_dung_bacsi",
            "--i-confirm-sap-locked", "--i-confirm-irb-approved"])))
        bien_ban["buoc"].append(("G6 chấm sau phân tích", _chay(["tools/g6_quality_gate.py", "--study", STUDY])))
    if "G10" in cong:  # biên nhận A12 phải ký bằng khoá của lượt này (bản sao mang biên nhận ký khoá thật)
        import re as _re  # noqa: PLC0415
        pm = set()
        for ten in (f"DE_CUONG_THONG_NHAT_{STUDY}.md", f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md"):
            if (OUT / ten).is_file():
                pm |= set(_re.findall(r"PMID:?\s*(\d{5,9})", (OUT / ten).read_text(encoding="utf-8")))
        bien_ban["buoc"].append(("G10 A12 kiểm trích dẫn (khoá giả)", _chay(
            ["tools/check_citations.py", "--study", STUDY, "--pmids", ",".join(sorted(pm))])))
    for g, lenh in (("G7", ["tools/run_g7_auto.py", "--study", STUDY]),
                    ("G8", ["tools/run_g8_auto.py", "--study", STUDY]),
                    ("G9", ["tools/run_g9_auto.py", "--study", STUDY]),
                    ("G10", ["tools/run_g10_assemble.py", "--study", STUDY])):
        if g in cong:
            bien_ban["buoc"].append((f"{g} chạy công cụ", _chay(lenh)))
            bien_ban["buoc"].append((f"{g} chấm", _chay([f"tools/{g.lower()}_quality_gate.py", "--study", STUDY])))
    ra = OUT / "DIEN_TAP" / f"bien_ban_{'_'.join(cong)}.json"
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(json.dumps(bien_ban, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    for ten, kq in bien_ban["buoc"]:
        print(f"\n### {ten} — mã {kq['ma_thoat']}")
        for x in (kq["dong_chan"] or kq["cuoi"])[:12]:
            print("   ", x[:220])
    assert ra.is_file()
