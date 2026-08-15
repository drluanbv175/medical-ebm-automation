# Test Plan

## Required scenarios

1. Bac si dang nhap va tao care plan.
2. Dieu duong chi cap nhat phan duoc phan quyen.
3. Le tan khong xem note lam sang nhay cam.
4. Nguoi benh nguy co do hien canh bao.
5. Khong cho hoan tat buoi kham neu thieu phan tang nguy co.
6. Tao task nhac tai kham cho nguoi benh qua han.
7. Ghi audit log khi care plan thay doi.
8. Tao printable loi dan A5.
9. AI khong tu ky note.
10. Khong gui thong diep dieu tri tu dong.
11. Export tong hop da khu dinh danh.
12. Chan truy cap cheo ho so.

## Implemented offline checks

`tests/clinic-os.test.mjs` kiem tra:

- Seed demo co 50 nguoi benh.
- Co du nhom tinh huong bat buoc.
- Risk engine bat red flag va polypharmacy.
- RBAC chan le tan xem clinical note.
- AI disabled by default.
- Prisma schema co cac model cot loi.
