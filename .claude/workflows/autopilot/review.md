# Autopilot — Review (local candidate) playbook

> Nguồn: spec §7 (`review-local-v1`), §9.3 (authority của controller). Dùng bởi adapter `review-local-v1` (kind `review`). Phiên này **chỉ đọc + viết đúng một file report vào staging** — không sửa code, không sửa ticket, không chạm review-state.

## Việc của phiên này

Soi candidate (HEAD của worktree mission so với base branch) rồi **ghi một file report JSON vào staging của chính attempt này**. Controller đọc report đó, tự kiểm rồi tự ghi receipt — worker **không bao giờ** ghi receipt, và cũng không có quyền để làm việc đó.

## Trình tự bắt buộc

1. **Đọc diff candidate**: `git -C <repo> diff <base>...HEAD`, `git -C <repo> log`, `git -C <repo> show`. Không sửa gì, không chạy test, không commit.

   Prompt có mục "## Lựa chọn đã chốt trong mission (chỉ đọc)" ⇒ đối chiếu code với từng lựa chọn ở đó (quyết định có thẩm quyền đã chốt); không ghi `remaining_work` đòi xác nhận lại mục đã có trong bảng.

2. **Chạy rà soát theo skill `pr-gatekeeper-local` + checklist `skills/code-review/references/performing-code-review.md` (mục "Inline mode")** trên đúng diff đó; phiên này không được cấp quyền spawn subagent (`maxInternalSubagents: 0`) nên áp dụng trực tiếp, không gọi Agent.

3. **Rà secret** trên diff: credential/token/khoá API/dotenv lọt vào diff. Kết quả bắt buộc phải có mặt trong report — thiếu nó controller **chặn push** (không phải cảnh báo).

4. **Chấm risk** theo thang 4 mức `low` | `medium` | `high` | `critical`:
   - `low`/`medium` → controller cho phép push tiếp.
   - `high`/`critical` → controller **chặn push**. Chấm đúng mức mình thật sự đo được; không hạ mức để mission đi tiếp — đó là hạ tín hiệu sau khi đo, đúng lớp lỗi dự án đã trả giá.

5. **Khai report trong result JSON — đây là nghĩa vụ BẮT BUỘC của phiên này.** Result phải có field `review_report` đúng shape dưới đây. Thiếu nó ⇒ controller **từ chối attempt** (`rejected`, ticket không `done`) — không phải cảnh báo. Sai shape (vd `risk: "ok"`) ⇒ `contract_error` ngay ở tầng schema.

6. **Có thể ghi kèm bản sao report vào đường dẫn quy ước** — `.avatar/attempt-output/<run_id>/review-report.json`, ghi trực tiếp bằng Write. Tên file và vị trí là **cố định** (controller tự dựng từ `run_id`, không hỏi worker). Controller dùng bản trong result; bản file chỉ để **đối chiếu** — hai bản lệch nhau thì controller ghi nhận sự lệch.

   `<run_id>` lấy nguyên văn từ binding của phiên (`.claude/state/autopilot-binding.json`), như mọi giá trị định danh khác.

   **KHÔNG** ghi ra ngoài staging: `review-staging/` ở control root là của controller, worker không có quyền và không được thử.

   File **không thay được** `review_report` trong result: ghi file mà quên field trong result ⇒ vẫn bị từ chối ở bước 5 (nguồn kết quả duy nhất là terminal result của phiên, H12).

7. **KHÔNG khai report này trong `evidence[]`.** `evidence[]` mang nghĩa "tôi đã chạy recipe đã duyệt X" — controller chạy lại recipe đó để kiểm và **từ chối attempt** nếu recipe không có trong `verification-profile.json`. Report review là artifact, không phải kết quả recipe. Phiên này để `evidence: []` trừ khi thật sự có chạy một recipe đã duyệt.

## Shape của report (bắt buộc, dùng chung cho `review_report` trong result và file `review-report.json`)

```json
{
  "risk": "low",
  "secret_scan": { "verdict": "clean", "findings": 0 },
  "evidence_hashes": []
}
```

Trong result, khối này nằm ở field `review_report` (xem `templates/autopilot/result.schema.json`) — schema `strict`, không nhận field lạ.

- `risk`: đúng một trong `low` | `medium` | `high` | `critical`. Giá trị lạ ⇒ controller chặn push.
- `secret_scan.verdict`: mô tả ngắn kết quả rà (vd `clean`, `findings_present`); `secret_scan.findings`: số phát hiện. **Thiếu cả object này ⇒ chặn push.**
- `evidence_hashes[]`: tuỳ chọn, để `[]` nếu không có. Không bịa hash (cùng nguyên tắc `sha256` placeholder trong `session-prompt.tpl.md`).

## Không làm

- Không sửa code, ticket, BLUEPRINT/PLAN, `verification-profile.json`.
- Không ghi vào `review-staging/`, `review-state/`, hay bất kỳ đường nào ngoài staging của attempt.
- Không coi "đã viết report" là xong nếu result thiếu `review_report` — attempt bị **`rejected`** (result hợp lệ nhưng thiếu nghĩa vụ của adapter này), ticket KHÔNG `done`. Khác với thiếu hẳn khối JSON cuối: đó là `contract_error` (không có result nào để đọc), như mọi adapter khác.
