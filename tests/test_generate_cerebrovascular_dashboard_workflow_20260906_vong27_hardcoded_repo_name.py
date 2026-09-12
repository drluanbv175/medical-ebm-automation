"""Hồi quy phát hiện #3 (Trung bình) của Workflow đối kháng đa-agent
2026-09-06 (vòng 27) trong
tools/generate_cerebrovascular_dashboard_20260723.py — đường dẫn "đã vá"
vẫn hardcode TÊN thư mục repo, tái phát cùng họ lỗi macOS/Windows từng
được đo là "🔴 duy nhất toàn kho" (chốt kiem_tuong_thich_da_nen ở repo
gốc, xem comment 15/08/2026 tại chỗ trong module).

CƠ CHẾ LỖI (TRƯỚC bản vá):
    ROOT = Path(__file__).resolve().parents[2]      # thư mục CHA của repo
    REPO = ROOT / "medical-ebm-automation"           # ghép TÊN cứng

Bản vá 15/08 thay MỘT hardcode (path Windows tuyệt đối) bằng MỘT
hardcode khác: tính ROOT (thư mục cha của repo) rồi ghép cứng chuỗi
"medical-ebm-automation" để suy ngược lại vị trí repo — chỉ đúng NẾU
thư mục checkout thực sự tên đúng y hệt vậy. Mọi file "chị em" khác
trong kho (tools/verify_evidence_surveillance_deployment.py,
tools/verify_clinical_evidence_agent_standards.py) đều lấy repo root
TRỰC TIẾP bằng Path(__file__).resolve().parents[1] — không phụ thuộc
tên thư mục.

HẠI THẬT: clone/worktree với tên khác (vd "medical-ebm-automation-fix",
hoặc git worktree đặt tên theo branch) khiến REPO trỏ sai chỗ,
sys.path.insert chèn một đường dẫn không tồn tại,
"from app.reports.evidence_workbench import ..." ném ModuleNotFoundError
— tái hiện đúng triệu chứng ban đầu ("tool CHƯA TỪNG chạy được") dưới
dạng khác.

BẢN VÁ: REPO tính TRỰC TIẾP bằng Path(__file__).resolve().parents[1]
(khớp quy ước 2 module chị em ở trên); ROOT suy từ REPO.parent.

★ GHI CHÚ TRUNG THỰC VỀ GIỚI HẠN MUTATION TEST ★
Thư mục checkout của CHÍNH sandbox này tình cờ đúng tên
"medical-ebm-automation", nên công thức CŨ (ghép tên cứng) và công thức
MỚI (parents[1]) tính ra CÙNG một giá trị REPO ở đây — một test hành vi
thuần túy (gọi module thật, so giá trị REPO) sẽ pass trên CẢ bản gốc
lẫn bản vá, không phân biệt được. Đây không phải lỗi của test mà là bản
chất của lỗi portability (chỉ lộ ra khi TÊN THƯ MỤC khác đi). Vì vậy:
- test_repo_bang_parents_1_khong_ghep_ten_cung KHÔNG mutation-phân-biệt
  được trong sandbox này — nó khoá ĐÚNG CÔNG THỨC hiện tại (giá trị
  regression thông thường), không phải bằng chứng phát hiện lỗi.
- test_khong_con_ghep_ten_thu_muc_cung (kiểm cấu trúc mã nguồn, không
  phải hành vi) MỚI là test THỰC SỰ phân biệt được bản gốc/bản vá — vì
  vậy được xếp là ca chính duy nhất có bằng chứng mutation test.
- TestMinhHoaCongThucCuSaiKhiDoiTenCheckout minh hoạ CƠ CHẾ (phép tính
  đường dẫn thuần, không đụng module thật) để người đọc hiểu TẠI SAO —
  nó luôn pass bất kể trạng thái module thật, không phải bằng chứng
  mutation test."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import generate_cerebrovascular_dashboard_20260723 as DASH  # noqa: E402


class TestRepoKhongPhuThuocTenThuMuc:
    """Khoá công thức ĐÚNG hiện tại (không mutation-phân-biệt được trong
    sandbox này — xem ghi chú giới hạn ở đầu file)."""

    def test_repo_bang_parents_1_khong_ghep_ten_cung(self):
        module_path = Path(DASH.__file__).resolve()
        assert DASH.REPO == module_path.parents[1]

    def test_root_la_cha_cua_repo(self):
        assert DASH.ROOT == DASH.REPO.parent

    def test_repo_ton_tai_that_tren_dia(self):
        assert DASH.REPO.exists() and DASH.REPO.is_dir()

    def test_sys_path_chua_dung_repo(self):
        assert str(DASH.REPO) in sys.path


class TestKhongConGhepCungTenThuMuc:
    """★★★ Ca chính — MUTATION-PHÂN-BIỆT ĐƯỢC. Kiểm CẤU TRÚC mã nguồn:
    dòng định nghĩa REPO không còn ghép chuỗi tên thư mục cứng."""

    def test_khong_con_ghep_ten_thu_muc_cung(self):
        source = Path(DASH.__file__).read_text(encoding="utf-8")
        dinh_nghia_repo = next(
            line for line in source.splitlines() if line.strip().startswith("REPO = ")
        )
        assert "medical-ebm-automation" not in dinh_nghia_repo, (
            "TRƯỚC bản vá: 'REPO = ROOT / \"medical-ebm-automation\"' ghép "
            "TÊN THƯ MỤC cứng — chỉ đúng khi checkout thực sự tên y hệt "
            "vậy. Dòng định nghĩa REPO phải tính từ __file__ trực tiếp, "
            "không được nhắc tới tên thư mục."
        )
        assert "parents[1]" in dinh_nghia_repo


class TestMinhHoaCongThucCuSaiKhiDoiTenCheckout:
    """Minh hoạ CƠ CHẾ (không phải regression cho module thật — phép
    tính đường dẫn thuần, luôn pass bất kể trạng thái module thật)."""

    def test_cong_thuc_cu_tro_sai_thu_muc_khi_checkout_doi_ten(self, tmp_path):
        checkout_ten_khac = tmp_path / "medical-ebm-automation-fix-branch-xyz"
        tools_dir_gia = checkout_ten_khac / "tools"
        tools_dir_gia.mkdir(parents=True)
        module_file_gia = tools_dir_gia / "generate_cerebrovascular_dashboard_20260723.py"
        module_file_gia.write_text("# placeholder\n", encoding="utf-8", newline="\n")

        repo_dung = module_file_gia.resolve().parents[1]
        assert repo_dung == checkout_ten_khac

        root_cu = module_file_gia.resolve().parents[2]
        repo_sai_theo_cong_thuc_cu = root_cu / "medical-ebm-automation"
        assert repo_sai_theo_cong_thuc_cu != checkout_ten_khac
