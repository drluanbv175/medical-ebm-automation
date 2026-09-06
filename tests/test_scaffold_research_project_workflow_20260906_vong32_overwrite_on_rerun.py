r"""Hồi quy phát hiện #3 (CRITICAL) của audit đa-agent 2026-09-06 (vòng 32)
trong tools/scaffold_research_project.py::scaffold() — gọi lại `scaffold()`
trên một đề tài ĐÃ TỒN TẠI sẽ ghi đè xóa sạch nội dung 20 file `.md` mà bác sĩ
đã điền, không cảnh báo, không backup.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    for num, fname, gate, artifact_key, title, body in SCAFFOLD_FILES:
        md_path = out / f"{num}_{fname}.md"
        header = (...)
        md_path.write_text(header + body, encoding="utf-8", newline="\n")   # LUÔN GHI ĐÈ

Vòng lặp ghi `.md` KHÔNG kiểm `md_path.exists()` — luôn ghi đè bằng nội dung
`body` placeholder cố định trong SCAFFOLD_FILES. Comment ngay bên dưới (ở
đoạn ghi study_meta.json) khẳng định thao tác scaffold là "non-destructive...
không đè nếu bác sĩ đã điền" — nhưng câu đó CHỈ đúng cho
`_GC.ensure_study_meta()`, KHÔNG đúng cho vòng lặp ghi `.md` phía trên.
`out.mkdir(parents=True, exist_ok=True)` còn chủ động cho phép chạy lại trên
thư mục đã tồn tại mà không báo lỗi.

Rủi ro thật: chính tài liệu vận hành (`.claude/agents/dieu-phoi-nghien-cuu.md`)
hướng dẫn "Đề tài MỚI → scaffold trước". Một lần gõ nhầm mã đề tài trùng với
đề tài đang chạy dở (hoặc một agent tưởng lệnh này idempotent giống
`regenerate_study_index()` — vốn CÓ cơ chế bảo tồn ghi chú tay) sẽ xóa vĩnh
viễn PICO/SAP/ICF/... đã điền, không có cách khôi phục nếu chưa commit git.

BẢN VÁ: kiểm `md_path.exists()` trước khi ghi — bỏ qua ĐÚNG entry (md + docx
cùng cặp, `continue` ngay sau khi bỏ qua md) khi file `.md` đã tồn tại, giữ
đúng lời hứa "non-destructive" cho MỌI file scaffold sinh ra, không chỉ
study_meta.json.

Nguyên tắc viết test: gọi `scaffold()` THẬT hai lần liên tiếp trên CÙNG một
thư mục tạm (`base_dir=tmp_path`), mô phỏng bác sĩ điền nội dung thật giữa
hai lần gọi — đúng kịch bản agent audit đã tái hiện."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import scaffold_research_project as SRP  # noqa: E402

_STUDY = "Vong32 Overwrite Repro"
_SLUG = _STUDY.replace(" ", "-")
_NOI_DUNG_BAC_SI_DIEN = "\nBệnh nhân đái tháo đường type 2, đã chốt bởi PI thật\n"


def _scaffold_lan_dau(tmp_path):
    SRP.scaffold(_STUDY, base_dir=str(tmp_path), with_docx=False)
    return tmp_path / _SLUG


class TestScaffoldLaiKhongXoaNoiDungBacSiDaDien:
    """★★★ Ca chính — gọi lại scaffold() trên đề tài đã có nội dung KHÔNG
    được xóa mất nội dung đó."""

    def test_noi_dung_song_sot_sau_lan_goi_thu_hai(self, tmp_path):
        out = _scaffold_lan_dau(tmp_path)
        target = out / f"{SRP.SCAFFOLD_FILES[0][0]}_{SRP.SCAFFOLD_FILES[0][1]}.md"
        assert target.exists()

        with target.open("a", encoding="utf-8") as f:
            f.write(_NOI_DUNG_BAC_SI_DIEN)
        truoc = target.read_text(encoding="utf-8")
        assert "PI thật" in truoc

        SRP.scaffold(_STUDY, base_dir=str(tmp_path), with_docx=False)

        sau = target.read_text(encoding="utf-8")
        assert "PI thật" in sau, (
            "TRƯỚC bản vá: vòng lặp ghi .md không kiểm tồn tại, luôn ghi đè "
            f"bằng placeholder gốc — nội dung bác sĩ đã điền bị xóa sạch. Nội "
            f"dung sau lần gọi thứ hai: {sau!r}"
        )
        assert sau == truoc, "Nội dung phải giữ NGUYÊN VẸN, không chỉ 'còn sót lại một phần'"

    def test_moi_file_trong_20_file_scaffold_deu_duoc_bao_ve(self, tmp_path):
        out = _scaffold_lan_dau(tmp_path)
        # Điền nội dung thật vào TẤT CẢ 20 file, không chỉ file đầu tiên.
        danh_dau = {}
        for num, fname, *_ in SRP.SCAFFOLD_FILES:
            p = out / f"{num}_{fname}.md"
            marker = f"NOI DUNG THAT #{num}"
            with p.open("a", encoding="utf-8") as f:
                f.write("\n" + marker + "\n")
            danh_dau[p] = marker

        SRP.scaffold(_STUDY, base_dir=str(tmp_path), with_docx=False)

        con_nguyen = [p for p, marker in danh_dau.items() if marker in p.read_text(encoding="utf-8")]
        assert len(con_nguyen) == len(danh_dau), (
            f"Chỉ {len(con_nguyen)}/{len(danh_dau)} file giữ được nội dung thật sau lần gọi "
            f"scaffold() thứ hai."
        )


class TestDoiChungScaffoldLanDauVanTaoDuFile:
    """Đối chứng — lần gọi ĐẦU TIÊN (thư mục chưa tồn tại) vẫn tạo đủ 20 file
    .md với nội dung placeholder gốc như hành vi cũ, không bị bản vá ảnh
    hưởng."""

    def test_lan_dau_tao_du_20_file_voi_noi_dung_goc(self, tmp_path):
        out = _scaffold_lan_dau(tmp_path)

        for num, fname, gate, _artifact_key, title, body in SRP.SCAFFOLD_FILES:
            p = out / f"{num}_{fname}.md"
            assert p.exists()
            noi_dung = p.read_text(encoding="utf-8")
            assert title.upper() in noi_dung
            assert body in noi_dung

    def test_goi_lai_tren_file_chua_dieu_gi_van_giu_placeholder_goc(self, tmp_path):
        """File CHƯA bị bác sĩ điền gì (vẫn placeholder gốc) — gọi lại
        scaffold() vẫn bỏ qua (không ghi lại, không lỗi), nội dung vẫn ĐÚNG
        placeholder cũ (không đổi vì header ngày tạo cũng được giữ nguyên)."""
        out = _scaffold_lan_dau(tmp_path)
        num, fname, *_ = SRP.SCAFFOLD_FILES[0]
        target = out / f"{num}_{fname}.md"
        truoc = target.read_text(encoding="utf-8")

        SRP.scaffold(_STUDY, base_dir=str(tmp_path), with_docx=False)

        sau = target.read_text(encoding="utf-8")
        assert sau == truoc
