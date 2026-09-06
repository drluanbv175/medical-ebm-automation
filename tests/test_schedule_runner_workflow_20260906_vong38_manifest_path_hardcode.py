"""Hồi quy phát hiện #4 (audit vòng 38, 2026-09-06) trong
research_automation/schedule_runner.py::check_manifest_integrity().

CƠ CHẾ LỖI (TRƯỚC bản vá):
    in_repo = "medical-ebm-automation/runtime/manifests" in str(mb).replace("\\\\", "/")

Đây là chuỗi con LITERAL TÊN THƯ MỤC CHECKOUT, không phải vị trí thật của
manifest. Repo clone/checkout vào thư mục tên khác (fork, CI runner,
worktree, mount point đổi tên) khiến manifest ĐÚNG NỘI DUNG/HASH 100% vẫn bị
báo MANIFEST_NOT_IN_REPO — false integrity failure hoàn toàn không liên
quan tới tính toàn vẹn thật của file.

BẢN VÁ: so `mb.resolve() == IN_REPO_MANIFEST_PATH.resolve()` — vị trí THẬT
tính từ Path(__file__) của chính runtime/agent_registry.py (BASE_DIR =
Path(__file__).parent.parent), không phụ thuộc tên thư mục checkout."""
from __future__ import annotations

import pathlib
import tempfile

from research_automation import schedule_runner
from runtime.agent_registry import IN_REPO_MANIFEST_PATH


class TestCaChinhTenThuMucCheckoutKhongAnhHuongKetQua:
    """★★★ Ca chính — manifest CANONICAL THẬT (không phải bản sao) nhưng nằm
    dưới một đường dẫn KHÔNG chứa chuỗi "medical-ebm-automation" (mô phỏng
    checkout/fork/CI runner đặt tên thư mục khác) vẫn phải được nhận diện
    ĐÚNG VỊ TRÍ. Patch CẢ HAI SCOPE_A_MANIFEST_PATH và IN_REPO_MANIFEST_PATH
    cùng trỏ một chỗ — mô phỏng "đây chính là file canonical, chỉ khác tên
    thư mục checkout", KHÁC với việc đặt một BẢN SAO ở nơi khác (trường hợp
    đó cả code cũ lẫn mới đều đúng khi báo NOT_IN_REPO, không phân biệt được
    hai hành vi)."""

    def test_duong_dan_canonical_khong_chua_ten_thu_muc_van_duoc_nhan_dung(self):
        with tempfile.TemporaryDirectory(prefix="not_medical_ebm_") as tmp:
            fake_dir = pathlib.Path(tmp) / "some-other-checkout-name" / "runtime" / "manifests"
            fake_dir.mkdir(parents=True)
            fake_path = fake_dir / "agent_source_manifest.csv"
            fake_path.write_bytes(IN_REPO_MANIFEST_PATH.read_bytes())

            # getattr(..., None) thay vì đọc thẳng thuộc tính: bản CHƯA vá
            # không import IN_REPO_MANIFEST_PATH vào schedule_runner — đọc
            # thẳng sẽ raise AttributeError (vẫn là một dạng "đỏ" hợp lệ khi
            # mutation-test, nhưng getattr cho lỗi rõ ràng hơn khi so sánh
            # hai phiên bản test cùng chạy được).
            orig_scope = schedule_runner.SCOPE_A_MANIFEST_PATH
            orig_in_repo = getattr(schedule_runner, "IN_REPO_MANIFEST_PATH", None)
            schedule_runner.SCOPE_A_MANIFEST_PATH = fake_path
            schedule_runner.IN_REPO_MANIFEST_PATH = fake_path
            try:
                # Nội dung sao y hệt IN_REPO_MANIFEST_PATH thật → hash mặc
                # định (MANIFEST_SELF_CHECK_SHA256) đã khớp sẵn, không cần
                # truyền expected_sha riêng.
                rep = schedule_runner.check_manifest_integrity()
            finally:
                schedule_runner.SCOPE_A_MANIFEST_PATH = orig_scope
                if orig_in_repo is None:
                    del schedule_runner.IN_REPO_MANIFEST_PATH
                else:
                    schedule_runner.IN_REPO_MANIFEST_PATH = orig_in_repo

            assert "MANIFEST_NOT_IN_REPO" not in rep.findings, (
                "TRƯỚC bản vá: so chuỗi con literal "
                "'medical-ebm-automation/runtime/manifests' — đường dẫn giả "
                "'some-other-checkout-name/runtime/manifests' không chứa "
                "chuỗi đó nên bị báo NOT_IN_REPO dù đây chính là file "
                "canonical (SCOPE_A_MANIFEST_PATH == IN_REPO_MANIFEST_PATH)."
            )
            assert rep.ok is True


class TestDoiChungDuongDanThatVanOkNhuCu:
    """Đối chứng — manifest ở đúng vị trí canonical (SCOPE_A_MANIFEST_PATH
    mặc định, không override) vẫn PASS như cũ, bất kể tên thư mục checkout
    thật của máy đang chạy test là gì."""

    def test_duong_dan_that_van_ok(self):
        rep = schedule_runner.check_manifest_integrity()
        assert rep.ok is True
        assert rep.findings == []

    def test_hash_sai_van_bi_bat_nhu_cu(self):
        rep = schedule_runner.check_manifest_integrity(expected_sha="0" * 64)
        assert rep.ok is False
        assert any(f.startswith("MANIFEST_HASH_MISMATCH") for f in rep.findings)

    def test_manifest_khong_ton_tai_van_bi_bat_nhu_cu(self):
        orig = schedule_runner.SCOPE_A_MANIFEST_PATH
        schedule_runner.SCOPE_A_MANIFEST_PATH = pathlib.Path("/tmp/khong-ton-tai-vong38.csv")
        try:
            rep = schedule_runner.check_manifest_integrity()
        finally:
            schedule_runner.SCOPE_A_MANIFEST_PATH = orig
        assert rep.ok is False
        assert rep.findings == ["MANIFEST_MISSING"]
