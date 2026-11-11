#!/usr/bin/env python3
"""Entry: fetch board /c-{channelId} + tóm tắt backlog (digest on-demand).

Ported from po-ai-pack phase-01 (06/07) — team-ai-pack phase-05 subset cho
/avatar:specs:receive (cần field `lane_ids` để lọc lane Todo + card assignUsers
chứa username dev). Giữ NGUYÊN logic tổng hợp gốc; THÊM flag `--todo-detail`
(team-ai-pack phase-05 — po-ai-pack KHÔNG có flag này) để trả chi tiết từng
card lane Todo, vì /avatar:specs:receive cần liệt kê + lọc theo assignUsers,
không chỉ đếm số lượng như digest gốc.

Usage:
    (không arg)       → in JSON tổng hợp:
        {"lanes":{"<lane>":count}, "lane_ids":[...], "waiting_assigned":N,
         "unassigned":N, "overdue":N, "total":N,
         "cap":N, "truncated":bool, "truncated_lanes":[...], "cap_changed":bool,
         "cap_drop_suspected":bool}
    --todo-detail     → in JSON chi tiết card lane "Todo":
        {"cards":[{"id","cardNumberRef","title","descriptionShort","deadline",
                   "assignUsers","fileIds","files","threadId"}],
         "cap":N, "truncated":bool, "truncated_lanes":[...], "cap_changed":bool,
         "cap_drop_suspected":bool}

⛔ CẢNH BÁO CẮT CỤT (#194): `total`/`lanes` KHÔNG phải số thật của board — server
cắt ở `cap` card/lane và không trả tín hiệu nào. 5 key `cap`/`truncated`/
`truncated_lanes`/`cap_changed`/`cap_drop_suspected` LUÔN CÓ MẶT ở cả hai nhánh
output (key xuất hiện
im lặng chính là loài lỗi #194 sinh ra để diệt). Đọc `truncated` TRƯỚC khi kết
luận bất cứ điều gì dạng "board có N card" / "card X không tồn tại".

VERIFIED: GET /plugins/chatops-kanban-plugin/c-{id} trả lanes + cards + overviews.
"deadline" có trong card (edit-shape) → tính overdue được (phase-00 xác nhận).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mattermost_api_http_client_with_bearer_auth import (  # noqa: E402
    MattermostApiError, MattermostClient,
)
from mattermost_credentials_reader_and_token_masker import (  # noqa: E402
    CredentialsError, load_credentials,
)
from kanban_board_truncation_cap_detector import (  # noqa: E402
    cap_changed_hint, observed_max_lane_size, truncation_report,
)
from kanban_cap_watermark_state_tracker import (  # noqa: E402
    cap_drop_hint, check_and_update_watermark,
)

_DESC_MAX_CHARS = 160  # cắt descriptionShort dài hơn ngưỡng này + "…"

# Ép stdio về UTF-8. Claude Code gửi/nhận JSON UTF-8, còn Python trên Windows lấy bảng mã
# locale cho pipe: cp932 nuốt dấu `\` của JSON và không mã hoá được tiếng Việt.
for _stream, _errors in ((sys.stdin, "surrogateescape"), (sys.stdout, "backslashreplace"),
                         (sys.stderr, "backslashreplace")):
    try:
        _stream.reconfigure(encoding="utf-8", errors=_errors)
    except Exception:  # luồng bị thay (test double) hoặc đã đóng: giữ nguyên
        pass


def _parse_deadline_ms(card) -> int:
    """Lấy deadline dạng epoch ms nếu có; 0 = không đặt hạn."""
    d = card.get("deadline") or card.get("endDate") or 0
    try:
        return int(d)
    except (TypeError, ValueError):
        return 0


def _description_short(description) -> str:
    """Rút gọn description: lấy tối đa 2 dòng non-empty đầu, trim, cắt ~160 ký tự.

    Ported từ po-ai-pack digest (cùng logic, giữ nguyên ngưỡng 160 ký tự).
    """
    if not description:
        return ""
    lines = [ln.strip() for ln in str(description).splitlines() if ln.strip()]
    short = " ".join(lines[:2])
    if len(short) > _DESC_MAX_CHARS:
        short = short[:_DESC_MAX_CHARS].rstrip() + "…"
    return short


def _card_detail(card, lane_title: str, client: MattermostClient) -> dict:
    """Build 1 phần tử cards[] từ raw card + lane hiện tại.

    Field lấy trực tiếp từ camelCase phẳng của board GET (KHÔNG phải edit-shape
    snake_case — đó chỉ dùng cho body PUT, xem build_card_edit_payload()).
    `files` = tên file thật, resolve qua client.resolve_file_names() (per-file
    API call — board GET chỉ trả fileIds, không có tên).
    """
    file_ids = card.get("fileIds") or []
    deadline_ms = _parse_deadline_ms(card)
    return {
        "id": card["id"],
        "cardNumberRef": card.get("cardNumberRef"),
        "laneTitle": lane_title,
        "title": card.get("title", ""),
        "descriptionShort": _description_short(card.get("description")),
        "deadline": deadline_ms if deadline_ms else None,
        "assignUsers": card.get("assignUsers", []),
        "fileIds": file_ids,
        "files": client.resolve_file_names(file_ids) if file_ids else [],
        "threadId": (card.get("props") or {}).get("threadId"),
    }


def _todo_detail(board, client: MattermostClient) -> dict:
    """Chi tiết card lane "Todo" cho /avatar:specs:receive liệt kê + lọc theo assignUsers."""
    cards = [
        _card_detail(card, lane["title"], client)
        for lane in board.get("lanes", [])
        if lane.get("title") == "Todo"
        for card in (lane.get("cards") or [])
    ]
    return {"cards": cards}


def _warn_truncated(trunc) -> None:
    """In cảnh báo ra STDERR — stdout phải giữ nguyên MỘT dòng JSON hợp lệ.

    Chỉ nêu TÊN LANE + số cap; KHÔNG in tiêu đề/nội dung card (tránh rò nội dung
    ticket nội bộ ra log CI).
    """
    lanes = ", ".join(t for t in trunc["truncated_lanes"] if t) or "(không xác định)"
    print(
        f"⚠️  Server cắt ở {trunc['cap']} card/lane — lane chạm ngưỡng: {lanes}. "
        "Danh sách dưới đây có thể THIẾU card; `total`/`lanes` KHÔNG phải số thật "
        "của board. Đừng kết luận \"card X không tồn tại\" từ dữ liệu này.",
        file=sys.stderr,
    )
    hint = cap_changed_hint(trunc)
    if hint is not None:
        print(hint, file=sys.stderr)


def _warn_cap_drop(board, cap) -> bool:
    """Cập nhật mốc watermark + in cảnh báo nghi cap GIẢM. Trả cờ để nhét vào JSON.

    Cờ ra CẢ stdout (JSON) chứ không chỉ stderr: caller nào nuốt stderr mà chỉ đọc
    JSON vẫn phải thấy được nghi ngờ — đúng kỷ luật "đừng để tín hiệu chết im lặng"
    của #194.
    """
    verdict = check_and_update_watermark(observed_max_lane_size(board), cap)
    hint = cap_drop_hint(verdict, cap)  # path lấy trong verdict — không phân giải lại
    if hint is not None:
        print(hint, file=sys.stderr)
    return verdict["cap_drop_suspected"]


def main() -> int:
    detail_mode = "--todo-detail" in sys.argv[1:]
    try:
        c = load_credentials()
        client = MattermostClient(c["mattermostUrl"], c["botToken"], c["teamId"])
        board = client.get_json(f"/plugins/chatops-kanban-plugin/c-{c['defaultChannelId']}")
    except (CredentialsError, MattermostApiError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    trunc = truncation_report(board)
    if trunc["truncated"]:
        _warn_truncated(trunc)

    # Chiều cap GIẢM (#216) — `truncated`/`cap_changed` ở trên MÙ với chiều này vì
    # cả hai so trong MỘT snapshot. Phép đo lịch sử nằm ngoài, chỉ mượn 1 cờ.
    trunc["cap_drop_suspected"] = _warn_cap_drop(board, trunc["cap"])

    if detail_mode:
        print(json.dumps({**_todo_detail(board, client), **trunc}, ensure_ascii=False))
        return 0

    now_ms = int(time.time() * 1000)
    lanes_count, waiting, unassigned, overdue, total = {}, 0, 0, 0, 0
    card_details = []  # cards[] chi tiết MỌI lane — /avatar:specs:done resolve #ref → cardId
    for lane in board.get("lanes", []):
        cards = lane.get("cards") or []
        lanes_count[lane["title"]] = len(cards)
        total += len(cards)
        for card in cards:
            dl = _parse_deadline_ms(card)
            if dl and dl < now_ms and lane["title"] != "Done":
                overdue += 1
            if lane["title"] == "Todo":
                if card.get("assignUsers"):
                    waiting += 1
                else:
                    unassigned += 1
            card_details.append(_card_detail(card, lane["title"], client))
    # lane_ids: [{id,title}] để command receive lấy lane-id-by-title (vd Todo/
    # InProgress) mà không phải gọi board API ngoài script layer (C2 review).
    lane_ids = [{"id": ln["id"], "title": ln["title"]} for ln in board.get("lanes", [])]
    print(json.dumps({
        "lanes": lanes_count, "lane_ids": lane_ids, "waiting_assigned": waiting,
        "unassigned": unassigned, "overdue": overdue, "total": total,
        "cards": card_details, **trunc,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
