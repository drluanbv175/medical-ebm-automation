# Architecture

## Tong quan

Chronic Care Clinic OS duoc thiet ke nhu mot ung dung Next.js monolith co bien gioi ro rang:

- Presentation: Next.js App Router, TypeScript, Tailwind CSS.
- Application layer: server actions/API routes cho workflow noi bo.
- Domain layer: RBAC, audit, risk rules, medication reconciliation, care plan validation.
- Data layer: PostgreSQL qua Prisma ORM.
- Governance: audit log bat buoc, soft archive, version history cho note/care plan.

Trong ban MVP nay, UI demo doc seed TypeScript tinh de co the duyet luong nghiep vu ngay khi chua cai PostgreSQL. Prisma schema va seed script la nguon san sang cho database that.

## Module boundaries

- `app/`: routes va man hinh workflow.
- `components/`: reusable UI primitives va clinical widgets.
- `lib/`: domain logic, RBAC, audit types, risk engine, demo data.
- `prisma/`: schema va seed database.
- `scripts/`: kiem tra tinh toan seed/rule offline.
- `docs/`: SOP, deployment, security, governance va user guides.

## Clinical safety architecture

- Risk engine chi sinh `suggestedRiskLevel`, khong chot muc cuoi.
- Moi rule co ten, mo ta, muc do, hanh dong de xuat, version, ngay hieu luc, ngay review va yeu cau bac si xac nhan.
- Red-flag UI luon hien thong diep: "Can bac si danh gia truc tiep ngay..."
- Care plan co status `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`, `ARCHIVED`.
- Loi dan A5 chi o trang thai draft cho den khi co `approvedBy`.
- AI mac dinh disabled in production va khong duoc tu ky note.

## Security architecture

- RBAC kiem tra o frontend va du kien backend middleware.
- Least privilege theo role.
- Audit log cho create/update/view/export/approve/reject/archive.
- Khong xoa hard delete ho so lam sang.
- Khong dua PII len AI public.
- `.env` khong commit; `.env.example` chi chua placeholder.
- Session timeout va MFA-ready Auth.js architecture.

## Deployment path

- Local: `npm install`, `npx prisma migrate dev`, `npm run seed`, `npm run dev`.
- Private server: Docker Compose gom app va PostgreSQL.
- Future: private cloud/on-premise, FHIR layer, HIS/EMR integration, SMS/Zalo/email gateway.
