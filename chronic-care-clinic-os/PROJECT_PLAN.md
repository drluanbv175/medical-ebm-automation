# Chronic Care Clinic OS - Project Plan

## Muc tieu san pham

Chronic Care Clinic OS la he thong web noi bo ho tro phong kham ngoai tru quan ly lien tuc nguoi benh co benh man tinh. MVP tap trung vao tang huyet ap, dai thao duong type 2, roi loan lipid mau, beo phi, nguy co tim mach cao, da benh ly, da thuoc va benh than man giai doan som-trung binh.

He thong khong chan doan, khong ke don, khong tu dong thay doi dieu tri. Moi goi y lam sang la ban nhap can bac si xac nhan va luu audit trail.

## Pham vi MVP

- Dang nhap mau va role-based access control.
- Dang ky, tra cuu va xem ho so nguoi benh gia lap.
- Ho so benh man, thuoc, sinh hieu, xet nghiem, hen, lan kham, care plan, task va chuyen tuyen.
- Phan tang nguy co xanh-vang-do bang rule-based draft.
- Dashboard cho bac si, dieu duong va quan ly chat luong.
- Luong kham lan dau, tai kham, qua han tai kham va sau xuat vien o muc workflow.
- Module loi dan A5 dang printable HTML, san sang gan PDF renderer.
- Audit log foundation va tai lieu van hanh.
- Seed data 50 nguoi benh gia lap, khong dung du lieu that.

## Thu tu trien khai

1. Pha 0: tai lieu kien truc, gia dinh, backlog, risk register.
2. Pha 1: project structure, RBAC, Prisma schema, seed, audit foundation, Docker, README.
3. Pha 2: patient registry, appointment, vital signs, medication reconciliation, visit note, care plan, risk stratification, task va handout.
4. Pha 3: care coordination sau khi Pha 1-2 duoc bac si duyet nghiep vu.
5. Pha 4: governance, KPI, SOP repository, data export va backup.
6. Pha 5: AI draft assistance, disabled by default in production.

## Definition of Done cho MVP hien tai

- Co tai lieu cai dat va van hanh.
- Co schema database versioned bang Prisma.
- Co seed data demo 50 nguoi benh.
- Co giao dien chinh cho cac role noi bo.
- Co test rule/data can chay duoc khong can du lieu that.
- Co IMPLEMENTATION_STATUS.md ghi ro phan da xong, dang lam, chua xong va rui ro.
