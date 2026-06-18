# Gap Analysis

## Ket luan ngan gon

Chronic Care Clinic OS hien la Clinical Coordination Platform cho quan ly benh man, khong phai EMR phap ly va khong duoc thay the ho so benh an chinh thuc. Ban hien tai co nhieu giao dien va domain rule demo, nhung backend write path, authentication production, audit bat bien va PDF engine chua hoan tat.

## Module da ton tai

- Next.js app skeleton va navigation.
- Dashboard bac si, dieu duong, quality.
- Patient registry va patient detail.
- Appointment list.
- Initial visit va follow-up workflow shell.
- Medication reconciliation queue.
- Lab review queue.
- Care plan list.
- Red-risk list va overdue follow-up list.
- Task list, referral list, A5 handout printable view.
- Clinical rules page, SOP repository, template page, user page, audit viewer va settings.
- Prisma schema ban dau.
- Demo seed 50 nguoi benh gia lap.
- RBAC matrix trong `lib/rbac.ts`.
- Rule-based risk engine trong `lib/clinical-safety.ts`.
- Offline tests.

## Module moi chi la giao dien

- Login/role selector.
- Patient registration button.
- Care plan create/approve actions.
- Appointment create/check-in.
- Vital sign entry.
- Medication reconciliation approval.
- A5 PDF generation.
- CSV/XLSX export.
- Rule approval workflow UI.
- User management actions.
- SOP/content approval actions.

## Module da co backend that

- Chua co backend production cho write workflow.
- Prisma schema va seed script da co, nhung chua co API/server action production wiring.
- Offline tests doc/schema/safety/RBAC da co.

## Module chua co phan quyen backend

- Tat ca route UI hien tai.
- Tat ca button create/update/approve/export.
- Can them API guard bat buoc cho moi read/write nhay cam truoc production.

## Module chua co audit trail production

- Patient create/update.
- Vitals create.
- Medication reconciliation.
- Care plan approval/versioning.
- Handout approval/print.
- Task workflow transitions.
- Rule activation.
- Dashboard export.

## Module chua co validation

- Form patient registration.
- Vitals input.
- Medication list input.
- Care plan draft.
- Appointment scheduling.
- Communication template approval.
- Rule creation/update.

## Module khong duoc dung production

- Demo role selector.
- Static seed UI data.
- A5 printable HTML thay cho PDF engine da kiem thu.
- Clinical rules draft chua co approval workflow that.
- AI module, hien chi la documented disabled state.
- Automation engine neu chua gan audit, approval va owner role that.

## Nham lan can sua ro

- Khong dung cum "EMR thay the" cho san pham nay.
- He thong chi nam duoi EMR phap ly: lay du lieu phu hop tu Clinical Record/EMR, dieu phoi cham soc va bao cao chat luong.
- Visit note trong app chi la coordination note/draft neu chua co quy trinh ky va khoa hop phap.

## Rui ro an toan lam sang

- Risk suggestion co the bi hieu la final neu UI khong yeu cau clinician confirmation.
- Red flag co the bi xu ly cham neu task queue thay cho canh bao truc tiep.
- Medication warnings co the bi hieu la ket luan tuong tac/chong chi dinh.
- Handout draft co the duoc in/giao khi chua duyet.
- Lab abnormal review co the bi gui sai cho nguoi benh neu khong chan automation.

## Rui ro bao mat du lieu

- Chua co auth/session production.
- Chua co organization/site isolation.
- Chua co backend RBAC enforcement.
- Chua co rate limit va secure headers.
- Chua co immutable audit store.
- Dashboard registry hien co the hien ten/phone trong demo; production can default de-identification theo role.

## Dependency can khoa version hoac thay the

- Next.js, React, NextAuth, Prisma, Zod, React Hook Form, QRCode can lockfile va vulnerability scan.
- Can them password hashing library da duyet neu dung credential login.
- Can PDF generator server-side duoc kiem thu neu can A5 PDF that.
- Can logger co PHI redaction.
