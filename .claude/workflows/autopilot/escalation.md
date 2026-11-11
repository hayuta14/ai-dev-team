# Autopilot — Escalation playbook

> Nguồn: spec §6.4 (taxonomy lỗi) + §10 nguyên tắc 3. Dùng khi worker/supervisor không thể tự tiến hành đúng contract và cần người quyết.

## Taxonomy lỗi và xử lý (§6.4)

| Loại lỗi | Xử lý |
|---|---|
| `quota` / `rate_limit` | Không tăng `counted_failures`. Bảo toàn attempt và checkout trước SLEEPING; parse reset có timezone hoặc backoff 15→30→60 phút, trần 60. Wake/reason/backoff bền qua restart. |
| `network` / `overloaded` | Retry hạ tầng có giới hạn và backoff; không tính lỗi code. Outage quá 30 phút mà không có đường khác thì escalation. Mattermost notification outage riêng vẫn fail-soft. |
| `auth_expired` | WAITING_HUMAN với hướng dẫn login lại. Không tự mở browser trong worker, không ngủ lặp vô hạn như rate limit, không tự đổi sang API khác. Áp cho cả id_token Google của supervisor (refresh qua `getValidIdToken` + `auth-device`; refresh fail liên tiếp cũng vào WAITING_HUMAN). |
| `permission` / `resource_missing` | Blocked với capability/tên key/đối tượng cần bổ sung. Không thử cách lách policy. |
| `scope_precondition` | Điều kiện tiên quyết nằm ngoài `allowed_paths` (vd test đỏ có sẵn từ ticket khác, file ngoài phạm vi) ⇒ `blocked`, nêu ticket/file gây ra; không mượn nhãn `permission`. |
| `task_failed` / `timeout` | Tối đa 3 counted failures/ticket. Lần kế đưa evidence lỗi đã redact; lần cuối buộc đổi cách tiếp cận. Timeout lần thứ hai: chia ticket trước khi chạy thêm. Fail 3 lần: blocked, đi tiếp ticket độc lập nếu DAG cho phép — trừ khi cửa sổ RED (testcase đã làm suite đỏ, implement của nó chưa xong) giữ ticket đó: `run` dừng với `red_window_conflict: …` kèm lệnh gỡ `avatar autopilot redirect --text "…"`. |
| `contract_error` | Không done; lưu diagnostic và tính failure. Nhiều ticket cùng lỗi protocol thì chặn runner như lỗi hệ thống để sửa contract — không tiêu hết 3 lần retry trên từng ticket riêng lẻ. |
| `state_corrupt` / `unknown_side_effect` | RECOVERING; không retry mutation khi chưa biết hậu quả. Không reconcile được bằng kiểm máy thì escalation kèm operation ID. |

## Nguyên tắc phân loại

- Classifier ưu tiên terminal/error events thật của phiên bản binary ghim; regex fallback chỉ chạy trên vùng lỗi đã xác định (không quét toàn stdout).
- Chữ "429" xuất hiện trong source code, test, hoặc lời model **không phải** bằng chứng Claude bị rate limit.
- Fixture ghi rõ nguồn/version; ưu tiên thứ tự specific trước generic. Raw response phải redact trước khi đưa vào bộ test.

## Khi nào escalation (khác taxonomy lỗi ở trên)

Escalation còn áp dụng khi:
- Cần mở rộng scope ngoài allowed_paths/capabilities hiện có.
- Cần tiền/tài nguyên/quyền/dữ liệu thật ngoài ủy quyền đã cấp.
- Quyết định không đủ thông tin để giữ đúng acceptance criteria (không phải "khó" mà là thiếu input).

## Nội dung post escalation (bắt buộc đủ 4 phần)

1. **Chuyện gì** — mô tả ngắn tình huống, ticket/run liên quan.
2. **Evidence đã thử** — các bước đã làm, kết quả quan sát được (redact secret).
3. **Lựa chọn + khuyến nghị** — ít nhất 1 phương án, có khuyến nghị rõ (không chỉ liệt kê rồi bỏ đó).
4. **Người cần làm gì + request ID** — hành động cụ thể (approve/answer/redirect) và ID để trả lời đúng chỗ.

## Câu hỏi cần người trả lời (B4)

Câu hỏi cần người trả lời phải ghi vào `.avatar/interview.json` theo hình dạng
`interview.schema.json`, mỗi câu đủ 4 trường:

| Trường | Ý nghĩa |
|---|---|
| `id` | Câu viết tay: ID ổn định giữa các lần hỏi lại (vd `q-env`). Câu tự đẻ: id theo nội dung (dưới). Người trả lời trích **nguyên** id này. |
| `title` | Câu hỏi, một dòng. |
| `type` | `text` \| `single` \| `multiple`. `single`/`multiple` **bắt buộc** có `options[]` — câu chọn mà không có gì để chọn là lỗi schema. |
| `required` | `true` ⇒ ticket feature **KHÔNG dispatch** cho tới khi có câu trả lời. |

### Hai nguồn câu hỏi

1. **Người/controller viết tay** — bước Clarify, 6 nhóm ở `clarify-questions.md`.
2. **Tự đẻ từ `needs_decision`** — worker trả `outcome: needs_decision` kèm
   `options[]`; controller dịch thành MỘT câu hỏi cho ticket đó, id theo nội dung
   `<ticket-id>-needs-decision-<8 hex>` (8 hex đầu sha256 của `{summary, options}` đã chuẩn hoá).
   - Câu khác nội dung ⇒ id mới, **không** thừa hưởng câu trả lời nào; câu cũ chưa trả lời bị thay.
     Câu đã trả lời ở lại `interview.json` làm lịch sử, không chặn dispatch.
   - Worker hỏi lặp **đúng câu đã được trả lời** (cùng nội dung ⇒ cùng id) ⇒ 1 counted failure
     `contract_error`, không đẻ câu mới. Lựa chọn đã chốt quay lại prompt ở mục "Quyết định đã
     chốt cho ticket này" — làm theo, không hỏi lại.

### Output contract V2 khi `needs_decision` (mọi mode)

- Mỗi phần tử `options[]` **PHẢI** có `id` (khớp `^[a-z0-9-]{1,32}$` — `OPTION_ID_PATTERN` của CLI,
  duy nhất trong result) + `label` (nhãn cho người đọc) — viết `options[].id` là để người và
  controller trả lời bằng id.
- `recommended_option_id` = id của lựa chọn khuyến nghị (bắt buộc là một id trong `options[]`) —
  chính là phần "khuyến nghị rõ" của mục 3 ở trên.
- Mỗi needs_decision chỉ MỘT quyết định: options[] là các phương án của cùng một câu hỏi. Còn ≥ 2 quyết định mở ⇒ hỏi riêng từng câu, câu thuộc phạm vi ủy nhiệm (mọi cờ boundary_claims = false) trước, câu đổi hành vi ở attempt sau. Một câu đã chốt chỉ chốt đúng option được chọn — quyết định chưa có câu riêng vẫn là quyết định mở.
- `boundary_claims`: khai THẬT 7 cờ boolean `changes_product_behavior`, `out_of_scope`,
  `touches_resources`, `touches_money_or_quota`, `touches_secret_or_deploy`,
  `touches_base_ref_or_approver`, `touches_personal_data_or_compliance` cùng `reversible`.
- Thiếu/trùng/sai dạng id ⇒ verifier **từ chối** result ngay ở tầng schema (issue tại
  `options[i].id`, `contract_error`) — không có đường hỏi theo nhãn thay thế.
- Controller chỉ xét tự áp `recommended_option_id` khi BLUEPRINT đã duyệt G0 khai
  `decision_policy: auto`, `reversible: true`, cả 7 cờ `false` **và** kiểm cứng của controller
  (token tài nguyên/secret/`base_ref`/approver, trần số quyết định) qua — không tin lời khai.
  Còn lại ⇒ hỏi người như trên. Sổ quyết định: `decision-log.md`.
- Quyết định worker **tự làm** (ghi ở `decisions[]`) **KHÔNG** viện G0/`decision_policy` trong 5 key `decisions[].policy`/`decided_by`/`authority`/`basis`/`source` (guard CLI từ chối result, fail-closed); nếu cho rằng lựa chọn thuộc G0 `decision_policy: auto` ⇒ trả `needs_decision` để controller áp (`decision_auto_applied`), không tự áp.

**Câu tự đẻ luôn `required: true`, và cờ đó do CONTROLLER đặt** — worker chỉ cấp
nội dung (`summary` → `title`, `options[]` → lựa chọn), không đổi được mức chặn
theo bất kỳ chiều nào. Lý do là chi phí đo được: ticket sau attempt quay lại
`todo` và scheduler chọn lại ngay ở tick kế, còn `max_attempts_per_mission` mặc
định là `0` (không giới hạn) — câu hỏi không chặn ⇒ worker lặp `needs_decision`
mỗi tick, mỗi tick một phiên trả tiền thật. Câu hỏi chặn ⇒ chạy đúng một lần.

Worker **KHÔNG tự trả lời** được câu hỏi của chính nó: `recordInterviewAnswer`
chỉ nhận directive mang danh tính người (`answered_by`), và worker không có
đường ghi vào inbox directive.

Người trả lời bằng **một** trong hai đường (cả hai ghi vào cùng một chỗ), với **nguyên id** lấy
từ dòng `Dispatch bị chặn …` mà `avatar autopilot run` in ra, hoặc từ `interview.json`
(`avatar autopilot status --decisions` cũng liệt kê câu đang chờ). Câu tự đẻ: giá trị là
**option id** (nhãn chỉ được nhận khi ánh xạ duy nhất về một id):

```
@avatar answer <question-id>: <giá trị>          # Mattermost
avatar autopilot answer --question <id> --text <giá trị>   # CLI local
```

Phiên chat lái mission (`chat-drive.md`) trả lời ủy nhiệm chủ mission bằng
`answer --question <id> --text <option id> --delegated --reason "<căn cứ>"` — ghi
`chat_delegated:<actor>`, không bao giờ là người.

Đường thứ ba — `redirect` op `amend` đúng ticket đang hỏi: QĐ vào sổ chỉ khi `patch.outcome`/`patch.title`/`patch.acceptance[]` nhắc **đúng một** option id **bọc backtick** (`` `raise-valueerror` ``); id trần, không id hoặc ≥ 2 id ⇒ chỉ gỡ câu, không ghi QĐ (suy sai ⇒ `answer` ghi đè). Vì vậy khi viết `acceptance`/`outcome` có nhắc option id ⇒ bọc backtick.

**Luật:**
- Câu `required` chưa trả lời ⇒ dispatch bị chặn, lý do nêu đúng id còn thiếu.
  Hệ thống **KHÔNG** tự suy câu trả lời từ `default` — trả lời là quyền của người (hoặc Claude
  ủy nhiệm khi chủ mission giao lái từ chat, ghi `chat_delegated`).
- Trả lời một phần ⇒ tiếp tục chờ phần còn lại, không tự đoán nốt.
- Trả lời cho `id` không tồn tại, hoặc giá trị ngoài `options` đã khai ⇒ bị từ chối
  **có nêu lý do** (không im lặng bỏ qua).
- **Phạm vi chặn khác nhau theo NGUỒN câu hỏi:**
  - Câu **tự đẻ từ `needs_decision`** (id `<ticket-id>-needs-decision-<8 hex>`; id v1 không hash
    vẫn đọc như câu của ticket đó) chỉ chặn **đúng ticket đã hỏi** — so nguyên id, T1 không khớp
    T10. Ticket độc lập vẫn chạy bình thường.
  - Câu **viết tay bước Clarify** (id tự do, vd `q-env`) là câu của **cả mission**
    (môi trường đích, ngân sách, PII) ⇒ chặn **mọi** ticket feature tới khi có
    câu trả lời. Đánh dấu `required` cho câu loại này là quyết định nặng.
- `interview.json` **KHÔNG** được chứa giá trị secret. Câu hỏi cần key thì câu trả
  lời là **TÊN BIẾN**, giá trị đi qua env/stdin (xem `child-env-allowlist-builder`).

## Không làm

- Không lặp lại hỏi approval/tài nguyên đã cấp chỉ vì retry hoặc đổi phiên làm việc.
- Không dùng bypass/override để biến một escalation thành "đã xanh".
- Ticket blocked không chặn ticket độc lập khác nếu DAG và baseline vẫn cho phép — escalation không có nghĩa dừng toàn mission.
