# AI Dev Team: framework quản lý phát triển phần mềm đa agent

Một repo mẫu cho Claude Code. Session chính đóng vai **Project Manager (PM)**, điều phối **7 subagent chuyên môn** (định nghĩa native trong `.claude/agents/`). Bạn là chủ dự án và là người ra quyết định cuối cùng.

## Cấu trúc

```
.claude/agents/     7 subagent: business-analyst, solution-architect, database-architect,
                    frontend-developer, backend-developer, qa-engineer, code-reviewer
.claude/settings.json   model mặc định của PM (sonnet) và các quy tắc ask/deny
CLAUDE.md           luật điều phối của PM (workflow, routing model, các mốc cần duyệt)
PROJECT_STATUS.md   backlog, trạng thái task, rủi ro, nhật ký agent (PM cập nhật)
requirements/       do business-analyst viết
docs/               do solution-architect viết (kiến trúc, API contract, ADR)
database/           do database-architect viết (ERD, schema, migration, index)
testing/            do qa-engineer viết (strategy, cases, report, bugs)
```

## Dùng cho dự án mới

1. Sao chép repo này thành dự án mới. Có thể bỏ thư mục `.git` để bắt đầu lịch sử mới:
   `git clone C:\Users\admin\ai-dev-team D:\projects\my-app`
   Nếu muốn áp vào **repo có sẵn**: chép `.claude/agents/`, `.claude/settings.json`, `CLAUDE.md` và `PROJECT_STATUS.md` vào đó. Nếu repo đã có `CLAUDE.md`, hãy gộp nội dung, đừng ghi đè. Các thư mục tài liệu sẽ được agent tạo khi cần.
2. Mở thư mục đó bằng Claude Code (`claude` trong terminal, hoặc mở bằng VS Code). Gõ `/agents` để kiểm tra đủ 7 agent.
3. Dán định nghĩa dự án, ví dụ:
   > Dự án mới: hệ thống đặt lịch khám cho phòng khám nhỏ. Mục tiêu: … Người dùng: … Tính năng chính: … Ràng buộc: (ngân sách, công nghệ bắt buộc, deadline) … Hãy bắt đầu Phase 1.
4. PM sẽ đi qua các phase:
   khởi tạo → BA phân tích (**PM hỏi bạn các câu Blocking**) → kiến trúc + DB (**bạn duyệt ADR**) → lập backlog → dev → QA → review (**bạn duyệt nếu còn finding HIGH/CRITICAL**) → báo cáo bàn giao.
5. Theo dõi tiến độ trong `PROJECT_STATUS.md`. Bạn có thể ra lệnh bất cứ lúc nào, ví dụ "chỉ làm requirements, dừng trước kiến trúc" hoặc "dùng opus cho review bảo mật".

## Gọi agent trực tiếp

- "Dùng subagent business-analyst để phân tích yêu cầu sau…"
- `@agent-code-reviewer` (gõ `@` rồi chọn agent) để review các file vừa đổi.

## Model

| Agent | Mặc định | Leo thang |
|---|---|---|
| PM (session chính) | sonnet | opus (`/model opus`) |
| business-analyst, solution-architect, database-architect, frontend-developer, backend-developer, code-reviewer | sonnet | opus |
| qa-engineer | haiku | sonnet |

PM đổi model cho từng lần gọi bằng tham số `model` của Agent tool. Muốn đổi mặc định thì sửa dòng `model:` trong file agent tương ứng.

## An toàn

- `code-reviewer` chỉ có Read/Grep/Glob, không sửa được file.
- `database-architect` không có shell, nên không chạy được SQL vào DB thật.
- `git push`, `git reset --hard`, `git clean`, `rm -rf`, `npm publish`, `docker push` luôn hỏi bạn trước (`.claude/settings.json`). Agent không đọc được `.env` và `secrets/`.
- Ranh giới file của từng agent (agent nào được ghi vào đâu) được ép bằng system prompt, **không** ép bằng quyền. Claude Code không giới hạn tool Write/Edit theo thư mục cho từng subagent. PM kiểm tra lại các file đã đổi trong báo cáo của agent.
