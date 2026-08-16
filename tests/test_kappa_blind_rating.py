"""
Deterministic regression tests cho kappa_blind_rating.py.
Không cần API key, không cần scipy/statsmodels. Mọi test PASS/FAIL xác định.

Dữ liệu là GIẢ LẬP (synthetic) — KHÔNG phải điểm MRAQ V4 thật. Mục đích chỉ là
xác nhận công thức Cohen's κ / Fleiss' κ được cài đặt đúng, bằng cách so với
giá trị tính TAY (thủ công, trình bày trong docstring từng test).

Chuyển vào medical-ebm-automation/ để track git 2026-07-15 (trước đó ở
MRAQ100_AUDIT/tests/, thư mục không thuộc repo git nào). Công cụ được kiểm ở
đây độc lập với dữ liệu MRAQ V4 thật (vẫn nằm ở ../MRAQ100_AUDIT/, ngoài repo).
"""

import csv
import json
import sys
from pathlib import Path

import pytest

# Cùng quy ước với tests/test_check_citation_retraction.py trong repo này: chèn
# thư mục tools/ (ở đây là tools/mraq_kappa, không phải tools/ gốc) vào
# sys.path rồi import trực tiếp — tools/ không phải package, không có __init__.py.
REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools" / "mraq_kappa"
sys.path.insert(0, str(TOOLS_DIR))

import kappa_blind_rating as K  # noqa: E402

# ─── Cohen's kappa (2 người chấm) ───────────────────────────────────────────

def test_cohen_kappa_hand_calculated_example():
    """
    Bảng 2x2 tự dựng, 50 case, 2 nhãn {Yes, No}:

                  Rater B: Yes   No   Total
    Rater A: Yes    20      5     25
    Rater A: No     10     15     25
    Total           30     20     50

    Tính tay:
      po = (20+15)/50 = 0.70
      pe = (25*30 + 25*20) / 50^2 = (750+500)/2500 = 0.50
      kappa = (0.70-0.50)/(1-0.50) = 0.20/0.50 = 0.40
    """
    labels_a = ["Yes"] * 20 + ["Yes"] * 5 + ["No"] * 10 + ["No"] * 15
    labels_b = ["Yes"] * 20 + ["No"] * 5 + ["Yes"] * 10 + ["No"] * 15
    assert len(labels_a) == len(labels_b) == 50

    k = K.cohen_kappa(labels_a, labels_b, categories=["Yes", "No"])
    assert k == pytest.approx(0.4, abs=1e-9)


def test_cohen_kappa_perfect_agreement_is_one():
    labels = ["1", "2", "3", "4"] * 5
    k = K.cohen_kappa(labels, list(labels), categories=K.DEFAULT_CATEGORIES)
    assert k == pytest.approx(1.0, abs=1e-9)


# ─── Fleiss' kappa (>2 người chấm) ──────────────────────────────────────────

def test_fleiss_kappa_hand_calculated_example():
    """
    3 người chấm, 4 case, 2 nhãn {A, B}:
      Case1: A,A,A   Case2: A,A,B   Case3: B,B,B   Case4: A,B,B

    Tính tay (công thức Fleiss 1971):
      n=3 rater/case, N=4 case, k=2 nhãn.
      Đếm theo (n_A, n_B): [3,0], [2,1], [0,3], [1,2]
      Tổng lượt = 12; p_A = 6/12 = 0.5; p_B = 6/12 = 0.5
      P_e = 0.5^2 + 0.5^2 = 0.5

      P_i = (Σ n_ij^2 - n) / (n(n-1)), n(n-1)=6:
        Case1: (9+0-3)/6 = 1.0
        Case2: (4+1-3)/6 = 2/6 = 1/3
        Case3: (0+9-3)/6 = 1.0
        Case4: (1+4-3)/6 = 2/6 = 1/3
      P̄ = (1 + 1/3 + 1 + 1/3) / 4 = (8/3) / 4 = 2/3

      kappa = (P̄ - P_e) / (1 - P_e) = (2/3 - 1/2) / (1/2) = (1/6)/(1/2) = 1/3
    """
    count_matrix = [
        [3, 0],  # Case1: A,A,A
        [2, 1],  # Case2: A,A,B
        [0, 3],  # Case3: B,B,B
        [1, 2],  # Case4: A,B,B
    ]
    k = K.fleiss_kappa_from_counts(count_matrix, n_raters=3)
    assert k == pytest.approx(1.0 / 3.0, abs=1e-9)


def test_fleiss_kappa_perfect_agreement_is_one():
    # 3 rater, 5 case, tất cả đồng thuận tuyệt đối trên 4 nhãn khác nhau
    count_matrix = [
        [3, 0, 0, 0],
        [0, 3, 0, 0],
        [0, 0, 3, 0],
        [0, 0, 0, 3],
        [3, 0, 0, 0],
    ]
    k = K.fleiss_kappa_from_counts(count_matrix, n_raters=3)
    assert k == pytest.approx(1.0, abs=1e-9)


def test_fleiss_kappa_via_ratings_dict_matches_from_counts():
    """compute_kappa() với 3 rater phải cho đúng kết quả như fleiss_kappa_from_counts()."""
    ratings = {
        "r1": {"C1": {"score": "A", "notes": ""}, "C2": {"score": "A", "notes": ""},
               "C3": {"score": "B", "notes": ""}, "C4": {"score": "A", "notes": ""}},
        "r2": {"C1": {"score": "A", "notes": ""}, "C2": {"score": "A", "notes": ""},
               "C3": {"score": "B", "notes": ""}, "C4": {"score": "B", "notes": ""}},
        "r3": {"C1": {"score": "A", "notes": ""}, "C2": {"score": "B", "notes": ""},
               "C3": {"score": "B", "notes": ""}, "C4": {"score": "B", "notes": ""}},
    }
    common_ids, incomplete = K.common_cases(ratings)
    assert incomplete == {}
    assert common_ids == ["C1", "C2", "C3", "C4"]

    k, method = K.compute_kappa(ratings, common_ids, categories=["A", "B"])
    assert method == "fleiss"
    assert k == pytest.approx(1.0 / 3.0, abs=1e-9)


# ─── common_cases() / thiếu điểm / bất đồng ─────────────────────────────────

def test_common_cases_excludes_missing_and_na():
    ratings = {
        "r1": {"A1": {"score": "2", "notes": ""}, "A2": {"score": "3", "notes": ""}},
        "r2": {"A1": {"score": "2", "notes": ""}, "A2": {"score": None, "notes": ""}},  # NA
        # r2 không có A3 => A3 cũng bị loại (không có trong ratings["r1"] nữa để test rõ hơn)
    }
    common_ids, incomplete = K.common_cases(ratings)
    assert common_ids == ["A1"]
    assert "A2" in incomplete and "r2" in incomplete["A2"]


def test_agreement_report_flags_disagreement_and_spread():
    ratings = {
        "r1": {"A1": {"score": "2", "notes": ""}, "A2": {"score": "4", "notes": ""}},
        "r2": {"A1": {"score": "2", "notes": ""}, "A2": {"score": "1", "notes": ""}},
    }
    common_ids, _ = K.common_cases(ratings)
    agree, disagree = K.agreement_report(ratings, common_ids)
    assert agree == ["A1"]
    assert len(disagree) == 1
    assert disagree[0]["case_id"] == "A2"
    assert disagree[0]["spread"] == 3


def test_domain_of_extracts_letter_prefix():
    assert K.domain_of("A1") == "A"
    assert K.domain_of("H12") == "H"
    assert K.domain_of("i5") == "I"


def test_validate_categories_rejects_out_of_range_score():
    ratings = {
        "r1": {"A1": {"score": "2", "notes": ""}},
        "r2": {"A1": {"score": "9", "notes": ""}},  # ngoài thang 1-4
    }
    common_ids, _ = K.common_cases(ratings)
    with pytest.raises(K.RatingError):
        K.validate_categories(ratings, common_ids, K.DEFAULT_CATEGORIES)


# ─── Đọc file CSV / JSON thật (I/O) ─────────────────────────────────────────

def test_load_rating_csv_and_json_roundtrip(tmp_path):
    csv_path = tmp_path / "rating_bs_an.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "score", "notes"])
        w.writerow(["A1", "2", "có script nhưng chưa log"])
        w.writerow(["A2", "NA", "không đủ bằng chứng để chấm"])

    json_path = tmp_path / "rating_bs_binh.json"
    json_path.write_text(
        json.dumps([{"case_id": "A1", "score": 3, "notes": "có log thật"}], ensure_ascii=False),
        encoding="utf-8",
    )

    r_csv = K.load_rating_csv(str(csv_path))
    assert r_csv["A1"]["score"] == "2"
    assert r_csv["A2"]["score"] is None  # "NA" -> None (thiếu, không phải điểm 0)

    r_json = K.load_rating_json(str(json_path))
    assert r_json["A1"]["score"] == "3"


def test_discover_rating_files_and_full_pipeline(tmp_path):
    """Test end-to-end: 2 file rating thật trong thư mục -> build_report() chạy được."""
    (tmp_path / "rating_bs_an.csv").write_text(
        "case_id,score,notes\nA1,2,\nA2,3,\nB1,2,\n", encoding="utf-8"
    )
    (tmp_path / "rating_bs_binh.csv").write_text(
        "case_id,score,notes\nA1,2,\nA2,2,\nB1,2,\n", encoding="utf-8"
    )

    report = K.build_report(str(tmp_path), categories=K.DEFAULT_CATEGORIES)
    assert set(report["raters"]) == {"bs_an", "bs_binh"}
    assert report["method"] == "cohen"
    assert report["n_cases_common"] == 3
    assert report["n_agree"] == 2  # A1, B1 khớp
    assert report["n_disagree"] == 1  # A2 lệch (3 vs 2)
    assert report["disagree_cases"][0]["case_id"] == "A2"
    # κ theo domain: domain A có 2 case chung -> tính được; domain B chỉ 1 case -> ghi chú
    assert report["by_domain"]["A"]["n_cases"] == 2
    assert report["by_domain"]["B"]["kappa"] is None
    assert "quá ít case" in report["by_domain"]["B"]["note"]


def test_discover_rating_files_rejects_duplicate_rater(tmp_path):
    (tmp_path / "rating_bs_an.csv").write_text("case_id,score\nA1,2\n", encoding="utf-8", newline="\n")
    (tmp_path / "rating_bs_an.json").write_text('{"A1": 2}', encoding="utf-8", newline="\n")
    with pytest.raises(K.RatingError):
        K.discover_rating_files(str(tmp_path))


def test_load_all_ratings_requires_at_least_two_files(tmp_path):
    (tmp_path / "rating_solo.csv").write_text("case_id,score\nA1,2\n", encoding="utf-8", newline="\n")
    with pytest.raises(K.RatingError):
        K.load_all_ratings(str(tmp_path))


# ─── CLI self-test (chạy được như 1 script) ─────────────────────────────────

def test_cli_selftest_runs_without_error(capsys):
    rc = K.main(["--selftest"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "0.4000" in out
    assert "PASS" in out
