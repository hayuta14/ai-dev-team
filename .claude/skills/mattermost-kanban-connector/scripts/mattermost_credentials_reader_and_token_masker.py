#!/usr/bin/env python3
"""Đọc + validate Mattermost credentials store, và mask token khi in.

Ported from po-ai-pack phase-01 (06/07) — team-ai-pack phase-05 subset cho
/avatar:specs:receive. Giữ NGUYÊN schema A2 + logic. Sửa lệnh gợi ý trong
message lỗi: "comm-connect" (avatar CLI dev) thay vì "avatar-po comm-connect".

Module (snake_case) — bị import bởi các script entry khác (KHÔNG chạy độc lập).
Nguồn: <workspace>/.mattermost/credentials.json (chmod 600, gitignored) ghi bởi
lệnh CLI `comm-connect` (avatar CLI). Schema A2 (blueprint HTML §A2):
    {mattermostUrl, botName, botToken, teamId, defaultChannelId, defaultChannelName}

Nguyên tắc bảo mật:
- Token CHỈ đọc từ store — KHÔNG nhận qua argv (tránh lộ trong `ps`).
- KHÔNG log token. Khi cần hiển thị → mask_token() chỉ giữ 4 ký tự cuối.
- Thiếu file/field → CredentialsError với message tiếng Việt gợi ý chạy comm-connect.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

# 6 field bắt buộc theo schema A2 (LOCKED — pack đọc, CLI ghi).
REQUIRED_FIELDS = (
    "mattermostUrl",
    "botName",
    "botToken",
    "teamId",
    "defaultChannelId",
    "defaultChannelName",
)

CREDENTIALS_RELATIVE_PATH = os.path.join(".mattermost", "credentials.json")

# Danh tính PHỤ (PAT cá nhân) — ghi bởi `avatar comm-connect --personal`. Lưu riêng,
# KHÔNG nằm trong schema A2. Chỉ đọc khi caller truyền as_me=True (mặc định = bot).
PERSONAL_TOKEN_RELATIVE_PATH = os.path.join(".mattermost", "personal-token.json")
PERSONAL_REQUIRED_FIELDS = ("mattermostUrl", "username", "patToken")


class CredentialsError(Exception):
    """Lỗi credentials — message tiếng Việt để command in thẳng cho user."""


def mask_token(token: str) -> str:
    """Che token, chỉ giữ 4 ký tự cuối. Token rỗng/ngắn → toàn dấu chấm."""
    if not token:
        return "(rỗng)"
    if len(token) <= 4:
        return "•" * len(token)
    return "•" * (len(token) - 4) + token[-4:]


def _find_workspace_root(start: Path):
    """Đi lên từ `start` tìm thư mục chứa .mattermost/credentials.json.

    Cho phép script chạy từ subdir bất kỳ trong workspace (vd Claude Code cd
    vào specs/). Dừng khi gặp credentials store hoặc chạm filesystem root.
    """
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / CREDENTIALS_RELATIVE_PATH).is_file():
            return candidate
    return None


def load_credentials(workspace_root=None, as_me: bool = False) -> dict:
    """Đọc + validate credentials store. Trả dict 6 field.

    workspace_root None → tự dò từ CWD đi lên. Thiếu file hoặc field →
    CredentialsError (message tiếng Việt). Không bao giờ trả token trong exception.

    as_me=True → thay botToken/botName bằng PAT/username cá nhân (từ personal-token.json)
    để mọi caller (`MattermostClient(c["mattermostUrl"], c["botToken"], …)`) giữ nguyên.
    Thiếu file PAT → CredentialsError, KHÔNG tự rơi về bot (tránh đăng nhầm tên).
    """
    if workspace_root is not None:
        cred_path = Path(workspace_root) / CREDENTIALS_RELATIVE_PATH
    else:
        root = _find_workspace_root(Path.cwd())
        if root is None:
            raise CredentialsError(
                "Không tìm thấy .mattermost/credentials.json trong workspace. "
                "Chạy 'avatar comm-connect' để cấu hình kết nối Mattermost."
            )
        cred_path = root / CREDENTIALS_RELATIVE_PATH

    if not cred_path.is_file():
        raise CredentialsError(
            f"Thiếu credentials store tại {cred_path}. "
            "Chạy 'avatar comm-connect' để cấu hình."
        )

    try:
        data = json.loads(cred_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise CredentialsError(
            f"Không đọc/parse được credentials store ({cred_path.name}): {exc}. "
            "Chạy lại 'avatar comm-connect'."
        ) from exc

    missing = [f for f in REQUIRED_FIELDS if not data.get(f)]
    if missing:
        raise CredentialsError(
            "Credentials store thiếu field: "
            + ", ".join(missing)
            + ". Chạy lại 'avatar comm-connect' để cấu hình đủ."
        )

    creds = {f: data[f] for f in REQUIRED_FIELDS}
    if as_me:
        creds = _apply_personal_identity(creds, cred_path.parent)
    return creds


def _apply_personal_identity(creds: dict, mattermost_dir: Path) -> dict:
    """Trả bản copy creds với token/tên của PAT cá nhân. Lỗi → CredentialsError."""
    hint = "Chạy 'avatar comm-connect --personal' để lưu PAT cá nhân."
    pat_path = mattermost_dir / os.path.basename(PERSONAL_TOKEN_RELATIVE_PATH)
    if not pat_path.is_file():
        raise CredentialsError(f"Chưa có PAT cá nhân ({pat_path}). {hint}")
    try:
        pat = json.loads(pat_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise CredentialsError(f"Không đọc/parse được {pat_path.name}: {exc}. {hint}") from exc
    missing = [f for f in PERSONAL_REQUIRED_FIELDS if not pat.get(f)]
    if missing:
        raise CredentialsError(f"{pat_path.name} thiếu field: {', '.join(missing)}. {hint}")
    # PAT của server khác = sai đích; gửi Bearer sang host lạ là lộ secret.
    if pat["mattermostUrl"].rstrip("/") != creds["mattermostUrl"].rstrip("/"):
        raise CredentialsError(
            "PAT cá nhân thuộc server Mattermost khác với credentials.json. " + hint
        )
    return {**creds, "botToken": pat["patToken"], "botName": pat["username"]}
