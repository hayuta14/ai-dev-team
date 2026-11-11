# Autopilot — Session contract (chạy Claude Code headless)

> Nguồn: spec §6.2 (contract chạy Claude Code) + §5.3 (kết quả worker). Playbook cho supervisor/runner (P2 TS) và cho worker hiểu mình đang chạy dưới contract nào.

## Spawn

- Spawn binary bằng argv array, **không** shell interpolation; prompt truyền qua stdin có giới hạn (`limits.prompt_max_kib`), đóng stdin đúng thời điểm.
- `cwd = mission_workspace`; `repo_root` tuyệt đối truyền trong prompt/adapter; git luôn dùng `git -C <repo_root>`.
- Dùng `claude -p` ở chế độ load Avatar bình thường (KHÔNG `--bare` — bản đã kiểm bỏ hooks/context và không đọc OAuth subscription).
- Output JSON hoặc `stream-json`/schema theo capability manifest (S1); `--verbose` khi dùng stream. `--include-hook-events` chỉ dùng cùng `--output-format stream-json`.
- Model: luôn truyền `--model <worker_model>` (config `worker_model`, default `claude-sonnet-5`, D03) — không phụ thuộc model mặc định của user, không tự `claude update`.

## Env bắt buộc

`AVATAR_AUTOPILOT=1`, `AVATAR_NON_INTERACTIVE=1`, `AVATAR_MISSION_ID`, `AVATAR_TICKET_ID`, `AVATAR_RUN_ID`, `AVATAR_REPO_ROOT`. Supervisor cấp session UUID nếu binary hỗ trợ (`--session-id`) và lưu mapping. Không ghi đè biến nội bộ Claude (`ANTHROPIC_*`, provider/auth selectors) bằng giả định chưa spike — doctor xác nhận auth/provider thực tế trước; xung đột thì fail rõ.

## Binding (trước spawn)

Controller ghi atomic `<mission_workspace>/.claude/state/autopilot-binding.json` theo `binding.schema.json`: `session_id` do supervisor cấp, mission/ticket/run id, `kind`, `allowed_paths`, `capabilities`, `issued_at`/`expires_at`, `hash`. Hook đọc qua `CLAUDE_PROJECT_DIR`, so `session_id` trong stdin với file; thiếu file, hết hạn, lệch session hoặc sai schema ⇒ hook giữ nguyên hành vi phiên thường (inert). `AVATAR_AUTOPILOT` chỉ là tín hiệu **chọn nhánh đọc** binding, tự nó không cấp quyền gì.

## Permission

- Profile v1: `--permission-mode dontAsk` **cộng** allowlist theo `kind` (từ `command-adapters.md`), đã thử trên binary ghim.
- Cấm worker: git mutation, sửa control paths, deploy, chỉnh policy.
- Thiếu quyền ⇒ blocked/escalation; **không** dùng bypass-all để biến test tương thích thành xanh. Một lệnh bị từ chối vì sai **dạng** (ghép `;`/`&&`/`|`, `cd … &&`, gọi script của recipe) KHÔNG phải thiếu quyền: chạy lại đúng một lệnh khớp quyền (vd `npm test`) rồi làm tiếp — chỉ blocked khi việc cần một quyền thật sự không được cấp.
- `dontAsk` + prompt **không tự tạo ranh giới filesystem** — sandbox/quyền thật do `allowed_paths` trong binding + verifier diff inventory sau attempt quyết định, không phải do CLI flag đơn thuần.

## Nội dung prompt (§6.2 dòng cuối)

Prompt chỉ chứa: ticket revision, blueprint/plan/phase đã chọn, output dependencies, baseline, quyết định và directives liên quan, playbook cần thiết (ví dụ `principles.md`), output contract. **Không** nạp cả workspace mỗi lần, **không** kế thừa active-plan của phiên người dùng thường. `SessionStart`/`PreCompact` chỉ bind đúng plan của mission đang chạy — xem `templates/autopilot/session-prompt.tpl.md` cho khuôn thật.

## Giới hạn và dọn tiến trình (§6.3)

- Timeout theo `kind` (§18 config); phân biệt startup timeout, deadline công việc, rollout timeout.
- Đọc output stream bằng buffer giới hạn (`limits.line_max_mib`, `limits.raw_log_max_mib`, `limits.stderr_ring_kib`), redaction trước khi lưu.
- Hết deadline: yêu cầu interrupt/graceful stop → chờ grace (`shutdown_grace_sec`) → TERM/KILL cả process group. Chỉ cleanup worktree khi không còn process của attempt có thể ghi.
- SIGKILL có thể không chạy `SessionEnd` — lease/journal là đường recovery, không phải hook lifecycle.

## Kết quả worker (§5.3) — tóm tắt, xem `result.schema.json` cho full contract

- Nguồn kết quả **duy nhất** là terminal result của phiên Claude CLI: `structured_output` nếu binary trả, không có thì object JSON cuối trong `result` text (có hay không có fence — worker viết nó thành khối ```json cuối); normalize theo `result.schema.json`. Controller không đọc file result nào — worker ghi result ra file thay cho câu trả lời ⇒ `missing_result_event`/`no_result_json_found`, attempt bị từ chối (H12, 2026-09-29).
- Không dùng marker tự do trong stdout làm bằng chứng "done".
- `outcome`: `done` | `failed` | `blocked` | `needs_decision`. `blocked` cần `reason`/`capability`/`request`; `needs_decision` cần `options` + khuyến nghị.
- `proposed_changes` có `op = create|amend|cancel|supersede`, `target`, `expected_revision`, `replacement_ids` hoặc nội dung artifact. Worker **không tự sửa** ticket/BLUEPRINT; supervisor validate, tăng revision, áp proposal, append quyết định.
- Supervisor tin session/run identity **mình đã cấp** và transport đã quan sát; không tin worker tự khai ID.
- Attempt number tăng ở **mọi** physical run kể cả rate limit; `counted_failures` là bộ đếm riêng (không tính quota/network vào đây — xem `escalation.md`).
