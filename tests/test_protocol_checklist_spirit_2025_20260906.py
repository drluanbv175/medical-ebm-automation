"""Hồi quy cho checklist ĐỀ CƯƠNG theo từng mục sinh kèm đề cương G10 (06/09/2026).

Vì sao có: G1-AUTO-03b chỉ kiểm TÊN chuẩn protocol khớp thiết kế; không nơi nào liệt
kê từng item SPIRIT 2025 để bác sĩ tick. Danh mục 34 mục/53 dòng được sinh TỰ ĐỘNG từ
toàn văn bài Explanation & Elaboration chính thức (BMJ 2025, PMC12128891) — không gõ
tay; test này khoá số lượng, tính duy nhất, provenance và việc G10 in đủ cho RCT nhưng
KHÔNG bịa checklist cho thiết kế không có (quan sát) hoặc kho chưa có (PRISMA-P).

Ba luật khi thêm ca thử: kiểm hành vi bằng mã sống; mỗi ca gắn rủi ro thật (mất dòng
khi tái sinh module · in checklist sai thiết kế · giả vờ có PRISMA-P); ngoại tuyến.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import protocol_checklist_items as PCI  # noqa: E402
import run_g10_assemble as G10  # noqa: E402

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))
from test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402


def _retarget_design(d: Path, code: str) -> None:
    """Đổi mã thiết kế ở MỌI checkpoint có ghi (G1/G3/G5/G6) + study_meta để không
    tạo DESIGN_CONFLICT giả trong kiểm ngữ nghĩa."""
    for g in ("G1", "G3", "G5", "G6"):
        p = d / f"{g}_checkpoint.json"
        cp = json.loads(p.read_text(encoding="utf-8"))
        if g == "G1":
            cp["design"]["internal_code"] = code
            cp["design"]["primary"] = "Thử nghiệm ngẫu nhiên có đối chứng" if code == "rct" else cp["design"]["primary"]
            cp["design"]["reporting_standard"] = "CONSORT 2025" if code == "rct" else cp["design"]["reporting_standard"]
        else:
            cp["design_code"] = code
        p.write_text(json.dumps(cp, ensure_ascii=False), encoding="utf-8")
    mp = d / "study_meta.json"
    meta = json.loads(mp.read_text(encoding="utf-8"))
    meta["design_code"] = code
    mp.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


class TestItemModule:
    def test_spirit_2025_has_34_items_53_rows_unique_and_ordered(self):
        ids = [i for i, _, _ in PCI.SPIRIT_2025_ITEMS]
        assert len(ids) == 53 == len(set(ids))
        numbered = sorted({int(re.match(r"\d+", i).group(0)) for i in ids})
        assert numbered == list(range(1, 35))          # 34 mục chính thức
        assert ids[0] == "1a" and ids[-1] == "34"
        # Không dòng nào rỗng/đã bị dịch (giữ nguyên văn tiếng Anh).
        for _i, text, hint in PCI.SPIRIT_2025_ITEMS:
            assert len(text) > 15 and hint.strip()

    def test_provenance_is_traceable(self):
        prov = PCI.SPIRIT_2025_PROVENANCE
        assert "40294593" in prov["statement"] and "10.1001/jama.2025.4486" in prov["statement"]
        assert "PMC12128891" in prov["items_source"] and "40294956" in prov["items_source"]
        assert prov["n_items"] == 34 and prov["n_rows"] == 53

    def test_design_routing_is_honest(self):
        assert PCI.items_for_design("rct")[0] == "SPIRIT 2025"
        assert PCI.items_for_design("cross_sectional") is None
        assert PCI.items_for_design(None) is None
        name, reason = PCI.missing_item_list_reason("sr_ma")
        assert name == "PRISMA-P 2015" and "KHÔNG dùng danh mục tự nhớ" in reason

    def test_aliases_and_canon_codes_route_identically(self):
        """Lỗi thật 06/09/2026: bản đầu khoá lý do PRISMA-P theo bí danh 'sr_ma', trong khi
        G10 chuẩn hoá mã về 'systematic_review' TRƯỚC khi tra ⇒ nhánh đó không bao giờ
        chạy tới (test sr_ma ở dưới đỏ). Mọi tra cứu phải đi qua canonical_design_code."""
        import skill_standards as S
        for alias in ("sr_ma", "sr", "meta_analysis", "systematic_review", "SR_MA"):
            got = PCI.missing_item_list_reason(alias)
            assert got is not None and got[0] == "PRISMA-P 2015", alias
            assert PCI.items_for_design(alias) is None, alias
        for alias in ("rct", "rct_parallel", "rct_crossover", "randomized", "RCT"):
            found = PCI.items_for_design(alias)
            assert found is not None and found[0] == "SPIRIT 2025", alias
            assert PCI.missing_item_list_reason(alias) is None, alias
        for obs in ("cohort", "case_control_study", "cross_sectional_descriptive", "prevalence"):
            assert PCI.items_for_design(obs) is None and PCI.missing_item_list_reason(obs) is None, obs
        # Khoá của hai bảng tra phải là mã CANON — khoá theo bí danh là chính lỗi đã mắc.
        for key in list(PCI._PROTOCOL_CHECKLIST_BY_DESIGN) + list(PCI._NO_ITEM_LIST_REASON):
            assert S.canonical_design_code(key) == key, key


class TestG10Emission:
    def test_rct_gets_full_spirit_table_with_manual_status(self, tmp_path):
        _write_cross_sectional_fixture(tmp_path)
        _retarget_design(tmp_path, "rct")
        res = G10.assemble("FIXT", tmp_path)
        text = res["md"].read_text(encoding="utf-8")
        block = text.split("# Checklist chuẩn đề cương theo từng mục")[1].split("\n# ")[0]
        assert "SPIRIT 2025" in block and "PMC12128891" in block
        for item_id, _t, _h in PCI.SPIRIT_2025_ITEMS:
            assert re.search(rf"^\|\s*{re.escape(item_id)}\s*\|", block, re.MULTILINE), item_id
        # G10 KHÔNG tự tick: mọi dòng đều mang nhãn xác nhận thủ công.
        assert block.count(G10.TAG_MANUAL) == 53

    def test_cross_sectional_states_no_item_checklist_instead_of_inventing_one(self, tmp_path):
        _write_cross_sectional_fixture(tmp_path)
        res = G10.assemble("FIXT", tmp_path)
        text = res["md"].read_text(encoding="utf-8")
        block = text.split("# Checklist chuẩn đề cương theo từng mục")[1].split("\n# ")[0]
        assert "không có checklist ĐỀ CƯƠNG theo từng mục" in block
        assert "| 1a |" not in block and "SPIRIT_2025" not in block

    def test_validator_r18_warns_when_rct_table_removed_but_does_not_block(self, tmp_path):
        """Đột biến có chủ ý: xoá bảng SPIRIT khỏi đề cương RCT ⇒ R18 phải CẢNH BÁO
        (không chặn — đề cương lắp trước 06/09 chưa có bảng, nội dung không vì thế sai)."""
        import check_de_cuong
        _write_cross_sectional_fixture(tmp_path)
        _retarget_design(tmp_path, "rct")
        res = G10.assemble("FIXT", tmp_path)
        md = res["md"]
        rep_ok = check_de_cuong.validate(md, tmp_path)
        assert rep_ok["checks"]["R18_protocol_checklist"].startswith("PASS (SPIRIT 2025")
        text = md.read_text(encoding="utf-8")
        head, _sep, tail = text.partition("# Checklist chuẩn đề cương theo từng mục")
        tail = tail.split("\n# ", 1)[1] if "\n# " in tail else ""
        md.write_text(head + ("# " + tail if tail else ""), encoding="utf-8")
        rep = check_de_cuong.validate(md, tmp_path)
        assert rep["checks"]["R18_protocol_checklist"].startswith("WARN")
        assert any(w.startswith("R18") for w in rep["warnings"])
        assert not any(e.startswith("R18") for e in rep["errors"])

    def test_sr_ma_says_prisma_p_items_not_in_store(self, tmp_path):
        _write_cross_sectional_fixture(tmp_path)
        _retarget_design(tmp_path, "sr_ma")
        res = G10.assemble("FIXT", tmp_path)
        text = res["md"].read_text(encoding="utf-8")
        block = text.split("# Checklist chuẩn đề cương theo từng mục")[1].split("\n# ")[0]
        assert "PRISMA-P 2015" in block and "CHƯA có danh mục item" in block
        assert "| 1a |" not in block
