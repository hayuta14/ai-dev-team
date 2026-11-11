#!/usr/bin/env python3
"""Entry: comment vào thread của card / gửi Direct Message tới 1 user.

Ported from po-ai-pack phase-01 (06/07) — team-ai-pack phase-05 subset cho
/avatar:specs:receive (comment xác nhận nhận ticket, notify ngược PO). Giữ
NGUYÊN logic.

Usage (msg đọc từ stdin để tránh lộ/escape qua argv):
    comment <threadId> [--file-id <id>]   < message.txt
    dm      <username>                     < message.txt
Thêm `--as-me` (sau tham số vị trí) để đăng dưới tên cá nhân bằng PAT lưu bởi
`avatar comm-connect --personal`. Mặc định (không cờ) = bot @avatar. Thiếu PAT → lỗi, KHÔNG rơi về bot.

VERIFIED 06/07: POST /api/v4/posts (message, channel_id, root_id, file_ids) ·
POST /api/v4/channels/direct ([botUserId, targetUserId]) → DM channel.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mattermost_api_http_client_with_bearer_auth import (  # noqa: E402
    MattermostApiError, MattermostClient,
)
from mattermost_credentials_reader_and_token_masker import (  # noqa: E402
    CredentialsError, load_credentials,
)

# Ép stdio về UTF-8. Claude Code gửi/nhận JSON UTF-8, còn Python trên Windows lấy bảng mã
# locale cho pipe: cp932 nuốt dấu `\` của JSON và không mã hoá được tiếng Việt.
for _stream, _errors in ((sys.stdin, "surrogateescape"), (sys.stdout, "backslashreplace"),
                         (sys.stderr, "backslashreplace")):
    try:
        _stream.reconfigure(encoding="utf-8", errors=_errors)
    except Exception:  # luồng bị thay (test double) hoặc đã đóng: giữ nguyên
        pass


def _client_and_cred(as_me: bool = False):
    c = load_credentials(as_me=as_me)
    return MattermostClient(c["mattermostUrl"], c["botToken"], c["teamId"]), c


def _bot_user_id(client) -> str:
    # /users/me của token đang dùng (bot hoặc PAT cá nhân khi --as-me).
    return client.get_json("/api/v4/users/me")["id"]


def do_comment(thread_id, message, file_id=None, as_me=False) -> int:
    client, cred = _client_and_cred(as_me)
    ch = cred["defaultChannelId"]
    body = {"channel_id": ch, "message": message, "root_id": thread_id}
    if file_id:
        body["file_ids"] = [file_id]
    res = client.post_json("/api/v4/posts", body)
    print(json.dumps({"post_id": res["id"]}))
    return 0


def do_dm(username, message, as_me=False) -> int:
    client, _ = _client_and_cred(as_me)
    bot_id = _bot_user_id(client)
    peer = client.get_json(f"/api/v4/users/username/{username}")
    if not peer or "id" not in peer:
        print(f"Không tìm thấy user @{username} trên Mattermost.", file=sys.stderr)
        return 3
    dm = client.post_json("/api/v4/channels/direct", [bot_id, peer["id"]])
    res = client.post_json("/api/v4/posts", {"channel_id": dm["id"], "message": message})
    print(json.dumps({"dm_channel_id": dm["id"], "post_id": res["id"]}))
    return 0


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] not in ("comment", "dm"):
        print("Usage: comment <threadId> | dm <username> [--as-me]  (message qua stdin)",
              file=sys.stderr)
        return 1
    message = sys.stdin.read().strip()
    if not message:
        print("Message rỗng (stdin).", file=sys.stderr)
        return 1
    file_id = None
    if "--file-id" in sys.argv:
        file_id = sys.argv[sys.argv.index("--file-id") + 1]
    as_me = "--as-me" in sys.argv
    try:
        if sys.argv[1] == "comment":
            return do_comment(sys.argv[2], message, file_id, as_me)
        return do_dm(sys.argv[2], message, as_me)
    except (CredentialsError, MattermostApiError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
