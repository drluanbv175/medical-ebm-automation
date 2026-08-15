# Automation Safety Model

## Nguyen tac

Automation trong MVP chi tao task, queue, draft hoac canh bao noi bo. Automation khong tu gui dieu tri, khong tu thay doi care plan, khong tu quyet dinh chuyen vien.

## Automation rule contract

Moi rule can:

- `rule_id`
- `rule_name`
- `description`
- `priority`
- `trigger_type`
- `eligibility_logic`
- `exclusion_logic`
- `assigned_role`
- `approval_required`
- `notification_template`
- `escalation_logic`
- `is_active`
- `version`
- `approved_by`
- `effective_date`
- `review_date`

## Noi bo vs nguoi benh

Notification noi bo duoc phep cho task moi, task qua han, nguy co cao, care plan cho duyet, lab cho review va nguoi benh qua hen.

Communication voi nguoi benh chi duoc gui khi co template duoc duyet, consent phu hop, khong co noi dung dieu tri ca the hoa chua duyet, co owner va co communication log.
