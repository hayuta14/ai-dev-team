"""Suy luận "board Kanban có bị server cắt cụt không" — logic THUẦN, dùng chung.

Vì sao tên file snake_case (không phải gạch ngang như các entry script cạnh đây):
hai entry script `kanban-board-digest-fetch-and-summarize.py` và
`kanban-card-create-and-update-lane-fileids.py` đều mang tên **gạch ngang** ⇒ KHÔNG
`import` thẳng được. Module dùng chung phải snake_case để cả hai import được bằng tên
(cùng convention với `mattermost_api_http_client_with_bearer_auth.py` và
`mattermost_credentials_reader_and_token_masker.py` trong cùng thư mục).

Module này **không import gì** (kể cả stdlib) và **không I/O** — chỉ đọc dict `board`.

⛔ Đây là nguồn DUY NHẤT của `LANE_CARD_CAP` + `truncation_report` (#222). Chép hàm
sang entry script = hai bản hằng số trôi lệch nhau, đúng loài lỗi #194 vừa diệt.
"""
from __future__ import annotations

# Cap do SERVER `chatops-kanban-plugin` áp, KHÔNG phải do script nào cắt (#194).
# Đo 2026-08-11: 9 biến thể tham số phân trang — (no qs) · page=1 · page=2 ·
# per_page=200 · perPage=200 · limit=200 · offset=10 · page=2&per_page=10 ·
# page=2&perPage=10 — đều trả kết quả BẤT BIẾN; `overviews.cardState.cardTotal`
# và `overviews.laneState` toàn 0 kể cả khi thêm `currentTeamId`.
# ⇒ Không có đường nào lấy SỐ THẬT từ phía client; chỉ suy ra được "đã bị cắt".
LANE_CARD_CAP = 10


def truncation_report(board) -> dict:
    """Suy ra board có bị server cắt cụt không. Hàm THUẦN — chỉ đọc `board`.

    Chỉ khai được **"đã bị cắt"**, KHÔNG khai được **"cắt mất mấy"**: server không
    có tham số phân trang và `overviews` trả rỗng (xem comment `LANE_CARD_CAP`).

    `len(cards) >= cap` là SUY LUẬN, không phải quan sát trực tiếp — lane có đúng
    `cap` card thật cũng bật cờ. Đây là **dương tính giả có chủ ý**: sai về phía
    ồn ào, không sai về phía im lặng.

    ⛔ TRIPWIRE MỘT CHIỀU — giới hạn phải đọc trước khi tin cờ này:
    `cap_changed` chỉ bắt được cap TĂNG (lane trả > cap ⇒ hằng số đã lỗi thời).
    Cap GIẢM (vd 10 → 5) đi qua HOÀN TOÀN IM LẶNG: mọi lane trả ≤5 nên cả
    `>= 10` lẫn `> 10` đều sai ⇒ `truncated: False` y hệt bug gốc. KHÔNG có phép
    đo phía client nào phân biệt được "lane bị cắt ở 5" với "lane có đúng 5 card
    thật". Đây KHÔNG phải lời giải trọn vẹn cho "cap đổi = chết im lặng".
    """
    lanes = board.get("lanes") or []
    truncated_lanes = [
        lane.get("title")
        for lane in lanes
        if len(lane.get("cards") or []) >= LANE_CARD_CAP
    ]
    cap_changed = any(len(lane.get("cards") or []) > LANE_CARD_CAP for lane in lanes)
    return {
        "cap": LANE_CARD_CAP,
        # `cap_changed` kéo theo `truncated` cả khi vị từ trên đổi về sau.
        "truncated": bool(truncated_lanes) or cap_changed,
        "truncated_lanes": truncated_lanes,
        "cap_changed": cap_changed,
    }


def cap_changed_hint(trunc) -> str | None:
    """Câu cảnh báo "hằng số cap đã lỗi thời", hoặc `None` khi cap chưa đổi.

    Dùng chung cho CẢ digest LẪN update — lời khuyên y hệt nhau ở hai nơi.
    KHÔNG nhận card làm tham số ⇒ không thể rò tiêu đề/nội dung ticket ra log.
    """
    if not trunc["cap_changed"]:
        return None
    return (
        f"⛔ Có lane trả NHIỀU HƠN {trunc['cap']} card ⇒ cap phía server đã "
        "đổi, hằng số `LANE_CARD_CAP` trong pack đã lỗi thời. Báo team admin "
        "cập nhật pack."
    )


def observed_max_lane_size(board) -> int:
    """Số card LỚN NHẤT quan sát được ở một lane trong snapshot này. Hàm THUẦN.

    Tách khỏi `truncation_report` vì phục vụ mục đích KHÁC: `truncation_report`
    so với hằng `LANE_CARD_CAP` trong MỘT snapshot, còn số này là nguyên liệu cho
    phép đo LỊCH SỬ giữa NHIỀU lần chạy (#216) — thứ duy nhất bắt được chiều cap
    GIẢM. Giữ ở đây (không nhét sang tracker) để mọi phép đọc `lanes[].cards`
    nằm cùng một chỗ; tracker chỉ lo state I/O.

    Board rỗng ⇒ 0.
    """
    return max(
        (len(lane.get("cards") or []) for lane in (board.get("lanes") or [])),
        default=0,
    )
