# V4.3.3.2 — hai lượt freeze, không phải trùng lặp

Thư mục này gộp bằng chứng của **hai lượt đóng băng riêng biệt** cùng thuộc
release V4.3.3.2, dồn về đây ngày 06/09/2026 (trước đó nằm rải ở gốc repo).

| File | Lượt freeze | Commit | Nội dung |
|---|---|---|---|
| `V4_3_3_2_RATIONALIZATION_FREEZE_SUMMARY.md` | 1 — Repo rationalization | `30a27f71` | Đóng băng đợt dọn dẹp/chính sách retention (nhánh `feat/v4-3-3-2-repository-rationalization`): 12 cổng MET, tạo `RETENTION_POLICY`/`CLEANUP_DECISION_MATRIX`/`ARCHIVE_RECEIPT`… |
| `V4_3_3_2_FREEZE_SUMMARY.md` | 2 — Full suite fresh archive | `0ce0d47` (tag `v4.3.3.2-frozen`) | Đóng băng chính thức: 756 test pass, archive SHA256 xác minh, D-R13/D-R8 gate check |

12 file còn lại trong thư mục (`V4_3_3_2_ARCHIVE_RECEIPT.json`, `V4_3_3_2_RETENTION_POLICY.md`,
`V4_3_3_2_CLEANUP_DECISION_MATRIX.md`…) là bằng chứng của **lượt 1**. Các file
`V4_3_3_2_FULL_SUITE_*` (đã có sẵn trong thư mục từ trước) là bằng chứng của
**lượt 2**.

Không file nào bị xoá hay sửa nội dung khi dồn về đây — chỉ đổi vị trí, và đổi
tên đúng một file (`V4_3_3_2_FREEZE_SUMMARY.md` gốc → thêm tiền tố
`RATIONALIZATION_`) để không đè lên bản đã có sẵn ở đây từ lượt 2.
