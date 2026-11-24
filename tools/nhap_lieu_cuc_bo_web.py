#!/usr/bin/env python3
"""GIAO DIỆN WEB CỤC BỘ của hệ nhập liệu theo từ điển G5 (`tools/nhap_lieu_cuc_bo.py`, 23/11/2026).

Chỉ nghe 127.0.0.1 (không có tuỳ chọn mở ra mạng), cổng tự chọn; KHÔNG có chế độ người bệnh tự điền. Mọi nghiệp vụ
(đánh giá logic nhánh, calc, kiểm giá trị, lý do sửa, nhật ký chuỗi băm, nhập kép, truy vấn, khoá, xuất) nằm ở lớp
dịch vụ `Kho` — trang web chỉ dựng biểu mẫu và GỬI LẠI TRANG để máy chủ đánh giá bằng đúng `danh_gia_logic`.

An toàn trình duyệt: chặn Host lạ (chống DNS rebinding), mã chống giả mạo yêu cầu (CSRF) cho mọi POST, cookie
SameSite=Strict + HttpOnly, khoá bí mật phiên sinh ngẫu nhiên mỗi lần mở, phiên hết hạn sau 30 phút không thao tác,
không tải CSS/JS từ mạng. Quy trách phiên cục bộ — KHÔNG phải chữ ký điện tử. Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import secrets
import sys
import time
import webbrowser
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import cau_noi_spss as SP  # noqa: E402
import nhap_lieu_cuc_bo as M  # noqa: E402

MAY_CHU = "127.0.0.1"
HET_HAN_PHIEN = 30 * 60  # giây không thao tác
TEN_VAI = {"nhap_lieu_1": "nhập lượt 1", "nhap_lieu_2": "nhập lượt 2", "quan_ly_du_lieu": "quản lý dữ liệu"}

_CSS = """
body{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:0;background:#f6f7f9;color:#1d2330;
font-size:15px}
header{background:#1f3a5f;color:#fff;padding:10px 18px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
header a{color:#fff}header form{margin:0}main{max-width:1050px;margin:16px auto;padding:0 16px}
.the{background:#fff;border:1px solid #d9dde4;border-radius:8px;padding:14px 16px;margin-bottom:14px}
table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #e4e7ec;padding:6px 8px;text-align:left;
vertical-align:top}th{background:#eef1f5}.loi{color:#b3261e;font-weight:600}.canh{color:#8a5300}.ok{color:#1b7a3a}
.an{color:#7a8190;font-style:italic}.nhan{font-weight:600}.ghichu{color:#5b6372;font-size:13px}
.truong{padding:10px 0;border-bottom:1px dashed #e4e7ec}.phan{background:#eef1f5;padding:6px 10px;margin-top:10px;
font-weight:700}input[type=text],select,textarea{padding:5px;border:1px solid #b9c0cc;border-radius:4px;font-size:15px}
textarea{width:100%;min-height:60px}button{padding:6px 14px;border-radius:5px;border:1px solid #1f3a5f;
background:#1f3a5f;color:#fff;cursor:pointer}button.phu{background:#fff;color:#1f3a5f}.tb{padding:8px 12px;
border-radius:6px;margin-bottom:10px}.tb.loi{background:#fde7e6}.tb.ok{background:#e6f4ea}.tb.canh{background:#fff4e0}
.chan{font-size:12px;color:#5b6372;margin-top:24px}.lydo{margin-top:4px}.lydo input{width:60%}
"""

_MAU = {
    "co_so.html": """<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Nhập liệu — {{ study }}</title>
<style>{{ css }}</style></head><body>
<header><strong>Hệ nhập liệu cục bộ · {{ study }}</strong>
{% if phien %}<span>{{ phien.ma }} — {{ ten_vai[phien.vai] }}</span><a href="{{ url_for('ds_phieu') }}">Phiếu</a>
<a href="{{ url_for('ds_truy_van') }}">Truy vấn</a>
{% if phien.vai == 'quan_ly_du_lieu' %}<a href="{{ url_for('nguoi') }}">Người nhập</a>
<a href="{{ url_for('xuat') }}">Xuất</a><a href="{{ url_for('kiem_nhat_ky') }}">Kiểm nhật ký</a>{% endif %}
<form method="post" action="{{ url_for('dang_xuat') }}"><input type="hidden" name="_csrf" value="{{ csrf }}">
<button class="phu">Đăng xuất</button></form>{% endif %}</header><main>
{% for loai, nd in thong_bao %}<div class="tb {{ loai }}">{{ nd }}</div>{% endfor %}
{% block noi_dung %}{% endblock %}
<div class="chan">{{ quy_trach }} Máy chỉ nghe 127.0.0.1 — không mở ra mạng. {{ can_kiem }}</div>
</main></body></html>""",
    "dang_nhap.html": """{% extends "co_so.html" %}{% block noi_dung %}<div class="the"><h2>Đăng nhập</h2>
<form method="post"><input type="hidden" name="_csrf" value="{{ csrf }}">
<p>Mã người nhập <input type="text" name="ma" autocomplete="off" required></p>
<p>PIN (nếu đã đặt) <input type="password" name="pin" autocomplete="off"></p><button>Vào</button></form>
<p class="ghichu">Chỉ dùng mã/chữ viết tắt đã khai; không gõ họ tên.</p></div>{% endblock %}""",
    "loi.html": """{% extends "co_so.html" %}{% block noi_dung %}<div class="the"><p class="loi">{{ loi }}</p>
<a href="{{ url_for('ds_phieu') }}">Về danh sách phiếu</a></div>{% endblock %}""",
    "ds_phieu.html": """{% extends "co_so.html" %}{% block noi_dung %}<div class="the"><h2>Phiếu</h2>
<form method="post"><input type="hidden" name="_csrf" value="{{ csrf }}">Mã phiếu mới
<input type="text" name="record_id" autocomplete="off" placeholder="vd BN-001"> <button>Tạo phiếu</button></form></div>
<div class="the"><table><tr><th>Mã phiếu</th>{% if la_ql %}<th>Lượt 1</th><th>Lượt 2</th><th>Đối chiếu</th>
<th>Ô lệch mở</th><th>Truy vấn mở</th><th>Khoá</th>{% else %}<th>Lượt của bạn</th>{% endif %}</tr>
{% for p in ds %}<tr><td><a href="{{ url_for('phieu', rid=p.record_id) }}">{{ p.record_id }}</a>
{% if p.nham %}<span class="an">(nhầm mã)</span>{% endif %}</td>
{% if la_ql %}<td>{{ 'xong' if p.lan1_xong else (p.lan1_nguoi and 'đang nhập' or '—') }}</td>
<td>{{ 'xong' if p.lan2_xong else (p.lan2_nguoi and 'đang nhập' or '—') }}</td>
<td>{{ 'đã đối chiếu' if p.da_doi_chieu else '—' }}</td><td>{{ p.lech_mo }}</td><td>{{ p.truy_van_mo }}</td>
<td>{{ 'KHOÁ' if p.khoa else '' }}</td>{% else %}
<td>{{ 'xong' if p[lan ~ '_xong'] else ('đang nhập' if p[lan ~ '_nguoi'] == phien.ma else
('người khác' if p[lan ~ '_nguoi'] else 'chưa nhập')) }}</td>{% endif %}</tr>{% endfor %}</table></div>
{% endblock %}""",
    "phieu.html": """{% extends "co_so.html" %}{% block noi_dung %}<div class="the"><h2>Phiếu {{ rid }}</h2>
{% if p.khoa %}<p class="ok">Phiếu đã KHOÁ.</p>{% endif %}
{% if p.nham %}<p class="an">Đã đánh dấu nhầm mã.</p>{% endif %}
{% if lan %}<h3>Biểu mẫu — {{ lan }}</h3><table>{% for f in forms %}<tr><td>
<a href="{{ url_for('bieu_mau', rid=rid, lan=lan, form=f) }}">{{ f }}</a></td>
<td>{{ 'đã lưu' if f in da_luu else 'chưa lưu' }}</td></tr>{% endfor %}</table>
<form method="post" action="{{ url_for('hoan_tat', rid=rid, lan=lan) }}"><input type="hidden" name="_csrf"
value="{{ csrf }}"><p><button>Hoàn tất lượt {{ lan }}</button>
<span class="ghichu">mọi biểu mẫu đã lưu, câu bắt buộc có giá trị hoặc mã thiếu</span></p></form>{% endif %}
{% if la_ql %}<p><a href="{{ url_for('doi_chieu', rid=rid) }}">Đối chiếu nhập kép</a> ·
<a href="{{ url_for('ds_truy_van', rid=rid) }}">Truy vấn của phiếu</a></p>
{% if chot %}<h3>Bản chốt</h3><table><tr><th>Trường</th><th>Giá trị</th></tr>{% for c, v in chot %}
<tr><td>{{ c }}</td><td>{{ v }}</td></tr>{% endfor %}</table>
<form method="post" action="{{ url_for('sua_chot', rid=rid) }}"><input type="hidden" name="_csrf" value="{{ csrf }}">
<p>Sửa bản chốt: trường <select name="cot">{% for c, v in chot %}<option>{{ c }}</option>{% endfor %}</select>
giá trị <input type="text" name="gia_tri"> lý do <input type="text" name="ly_do"> tham chiếu phiếu gốc
<input type="text" name="tham_chieu"> <button>Sửa</button></p></form>{% endif %}
<form method="post" action="{{ url_for('khoa', rid=rid) }}"><input type="hidden" name="_csrf" value="{{ csrf }}">
{% if p.khoa %}<p>Lý do mở khoá <input type="text" name="ly_do">
<button name="hanh_dong" value="mo">Mở khoá</button></p>
{% else %}<p><button name="hanh_dong" value="khoa">Khoá phiếu</button>
<span class="ghichu">sau đối chiếu xong và hết truy vấn mở</span></p>{% endif %}</form>
{% if not p.khoa %}<form method="post" action="{{ url_for('nham_ma', rid=rid) }}"><input type="hidden" name="_csrf"
value="{{ csrf }}"><p>Lý do <input type="text" name="ly_do"> <button class="phu" name="nham" value="{{ '0' if p.nham
else '1' }}">{{ 'Bỏ đánh dấu nhầm mã' if p.nham else 'Đánh dấu nhầm mã' }}</button></p></form>{% endif %}{% endif %}
</div>{% endblock %}""",
    "bieu_mau.html": """{% extends "co_so.html" %}{% block noi_dung %}<div class="the">
<h2>{{ rid }} · {{ lan }} · {{ form }}</h2>
{% if chua_luu %}<div class="tb canh">Đang xem thử — CHƯA LƯU.</div>{% endif %}
{% for x in loi_chung %}<div class="tb loi">{{ x }}</div>{% endfor %}
{% for x in canh_chung %}<div class="tb canh">{{ x }}</div>{% endfor %}
<form method="post" id="bm"><input type="hidden" name="_csrf" value="{{ csrf }}">
{% for t in truong %}{% if t.phan %}<div class="phan">{{ t.phan }}</div>{% endif %}<div class="truong">
{% if t.kieu == 'mo_ta' %}<div class="ghichu">{{ t.nhan }}</div>
{% elif t.kieu == 'dinh_danh' %}<div class="an">{{ t.nhan }} — trường ĐỊNH DANH: không nhập vào hệ (chỉ ghi trên phiếu
giấy).</div>
{% elif t.kieu == 'an' %}<div class="an">{{ t.nhan }} — đang ẩn theo logic nhánh.</div>
{% elif t.kieu == 'calc' %}<div><span class="nhan">{{ t.nhan }}</span> (máy tính):
{% if t.loi %}<span class="canh">không tính được — {{ t.loi }}</span>
{% else %}<strong>{{ t.gia_tri }}</strong>{% endif %}
</div>{% else %}
<div class="nhan">{{ t.nhan }}{% if t.bat_buoc %} <span class="loi">*</span>{% endif %}</div>
{% if t.ghi_chu %}<div class="ghichu">{{ t.ghi_chu }}</div>{% endif %}
{% if t.goi_y %}<div class="ghichu">{{ t.goi_y }}</div>{% endif %}
{% if t.hien == none %}<div class="canh">Máy không đánh giá được logic nhánh — đối chiếu phiếu gốc.</div>{% endif %}
{% if t.hien == false %}<div class="loi">Câu đang bị ẩn theo logic nhánh nhưng còn giá trị — xoá giá trị (kèm lý do nếu
đã lưu) hoặc kiểm lại câu điều kiện.</div>{% endif %}
{% for c in t.cot %}<input type="hidden" name="hien" value="{{ c }}">{% endfor %}
{% if t.kieu == 'hop' %}{% for c, ma, nhan, chon in t.hop %}<label><input type="checkbox" name="f__{{ c }}" value="1"
{% if chon %}checked{% endif %}{% if t.kich %} onchange="xemLai()"{% endif %}> {{ ma }} — {{ nhan }}</label><br>
{% endfor %}
{% elif t.kieu == 'radio' %}{% for ma, nhan in t.lua_chon %}<label><input type="radio" name="f__{{ t.ten }}"
value="{{ ma }}" {% if t.gia_tri == ma %}checked{% endif %}{% if t.kich %} onchange="xemLai()"{% endif %}>
{{ ma }} — {{ nhan }}</label><br>{% endfor %}<label><input type="radio" name="f__{{ t.ten }}" value=""
{% if t.gia_tri == '' %}checked{% endif %}{% if t.kich %} onchange="xemLai()"{% endif %}> (để trống)</label>
{% elif t.kieu == 'select' %}<select name="f__{{ t.ten }}"{% if t.kich %} onchange="xemLai()"{% endif %}>
<option value="">(để trống)</option>{% for ma, nhan in t.lua_chon %}<option value="{{ ma }}"
{% if t.gia_tri == ma %}selected{% endif %}>{{ ma }} — {{ nhan }}</option>{% endfor %}</select>
{% elif t.kieu == 'van_ban' %}<textarea name="f__{{ t.ten }}">{{ t.gia_tri_o }}</textarea>
{% else %}<input type="{{ t.loai_input }}" name="f__{{ t.ten }}" value="{{ t.gia_tri_o }}" autocomplete="off"
{% if t.kieu in ('so', 'so_nguyen') %}inputmode="decimal"{% endif %}{% if t.kich %} onchange="xemLai()"{% endif %}>
{% if t.ma_thieu %} hoặc mã thiếu <select name="mt__{{ t.ten }}"{% if t.kich %} onchange="xemLai()"{% endif %}>
<option value="">—</option>{% for ma, nhan in t.ma_thieu %}<option value="{{ ma }}"{% if t.gia_tri == ma %}
selected{% endif %}>{{ ma }} — {{ nhan }}</option>{% endfor %}</select>{% endif %}{% endif %}
{% for x in t.loi %}<div class="loi">{{ x }}</div>{% endfor %}{% for x in t.canh_bao %}<div class="canh">{{ x }}</div>
{% endfor %}{% if t.da_luu %}<div class="lydo ghichu">Lý do sửa (bắt buộc nếu đổi giá trị đã lưu)
<input type="text" name="lydo__{{ t.ten }}" value="{{ t.ly_do }}"></div>{% endif %}{% endif %}</div>{% endfor %}
<p><button name="hanh_dong" value="luu">Lưu biểu mẫu</button>
<button class="phu" name="hanh_dong" value="xem">Cập nhật hiển thị (không lưu)</button>
<a href="{{ url_for('phieu', rid=rid) }}">Về phiếu</a></p></form></div>
<script>function xemLai(){var f=document.getElementById('bm');var a=document.createElement('input');a.type='hidden';
a.name='hanh_dong';a.value='xem';f.appendChild(a);f.submit();}</script>{% endblock %}""",
    "doi_chieu.html": """{% extends "co_so.html" %}{% block noi_dung %}<div class="the">
<h2>Đối chiếu nhập kép — {{ rid }}</h2>
{% if not tt.da_doi_chieu %}<form method="post">
<input type="hidden" name="_csrf" value="{{ csrf }}">
<button name="hanh_dong" value="doi_chieu">Đối chiếu từng ô (hai lượt đã hoàn tất)</button></form>{% else %}
<p>{{ tt.so_o }} ô so sánh · {{ tt.lech|length }} ô lệch · còn {{ tt.con_lech }} chưa giải quyết</p>
<table><tr><th>Trường</th><th>Lượt 1</th><th>Lượt 2</th><th>Giải quyết theo phiếu gốc</th></tr>
{% for x in tt.lech %}<tr><td>{{ x.cot }}</td><td>{{ x.gia_tri_lan1 or '∅' }}</td><td>{{ x.gia_tri_lan2 or '∅' }}</td>
<td>{% if x.giai_quyet %}<span class="ok">đã giải quyết</span>{% else %}<form method="post">
<input type="hidden" name="_csrf" value="{{ csrf }}"><input type="hidden" name="cot" value="{{ x.cot }}">
<label><input type="radio" name="chon" value="lan1" checked> theo lượt 1</label>
<label><input type="radio" name="chon" value="lan2"> theo lượt 2</label>
<label><input type="radio" name="chon" value="khac"> khác:</label> <input type="text" name="gia_tri_khac" size="10"><br>
lý do <input type="text" name="ly_do"> tham chiếu phiếu gốc <input type="text" name="tham_chieu"
placeholder="vd phiếu giấy trang 2"> <button name="hanh_dong" value="giai_quyet">Ghi</button></form>{% endif %}</td>
</tr>{% endfor %}</table>{% endif %}<p><a href="{{ url_for('phieu', rid=rid) }}">Về phiếu</a></p></div>
{% endblock %}""",
    "truy_van.html": """{% extends "co_so.html" %}{% block noi_dung %}<div class="the"><h2>Truy vấn dữ liệu</h2>
{% if la_ql %}<form method="post" action="{{ url_for('quet_truy_van') }}"><input type="hidden" name="_csrf"
value="{{ csrf }}"><button>Quét truy vấn tự động (luật DQ, khoảng, logic)</button></form>
<form method="post" action="{{ url_for('tao_truy_van') }}"><input type="hidden" name="_csrf" value="{{ csrf }}">
<p>Truy vấn tay: mã phiếu <input type="text" name="record_id" size="10"> trường <input type="text" name="cot" size="12">
nội dung <input type="text" name="noi_dung" size="40"> <button>Tạo</button></p></form>{% endif %}
<table><tr><th>#</th><th>Phiếu</th><th>Trường</th><th>Nguồn</th><th>Nội dung</th>
{% if la_ql %}<th>Giá trị</th>{% endif %}
<th>Trạng thái</th><th>Trả lời</th><th></th></tr>{% for q in ds %}<tr><td>{{ q.id }}</td><td>{{ q.record_id }}</td>
<td>{{ q.cot }}</td><td>{{ q.nguon }}</td><td>{{ q.noi_dung }}</td>{% if la_ql %}<td>{{ q.gia_tri }}</td>{% endif %}
<td>{{ q.trang_thai }}</td><td>{{ q.tra_loi }}{% if q.dong_ly_do %}<br><span class="ghichu">đóng: {{ q.dong_ly_do }}
</span>{% endif %}</td><td>{% if q.trang_thai != 'dong' %}
<form method="post" action="{{ url_for('tra_loi', qid=q.id) }}">
<input type="hidden" name="_csrf" value="{{ csrf }}"><input type="text" name="noi_dung" size="18">
<button class="phu">Trả lời</button></form>{% if la_ql %}<form method="post" action="{{ url_for('dong', qid=q.id) }}">
<input type="hidden" name="_csrf" value="{{ csrf }}"><input type="text" name="ly_do" size="18" placeholder="lý do đóng">
<button class="phu">Đóng</button></form>{% endif %}{% endif %}</td></tr>{% endfor %}</table></div>{% endblock %}""",
    "nguoi.html": """{% extends "co_so.html" %}{% block noi_dung %}<div class="the">
<h2>Người nhập (khai theo đề tài)</h2>
<table><tr><th>Mã</th><th>Vai</th><th>PIN</th></tr>{% for n in ds %}<tr><td>{{ n.ma }}</td><td>{{ ten_vai[n.vai] }}</td>
<td>{{ 'có' if n.co_pin else 'không' }}</td></tr>{% endfor %}</table>
<form method="post"><input type="hidden" name="_csrf" value="{{ csrf }}"><p>Mã/chữ viết tắt
<input type="text" name="ma" size="10" autocomplete="off"> vai <select name="vai">{% for v, t in ten_vai.items() %}
<option value="{{ v }}">{{ t }}</option>{% endfor %}</select> PIN (tuỳ chọn) <input type="password" name="pin"
autocomplete="new-password"> <button>Khai</button></p></form></div>{% endblock %}""",
    "xuat.html": """{% extends "co_so.html" %}{% block noi_dung %}<div class="the"><h2>Xuất CSV khuôn REDCap</h2>
<form method="post"><input type="hidden" name="_csrf" value="{{ csrf }}"><p>Thư mục ra (ngoài repo, ngoài OneDrive)
<input type="text" name="ra" size="60" value="{{ ra }}"></p><p><label><input type="checkbox" name="ban_nhap" value="1">
Bản NHÁP (còn phiếu chưa khoá)</label> <label><input type="checkbox" name="tiep_nhan" value="1"> Gọi luôn cổng tiếp
nhận</label></p><button>Xuất</button></form>{% if kq %}<p class="ok">CSV: {{ kq.csv }} · {{ kq.so_phieu }} phiếu ·
SHA-256 {{ kq.csv_sha256[:16] }}…</p><p>Bằng chứng cho G5 (không giá trị): {{ kq.bang_chung }}</p>
{% if kq.tiep_nhan %}<p>Cổng tiếp nhận: {{ kq.tiep_nhan.status }}</p>{% endif %}{% endif %}</div>{% endblock %}""",
    "kiem.html": """{% extends "co_so.html" %}{% block noi_dung %}<div class="the"><h2>Kiểm nhật ký kiểm toán</h2>
{% if kt.dat %}<p class="ok">KHỚP: {{ kt.so_ban_ghi }} bản ghi · đầu chuỗi {{ kt.dau_chuoi.hash[:16] }}… · neo khớp ·
phát lại khớp kho.</p>{% else %}<p class="loi">KHÔNG ĐẠT:</p><ul>{% for x in kt.loi %}<li class="loi">{{ x }}</li>
{% endfor %}</ul>{% endif %}</div>{% endblock %}""",
}


def _ten_tham_chieu(kh: M.KeHoach) -> set[str]:
    """Trường mà logic nhánh/calc tham chiếu — đổi giá trị của chúng thì tự gửi lại trang để máy chủ đánh giá."""
    bt = [c.nhanh for c in kh.cot] + [ct for _, ct in kh.ds_calc]
    return {m.group(1) for x in bt for m in M._THAM_CHIEU_RE.finditer(x or "")}


def truong_hien_thi(kho: M.Kho, kq: M.KetQuaBieuMau, form: str, ly_do: dict[str, str]) -> list[dict]:
    """Mô hình hiển thị từng câu của MỘT biểu mẫu theo đúng thứ tự từ điển (gồm descriptive, calc, định danh)."""
    kh = kho.kh
    kich = _ten_tham_chieu(kh)
    ra: list[dict] = []
    for t in kh.td[1:]:
        if (t["form"] or "du_lieu") != form:
            continue
        ten, loai = t["ten"], t["loai"].lower()
        chung = {"ten": ten, "nhan": SP.bo_html(t["nhan"]) or ten, "phan": SP.bo_html(t["phan"]),
                 "ghi_chu": SP.bo_html(t["ghi_chu"])}  # fmt: skip
        if loai == "descriptive":
            ra.append({**chung, "kieu": "mo_ta"})
            continue
        if loai == "calc":
            ra.append({**chung, "kieu": "calc", "gia_tri": kq.calc.get(ten), "loi": kq.loi_calc.get(ten)})
            continue
        cot = [c for c in kh.cot_tat_ca if c.truong == ten]
        if not cot:
            continue  # file/sql: không nhập tay
        if any(c.ten in kh.dinh_danh for c in cot):
            ra.append({**chung, "kieu": "dinh_danh"})
            continue
        hien = kq.hien_thi.get(cot[0].ten, True)
        loi = [x for c in cot for x in kq.loi.get(c.ten, [])]
        canh = [x for c in cot for x in kq.canh_bao.get(c.ten, [])]
        if cot[0].kieu == "hop":
            chon = [kq.gia_tri.get(c.ten) == "1" for c in cot]
            co_gt = any(chon) or any(kq.da_luu.get(c.ten) == "1" for c in cot)
            if hien is False and not co_gt and not loi:
                ra.append({**chung, "kieu": "an"})
                continue
            ra.append({**chung, "kieu": "hop", "cot": [c.ten for c in cot], "hien": hien, "loi": loi, "canh_bao": canh,
                       "hop": [(c.ten, c.ma_hop, c.lua_chon.get(c.ma_hop, ""), ch) for c, ch in zip(cot, chon)],
                       "bat_buoc": any(c.bat_buoc for c in cot), "kich": ten in kich,
                       "da_luu": any(kq.da_luu.get(c.ten) == "1" for c in cot),
                       "ly_do": ly_do.get(ten, "")})  # fmt: skip
            continue
        c = cot[0]
        gt = kq.gia_tri.get(c.ten, "")
        if hien is False and gt == "" and not loi:
            ra.append({**chung, "kieu": "an"})
            continue
        goi_y = []
        if c.kieu in ("so_nguyen", "so"):
            goi_y.append(("số nguyên" if c.kieu == "so_nguyen" else "số, dấu chấm thập phân")
                         + (f", từ {c.min}" if c.min else "") + (f" đến {c.max}" if c.max else ""))  # fmt: skip
        elif c.kieu == "ngay":
            goi_y.append("ngày dạng năm-tháng-ngày" + (f", từ {c.min}" if c.min else "")
                         + (f" đến {c.max}" if c.max else ""))  # fmt: skip
        if c.ma_thieu and c.kieu != "ma":
            goi_y.append("phiếu bỏ trống/không đọc được ⇒ chọn mã thiếu")
        loai_input = {"ngay": "date", "ngay_gio": "datetime-local", "gio": "time"}.get(c.kieu, "text")
        la_mt = gt in c.ma_thieu
        gia_tri_o = "" if la_mt else (gt.replace(" ", "T") if c.kieu == "ngay_gio" else gt)
        if c.kieu == "ma":
            kieu = "select" if loai == "dropdown" else "radio"
            lua_chon = list(c.lua_chon.items()) + list(c.ma_thieu.items())
        else:
            kieu, lua_chon = c.kieu, []
        ra.append({**chung, "kieu": kieu, "cot": [c.ten], "hien": hien, "loi": loi, "canh_bao": canh,
                   "gia_tri": gt, "gia_tri_o": gia_tri_o, "lua_chon": lua_chon, "ma_thieu": list(c.ma_thieu.items()),
                   "loai_input": loai_input, "goi_y": "; ".join(goi_y), "bat_buoc": c.bat_buoc, "kich": ten in kich,
                   "da_luu": kq.da_luu.get(c.ten, "") != "", "ly_do": ly_do.get(c.ten, "")})  # fmt: skip
    return ra


def doc_bieu_mau_gui(kho: M.Kho, form_du_lieu) -> tuple[dict[str, str], dict[str, str], dict[str, list[str]]]:
    """POST của biểu mẫu ⇒ (giá trị CHỈ của các câu đã hiện trên trang, lý do sửa, lỗi của chính trang web)."""
    gia_tri: dict[str, str] = {}
    ly_do: dict[str, str] = {}
    loi: dict[str, list[str]] = {}
    for ten in form_du_lieu.getlist("hien"):
        c = kho.kh.cot_theo_ten.get(ten)
        if c is None:
            if ten in kho.kh.dinh_danh:
                gia_tri[ten] = form_du_lieu.get(f"f__{ten}", "")  # để lớp dịch vụ TỪ CHỐI và ghi rõ lý do
            continue
        if c.kieu == "hop":
            gia_tri[ten] = "1" if form_du_lieu.get(f"f__{ten}") == "1" else "0"
            ld = form_du_lieu.get(f"lydo__{c.truong}", "")
        else:
            v, mt = form_du_lieu.get(f"f__{ten}", ""), form_du_lieu.get(f"mt__{ten}", "")
            if mt and v.strip():
                loi.setdefault(ten, []).append("chọn MỘT trong hai: giá trị hoặc mã thiếu")
            gia_tri[ten] = mt or v
            ld = form_du_lieu.get(f"lydo__{ten}", "")
        if ld.strip():
            ly_do[ten] = ld
    return gia_tri, ly_do, loi


def tao_ung_dung(kho: M.Kho, *, host_hop_le: set[str] | None = None):
    """Ứng dụng Flask gắn MỘT kho. `host_hop_le`: tên Host được nhận (mặc định localhost/127.0.0.1 — `chay` đặt
    lại theo cổng thật)."""
    from flask import Flask, abort, redirect, render_template, request, session, url_for  # noqa: PLC0415
    from jinja2 import DictLoader  # noqa: PLC0415

    app = Flask(__name__)
    app.secret_key = secrets.token_bytes(32)
    app.jinja_loader = DictLoader(_MAU)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Strict", MAX_CONTENT_LENGTH=2_000_000,
                      HOST_HOP_LE=set(host_hop_le or {"localhost", "127.0.0.1"}))  # fmt: skip

    def phien() -> M.Phien | None:
        return M.Phien(session["ma"], session["vai"]) if session.get("ma") else None

    def bao(loai: str, nd: str) -> None:
        session.setdefault("tb", []).append((loai, nd))
        session.modified = True

    def ve(mau: str, ma: int = 200, **kw):
        tb = session.pop("tb", [])
        return render_template(mau, study=kho.kh.study, css=_CSS, phien=phien(), ten_vai=TEN_VAI,
                               csrf=session.get("csrf", ""), thong_bao=tb, quy_trach=M.QUY_TRACH,
                               can_kiem=M.CAN_KIEM, **kw), ma  # fmt: skip

    @app.before_request
    def _chan():
        if request.host not in app.config["HOST_HOP_LE"]:
            abort(400, "Host không hợp lệ — giao diện chỉ phục vụ 127.0.0.1")
        if "csrf" not in session:
            session["csrf"] = secrets.token_urlsafe(32)
        if request.method == "POST":
            gui = request.form.get("_csrf", "")
            if not gui or not secrets.compare_digest(gui, session["csrf"]):
                abort(400, "thiếu/sai mã chống giả mạo yêu cầu (CSRF) — tải lại trang")
        if session.get("ma"):
            if time.time() - float(session.get("luc", 0)) > HET_HAN_PHIEN:
                session.clear()
                session["csrf"] = secrets.token_urlsafe(32)
                bao("canh", "Phiên đã hết hạn sau 30 phút không thao tác — đăng nhập lại.")
                return redirect(url_for("dang_nhap"))
            session["luc"] = time.time()
        elif request.endpoint not in ("dang_nhap", "static"):
            return redirect(url_for("dang_nhap"))
        return None

    @app.after_request
    def _dau(resp):
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Cache-Control"] = "no-store"
        resp.headers["Content-Security-Policy"] = (
            "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; form-action 'self'; "
            "base-uri 'none'; frame-ancestors 'none'")
        return resp

    @app.errorhandler(M.TuChoi)
    def _tu_choi(e):
        return ve("loi.html", 403, loi=str(e))

    @app.route("/")
    def goc():
        return redirect(url_for("ds_phieu"))

    @app.route("/dang-nhap", methods=["GET", "POST"])
    def dang_nhap():
        if request.method == "POST":
            try:
                ph = kho.dang_nhap(request.form.get("ma", ""), request.form.get("pin") or None)
            except M.TuChoi as e:
                bao("loi", str(e))
                return ve("dang_nhap.html", 401)
            session.clear()
            session.update(ma=ph.ma, vai=ph.vai, luc=time.time(), csrf=secrets.token_urlsafe(32))
            return redirect(url_for("ds_phieu"))
        return ve("dang_nhap.html")

    @app.route("/dang-xuat", methods=["POST"])
    def dang_xuat():
        kho.dang_xuat(phien())
        session.clear()
        return redirect(url_for("dang_nhap"))

    @app.route("/phieu", methods=["GET", "POST"])
    def ds_phieu():
        ph = phien()
        if request.method == "POST":
            try:
                rid = kho.tao_phieu(ph, request.form.get("record_id", ""))
                return redirect(url_for("phieu", rid=rid))
            except M.TuChoi as e:
                bao("loi", str(e))
        return ve("ds_phieu.html", ds=kho.danh_sach_phieu(), la_ql=ph.vai == M.QLDL, lan=M.LAN_CUA_VAI.get(ph.vai))

    @app.route("/phieu/<rid>")
    def phieu(rid: str):
        ph = phien()
        p = next((x for x in kho.danh_sach_phieu() if x["record_id"] == rid), None)
        if p is None:
            raise M.TuChoi(f"không có phiếu «{rid}»")
        lan = M.LAN_CUA_VAI.get(ph.vai)
        da_luu: set[str] = set()
        if lan:
            with kho._doc() as cn:
                kho._kiem_luot(cn, ph, rid, lan, ghi=False)
                da_luu = kho._forms_da_luu(cn, rid, lan)
        chot = []
        if ph.vai == M.QLDL and p["da_doi_chieu"] and not p["lech_mo"]:
            chot = [(c, v) for c, v in kho.gia_tri_chot(ph, rid).items() if c != kho.kh.cid.ten]
        return ve("phieu.html", rid=rid, p=p, lan=lan, forms=kho.kh.forms, da_luu=da_luu, la_ql=ph.vai == M.QLDL,
                  chot=chot)  # fmt: skip

    @app.route("/phieu/<rid>/<lan>/<form>", methods=["GET", "POST"])
    def bieu_mau(rid: str, lan: str, form: str):
        ph = phien()
        chua_luu = False
        loi_web: dict[str, list[str]] = {}
        if request.method == "POST":
            gia_tri, ly_do, loi_web = doc_bieu_mau_gui(kho, request.form)
            if request.form.get("hanh_dong") == "luu" and not loi_web:
                kq = kho.luu_bieu_mau(ph, rid, lan, form, gia_tri, ly_do)
                if kq.luu:
                    bao("ok", f"Đã lưu biểu mẫu {form} ({kq.so_thay_doi} ô đổi).")
                    return redirect(url_for("bieu_mau", rid=rid, lan=lan, form=form))
            else:
                kq = kho.xem_bieu_mau(ph, rid, lan, form, gia_tri, ly_do)
                chua_luu = True
            for k, ds in loi_web.items():
                for x in ds:
                    M._them(kq.loi, k, x)
            if kq.co_loi():
                chua_luu = True
        else:
            ly_do = {}
            kq = kho.xem_bieu_mau(ph, rid, lan, form)
        return ve("bieu_mau.html", 200 if not kq.co_loi() else 422, rid=rid, lan=lan, form=form, chua_luu=chua_luu,
                  truong=truong_hien_thi(kho, kq, form, ly_do), loi_chung=kq.loi_chung,
                  canh_chung=kq.canh_bao_chung)  # fmt: skip

    @app.route("/phieu/<rid>/<lan>/hoan-tat", methods=["POST"])
    def hoan_tat(rid: str, lan: str):
        try:
            kho.hoan_tat_luot(phien(), rid, lan)
            bao("ok", f"Đã hoàn tất {lan} của phiếu {rid}.")
        except M.TuChoi as e:
            bao("loi", str(e))
        return redirect(url_for("phieu", rid=rid))

    @app.route("/doi-chieu/<rid>", methods=["GET", "POST"])
    def doi_chieu(rid: str):
        ph = phien()
        if ph.vai != M.QLDL:
            raise M.TuChoi("đối chiếu nhập kép chỉ dành cho quản lý dữ liệu")
        if request.method == "POST":
            try:
                if request.form.get("hanh_dong") == "doi_chieu":
                    kho.doi_chieu(ph, rid)
                else:
                    cot = request.form.get("cot", "")
                    lech = {x["cot"]: x for x in kho.trang_thai_doi_chieu(rid)["lech"]}.get(cot) or {}
                    chon = request.form.get("chon")
                    gt = {"lan1": lech.get("gia_tri_lan1", ""), "lan2": lech.get("gia_tri_lan2", "")}.get(
                        chon, request.form.get("gia_tri_khac", ""))
                    kho.giai_quyet_lech(ph, rid, cot, gt, request.form.get("ly_do", ""),
                                        request.form.get("tham_chieu", ""))  # fmt: skip
                    bao("ok", f"Đã giải quyết ô {cot}.")
            except M.TuChoi as e:
                bao("loi", str(e))
            return redirect(url_for("doi_chieu", rid=rid))
        return ve("doi_chieu.html", rid=rid, tt=kho.trang_thai_doi_chieu(rid))

    @app.route("/phieu/<rid>/sua-chot", methods=["POST"])
    def sua_chot(rid: str):
        try:
            kho.sua_chot(phien(), rid, request.form.get("cot", ""), request.form.get("gia_tri", ""),
                         request.form.get("ly_do", ""), request.form.get("tham_chieu", ""))  # fmt: skip
            bao("ok", "Đã sửa bản chốt.")
        except M.TuChoi as e:
            bao("loi", str(e))
        return redirect(url_for("phieu", rid=rid))

    @app.route("/phieu/<rid>/khoa", methods=["POST"])
    def khoa(rid: str):
        try:
            if request.form.get("hanh_dong") == "mo":
                kho.mo_khoa_phieu(phien(), rid, request.form.get("ly_do", ""))
                bao("ok", "Đã mở khoá.")
            else:
                kho.khoa_phieu(phien(), rid)
                bao("ok", "Đã khoá phiếu.")
        except M.TuChoi as e:
            bao("loi", str(e))
        return redirect(url_for("phieu", rid=rid))

    @app.route("/phieu/<rid>/nham-ma", methods=["POST"])
    def nham_ma(rid: str):
        try:
            kho.danh_dau_nham(phien(), rid, request.form.get("ly_do", ""), nham=request.form.get("nham") == "1")
        except M.TuChoi as e:
            bao("loi", str(e))
        return redirect(url_for("phieu", rid=rid))

    @app.route("/truy-van")
    def ds_truy_van():
        ph = phien()
        rid = request.args.get("rid") or None
        return ve("truy_van.html", ds=kho.danh_sach_truy_van(rid), la_ql=ph.vai == M.QLDL)

    @app.route("/truy-van/quet", methods=["POST"])
    def quet_truy_van():
        try:
            kq = kho.quet_truy_van(phien())
            bao("ok", f"Đã quét: {kq['tao']} truy vấn mới, {kq['dong']} truy vấn tự đóng.")
        except M.TuChoi as e:
            bao("loi", str(e))
        return redirect(url_for("ds_truy_van"))

    @app.route("/truy-van/tao", methods=["POST"])
    def tao_truy_van():
        try:
            kho.tao_truy_van(phien(), request.form.get("record_id", ""), request.form.get("cot", ""),
                             request.form.get("noi_dung", ""))  # fmt: skip
            bao("ok", "Đã tạo truy vấn.")
        except M.TuChoi as e:
            bao("loi", str(e))
        return redirect(url_for("ds_truy_van"))

    @app.route("/truy-van/<int:qid>/tra-loi", methods=["POST"])
    def tra_loi(qid: int):
        try:
            kho.tra_loi_truy_van(phien(), qid, request.form.get("noi_dung", ""))
        except M.TuChoi as e:
            bao("loi", str(e))
        return redirect(url_for("ds_truy_van"))

    @app.route("/truy-van/<int:qid>/dong", methods=["POST"])
    def dong(qid: int):
        try:
            kho.dong_truy_van(phien(), qid, request.form.get("ly_do", ""))
        except M.TuChoi as e:
            bao("loi", str(e))
        return redirect(url_for("ds_truy_van"))

    @app.route("/nguoi", methods=["GET", "POST"])
    def nguoi():
        ph = phien()
        if ph.vai != M.QLDL:
            raise M.TuChoi("khai người nhập chỉ dành cho quản lý dữ liệu")
        if request.method == "POST":
            try:
                kho.them_nguoi(ph, request.form.get("ma", ""), request.form.get("vai", ""),
                               request.form.get("pin") or None)  # fmt: skip
                bao("ok", "Đã khai người nhập.")
            except M.TuChoi as e:
                bao("loi", str(e))
            return redirect(url_for("nguoi"))
        return ve("nguoi.html", ds=kho.danh_sach_nguoi())

    @app.route("/xuat", methods=["GET", "POST"])
    def xuat():
        ph = phien()
        if ph.vai != M.QLDL:
            raise M.TuChoi("xuất dữ liệu chỉ dành cho quản lý dữ liệu")
        kq = None
        ra = str(kho.thu_muc / "xuat")
        if request.method == "POST":
            ra = request.form.get("ra", "").strip() or ra
            try:
                kq = kho.xuat(ph, Path(ra), ban_nhap=request.form.get("ban_nhap") == "1",
                              tiep_nhan=request.form.get("tiep_nhan") == "1")  # fmt: skip
            except M.TuChoi as e:
                bao("loi", str(e))
        return ve("xuat.html", kq=kq, ra=ra)

    @app.route("/kiem-nhat-ky")
    def kiem_nhat_ky():
        if phien().vai != M.QLDL:
            raise M.TuChoi("kiểm nhật ký chỉ dành cho quản lý dữ liệu")
        return ve("kiem.html", kt=kho.kiem_nhat_ky())

    return app


def tao_may_chu(kho: M.Kho, cong: int = 0):
    """(máy chủ, ứng dụng, địa chỉ) — LUÔN bind 127.0.0.1; cổng 0 = hệ điều hành chọn cổng trống."""
    from werkzeug.serving import make_server  # noqa: PLC0415

    app = tao_ung_dung(kho)
    srv = make_server(MAY_CHU, int(cong), app, threaded=False)
    thuc = srv.server_port
    app.config["HOST_HOP_LE"] = {f"{MAY_CHU}:{thuc}", f"localhost:{thuc}"}
    return srv, app, f"http://{MAY_CHU}:{thuc}/"


def chay(kho: M.Kho, *, cong: int = 0, mo_trinh_duyet: bool = True) -> int:
    srv, _app, url = tao_may_chu(kho, cong)
    print(f"✓ Hệ nhập liệu cục bộ đang chạy: {url}  (chỉ máy này truy cập được — Ctrl+C để dừng)")
    print("   " + M.QUY_TRACH)
    if mo_trinh_duyet:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("Đã dừng.")
    finally:
        srv.server_close()
    return M.MA_OK


__all__ = ["tao_ung_dung", "tao_may_chu", "chay", "truong_hien_thi", "doc_bieu_mau_gui"]
