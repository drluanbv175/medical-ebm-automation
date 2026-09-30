"""Hồi quy 30/09/2026: đầu ra RxNorm phải mang dòng miễn trừ NGUYÊN VĂN của NLM (điều khoản RxNav).

Điều khoản RxNav (https://lhncbc.nlm.nih.gov/RxNav/TermsofService.html — mở trang, đọc nguyên văn 30/09/2026) đề nghị
mọi ứng dụng dùng dữ liệu NLM kèm một câu miễn trừ. Từ 20/09 tới 30/09 `tra_thuoc_quoc_te.py chuan-hoa` chỉ ghi nguồn
«RxNorm (NLM RxNav REST)», CHƯA in câu đó (sổ nguồn của repo gốc, mục SRC-047, ghi là việc còn nợ).

Canh SÁU thứ — mỗi thứ là một cách việc này hỏng IM LẶNG:
  1. câu chữ bị sửa/dịch/diễn giải      ⇒ khoá SHA-256 tính trên VĂN BẢN CỦA TRANG THẬT (không phải trên chuỗi tự gõ);
  2. một đường trả về của client quên    ⇒ mọi trạng thái: khớp · gần đúng · không thấy · lỗi mạng · đầu vào bị từ chối;
  3. CLI in thiếu / in lặp / trộn trường ⇒ JSON và bản đọc đều có ĐÚNG MỘT lần, ở trường/dòng riêng;
  4. gắn nhầm sang `ema`                 ⇒ EMA không phải dữ liệu NLM, không được mang câu này;
  5. thêm trường làm lệch fail-closed cũ ⇒ `loi` ≠ không thấy, `gan_dung` không tự chấp nhận, mã thoát giữ nguyên;
  6. công cụ in mà agent không được dạy  ⇒ doctrine §1ter (cả bản `.claude` lẫn mirror `.codex`) phải trích đúng câu.
Ngoại tuyến hoàn toàn: HTTP giả, không gọi mạng. Hình dạng phản hồi mượn của `test_rxnorm_ema_medicines.py` (lấy từ
các lời gọi thật 20/09/2026).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import pytest

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

from app.sources.rxnorm import MIEN_TRU_NLM, NGUON, RxNormClient  # noqa: E402
from tests.test_rxnorm_ema_medicines import FakeHttp, _bg, _ema, _tuyen_gan_dung, _tuyen_glucophage  # noqa: E402
from tools import tra_thuoc_quoc_te as M  # noqa: E402

# Mã băm tính NGAY TRONG TRÌNH DUYỆT trên văn bản của trang điều khoản (30/09/2026, phần tử <li> chứa câu, bỏ hai dấu
# nháy bao ngoài; 263 ký tự ASCII). Không lấy từ hằng trong mã ⇒ gõ sai một ký tự là lệch.
SHA256_CAU_TREN_TRANG_DIEU_KHOAN = "1e8b7498c246e6d799396d49e4bda11c6b3ee3f529bc438d680f400c567720f7"
_KHOA_GOC = {"ten_nhap", "trang_thai", "ket_qua", "nguon", "canh_bao"}
_DONG_NGUON = "Nguồn: RxNorm (NLM RxNav REST). Cần bác sĩ kiểm chứng."


# ---------------------------------------------------------------- 1. nguyên văn
def test_mien_tru_nlm_dung_nguyen_van_tren_trang_dieu_khoan():
    assert hashlib.sha256(MIEN_TRU_NLM.encode("utf-8")).hexdigest() == SHA256_CAU_TREN_TRANG_DIEU_KHOAN, (
        "MIEN_TRU_NLM không còn là nguyên văn của NLM — không dịch, không diễn giải; NLM đổi câu chữ thì mở lại trang "
        "điều khoản, chép lại rồi cập nhật mã băm này cùng lúc")
    assert len(MIEN_TRU_NLM) == 263 and MIEN_TRU_NLM.isascii() and "  " not in MIEN_TRU_NLM
    assert MIEN_TRU_NLM.startswith("This product uses publicly available data from the U.S. National Library of Medi")
    assert MIEN_TRU_NLM.endswith("and does not endorse or recommend this or any other product.")


# ---------------------------------------------------------------- 2 + 5. client
def _tuyen_khong_thay() -> Dict[str, Any]:
    return {"rxcui.json": {"idGroup": {}}, "approximateTerm.json": {"approximateGroup": {}}}


def _tuyen_ma_ngung() -> Dict[str, Any]:
    return {"rxcui.json": {"idGroup": {"rxnormId": ["196500"]}},
            "rxcui/196500/properties.json": {"properties": {}},
            "rxcui/196500/historystatus.json": {"rxcuiStatusHistory": {
                "metaData": {"status": "Obsolete"}, "attributes": {"name": "Coversyl", "tty": "BN"}}}}


_PII = "bệnh nhân Nguyễn Văn A số điện thoại 0912345678 dùng metformin"
# (nhãn, hàm dựng HTTP giả, tên nhập, trạng thái phải ra, mã thoát phải ra)
CAC_CA: List[Tuple[str, Callable[[], FakeHttp], str, str, int]] = [
    ("khop_chinh_xac", lambda: FakeHttp(_tuyen_glucophage()), "Glucophage", "khop_chinh_xac", 0),
    ("ma_da_ngung", lambda: FakeHttp(_tuyen_ma_ngung()), "Coversyl", "khop_chinh_xac", 0),
    ("gan_dung", lambda: FakeHttp(_tuyen_gan_dung()), "metfromin", "gan_dung", 0),
    ("khong_thay", lambda: FakeHttp(_tuyen_khong_thay()), "xyzqwertyuiop", "khong_thay", 1),
    ("loi_mang_ngay_buoc_dau", lambda: FakeHttp(_tuyen_glucophage(), loi_o="rxcui.json"), "Glucophage", "loi", 2),
    ("loi_mang_giua_chung", lambda: FakeHttp(_tuyen_glucophage(), loi_o="related.json"), "Glucophage", "loi", 2),
    ("loi_ten_rong", lambda: FakeHttp({}), "   ", "loi", 2),
    ("loi_qua_dai", lambda: FakeHttp({}), "x" * 101, "loi", 2),
    ("loi_co_dau_hieu_pii", lambda: FakeHttp({}), _PII, "loi", 2),
]
_THAM_SO_CA = pytest.mark.parametrize("tao_http, ten, trang_thai, ma", [c[1:] for c in CAC_CA],
                                      ids=[c[0] for c in CAC_CA])


@_THAM_SO_CA
def test_moi_trang_thai_cua_client_deu_mang_dong_mien_tru_o_truong_rieng(tao_http, ten, trang_thai, ma):
    kq = RxNormClient(tao_http()).chuan_hoa(ten)
    assert kq["trang_thai"] == trang_thai and M.ma_thoat(kq) == ma  # hành vi cũ không đổi
    assert kq["mien_tru_nlm"] == MIEN_TRU_NLM  # nguyên văn, đủ mọi đường trả về
    # Trường RIÊNG: không trộn vào nguồn, không trộn vào cảnh báo; ngoài `mien_tru_nlm` không thêm khoá nào khác.
    assert kq["nguon"] == NGUON == "RxNorm (NLM RxNav REST)"
    assert not any("This product uses" in c for c in kq["canh_bao"])
    assert set(kq) - {"ly_do"} == _KHOA_GOC | {"mien_tru_nlm"}
    assert ("ly_do" in kq) == (trang_thai == "loi")


def test_them_truong_khong_lam_lech_ba_luat_fail_closed():
    """Ba luật cũ còn nguyên sau khi thêm trường: `loi` ≠ không thấy · `gan_dung` không tự chấp nhận · không thấy ≠
    không tồn tại."""
    loi = RxNormClient(FakeHttp(_tuyen_glucophage(), loi_o="rxcui.json")).chuan_hoa("Glucophage")
    assert loi["trang_thai"] == "loi" and loi["ket_qua"] == [] and M.ma_thoat(loi) == 2
    assert any("KHÔNG BIẾT" in c for c in loi["canh_bao"])

    gan = RxNormClient(FakeHttp(_tuyen_gan_dung())).chuan_hoa("metfromin")
    assert gan["trang_thai"] == "gan_dung" and gan["trang_thai"] != "khop_chinh_xac"
    assert [r["ten"] for r in gan["ket_qua"]][0] == "merbromin"  # thuốc KHÁC — vì thế không bao giờ tự chấp nhận
    assert any("look-alike" in c and "KHÔNG dùng tự động" in c for c in gan["canh_bao"])

    khong = RxNormClient(FakeHttp(_tuyen_khong_thay())).chuan_hoa("xyzqwertyuiop")
    assert khong["trang_thai"] == "khong_thay" and M.ma_thoat(khong) == 1
    assert any("KHÔNG có nghĩa thuốc không tồn tại" in c for c in khong["canh_bao"])


def test_dau_vao_bi_tu_choi_van_khong_goi_mang():
    """Dòng miễn trừ có mặt ở trạng thái `loi` KHÔNG có nghĩa đã gửi gì ra ngoài."""
    http = FakeHttp({})
    kq = RxNormClient(http).chuan_hoa(_PII)
    assert kq["trang_thai"] == "loi" and http.goi == [] and kq["mien_tru_nlm"] == MIEN_TRU_NLM


# ---------------------------------------------------------------- 3. CLI `chuan-hoa`
def _chay_chuan_hoa(monkeypatch, capsys, tao_http, ten: str, *co: str) -> Tuple[int, str]:
    monkeypatch.setattr(M, "RxNormClient", lambda: RxNormClient(tao_http()))
    ma = M.main(["chuan-hoa", ten, *co])
    return ma, capsys.readouterr().out


@_THAM_SO_CA
def test_cli_chuan_hoa_json_co_truong_rieng_dung_mot_lan(monkeypatch, capsys, tao_http, ten, trang_thai, ma):
    ma_thuc, ra = _chay_chuan_hoa(monkeypatch, capsys, tao_http, ten, "--json")
    d = json.loads(ra)
    assert ma_thuc == ma and d["trang_thai"] == trang_thai
    assert d["mien_tru_nlm"] == MIEN_TRU_NLM and ra.count(MIEN_TRU_NLM) == 1
    assert d["nguon"] == NGUON and not any("This product uses" in c for c in d["canh_bao"])


@_THAM_SO_CA
def test_cli_chuan_hoa_ban_doc_in_dung_mot_dong_nguyen_van(monkeypatch, capsys, tao_http, ten, trang_thai, ma):
    ma_thuc, ra = _chay_chuan_hoa(monkeypatch, capsys, tao_http, ten)
    dong = [d.strip() for d in ra.splitlines()]
    assert ma_thuc == ma and f"→ {trang_thai}" in dong[0]
    vi_tri = [i for i, d in enumerate(dong) if d == MIEN_TRU_NLM]  # cả DÒNG đúng bằng câu của NLM, không kèm chữ khác
    assert len(vi_tri) == 1 and ra.count(MIEN_TRU_NLM) == 1
    # Dòng nguồn cũ còn nguyên vẹn (không bị nối thêm câu của NLM), và câu miễn trừ đứng SAU nó.
    assert dong.count(_DONG_NGUON) == 1 and vi_tri[0] > dong.index(_DONG_NGUON)


class _ClientKhongGanDung:
    """Client thay thế trả kết quả THIẾU trường, hoặc mang một bản đã bị sửa/dịch — CLI vẫn phải in đúng nguyên văn."""

    _VANG = object()

    def __init__(self, gia_tri: Any = _VANG) -> None:
        self.gia_tri = gia_tri

    def chuan_hoa(self, ten: str) -> Dict[str, Any]:
        kq: Dict[str, Any] = {"ten_nhap": ten, "trang_thai": "khop_chinh_xac", "canh_bao": [], "nguon": NGUON,
                              "ket_qua": [{"rxcui": "6809", "ten": "metformin", "tty": "IN", "hoat_chat": [],
                                           "hieu_luc": True}]}
        if self.gia_tri is not self._VANG:
            kq["mien_tru_nlm"] = self.gia_tri
        return kq


_BAN_DICH = "Sản phẩm này dùng dữ liệu công khai của Thư viện Y khoa Quốc gia Hoa Kỳ"


@pytest.mark.parametrize("gia_tri", [_ClientKhongGanDung._VANG, None, "", _BAN_DICH],
                         ids=["vang_truong", "None", "rong", "ban_da_dich"])
@pytest.mark.parametrize("co", [(), ("--json",)], ids=["ban_doc", "json"])
def test_cli_tu_bao_dam_nguyen_van_du_client_thieu_hoac_sua_truong(monkeypatch, capsys, gia_tri, co):
    monkeypatch.setattr(M, "RxNormClient", lambda: _ClientKhongGanDung(gia_tri))
    assert M.main(["chuan-hoa", "metformin", *co]) == 0
    ra = capsys.readouterr().out
    assert ra.count(MIEN_TRU_NLM) == 1 and _BAN_DICH not in ra
    if co:
        assert json.loads(ra)["mien_tru_nlm"] == MIEN_TRU_NLM


_GIA_CP1252 = r'''
import sys
from tools import tra_thuoc_quoc_te as M

class GiaRx:
    def chuan_hoa(self, ten):
        return {"ten_nhap": ten, "trang_thai": "khop_chinh_xac", "canh_bao": ["đọc kỹ → cần bác sĩ"],
                "nguon": "RxNorm (giả lập)",
                "ket_qua": [{"rxcui": "6809", "ten": "metformin", "tty": "IN", "hoat_chat": [], "hieu_luc": True}]}

M.RxNormClient = GiaRx
sys.exit(M.chay_cli(["chuan-hoa", "Glucophage"] + sys.argv[1:]))
'''


@pytest.mark.parametrize("co", [(), ("--json",)], ids=["ban_doc", "json"])
def test_cli_chuan_hoa_duoi_console_cp1252_van_in_nguyen_van(co):
    """Console Windows (cp1252): dòng miễn trừ vẫn ra đúng MỘT lần, mã thoát không đổi, không UnicodeEncodeError."""
    env = dict(os.environ)
    env.update({"PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0", "PYTHONPATH": str(GOC), "USE_MOCK_SOURCES": "true"})
    kq = subprocess.run([sys.executable, "-X", "utf8=0", "-c", _GIA_CP1252, *co],
                        cwd=str(GOC), env=env, capture_output=True, timeout=120)
    assert kq.returncode == 0, kq.stderr.decode("utf-8", "replace")
    assert b"UnicodeEncodeError" not in kq.stderr
    assert kq.stdout.decode("utf-8").count(MIEN_TRU_NLM) == 1


# ---------------------------------------------------------------- 4. `ema` KHÔNG mang
def _cac_client_ema() -> Dict[str, Tuple[Any, str, int]]:
    du_lieu = [_bg("Avandia", "Rosiglitazone", "Expired")]
    return {"co_ket_qua": (_ema(du_lieu), "rosiglitazone", 0),
            "khong_thay": (_ema(du_lieu), "zzzzqqqq", 1),
            "loi_mang": (_ema(du_lieu, loi_o="medicines_json"), "rosiglitazone", 2),
            "loi_dau_vao": (_ema(du_lieu), "ab", 2)}


@pytest.mark.parametrize("ca", ["co_ket_qua", "khong_thay", "loi_mang", "loi_dau_vao"])
def test_client_ema_khong_co_truong_mien_tru_nlm(ca):
    client, tu_khoa, ma = _cac_client_ema()[ca]
    kq = client.tra(tu_khoa)
    assert M.ma_thoat(kq) == ma and "mien_tru_nlm" not in kq
    assert "National Library of Medicine" not in json.dumps(kq, ensure_ascii=False)


@pytest.mark.parametrize("ca", ["co_ket_qua", "khong_thay", "loi_mang", "loi_dau_vao"])
@pytest.mark.parametrize("co", [(), ("--json",)], ids=["ban_doc", "json"])
def test_cli_ema_khong_gan_dong_mien_tru_cua_nlm(monkeypatch, capsys, ca, co):
    client, tu_khoa, ma = _cac_client_ema()[ca]
    monkeypatch.setattr(M, "EmaMedicinesClient", lambda: client)
    assert M.main(["ema", tu_khoa, *co]) == ma
    ra = capsys.readouterr().out
    assert ra.strip()  # có in kết quả thật, không phải «không thấy câu» vì đầu ra rỗng
    for cam in ("mien_tru_nlm", MIEN_TRU_NLM, "National Library of Medicine", "Miễn trừ"):
        assert cam not in ra, f"lệnh `ema` không dùng dữ liệu NLM nhưng đầu ra lại có «{cam[:40]}»"


# ---------------------------------------------------------------- 6. doctrine dạy agent
@pytest.mark.parametrize("thu_muc", [".claude", ".codex"])
def test_doctrine_1ter_day_agent_in_dong_mien_tru_nguyen_van(thu_muc):
    """BH41/§6.4 của repo gốc: công cụ in mà doctrine không dạy thì agent trình kết quả vẫn thiếu dòng miễn trừ."""
    van_ban = (GOC / thu_muc / "agents" / "_CONNECTOR-CHUNG-CU.md").read_text(encoding="utf-8")
    i = van_ban.find("## 1ter. ")
    assert i >= 0, f"{thu_muc}: doctrine mất mục §1ter"
    j = van_ban.find("\n## ", i + 5)
    muc = van_ban[i:j if j > 0 else len(van_ban)]
    assert muc.count(MIEN_TRU_NLM) == 1, f"{thu_muc}: §1ter không trích đúng MỘT lần nguyên văn câu của NLM"
    dong = next(d for d in muc.splitlines() if MIEN_TRU_NLM in d)
    for can in ("`mien_tru_nlm`", "ĐÚNG MỘT lần", "không dịch", "KHÔNG chép dòng đó vào artifact", "`ema`"):
        assert can in dong, f"{thu_muc}: luật in dòng miễn trừ ở §1ter thiếu «{can}»"
