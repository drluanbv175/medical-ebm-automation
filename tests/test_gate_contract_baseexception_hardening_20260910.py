r"""Hồi quy BH99 phần A (đo lại 10/09/2026) — rào `cryptography` là fail-CRASH,
không phải fail-closed, dù CLAUDE.md từng khai "đã vá 02/09/2026".

CƠ CHẾ LỖI: thư viện `cryptography` cài HỎNG NỬA CHỪNG (có gói, thiếu
`_cffi_backend`) ném `pyo3_runtime.PanicException` — lớp đó kế thừa THẲNG
`BaseException`, KHÔNG qua `Exception`. Bốn hàm trong `tools/gate_contract.py`
(`_load_ed_private`, `_load_ed_public`, `sign_approval_ed25519`,
`verify_approval_signature` nhánh ed1) và một điểm trong
`tools/setup_gate_approval_key.py` (`Ed25519PrivateKey.generate()`) từng chỉ
bắt `except Exception`, nên panic đó LỌT QUA và làm CHẾT tiến trình ngay trong
các hàm tự khai "fail-closed" trong docstring/comment của chính chúng — đúng
họ BH27 (phạm vi rào không khớp lời khai).

Audit toàn diện hệ nghiên cứu 10/09/2026 đo lại bằng `git log -S "BaseException"
-- tools/gate_contract.py tools/setup_gate_approval_key.py` trên MỌI nhánh → 0
kết quả, xác nhận bản vá "02/09" mà CLAUDE.md khai chưa từng landed trên mã
sống. Bản vá thật sự thêm ở đây.

Nguyên tắc viết test (không dùng `pytest.importorskip` — module KHÔNG import
cryptography ở mức module nên collection luôn an toàn; chỉ hàm gọi mới đụng
thư viện):
1. Mô phỏng `pyo3_runtime.PanicException` bằng một lớp `BaseException` tự viết
   (không cần cài hỏng cryptography thật) — chỉ cần chứng minh CHỖ BẮT đúng
   loại, không phụ thuộc trạng thái cài đặt máy đang chạy test.
2. Với MỖI điểm rào: (a) BaseException giả bị bắt, hàm trả None/False như đã
   khai, KHÔNG crash; (b) KeyboardInterrupt/SystemExit KHÔNG bị nuốt — đây là
   rào có chủ đích hẹp, không phải lá chắn nuốt hết mọi ngắt.
3. Đã tự kiểm bằng đột biến: đổi `except BaseException` → `except Exception`
   tại một điểm rồi chạy lại đúng test tương ứng ⇒ đỏ (lỗi thật lọt ra làm
   test crash thay vì assert được `None`/`False`); khôi phục lại ⇒ xanh.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import gate_contract as GC  # noqa: E402
import setup_gate_approval_key as SGAK  # noqa: E402


class _GiaLapPanicException(BaseException):
    """Mô phỏng pyo3_runtime.PanicException — kế thừa BaseException, không phải Exception."""


ROLE = "IRB_ETHICS_COMMITTEE"


class TestLoadEdPrivateBatBaseException:
    def test_base_exception_bi_bat_tra_none(self, tmp_path, monkeypatch):
        fake_priv = tmp_path / "fake.key"
        fake_priv.write_bytes(b"khong quan trong noi dung, khong doc that")
        monkeypatch.setattr(GC, "_ed_private_path", lambda group: fake_priv)

        import cryptography.hazmat.primitives.serialization as ser_mod

        def _no(*a, **kw):
            raise _GiaLapPanicException("gia lap cffi hong")

        monkeypatch.setattr(ser_mod, "load_pem_private_key", _no)

        assert GC._load_ed_private("IRB") is None

    def test_keyboardinterrupt_khong_bi_nuot(self, tmp_path, monkeypatch):
        fake_priv = tmp_path / "fake.key"
        fake_priv.write_bytes(b"khong quan trong")
        monkeypatch.setattr(GC, "_ed_private_path", lambda group: fake_priv)

        import cryptography.hazmat.primitives.serialization as ser_mod

        def _ngat(*a, **kw):
            raise KeyboardInterrupt()

        monkeypatch.setattr(ser_mod, "load_pem_private_key", _ngat)

        with pytest.raises(KeyboardInterrupt):
            GC._load_ed_private("IRB")


class TestLoadEdPublicBatBaseException:
    def test_base_exception_bi_bat_tra_none(self, tmp_path, monkeypatch):
        fake_pub = tmp_path / "fake.pub"
        fake_pub.write_bytes(b"khong quan trong noi dung, khong doc that")
        monkeypatch.setattr(GC, "_ed_public_path", lambda group: fake_pub)

        import cryptography.hazmat.primitives.serialization as ser_mod

        def _no(*a, **kw):
            raise _GiaLapPanicException("gia lap cffi hong")

        monkeypatch.setattr(ser_mod, "load_pem_public_key", _no)

        assert GC._load_ed_public("IRB") is None

    def test_systemexit_khong_bi_nuot(self, tmp_path, monkeypatch):
        fake_pub = tmp_path / "fake.pub"
        fake_pub.write_bytes(b"khong quan trong")
        monkeypatch.setattr(GC, "_ed_public_path", lambda group: fake_pub)

        import cryptography.hazmat.primitives.serialization as ser_mod

        def _thoat(*a, **kw):
            raise SystemExit(1)

        monkeypatch.setattr(ser_mod, "load_pem_public_key", _thoat)

        with pytest.raises(SystemExit):
            GC._load_ed_public("IRB")


class TestSignApprovalEd25519BatBaseException:
    def test_base_exception_bi_bat_tra_none(self, monkeypatch):
        class _FakePriv:
            def sign(self, payload):
                raise _GiaLapPanicException("gia lap")

        monkeypatch.setattr(GC, "_load_ed_private", lambda group: _FakePriv())

        ket_qua = GC.sign_approval_ed25519(
            "G2", "PYTEST-STUDY", "deadbeef", "2026-09-10T00:00:00Z",
            reviewer_role=ROLE,
        )
        assert ket_qua is None

    def test_keyboardinterrupt_khong_bi_nuot(self, monkeypatch):
        class _FakePriv:
            def sign(self, payload):
                raise KeyboardInterrupt()

        monkeypatch.setattr(GC, "_load_ed_private", lambda group: _FakePriv())

        with pytest.raises(KeyboardInterrupt):
            GC.sign_approval_ed25519(
                "G2", "PYTEST-STUDY", "deadbeef", "2026-09-10T00:00:00Z",
                reviewer_role=ROLE,
            )


class TestVerifyApprovalSignatureEd1BatBaseException:
    def _record(self):
        return {
            "gate_id": "G2",
            "evidence_hash": "deadbeef",
            "timestamp_utc": "2026-09-10T00:00:00Z",
            "reviewer_role": ROLE,
            "reviewer_identity_reference": "dr-test",
            "decision": "APPROVED",
            "is_synthetic": False,
            "prev_hash": "",
            "approver_signature": "ed1:role:" + "ab" * 32,
        }

    def test_base_exception_bi_bat_tra_false(self, monkeypatch):
        class _FakePub:
            def verify(self, sig, payload):
                raise _GiaLapPanicException("gia lap InvalidSignature khong that")

        monkeypatch.setattr(GC, "_load_ed_public", lambda group: _FakePub())

        assert GC.verify_approval_signature(self._record(), "PYTEST-STUDY") is False

    def test_keyboardinterrupt_khong_bi_nuot(self, monkeypatch):
        class _FakePub:
            def verify(self, sig, payload):
                raise KeyboardInterrupt()

        monkeypatch.setattr(GC, "_load_ed_public", lambda group: _FakePub())

        with pytest.raises(KeyboardInterrupt):
            GC.verify_approval_signature(self._record(), "PYTEST-STUDY")

    def test_doi_chung_invalidsignature_that_van_tra_false(self, monkeypatch):
        """Đối chứng: InvalidSignature (Exception thường, ca PHỔ BIẾN NHẤT —
        chữ ký sai/hỏng) vẫn phải trả False như cũ, không bị bản vá làm hồi quy."""
        class _InvalidSignatureGiaLap(Exception):
            pass

        class _FakePub:
            def verify(self, sig, payload):
                raise _InvalidSignatureGiaLap()

        monkeypatch.setattr(GC, "_load_ed_public", lambda group: _FakePub())

        assert GC.verify_approval_signature(self._record(), "PYTEST-STUDY") is False


class TestSetupGateApprovalKeyEd25519GenerateBaseException:
    def _chuan_bi(self, tmp_path, monkeypatch, argv_extra):
        monkeypatch.setattr(SGAK, "BASE", tmp_path)
        monkeypatch.setattr(SGAK, "_KEY_PATH", tmp_path / ".ebm-secrets" / "gate_approval_key")
        monkeypatch.setattr(sys, "argv", ["setup_gate_approval_key.py", *argv_extra])

    def test_cai_hong_nua_chung_thoat_ma_2_va_phan_biet_thong_diep(
        self, tmp_path, monkeypatch, capsys,
    ):
        self._chuan_bi(tmp_path, monkeypatch, ["--ed25519", "--role", "IRB"])

        import cryptography.hazmat.primitives.asymmetric.ed25519 as ed25519_mod

        class _KhoaGiaHong:
            @staticmethod
            def generate():
                raise _GiaLapPanicException("gia lap cffi backend hong")

        monkeypatch.setattr(ed25519_mod, "Ed25519PrivateKey", _KhoaGiaHong)

        ma_thoat = SGAK.main()

        assert ma_thoat == 2
        ra = capsys.readouterr().out
        assert "HỎNG NỬA CHỪNG" in ra
        assert "force-reinstall" in ra
        # Không được tạo file khóa nào khi generate() nổ giữa chừng.
        assert not (tmp_path / ".ebm-secrets" / "gate_approval_key").parent.exists() or not list(
            (tmp_path / ".ebm-secrets").glob("gate_ed25519_*.key")
        )

    def test_keyboardinterrupt_khong_bi_nuot(self, tmp_path, monkeypatch):
        self._chuan_bi(tmp_path, monkeypatch, ["--ed25519", "--role", "IRB"])

        import cryptography.hazmat.primitives.asymmetric.ed25519 as ed25519_mod

        class _KhoaGiaNgat:
            @staticmethod
            def generate():
                raise KeyboardInterrupt()

        monkeypatch.setattr(ed25519_mod, "Ed25519PrivateKey", _KhoaGiaNgat)

        with pytest.raises(KeyboardInterrupt):
            SGAK.main()

    def test_doi_chung_sinh_khoa_that_van_hoat_dong_binh_thuong(self, tmp_path, monkeypatch):
        """Đối chứng: đường chạy THẬT (cryptography lành, generate() thành công)
        không bị bản vá làm hồi quy — vẫn tạo đủ cặp khóa như trước."""
        self._chuan_bi(tmp_path, monkeypatch, ["--ed25519", "--role", "STATISTICIAN"])

        ma_thoat = SGAK.main()

        assert ma_thoat == 0
        priv_path = (tmp_path / ".ebm-secrets" / "gate_approval_key").parent / "gate_ed25519_STATISTICIAN.key"
        pub_path = tmp_path / "config" / "gate_ed25519_pubkeys" / "STATISTICIAN.pub"
        assert priv_path.exists()
        assert pub_path.exists()
