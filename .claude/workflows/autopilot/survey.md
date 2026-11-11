# Autopilot — Survey (brownfield) playbook

> Nguồn: spec §12. Dùng bởi adapter `survey-v1`. Áp dụng khi mission chạm codebase đã có (brownfield); vẫn hợp lệ khi mission nhỏ/greenfield thì các bước co lại tương ứng ("Cỡ việc tự co" — xem cuối file).

## Trình tự bắt buộc

1. **Checkout đúng base SHA đã ghi** trong mission (base_sha ở init/binding). Source checkout của người dùng có thay đổi chưa commit **không bị stash/reset**; báo rõ các thay đổi đó không thuộc baseline. Nếu blueprint cần các thay đổi đó, yêu cầu người chọn một checkpoint có thể tái lập được (commit/tag) thay vì tự ý dùng working tree bẩn.

2. **Index GitNexus đúng execution_repo**, ưu tiên CLI helper chạy ở chế độ index-only. Nếu dùng `avatar gitnexus analyze <registered-name> --non-interactive` thì phải resolve đúng về repo của mission; kiểm meta/index head thực tế (không tin exit code 0 của wrapper là bằng chứng đủ).

3. **Survey chỉ đọc source** và chạy baseline recipe với quyền `local_test` (không có quyền ghi ngoài staging). Output `CURRENT_STATE` và gap analysis xuất vào staging (`.avatar/attempt-output/<run_id>/`), không ghi trực tiếp vào worktree tracked. **Ghi file staging (`CURRENT_STATE.md`, gap analysis draft) trực tiếp bằng Write/Edit vào `.avatar/attempt-output/<run_id>/` — KHÔNG khai qua `proposed_changes` trong result.** `proposed_changes` chỉ dành cho mutation TICKET (`op`/`target`/`content` khớp ticket schema, xem `result.schema.json`); `content` một file markdown không phải ticket-shaped object sẽ bị supervisor từ chối áp (content không khớp ticket schema). Chỉ liệt kê đường dẫn file staging trong `evidence[]`/`summary`, không đưa vào `proposed_changes`. Không gọi nguyên `/avatar:review:codebase` interactive rồi để nó tự "cải thiện" code trước khi có plan — review chỉ đọc/báo cáo ở bước này.

4. **CURRENT_STATE** ghi theo cấu trúc:
   - Tóm tắt business ở trên (ngắn, cho người không đọc code).
   - Evidence kỹ thuật + `path:line` ở dưới (kiến trúc, module/contract liên quan, auth/data flow, test hiện có, nợ kỹ thuật trong scope).
   - Phân biệt rõ source/config **local** với trạng thái **remote đã probe** (đừng lẫn "code nói vậy" với "server trả lời vậy").

5. **Đo test sẵn có**: lưu command, env, commit, report, danh sách failures. Chạy toàn bộ suite nếu khả thi; nếu không chạy được phải ghi lý do cụ thể và liệt kê phần còn thiếu — **không** gọi đó là "baseline xanh" khi chưa chạy thật. Exception ngoài scope phải được G2 duyệt; failure mới phát sinh trong scope vẫn block dù có exception cũ.

6. **Repo chưa có test ở vùng sắp thay đổi**: tạo characterization testcase trước implementation — test khoá lại hành vi hiện tại, tách biệt rõ với test hành vi mới (mục tiêu blueprint). Không vô tình "khoá" luôn bug mà blueprint yêu cầu sửa.

7. **Gap analysis** giữ/sửa/thay/thêm thành **bản nháp đề xuất sửa** `BLUEPRINT.tpl.md`/`PLAN.tpl.md` — ghi trực tiếp bằng Write/Edit vào staging (`.avatar/attempt-output/<run_id>/`), liệt kê trong `evidence[]`/`summary` của result; **KHÔNG qua `proposed_changes`** (field đó chỉ dành cho mutation TICKET). Supervisor đọc bản nháp trong staging, validate rồi mới áp vào BLUEPRINT/PLAN thật sau gate G2. Gom câu hỏi + resource amendment thành **một post** với request IDs; câu ảnh hưởng AC/authority chưa có đáp án thì chờ (không bắt buộc hỏi nếu source/blueprint đã đủ trả lời).

8. **Khảo sát git host/policy và release thực tế** (read-only): merge-trigger hay tag/job/command kích hoạt deploy, migration chạy trước/sau app, target IDs thật. Việc này phục vụ hoàn thiện resource profile G1 trước G3 — không tự suy Supabase/cloud project từ config repo khi workspace có nhiều project khác vai (xem `notes/orientation.md` ở workspace root, ví dụ 2 Supabase project tách vai của chính team này).

## Quyết định mở của BLUEPRINT ⇒ acceptance `needs_decision`

Ticket đề xuất (gap analysis, bản nháp PLAN) chạm tới một mục trong `## Quyết định mở` của BLUEPRINT ⇒ ghi thành acceptance đúng dạng: "gặp quyết định <X> ⇒ trả `needs_decision` (options + `recommended_option_id`)". Worker đọc ticket như nguồn sự thật, mà chỉ controller áp ủy nhiệm G0 (`principles.md` mục 1).
- CẤM ghi "tự quyết theo G0" hay "theo `decision_policy`" vào gap analysis/ticket đề xuất: lời giao đó biến thành worker tự áp G0, controller escalate plan có acceptance như vậy.
- Acceptance không nhắc G0 (kể cả để phủ định) — controller so chữ, không đọc ý.
- Mục còn mở: không đề xuất vị trí file hay `allowed_paths` của riêng một phương án — không chốt một phương án qua `allowed_paths`; ticket đề xuất phủ mọi phương án, vị trí là một option của câu `needs_decision`.

## Cỡ việc tự co

Blueprint vài dòng cho một feature nhỏ vẫn hợp lệ: survey khoanh vùng hẹp, plan ít ticket; G2 vẫn cần duyệt (người hoặc Claude ủy nhiệm) sau khi plan xong (v1 chưa xác định được việc destructive/migration nên uỷ nhiệm ở G0 không còn waive G2). Dù nhỏ, vẫn phải đi đủ qua contract (ticket, verifier, gate cần thiết) — không bỏ bước vì "việc nhỏ".

## Bảng kiểm theo loại thay đổi (verification matrix)

Nguyên liệu đã có sẵn từ bước 5 (baseline test report) — bước này chỉ bắt **ghi
thành bảng**, để người sau biết "đổi gì thì kiểm gì" mà không phải đọc lại cả
survey.

| Loại thay đổi | Lệnh/recipe kiểm | Đã chạy thử? | Thời gian |
|---|---|---|---|
| (vd) logic backend | `recipe_id` trong `verification-profile.json` | có/không | ~Xs |

**Luật:**
- Mỗi dòng phải do agent **chạy thử ít nhất một lần** trong phiên survey — **KHÔNG
  suy từ `package.json`/CI config**. Chưa chạy thì ghi "chưa" ở cột "đã chạy thử",
  đừng bỏ trống và đừng đoán thời gian.
- Cột "lệnh/recipe" trỏ `recipe_id` **đã có trong `verification-profile.json`**.
  Survey **không** được tự thêm recipe mới — recipe ngoài profile bị
  `checkRecipeIsApproved` từ chối ở verifier.
- Mục **"Chưa xác minh"** đi kèm, **không được rỗng**: vùng nào của thay đổi chưa
  có lệnh nào phủ. Rỗng nghĩa là khai "mọi thứ đều có test" — gần như luôn sai, và
  đúng điều cấm về báo cáo thiếu phần giới hạn.

## Output bắt buộc (vào staging, supervisor áp)

- `CURRENT_STATE.md` draft
- Gap analysis draft + đề xuất sửa BLUEPRINT/PLAN (staging; supervisor áp sau G2, KHÔNG qua `proposed_changes`)
- Danh sách request IDs (câu hỏi + resource amendment gộp một post)
- Baseline test report (command/env/commit/report path)
- Result: `proposed_tickets` luôn `[]` — survey không tạo ticket (chỉ worker plan tạo, qua `proposed_changes`); ticket đề xuất chỉ nằm trong bản nháp gap analysis (staging). Khác rỗng ⇒ done bị từ chối (`proposed_tickets_rejected`), tính **một lần thất bại** (`counted_failures` + 1): ticket về `todo`, attempt kế nhận lý do ở mục "Lần trước bị từ chối vì"; hết `max_counted_failures` ⇒ `blocked` (dogfood chat-drive run 2, F-73).
- **Bảng kiểm theo loại thay đổi** (verification matrix) + mục "Chưa xác minh" (xem trên)
