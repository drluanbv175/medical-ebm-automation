# Security

## Principles

- Privacy by design.
- Least privilege.
- Role-based access control.
- Audit trail by default.
- No public AI exposure of identifiable patient data.
- No real patient data in demo or tests.

## Access control

RBAC duoc dinh nghia tai `lib/rbac.ts` va `ROLE_MATRIX.md`. Moi hanh dong production phai kiem tra quyen o frontend va backend.

## Secrets

- Khong commit `.env`.
- Dung `.env.example` cho placeholder.
- Production can secret manager hoac encrypted environment.

## Audit

Moi hanh dong xem, sua, duyet, xuat, luu tru hoac huy kich hoat can ghi `AuditLog`.
Moi write action production phai ghi business row va `AuditLog` trong cung transaction, voi `sequence`, `previousHash`, `eventHash` va policy insert-only.

## Data deletion

Khong xoa truc tiep ho so lam sang. Dung archive/deactivate va version history.
