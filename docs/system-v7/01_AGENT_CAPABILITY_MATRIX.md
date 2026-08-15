# 01 - Agent Capability Matrix

## Nhạc trưởng

| Nhóm | Agent | Nhiệm vụ | Cổng bắt buộc |
|---|---|---|---|
| Lâm sàng | `dieu-phoi-lam-sang` | 5 bước EBM, cờ đỏ, áp dụng có bác sĩ duyệt | Cổng A, Cổng B, `tham-dinh-dau-ra` |
| Nghiên cứu | `dieu-phoi-nghien-cuu` | G0-G9, thiết kế, đạo đức, SAP, báo cáo | G2, G4, liêm chính tác giả |
| Guardrail | `tham-dinh-dau-ra` | Soi liêm chính và chất lượng Med-PaLM 2 | R1-R7, Q1-Q7 |

## V7 capability mapping

| Năng lực | Module V7 | Tình trạng |
|---|---|---|
| Run packet thống nhất | `app/core/run_packet.py` | Đã có |
| State machine | `app/core/run_state_machine.py` | Đã có |
| Policy engine | `app/core/policy_engine.py` | Đã có |
| Approval center | `app/core/approval_service.py` | Đã có |
| Audit logger khử PII | `app/core/audit_logger.py` | Đã có |
| Evidence registry | `app/evidence/evidence_registry.py` | Đã có |
| Claim registry | `app/evidence/claim_registry.py` | Đã có |
| Safety kernel | `app/safety/*` | Đã có |
| ResearchOS gates | `app/research_os/*` | Đã có |
| ChatGPT bridge | `app/export_bridge/chatgpt_project_bridge.py` | Đã có |
| Dashboard V7 sections | `app/dashboard/v7_registry.py` | Đã có |

## Nguyên tắc dùng chung

- Agent chỉ đề xuất, không tự áp dụng.
- Output lâm sàng phải có nguồn truy nguyên hoặc nhãn cần xác minh.
- Không lưu PII.
- Mọi phát hành lâm sàng cần bác sĩ duyệt.
