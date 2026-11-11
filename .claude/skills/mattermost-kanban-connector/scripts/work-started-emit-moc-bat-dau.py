#!/usr/bin/env python3
"""Ghi mốc work-started lên telemetry NGAY khi card chuyển Todo → InProgress.

Vì sao phải ghi TẠI THỜI ĐIỂM chuyển lane (đo 2026-08-24): card Kanban KHÔNG lưu
lịch sử lane — 23 field chỉ có `laneId` hiện tại, `updatedAt` ≡ `createdAt` trên
16/16 card quan sát được. Không job nào truy hồi được mốc này về sau; bỏ lỡ là mất
vĩnh viễn. Server nhận là POST /api/work-started (repo telemetry) — idempotent theo
ticket_id, mốc ĐẦU TIÊN thắng, nên gọi trùng vô hại.

I/O (khuôn connector): JSON qua stdin `{"ticket_id": <int>}` (tuỳ chọn
`"moc_bat_dau": "<ISO>"` — vắng thì lấy now UTC). Thành công → JSON ra stdout,
exit 0. Lỗi → tiếng Việt ra stderr, exit != 0. KHÔNG BAO GIỜ in token.

Token: KHÔNG đọc `.mattermost/credentials.json` (bot token Mattermost không phải
Google id_token). Lấy qua `avatar print-id-token` (tự refresh, cùng nguồn ưu tiên
số 2 của tools/telemetry/hooks/shared/token_reader.py), fallback id_token tĩnh
trong ~/.avatar/config.json. Không import cross-tree sang tools/ — package context
của skill scripts không thấy cây đó.
"""
import json
import os
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

WORK_STARTED_URL_DEFAULT = "https://telemetry.nal.vn/api/work-started"
AVATAR_PRINT_TOKEN_TIMEOUT_S = 4
HTTP_TIMEOUT_S = 10
AVATAR_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".avatar", "config.json")

# Ép stdio về UTF-8. Claude Code gửi/nhận JSON UTF-8, còn Python trên Windows lấy bảng mã
# locale cho pipe: cp932 nuốt dấu `\` của JSON và không mã hoá được tiếng Việt.
for _stream, _errors in ((sys.stdin, "surrogateescape"), (sys.stdout, "backslashreplace"),
                         (sys.stderr, "backslashreplace")):
    try:
        _stream.reconfigure(encoding="utf-8", errors=_errors)
    except Exception:  # luồng bị thay (test double) hoặc đã đóng: giữ nguyên
        pass


def _lay_id_token():
    """Google id_token, ưu tiên bản tươi từ CLI. Trả None nếu mọi nguồn cạn."""
    try:
        ket_qua = subprocess.run(
            ["avatar", "print-id-token"],  # noqa: S607  # avatar resolved from PATH, intentional
            capture_output=True, text=True, timeout=AVATAR_PRINT_TOKEN_TIMEOUT_S,
        )
        if ket_qua.returncode == 0:
            token = ket_qua.stdout.strip()
            if token:
                return token
    except Exception:
        pass

    # Fallback: token tĩnh — có thể stale, nhưng còn hơn mất mốc.
    try:
        with open(AVATAR_CONFIG_PATH) as f:
            token = (json.load(f).get("id_token") or "").strip()
        return token or None
    except Exception:
        return None


def _post_moc(url, token, ticket_id, moc_bat_dau):
    """POST mốc lên route. Trả (status_code, body_text). Lỗi mạng → raise."""
    body = json.dumps({"ticket_id": ticket_id, "moc_bat_dau": moc_bat_dau}).encode()
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )
    # Luôn verify cert — request mang Bearer id_token.
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def main():
    try:
        du_lieu = json.load(sys.stdin)
    except Exception:
        print("Lỗi: stdin phải là JSON dạng {\"ticket_id\": <số>}.", file=sys.stderr)
        return 2

    if not isinstance(du_lieu, dict):
        print("Lỗi: stdin phải là JSON object dạng {\"ticket_id\": <số>}.", file=sys.stderr)
        return 2

    ticket_id = du_lieu.get("ticket_id")
    try:
        # bool là lớp con của int (True → 1) và int(3.7) = 3 — cả hai đều cắt ngầm thành
        # một ticket KHÁC, ghi nhầm mốc cho người khác mà không báo gì.
        if isinstance(ticket_id, bool) or (isinstance(ticket_id, float) and not ticket_id.is_integer()):
            raise ValueError
        ticket_id = int(ticket_id)
        if ticket_id <= 0:
            raise ValueError
    except (TypeError, ValueError):
        print("Lỗi: ticket_id phải là số nguyên dương (cardNumberRef của card).", file=sys.stderr)
        return 2

    moc_bat_dau = du_lieu.get("moc_bat_dau") or datetime.now(timezone.utc).isoformat()

    token = _lay_id_token()
    if not token:
        print(
            "Lỗi: không lấy được Google id_token (avatar print-id-token fail và "
            "~/.avatar/config.json không có id_token). Chạy `avatar login` rồi thử lại. "
            f"Mốc work-started #{ticket_id} CHƯA được ghi.",
            file=sys.stderr,
        )
        return 3

    url = os.environ.get("AVATAR_WORK_STARTED_URL", WORK_STARTED_URL_DEFAULT)
    try:
        status, body = _post_moc(url, token, ticket_id, moc_bat_dau)
    except Exception as e:
        # Không in repr đầy đủ của request — chỉ loại lỗi, tránh mọi đường rò token.
        print(
            f"Lỗi mạng khi ghi mốc work-started #{ticket_id}: {type(e).__name__}. "
            "Mốc CHƯA được ghi — server không truy hồi được, thử lại được bằng cách "
            f"chạy lại: echo '{{\"ticket_id\": {ticket_id}}}' | python3 <script này>.",
            file=sys.stderr,
        )
        return 4

    if status == 200:
        print(json.dumps({"ok": True, "ticket_id": ticket_id, "moc_bat_dau": moc_bat_dau}))
        return 0

    # Route fail-CLOSED (500 khi DB lỗi) — nói thẳng là mốc chưa ghi, đừng im lặng.
    print(
        f"Lỗi: server trả HTTP {status} — mốc work-started #{ticket_id} CHƯA được ghi. "
        f"Chi tiết: {body[:200]}",
        file=sys.stderr,
    )
    return 5


if __name__ == "__main__":
    sys.exit(main())
