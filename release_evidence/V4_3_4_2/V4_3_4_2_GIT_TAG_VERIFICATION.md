# V4.3.4.2 Git Tag Verification

**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Baseline verification

```
git rev-parse v4.3.4^{commit}
→ 101ca08a331605e95b15cb82a4839e0e2a799e3e  ✓

git show --oneline --no-patch v4.3.4
→ 101ca08 feat: V4.3.4 Human Review Operations — 4 roles, 5 decisions, append-only ledger

git status --porcelain
→ (clean working tree at time of baseline verification)
```

**Baseline CONFIRMED** — `v4.3.4` trỏ đúng commit `101ca08a...`.

---

## Archive SHA256

| Method | SHA256 |
|--------|--------|
| `git archive --format=tar v4.3.4 \| shasum -a 256` (no prefix, pipe) | `df968469e1509447f48d74a556a0c1142442ef3cd0e9d4d2cd7b1fbc214a5789` |
| `git archive --format=tar --prefix=medical-ebm-automation/ v4.3.4 > file` + `shasum -a 256 file` | `d69fe47c99aafe3036371af91d843303b25323ade80c8ad09ded118e98fde851` |

**Lý do khác biệt:** `--prefix=medical-ebm-automation/` thay đổi đường dẫn trong tar → SHA256 khác nhau. Cả hai đều đại diện cho cùng nội dung nguồn từ commit `101ca08a`.

---

## Annotated freeze tag (sau khi tất cả điều kiện PASS)

```
git cat-file -t v4.3.4-frozen
→ tag  (annotated — NOT lightweight)

git rev-parse v4.3.4-frozen^{commit}
→ 101ca08a331605e95b15cb82a4839e0e2a799e3e

git tag -n99 v4.3.4-frozen
→ v4.3.4-frozen   V4.3.4 human review operations fresh-archive
                   and manifest-registry verified
```

---

## Tags summary

| Tag | Type | Target commit |
|-----|------|--------------|
| `v4.3.4` | lightweight | `101ca08a...` |
| `v4.3.4-frozen` | **annotated** | `101ca08a...` |

---

*Manual review record does not constitute ethics, PI, final, or independent approval.*
