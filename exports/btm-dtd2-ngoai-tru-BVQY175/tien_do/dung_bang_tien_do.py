"""Dựng bảng theo dõi tiến độ (HTML cho khung hiển thị trong phiên Claude) từ sổ TIEN_DO_<đề tài>.json.

Cách dùng: python3 dung_bang_tien_do.py  →  ghi bang_tien_do.html cạnh tệp này; phiên Claude đọc tệp đó rồi hiển thị.
Sổ JSON là nguồn sự thật; tệp HTML chỉ là bản dựng, không sửa tay.
"""
import json
import sys
from pathlib import Path

THU_MUC = Path(__file__).resolve().parent
MA = "btm-dtd2-ngoai-tru-BVQY175"


def ngan(ngay: str) -> str:
    """dd/mm/yyyy → dd/mm/yy cho gọn bảng."""
    return ngay[:6] + ngay[8:] if len(ngay) == 10 else ngay


def du_lieu_gon(so: dict) -> dict:
    """Rút sổ đầy đủ thành dạng gọn mà mẫu HTML đọc: g = giai đoạn, v = việc."""
    chi_so = {g["id"]: k for k, g in enumerate(so["giai_doan"])}
    return {
        "u": so["cap_nhat"],
        "g": [[g["ten"], ngan(g["tu"]), ngan(g["den"])] for g in so["giai_doan"]],
        "v": [[v["id"], chi_so[v["gd"]], v["ten"], v["ai"], ngan(v["han"]), v["trang_thai"], v["phu_thuoc"]]
              for v in so["viec"]],
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    so = json.loads((THU_MUC / f"TIEN_DO_{MA}.json").read_text(encoding="utf-8"))
    mau = (THU_MUC / "mau_bang_tien_do.html").read_text(encoding="utf-8")
    du_lieu = json.dumps(du_lieu_gon(so), ensure_ascii=False, separators=(",", ":"))
    (THU_MUC / "bang_tien_do.html").write_text(mau.replace("__DATA__", du_lieu), encoding="utf-8")
    xong = sum(v["trang_thai"] == "xong" for v in so["viec"])
    print(f"bang_tien_do.html — {xong}/{len(so['viec'])} việc xong, sổ cập nhật {so['cap_nhat']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
