# EBM Copilot trong ứng dụng ChatGPT

## Phạm vi điều phối có quản trị

Đây là ChatGPT App dạng `tool-only`, dùng MCP Streamable HTTP hoặc stdio qua
Secure MCP Tunnel. App nạp đội agent từ nguồn `.claude/agents`, không nhận PII,
không tự phê duyệt cổng và không tự áp dụng khuyến cáo.

Tools:

- `search(query)`: tìm tài liệu theo schema company knowledge/deep research.
- `fetch(id)`: đọc tài liệu do `search` trả về.
- `get_system_status()`: xem trạng thái corpus và cổng an toàn.
- `list_ebm_agents(domain)`: liệt kê toàn đội agent lâm sàng/nghiên cứu.
- `get_ebm_agent_instructions(agent_id)`: nạp đúng role cho từng bước.
- `prepare_clinical_workflow(case_summary)`: chạy nhạc trưởng lâm sàng, dừng Cổng A/B.
- `prepare_research_workflow(research_topic)`: chạy nhạc trưởng nghiên cứu, dừng các cổng G.
- `get_sync_status()`: kiểm mirror Claude↔Codex và live reload.
- `synchronize_ebm_system(confirmation)`: tái sinh mirror sau xác nhận của bác sĩ.

Không hỗ trợ: tự kê đơn/áp dụng khuyến cáo, ghi EMR/HIS, tự chạy phân tích chính
thức trước khóa SAP/data hoặc phê duyệt thay bác sĩ. Tool đồng bộ không tự
`git pull/push`.

Kho tài liệu và agent được đọc lại ở mỗi tool call. Thay đổi đã đồng bộ xuống
OneDrive được nhận ngay; GitHub push vẫn là thao tác chủ ý để tránh phát hành
nhầm dữ liệu nhạy cảm.

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

## Đồng bộ code sống — Codex tự nhận, Tunnel cần restart (quan trọng)

**Nội dung agent (`.claude/agents/*.md`)** luôn được đọc lại từ đĩa ở MỖI lần
gọi tool (`search`/`fetch`/`list_ebm_agents`/`get_ebm_agent_instructions`) —
không cần restart gì khi sửa các file `.md` này.

**Code Python của server** (`app/chatgpt_app/*.py`, `app/core/policy_engine.py`,
`app/core/export_policy.py`, `tools/run_chatgpt_mcp_stdio.py`) thì KHÁC nhau
theo từng kênh kết nối:
- **Codex desktop app** (mục dưới, stdio cục bộ qua `~/.codex/config.toml`):
  đã xác nhận thực nghiệm — mỗi "Tác vụ mới" spawn một tiến trình Python MỚI,
  tự nhận code mới nhất trên đĩa, không cần làm gì thêm.
- **Secure MCP Tunnel** (mục "Kết nối ChatGPT — khuyến nghị Secure MCP Tunnel"
  dưới): tunnel-client giữ tiến trình MCP sống SUỐT vòng đời launchd job —
  sửa code KHÔNG tự áp dụng cho kết nối đang chạy. Xác nhận bằng thực nghiệm
  2026-07-20: sau khi vá lỗ hổng PII, gọi thật qua app ChatGPT vẫn lọt PII
  (tiến trình cũ) cho tới khi `launchctl kickstart -k gui/$(id -u)/
  vn.drluan.ebm-copilot-tunnel`, sau đó mới chặn đúng.

Để không phải nhớ làm tay: `.githooks/post-commit` (kích hoạt bằng
`git config core.hooksPath .githooks`) tự động kickstart tunnel-client ngay
sau mỗi commit chạm 1 trong 4 đường dẫn trên — chạy với MỌI công cụ commit
(Claude Code, Codex, hay tay), vì hook gắn với repo chứ không gắn với người
gọi `git commit`.

## Kết nối ChatGPT/Codex desktop app trên CÙNG máy — stdio cục bộ (đơn giản nhất)

Nếu máy đã cài **ChatGPT desktop app (có Codex)** — không phải trình duyệt ChatGPT
web — thì KHÔNG cần Secure MCP Tunnel/ngrok. App này tự đọc `~/.codex/config.toml`
và có thể tự spawn một MCP server stdio cục bộ, y hệt cách nó đã cấu hình sẵn
`node_repl`/`computer-use`. Thêm khối sau vào `~/.codex/config.toml` (sao lưu
file trước khi sửa tay):

```toml
[mcp_servers.ebm-copilot]
command = "/Users/<user>/.ebm-venv/bin/python3"
args = ["tools/run_chatgpt_mcp_stdio.py"]
cwd = "/đường/dẫn/tới/medical-ebm-automation"
startup_timeout_sec = 60
```

`tools/run_chatgpt_mcp_stdio.py` tự đặt `EBM_MCP_TRANSPORT=stdio` trước khi nạp
`app.chatgpt_app.server` nên không cần khai thêm biến môi trường. Vì server
chạy stdio do chính app spawn — KHÔNG bind cổng mạng, KHÔNG cần
`EBM_MCP_TOKEN`, KHÔNG phơi ra Internet. Sau khi sửa file, **khởi động lại
ChatGPT app** (MCP server chỉ được app đọc lại lúc khởi động) rồi kiểm 9 tool
đã liệt kê ở đầu tài liệu này xuất hiện trong danh sách MCP tool của app.

Xác minh nhanh không cần mở app (mô phỏng đúng handshake MCP mà app sẽ làm):

```bash
cd medical-ebm-automation
~/.ebm-venv/bin/python3 -m pytest tests/test_chatgpt_app_knowledge.py tests/test_chatgpt_app_agents.py -q
```

Đường này phù hợp máy cá nhân một người dùng. Muốn ChatGPT WEB (không phải
desktop app) hoặc nhiều người dùng cùng truy cập thì mới cần Streamable HTTP +
Secure MCP Tunnel ở mục dưới.

## Kết nối ChatGPT — khuyến nghị Secure MCP Tunnel

Vì đây là hệ thống y khoa chạy trên máy cá nhân, ưu tiên **Secure MCP Tunnel**
của OpenAI thay vì mở endpoint ra Internet. Tunnel chỉ tạo kết nối HTTPS đi ra,
giữ MCP server ở `127.0.0.1`.

1. Trong OpenAI Platform tunnel settings, tạo tunnel và liên kết đúng ChatGPT
   workspace; lấy `tunnel_id` và runtime API key.
2. Tải `tunnel-client` từ liên kết trong Platform tunnel settings.
3. Có thể để tunnel-client quản lý server qua stdio bằng
   `EBM_MCP_TRANSPORT=stdio python -m app.chatgpt_app.server`.
4. Khởi tạo profile tunnel-client, rồi chạy `doctor` và `run` theo hướng dẫn Platform.
5. Trong ChatGPT, bật Developer Mode, tạo app mới, chọn **Tunnel** và chọn đúng
   `tunnel_id`.
6. Sau mỗi lần đổi tool/schema, restart server rồi refresh app trong ChatGPT.

Tài liệu: https://developers.openai.com/api/docs/guides/secure-mcp-tunnels

Nếu tài khoản chưa có Secure MCP Tunnel, phương án phát triển tạm thời là
`ngrok http 2091` rồi nhập `https://<subdomain>.ngrok.app/mcp` trong custom app.
Không dùng tunnel công khai cho dữ liệu bệnh nhân hoặc production.

**⚠️ `EBM_MCP_TOKEN` KHÔNG phải xác thực request thật (audit MCP 2026-07-20).**
Cổng fail-closed trong `main()` chỉ kiểm tra biến này CÓ ĐƯỢC ĐẶT hay không lúc
khởi động (`EBM_MCP_HOST` khác localhost mà thiếu token → từ chối chạy) — giá
trị token KHÔNG bao giờ được so khớp với request MCP thật (`FastMCP(...)` chưa
truyền `token_verifier`/`auth`). Đặt `EBM_MCP_TOKEN` chỉ vượt qua được cổng
khởi động, **không** tạo ra lớp xác thực nào chặn client mạng ngoài gọi vào 9
tool (kể cả `synchronize_ebm_system`). Cổng này cũng KHÔNG phát hiện được
trường hợp `ngrok`/reverse-proxy forward cổng cục bộ ra Internet trong khi
`EBM_MCP_HOST` vẫn là `127.0.0.1` — đúng kịch bản "phương án tạm thời" ở trên.
**Kết luận vận hành: chỉ dùng transport `streamable-http` sau khi tự triển
khai `token_verifier`/`auth` thật (xem tham số của `mcp.server.fastmcp.FastMCP`)
hoặc đặt sau một proxy có xác thực riêng; đường AN TOÀN THẬT hiện tại là
stdio cục bộ (mục "ChatGPT/Codex desktop app" phía trên, hoặc tunnel-client ở
chế độ quản lý stdio) — cả hai không bao giờ chạm nhánh fail-closed này.**

Production cần xác thực, log/metrics, rate limit và quy trình vận hành sự cố.
Không đưa `.env`, database, dataset thô hoặc dữ liệu bệnh nhân lên hosting.

## Cổng an toàn

- Allowlist gồm tài liệu hệ thống, knowledge pack và agent nguồn.
- Mỗi lần `fetch` đều chạy lại `classify_export_file`.
- Path traversal, secret, dữ liệu nhị phân/raw và PII-like text bị chặn.
- Mọi tài liệu trả về có SHA-256 và disclaimer “Cần bác sĩ kiểm chứng”.
- `clinical_release=blocked`, chỉ cho phép đồng bộ mirror có xác nhận, `pii_allowed=false`.

## Tài liệu chuẩn

- https://developers.openai.com/apps-sdk/quickstart
- https://developers.openai.com/apps-sdk/build/mcp-server
- https://developers.openai.com/apps-sdk/plan/tools
- https://developers.openai.com/apps-sdk/deploy
