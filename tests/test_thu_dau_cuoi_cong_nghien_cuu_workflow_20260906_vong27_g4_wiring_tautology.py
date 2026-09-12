"""Hồi quy phát hiện #1 (Nghiêm trọng) của Workflow đối kháng đa-agent
2026-09-06 (vòng 27) trong tools/thu_dau_cuoi_cong_nghien_cuu.py —
wiring-canary cho G4 là kiểm TAUTOLOGY, không bao giờ chạm được code path
nó tuyên bố kiểm.

CƠ CHẾ LỖI:
    def _wiring_seed_g4(study_dir: Path) -> Path:
        artifact = study_dir / "G4_A5_SAP_FINAL.md"        # THIẾU "_{study}"
        ...

Tên artifact GỐC (hợp đồng bất biến, tools/g4_quality_gate.py::
sap_artifact_name) là "G4_A5_SAP_FINAL_{study}.md". approve_gate.py (dòng
~518-527) so khớp `artifact_path.resolve() == expected_artifact.resolve()`
TRƯỚC KHI gọi G4Q.evaluate_study() (dòng bị mock.patch trong wiring
canary) — không khớp thì `return 1` NGAY, patch không bao giờ được thực
thi.

Vì _wiring_seed_g4 ghi sai tên file, approve_gate.py LUÔN từ chối ở bước
so khớp tên (thông điệp "artifact phải là...") — KHÔNG PHẢI vì report
BLOCKED do patch trả về. run_wiring_canary() suy caught=True từ
`(rc != 0) and (not ledger_has_record)` — điều kiện này ĐÚNG CẢ KHI dây
nối đã đứt hoàn toàn (không ai gọi G4Q.evaluate_study nữa), vì approve_
gate vẫn rc=1 do sai tên file, không liên quan gì tới patch.

HẠI THẬT: nếu ai revert đúng bản vá Sprint 9 task 9.1 (gỡ lời gọi
G4Q.evaluate_study khỏi approve_gate.py trước khi ghi ledger — chính lỗ
hổng module này viết ra để canh), WIRING-G4-BLOCK-NOT-ENFORCED vẫn báo
xanh (caught=True) vì check vẫn thất bại ở bước so tên file — không phải
vì dây nối còn nguyên. Đúng lớp lỗi tautology BH72 mà module này (task
9.5) sinh ra để triệt tiêu, tái xuất hiện bên trong chính nó, cho một
trong 6 cổng cứng quan trọng nhất (SAP/khóa thống kê).

BẢN VÁ: _wiring_seed_g4() dùng đúng G4Q.sap_artifact_name(study_dir.name)
— cùng cách _wiring_seed_g8() đã làm đúng với
G8Q.presubmission_artifact_name().

Nguyên tắc viết test:
1. Test TRỰC TIẾP nhất — tên file seed phải khớp CHÍNH XÁC hàm hợp đồng
   mà approve_gate.py dùng để so khớp (không suy đoán qua rc/ledger).
2. Test đầu-cuối — chạy THẬT run_wiring_canary() (không mock nội bộ gì
   thêm), bắt stdout, xác nhận thông điệp từ chối G4 là đúng NHÁNH
   quality-gate ("SAP chưa qua đủ tiêu chí tự động") — KHÔNG PHẢI nhánh
   sai-tên-file ("artifact phải là...")."""
from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(REPO_ROOT), str(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g4_quality_gate as G4Q  # noqa: E402
import g8_quality_gate as G8Q  # noqa: E402
import thu_dau_cuoi_cong_nghien_cuu as CANARY  # noqa: E402


class TestWiringSeedG4DungTenArtifactChuan:
    """★★★ Ca chính — seed phải ghi ĐÚNG tên artifact mà approve_gate.py
    dùng để so khớp, không tự suy tên."""

    def test_ten_file_khop_hop_dong_sap_artifact_name(self, tmp_path):
        study_dir = tmp_path / "CANARY-TEST-G4"
        study_dir.mkdir()

        artifact = CANARY._wiring_seed_g4(study_dir)

        assert artifact.name == G4Q.sap_artifact_name(study_dir.name), (
            "TRƯỚC bản vá: seed ghi 'G4_A5_SAP_FINAL.md' (thiếu hậu tố "
            "'_{study}') — approve_gate.py không bao giờ nhận diện đúng "
            "file này, luôn từ chối ở bước so tên TRƯỚC KHI chạm tới "
            "G4Q.evaluate_study() bị patch"
        )

    def test_seed_g8_da_dung_tu_truoc_khong_bi_dong_hoi(self, tmp_path):
        """Đối chứng — _wiring_seed_g8() đã đúng từ đầu, không bị đổi
        hành vi bởi bản vá này."""
        study_dir = tmp_path / "CANARY-TEST-G8"
        study_dir.mkdir()

        artifact = CANARY._wiring_seed_g8(study_dir)

        assert artifact.name == G8Q.presubmission_artifact_name(study_dir.name)


class TestWiringCanaryG4DiDungDuongEvaluate:
    """★★★ Ca chính — chạy THẬT run_wiring_canary() (production code,
    không mock thêm gì), xác nhận thông điệp từ chối G4 đến từ nhánh
    quality-gate (patch THẬT SỰ được gọi), không phải nhánh so-tên-file."""

    def test_thong_diep_tu_choi_g4_la_quality_gate_khong_phai_sai_ten(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = CANARY.run_wiring_canary()
        out = buf.getvalue()

        g4_entry = next(r for r in result["wiring_results"] if r["code"] == "WIRING-G4-BLOCK-NOT-ENFORCED")
        assert g4_entry["caught"] is True

        assert "SAP chưa qua đủ tiêu chí tự động" in out, (
            "TRƯỚC bản vá: approve_gate.py từ chối G4 ở bước so tên file "
            "(thông điệp 'artifact phải là...'), KHÔNG BAO GIỜ chạm tới "
            "nhánh in ra 'SAP chưa qua đủ tiêu chí tự động' — tức patch "
            "G4Q.evaluate_study không bao giờ được thực thi, dù canary "
            "vẫn báo caught=True (đúng kết luận nhưng SAI lý do)"
        )
        assert "artifact phải là" not in out.split("TỪ CHỐI ký G8")[-1].split("TỪ CHỐI ký G2")[0], (
            "Đoạn từ chối G4 KHÔNG được rơi vào nhánh so-tên-file — nếu "
            "còn xuất hiện nghĩa là bản vá chưa có hiệu lực"
        )
