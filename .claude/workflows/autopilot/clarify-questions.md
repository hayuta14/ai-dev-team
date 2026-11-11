# Autopilot — Clarify: sáu nhóm câu hỏi (startbuild)

> Dùng bởi `commands/avatar/startbuild.md` bước Clarify (lô 2, **sau** khi có BLUEPRINT draft).
> Phỏng vấn **trước** draft (nhánh A0) và triage nhánh B nằm ở `startbuild-interview.md`. Nguồn: spec §13.
> Chỉ hỏi điều **còn thiếu** so với blueprint đã đọc — không hỏi lại điều blueprint đã trả lời rõ.

## Nguyên tắc lô câu hỏi

- Tối đa **10 câu/lô**, tối đa **2 lượt** (lô 1 → người trả lời → lô 2 nếu còn thiếu → chốt).
- Mỗi câu có **default** và **hệ quả nếu dùng default** — không để câu hỏi trần không có phương án dự phòng.
- Thiếu sót ảnh hưởng AC/authority mà sau 2 lượt vẫn chưa có đáp án ⇒ chuyển thành **request** (G0/resource-request), không tự đoán cho đủ hạn nộp.
- Câu hỏi ngoài 6 nhóm dưới đây (tò mò kỹ thuật không ảnh hưởng scope/AC) không hỏi ở bước này.
  Ngoại lệ duy nhất: câu ủy nhiệm `a11-decision-policy` đi cùng lô này khi CLI có cờ
  `decision_policy` (bảng + luật ở `startbuild-interview.md` "Nhánh A0 — lô 2").

## Sáu nhóm

### 1. Người dùng / giá trị (user & value)
- Ai là người dùng chính, kịch bản dùng chính là gì?
- Giá trị/kết quả mong đợi đo bằng gì (hành vi quan sát được, không phải "code chạy")?
- Default: suy từ mô tả blueprint hiện có, ghi rõ "default được ủy nhiệm" nếu bỏ qua câu.

### 2. Dữ liệu / danh tính (data & identity)
- Dữ liệu nào được đọc/ghi, thuộc identity/tenant nào?
- Có PII/dữ liệu nhạy cảm không? Cần ẩn danh hoá/redact ở đâu?
- Default: coi là không có PII mới ngoài phạm vi hiện có của repo, ghi rõ giả định.

### 3. An toàn / lạm dụng (safety & abuse)
- Ai có thể lạm dụng feature này, giới hạn rate/quyền nào cần?
- Có hành động phá hoại/destructive nào (xoá, ghi đè, revert) cần xác nhận thêm không?
- Default: áp policy an toàn nghiêm nhất hiện có trong repo (không nới lỏng ngầm).

### 4. Vào / ra phạm vi (in/out scope)
- File/module/allowed_paths nào **trong** scope, cái gì rõ ràng **ngoài** scope?
- **Tài nguyên NGOÀI repo nào mission được phép đụng?** (channel Mattermost, git remote,
  project Supabase, bucket, DB...) → đi thẳng vào `resource_names` của init request.
  Đặt tên dạng `<loại>:<định danh>`, vd `mattermost:test-avatar-po`, `git-remote:origin`.
  Người khai, **worker không ghi được** — đây là ranh giới G2 đo plan (§8 điều kiện 4).
  Không đụng tài nguyên ngoài nào → khai `[]`, hợp lệ, nhưng G2 sẽ cần duyệt (người hoặc Claude ủy nhiệm).
- Có phụ thuộc/breaking change nào cần tách ticket riêng?
- Default: scope hẹp nhất còn thoả acceptance criteria đã nêu; phần rộng hơn → ticket sau.

### 5. Phi chức năng / tiền (non-functional & cost)
- Ràng buộc hiệu năng, uptime, chi phí (nếu chạm resource có phí) là gì?
- Ngân sách được phép cho compute/API calls trong scope này?
- Default: dùng ngưỡng mặc định của `config.schema` (`limits.*`), không tự đặt số mới.

### 6. Vận hành / admin (operations & admin)
- Ai duyệt G0/G1/G2/G3? Kênh Mattermost đã có (channel thử `test-avatar-po` chỉ dùng cho spike, KHÔNG dùng cho mission thật)?
- Môi trường đích và quy trình release hiện có của repo là gì? **Bỏ câu này** nếu `## Deploy target`
  của BLUEPRINT đã điền (startbuild v2 hỏi `a7-deploy` ngay lô 1 — không hỏi lại dưới id khác).
- Default: môi trường thấp rủi ro nhất (`local-only`) cho tới khi G1/G3 mở rộng quyền tường minh.

## Hình dạng câu hỏi (B4) — mỗi câu phải có ID ổn định

Câu hỏi ghi vào `.avatar/interview.json` theo `interview.schema.json`, mỗi câu đủ:

```json
{ "id": "a7-deploy", "title": "Deploy target?", "type": "single",
  "options": ["local-only", "qa", "staging", "production"], "required": true }
```

- `id` **ổn định giữa các lượt** — hỏi lại lượt 2 giữ nguyên id của lượt 1, để câu
  trả lời đã có không bị mất (store giữ lại answer của id còn trong bộ câu hỏi mới).
- `type`: `text` | `single` | `multiple`. `single`/`multiple` **bắt buộc** `options[]`.
- `required: true` ⇒ **chặn dispatch ticket feature** cho tới khi có câu trả lời.
  Đây là lý do phải cân nhắc: đánh dấu required cho câu không thật sự chặn việc sẽ
  treo mission. Câu "biết thì tốt" ⇒ `required: false`.

Người trả lời (Claude ủy nhiệm khi lái từ chat: thêm `--delegated --reason`, xem `chat-drive.md`):

```
@avatar answer <question-id>: <giá trị>
avatar autopilot answer --question <id> --text <giá trị>
```

**Câu hỏi ở bước Clarify này là loại VIẾT TAY.** Còn một nguồn thứ hai: worker
trả `outcome: needs_decision` ⇒ controller tự đẻ MỘT câu, id theo nội dung
`<ticket-id>-needs-decision-<8 hex>` (nội dung khác ⇒ id mới; xem `escalation.md`).
Hai nguồn dùng chung `interview.json` nhưng khác không gian id, nên không đá nhau —
đừng đặt tay id nào có tiền tố `<ticket-id>-needs-decision`.

Hệ thống **KHÔNG tự suy câu trả lời từ `default`** khi câu là `required` — mục
"default + hệ quả" ở trên áp cho câu **không** required (dùng default rồi ghi rõ
giả định), không phải giấy phép tự quyết thay người.

## Output của bước clarify

Mỗi câu chưa trả lời sau 2 lượt: ghi vào `resource-request.tpl.md` hoặc phần "Quyết định mở" của `BLUEPRINT.tpl.md` với default đã áp và hệ quả, không để trống.
