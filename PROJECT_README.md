# AI Dev Team: framework quản lý phát triển phần mềm đa agent

Một repo mẫu cho Claude Code. Session chính đóng vai **Project Manager (PM)**, điều phối **22 subagent chuyên môn** (định nghĩa native trong `.claude/agents/`) và dùng các skill trong `.claude/skills/`. Bạn là chủ dự án và là người ra quyết định cuối cùng.

## Cấu trúc

```
.claude/agents/      22 subagent (xem CLAUDE.md mục 1 để biết vai trò, model và skill của từng agent)
.claude/skills/      40 skill dùng chung; mỗi agent preload hoặc đọc theo bảng "Skills per agent" trong CLAUDE.md
.claude/workflows/   quy tắc dùng chung mà agent tham chiếu (development-rules, test-standards, git-flow, ...)
.claude/settings.json   model mặc định của PM (sonnet) và các quy tắc ask/deny
CLAUDE.md            luật điều phối của PM (workflow, routing model, các mốc cần duyệt)
PROJECT_STATUS.md    backlog, trạng thái task, rủi ro, nhật ký agent (PM cập nhật)
plans/               kế hoạch và báo cáo của agent (tạo khi dùng lần đầu)
requirements/, docs/, database/, testing/   tài liệu dự án (của bộ agent cũ; giữ lại nếu còn dùng)
```

Nhóm agent: Explore (`brainstormer`, `scout`, `researcher`), Plan (`planner`, `debate-*`), Build (`fullstack-developer`, `ui-ux-designer`, `database-*`, `devops-engineer`), Verify (`tester`, `qa-reviewer`, `debugger`, `performance-engineer`), Review (`code-reviewer`, `security-auditor`), Deliver (`docs-manager`, `project-manager`, `git-manager`), Utility (`journal-writer`, `mcp-manager`).

## Dùng cho dự án mới

1. Sao chép repo này, hoặc áp vào repo có sẵn: chép `.claude/agents/`, `.claude/skills/`, `.claude/workflows/`, `.claude/settings.json`, `CLAUDE.md` và `PROJECT_STATUS.md`. Nếu repo đã có `CLAUDE.md`, hãy gộp nội dung, đừng ghi đè.
2. Mở thư mục bằng Claude Code. Gõ `/agents` để kiểm tra đủ 22 agent.
3. Dán định nghĩa dự án và yêu cầu PM bắt đầu.
4. PM đi qua: khởi tạo → scout/researcher/brainstormer (**PM hỏi bạn các câu hỏi chặn**) → planner (**bạn duyệt plan**) → build → verify → review (**bạn duyệt nếu còn finding HIGH/CRITICAL**) → docs và báo cáo bàn giao.
5. Theo dõi tiến độ trong `PROJECT_STATUS.md`.

## Gọi agent trực tiếp

- "Dùng subagent scout để tìm các file liên quan đến …"
- `@agent-code-reviewer` (gõ `@` rồi chọn agent) để review các file vừa đổi.

## Model

Model mặc định nằm ở dòng `model:` trong từng file agent (opus cho brainstormer, planner, debugger, performance-engineer, qa-reviewer, security-auditor, ui-ux-designer, debate-skeptic; sonnet cho phần còn lại). PM đổi model cho từng lần gọi bằng tham số `model` của Agent tool; quy tắc nằm ở CLAUDE.md mục 5.

## An toàn

- Agent chỉ đọc (`scout`, `code-reviewer`, `database-optimizer`, `debugger`, ...) không sửa mã nguồn; chúng chỉ ghi file báo cáo.
- `database-admin` mặc định read-only; lệnh phá huỷ luôn chờ người duyệt. `devops-engineer` chỉ chuẩn bị, chỉ chạy bước đã được duyệt.
- `git-manager` không bao giờ push khi chưa được yêu cầu, không dùng `--no-verify`, và quét secret trước khi commit.
- `git push`, `git reset --hard`, `git clean`, `rm -rf`, `npm publish`, `docker push` luôn hỏi bạn trước (`.claude/settings.json`). Agent không đọc được `.env` và `secrets/`.
- Ranh giới file của từng agent được ép bằng system prompt, **không** ép bằng quyền. PM kiểm tra lại các file đã đổi trong báo cáo của agent.
- Một số agent nhắc tới lệnh `/avatar:*`, hook và `.claude/active-plan` của pack gốc; repo này không có các thứ đó, PM làm các bước tương ứng bằng brief trực tiếp (CLAUDE.md mục 1).
