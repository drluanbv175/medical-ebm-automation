#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kappa_blind_rating.py — Công cụ tính Cohen's κ / Fleiss' κ cho vòng chấm mù MRAQ V4
=====================================================================================
Mục đích: hỗ trợ ≥2 người chấm ĐỘC LẬP (blind) đánh giá lại bộ 53 tiêu chí (case)
của MRAQ-100 V4 (Domain A–I, xem `03_MRAQ100_SCORECARD.md`), rồi tính hệ số đồng
thuận liên-người-chấm (inter-rater agreement) giữa các bản chấm đó.

CÔNG CỤ NÀY KHÔNG TỰ CHẤM BẤT KỲ CASE NÀO. Nó chỉ đọc các file rating_*.json /
rating_*.csv do người chấm thật điền, rồi tính κ. Không có "điểm mặc định", không
suy diễn điểm còn thiếu, không dùng LLM.

VỊ TRÍ & PHẠM VI (chuyển vào medical-ebm-automation/ để track git, 2026-07-15):
công cụ này ĐO chất lượng đánh giá của hệ MRAQ V4 — bản thân dữ liệu chấm điểm
thật (rating_*.csv/.json) và scorecard `03_MRAQ100_SCORECARD.md` vẫn nằm ở
`../MRAQ100_AUDIT/` (thư mục KHÔNG thuộc repo này, không track git — xem
CLAUDE.md gốc mục "Bản đồ dự án"). Công cụ ĐỘC LẬP với dữ liệu: không hard-code
đường dẫn tới đó; người dùng tự trỏ `--ratings-dir` tới đúng nơi lưu file chấm
điểm thật (ví dụ `../MRAQ100_AUDIT/kappa_round_2026xxxx`) — chỉ cần gọi đúng
tham số dòng lệnh là chạy được, dù dữ liệu nằm trong hay ngoài repo nào.

Quy trình BLIND (bắt buộc) và định dạng file rating: xem `BLIND_RATING_GUIDE.md`
cùng thư mục. Template case rỗng (chưa có điểm): `rating_template.csv`.

Cách dùng (chạy từ thư mục gốc medical-ebm-automation/):
    python3 tools/mraq_kappa/kappa_blind_rating.py --ratings-dir <thư_mục_chứa_rating_*.csv_hoặc_.json>
    python3 tools/mraq_kappa/kappa_blind_rating.py --ratings-dir <dir> --out report.json
    python3 tools/mraq_kappa/kappa_blind_rating.py --selftest        # dữ liệu GIẢ để kiểm công thức κ

Công thức:
    - 2 người chấm  → Cohen's κ (không trọng số):
          κ = (p_o − p_e) / (1 − p_e)
      p_o = tỉ lệ đồng ý quan sát được; p_e = tỉ lệ đồng ý kỳ vọng do ngẫu nhiên
      (từ phân phối biên của mỗi người chấm).
    - >2 người chấm → Fleiss' κ (Fleiss 1971), công thức chuẩn:
          P̄ = trung bình P_i (đồng thuận từng case); P_e = Σ p_j²
          κ = (P̄ − P_e) / (1 − P_e)

Không phụ thuộc thư viện ngoài chuẩn Python (không cần scipy/statsmodels dù đã có
sẵn trong requirements.txt của dự án — công thức κ đơn giản, tự cài đặt tay để
công cụ chạy được ở BẤT KỲ máy nào, kể cả khi venv EBM chưa kích hoạt).

Cần bác sĩ / người chấm kiểm chứng lại danh sách case bất đồng trước khi cập nhật
điểm chính thức vào `../MRAQ100_AUDIT/03_MRAQ100_SCORECARD.md`.
"""

import argparse
import csv
import json
import os
import re
import sys
from collections import OrderedDict

# ─── Hằng số ─────────────────────────────────────────────────────────────────

# Thang điểm chuẩn MRAQ V4 (xem "QUY TẮC CHẤM ĐIỂM MỚI" trong 03_MRAQ100_SCORECARD.md):
#   1 = dưới ngưỡng DOCUMENTED / thiếu hẳn
#   2 = DOCUMENTED (+ IMPLEMENTED nếu có — chưa chạy thì vẫn 2)
#   3 = + EXECUTED (có log/timestamp/exit code thật)
#   4 = + INDEPENDENTLY REVIEWED (người/hệ thống độc lập đã ký)
DEFAULT_CATEGORIES = ["1", "2", "3", "4"]

# Giá trị coi là "không chấm / không áp dụng" — bị loại khỏi tính κ cho case đó
# (không được coi là bất đồng, chỉ là thiếu dữ liệu).
_MISSING_TOKENS = {"", "na", "n/a", "-", "--", "none", "null", "pending"}

RATING_FILE_RE = re.compile(r"^rating_(?P<name>.+)\.(?P<ext>json|csv)$", re.IGNORECASE)


class RatingError(ValueError):
    """Lỗi dữ liệu rating (định dạng sai, điểm ngoài thang, case thiếu…)."""


# ─── Đọc file rating ─────────────────────────────────────────────────────────

def _normalize_score(raw):
    """Chuẩn hoá 1 giá trị điểm thô -> str đã strip, hoặc None nếu là 'thiếu'."""
    if raw is None:
        return None
    s = str(raw).strip()
    if s.lower() in _MISSING_TOKENS:
        return None
    return s


def load_rating_csv(path):
    """
    Đọc 1 file rating_<ten>.csv. Cột bắt buộc: case_id, score. Cột tuỳ chọn: notes.
    Trả về OrderedDict[case_id] -> {"score": str, "notes": str}.
    """
    out = OrderedDict()
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise RatingError(f"File rỗng hoặc không có header: {path}")
        fields_lower = {c.lower().strip(): c for c in reader.fieldnames}
        if "case_id" not in fields_lower or "score" not in fields_lower:
            raise RatingError(
                f"{path}: thiếu cột bắt buộc 'case_id' và/hoặc 'score' "
                f"(header hiện có: {reader.fieldnames})"
            )
        case_col = fields_lower["case_id"]
        score_col = fields_lower["score"]
        notes_col = fields_lower.get("notes")
        for i, row in enumerate(reader):
            case_id = (row.get(case_col) or "").strip()
            if not case_id:
                continue  # dòng trống / dòng phân tách domain — bỏ qua
            score = _normalize_score(row.get(score_col))
            notes = (row.get(notes_col) or "").strip() if notes_col else ""
            if case_id in out:
                raise RatingError(f"{path}: case_id '{case_id}' bị lặp (dòng {i + 2})")
            out[case_id] = {"score": score, "notes": notes}
    return out


def load_rating_json(path):
    """
    Đọc 1 file rating_<ten>.json. Chấp nhận 2 dạng:
      (a) list các object: [{"case_id": "A1", "score": 2, "notes": "..."}, ...]
      (b) dict phẳng:      {"A1": 2, "A2": "3", ...}  hoặc  {"A1": {"score":2,"notes":"..."}}
    Trả về OrderedDict[case_id] -> {"score": str, "notes": str}.
    """
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)

    out = OrderedDict()
    if isinstance(data, list):
        for i, item in enumerate(data):
            if not isinstance(item, dict) or "case_id" not in item:
                raise RatingError(f"{path}: phần tử thứ {i} thiếu 'case_id' hoặc không phải object")
            case_id = str(item["case_id"]).strip()
            score = _normalize_score(item.get("score"))
            notes = str(item.get("notes") or "").strip()
            if case_id in out:
                raise RatingError(f"{path}: case_id '{case_id}' bị lặp")
            out[case_id] = {"score": score, "notes": notes}
    elif isinstance(data, dict):
        for case_id, val in data.items():
            case_id = str(case_id).strip()
            if isinstance(val, dict):
                score = _normalize_score(val.get("score"))
                notes = str(val.get("notes") or "").strip()
            else:
                score = _normalize_score(val)
                notes = ""
            out[case_id] = {"score": score, "notes": notes}
    else:
        raise RatingError(f"{path}: JSON phải là list hoặc dict ở top-level")
    return out


def load_rating_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return load_rating_csv(path)
    if ext == ".json":
        return load_rating_json(path)
    raise RatingError(f"Định dạng không hỗ trợ: {path} (chỉ .csv / .json)")


def discover_rating_files(ratings_dir):
    """Tìm mọi file rating_<ten>.{csv,json} trong thư mục. Trả về dict rater_name -> path."""
    found = {}
    for fname in sorted(os.listdir(ratings_dir)):
        m = RATING_FILE_RE.match(fname)
        if not m:
            continue
        rater = m.group("name")
        if rater in found:
            raise RatingError(
                f"Người chấm '{rater}' có >1 file rating trong {ratings_dir} "
                f"({os.path.basename(found[rater])} và {fname}) — chỉ được 1 file/người."
            )
        found[rater] = os.path.join(ratings_dir, fname)
    return found


def load_all_ratings(ratings_dir):
    """Trả về OrderedDict[rater_name] -> OrderedDict[case_id] -> {"score","notes"}."""
    files = discover_rating_files(ratings_dir)
    if len(files) < 2:
        raise RatingError(
            f"Cần ≥2 file rating_<ten>.csv/.json trong '{ratings_dir}' để tính κ "
            f"(tìm thấy {len(files)}: {list(files.keys())})."
        )
    ratings = OrderedDict()
    for rater in sorted(files):
        ratings[rater] = load_rating_file(files[rater])
    return ratings


# ─── Gộp case chung + kiểm định thang điểm ──────────────────────────────────

def domain_of(case_id):
    """Domain = tiền tố chữ cái đầu case_id (VD 'A1' -> 'A', 'H12' -> 'H')."""
    m = re.match(r"^[A-Za-z]+", case_id)
    return m.group(0).upper() if m else "?"


def common_cases(ratings):
    """
    Trả về (common_ids đã sort, incomplete) trong đó incomplete là dict
    case_id -> list rater còn thiếu điểm (bị NA hoặc không xuất hiện trong file
    của rater đó) — các case này bị LOẠI khỏi tính κ, không tính là bất đồng.
    """
    all_case_ids = set()
    for r in ratings.values():
        all_case_ids.update(r.keys())

    common, incomplete = [], {}
    for cid in sorted(all_case_ids):
        missing = [
            rater for rater, r in ratings.items()
            if cid not in r or r[cid]["score"] is None
        ]
        if missing:
            incomplete[cid] = missing
        else:
            common.append(cid)
    return common, incomplete


def validate_categories(ratings, common_ids, allowed_categories):
    """FAIL nếu có điểm ngoài thang cho phép. allowed_categories=None -> không giới hạn."""
    if allowed_categories is None:
        return
    allowed = set(allowed_categories)
    bad = []
    for rater, r in ratings.items():
        for cid in common_ids:
            score = r[cid]["score"]
            if score not in allowed:
                bad.append((rater, cid, score))
    if bad:
        detail = "; ".join(f"{rater}/{cid}='{score}'" for rater, cid, score in bad[:20])
        raise RatingError(
            f"Có {len(bad)} điểm ngoài thang hợp lệ {sorted(allowed)}: {detail}"
            + (" ..." if len(bad) > 20 else "")
        )


# ─── Cohen's kappa (2 người chấm, không trọng số) ───────────────────────────

def cohen_kappa(labels_a, labels_b, categories):
    """
    κ Cohen không trọng số. labels_a/labels_b: list điểm cùng thứ tự case.
    categories: danh sách nhãn có thể xuất hiện (dùng để cố định kích thước bảng).
    """
    n = len(labels_a)
    if n == 0:
        return None
    if n != len(labels_b):
        raise RatingError("cohen_kappa: 2 danh sách nhãn phải cùng độ dài")

    idx = {c: i for i, c in enumerate(categories)}
    k = len(categories)
    table = [[0] * k for _ in range(k)]
    for a, b in zip(labels_a, labels_b):
        table[idx[a]][idx[b]] += 1

    po = sum(table[i][i] for i in range(k)) / n
    row_marg = [sum(table[i]) / n for i in range(k)]
    col_marg = [sum(table[i][j] for i in range(k)) / n for j in range(k)]
    pe = sum(row_marg[j] * col_marg[j] for j in range(k))

    if pe == 1:
        return 1.0 if po == 1 else 0.0
    return (po - pe) / (1 - pe)


# ─── Fleiss' kappa (>2 người chấm) ──────────────────────────────────────────

def fleiss_kappa_from_counts(count_matrix, n_raters):
    """
    count_matrix: list các hàng, mỗi hàng = list đếm số rater chọn từng category
    cho 1 case (mỗi hàng phải sum = n_raters). Công thức Fleiss (1971) chuẩn.
    """
    N = len(count_matrix)
    if N == 0:
        return None
    n = n_raters
    for row in count_matrix:
        if sum(row) != n:
            raise RatingError(
                f"fleiss_kappa: mỗi case phải có đúng {n} lượt chấm, gặp hàng sum={sum(row)}"
            )

    k = len(count_matrix[0])
    P_i = [
        (sum(x * x for x in row) - n) / (n * (n - 1))
        for row in count_matrix
    ]
    P_bar = sum(P_i) / N

    p_j = [sum(row[j] for row in count_matrix) / (N * n) for j in range(k)]
    P_e = sum(p * p for p in p_j)

    if P_e == 1:
        return 1.0 if P_bar == 1 else 0.0
    return (P_bar - P_e) / (1 - P_e)


def fleiss_kappa(ratings, common_ids, categories):
    """Xây count_matrix từ ratings (dict rater->case->{"score"}) rồi gọi fleiss_kappa_from_counts."""
    raters = list(ratings.keys())
    n_raters = len(raters)
    idx = {c: i for i, c in enumerate(categories)}
    matrix = []
    for cid in common_ids:
        row = [0] * len(categories)
        for rater in raters:
            score = ratings[rater][cid]["score"]
            row[idx[score]] += 1
        matrix.append(row)
    return fleiss_kappa_from_counts(matrix, n_raters)


# ─── Điểm chung: tự chọn Cohen/Fleiss theo số người chấm ────────────────────

def compute_kappa(ratings, common_ids, categories):
    """Trả về (kappa, method_name). None nếu không đủ dữ liệu (0 case chung)."""
    raters = list(ratings.keys())
    if len(common_ids) == 0:
        return None, ("cohen" if len(raters) == 2 else "fleiss")
    if len(raters) == 2:
        a = [ratings[raters[0]][cid]["score"] for cid in common_ids]
        b = [ratings[raters[1]][cid]["score"] for cid in common_ids]
        return cohen_kappa(a, b, categories), "cohen"
    return fleiss_kappa(ratings, common_ids, categories), "fleiss"


def interpret_kappa(k):
    """Băng diễn giải κ — dùng chung ngưỡng với tools/eval/human_eval_score.py::band_p32
    (repo gốc "Claude AI/tools/eval/", KHÁC thư mục tools/ trong medical-ebm-automation
    này — hai repo git độc lập)."""
    if k is None:
        return "thiếu dữ liệu"
    if k >= 0.80:
        return "excellent (κ≥0.80, gần như hoàn toàn đồng thuận)"
    if k >= 0.60:
        return "pass (κ≥0.60, đồng thuận đáng kể)"
    if k >= 0.40:
        return "moderate (0.40≤κ<0.60)"
    if k >= 0.0:
        return "yếu (0≤κ<0.40) — nên bàn lại tiêu chí"
    return "kém hơn ngẫu nhiên (κ<0) — cần rà lại toàn bộ rubric"


# ─── Đồng thuận / bất đồng theo từng case ───────────────────────────────────

def agreement_report(ratings, common_ids):
    """
    Trả về (agree_ids, disagree) trong đó disagree là list dict:
      {"case_id", "scores": {rater: score}, "spread": int|None}
    sắp theo spread giảm dần (case lệch nhiều nhất lên đầu để bàn lại trước).
    """
    raters = list(ratings.keys())
    agree, disagree = [], []
    for cid in common_ids:
        scores = {rater: ratings[rater][cid]["score"] for rater in raters}
        values = list(scores.values())
        if len(set(values)) == 1:
            agree.append(cid)
        else:
            spread = None
            try:
                nums = [int(v) for v in values]
                spread = max(nums) - min(nums)
            except (TypeError, ValueError):
                pass
            disagree.append({"case_id": cid, "scores": scores, "spread": spread})

    disagree.sort(key=lambda d: (-(d["spread"] if d["spread"] is not None else 0), d["case_id"]))
    return agree, disagree


# ─── Báo cáo tổng hợp ────────────────────────────────────────────────────────

def build_report(ratings_dir, categories=DEFAULT_CATEGORIES, out_path=None):
    ratings = load_all_ratings(ratings_dir)
    raters = list(ratings.keys())
    common_ids, incomplete = common_cases(ratings)
    validate_categories(ratings, common_ids, categories)

    overall_kappa, method = compute_kappa(ratings, common_ids, categories)
    agree_ids, disagree = agreement_report(ratings, common_ids)

    # κ theo domain (nhóm case_id theo tiền tố chữ cái, VD A/B/C.../I)
    by_domain = OrderedDict()
    for cid in common_ids:
        by_domain.setdefault(domain_of(cid), []).append(cid)

    domain_report = OrderedDict()
    for dom, ids in sorted(by_domain.items()):
        if len(ids) < 2:
            domain_report[dom] = {"n_cases": len(ids), "kappa": None,
                                   "note": "quá ít case chung để tính κ nhóm (<2)"}
            continue
        k, _ = compute_kappa(ratings, ids, categories)
        domain_report[dom] = {"n_cases": len(ids), "kappa": k, "note": interpret_kappa(k)}

    report = {
        "raters": raters,
        "method": method,
        "n_cases_common": len(common_ids),
        "n_cases_incomplete": len(incomplete),
        "incomplete_cases": incomplete,
        "overall_kappa": overall_kappa,
        "overall_interpretation": interpret_kappa(overall_kappa),
        "n_agree": len(agree_ids),
        "n_disagree": len(disagree),
        "agree_case_ids": agree_ids,
        "disagree_cases": disagree,
        "by_domain": domain_report,
        "disclaimer": "Cần bác sĩ / người chấm kiểm chứng lại danh sách case bất đồng "
                       "trước khi cập nhật điểm chính thức. Công cụ không tự chấm case nào.",
    }

    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    return report


def format_report_text(report):
    lines = []
    lines.append("=" * 72)
    lines.append("BÁO CÁO κ CHẤM MÙ — MRAQ V4 (blind inter-rater agreement)")
    lines.append("=" * 72)
    lines.append(f"Người chấm ({len(report['raters'])}): {', '.join(report['raters'])}")
    lines.append(f"Phương pháp: {'Cohen' if report['method'] == 'cohen' else 'Fleiss'} κ "
                 f"({len(report['raters'])} người chấm)")
    lines.append(f"Case chung (đủ điểm mọi người chấm): {report['n_cases_common']}")
    if report["n_cases_incomplete"]:
        lines.append(f"⚠️ Case THIẾU điểm ở ≥1 người chấm (bị loại khỏi κ): "
                     f"{report['n_cases_incomplete']} — {sorted(report['incomplete_cases'].keys())}")

    k = report["overall_kappa"]
    k_str = f"{k:.4f}" if k is not None else "N/A"
    lines.append("")
    lines.append(f"κ TỔNG = {k_str}  → {report['overall_interpretation']}")
    lines.append(f"Đồng thuận hoàn toàn: {report['n_agree']}/{report['n_cases_common']} case")
    lines.append(f"Bất đồng: {report['n_disagree']}/{report['n_cases_common']} case")

    lines.append("")
    lines.append("κ theo domain:")
    for dom, d in report["by_domain"].items():
        kd = d["kappa"]
        kd_str = f"{kd:.4f}" if kd is not None else "N/A"
        lines.append(f"  {dom}: n={d['n_cases']:>2}  κ={kd_str:>7}  {d['note']}")

    if report["disagree_cases"]:
        lines.append("")
        lines.append("DANH SÁCH CASE BẤT ĐỒNG (sắp theo mức lệch giảm dần — bàn lại theo thứ tự này):")
        for d in report["disagree_cases"]:
            scores_str = ", ".join(f"{r}={s}" for r, s in d["scores"].items())
            spread_str = f" (lệch {d['spread']} bậc)" if d["spread"] is not None else ""
            lines.append(f"  - {d['case_id']}{spread_str}: {scores_str}")

    lines.append("")
    lines.append(f"⚠️ {report['disclaimer']}")
    lines.append("=" * 72)
    return "\n".join(lines)


# ─── Self-test bằng dữ liệu giả (không phải điểm MRAQ thật) ─────────────────

def _selftest():
    print("⚠️ SELF-TEST — DỮ LIỆU GIẢ LẬP, KHÔNG PHẢI ĐIỂM MRAQ V4 THẬT\n")

    # 2 người chấm, bảng 2x2 tự tính tay: po=0.7, pe=0.5 -> kappa=0.4
    ratings_2 = {
        "bs_an": {},
        "bs_binh": {},
    }
    # 20 case cả 2 cùng chấm "2", 5 case an=2/binh=1, 10 case an=1/binh=2, 15 case cả 2 chấm "1"
    cid = 0
    for _ in range(20):
        cid += 1
        ratings_2["bs_an"][f"C{cid}"] = {"score": "2", "notes": ""}
        ratings_2["bs_binh"][f"C{cid}"] = {"score": "2", "notes": ""}
    for _ in range(5):
        cid += 1
        ratings_2["bs_an"][f"C{cid}"] = {"score": "2", "notes": ""}
        ratings_2["bs_binh"][f"C{cid}"] = {"score": "1", "notes": ""}
    for _ in range(10):
        cid += 1
        ratings_2["bs_an"][f"C{cid}"] = {"score": "1", "notes": ""}
        ratings_2["bs_binh"][f"C{cid}"] = {"score": "2", "notes": ""}
    for _ in range(15):
        cid += 1
        ratings_2["bs_an"][f"C{cid}"] = {"score": "1", "notes": ""}
        ratings_2["bs_binh"][f"C{cid}"] = {"score": "1", "notes": ""}

    common_ids, incomplete = common_cases(ratings_2)
    k, method = compute_kappa(ratings_2, common_ids, ["1", "2"])
    print(f"[2 người chấm] κ Cohen = {k:.4f} (kỳ vọng tính tay = 0.4000) — {interpret_kappa(k)}")
    assert abs(k - 0.4) < 1e-9, "Self-test Cohen kappa SAI công thức!"

    print("\nSelf-test PASS — công thức κ khớp giá trị tính tay.")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Tính Cohen's κ / Fleiss' κ giữa các bản chấm mù độc lập cho case MRAQ V4."
    )
    ap.add_argument("--ratings-dir", help="Thư mục chứa rating_<ten_nguoi_cham>.{csv,json}")
    ap.add_argument("--out", help="Ghi báo cáo JSON đầy đủ ra file này (tuỳ chọn)")
    ap.add_argument(
        "--categories", default=None,
        help="Danh sách nhãn hợp lệ, phân cách bởi dấu phẩy (mặc định: 1,2,3,4 theo rubric MRAQ V4). "
             "Truyền 'any' để bỏ kiểm tra thang điểm.",
    )
    ap.add_argument("--selftest", action="store_true", help="Chạy self-test với dữ liệu giả")
    args = ap.parse_args(argv)

    if args.selftest:
        _selftest()
        return 0

    if not args.ratings_dir:
        ap.error("Cần --ratings-dir (hoặc --selftest)")

    if args.categories is None:
        categories = DEFAULT_CATEGORIES
    elif args.categories.strip().lower() == "any":
        categories = None
    else:
        categories = [c.strip() for c in args.categories.split(",") if c.strip()]

    try:
        report = build_report(args.ratings_dir, categories=categories, out_path=args.out)
    except RatingError as e:
        print(f"LỖI DỮ LIỆU: {e}", file=sys.stderr)
        return 1

    print(format_report_text(report))
    if args.out:
        print(f"\n(Đã ghi báo cáo JSON đầy đủ vào: {args.out})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
