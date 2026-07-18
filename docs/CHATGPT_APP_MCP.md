# EBM Copilot trong ứng dụng ChatGPT

## Phạm vi MVP

Đây là ChatGPT App dạng `tool-only`, dùng MCP Streamable HTTP. Bản đầu tiên chỉ
đọc tài liệu đã vượt chính sách export an toàn, không có công cụ ghi và không
nhận PII.

Tools:

- `search(query)`: tìm tài liệu theo schema company knowledge/deep research.
- `fetch(id)`: đọc tài liệu do `search` trả về.
- `get_system_status()`: xem trạng thái corpus và cổng an toàn.

Không hỗ trợ: kê đơn, tự áp dụng khuyến cáo, ghi EMR/HIS, sửa dữ liệu, chạy phân
tích chính thức hoặc phê duyệt thay bác sĩ.

## Chạy cục bộ

```bash
source ~/.ebm-venv/bin/activate
pip install -r requirements.txt
python -m app.chatgpt_app.server
```

Server mặc định nghe tại `http://127.0.0.1:2091/mcp`. Có thể đổi bằng:

```bash
export EBM_MCP_HOST=127.0.0.1
export EBM_MCP_PORT=2091
export EBM_GITHUB_REPOSITORY=drluanbv175/medical-ebm-automation
export EBM_GITHUB_REF=feat/r1-1-2-design-gap-remediation
```

Khi chạy local, nếu không đặt `EBM_GITHUB_REF`, server tự đọc nhánh Git hiện
tại. Khi deploy production phải đặt biến này tường minh theo nhánh/tag đã phát
hành để URL trích dẫn ổn định.

## Kiểm tra cục bộ

```bash
python -m pytest tests/test_chatgpt_app_knowledge.py -q
npx @modelcontextprotocol/inspector http://127.0.0.1:2091/mcp
```

## Kết nối ChatGPT — khuyến nghị Secure MCP Tunnel

Vì đây là hệ thống y khoa chạy trên máy cá nhân, ưu tiên **Secure MCP Tunnel**
của OpenAI thay vì mở endpoint ra Internet. Tunnel chỉ tạo kết nối HTTPS đi ra,
giữ MCP server ở `127.0.0.1`.

1. Trong OpenAI Platform tunnel settings, tạo tunnel và liên kết đúng ChatGPT
   workspace; lấy `tunnel_id` và runtime API key.
2. Tải `tunnel-client` từ liên kết trong Platform tunnel settings.
3. Chạy server cục bộ bằng lệnh ở phần trên.
4. Khởi tạo profile HTTP trỏ tới `http://127.0.0.1:2091/mcp`, rồi chạy
   `tunnel-client doctor` và `tunnel-client run` theo hướng dẫn Platform.
5. Trong ChatGPT, bật Developer Mode, tạo app mới, chọn **Tunnel** và chọn đúng
   `tunnel_id`.
6. Sau mỗi lần đổi tool/schema, restart server rồi refresh app trong ChatGPT.

Tài liệu: https://developers.openai.com/api/docs/guides/secure-mcp-tunnels

Nếu tài khoản chưa có Secure MCP Tunnel, phương án phát triển tạm thời là
`ngrok http 2091` rồi nhập `https://<subdomain>.ngrok.app/mcp` trong custom app.
Không dùng tunnel công khai cho dữ liệu bệnh nhân hoặc production.

Production cần xác thực, log/metrics, rate limit và quy trình vận hành sự cố.
Không đưa `.env`, database, dataset thô hoặc dữ liệu bệnh nhân lên hosting.

## Cổng an toàn

- Allowlist chỉ gồm tài liệu hệ thống và knowledge pack.
- Mỗi lần `fetch` đều chạy lại `classify_export_file`.
- Path traversal, secret, dữ liệu nhị phân/raw và PII-like text bị chặn.
- Mọi tài liệu trả về có SHA-256 và disclaimer “Cần bác sĩ kiểm chứng”.
- `clinical_release=blocked`, `writes_enabled=false`, `pii_allowed=false`.

## Tài liệu chuẩn

- https://developers.openai.com/apps-sdk/quickstart
- https://developers.openai.com/apps-sdk/build/mcp-server
- https://developers.openai.com/apps-sdk/plan/tools
- https://developers.openai.com/apps-sdk/deploy
