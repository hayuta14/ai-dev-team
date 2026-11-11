# Autopilot — Phục hồi, revert và rollback

> Nguồn: spec §15. Dùng bởi executor=controller cho `revert-v1` và bởi supervisor khi resume sau crash/interrupt. "Biết operation đã làm tới đâu trước khi retry."

## Theo tầng

| Tầng | Phục hồi bắt buộc |
|---|---|
| Process / lease | Supervisor mất nhưng child còn sống: **không spawn thêm**. Xác minh identity (PID + process-start), đợi hoặc dừng group theo saved policy, thu output có thể lấy và đối chiếu worktree. Không giả định `SessionEnd` đã chạy. |
| Attempt | Lưu baseline SHA/tree + inventory **trước** run; forensic gồm tracked/staged/binary patch và archive file mới thuộc attempt. Rollback về checkpoint trước attempt chỉ trên worktree **sở hữu**, sau khi hết writers; giữ runtime và ignored resources. Không `git clean`/`reset` mù lên checkout người dùng. |
| Commit/result | Commit operation intent có run ID, expected tree và trailer. Chết sau commit trước ack: tìm/kiểm commit thực tế rồi hoàn tất receipt — không commit lại hoặc chạy ticket lại. Result tồn tại nhưng chưa verify vẫn phải verify. |
| Ticket revert | Decision đánh giá dependents, migration và commit mapping; tạo revert + retest tickets. Revert theo SHA đã lưu, xử lý squash bằng mapping/replacement patch; conflict thành công việc sửa có test — không coi revert message là bằng chứng đủ. |
| Deploy/migration | Remote đã có thể thành công nhưng thiếu ack: probe pipeline/artifact/schema/migration ledger. Không retry migration/deploy không idempotent khi trạng thái uncertain. Rollback chỉ chạy procedure đã duyệt, kiểm preconditions và smoke sau đó. |
| Control state | Replay record JSONL đủ newline và hợp schema/checksum/seq (§3.4); tail dở được bảo toàn, truncate/flush trước khi ghi tiếp. Record hoàn chỉnh bị hỏng hoặc thiếu event đã nhận ⇒ RECOVERING. Rebuild projections kể cả review-state; verify artifact hashes/receipts. Schema không hỗ trợ thì doctor chặn với đường nâng cấp rõ, không ghi đè state cũ. |

## Kết quả attempt gián đoạn (§15.1)

Với quota/timeout/failure chưa có commit operation được xác minh: bảo toàn forensic rồi phục hồi checkpoint đã chấp nhận. Worker bình thường không commit; nếu thấy commit ngoài controller, scope thay đổi hoặc người can thiệp worktree thì **RECOVERING + escalation**, không tự bỏ commit. Chỉ phần công việc được verifier xác nhận mới trở thành checkpoint; partial progress có thể đề xuất thành ticket nhỏ hơn thay vì tự nhận done.

## Operation `failed` KHÔNG tự chạy lại (§15.1, B2)

Một operation đã có `outcome` thất bại (`push_failed`, `uncertain`, deploy/migration lỗi) **KHÔNG được tự chạy lại dưới cùng idempotency key**. Key ổn định theo **ý định** (mission + kind + correlation), không theo thời gian và không theo nội dung message — nên "dựng lại cùng một ý định ở attempt sau" không đẻ lần gửi thứ hai.

- Muốn thử lại ⇒ phải là **ý định MỚI**: key mới, kèm **lý do** ghi vào journal. Không có lý do thì không có lần thử lại.
- `uncertain` (gửi rồi nhưng mất response) ⇒ **hoà giải trước** (probe thực tại / correlation marker), không gửi mù. Không hoà giải được thì để nguyên `uncertain` cho người xử lý — KHÔNG tự nâng thành `sent`, KHÔNG tự gửi lại. Ngoại lệ duy nhất (root post Mattermost, close-out X1): lookup theo correlation marker **chứng minh được** post không tồn tại (đã liệt kê lùi qua thời điểm tạo mission, đúng bot) ⇒ gửi lại dưới cùng key là an toàn; lookup lỗi/chạm trần/không biết bot ⇒ vẫn `uncertain`. Op `pending` còn sót do process chết giữa POST và ghi `sent` cũng được hoà giải như `uncertain`.
- Ghi đủ vết: mọi lối thoát đã **qua** ý định thực thi phải có cả `operation_intent` lẫn `operation_result`. Lối thoát **trước** khi ý định hình thành (policy từ chối, không dựng được candidate) thì KHÔNG ghi intent — ghi vào đó là bịa ra một lần thử chưa từng xảy ra.

## Pause, abort và thu hẹp scope (§15.2)

- **Pause**: giữ mission và state, drain/interrupt theo §6; run/resume tiếp tục đúng điều kiện gate/quota còn hiệu lực.
- **Abort trước remote side effect**: dừng worker, phục hồi phần attempt dở, giữ nhánh/artifact để tra cứu; đánh dấu `ABORTED` sau cleanup. Không xoá nhánh/worktree tự động.
- **Abort sau merge/migrate/deploy**: STOPPING → reconcile → ROLLING_BACK nếu có procedure hợp authority. Không có đường quay lui đã duyệt hoặc rollback fail ⇒ WAITING_HUMAN với trạng thái môi trường thật — không tuyên bố "nhánh nền chưa bị đụng". `ABORTED` chỉ dùng khi hậu quả đã được xử lý/chấp nhận và ghi receipt; `DONE` không dùng cho một rollback do abort.
- **Giữ phần hoàn chỉnh, kết thúc sớm**: redirect thu hẹp scope → decision điều chỉnh tickets/AC → TESTING → REVIEWING → G3 → release. Lát đã verify là nền chạy được, nhưng vẫn phải kiểm tích hợp lại sau khi bỏ feature/dependency.

## Không làm

- Không diễn giải `session_id` thành PID hoặc xoá lock không rõ chủ (§9.4).
- Không chạm checkout người dùng khi cleanup worktree.
- Không copy PID lock rồi chạy trên máy khác — chuyển máy phải theo quy trình chuyển quyền/tài nguyên riêng.
