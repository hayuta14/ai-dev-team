# Development Rules

Use the skills whose descriptions match the task.
Follow YAGNI (You Aren't Gonna Need It), KISS (Keep It Simple, Stupid) and DRY (Don't Repeat Yourself).

## Cắt khối lượng bơm vào context
- **Output tool > 8.000 ký tự ⇒ ghi ra file**, context chỉ giữ đường dẫn + vài dòng đầu. Ghi vào scratchpad phiên hoặc `.claude/state/`, KHÔNG ghi vào cây repo (tránh lọt commit). Ngưỡng dẫn từ đo thật: chạm ~10% số lần gọi tool nhưng phủ ~61% tổng khối lượng.
- **Đọc file bằng `offset`/`limit`**, không đọc lại file KHÔNG đổi trong cùng phiên. ⚠️ **BẮT BUỘC đọc lại** khi `mtime`/hash đã đổi hoặc ngay sau khi chính mình vừa ghi — bỏ vế này là vá đè lên bản cũ.
- **Việc "đọc nhiều để tìm" đẩy cho subagent**, cha nhận tóm tắt. Chỉ đẩy khi phải quét nhiều file/chưa biết đích; đọc 1-2 file đã biết đường dẫn thì tự đọc — dựng agent có giá.
- **Gộp lệnh để giảm số content block mỗi lượt**: nhiều lệnh Bash độc lập gộp một khối, output lớn ra file rồi đọc lát. Block tích luỹ mỗi lượt đã vượt xa cửa sổ lookback của cache ⇒ block thừa đẩy prefix ra ngoài cửa sổ, **mất cache im lặng**.

## Tìm kiếm trong shell: dùng `rg`, không dùng `grep`
- `grep`/`egrep`/`fgrep` bị **deny** trong workspace Avatar (`permissions.deny` do `avatar sync` mang từ pack) — gọi là bị từ chối. Dùng `rg` hoặc tool Grep (nếu phiên có). Đừng lách bằng `/usr/bin/grep`. `git grep` vẫn dùng được.
- Lọc output qua pipe: `cmd | rg pattern`.
- `rg` trong Bash của Claude Code có thể chỉ là shell function (máy không cài rg hệ thống) ⇒ đừng gọi qua `xargs`/`find -exec`/`env`/subprocess — dùng `rg Y $(rg -l X)` hoặc `-g`/`-t` thay cho `find`.
- ⚠️ Cờ khác nghĩa với grep: `rg` mặc định đệ quy và bỏ qua file trong `.gitignore`/file ẩn (`-uu` để quét hết) · `-r` của rg là **replace**, không phải recursive · `-E` của rg là **encoding** (regex mở rộng là mặc định) · chuỗi literal (có `(`, `*`, `.`) dùng `-F`.
- Hay dùng: `-n` số dòng · `-i` không phân biệt hoa thường · `-c` đếm (⚠️ không khớp thì KHÔNG in gì, grep in `0`; nhiều file thì bỏ file 0 dòng) · `-l` chỉ tên file · `-g '*.ts'` lọc glob · `-t py` lọc loại file.

## General
- **File Naming**: Use kebab-case for file names with a meaningful name that describes the purpose of the file, doesn't matter if the file name is long, just make sure when LLMs read the file names while using Grep or other tools, they can understand the purpose of the file right away without reading the file content.
- **File Size Management**: Keep individual code files under 200 lines for optimal context management
  - Split large files into smaller, focused components/modules
  - Use composition over inheritance for complex widgets
  - Extract utility functions into separate modules
  - Create dedicated service classes for business logic
- `gh` reaches only the GitHub mirror (`github` remote); every `src/<repo>` origin is GitLab `git.nal.vn`.
- Use `psql` bash command to query Postgres database for debugging if needed
- Images, screenshots, PDFs: read them with the Read tool (Claude vision). Videos: extract still frames with `ffmpeg` (`media-processing` skill), then Read them. Audio: ask the user for a transcript. No external vision/generation API
- Use `media-processing` skill for editing images, videos, audio (ImageMagick/FFmpeg)
- Use the `debugging` skill for root-cause analysis of bugs.
- **[IMPORTANT]** Follow the codebase structure and code standards in `./docs` during implementation.
- **[IMPORTANT]** Do not just simulate the implementation or mocking them, always implement the real code.

## Code Quality Guidelines
- Read and follow codebase structure and code standards in `./docs`
- Don't be too harsh on code linting, but **make sure there are no syntax errors and code are compilable**
- Prioritize functionality and readability over strict style enforcement and code formatting
- Use reasonable code quality standards that enhance developer productivity
- Use try catch error handling & cover security standards
- Use `code-reviewer` agent to review code after every implementation

## Pre-commit/Push Rules
- Run linting before commit
- Run tests before push (DO NOT ignore failed tests just to pass the build or github actions)
- Keep commits focused on the actual code changes
- **DO NOT** commit and push any confidential information (such as dotenv files, API keys, database credentials, etc.) to git repository!
- Create clean, professional commit messages without AI references. Use conventional commit format.

## Code Implementation
- Write clean, readable, and maintainable code
- Follow established architectural patterns
- Implement features according to specifications
- Handle edge cases and error scenarios
- **DO NOT** create new enhanced files, update to the existing files directly.

## Danh sách việc trong lượt (📋)
Việc có từ 3 bước trở lên: in 1 dòng riêng dạng `📋 Việc: ✓ <đã xong> · ● <đang làm> · ○ <chưa làm>`, nguyên dạng — không bọc backtick/bold/list, ký tự 📋 nằm ngay đầu dòng (extension Office đọc dòng này từ transcript chat cho card "Việc trong lượt"). Ví dụ đúng nguyên dòng:
📋 Việc: ✓ Đọc code · ● Sửa lỗi · ○ Chạy test
- In lại dòng đó mỗi khi một bước đổi trạng thái (bắt đầu làm hoặc làm xong).
- Tối đa 12 mục, mỗi mục ≤ 120 ký tự; ký hiệu đúng ✓ ● ○, ngăn mục bằng ` · `.
- Chỉ in trong chat — không ghi vào file, commit hay PR.

## Tồn đọng của phiên (📌)
Phiên có từ 2 hạng mục chưa xong trở lên (việc user giao, nợ chưa trả, việc chờ user nghiệm thu): in 1 dòng riêng dạng `📌 Tồn đọng: ✓ <đã xong> · ● <đang làm> · ○ <chưa làm>`, nguyên dạng — không bọc backtick/bold/list, ký tự 📌 nằm ngay đầu dòng (extension Office đọc dòng này từ transcript chat cho card "Tồn đọng của phiên"; khác `📋 Việc:` chỉ nằm trong một lượt, card này giữ bản mới nhất của cả phiên). Ví dụ đúng nguyên dòng:
📌 Tồn đọng: ✓ Gửi báo cáo · ● Sửa card HUD · ○ Chờ user nghiệm thu
- In lại TOÀN BỘ danh sách mỗi khi có mục thêm, đổi trạng thái hoặc xong — dòng mới nhất thay hẳn dòng cũ.
- Mục ✓ giữ suốt phiên để user theo dõi việc đã xong; chỉ khi chạm trần 20 mục mới bỏ mục ✓ cũ nhất (Office vẫn nhớ mọi mục từng ✓ trong phiên).
- Tối đa 20 mục, mỗi mục ≤ 120 ký tự; ký hiệu đúng ✓ ● ○, ngăn mục bằng ` · `.
- Chỉ in trong chat — không ghi vào file, commit hay PR.
