"""Script R tái lặp Bảng 5 (MI) — thêm 29/09/2026.

Trước đây `generate_r_script` không có khối MI nên Bảng 5 (Python MICE) không tái lặp độc lập bằng R được.
Kiểm văn bản script (CI không có R): chỉ chạy khi biến phân tích có thiếu; không cụm ⇒ mice::pool; có cụm ⇒
Rubin thủ công trên vcovCL + t(G−1) như `_suy_luan_t_cum`; mã cụm không vào mô hình impute.
Chạy thật trong R vẫn là việc cần kiểm chứng [CẦN KIỂM CHỨNG].
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))
import run_stats_analysis as RSA  # noqa: E402


def _mi(script: str) -> str:
    assert "# 3d. Bảng 5" in script
    return script.split("# 3d. Bảng 5")[1].split("# 4. Kiểm tra giả định")[0]


def test_khong_cum_dung_pool_chuan():
    k = _mi(RSA.generate_r_script("S", "G6", "diem", "nhom", ["x", "tuoi"], "continuous"))
    assert 'vars_mi <- c("diem", "nhom", "x", "tuoi")' in k
    assert "if (anyNA(data[, vars_mi]))" in k
    assert 'mice(data[, vars_mi], m = 20, method = "pmm", seed = 42' in k
    assert "with(imp, glm(diem ~ nhom + x + tuoi, family = gaussian))" in k
    assert "pool(fit_mi)" in k and "vcovCL" not in k and "qt(" not in k


def test_co_cum_rubin_tren_vcovcl_va_t_g_tru_1():
    k = _mi(RSA.generate_r_script("S", "G6", "hl", "nhom", ["x"], "binary", "ban"))
    assert "d_mi <- data[!is.na(data$ban)" in k
    assert 'pred[, "ban"] <- 0' in k
    assert "vcovCL(m_i, cluster = ~ ban)" in k
    assert "t_tot <- u_bar + (1 + 1 / imp$m) * cov(B_mat)" in k
    assert "df_mi <- length(unique(d_mi$ban)) - 1" in k
    assert "q_t <- qt(0.975, df_mi)" in k
    assert "pt(abs(q_bar / se_mi), df_mi, lower.tail = FALSE)" in k
    assert "exp(bang5[, 1:3])" in k and "pool(" not in k


def test_co_cum_lien_tuc_khong_mu_hoa():
    k = _mi(RSA.generate_r_script("S", "G6", "diem", "nhom", ["x"], "continuous", "ban"))
    assert "exp(" not in k and "family = gaussian" in k


def test_khoi_mi_nam_sau_khoi_cum_can_sandwich():
    s = RSA.generate_r_script("S", "G6", "hl", "nhom", ["x"], "binary", "ban")
    assert s.index("library(sandwich)") < s.index("# 3d. Bảng 5")
