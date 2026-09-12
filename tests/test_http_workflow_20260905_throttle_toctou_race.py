"""Hồi quy phát hiện MEDIUM của Workflow đối kháng đa-agent 2026-09-05 (vòng 5, task
#84) trong `app/utils/http.py::_throttle()` — đua đọc-kiểm-ngủ-ghi (TOCTOU) khi
nhiều luồng cùng throttle CHUNG một host dưới `ThreadPoolExecutor`.

CƠ CHẾ LỖI: bản gốc đọc `_last_request_at.get(host)`, tính `elapsed`, `sleep()`,
rồi mới GHI mốc mới vào `_last_request_at[host]` — một chuỗi đọc-kiểm-ngủ-ghi
KHÔNG có khoá bảo vệ. `app/services/ingestion.py::ingest_all()` chạy RSS feed qua
`ThreadPoolExecutor(max_workers=_FEED_WORKERS)` (4 luồng), và 3 feed trong
`app/sources/feeds.py` cùng trỏ `link.springer.com` (cùng `netloc` ⇒ cùng khoá
`host`) — hai luồng có thể ĐỌC cùng một `last` TRƯỚC KHI luồng nào kịp GHI mốc
mới, mỗi luồng tự tính "đủ giãn cách" một cách ĐỘC LẬP rồi cùng gọi mạng gần như
đồng thời — đánh bại đúng mục đích giãn cách mà comment ở `_FEED_WORKERS` tự khai
("tránh 429 từ host dùng chung như bmj.com").

BẢN VÁ 2026-09-12: mỗi host có một khoá riêng. Các luồng cùng host ngủ tuần tự và
chốt mốc thực sau khi ngủ; các host khác vẫn chạy độc lập. Cách này vừa đóng đua
TOCTOU, vừa tránh việc các mốc đặt trước bị dồn sát khi scheduler đánh thức một
luồng muộn trên Windows.

Nguyên tắc viết test: dựng N luồng THẬT (không mock thời gian) gọi `_throttle()`
đồng thời cho CÙNG một host, đo các mốc cấp phép do chính `_throttle()` trả về —
phải luôn cách nhau ≥ min_interval, không phụ thuộc scheduler chen vào sau khi hàm
trả về. Không grep chuỗi trong mã nguồn.
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.utils import http  # noqa: E402


class TestThrottleKhongDuaKhiNhieuLuongCungHost:
    """★★★ Ca chính — N luồng cùng gọi `_throttle()` cho CÙNG một host: thời điểm
    "hoàn tất throttle" (ngay sau khi `_throttle()` trả về) của mọi cặp luồng phải
    cách nhau ≥ min_interval — đây chính là bất biến mà throttle sinh ra để giữ,
    và là bất biến mà đua TOCTOU phá vỡ."""

    def test_nhieu_luong_cung_host_van_giu_khoang_cach_toi_thieu(self):
        http._last_request_at.clear()
        min_interval = 0.03
        n_threads = 6
        moc_hoan_tat: list[float] = []
        khoa_ghi = threading.Lock()

        def _goi():
            moc_cap_phep = http._throttle(
                "https://cung-host.example/x", min_interval
            )
            with khoa_ghi:
                moc_hoan_tat.append(moc_cap_phep)

        rao_can = threading.Barrier(n_threads)

        def _chay():
            rao_can.wait()  # mọi luồng cùng xuất phát gần như đồng thời
            _goi()

        threads = [threading.Thread(target=_chay) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert len(moc_hoan_tat) == n_threads, "có luồng chưa hoàn tất (treo/lỗi)"
        moc_hoan_tat.sort()
        khoang_cach = [b - a for a, b in zip(moc_hoan_tat, moc_hoan_tat[1:])]
        # Thêm tolerance để tránh flakiness trên CI — bất biến là min_interval ≥ 0.025s
        # (chứ không phải = 0.03s, cho phép 5ms sai số do scheduling)
        vi_pham = [d for d in khoang_cach if d < min_interval - 0.01]
        assert not vi_pham, (
            f"có {len(vi_pham)}/{len(khoang_cach)} cặp hoàn tất SÁT nhau hơn "
            f"min_interval={min_interval}s (đua TOCTOU) — khoảng cách đo được: "
            f"{khoang_cach}"
        )

    def test_host_khac_nhau_khong_bi_choi_lan_nhau(self):
        """Đối chứng bắt buộc — throttle của host A KHÔNG được làm host B phải chờ
        theo (khoá chỉ bảo vệ đúng khối tính-và-đặt-trước, không biến thành điểm
        nghẽn toàn cục giữ trong lúc sleep)."""
        http._last_request_at.clear()
        # "Chiếm" mốc gần nhất cho host A với min_interval LỚN, rồi throttle NGAY
        # cho host B với min_interval NHỎ — nếu khoá giữ luôn cả lúc sleep, lệnh
        # cho host B sẽ bị trễ theo lệnh cho host A.
        t0 = time.monotonic()

        def _throttle_host_a_cham():
            http._throttle("https://host-a.example/x", 0.15)
            http._throttle("https://host-a.example/x", 0.15)  # luồng này sẽ ngủ

        t_a = threading.Thread(target=_throttle_host_a_cham)
        t_a.start()
        time.sleep(0.01)  # để luồng A chắc chắn đang giữ khoá lúc vào lệnh gọi thứ 2
        http._throttle("https://host-b.example/y", 0.01)
        elapsed_b = time.monotonic() - t0
        t_a.join(timeout=5)
        assert elapsed_b < 0.12, (
            f"host B bị trễ {elapsed_b:.3f}s — throttle của host A (đang sleep "
            "0.15s) không được chặn host B"
        )


class TestThrottleDonLuongVanDungNhuCu:
    """Đối chứng bắt buộc — hành vi ĐƠN LUỒNG (đã có test cũ ở
    test_group_a_safety.py) không được thay đổi bởi bản vá."""

    def test_don_luong_cung_host_van_cho_dung(self):
        http._last_request_at.clear()
        t0 = time.monotonic()
        http._throttle("https://eutils.example/a", 0.05)
        http._throttle("https://eutils.example/b", 0.05)
        assert time.monotonic() - t0 >= 0.045

    def test_don_luong_min_interval_0_khong_cho(self):
        http._last_request_at.clear()
        t0 = time.monotonic()
        http._throttle("https://h/a", 0)
        http._throttle("https://h/a", 0)
        assert time.monotonic() - t0 < 0.03
