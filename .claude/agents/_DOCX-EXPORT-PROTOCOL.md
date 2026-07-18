# GIAO THỨC XUẤT WORD (.docx) — CHUẨN HÓA ĐẦU RA NGHIÊN CỨU Y KHOA

> **File hạ tầng `_*`** (không phải agent). Tạo 2026-06-29.
> Áp dụng cho: `dieu-phoi-nghien-cuu` và tất cả agent con.
> Mục đích: mọi cổng G đều sinh ra file .docx chuẩn hóa, tự động, không cần bác sĩ yêu cầu lại.

---

## §1. NGUYÊN TẮC CỨNG

1. **MẶC ĐỊNH**: sau mỗi cổng G hoàn thành → tự xuất .docx (không chờ bác sĩ yêu cầu).
2. **KHÔNG bịa nội dung**: placeholder `[CẦN BỔ SUNG]` thay vì số liệu giả.
3. **KHÔNG PII**: KHÔNG lẫn định danh bệnh nhân vào bất kỳ file nào.
4. **Disclaimer bắt buộc**: mọi file kết thúc bằng *"Cần bác sĩ kiểm chứng."*
5. **Font/Margin chuẩn**: Times New Roman 13pt · lề T2.5/B2.5/L3/R2 cm.
6. **Thư mục lưu**: `medical-ebm-automation/exports/<TEN-DE-TAI>/`.
7. **Naming convention**: `<code>_<artifact-key-upper>_<TEN-DE-TAI>.docx`

---

## §2. MAPPING CỔNG → LỆNH XUẤT WORD

Chạy từ thư mục `medical-ebm-automation/`:

| Cổng | Lệnh chuẩn | File .docx sinh ra |
|------|-----------|-------------------|
| **G0** | `python tools/gen_research_docx.py --study "<TEN>" --gate G0` | G0a_INTAKE · G0b_PICO · G0c_LITERATURE |
| **G1** | `python tools/gen_research_docx.py --study "<TEN>" --gate G1` | G1a_PROTOCOL · G1b_CHARTER · G1c_PLAN · G1d_RISK |
| **G2 🔒** | `python tools/gen_research_docx.py --study "<TEN>" --artifact ethics` | G2_ETHICS |
| **G3** | `python tools/gen_research_docx.py --study "<TEN>" --gate G3` | G3a_SAMPLESIZE · G3b_VARIABLES · G3c_CRF · G3d_INSTRUMENT |
| **G4 🔒** | `python tools/gen_research_docx.py --study "<TEN>" --artifact sap` | G4_SAP |
| **G5** | `python tools/gen_research_docx.py --study "<TEN>" --gate G5` | G5a_SOP · G5b_DMP · G5c_DATALOCK |
| **G6** | `python tools/gen_research_docx.py --study "<TEN>" --gate G6` | G6a_ANALYSIS · G6b_INTERPRETATION |
| **G7** | `python tools/gen_research_docx.py --study "<TEN>" --gate G7` | G7a_MANUSCRIPT · G7b_CHECKLIST · **+ G1d_RISK bị sinh lại (2026-07-12: xác nhận bằng cách chạy mô phỏng `generate_all_gates()` thật — artifact `risk` có gate="G1+G7", hàm khớp gate bằng substring "G7" in "G1+G7" nên bị lặp; đây là hành vi thật của code, không phải lỗi tài liệu — đừng ngạc nhiên khi thấy Risk Register bị ghi đè ở G7)** |
| **G8** | `python tools/gen_research_docx.py --study "<TEN>" --artifact review` | G8_REVIEW |
| **G9 🔒** | `python tools/gen_research_docx.py --study "<TEN>" --artifact readiness` | G9_READINESS |
| **Tất cả** | `python tools/gen_research_docx.py --study "<TEN>" --all` | **22** file docx toàn đề tài (2026-07-12: sửa "20" — `len(ARTIFACT_MAP)` thật = 22, xác nhận bằng import module thật + đếm bảng §5 dưới đây) |

**Scaffold toàn đề tài** (tạo lần đầu):
```bash
python tools/scaffold_research_project.py --study "<TEN-DE-TAI>"
```
**2026-07-12: sửa "20 file .md + 20 file .docx"** — kiểm `SCAFFOLD_FILES` thật: 21 dòng nhưng chỉ **18 key duy nhất** (3 khóa bị khai trùng: `literature`/`sap`/`checklist` mỗi khóa 2 lần), và **THIẾU hẳn 4 artifact hợp lệ** so với `ARTIFACT_MAP` (`instrument`, `review`, `plan`, `interpretation`) — scaffold thật sinh **18 cặp .md/.docx**, không phải 20, và không đủ 22 như `--all` của `gen_research_docx.py`.

---

## §3. TRUYỀN NỘI DUNG (--content)

Để file .docx chứa nội dung thật (không chỉ placeholder), truyền JSON content:

```bash
python tools/gen_research_docx.py \
  --study "PCOS-MET-2026" \
  --artifact pico \
  --content '{"pico": {"P": "Phụ nữ PCOS 18–45 tuổi ngoại trú", "I": "Metformin 1500mg/ngày", "C": "Giả dược", "O_primary": "Nồng độ testosterone tổng", "T": "6 tháng", "S": "Khoa Nội tiết BV Quân y 175"}}'
```

Hoặc dùng file JSON:
```bash
python tools/gen_research_docx.py --study "PCOS-MET-2026" --artifact pico --content content_g0.json
```

---

## §4. QUY TRÌNH AGENT (thực thi trong claude-code / phiên có Bash tool)

Sau mỗi cổng G hoàn thành, agent `dieu-phoi-nghien-cuu` thực hiện THEO THỨ TỰ:

```
BƯỚC A (completeness-critic): đối chiếu A1–A18
BƯỚC B (sổ cái): giao so-cai-ghi-nho ghi PASS + ngày
BƯỚC C (XUẤT WORD — MẶC ĐỊNH):
  Bash: cd medical-ebm-automation && python tools/gen_research_docx.py \
        --study "<TEN>" --gate G<n>
  Thông báo: đường dẫn file .docx cho bác sĩ
BƯỚC D (thẩm định đầu ra): gọi tham-dinh-dau-ra
BƯỚC E (bàn giao): nêu cổng kế tiếp + cần bác sĩ cấp gì
```

---

## §5. DANH SÁCH 22 ARTIFACT KEY (dùng với --artifact — 2026-07-12: sửa "20", đếm thật khớp bảng dưới)

| Key | Code | Cổng | Tên |
|-----|------|------|-----|
| `intake` | G0a | G0 | Research Intake & Feasibility Audit |
| `pico` | G0b | G0 | Câu hỏi nghiên cứu — PICO/PECO/FINER |
| `literature` | G0c | G0-G1 | Tổng quan y văn & Evidence Ledger |
| `protocol` | G1a | G1 | Đề cương & Thiết kế nghiên cứu |
| `charter` | G1b | G1 | Project Charter |
| `plan` | G1c | G1 | Kế hoạch triển khai |
| `risk` | G1d | G1+G7 | Risk Register sống |
| `ethics` | G2 | G2🔒 | Hồ sơ đạo đức (IRB) + ICF |
| `samplesize` | G3a | G3 | Tính cỡ mẫu & Power |
| `variables` | G3b | G3 | Biến số & Data Dictionary |
| `crf` | G3c | G3 | Công cụ thu thập (CRF) |
| `instrument` | G3d | G3 | Kiểm định công cụ đo lường |
| `sap` | G4 | G4🔒 | SAP + Dummy Tables |
| `sop` | G5a | G5 | SOP Thu thập số liệu |
| `dmp` | G5b | G5 | Kế hoạch quản lý dữ liệu |
| `datalock` | G5c | G5-G6 | Biên bản khóa dữ liệu |
| `analysis` | G6a | G6 | Kết quả phân tích thống kê |
| `interpretation` | G6b | G6-G7 | Diễn giải kết quả |
| `manuscript` | G7a | G7 | Bản thảo khoa học (IMRAD) |
| `checklist` | G7b | G7 | Checklist chuẩn báo cáo |
| `review` | G8 | G8 | Bình duyệt nội bộ |
| `readiness` | G9 | G9🔒 | Báo cáo sẵn sàng nghiệm thu |

---

## §6. CÁC BẤT BIẾN LIÊM CHÍNH (không vi phạm khi xuất Word)

- KHÔNG tự điền số phê duyệt IRB / mã đăng ký nghiên cứu giả
- KHÔNG bịa effect size / cỡ mẫu nếu không có nguồn (PMID/DOI)
- KHÔNG tự gán GRADE / độ mạnh khuyến cáo
- KHÔNG ghi SUBMITTED_EXTERNALLY hoặc APPROVED_EXTERNALLY khi chưa có xác nhận thật
- File .docx chỉ soạn thảo hỗ trợ — BÁC SĨ phải duyệt trước khi dùng chính thức
- Mọi placeholder `[CẦN BỔ SUNG]` là tín hiệu để bác sĩ điền — KHÔNG bỏ hoặc thay bằng nội dung giả

---

**Cần bác sĩ kiểm chứng.**
