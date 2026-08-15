"""
project_crf_builder — Xây dựng CRF draft theo loại nghiên cứu (V4.3.3).

Mọi giá trị số/ngưỡng đều là REQUIRE_HUMAN_INPUT. OFFLINE · KHÔNG PII / API.
"""

from __future__ import annotations

import dataclasses
from typing import List

from .project_config import DISCLAIMER, REQUIRE_HUMAN_INPUT_MARKER, StudyType


@dataclasses.dataclass
class CRFField:
    field_id: str
    field_name: str
    field_type: str      # text | number | date | select | checkbox | yesno
    options: List[str]   # cho select/checkbox
    unit: str
    validation_rule: str
    required: bool
    notes: str

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class CRFSection:
    section_id: str
    section_name: str
    fields: List[CRFField]

    def as_dict(self) -> dict:
        return {"section_id": self.section_id,
                "section_name": self.section_name,
                "fields": [f.as_dict() for f in self.fields]}


@dataclasses.dataclass
class CRFDraft:
    study_type: str
    version: str
    sections: List[CRFSection]
    notes: str

    def to_markdown(self) -> str:
        RHI = REQUIRE_HUMAN_INPUT_MARKER
        lines = [
            f"# CRF DRAFT — {self.study_type}",
            f"> Phiên bản: {self.version} · {RHI} · {DISCLAIMER}",
            "",
        ]
        for sec in self.sections:
            lines.append(f"## {sec.section_id}. {sec.section_name}")
            lines.append("")
            lines.append("| Field ID | Tên trường | Kiểu | Đơn vị | Bắt buộc | Ghi chú |")
            lines.append("|----------|-----------|------|--------|----------|---------|")
            for f in sec.fields:
                req = "✓" if f.required else ""
                opts = ", ".join(f.options) if f.options else ""
                display = f"{f.field_type}" + (f" [{opts}]" if opts else "")
                lines.append(
                    f"| {f.field_id} | {f.field_name} | {display} | {f.unit} | {req} | {f.notes} |"
                )
            lines.append("")
        lines += [self.notes, "", "---", f"**Disclaimer:** {DISCLAIMER}"]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CRF templates theo loại nghiên cứu
# ---------------------------------------------------------------------------

def _demographic_section() -> CRFSection:
    RHI = REQUIRE_HUMAN_INPUT_MARKER
    return CRFSection("CRF-DEM", "Nhân khẩu học (Bắt buộc với mọi thiết kế)", [
        CRFField("DEM-01", "Mã tham gia (pseudonym)", "text", [], "", "Bắt buộc, KHÔNG nhập mã bệnh viện thật", True, "PII-SAFE: chỉ mã giả danh"),
        CRFField("DEM-02", "Tuổi (năm)", "number", [], "năm", f"Số nguyên ≥ 18 · {RHI}: ngưỡng tuổi tối thiểu do PI ấn định", True, ""),
        CRFField("DEM-03", "Giới tính", "select", ["Nam", "Nữ", "Khác/Không xác định"], "", "", True, ""),
        CRFField("DEM-04", "Trình độ học vấn", "select", ["Tiểu học", "THCS", "THPT", "Đại học+", "Không biết"], "", "", False, ""),
    ])


def _cross_sectional_crf() -> List[CRFSection]:
    RHI = REQUIRE_HUMAN_INPUT_MARKER
    return [
        _demographic_section(),
        CRFSection("CRF-EXP", "Phơi nhiễm / Biến giải thích", [
            CRFField("EXP-01", f"Biến phơi nhiễm chính {RHI}", "text", [], "", f"Tên/giá trị do PI xác định {RHI}", True, ""),
            CRFField("EXP-02", "Thời điểm thu thập", "date", [], "", "ISO 8601", True, ""),
            CRFField("EXP-03", "Phương pháp đo phơi nhiễm", "text", [], "", f"{RHI}: công cụ đo, nguồn thông tin", True, ""),
        ]),
        CRFSection("CRF-OUT", "Kết cục chính", [
            CRFField("OUT-01", f"Kết cục chính {RHI}", "text", [], f"{RHI}", f"Định nghĩa từ SAP {RHI}", True, ""),
            CRFField("OUT-02", f"Kết cục phụ 1 {RHI}", "text", [], f"{RHI}", f"{RHI}", False, ""),
        ]),
        CRFSection("CRF-CONF", "Biến nhiễu", [
            CRFField("CONF-01", f"Bệnh nền {RHI}", "checkbox", [f"{RHI}: liệt kê theo protocol"], "", "", False, ""),
            CRFField("CONF-02", f"Thuốc đang dùng {RHI}", "text", [], "", f"{RHI}", False, ""),
        ]),
    ]


def _cohort_crf() -> List[CRFSection]:
    RHI = REQUIRE_HUMAN_INPUT_MARKER
    base = _cross_sectional_crf()
    base.append(CRFSection("CRF-FU", "Theo dõi (Follow-up)", [
        CRFField("FU-01", "Ngày tái khám / cột mốc", "date", [], "", "ISO 8601", True, ""),
        CRFField("FU-02", "Trạng thái tại cột mốc", "select", ["Còn sống / không biến cố", "Biến cố chính", "Mất theo dõi", "Tử vong", "Rút khỏi nghiên cứu"], "", "", True, ""),
        CRFField("FU-03", f"Lý do mất theo dõi {RHI}", "text", [], "", f"{RHI}", False, "Chỉ điền nếu mất theo dõi"),
        CRFField("FU-04", f"Ngày xảy ra biến cố {RHI}", "date", [], "", "ISO 8601", False, ""),
    ]))
    return base


def _case_control_crf() -> List[CRFSection]:
    RHI = REQUIRE_HUMAN_INPUT_MARKER
    return [
        _demographic_section(),
        CRFSection("CRF-CASE", "Xác định ca bệnh / chứng", [
            CRFField("CASE-01", "Phân loại", "select", ["Ca bệnh", "Chứng"], "", "", True, ""),
            CRFField("CASE-02", f"Tiêu chí ca bệnh thỏa mãn {RHI}", "checkbox", [f"{RHI}"], "", "", True, ""),
            CRFField("CASE-03", "Ngày chẩn đoán ca bệnh", "date", [], "", "ISO 8601", False, "Chỉ cho ca bệnh"),
        ]),
        CRFSection("CRF-EXP", f"Phơi nhiễm hồi cứu {RHI}", [
            CRFField("EXP-01", f"Phơi nhiễm chính {RHI}", "yesno", [], "", f"{RHI}", True, ""),
            CRFField("EXP-02", "Thời gian phơi nhiễm", "text", [], f"{RHI}", f"{RHI}: cách tính, nguồn thông tin", False, ""),
        ]),
        CRFSection("CRF-CONF", "Biến nhiễu", [
            CRFField("CONF-01", f"Biến nhiễu 1 {RHI}", "text", [], "", f"{RHI}", False, ""),
        ]),
    ]


def _rct_crf() -> List[CRFSection]:
    RHI = REQUIRE_HUMAN_INPUT_MARKER
    return [
        _demographic_section(),
        CRFSection("CRF-RAND", "Phân bổ ngẫu nhiên", [
            CRFField("RAND-01", "Mã phân bổ ngẫu nhiên", "text", [], "", "Mã do hệ thống IWRS cấp", True, ""),
            CRFField("RAND-02", "Nhóm phân bổ", "select", ["Can thiệp", "Đối chứng"], "", "KHÔNG điền trước khi mở kết quả phân bổ", True, ""),
            CRFField("RAND-03", "Ngày phân bổ", "date", [], "", "ISO 8601", True, ""),
        ]),
        CRFSection("CRF-INTV", f"Can thiệp / Tuân thủ {RHI}", [
            CRFField("INTV-01", f"Liều / loại can thiệp {RHI}", "text", [], f"{RHI}", f"Mô tả theo protocol {RHI}", True, ""),
            CRFField("INTV-02", "Ngày bắt đầu can thiệp", "date", [], "", "ISO 8601", True, ""),
            CRFField("INTV-03", "Ngày kết thúc can thiệp", "date", [], "", "ISO 8601", False, ""),
            CRFField("INTV-04", "Tuân thủ (%)", "number", [], "%", f"0–100; {RHI}: cách đo", False, ""),
        ]),
        CRFSection("CRF-OUT", f"Kết cục {RHI}", [
            CRFField("OUT-01", f"Kết cục chính {RHI}", "text", [], f"{RHI}", f"Đo tại {RHI} tuần/tháng", True, ""),
            CRFField("OUT-02", f"Kết cục phụ {RHI}", "text", [], f"{RHI}", f"{RHI}", False, ""),
        ]),
        CRFSection("CRF-AE", "Biến cố bất lợi (AE)", [
            CRFField("AE-01", "Có AE không?", "yesno", [], "", "", False, ""),
            CRFField("AE-02", "Mô tả AE", "text", [], "", f"MedDRA preferred term {RHI}", False, ""),
            CRFField("AE-03", "Mức độ AE (CTCAE)", "select", ["1", "2", "3", "4", "5", "Không áp dụng"], "", f"CTCAE v5 {RHI}", False, ""),
            CRFField("AE-04", "AE nghiêm trọng (SAE)?", "yesno", [], "", "SAE = CTCAE ≥ 3 hoặc gây nhập viện", False, ""),
        ]),
    ]


def _diagnostic_crf() -> List[CRFSection]:
    RHI = REQUIRE_HUMAN_INPUT_MARKER
    return [
        _demographic_section(),
        CRFSection("CRF-TEST", f"Test chỉ số {RHI}", [
            CRFField("TEST-01", f"Tên test chỉ số {RHI}", "text", [], "", f"{RHI}: ghi tên đầy đủ, phiên bản", True, ""),
            CRFField("TEST-02", "Kết quả test (số)", "number", [], f"{RHI}", f"Đơn vị: {RHI}", False, ""),
            CRFField("TEST-03", "Kết quả test (phân loại)", "select", ["Dương tính", "Âm tính", "Không xác định"], "", f"Ngưỡng: {RHI}", True, ""),
            CRFField("TEST-04", "Ngày thực hiện test", "date", [], "", "ISO 8601", True, ""),
        ]),
        CRFSection("CRF-REF", f"Chuẩn vàng {RHI}", [
            CRFField("REF-01", f"Chuẩn vàng {RHI}", "text", [], "", f"{RHI}: tên, phương pháp", True, ""),
            CRFField("REF-02", "Kết quả chuẩn vàng", "select", ["Bệnh", "Không bệnh", "Không xác định"], "", f"{RHI}", True, ""),
            CRFField("REF-03", "Người đọc chuẩn vàng (pseudonym)", "text", [], "", "KHÔNG tên thật", True, ""),
        ]),
    ]


def _sr_ma_crf() -> List[CRFSection]:
    RHI = REQUIRE_HUMAN_INPUT_MARKER
    return [
        CRFSection("CRF-SEARCH", "Tìm kiếm tài liệu", [
            CRFField("SCH-01", "CSDL tìm kiếm", "checkbox", ["PubMed", "Embase", "Cochrane", "Scopus", "Khác"], "", f"{RHI}: ngày tìm kiếm", True, ""),
            CRFField("SCH-02", "Ngày tìm kiếm cuối", "date", [], "", "ISO 8601", True, ""),
            CRFField("SCH-03", "Số kết quả thô", "number", [], "bài", "", True, ""),
        ]),
        CRFSection("CRF-SCREEN", "Sàng lọc", [
            CRFField("SCR-01", "Mã nghiên cứu (tự tạo)", "text", [], "", "KHÔNG dùng PMID làm ID sơ cấp", True, ""),
            CRFField("SCR-02", "Quyết định sàng lọc tiêu đề/tóm tắt", "select", ["Đưa vào", "Loại", "Cần đọc toàn văn"], "", "", True, ""),
            CRFField("SCR-03", "Quyết định đọc toàn văn", "select", ["Đưa vào", "Loại", "Chờ xác nhận"], "", "", False, ""),
            CRFField("SCR-04", f"Lý do loại {RHI}", "text", [], "", f"{RHI}", False, ""),
        ]),
        CRFSection("CRF-EXTRACT", "Trích xuất dữ liệu", [
            CRFField("EXT-01", f"Dân số (P) {RHI}", "text", [], "", f"{RHI}", True, ""),
            CRFField("EXT-02", f"Can thiệp/phơi nhiễm (I/E) {RHI}", "text", [], "", f"{RHI}", True, ""),
            CRFField("EXT-03", f"So sánh (C) {RHI}", "text", [], "", f"{RHI}", True, ""),
            CRFField("EXT-04", f"Kết cục (O) với ước lượng + CI {RHI}", "text", [], "", f"{RHI}: ghi RR/OR/MD + 95% CI", True, ""),
            CRFField("EXT-05", f"PMID / DOI {RHI}", "text", [], "", f"Cần xác minh trước khi nhập {RHI}", True, "Không tự suy luận"),
        ]),
    ]


def _qualitative_crf() -> List[CRFSection]:
    RHI = REQUIRE_HUMAN_INPUT_MARKER
    return [
        _demographic_section(),
        CRFSection("CRF-PART", "Đặc điểm người tham gia", [
            CRFField("PART-01", "Mã người tham gia (pseudonym)", "text", [], "", "KHÔNG tên thật", True, "PII-SAFE"),
            CRFField("PART-02", f"Tiêu chí mục đích lấy mẫu {RHI}", "text", [], "", f"{RHI}", True, ""),
            CRFField("PART-03", "Số lượt phỏng vấn", "number", [], "lượt", "", True, ""),
        ]),
        CRFSection("CRF-DATA", "Thu thập dữ liệu định tính", [
            CRFField("DATA-01", "Phương pháp", "select", ["Phỏng vấn sâu", "Nhóm tiêu điểm", "Quan sát", "Khác"], "", "", True, ""),
            CRFField("DATA-02", "Thời lượng (phút)", "number", [], "phút", "", False, ""),
            CRFField("DATA-03", "Đạt bão hòa?", "yesno", [], "", f"Tiêu chí bão hòa: {RHI}", False, ""),
        ]),
    ]


_CRF_MAP = {
    StudyType.CROSS_SECTIONAL: _cross_sectional_crf,
    StudyType.COHORT: _cohort_crf,
    StudyType.CASE_CONTROL: _case_control_crf,
    StudyType.RCT: _rct_crf,
    StudyType.DIAGNOSTIC: _diagnostic_crf,
    StudyType.SR_MA: _sr_ma_crf,
    StudyType.QUALITATIVE: _qualitative_crf,
}


def build_crf_draft(study_type: StudyType, version: str = "0.1.0") -> CRFDraft:
    """Xây dựng CRF draft cho loại nghiên cứu. Mọi nội dung là DRAFT."""
    fn = _CRF_MAP.get(study_type)
    if fn is None:
        raise ValueError(f"StudyType không hỗ trợ: {study_type}")
    sections = fn()
    return CRFDraft(
        study_type=study_type.value,
        version=version,
        sections=sections,
        notes=(
            f"**Lưu ý:** Mọi trường {REQUIRE_HUMAN_INPUT_MARKER} cần PI điền trước khi xây "
            f"data dictionary. KHÔNG nhập PII. Mọi thay đổi CRF → trigger Change Control."
        ),
    )
