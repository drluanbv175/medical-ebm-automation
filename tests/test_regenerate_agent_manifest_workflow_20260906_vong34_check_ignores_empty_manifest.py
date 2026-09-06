r"""Hồi quy phát hiện #3 (audit vòng 34, 2026-09-06) trong
scripts/regenerate_agent_manifest.py — guard tautology ở chế độ ``--check``.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    try:
        current_content = SCOPE_A_MANIFEST_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        problems.append(...)
        current_content = ""
    if current_content and current_content != content:
        problems.append("manifest hiện tại khác nội dung sinh lại từ .claude/agents")

Nếu file manifest thật (``runtime/manifests/agent_source_manifest.csv``) bị ghi
đè thành RỖNG (0 byte — do lỗi ghi dở, disk full, thao tác `> file` nhầm...),
``current_content`` đọc được là ``""``, một giá trị FALSY. Biểu thức
``current_content and current_content != content`` short-circuit về ``False``
NGAY LẬP TỨC mà không hề so sánh nội dung — nên một manifest rỗng lọt qua
``--check`` thành ``CHECK PASS: manifest hiện tại khớp agent source và
self-check`` dù rõ ràng KHÔNG khớp gì cả. Đây đúng là kịch bản `--check` sinh
ra để bắt (drift giữa manifest đã ghi và nguồn `.claude/agents/*.md` thật).

BẢN VÁ: đổi giá trị fallback trong nhánh ``except`` từ ``""`` sang ``None``
(đánh dấu RIÊNG ca "không đọc được file", khác ca "đọc được nhưng rỗng"), và
đổi guard sang ``current_content is not None and current_content != content``
— một chuỗi rỗng ("" is not None" → True) nay đúng đắn kích hoạt so sánh nội
dung, trong khi ca không đọc được file (None) không bị báo trùng thông điệp
(thông điệp "không đọc được manifest hiện tại" đã có sẵn ở nhánh except).

NGUYÊN TẮC AN TOÀN KHI VIẾT TEST NÀY (rút từ sự cố THẬT xảy ra trong CHÍNH
vòng audit 34 — một agent nền vô tình ghi vào database production thật khi
tưởng đã cô lập bằng cách đổi thư mục làm việc): ``SCOPE_A_MANIFEST_PATH``
là đường dẫn tới file manifest THẬT đang sống
(``runtime/manifests/agent_source_manifest.csv``), được các cổng thật
(`AgentRegistry`/`verify_manifest_registry.py`) tin dùng. Test này TUYỆT ĐỐI
KHÔNG được đọc/ghi file đó. Thay vào đó, nạp module bằng
``importlib.util.spec_from_file_location`` (đăng ký vào ``sys.modules``
TRƯỚC ``exec_module`` — bài học nền: bỏ bước này làm mọi ``@dataclass`` nạp
hỏng) rồi ``monkeypatch.setattr(mod, "SCOPE_A_MANIFEST_PATH", <tmp_path>)`` —
mọi lần gọi ``mod.main()`` sau đó chỉ đọc/ghi file tạm của riêng test, không
bao giờ chạm ``runtime/manifests/agent_source_manifest.csv`` thật.

Test KHÔNG monkeypatch ``AGENTS_DIR``/``MANIFEST_SELF_CHECK_SHA256``/
``MINIMUM_AGENT_COUNT`` — chúng vẫn đọc từ ``.claude/agents/`` thật (chỉ ĐỌC,
không ghi) để có ``content``/``self_hash`` xác thực; test đã xác nhận bằng
tay (ngoài bộ test) rằng ở trạng thái hiện tại của repo, `self_hash` khớp
đúng ``MANIFEST_SELF_CHECK_SHA256`` và số agent >= ``MINIMUM_AGENT_COUNT`` —
nên phép thử KHÔNG bị nhiễu bởi hai luật kia; ca chính chỉ khác biệt đúng ở
guard đang kiểm."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "regenerate_agent_manifest.py"

_PROBLEM_NOI_DUNG_KHAC = "manifest hiện tại khác nội dung sinh lại từ .claude/agents"
_PROBLEM_KHONG_DOC_DUOC = "không đọc được manifest hiện tại"


def _nap():
    """Nạp scripts/regenerate_agent_manifest.py qua đường dẫn file — module
    này không nằm trong một package (không có scripts/__init__.py) nên phải
    nạp bằng spec_from_file_location, cùng khuôn với các test khác trong
    repo (vd tests/test_g6_quality_gate_20260815.py::_nap)."""
    spec = importlib.util.spec_from_file_location(
        "regenerate_agent_manifest_vong34_test", SCRIPT_PATH,
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["regenerate_agent_manifest_vong34_test"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestCaChinhManifestRongLotQuaCheck:
    """★★★ Ca chính — manifest bị ghi đè thành RỖNG (0 byte) phải bị --check
    phát hiện là drift, KHÔNG được báo CHECK PASS."""

    def test_manifest_rong_bi_bao_khac_noi_dung(self, tmp_path, monkeypatch, capsys):
        mod = _nap()
        fake_manifest = tmp_path / "agent_source_manifest.csv"
        fake_manifest.write_text("", encoding="utf-8", newline="\n")

        monkeypatch.setattr(mod, "SCOPE_A_MANIFEST_PATH", fake_manifest)
        monkeypatch.setattr(sys, "argv", ["regenerate_agent_manifest.py", "--check"])

        exit_code = mod.main()
        captured = capsys.readouterr()

        assert _PROBLEM_NOI_DUNG_KHAC in captured.out, (
            "TRƯỚC bản vá: guard 'current_content and current_content != content' "
            "coi chuỗi rỗng là falsy nên KHÔNG BAO GIỜ so sánh nội dung, một "
            "manifest 0-byte lọt qua --check thành CHECK PASS. "
            f"stdout={captured.out!r}"
        )
        assert exit_code == 1, (
            f"--check phải trả mã 1 (CHECK FAIL) khi manifest rỗng khác nội "
            f"dung sinh lại. stdout={captured.out!r}"
        )
        assert "CHECK FAIL" in captured.out


class TestDoiChungManifestKhopVaThieuFile:
    """Đối chứng — hai ca KHÔNG bị bản vá ảnh hưởng, phải giữ nguyên hành vi
    trước/sau: manifest khớp 100% vẫn PASS; file không đọc được vẫn báo ĐÚNG
    MỘT thông điệp, không báo trùng."""

    def test_manifest_khop_hoan_toan_van_pass(self, tmp_path, monkeypatch, capsys):
        mod = _nap()
        fake_manifest = tmp_path / "agent_source_manifest.csv"

        # Sinh nội dung THẬT bằng chính --write của script (không tự chép lại
        # logic sinh CSV trong test) rồi --check ngay trên file đó — đảm bảo
        # so khớp byte-for-byte, không phụ thuộc format tay.
        monkeypatch.setattr(mod, "SCOPE_A_MANIFEST_PATH", fake_manifest)
        monkeypatch.setattr(sys, "argv", ["regenerate_agent_manifest.py", "--write"])
        write_exit = mod.main()
        capsys.readouterr()
        assert write_exit == 0
        assert fake_manifest.exists()

        monkeypatch.setattr(sys, "argv", ["regenerate_agent_manifest.py", "--check"])
        check_exit = mod.main()
        captured = capsys.readouterr()

        assert _PROBLEM_NOI_DUNG_KHAC not in captured.out
        assert "CHECK PASS" in captured.out
        assert check_exit == 0

    def test_thieu_file_bao_dung_mot_thong_diep_khong_trung(
        self, tmp_path, monkeypatch, capsys,
    ):
        mod = _nap()
        # Thư mục cha không tồn tại ⇒ .read_text() ném FileNotFoundError
        # (con của OSError) — đúng nhánh except.
        missing_manifest = tmp_path / "khong-ton-tai" / "agent_source_manifest.csv"

        monkeypatch.setattr(mod, "SCOPE_A_MANIFEST_PATH", missing_manifest)
        monkeypatch.setattr(sys, "argv", ["regenerate_agent_manifest.py", "--check"])

        exit_code = mod.main()
        captured = capsys.readouterr()

        assert _PROBLEM_KHONG_DOC_DUOC in captured.out
        assert _PROBLEM_NOI_DUNG_KHAC not in captured.out, (
            "Ca không đọc được file KHÔNG được báo trùng thêm thông điệp "
            "'khác nội dung sinh lại' — đã có thông điệp 'không đọc được' rồi."
        )
        assert exit_code == 1
