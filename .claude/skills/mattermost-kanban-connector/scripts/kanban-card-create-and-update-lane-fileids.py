#!/usr/bin/env python3
"""Entry: create card / update card trên Kanban (chatops-kanban-plugin).

Ported from po-ai-pack phase-01 (06/07) — team-ai-pack phase-05 subset cho
/avatar:specs:receive (cần nhánh update → move lane Todo→InProgress). Giữ
NGUYÊN contract (create vẫn có, dùng chung module — receive chỉ dùng update).

Usage (đọc payload JSON từ stdin để tránh lộ dữ liệu qua argv):
    create   < create.json   → in JSON card mới {"id","cardNumberRef","laneId"}
    update   < update.json   → in JSON card sau update

create.json: {"title","description","laneId","assignUsers":[],"tags":[],"file_ids":[],
              "spec_slug":"<slug>"}  (spec_slug → tự thêm tag "spec::<slug>")
update.json: {"cardId","targetLaneId"?,"description"?,"file_ids"?,"assignUsers"?,"tags"?}
             (field vắng = giữ nguyên; targetLaneId → move lane qua PATH)

CONTRACT VERIFIED 06/07 (xem SKILL.md): update = PUT .../card/{TARGET_laneId}/{cardId}
?currentTeamId= body edit-shape snake_case (file_ids/is_complete/data:{tags,assignUsers}).
Create verified 03/07: POST .../channel/{ch}/card?currentTeamId= body {title,description,
lane_id,creatorEmail,deadline,data:{assignUsers,tags}}.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mattermost_api_http_client_with_bearer_auth import (  # noqa: E402
    MattermostApiError, MattermostClient, build_card_edit_payload,
)
from mattermost_credentials_reader_and_token_masker import (  # noqa: E402
    CredentialsError, load_credentials,
)
from kanban_board_truncation_cap_detector import (  # noqa: E402
    cap_changed_hint, truncation_report,
)

SPEC_TAG_PREFIX = "spec::"

# Ép stdio về UTF-8. Claude Code gửi/nhận JSON UTF-8, còn Python trên Windows lấy bảng mã
# locale cho pipe: cp932 nuốt dấu `\` của JSON và không mã hoá được tiếng Việt.
for _stream, _errors in ((sys.stdin, "surrogateescape"), (sys.stdout, "backslashreplace"),
                         (sys.stderr, "backslashreplace")):
    try:
        _stream.reconfigure(encoding="utf-8", errors=_errors)
    except Exception:  # luồng bị thay (test double) hoặc đã đóng: giữ nguyên
        pass


def _client_and_cred():
    c = load_credentials()
    return MattermostClient(c["mattermostUrl"], c["botToken"], c["teamId"]), c


def _fetch_card(client, channel_id, card_id):
    """Đọc card object hiện tại từ board (cần cho update edit-shape).

    Trả `(card, lane_id, trunc)`; không thấy ⇒ `(None, None, trunc)`.

    ⛔ `card is None` **KHÔNG** đồng nghĩa "card không tồn tại": server cắt ở
    `cap` card/lane và không trả tín hiệu nào, nên `board` chỉ là TRANG ĐẦU.
    Card có thật nằm ngoài trang đầu cũng cho `None` — đúng bug #222. Vì thế
    `trunc` (đủ 4 key, ở MỌI đường trả — kể cả khi tìm thấy) phải được caller
    đọc TRƯỚC khi kết luận bất cứ điều gì.

    `trunc` tính từ CHÍNH `board` vừa GET ⇒ không phát sinh HTTP call thứ hai.
    """
    board = client.get_json(f"/plugins/chatops-kanban-plugin/c-{channel_id}")
    trunc = truncation_report(board)
    for lane in board.get("lanes", []):
        for card in (lane.get("cards") or []):
            if card["id"] == card_id:
                return card, lane["id"], trunc
    return None, None, trunc


def do_create(payload) -> int:
    client, cred = _client_and_cred()
    ch = cred["defaultChannelId"]
    team = cred["teamId"]
    tags = list(payload.get("tags", []))
    slug = payload.get("spec_slug")
    if slug:  # tag spec:: BỔ SUNG (không thay) — nền self-heal
        spec_tag = f"{SPEC_TAG_PREFIX}{slug}"
        if spec_tag not in tags:
            tags.append(spec_tag)
    body = {
        "title": payload["title"],
        "description": payload.get("description", ""),
        "lane_id": payload["laneId"],
        "creatorEmail": cred["botName"] + "@localhost",
        "deadline": payload.get("deadline", ""),
        "data": {"assignUsers": payload.get("assignUsers", []), "tags": tags},
    }
    res = client.post_json(
        f"/plugins/chatops-kanban-plugin/channel/{ch}/card?currentTeamId={team}", body)
    print(json.dumps({
        "id": res["id"], "cardNumberRef": res.get("cardNumberRef"),
        "laneId": res.get("laneId"), "threadId": (res.get("props") or {}).get("threadId"),
    }))
    return 0


def do_update(payload) -> int:
    client, cred = _client_and_cred()
    ch = cred["defaultChannelId"]
    team = cred["teamId"]
    card_id = payload["cardId"]
    card, cur_lane, trunc = _fetch_card(client, ch, card_id)
    if card is None:
        # ⛔ Rẽ theo `truncated` — KHÔNG khẳng định một chiều (#222). Board bị cắt
        # thì "không thấy" là dữ kiện về RESPONSE, không phải về sự tồn tại của card.
        if not trunc["truncated"]:
            print(f"Không tìm thấy card {card_id} trên board (có thể đã bị xoá tay).",
                  file=sys.stderr)
        else:
            lanes = ", ".join(t for t in trunc["truncated_lanes"] if t) or "(không xác định)"
            print(
                f"Không thấy card {card_id} trong dữ liệu server trả về — nhưng board "
                f"đang bị CẮT ở {trunc['cap']} card/lane (lane chạm ngưỡng: {lanes}), "
                "nên có 2 khả năng:\n"
                "  1. Card không tồn tại (đã bị xoá), hoặc\n"
                f"  2. Card có thật nhưng nằm ngoài {trunc['cap']} card đầu của lane "
                "nên server không trả về.\n"
                "Không phân biệt được từ phía client. Mở board Mattermost xem trực tiếp "
                "để xác nhận.",
                file=sys.stderr,
            )
            hint = cap_changed_hint(trunc)
            if hint is not None:
                print(hint, file=sys.stderr)
        return 3
    target_lane = payload.get("targetLaneId") or cur_lane
    body = build_card_edit_payload(
        card,
        file_ids=payload.get("file_ids"),
        description=payload.get("description"),
        tags=payload.get("tags"),
        assign_users=payload.get("assignUsers"),
    )
    res = client.put_json(
        f"/plugins/chatops-kanban-plugin/channel/{ch}/card/{target_lane}/{card_id}"
        f"?currentTeamId={team}", body)
    # threadId lấy từ card gốc (_fetch_card đã đọc) — do_update cần trả để command
    # comment version vào thread mà KHÔNG phải gọi thêm API ngoài script (C1 review).
    thread_id = (card.get("props") or {}).get("threadId")
    print(json.dumps({
        "id": res["id"], "cardNumberRef": res.get("cardNumberRef"),
        "laneId": res.get("laneId"), "threadId": thread_id,
    }))
    return 0


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ("create", "update"):
        print("Usage: create|update  (payload JSON qua stdin)", file=sys.stderr)
        return 1
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Payload stdin không phải JSON hợp lệ: {exc}", file=sys.stderr)
        return 1
    try:
        return do_create(payload) if sys.argv[1] == "create" else do_update(payload)
    except (CredentialsError, MattermostApiError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except KeyError as exc:
        print(f"Payload thiếu field bắt buộc: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
