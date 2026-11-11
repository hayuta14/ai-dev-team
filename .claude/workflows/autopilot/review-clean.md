# Autopilot — Review context sạch (reviewer thứ hai)

> Nguồn: spec nâng cấp §C2. Dùng bởi adapter `review-clean-v1` (kind `review`). Đây là phiên review **THỨ HAI**, chạy sau `review-local-v1` trên cùng candidate. Chỉ đọc + ghi đúng một file report vào staging.

## Vì sao có phiên này

`review-local-v1` nhìn thấy `plan_path`, `phase_path` và playbook `review.md` — tức là khung nhìn của chính phiên đã viết code. Reviewer đọc lại lập luận của tác giả thì có xu hướng tái tạo kết luận của tác giả, kể cả chỗ tác giả sai. Phiên này cố ý **không** được cấp mấy thứ đó.

Cái bạn nhận: **diff candidate** + **hợp đồng của ticket** (`outcome`, `acceptance[]`, `coverage_limits[]`). Cái bạn KHÔNG nhận, và đừng đi tìm: plan, phase file, câu hỏi/lời kể của bên implement, lịch sử phiên implement. `run-command-prompt-builder.ts` lược chúng khỏi cả phần văn xuôi lẫn khối JSON ticket.

**Không có chúng là chủ ý, không phải thiếu sót.** Đừng coi việc thiếu ngữ cảnh là lý do để hạ mức rủi ro hay để nói "chắc có lý do nào đó ở plan". Nếu diff không tự giải thích được nó làm đúng hợp đồng, đó là một phát hiện, không phải một khoảng trống cần lấp bằng suy đoán.

Prompt có mục "## Lựa chọn đã chốt trong mission (chỉ đọc)" (khi mission đã chốt quyết định): mỗi dòng là mã QĐ, ticket, option + nhãn, nguồn — không có câu hỏi. Bảng này là một phần hợp đồng như `acceptance[]`: đối chiếu diff với lựa chọn ở đó; không đi tìm interview.json/journal, không ghi `remaining_work` đòi xác nhận lại mục đã có trong bảng.

## Trình tự bắt buộc

1. **Đọc hợp đồng trước, diff sau.** Đọc `outcome` + `acceptance[]` + `coverage_limits[]` trong prompt. Đó là thứ candidate phải đáp ứng. Chưa đọc xong hợp đồng thì chưa mở diff — đọc ngược lại sẽ khiến bạn đánh giá "code này viết có khá không" thay vì "code này có giao đúng cái được yêu cầu không".

2. **Đọc diff candidate**: `git -C <repo> diff <base>...HEAD`, `git -C <repo> log`, `git -C <repo> show`. Không sửa gì, không chạy test, không commit.

3. **Đối chiếu từng dòng `acceptance[]` với diff.** Mỗi điều kiện, trả lời đúng một trong ba: **có bằng chứng trong diff** / **không tìm thấy bằng chứng** / **diff mâu thuẫn với điều kiện**. Dòng đã tick `done: true` kèm `evidence` mà bạn không tìm thấy dấu vết trong diff ⇒ nêu tường minh trong `summary`; đó là đúng loại sai lệch phiên này tồn tại để bắt.

4. **Soi `coverage_limits[]`.** Ticket tự nhận không phủ phần nào. Nếu diff chạm đúng phần đó mà không có test/bằng chứng kèm, nêu ra. Nếu diff phủ nhiều hơn `allowed_paths`, đó là vi phạm scope — verifier đã gác, nhưng vẫn nêu.

5. **Rà secret** trên diff: credential/token/khoá API/dotenv. Bắt buộc có trong report — thiếu ⇒ controller chặn push.

6. **Chấm risk** theo thang `low` | `medium` | `high` | `critical`. `high`/`critical` ⇒ controller chặn push. Chấm đúng mức mình thật sự đo được. **Không hạ mức vì "chắc phiên review thứ nhất đã xem rồi"** — hai phiên độc lập mới có giá trị; đồng ý theo quán tính thì phiên này bằng không.

7. **Khai `review_report` trong result JSON** đúng shape của `review.md` (dùng chung `ReviewReportSchema`). Thiếu ⇒ attempt bị từ chối. Có thể ghi kèm bản sao `.avatar/attempt-output/<run_id>/review-report.json` để đối chiếu (`<run_id>` lấy nguyên văn từ binding); file không thay được field trong result.

8. **`evidence[]` để rỗng `[]`.** Phiên này không chạy recipe đã duyệt nào. Report review là artifact, không phải kết quả recipe (lý do đầy đủ: `review.md` mục 7).

## Bất đồng với phiên review thứ nhất

Bạn **không** đọc verdict của `review-local-v1`, nên không có gì để "đồng ý" hay "phản đối" — cứ chấm độc lập. Controller là nơi đọc cả hai report; hai mức risk khác nhau là **tín hiệu hữu ích**, không phải lỗi cần hoà giải. Đừng cố đoán phiên kia chấm gì để chấm cho khớp.

## Không làm

- Không sửa code, ticket, BLUEPRINT/PLAN, `verification-profile.json`.
- Không đi tìm plan/phase/lịch sử phiên implement bằng Grep/Glob để "có thêm ngữ cảnh" — làm vậy là tự phá mục đích của phiên này.
- Không ghi ngoài staging của attempt; không chạm `review-staging/`, `review-state/`.
- Không approve gate, không commit, không push — phiên này không có quyền đó và không được thử.
