#!/usr/bin/env python3
"""Điểm vào CLI của hệ thống Medical EBM Automation.

Cách dùng:
    python run.py                 # mặc định: init + seed dữ liệu mẫu + báo cáo tuần
    python run.py init            # chỉ tạo database
    python run.py seed            # nạp dữ liệu mẫu (mock pipeline + scores + projects)
    python run.py pipeline        # chạy pipeline EBM (theo USE_MOCK_SOURCES)
    python run.py live-update     # QUÉT API THẬT (chỉ bài MỚI) + bản tin cảnh báo + báo cáo
    python run.py alert [số_ngày] # bản tin "Cảnh báo mới trong N ngày" (mặc định 7)
    python run.py notify [số_ngày]# GỬI cảnh báo email/webhook nếu có mục mới ưu tiên cao
    python run.py report          # chạy pipeline + xuất báo cáo tuần (md/html/docx)
    python run.py export          # xuất Excel/CSV/BibTeX
    python run.py safety          # xuất báo cáo An toàn thuốc + Kháng sinh tuần
    python run.py dossier <project_id>   # xuất Hồ sơ nghiên cứu (đề cương + tài liệu nền + checklist)
    python run.py zotero-push     # đẩy tài liệu actionable vào Zotero (cần cấu hình)
    python run.py test-live [nguồn] [từ khoá]   # gọi 1 nguồn API THẬT để kiểm chứng
    python run.py tiktok [N]      # sinh N gói nội dung TikTok (slideshow+caption) từ kho
    python run.py tiktok-watch [N]# như trên nhưng GỒM cả "tin nhanh – chưa kết luận"
    python run.py tiktok-video [N]# như tiktok nhưng dựng thêm VIDEO dọc + giọng đọc tiếng Việt
    python run.py tiktok-whiteboard [N]  # video PHONG CÁCH BẢNG TRẮNG viết tay + giọng đọc mềm
    python run.py tiktok-auto     # CHỈ sinh nếu .env bật ENABLE_TIKTOK_AUTO (dùng cho lịch nền)
    python run.py dashboard       # mở dashboard Streamlit
    python run.py schedule        # chạy scheduler định kỳ
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from app.config import BASE_DIR
from app.utils.logging_config import get_logger

logger = get_logger("run")


def _print(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "default"

    if cmd in ("default", "seed"):
        from app.main import cmd_seed
        result = cmd_seed()
        if cmd == "default":
            from app.main import cmd_weekly_report
            result["reports"] = cmd_weekly_report()
            print("\n✅ Khởi tạo xong. Chạy dashboard bằng: python run.py dashboard\n")
        _print(result)

    elif cmd == "init":
        from app.main import cmd_init
        cmd_init()

    elif cmd == "pipeline":
        from app.main import cmd_run_pipeline
        _print(cmd_run_pipeline())

    elif cmd == "live-update":
        from app.main import cmd_live_update
        _print(cmd_live_update())

    elif cmd == "alert":
        from app.main import cmd_alert
        days = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 7
        _print(cmd_alert(days=days))

    elif cmd == "notify":
        from app.main import cmd_notify
        days = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 7
        _print(cmd_notify(days=days))

    elif cmd == "notify-test":
        # Gửi thử cảnh báo NGAY (force) để kiểm tra SMTP/webhook, kể cả khi không có mục mới.
        from app.config import settings as _s
        _to = _s.alert_email_to or "(ALERT_EMAIL_TO chưa đặt)"
        _ans = input(
            f"⚠️  Sẽ GỬI email/webhook THẬT tới {_to} (kể cả khi không có mục mới). "
            "Tiếp tục? [y/N] "
        ).strip().lower()
        if _ans != "y":
            print("Đã hủy.")
            return 0
        from app.main import cmd_notify
        _print(cmd_notify(days=30, force=True))

    elif cmd == "set-email-password":
        # Lệnh thân thiện cho người không rành code: dán App Password -> tự lưu vào .env -> gửi thử.
        import getpass
        env_path = Path(BASE_DIR) / ".env"
        if not env_path.exists():
            print("❌ Không tìm thấy file .env. Hãy báo lại để tôi tạo giúp.")
            return 1
        print("\n📋 DÁN App Password 16 ký tự của Gmail vào đây rồi nhấn Enter.")
        print("   (Khi dán, màn hình SẼ KHÔNG hiện gì — đó là bình thường để bảo mật.)\n")
        pw = getpass.getpass("   App Password: ").replace(" ", "").strip()
        if len(pw) < 12:
            print("\n⚠️  Có vẻ chưa đúng (App Password Gmail thường 16 ký tự, không có khoảng trắng).")
            print("    Hãy chạy lại lệnh và dán đúng chuỗi từ https://myaccount.google.com/apppasswords")
            return 1
        lines = env_path.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if line.startswith("SMTP_PASSWORD="):
                lines[i] = f"SMTP_PASSWORD={pw}"
                break
        else:
            lines.append(f"SMTP_PASSWORD={pw}")
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n✅ Đã lưu App Password vào .env (an toàn, được .gitignore bảo vệ).")
        from app.config import settings as _s
        print(f"📧 Đang gửi email thử về {_s.alert_email_to or '(ALERT_EMAIL_TO chưa đặt trong .env)'} ...\n")
        from app.main import cmd_notify
        res = cmd_notify(days=30, force=True)
        em = res.get("email", {})
        if em.get("status") == "sent":
            print("🎉 GỬI THÀNH CÔNG! Hãy mở Gmail kiểm tra hộp thư (cả mục Quảng cáo/Spam).")
        elif em.get("status") == "skipped":
            print("⏭️  Bị bỏ qua:", em.get("reason"), "— kiểm tra lại .env.")
        else:
            print("❌ Gửi lỗi:", em.get("error", em))
            print("   Thường do App Password sai. Tạo lại tại https://myaccount.google.com/apppasswords")

    elif cmd == "report":
        from app.main import cmd_weekly_report
        _print(cmd_weekly_report())

    elif cmd == "export":
        from app.main import cmd_export_all
        _print(cmd_export_all())

    elif cmd == "safety":
        from app.database import init_db
        from app.reports import export_antibiotic_report, export_drug_safety_report
        init_db()
        drug = export_drug_safety_report()
        ab = export_antibiotic_report()
        _print({"drug_safety": {k: str(v) for k, v in drug.items()},
                "antibiotic": {k: str(v) for k, v in ab.items()}})

    elif cmd == "test-live":
        from app.main import cmd_test_live
        source = sys.argv[2] if len(sys.argv) > 2 else "europepmc"
        query = sys.argv[3] if len(sys.argv) > 3 else "atrial fibrillation guideline 2024"
        _print(cmd_test_live(source=source, query=query))

    elif cmd == "tiktok-auto":
        # Dùng cho lịch nền: chỉ sinh khi .env bật ENABLE_TIKTOK_AUTO (mặc định bỏ qua êm).
        from app.config import settings
        if not settings.enable_tiktok_auto:
            print("⏭️  ENABLE_TIKTOK_AUTO chưa bật trong .env — bỏ qua sinh TikTok tự động.")
        else:
            from app.main import cmd_tiktok
            res = cmd_tiktok(limit=settings.tiktok_auto_count,
                             make_video=settings.tiktok_auto_video)
            print(f"✅ TikTok tự động: {res['count']} bài (chờ duyệt) tại {res['batch_dir']}")
            _print(res)

    elif cmd == "tiktok-whiteboard":
        from app.main import cmd_tiktok
        n = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 3
        res = cmd_tiktok(limit=n, make_video=True, style="whiteboard", draw_on=True)
        print(f"\n✅ Đã sinh {res['count']} bài TikTok phong cách BẢNG TRẮNG + giọng đọc"
              f" — bỏ qua {res['skipped']} mục.")
        print(f"🎬 Video dựng được: {res.get('n_videos', 0)}/{res['count']}")
        print(f"👉 Mở xem trước: {res['index_html']}\n")
        _print(res)

    elif cmd in ("tiktok", "tiktok-watch", "tiktok-video"):
        from app.main import cmd_tiktok
        n = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 5
        make_video = (cmd == "tiktok-video")
        res = cmd_tiktok(limit=n, include_watch=(cmd == "tiktok-watch"),
                         make_video=make_video)
        print(f"\n✅ Đã sinh {res['count']} bài TikTok"
              f"{' (gồm tin nhanh)' if cmd == 'tiktok-watch' else ''}"
              f"{' + video' if make_video else ''}"
              f" — bỏ qua {res['skipped']} mục chưa đủ điều kiện.")
        if make_video:
            print(f"🎬 Video dựng được: {res.get('n_videos', 0)}/{res['count']}"
                  f"{'' if res.get('video_available') else ' (thiếu say/ffmpeg)'}")
        if not res["render_available"]:
            print("⚠️  Chưa vẽ được ảnh (thiếu Pillow/font) — gói chỉ có caption + kịch bản."
                  "  Cài ảnh: ~/.ebm-venv/bin/pip install Pillow")
        print(f"👉 Mở xem trước: {res['index_html']}\n")
        _print(res)

    elif cmd == "dossier":
        from app.database import init_db
        from app.research import export_research_dossier
        init_db()
        if len(sys.argv) < 3:
            print("Cần project_id. Ví dụ: python run.py dossier RES-2026-001")
            return 1
        path = export_research_dossier(sys.argv[2])
        _print({"dossier": str(path) if path else None,
                "note": None if path else "Không tìm thấy đề tài"})

    elif cmd == "zotero-push":
        from app.database import init_db
        from app.sources.zotero import ZoteroClient
        init_db()
        _print(ZoteroClient().push_actionable_evidence())

    elif cmd == "dashboard":
        app_path = Path(BASE_DIR) / "app" / "dashboard" / "main.py"
        logger.info("Khởi chạy Streamlit dashboard: %s", app_path)
        # Tắt file-watcher (tránh kẹt do OneDrive chạm mtime) – phù hợp app người dùng.
        return subprocess.call(
            [sys.executable, "-m", "streamlit", "run", str(app_path),
             "--server.fileWatcherType", "none", "--server.runOnSave", "false"])

    elif cmd == "schedule":
        from app.scheduler import run_scheduler
        run_scheduler()

    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
