#!/usr/bin/env python3
"""Entry: upload file lên Mattermost (trả file_id) / download file về đĩa.

Ported from po-ai-pack phase-01 (06/07) — team-ai-pack phase-05 subset cho
/avatar:specs:receive (cần nhánh download → specs/incoming/). Giữ NGUYÊN logic.

Usage:
    upload   <path> [--channel <channelId>]   → in JSON {"file_id": "..."}
    download <file_id> <dest_path>            → ghi file, in JSON {"path", "size"}

Import module client + credentials (snake_case). Chỉ stdlib. VERIFIED 06/07:
POST /api/v4/files (multipart, channel_id) · GET /api/v4/files/{id}.
Download validate dest nằm trong workspace (chống path traversal từ tên server trả).
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
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


def _client() -> MattermostClient:
    c = load_credentials()
    return MattermostClient(c["mattermostUrl"], c["botToken"], c["teamId"])


def _sanitize_filename(name: str) -> str:
    """Bỏ CR/LF/quote khỏi filename trước khi nhét vào header multipart.

    Phòng CRLF/quote injection nếu filename về sau đến từ nguồn không tin cậy
    (vd tên server trả — rủi ro phase-05). File local của PO thì vô hại nhưng
    sanitize sớm là rẻ + an toàn (defense-in-depth).
    """
    return name.replace("\r", "").replace("\n", "").replace('"', "").replace("\\", "")


def _build_multipart(field_channel: str, file_path: Path, boundary: str) -> bytes:
    """Dựng body multipart/form-data: channel_id + files. Chỉ stdlib."""
    name = _sanitize_filename(file_path.name)
    parts = [
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="channel_id"\r\n\r\n',
        f"{field_channel}\r\n".encode(),
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="files"; filename="{name}"\r\n'.encode(),
        b"Content-Type: application/octet-stream\r\n\r\n",
        file_path.read_bytes(),
        f"\r\n--{boundary}--\r\n".encode(),
    ]
    return b"".join(parts)


def do_upload(args) -> int:
    client = _client()
    cred = load_credentials()
    channel = args.channel or cred["defaultChannelId"]
    fp = Path(args.path)
    if not fp.is_file():
        print(f"File không tồn tại: {fp}", file=sys.stderr)
        return 1
    boundary = f"----avatar{uuid.uuid4().hex}"
    body = _build_multipart(channel, fp, boundary)
    res = client.post_multipart("/api/v4/files", body, boundary)
    infos = (res or {}).get("file_infos") or []
    if not infos:
        print("Upload không trả file_infos.", file=sys.stderr)
        return 1
    print(json.dumps({"file_id": infos[0]["id"], "name": infos[0].get("name")}))
    return 0


def do_download(args) -> int:
    client = _client()
    dest = Path(args.dest).resolve()
    # Chống traversal: dest phải NẰM TRONG cây thư mục CWD. Dùng relative_to
    # (không dùng str.startswith — bypass được bằng sibling trùng prefix chuỗi).
    try:
        dest.relative_to(Path.cwd().resolve())
    except ValueError:
        print(f"Đường dẫn đích ngoài workspace bị từ chối: {dest}", file=sys.stderr)
        return 1
    data = client.get_bytes(f"/api/v4/files/{args.file_id}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print(json.dumps({"path": str(dest), "size": len(data)}))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Mattermost file upload/download")
    sub = p.add_subparsers(dest="cmd", required=True)
    up = sub.add_parser("upload")
    up.add_argument("path")
    up.add_argument("--channel")
    dn = sub.add_parser("download")
    dn.add_argument("file_id")
    dn.add_argument("dest")
    args = p.parse_args()
    try:
        return do_upload(args) if args.cmd == "upload" else do_download(args)
    except (CredentialsError, MattermostApiError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
