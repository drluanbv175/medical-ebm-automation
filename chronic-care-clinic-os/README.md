# Chronic Care Clinic OS

Clinical Coordination Platform cho phong kham ngoai tru theo doi benh man tinh co cau truc. He thong nay khong phai EMR phap ly va khong thay the ho so benh an chinh thuc.

> Clinical safety: he thong chi tao ban nhap ho tro quyet dinh. Can bac si kiem chung va phe duyet truoc khi ap dung cho nguoi benh.

## Quick start

May hien tai can Node.js 20+ va PostgreSQL 15+.

```bash
cd chronic-care-clinic-os
cp .env.example .env
npm install
npx prisma migrate dev --name init_chronic_care
npm run seed
npm run dev
```

Mo `http://localhost:3000`.

## Docker local

```bash
docker compose up --build
```

## Test

```bash
npm test
```

Trong moi truong chua cai npm, co the chay test offline bang Node bundled neu co:

```bash
node --test tests/*.test.mjs
```

## Demo roles

- Super Admin
- Bac si
- Dieu duong / Care Coordinator
- Le tan
- Duoc si cong tac
- Quan ly chat luong
- Nguoi benh

## Production blockers

- Can thay demo role selector bang Auth.js that.
- Can bat PostgreSQL va Prisma runtime cho moi write action.
- Can review clinical rules, SOP va patient handout template.
- Can cau hinh backup/restore, TLS, logging va monitoring.
- AI phai disabled trong production cho den khi co quy trinh governance.
- Xem chi tiet tai `PRODUCTION_BLOCKERS.md`.
