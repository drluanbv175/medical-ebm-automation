r"""Hồi quy 3 phát hiện (vòng 43, 2026-09-07) trong run.py và
chronic-care-clinic-os/scripts/{run_node_tests,typecheck_app}.py — 4 file Python
CUỐI CÙNG trong repo chưa từng qua audit thật (đã dò bằng `git log --all --
<file>` cho toàn bộ cây, không chỉ file mẫu — 42 vòng trước đã quét sạch
app/, tools/, runtime/, research_studio/, research_automation/,
research_project/, scripts/). Cả 3 phát hiện được xác nhận bằng workflow đa
agent (3 lăng kính tìm độc lập + 3 lượt phản biện đối kháng mỗi phát hiện,
26/27 phiếu "không bác bỏ được"), cộng với tái hiện thực nghiệm trực tiếp của
phiên điều phối (node v22.22.2 thật cho phát hiện #1, thư mục .pnpm giả lập
cho phát hiện #2) TRƯỚC khi vá.

── PHÁT HIỆN #1 (HIGH) — run_node_tests.py: mjs_test_files rỗng nhưng
   ts_test_files không rỗng ⇒ truyền ZERO đối số vị trí cho `node --test` ──
CƠ CHẾ LỖI (TRƯỚC bản vá):
    mjs_result = subprocess.run(
        [node, "--test", *[str(path) for path in mjs_test_files]],  # rỗng!
        cwd=ROOT, check=False,
    )
    if mjs_result.returncode != 0 or not ts_test_files:
        return mjs_result.returncode

Guard đầu file `if not mjs_test_files and not ts_test_files: raise SystemExit(...)`
chỉ bắt trường hợp CẢ HAI rỗng (AND), bỏ sót trường hợp CHỈ mjs_test_files
rỗng. Khi đó lệnh thực thi là `node --test` KHÔNG có file nào — đã tái hiện
thực nghiệm bằng Node v22.22.2 thật: `node --test` không có đối số vị trí
KHÔNG no-op mà tự chuyển sang chế độ TỰ DÒ TÌM file test theo quy ước riêng
của Node trên toàn bộ cwd — có thể trả về 0 (nếu không khớp gì, che giấu
việc bước mjs coi như "thành công" dù không chạy file nào được yêu cầu) hoặc
chạy nhầm file KHÔNG liên quan rồi trả exit code của file đó, khiến dòng
`or not ts_test_files` phía sau (vốn không bao giờ được xét tới vì OR đã
short-circuit ở vế đầu) làm toàn bộ hàm return SỚM, bỏ qua hẳn bước biên
dịch+chạy các file `.test.ts` thật sự tồn tại.

── PHÁT HIỆN #2 (MEDIUM) — typecheck_app.py::find_tsc(): sort CHUỖI thay vì
   SỐ khi chọn bản TypeScript trong kho pnpm ──
CƠ CHẾ LỖI (TRƯỚC bản vá):
    matches = sorted((ROOT/"node_modules"/".pnpm").glob(
        "typescript@*/node_modules/typescript/bin/tsc"))
    return matches[-1]

`sorted()` so sánh theo TỪNG KÝ TỰ nên "typescript@10.0.0" < "typescript@9.0.0"
(ký tự '1' < '9' ở vị trí khác nhau đầu tiên) — đã tái hiện thực nghiệm bằng
thư mục giả `typescript@9.0.0/` và `typescript@10.0.0/` cùng tồn tại:
`matches[-1]` chọn NHẦM bản 9.0.0 (CŨ HƠN) dù ý đồ rõ ràng của code là "chọn
bản MỚI NHẤT" (mới sort rồi lấy phần tử cuối). Kho pnpm content-addressable
hoàn toàn có thể giữ nhiều bản typescript cùng lúc qua các lần cập nhật
lockfile.

── PHÁT HIỆN #3 (MEDIUM) — run.py: nhánh `dossier` trả mã thoát 0 (thành
   công) ngay cả khi KHÔNG tìm thấy đề tài ──
CƠ CHẾ LỖI (TRƯỚC bản vá):
    path = export_research_dossier(sys.argv[2])
    _print({"dossier": str(path) if path else None,
            "note": None if path else "Không tìm thấy đề tài"})
    # (không có return nào ở đây — rơi xuống `return 0` cuối main())

`export_research_dossier()` (app/research/dossier.py:197-206) trả về `None`
khi không tìm thấy đề tài — đã xác minh trực tiếp trong source. Nhánh xử lý
IN RA đúng ghi chú "Không tìm thấy đề tài" nhưng KHÔNG return mã lỗi, khác
hẳn nhánh chị em 3 dòng phía trên cùng khối `dossier` (`if len(sys.argv) < 3:
...; return 1`) VỐN đã return đúng khi thiếu đối số. Một script/CI/lịch nền
gọi `python run.py dossier <mã>` rồi kiểm tra exit code sẽ thấy "thành công"
giống hệt nhau dù đề tài có thật hay chỉ là gõ sai mã."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "chronic-care-clinic-os" / "scripts"


class _FakeCompleted:
    def __init__(self, returncode: int = 0) -> None:
        self.returncode = returncode


@pytest.fixture()
def ccos_scripts(monkeypatch):
    """Nạp lại node_runtime/typecheck_app/run_node_tests đúng khuôn sibling-
    import mà chính các script này dùng (thêm thư mục của chúng vào sys.path,
    giống hệt hành vi Python tự làm khi chạy `python <path>/run_node_tests.py`
    trực tiếp)."""
    monkeypatch.syspath_prepend(str(SCRIPTS_DIR))
    for name in ("node_runtime", "typecheck_app", "run_node_tests"):
        sys.modules.pop(name, None)
    node_runtime = importlib.import_module("node_runtime")
    typecheck_app = importlib.import_module("typecheck_app")
    run_node_tests = importlib.import_module("run_node_tests")
    try:
        yield {
            "node_runtime": node_runtime,
            "typecheck_app": typecheck_app,
            "run_node_tests": run_node_tests,
        }
    finally:
        for name in ("node_runtime", "typecheck_app", "run_node_tests"):
            sys.modules.pop(name, None)


def _make_app_tree(tmp_path: Path, *, mjs: bool, ts: bool) -> Path:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)
    if mjs:
        (tests_dir / "clinic-os.test.mjs").write_text(
            "// fake mjs test\n", encoding="utf-8", newline="\n"
        )
    if ts:
        (tests_dir / "sample.behavior.test.ts").write_text(
            "// fake ts test\n", encoding="utf-8", newline="\n"
        )
    return tmp_path


class TestPhatHien1MjsRongTsKhongRong:
    """★★★ Ca chính — mjs_test_files rỗng, ts_test_files không rỗng: KHÔNG
    được gọi `node --test` với đối số vị trí rỗng."""

    def test_khong_goi_node_test_voi_argv_rong(self, ccos_scripts, tmp_path, monkeypatch):
        run_node_tests = ccos_scripts["run_node_tests"]
        app_root = _make_app_tree(tmp_path, mjs=False, ts=True)
        monkeypatch.setattr(run_node_tests, "ROOT", app_root)
        monkeypatch.setattr(run_node_tests, "find_node", lambda: Path("FAKE_NODE"))
        monkeypatch.setattr(run_node_tests, "find_tsc", lambda: Path("FAKE_TSC"))

        calls = []

        def fake_run(argv, cwd=None, check=False):
            calls.append(list(argv))
            return _FakeCompleted(returncode=0)

        monkeypatch.setattr(run_node_tests.subprocess, "run", fake_run)

        exit_code = run_node_tests.main()

        bare_test_calls = [c for c in calls if c == ["FAKE_NODE", "--test"]]
        assert not bare_test_calls, (
            "TRƯỚC bản vá: mjs_test_files rỗng vẫn tạo lệnh `[node, '--test']` "
            "hoàn toàn không có file nào -- kích hoạt auto-discovery của Node "
            f"thay vì bỏ qua bước mjs. Các lệnh subprocess.run thực tế: {calls}"
        )
        assert exit_code == 0

    def test_van_chay_duoc_buoc_ts_sau_khi_bo_qua_mjs(self, ccos_scripts, tmp_path, monkeypatch):
        """Sau khi bỏ qua bước mjs (không có file), hàm phải TIẾP TỤC biên
        dịch + chạy .test.ts, không được return sớm."""
        run_node_tests = ccos_scripts["run_node_tests"]
        app_root = _make_app_tree(tmp_path, mjs=False, ts=True)
        monkeypatch.setattr(run_node_tests, "ROOT", app_root)
        monkeypatch.setattr(run_node_tests, "find_node", lambda: Path("FAKE_NODE"))
        monkeypatch.setattr(run_node_tests, "find_tsc", lambda: Path("FAKE_TSC"))

        calls = []

        def fake_run(argv, cwd=None, check=False):
            calls.append(list(argv))
            return _FakeCompleted(returncode=0)

        monkeypatch.setattr(run_node_tests.subprocess, "run", fake_run)
        run_node_tests.main()

        assert any("FAKE_TSC" in str(part) for c in calls for part in c), (
            "Bước biên dịch TypeScript (dùng find_tsc()) phải được gọi -- "
            f"lệnh thực tế: {calls}"
        )


class TestDoiChungHanhViCuVanDung:
    """Đối chứng — 3 tổ hợp còn lại của (mjs rỗng/không, ts rỗng/không)
    KHÔNG bị ảnh hưởng bởi bản vá."""

    def test_ca_hai_khong_rong_van_truyen_dung_file_mjs(self, ccos_scripts, tmp_path, monkeypatch):
        run_node_tests = ccos_scripts["run_node_tests"]
        app_root = _make_app_tree(tmp_path, mjs=True, ts=True)
        monkeypatch.setattr(run_node_tests, "ROOT", app_root)
        monkeypatch.setattr(run_node_tests, "find_node", lambda: Path("FAKE_NODE"))
        monkeypatch.setattr(run_node_tests, "find_tsc", lambda: Path("FAKE_TSC"))
        calls = []
        monkeypatch.setattr(
            run_node_tests.subprocess, "run",
            lambda argv, cwd=None, check=False: (calls.append(list(argv)), _FakeCompleted(0))[1],
        )
        run_node_tests.main()
        first_call = calls[0]
        assert "clinic-os.test.mjs" in " ".join(first_call), (
            f"Lệnh mjs đầu tiên phải chứa đúng file .test.mjs thật: {first_call}"
        )

    def test_chi_mjs_khong_co_ts_dung_1_lan_goi_va_tra_ve_dung(self, ccos_scripts, tmp_path, monkeypatch):
        run_node_tests = ccos_scripts["run_node_tests"]
        app_root = _make_app_tree(tmp_path, mjs=True, ts=False)
        monkeypatch.setattr(run_node_tests, "ROOT", app_root)
        monkeypatch.setattr(run_node_tests, "find_node", lambda: Path("FAKE_NODE"))
        calls = []
        monkeypatch.setattr(
            run_node_tests.subprocess, "run",
            lambda argv, cwd=None, check=False: (calls.append(list(argv)), _FakeCompleted(0))[1],
        )
        exit_code = run_node_tests.main()
        assert len(calls) == 1, f"Chỉ nên gọi subprocess.run đúng 1 lần (bước mjs): {calls}"
        assert exit_code == 0

    def test_mjs_that_bai_dung_return_som_khong_chay_ts(self, ccos_scripts, tmp_path, monkeypatch):
        run_node_tests = ccos_scripts["run_node_tests"]
        app_root = _make_app_tree(tmp_path, mjs=True, ts=True)
        monkeypatch.setattr(run_node_tests, "ROOT", app_root)
        monkeypatch.setattr(run_node_tests, "find_node", lambda: Path("FAKE_NODE"))
        monkeypatch.setattr(run_node_tests, "find_tsc", lambda: Path("FAKE_TSC"))
        calls = []

        def fake_run(argv, cwd=None, check=False):
            calls.append(list(argv))
            return _FakeCompleted(returncode=1)

        monkeypatch.setattr(run_node_tests.subprocess, "run", fake_run)
        exit_code = run_node_tests.main()
        assert exit_code == 1
        assert len(calls) == 1, (
            f"mjs thất bại phải return NGAY, không được chạy tiếp bước ts: {calls}"
        )

    def test_ca_hai_rong_van_bao_loi_ro_rang(self, ccos_scripts, tmp_path, monkeypatch):
        run_node_tests = ccos_scripts["run_node_tests"]
        app_root = _make_app_tree(tmp_path, mjs=False, ts=False)
        monkeypatch.setattr(run_node_tests, "ROOT", app_root)
        with pytest.raises(SystemExit):
            run_node_tests.main()


class TestPhatHien2FindTscChonDungBanMoiNhat:
    """★★★ Ca chính — find_tsc() phải chọn bản TypeScript MỚI NHẤT theo
    SỐ, không phải theo chuỗi."""

    def _make_pnpm_store(self, tmp_path: Path, versions: list) -> Path:
        pnpm_dir = tmp_path / "node_modules" / ".pnpm"
        for v in versions:
            tsc_path = pnpm_dir / f"typescript@{v}" / "node_modules" / "typescript" / "bin"
            tsc_path.mkdir(parents=True)
            (tsc_path / "tsc").write_text("#!/usr/bin/env node\n", encoding="utf-8", newline="\n")
        return tmp_path

    def test_chon_ban_10_thay_vi_ban_9(self, ccos_scripts, tmp_path, monkeypatch):
        typecheck_app = ccos_scripts["typecheck_app"]
        app_root = self._make_pnpm_store(tmp_path, ["9.0.0", "10.0.0"])
        monkeypatch.setattr(typecheck_app, "ROOT", app_root)

        result = typecheck_app.find_tsc()

        assert "typescript@10.0.0" in str(result), (
            "TRƯỚC bản vá: sort chuỗi khiến 'typescript@10.0.0' < "
            f"'typescript@9.0.0' -- find_tsc() chọn nhầm bản 9.0.0 cũ hơn. "
            f"Kết quả thực tế: {result}"
        )

    def test_chon_ban_moi_trong_bo_5_diem(self, ccos_scripts, tmp_path, monkeypatch):
        typecheck_app = ccos_scripts["typecheck_app"]
        app_root = self._make_pnpm_store(
            tmp_path, ["5.9.0", "5.10.0", "5.2.1", "5.10.10", "5.10.2"]
        )
        monkeypatch.setattr(typecheck_app, "ROOT", app_root)
        result = typecheck_app.find_tsc()
        assert "typescript@5.10.10" in str(result), f"Kết quả thực tế: {result}"


class TestDoiChungFindTscMotBanVanDung:
    """Đối chứng — chỉ có một bản TypeScript thì vẫn được chọn đúng như cũ."""

    def test_mot_ban_duy_nhat(self, ccos_scripts, tmp_path, monkeypatch):
        typecheck_app = ccos_scripts["typecheck_app"]
        pnpm_dir = tmp_path / "node_modules" / ".pnpm"
        tsc_path = pnpm_dir / "typescript@5.7.2" / "node_modules" / "typescript" / "bin"
        tsc_path.mkdir(parents=True)
        (tsc_path / "tsc").write_text("#!/usr/bin/env node\n", encoding="utf-8", newline="\n")
        monkeypatch.setattr(typecheck_app, "ROOT", tmp_path)
        result = typecheck_app.find_tsc()
        assert "typescript@5.7.2" in str(result)

    def test_khong_co_ban_nao_bao_loi(self, ccos_scripts, tmp_path, monkeypatch):
        typecheck_app = ccos_scripts["typecheck_app"]
        monkeypatch.setattr(typecheck_app, "ROOT", tmp_path)
        with pytest.raises(SystemExit):
            typecheck_app.find_tsc()


class TestPhatHien3RunPyDossierMaThoat:
    """★★★ Ca chính — nhánh `dossier` của run.py phải trả mã thoát khác 0
    khi không tìm thấy đề tài."""

    def test_khong_tim_thay_de_tai_tra_ve_1(self, monkeypatch):
        import app.research
        import run

        monkeypatch.setattr(sys, "argv", ["run.py", "dossier", "KHONG-TON-TAI-999"])
        monkeypatch.setattr(app.research, "export_research_dossier", lambda project_id, **kw: None)

        exit_code = run.main()

        assert exit_code == 1, (
            "TRƯỚC bản vá: nhánh dossier in đúng ghi chú 'Không tìm thấy đề "
            "tài' nhưng KHÔNG return mã lỗi, rơi xuống return 0 mặc định của "
            f"main(). Mã thoát thực tế: {exit_code}"
        )

    def test_tim_thay_de_tai_van_tra_ve_0(self, monkeypatch, tmp_path):
        import app.research
        import run

        fake_path = tmp_path / "Research_Dossier_TEST.md"
        fake_path.write_text("nội dung giả", encoding="utf-8", newline="\n")
        monkeypatch.setattr(sys, "argv", ["run.py", "dossier", "DE-TAI-THAT-001"])
        monkeypatch.setattr(app.research, "export_research_dossier", lambda project_id, **kw: fake_path)

        exit_code = run.main()

        assert exit_code == 0, "Đề tài tìm thấy được vẫn phải trả mã thoát 0 như cũ"
