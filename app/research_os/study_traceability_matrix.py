"""Ma trận truy nguyên nghiên cứu: objective → variable → instrument → analysis → output.

Ma trận đồng bộ theo chuẩn G0–G9:
  - objective:       Mục tiêu nghiên cứu (G1)
  - research_question: Câu hỏi PICO
  - variable_name:   Tên biến số (G4)
  - instrument_name: Công cụ đo lường (G4)
  - analysis_step:   Bước phân tích trong SAP (G7)
  - output_table:    Bảng kết quả tương ứng (G8)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class TraceabilityRow:
    """Một dòng trong ma trận truy nguyên. Các trường optional tương thích ngược."""
    research_question: str
    variable_name: str
    analysis_step: str
    output_table: str
    objective: str = ""            # G1 — mục tiêu tương ứng
    instrument_name: str = ""      # G4 — công cụ thu thập


def validate_traceability(rows: List[TraceabilityRow]) -> List[str]:
    """Kiểm tra ma trận truy nguyên. Trả danh sách vấn đề ([] = OK)."""
    issues: List[str] = []
    for index, row in enumerate(rows, start=1):
        if not row.research_question or not row.variable_name \
                or not row.analysis_step or not row.output_table:
            issues.append(f"Row {index} thiếu trường truy nguyên bắt buộc")
    # Kiểm tra trùng biến trong cùng một analysis_step
    seen: Dict[str, List[int]] = {}
    for idx, row in enumerate(rows, start=1):
        key = f"{row.variable_name}|{row.analysis_step}"
        seen.setdefault(key, []).append(idx)
    for key, indices in seen.items():
        if len(indices) > 1:
            var, step = key.split("|", 1)
            issues.append(
                f"Biến '{var}' xuất hiện nhiều lần trong analysis '{step}' "
                f"(rows {indices}) — kiểm tra trùng lặp"
            )
    return issues


def build_traceability_matrix(
    objectives: List[str],
    pico_question: str,
    variable_analysis_pairs: List[Dict[str, str]],
) -> List[TraceabilityRow]:
    """Helper xây ma trận từ danh sách mục tiêu và cặp (biến, công cụ, phân tích, bảng).

    Mỗi phần tử trong variable_analysis_pairs cần khoá:
      variable_name, analysis_step, output_table
    Tuỳ chọn: instrument_name, objective (ưu tiên lấy từ list objectives theo thứ tự)
    """
    rows: List[TraceabilityRow] = []
    for i, pair in enumerate(variable_analysis_pairs):
        obj = pair.get("objective", objectives[i] if i < len(objectives) else "")
        rows.append(
            TraceabilityRow(
                research_question=pico_question,
                variable_name=pair["variable_name"],
                analysis_step=pair["analysis_step"],
                output_table=pair["output_table"],
                objective=obj,
                instrument_name=pair.get("instrument_name", ""),
            )
        )
    return rows
