# TỰ SINH AGENT — cơ chế mở rộng đội agent khi thiếu năng lực (an toàn, có duyệt)

> Tài sản hạ tầng `_*` — KHÔNG tính vào bộ đếm agent. Tạo 2026-07-04.
> Mục đích: khi một đề tài/ca cần một **năng lực chuyên biệt CHƯA có** trong đội
> agent hiện tại, hệ **tự soạn + đăng ký một agent mới ĐÚNG CHUẨN NHÀ** thay vì
> bế tắc — nhưng agent mới là **ĐỀ XUẤT** (bác sĩ duyệt mới chính thức), giữ
> nguyên bất biến "chỉ đề xuất, người duyệt mới áp dụng".
> Đồng bộ: `_BAN-DO-KET-NOI.md`, `_TU-CHINH-SUA-PROTOCOL.md`, `_VONG-LAP-KHEP-KIN.md`,
> `dieu-phoi-nghien-cuu.md`, `README.md`. Công cụ: `tools/generate_agent.py`.

---

## 1. TRIẾT LÝ — tách VAI để an toàn theo cấu trúc

| Vai | Ai làm | Trách nhiệm |
|---|---|---|
| **Phát hiện khoảng trống** | Bộ điều phối (LLM: `dieu-phoi-nghien-cuu`/`dieu-phoi-lam-sang`) | Nhận ra "việc này KHÔNG agent nào đang có phụ trách đúng" |
| **Soạn SPEC** | Bộ điều phối | Viết đặc tả giàu: vai · trigger · phương pháp · ranh giới · cổng · nguồn bắt buộc |
| **Dựng + cấy guardrail + đăng ký** | `tools/generate_agent.py` (xác định, KHÔNG LLM) | Bảo đảm agent mới ĐÚNG KHUNG: luật nền · self-check · disclaimer · cổng guardrail · sync Codex · registry |
| **Duyệt** | **BÁC SĨ** | Rà nội dung/nguồn, xoá nhãn `[TỰ SINH — CHỜ BÁC SĨ DUYỆT]` → chính thức |

Nhờ tách vai này, **agent tự sinh AN TOÀN THEO CẤU TRÚC**: bất kể nội dung chuyên
môn, nó luôn thừa hưởng toàn bộ rào chắn liêm chính (cấy tự động bởi
`enforce_agent_guardrails.py`), và KHÔNG được coi là "đã tin cậy" cho tới khi bác sĩ duyệt.

## 2. KHI NÀO sinh agent (gate phát hiện khoảng trống)

Chỉ sinh khi HỘI ĐỦ (tránh phình đội vô ích):
1. Việc thuộc phạm vi hệ (nghiên cứu/lâm sàng y khoa EBM), VÀ
2. **KHÔNG** agent nào trong đội hiện tại phụ trách đúng (rà `README.md` + `_BAN-DO-KET-NOI.md` trước), VÀ
3. Năng lực đó **lặp lại/đủ tổng quát** để đáng có agent riêng (việc lẻ 1 lần → làm trực tiếp, đừng sinh), VÀ
4. Có thể mô tả được PHƯƠNG PHÁP + NGUỒN chuẩn (nếu phải bịa phương pháp → DỪNG, hỏi bác sĩ).

Nếu 1 trong 4 không thỏa → **KHÔNG sinh**; hoặc dùng agent gần nhất + nêu giới hạn, hoặc hỏi bác sĩ.

## 3. CÁCH sinh (tốt nhất) — SPEC → generate_agent.py → duyệt

Bộ điều phối soạn SPEC JSON (giàu, có nguồn), rồi:
```bash
python tools/generate_agent.py --spec spec.json --register
# --register: tự chạy enforce → sync Codex → --check → audit
# (kiểm khô trước khi ghi: thêm --dry-run)
```
`generate_agent.py` tự: kiểm slug/không trùng → dựng `.claude/agents/<slug>.md` đúng
khung (Luật nền · Khi nào kích hoạt · Phương pháp · Ranh giới · Tiêu chí · Self-check) →
gắn nhãn `[TỰ SINH — CHỜ BÁC SĨ DUYỆT]` → ghi `_TU-SINH-AGENT-REGISTRY.json` → (nếu
`--register`) cấy guardrail + đồng bộ Codex + audit.

**Chất lượng "tốt nhất":** nếu môi trường cho phép nhiều lượt, bộ điều phối nên
soạn SPEC theo lối **đối kháng đa lăng kính** — nháp vai/phương pháp, tự phản biện
"agent này có chồng lấn/để lọt gì?", rồi chốt SPEC tốt nhất trước khi gọi tool.

## 4. CỔNG DUYỆT (bất biến liêm chính)

- Agent tự sinh = **PROPOSED** trong registry; đầu ra của nó coi như **[DỰ THẢO]** cho
  tới khi bác sĩ xoá dòng `[TỰ SINH — CHỜ BÁC SĨ DUYỆT]`.
- **KHÔNG** dùng agent tự sinh để vượt cổng cứng (G2 đạo đức · G4 SAP · liêm chính
  tác giả · Cổng A/B lâm sàng). Nó chỉ ĐỀ XUẤT như mọi agent khác.
- Audit hệ (`audit_ebm_system.py`) đã **nhận biết registry**: agent tự sinh đã đăng ký
  được phép vượt baseline 48; agent thêm/bớt **chui** (không qua registry) vẫn bị tripwire bắt.

## 5. VÒNG ĐỜI + DỌN DẸP

- Bác sĩ duyệt → xoá nhãn cảnh báo, (tuỳ chọn) chuyển entry registry sang `status: APPROVED`.
- Không cần nữa → xoá file `.md` + entry registry + chạy lại sync; audit tự khớp số mới.
- Registry `_TU-SINH-AGENT-REGISTRY.json` là **nguồn sự thật** về agent tự sinh (đừng sửa tay lung tung).

## 6. VỊ TRÍ TRONG VÒNG LẶP KHÉP KÍN

`dieu-phoi-nghien-cuu` khi march G0→G10: nếu một cổng cần năng lực thiếu → (gate §2) →
sinh agent (§3) → dùng ngay trong lượt → ghi sổ cái + registry → bác sĩ duyệt sau. Xem
`_VONG-LAP-KHEP-KIN.md` §"Tự sinh agent" cho sơ đồ đầy đủ.

**Cần bác sĩ kiểm chứng.**
