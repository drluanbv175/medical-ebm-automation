"""Hồi quy phát hiện #2 (audit vòng 38, 2026-09-06) trong
research_automation/workflow_runner.py::WorkflowRunner.run().

CƠ CHẾ LỖI (TRƯỚC bản vá):
    for art in proj_result.artifacts:
        self.artifacts.register(art)
    ...
    for art in proj_result.artifacts:
        rec.artifact_hashes[art.artifact_id] = RunRegistry.hash_obj(art.to_dict())
        ...
        item = self.review_queue.add(..., artifact_id=art.artifact_id, ...)

`artifact_id` được sinh TẤT ĐỊNH chỉ từ `project_id:artifact_type`
(research_studio/research_workflow.py), và `ArtifactRegistry.register()`
idempotent theo artifact_id — lần đăng ký sau với cùng ID bị ÂM THẦM bỏ qua,
giữ nguyên nội dung của lần đầu (đúng thiết kế đã ghi trong docstring của
register()). `IdempotencyGuard` chỉ chặn khi request_hash GIỐNG HỆT — nếu
chạy lại CÙNG project_id với NỘI DUNG KHÁC (vd sửa title), request_hash khác
→ KHÔNG bị coi duplicate → workflow chạy lại từ đầu.

Bản cũ lặp lại trên `proj_result.artifacts` (object CỤC BỘ vừa build ở
scratch registry của run này) thay vì dùng GIÁ TRỊ TRẢ VỀ của register()
(object THẬT đang lưu) — hai hệ quả:
1. `rec.artifact_hashes[...]` ghi hash của nội dung MỚI chưa bao giờ thực sự
   được lưu (register() đã giữ bản CŨ) — sổ audit (tự khai "append-only,
   audit-grade") ghi sai truy nguyên.
2. `review_queue` nhận thêm MỘT item TRÙNG cho cùng artifact_id không có nội
   dung mới để duyệt — người duyệt thấy 2 việc cần duyệt cho cùng 1 artifact.

BẢN VÁ: dùng `registered = [self.artifacts.register(art) for art in
proj_result.artifacts]`, và bỏ qua hash/review-item khi `stored is not art`
(nội dung này chưa từng được lưu — register() đã trả về bản cũ)."""
from __future__ import annotations

from research_automation.run_registry import RunRegistry
from research_automation.workflow_runner import WorkflowRunner
from tests.test_v4_3_2_automation import _req, reset_guard_context


def setup_function():
    reset_guard_context()


def teardown_function():
    reset_guard_context()


class TestCaChinhCungProjectIdKhacNoiDungKhongTaoDuLieuSaiTraiNguyen:
    """★★★ Ca chính — chạy lại CÙNG project_id với title KHÁC (khác
    request_hash, không bị idempotency guard chặn) không được tạo review
    item trùng, và sổ audit không được ghi hash của nội dung chưa từng lưu."""

    def test_khong_tao_review_item_trung(self):
        runner = WorkflowRunner()
        r1 = runner.run(_req(pid="PDUP2", title="Title version A"))
        r2 = runner.run(_req(pid="PDUP2", title="Title version B"))
        assert r1.status == "CREATED" and r2.status == "CREATED"

        n_artifacts = len(runner.artifacts.for_project("PDUP2"))
        assert runner.review_queue.count() == n_artifacts, (
            "TRƯỚC bản vá: mỗi artifact_id nhận 2 review item (1 từ mỗi lần "
            f"run) — count()={runner.review_queue.count()}, "
            f"số artifact_id thật={n_artifacts}"
        )

    def test_so_audit_khong_ghi_hash_noi_dung_chua_tung_luu(self):
        runner = WorkflowRunner()
        runner.run(_req(pid="PDUP3", title="Title version A"))
        r2 = runner.run(_req(pid="PDUP3", title="Title version B"))

        rec2 = runner.run_registry.get(r2.run_id)
        # run2 không tạo nội dung mới nào (mọi artifact_id đã tồn tại từ
        # run1) — rec2.artifact_hashes phải RỖNG, không được ghi hash "ma"
        # của nội dung chưa từng lưu.
        assert rec2.artifact_hashes == {}, (
            "TRƯỚC bản vá: rec2.artifact_hashes ghi hash của object CỤC BỘ "
            "vừa build ở run2 (nội dung 'Title version B'), trong khi "
            "register() đã âm thầm giữ bản CŨ (run1) — hash ghi trong sổ "
            "audit LỆCH với nội dung artifact thật sự đang lưu."
        )

    def test_noi_dung_artifact_giu_nguyen_ban_dau_dung_thiet_ke_idempotent(self):
        runner = WorkflowRunner()
        r1 = runner.run(_req(pid="PDUP4", title="Title version A"))
        runner.run(_req(pid="PDUP4", title="Title version B"))

        arts = {a.artifact_id: a for a in runner.artifacts.for_project("PDUP4")}
        arts_r1 = {a.artifact_id: a for a in r1.artifacts}
        for aid, art in arts.items():
            assert art.workflow_run_id == arts_r1[aid].workflow_run_id, (
                "register() phải giữ bản của run1 (đúng thiết kế idempotent "
                "theo artifact_id) — run2 không được ghi đè nội dung."
            )


class TestDoiChungRunDauTienVaProjectKhacNhauKhongDoi:
    """Đối chứng — run đầu tiên của một project_id (chưa có artifact_id nào
    tồn tại trước) vẫn tạo đủ review item + hash như cũ; hai project_id
    KHÁC NHAU không ảnh hưởng lẫn nhau."""

    def test_run_dau_tien_van_du_review_item(self):
        runner = WorkflowRunner()
        r1 = runner.run(_req(pid="PSINGLE1"))
        assert r1.status == "CREATED"
        assert len(r1.review_items) == len(r1.artifacts)
        rec1 = runner.run_registry.get(r1.run_id)
        assert len(rec1.artifact_hashes) == len(r1.artifacts)
        for a in r1.artifacts:
            assert rec1.artifact_hashes[a.artifact_id] == RunRegistry.hash_obj(a.to_dict())

    def test_project_khac_nhau_khong_bi_anh_huong(self):
        runner = WorkflowRunner()
        r1 = runner.run(_req(pid="PINDEP-A"))
        r2 = runner.run(_req(pid="PINDEP-B"))
        assert r1.status == "CREATED" and r2.status == "CREATED"
        assert runner.review_queue.count() == len(r1.artifacts) + len(r2.artifacts)

    def test_duplicate_request_giong_het_van_bi_chan_boi_idempotency_nhu_cu(self):
        runner = WorkflowRunner()
        req = _req(pid="PSAMEHASH")
        r1 = runner.run(req)
        n1 = runner.review_queue.count()
        r2 = runner.run(req)
        assert r1.status == "CREATED" and r2.status == "DUPLICATE"
        assert runner.review_queue.count() == n1
