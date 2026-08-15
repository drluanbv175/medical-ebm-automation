# Clinical Knowledge Pack Standard

Một Clinical Knowledge Pack V7 tối thiểu gồm:

- `pack_id`
- `topic`
- `version`
- `scope`
- `evidence_ids`
- `claim_ids`
- `pathway_ids`
- `vietnam_localization`
- `safety_notes`
- disclaimer

Module: `app/clinical_content/clinical_knowledge_pack_standard.py`.

Pack hợp lệ không được thiếu evidence và claim. Nội dung cho Việt Nam phải có vùng `[CẦN XÁC NHẬN TẠI ĐƠN VỊ]` cho thuốc, BHYT/chi phí, xét nghiệm, tuyến chuyển và phác đồ địa phương.
