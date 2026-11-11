---
name: mattermost-kanban-connector
description: Use when a command needs to talk to the NAL Mattermost Kanban (plugin chatops-kanban-plugin) via the @avatar bot — download files, update card lane, post comments, list channel members. Invoked by /avatar:specs:receive and /avatar:specs:done. Scripts are deterministic API callers; the LLM does text parsing/decisions in the command, not here.
---

# Mattermost Kanban Connector (dev subset)

Bộ script Python deterministic gọi Mattermost REST API v4 + plugin nội bộ `chatops-kanban-plugin`
qua bot `@avatar`. Command `/avatar:specs:receive` và `/avatar:specs:done` điều phối; script CHỈ làm phần API, in JSON
ra stdout, lỗi tiếng Việt ra stderr + exit != 0.

**Nguồn gốc:** ported từ `po-ai-pack` (nhánh PO đã bỏ, không còn bản nào để đồng bộ) — chỉ lấy
SUBSET script cần cho luồng dev (không mang theo `specs-delivery-map-*` — state riêng của PO).
Contract Mattermost đổi ⇒ sửa tại đây, đây là bản duy nhất.

**Announce khi dùng:** "Đang dùng skill mattermost-kanban-connector để gọi Kanban API."

## Credentials (đọc, không nhận qua argv)

Mọi script đọc token từ `<workspace>/.mattermost/credentials.json` (chmod 600, gitignored) —
schema A2 (LOCKED, khớp avatar-cli `comm-connect`):
`{mattermostUrl, botName, botToken, teamId, defaultChannelId, defaultChannelName}`.
Thiếu file/field → lỗi tiếng Việt gợi ý chạy `avatar comm-connect`. Token KHÔNG bao giờ log;
in ra chỉ 4 ký tự cuối.

## Danh tính đăng bài: bot (mặc định) hoặc PAT cá nhân (`--as-me`)

Mặc định mọi script gọi bằng bot `@avatar` (`botToken`). Dev muốn comment/DM hiện **dưới tên mình**:
1. Lưu PAT một lần: `printf '%s' "$PAT" | avatar comm-connect --personal --comm-bot-token-stdin`
   → ghi `.mattermost/personal-token.json` `{mattermostUrl, username, patToken}` (chmod 600, gitignored;
   CLI từ chối token của bot). KHÔNG đụng `credentials.json` (schema A2 giữ nguyên).
2. Thêm `--as-me` khi gọi `mattermost-post-comment-thread-and-direct-message.py`
   (`comment <threadId> --as-me` · `dm <username> --as-me`). Không cờ = bot.

Thiếu `personal-token.json` hoặc PAT thuộc server khác → lỗi (exit 2), **KHÔNG tự rơi về bot** (tránh đăng nhầm tên).
Phạm vi hiện tại: chỉ script post (comment/DM); đổi lane, upload file vẫn là bot.

## Danh tính dev (KHÁC credentials — không nằm trong schema A2)

`/avatar:specs:receive` cần biết username Mattermost của dev đang chạy lệnh để lọc card lane
Todo theo `assignUsers`. Lưu riêng ở `.claude/state/mattermost-dev-identity.json`
(`{devUsername}`, gitignored) — KHÔNG thêm field vào `credentials.json` (schema A2 giữ nguyên,
dùng chung 1 bot token cho cả workspace). Xem `commands/avatar/specs/receive.md`.

## CONTRACT update card (đã verify — điểm dễ sai nhất)

Route: `PUT {url}/plugins/chatops-kanban-plugin/channel/{channelId}/card/{TARGET_laneId}/{cardId}?currentTeamId={teamId}`
— **laneId đích ở PATH** (đổi lane = đặt lane muốn tới vào path segment).
Body **edit-shape snake_case**:
```json
{ "id": "...", "title": "...", "description": "...", "reminder": 0,
  "is_complete": false, "ownerOnly": false, "deadline": "",
  "data": { "tags": [...], "assignUsers": [...] }, "file_ids": [...] }
```
⚠ BẪY: `file_ids` (KHÔNG `fileIds`), `is_complete` (KHÔNG `isComplete`); `assignUsers`/`tags`
trong `data`, KHÔNG ở root. Sai → HTTP 422 `"must be array"`. Header bắt buộc:
`X-Requested-With: XMLHttpRequest`.

## Bảng script

| Script | I/O |
|---|---|
| `mattermost_credentials_reader_and_token_masker.py` | module (import): `load_credentials()`, `mask_token()` |
| `mattermost_api_http_client_with_bearer_auth.py` | module (import): `MattermostClient` — get/post/put/upload, map lỗi VN |
| `kanban_board_truncation_cap_detector.py` | module (import): `LANE_CARD_CAP`, `truncation_report(board)` → 4 key cắt cụt, `cap_changed_hint(trunc)`, `observed_max_lane_size(board)`. Nguồn DUY NHẤT của hằng cap — digest và update cùng import, **cấm chép**. THUẦN: không import gì, không I/O |
| `kanban_cap_watermark_state_tracker.py` | module (import): `check_and_update_watermark()`, `cap_drop_hint()`, `default_state_path()`. Phép đo LỊCH SỬ bắt chiều cap **GIẢM** — state ở `.claude/state/kanban-cap-watermark.json`. Mọi I/O của cụm cắt cụt nằm ở ĐÂY để detector giữ được cam kết thuần |
| `kanban-card-create-and-update-lane-fileids.py` | entry: `create` \| `update` card (edit-shape). Receive chỉ dùng `update` (move lane). **`update` đọc cờ cắt cụt TRƯỚC khi khai "không tìm thấy"** — board bị cắt ⇒ nêu 2 khả năng, KHÔNG khẳng định card bị xoá |
| `mattermost-file-upload-and-download.py` | entry: `upload <path>` → file_id · `download <file_id> <dest>` — receive dùng `download` |
| `mattermost-post-comment-thread-and-direct-message.py` | entry: `comment <threadId> <msg>` · `dm <username> <msg>` |
| `mattermost-list-channel-members-for-assignee-resolve.py` | entry: (không arg) → JSON `[{username, fullName, nickname}]` (bỏ bot) — `/avatar:specs:done` dùng để resolve assignee |
| `work-started-emit-moc-bat-dau.py` | entry: stdin `{"ticket_id": <int>}` → POST mốc work-started lên `telemetry.nal.vn/api/work-started` (Bearer Google id_token qua `avatar print-id-token`, KHÔNG dùng bot token Mattermost). Gọi ở receive bước 2.3 NGAY SAU move lane thành công, trước comment — Kanban không lưu lịch sử lane nên mốc phải ghi tại chỗ. Fail → stderr VN + exit != 0, receive in cảnh báo rồi đi tiếp |
| `kanban-board-digest-fetch-and-summarize.py` | entry: tổng hợp lane/quá hạn/chờ nhận từ `/c-{id}`, kèm `lane_ids`. Flag `--todo-detail` → chi tiết từng card lane Todo (`id`,`cardNumberRef`,`title`,`assignUsers`,`fileIds`,`threadId`) cho receive lọc theo dev. **Cả 2 nhánh output LUÔN kèm 5 key cắt cụt** `cap`/`truncated`/`truncated_lanes`/`cap_changed`/`cap_drop_suspected` |

## ⛔ CẮT CỤT — đọc trước khi tin số của digest **và** lời khai của update

Server `chatops-kanban-plugin` trả **tối đa 10 card/lane** và **không có tín hiệu nào** báo đã cắt.
Do đó `total` và `lanes{}` của digest là số của **TRANG ĐẦU**, không phải tổng board — mọi kết luận dạng
*"board có N card"*, *"lane X còn đúng những card này"*, *"card Y không tồn tại"* đều SAI khi lane có ≥10 card.

⚠️ Cảnh báo này áp cho **cả digest và update**. `update` duyệt cùng response bị cắt đó để tìm card, nên
**"không tìm thấy" KHÔNG đồng nghĩa "card không tồn tại"** (card có thật nằm ngoài cửa sổ 10 vẫn không thấy).
`update` rẽ nhánh theo `truncated`: board bị cắt ⇒ nêu **2 khả năng**, KHÔNG khẳng định; board không cắt ⇒
khai "không tìm thấy".
Logic dùng chung nằm ở `kanban_board_truncation_cap_detector.py` — **cấm chép** sang entry script.

Đã đo: 9 biến thể tham số phân trang (`page`/`per_page`/`perPage`/`limit`/`offset`) trả kết quả
**bất biến**; `overviews.cardState.cardTotal` và `overviews.laneState` **toàn 0** kể cả khi thêm `currentTeamId`
⇒ **không có đường nào lấy số thật từ phía client**. Digest chỉ khai được *"đã bị cắt"*, không khai được *"cắt mất mấy"*.

Vì vậy digest luôn trả 5 key: `cap` (ngưỡng đang giả định) · `truncated` (bool) · `truncated_lanes` (tên lane
chạm ngưỡng) · `cap_changed` (bool) · `cap_drop_suspected` (bool). **Caller PHẢI đọc `truncated` trước khi kết luận.**

⚠️ `cap_changed` là **tripwire MỘT CHIỀU**: chỉ bắt được cap **TĂNG** (lane trả > hằng ⇒ hằng lỗi thời). Cap
**GIẢM** (vd 10 → 5) đi qua nó hoàn toàn im lặng — trong MỘT snapshot không phép đo nào phân biệt "lane bị cắt
ở 5" với "lane có đúng 5 card thật".

✅ Chiều GIẢM dùng `cap_drop_suspected` — phép đo **LỊCH SỬ giữa nhiều lần chạy**, không phải một
snapshot: nhớ mốc cao nhất từng quan sát, nghi ngờ khi đủ **3 vế** — mốc cũ `>= cap` · lần này `< mốc cũ` ·
lần này `< cap` (vế 3 chặn ca mốc-cao-hơn-cap: mốc 12 / cap 10 / quan sát 11 thì board VẪN chạm ngưỡng cắt).
⚠️ **Đây là NGHI NGỜ, không phải kết luận** — board *vơi thật* (archive bớt card) cho đúng cùng dấu hiệu; vì
vậy cảnh báo **kêu đúng MỘT lần** rồi tự đặt lại mốc về mức mới, chỉ kêu lại nếu cap tụt thêm nấc nữa (cảnh
báo kêu mãi mà thao tác thường không tắt được thì thành nhiễu, che mất đúng cảnh báo cắt cụt).
Cờ ra **cả stdout lẫn stderr** để caller nuốt stderr vẫn thấy. State ghi **atomic** (`os.replace`).
⛔ Nghi ngờ này KHÔNG thay được lời giải trọn vẹn — thứ đó phải đến từ server (field `total`), và hướng xin
maintainer plugin đã bị **chốt bỏ**.

Bỏ so với po-ai-pack: `specs-delivery-map-*.py` (state riêng PO, dev không cần).

## Quy tắc đặt tên

Module bị `import` = **snake_case** (Python import được; precedent
`state_file_lock_with_fcntl_posix.py` ở `scripts/` ROOT team-ai-pack). Script entry chạy độc
lập = **kebab-case**.
