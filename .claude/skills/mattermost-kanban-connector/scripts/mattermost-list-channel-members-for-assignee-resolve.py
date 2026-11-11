#!/usr/bin/env python3
"""Entry: liệt kê member của channel (username + tên) để command resolve assignee.

Ported từ po-ai-pack (07/07) — team-ai-pack /avatar:specs:done cần resolve
assignee khi text có "assign lại cho X" (giống po /avatar:specs:delivery
detect tên người từ text tự do rồi FUZZY-MATCH danh sách này; LLM làm phần
match, không phải script). ≥2 match hoặc 0 match → command HỎI LẠI, không đoán.
Giữ NGUYÊN logic gốc (chỉ đổi docstring context).

Usage:  (không arg) → in JSON list [{"username","fullName","nickname"}] (bỏ bot).
VERIFIED 06/07: GET /api/v4/users?in_channel={channelId} trả user objects.
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


def main() -> int:
    try:
        c = load_credentials()
        client = MattermostClient(c["mattermostUrl"], c["botToken"], c["teamId"])
        # per_page=200: channel PO nội bộ hiếm khi >200 member. Nếu channel lớn hơn
        # → member thứ >200 sẽ bị cắt (resolve "0 match" oan). Chấp nhận cho phase 1;
        # phase sau thêm vòng phân trang `page` nếu cần (H1 review).
        users = client.get_json(
            f"/api/v4/users?in_channel={c['defaultChannelId']}&per_page=200")
    except (CredentialsError, MattermostApiError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    members = []
    for u in users or []:
        if u.get("is_bot"):
            continue  # bỏ bot (kể cả @avatar) — không assign cho bot
        full = " ".join(p for p in (u.get("first_name"), u.get("last_name")) if p).strip()
        members.append({
            "username": u.get("username"),
            "fullName": full,
            "nickname": u.get("nickname", ""),
        })
    print(json.dumps(members, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
