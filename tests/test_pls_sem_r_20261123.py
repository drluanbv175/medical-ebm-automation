"""PLS-SEM — phép thử TÍCH HỢP R (23/11/2026): seminr và cSEM trên dữ liệu mô phỏng phải khớp nhau theo đúng luật kiểm
chéo của tools/pls_sem.py. Tự bỏ qua khi máy không có R hoặc thiếu gói (CI không cài R ngoài job giả lập PLS-SEM).
Tách khỏi test_pls_sem_20261123.py để tệp đó thuần Python (sổ kiểm đột biến định kỳ). Cần bác sĩ kiểm chứng."""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import pls_sem as PLS  # noqa: E402

from tests.test_pls_sem_20261123 import _sap  # noqa: E402


def _r_san_sang() -> bool:
    try:
        rs, ma, _ = PLS._r_san_sang()
    except Exception:  # noqa: BLE001
        return False
    return rs is not None and ma == 0


@pytest.mark.skipif(not _r_san_sang(), reason="máy không có R hoặc thiếu seminr/cSEM")
def test_r_seminr_khop_csem_tren_du_lieu_mo_phong(tmp_path):
    rng = random.Random(7)
    mh = PLS.doc_sap(_sap())
    mh["bootstrap"] = 600
    muc = [m for c in mh["cau_truc"] for m in c["muc"]]
    dong = []
    for _ in range(250):
        gt, hbx = rng.gauss(0, 1), [rng.gauss(0, 1) for _ in range(3)]
        hb = (0.5 * hbx[0] + 0.4 * hbx[1] + 0.3 * hbx[2]) / 0.707
        nt = 0.4 * gt + 0.3 * hb + rng.gauss(0, 0.8)
        tt = 0.3 * gt + 0.4 * nt + 0.2 * hb + rng.gauss(0, 0.75)
        r = [0.8 * gt + rng.gauss(0, 0.6) for _ in range(3)] + hbx + \
            [0.8 * nt + rng.gauss(0, 0.6) for _ in range(3)] + [0.8 * tt + rng.gauss(0, 0.6) for _ in range(3)]
        dong.append(r)
    p = tmp_path / "d.csv"
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(muc)
        w.writerows([[repr(x) for x in r] for r in dong])
    ch = PLS.cau_hinh_r(mh, PLS.S.sha256_tep(p), luot_mc=2)
    (tmp_path / "ch.json").write_text(json.dumps(ch), encoding="utf-8", newline="\n")
    (tmp_path / "pls.R").write_text(PLS.R.kich_ban_pls_sem(), encoding="utf-8", newline="\n")
    rs = PLS.R.tim_r()
    ma, _o, err = PLS.R.chay_r(rs, [str(tmp_path / "pls.R"), str(p), str(tmp_path / "kq.json"),
                                    str(tmp_path / "ch.json")], thu_muc=tmp_path, thoi_han=900)
    kq = json.loads((tmp_path / "kq.json").read_text(encoding="utf-8"))
    assert ma == 0 and not kq["loi"], err[-500:]
    kc = PLS.doi_chieu(kq, mh)
    lech = [x for x in kc["dong"] if x["ket"] == "LECH"]
    assert kc["trang_thai"] == "KHOP", lech[:5]
    dg = PLS.danh_gia(kq["seminr"], mh)
    assert len(dg["cau_truc"]) == 5 and dg["plspredict"]["chi_bao"]
    assert PLS.trinh_bay_ket_qua(dg, None, kc)
