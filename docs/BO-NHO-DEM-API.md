# Bộ nhớ đệm câu lệnh (prompt caching) của Claude API

Bác sĩ giao ngày 21/11/2026: «cài lưu bộ nhớ đệm câu lệnh giúp tôi» → «giải quyết một cách tốt nhất». Công cụ:
`tools/api_claude_nc.py` (cầu nối chung) · `tools/do_cache_api.py` (đo hiệu quả) · `runtime/claude_api_runtime.py`
(runtime agent).

> **Không có công tắc nào trong Claude Console.** Caching bật bằng **tham số trong từng request** API. Trang
> «Phân tích bộ nhớ đệm» của Console chỉ để XEM số liệu, không để bật. Thẻ «Chẩn đoán bộ nhớ đệm» trên trang đó cũng
> không có công tắc — chẩn đoán cũng bật bằng tham số request (xem §5).

> **Không đổi đầu ra của model.** Caching chỉ thay cách tính phí phần token VÀO. Câu trả lời y như khi không cache,
> nên bật/tắt không cần thẩm định lại chất lượng lâm sàng.

---

## 1. Luật nền: cache chỉ lợi khi token ĐÃ SẼ được gửi lại

Đây là điều quan trọng nhất của cả tệp này, và là chỗ dễ sai nhất.

Tính theo hệ số so với giá token vào:

| Việc | Hệ số | Hằng số trong mã |
|---|---|---|
| Gửi thẳng (không cache) | 1,00× | — |
| Ghi cache TTL 5 phút | 1,25× | `HE_SO_GHI_CACHE` |
| Ghi cache TTL 1 giờ | 2,00× | `HE_SO_GHI_CACHE_1H` |
| Đọc từ cache (Sonnet 5.5 · Opus 5.5) | 0,05× | `he_so_doc_cache()` |
| Đọc từ cache (Fable 5.1 · 5.2) | 0,025× | `he_so_doc_cache()` |
| Đọc từ cache (model khác) | ~0,1× | `he_so_doc_cache()` |

Từ đó: **TTL 5 phút hoà vốn ngay từ lần tái dùng ĐẦU TIÊN** (1,25 + 0,05 = 1,30 < 2,00), **TTL 1 giờ từ lần thứ
hai**. Hàm `nen_cache(so_lan_tai_dung, ttl, model)` mã hoá đúng luật này.

### Cạm bẫy: đừng phình prefix ra cho «cache được»

Đọc lại `n` lần tốn `n × 0,05`. Với `n = 33` thì đã là **1,65×**, vượt 1,00× của việc chỉ gửi mỗi thứ đúng một lần.
Nên **dồn nội dung dùng-một-lần vào một prefix chung luôn ĐẮT HƠN**.

Đo thật trên `kiem_noi_dung_trich_dan` (21/11/2026), 34 lô × 6 tài liệu × 1.000 token:

| Số tài liệu duy nhất | Gửi thẳng | Dồn corpus vào prefix cache | Kết |
|---|---|---|---|
| 40 | 204.000 | 116.000 | lợi 0,57× |
| 60 | 204.000 | 174.000 | lợi 0,85× |
| 100 | 204.000 | 290.000 | **lỗ 1,42×** |
| 204 | 204.000 | 591.600 | **lỗ 2,90×** |

⇒ Đếm số lần tái dùng của prefix **HIỆN CÓ**; đừng thiết kế prefix mới để thoả `nen_cache`.
Chốt bằng test: `tests/test_cache_nguong_va_ttl_20261121.py::test_nen_cache_khong_bien_minh_viec_phinh_prefix`.

---

## 2. Ngưỡng tối thiểu — lỗi IM LẶNG

Prefix **dưới ngưỡng** của model thì API **không cache và không tính phí ghi** — *không có lỗi trả về*. Chỗ duy nhất
thấy được là `usage.cache_creation_input_tokens == 0`. Bảng ngưỡng: `NGUONG_CACHE_TOKEN`.

| Ngưỡng | Model |
|---|---|
| 512 | Sonnet 5.5 · Opus 5.5 · Opus 5 · Haiku 5.5 · Fable 5 / 5.1 / 5.2 |
| 1.024 | Sonnet 5 · Opus 4.8 · Sonnet 4.6 |
| 2.048 | Opus 4.7 |
| 4.096 | Opus 4.6 · **Haiku 4.5** |

Hai hệ quả đã đo trong hệ này:

- `HE_THONG` của `kiem_noi_dung_trich_dan` = **591 token**, chỉ hơn ngưỡng 512 có **79 token**. Rất mong manh:
  sửa mất ~12 ký tự là rơi xuống dưới và âm thầm mất cache. Test canh có dự phòng 15% sẽ ĐỎ ngay khi điều đó xảy ra
  (`test_prompt_duoc_cache_phai_vuot_nguong_co_du_phong`). **Gặp test đó đỏ thì xem lại bản sửa prompt hoặc bỏ
  `cache_he_thong=True`, KHÔNG hạ `DU_PHONG` để test xanh lại.**
- `_DEFAULT_MODEL` của `runtime/claude_api_runtime.py` là Haiku 4.5, ngưỡng **4.096** ⇒ chỉ **61/99** agent spec
  in-repo được cache. Đó là mất cơ hội tiết kiệm, **không phải lỗi** và không phát sinh phí. Đổi sang Haiku 5.5 /
  Sonnet 5.5 (ngưỡng 512) thì cả 99 spec đều cache được — là quyết định của bác sĩ, không thuộc phạm vi lượt này.

---

## 3. Chỗ nào đang cache, chỗ nào CỐ Ý không

| Nơi gọi | Cache? | Vì sao |
|---|---|---|
| `runtime/claude_api_runtime.py` | ✅ system prompt | Agent spec tĩnh theo `agent_id`, trung bình ~5.300 token, dùng lại cho nhiều fixture |
| `tools/hoi_dong_cong_batch.py` | ✅ `cache_he_thong=True` | Cùng tệp agent cho nhiều đầu ra |
| `tools/kiem_tong_quan_g0_api.py` | ✅ | Cùng lời dặn nhiều lượt |
| `tools/kiem_noi_dung_trich_dan.py` | ✅ system (591 token) | Cùng lời dặn cho mọi lô — nhưng xem §2 về mức mong manh |
| `tools/phan_bien_may_de_cuong.py` | ❌ **cố ý** | MỘT lượt mỗi lần chạy ⇒ ghi cache 1,25× mà không ai đọc lại. Chốt: `test_phan_bien_mot_luot_khong_danh_dau_cache` |
| `app/integrations/` (SOAP, đọc ảnh) | ❌ **không thể** | `build_soap_prompt` phần tĩnh = **256 token**, `build_reading_prompt` = **283 token** — đều dưới ngưỡng 512. Dời sang `system` cũng không cache được; nhồi chữ cho đủ ngưỡng thì **không được phép** với prompt an toàn lâm sàng |

---

## 4. Dùng trong mã

```python
# TTL 5 phút (mặc định) — nhịp gọi dày, mỗi lần đọc làm mới miễn phí
kq = API.goi(noi_dung, he_thong=HE_THONG, cache_he_thong=True, nguon="ten_cong_cu")

# TTL 1 giờ — CHỈ khi các lượt cách nhau HƠN 5 phút mà vẫn trong vòng một giờ
kq = API.goi(noi_dung, he_thong=HE_THONG, cache_he_thong=True, cache_ttl="1h", nguon="ten_cong_cu")

# Kiểm trước khi quyết định bật
if API.nen_cache(so_lan_tai_dung=so_lo - 1, model=model):
    ...
```

`KetQuaGoi` trả về: `token_cache_ghi` (TỔNG token ghi) · `token_cache_ghi_1h` (phần TTL 1h, tính 2×) ·
`token_cache_doc` · `ly_do_truot_cache` · `token_truot_cache`.

Sổ chi phí `~/.ebm-api-claude-chi-phi.json` ghi `cache_ghi` · `cache_doc`, và chỉ thêm `cache_ghi_1h` /
`truot_cache` **khi khác 0 / khi có lý do** — giữ nguyên khuôn sổ cũ cho các lượt 5m thông thường.

> **Vì sao phải tách TTL khi tính tiền:** gộp một hệ số thì lượt TTL 1h bị ghi **THIẾU** tiền vào sổ ⇒ trần chi tiêu
> tháng canh sai (fail-open về tiền). Tách theo `usage.cache_creation.ephemeral_1h_input_tokens`, áp dụng cho cả
> đường gọi trực tiếp và đường Batch.

---

## 5. Chẩn đoán: vì sao trượt cache

`usage` chỉ cho biết **đã** trượt, không cho biết **tại sao**. Chẩn đoán cache so prefix của hai lượt liên tiếp và
chỉ ra chỗ lệch ĐẦU TIÊN.

```bash
EBM_API_CLAUDE_CHAN_DOAN_CACHE=1 python3 tools/kiem_noi_dung_trich_dan.py --goi-api …
```

Mặc định **TẮT**, để không đổi khuôn request của các lượt đã chạy thật. Khi bật:

- chuỗi so sánh nối **theo từng `nguon`** — trộn các công cụ thì lúc nào cũng ra «đổi hết» và chẩn đoán thành vô
  nghĩa;
- chỉ đi đường beta (model trong `MODEL_HIEN_HANH`); model cũ không nhận tham số này;
- **best-effort**: SDK chưa biết `diagnostics` ⇒ tự gọi lại KHÔNG chẩn đoán, lượt vẫn thành công, và tắt chẩn đoán
  cho phần còn lại của tiến trình;
- `cache_miss_reason: null` nghĩa là so sánh **CHƯA xong** (vô định) — **không** được đọc thành «prefix đã khớp».

Các loại lý do: `model_changed` · `system_changed` · `tools_changed` · `messages_changed` ·
`previous_message_not_found` (không có dấu vân cho id đó — *không* nghĩa là request đã đổi) · `unavailable`.

> **Riêng tư / PII:** tính năng này **không lưu chữ** của prompt hay câu trả lời. Máy chủ chỉ giữ một **dấu vân**
> (hash mật mã + ước số token) theo id response, phạm vi trong tổ chức và workspace, hết hạn sau thời gian ngắn.
> Vì vậy bật được mà **không đụng luật PII** của hệ.

---

## 6. Đo hiệu quả theo TỪNG công cụ

Trang Console chỉ cho số **tổng theo model**, mà hệ này có 6 công cụ cùng gọi Sonnet 5.5 — nên tổng đó không chỉ ra
công cụ nào gây trượt. Sổ chi phí đã ghi `nguon` + token theo từng lượt, nên bóc được ngay, **không gọi mạng, không
tốn tiền, không sửa sổ**:

```bash
python3 tools/do_cache_api.py            # bảng theo từng công cụ
python3 tools/do_cache_api.py --json     # JSON để nạp dashboard
python3 tools/do_cache_api.py --so <đường dẫn sổ khác>
```

Phải chạy **trên MÁY đã gọi API** (Mac/Windows của bác sĩ) — phiên Cloud không có sổ.

Năm nhãn và cách xử lý:

| Nhãn | Nghĩa | Làm gì |
|---|---|---|
| **ĐÃ TỐT** | ≥ 60% token vào đến từ cache | Để yên |
| **CẦN XEM LẠI** | Cache chạy (khấu hao > 1×) nhưng tỷ lệ đọc thấp | Kiểm xem phần đầu vào mới đó **CÓ THẬT** bị gửi lặp lại không. Nếu không → tỷ lệ thấp là ĐÚNG, **đừng ép cache** |
| **ĐANG LỖ VÌ CACHE** | Khấu hao ghi < 1× | Bỏ `cache_he_thong=True` ở nguồn đó |
| **CHƯA BẬT CACHE** | Không có token cache nào | Chỉ đáng bật nếu prefix tĩnh vượt ngưỡng §2 |
| **CHƯA ĐỦ DỮ LIỆU** | < 50.000 token vào | Chưa kết luận |

Mốc đo đầu (Console, 7 ngày tới 20/11/2026, trước khi vá): Sonnet 5.5 **13 Tr token vào · 12,7% đọc · 3,70× khấu
hao**; Opus 5.5 **464 N · 99,2% · 16,0×**. Tổng 13,4 Tr · 15,6% · 4,43×.

---

## 7. Kỳ vọng thực tế

Sau khi bật, **tỷ lệ đọc cache của Sonnet 5.5 có thể không nhảy lên nhiều** — và đó không phải thất bại. Phần lớn
khối 13 Tr token đến từ `kiem_noi_dung_trich_dan`, mà nội dung là **abstract khác nhau, mỗi cái gửi đúng một lần**.
Không có cache nào tiết kiệm cho nội dung chỉ gửi một lần (xem §1).

Đòn tiết kiệm **lớn hơn cache** cho đường đó là **Batch API: giảm 50% mọi khoản, cộng dồn với cache**. Hạ tầng batch
đã có (`API.nop_batch`, `tools/hoi_dong_cong_batch.py`), nhưng chuyển `kiem_noi_dung_trich_dan` sang batch là đổi
sang **bất đồng bộ** — thay đổi kiến trúc, cần bác sĩ duyệt riêng, chưa làm.

---

## 8. Tắt nhanh

| Biến môi trường | Tác dụng |
|---|---|
| `EBM_RUNTIME_TAT_CACHE_SYSTEM=1` | Tắt cache system prompt của `ClaudeApiRuntime` (giá trị lạ ⇒ vẫn BẬT, mặc định an toàn về chi phí) |
| `EBM_API_CLAUDE_CHAN_DOAN_CACHE=1` | **Bật** chẩn đoán (mặc định tắt) |

---

## 9. Test canh

`tests/test_cache_nguong_va_ttl_20261121.py` — 46 test, chia 7 nhóm: ngưỡng tối thiểu · TTL · giá ghi theo TTL ·
runtime · luật hoà vốn `nen_cache` · chẩn đoán · công cụ đo. Hai test đáng chú ý:

- `test_prompt_duoc_cache_phai_vuot_nguong_co_du_phong` — tripwire chống lỗi im lặng ở §2;
- `test_nen_cache_khong_bien_minh_viec_phinh_prefix` — chốt bằng số cạm bẫy ở §1.

Cần bác sĩ kiểm chứng.
