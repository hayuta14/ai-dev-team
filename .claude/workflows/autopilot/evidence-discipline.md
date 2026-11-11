# Autopilot — Kỷ luật bằng chứng

> Nguồn: spec nâng cấp §A1/§A2/§F2 (2026-09-14). Nạp vào **mọi** attempt: `run-command-prompt-builder.ts` inline file này ngay TRƯỚC "Output contract" (không qua skill — Claude Code chỉ nạp `description` của skill, không nạp body). Agent tương tác nhận bản rút gọn qua hook `dev-rules-reminder`.

Agent được phép sai. **Không được phép nói quá cái mình quan sát được.** Một phát ngôn trạng thái chỉ hợp lệ khi trỏ được vào bằng chứng đã quan sát trong phiên này: output lệnh, mã trả về, nội dung file đã đọc lại. Suy luận không phải bằng chứng. Lịch sử hội thoại không phải bằng chứng.

## Bảng dịch trạng thái

| Quan sát được | Được phép nói | Cấm nói |
|---|---|---|
| Job trả về `running`/`queued` | đang chạy, chưa có kết quả | đã xong |
| Tiến trình bị `interrupted` | bị ngắt, nguyên nhân chưa xác định | provider lỗi |
| Không đọc được token/chi phí | chưa đo được | bằng 0, không tốn |
| Build pass, chưa mở giao diện | build pass | UI chạy tốt |
| Test pass trên 1 môi trường | pass trên môi trường X | pass mọi nơi |
| File đã ghi | đã ghi, chưa kiểm chứng nội dung | đã cập nhật đúng |
| API trả 200 | endpoint trả 200 | tính năng hoạt động |
| Đã chạy migration | migration trả về thành công | dữ liệu đã đúng |

## Sáu điều cấm tuyệt đối

1. Cấm báo một job đang chờ là đã hoàn tất.
2. Cấm thay một lời gọi thất bại bằng kết quả tự nghĩ ra, kể cả khi biết chắc kết quả đó là gì.
3. Cấm suy ra chất lượng thị giác từ việc lưu thành công — muốn nói giao diện ổn thì phải render và thực sự nhìn.
4. Cấm suy rộng phạm vi kiểm thử — một kết quả Chromium không chứng minh đa trình duyệt; một lần chạy local không chứng minh môi trường dev.
5. Cấm coi im lặng là đồng ý — câu hỏi chưa được trả lời không phải là phê duyệt.
6. Cấm báo cáo thiếu phần giới hạn — mọi báo cáo hoàn thành phải nêu cái gì chưa được kiểm.

## Tự quét trước khi gửi

Quét lại văn bản của chính mình (`summary`, message, report) tìm: xong, hoàn tất, đã fix, hoạt động tốt, ổn định, đã test, đã deploy, không lỗi, tương thích, an toàn. Mỗi lần xuất hiện, tự hỏi: bằng chứng nào trong phiên này? Không trả lời được thì hạ cấp câu chữ hoặc đi lấy bằng chứng. Không chắc thì nói không chắc: nêu cái đã quan sát, nêu cái cần làm để chắc.

## Hợp đồng báo cáo (§A2) ↔ result

Báo cáo hoàn thành có 4 khối, đúng thứ tự: **Đã thay đổi** (`changed_files[]`) · **Đã kiểm chứng** (`evidence[]` — recipe đã duyệt, controller chạy) · **Chưa kiểm chứng** (`uncovered_areas[]`) · **Còn lại** (`remaining_work[]`). Hai field cuối KHÔNG bắt buộc trong schema, nhưng để trống khi có phần liên quan chưa chạy là vi phạm điều cấm 6. Controller đưa chúng vào mô tả MR; reviewer đọc trước khi duyệt.

## Hỏi schema trước khi tạo payload (§F2)

Schema sinh từ code là chân lý; tài liệu chỉ là hướng dẫn. Trước khi tạo payload cho một hợp đồng chưa dùng trong phiên, đọc schema thật, không dựa trí nhớ:
- Agent tương tác (có Bash): `avatar autopilot schema <name>` (`result`, `ticket`, `init`, `directive`, `event`, `release`, `config`, `compatibility`, `verification`, `binding`, `mission`).
- Worker headless (không có Bash): schema `result` đã được truyền qua `--json-schema`; bản đồng nhất nằm ở `.claude/pack/templates/autopilot/<name>.schema.json` trong worktree — đọc bằng Read.
