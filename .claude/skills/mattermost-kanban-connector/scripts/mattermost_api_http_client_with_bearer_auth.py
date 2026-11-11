#!/usr/bin/env python3
"""HTTP client cho Mattermost REST v4 + plugin chatops-kanban-plugin, Bearer auth.

Ported from po-ai-pack phase-01 (06/07) — team-ai-pack phase-05 subset cho
/avatar:specs:receive. Giữ NGUYÊN contract/logic (không đổi API surface).

Module (snake_case) — bị import bởi các script entry. Chỉ stdlib (urllib) — theo
constraint "curl+python3 only", không thêm dependency.

Map lỗi → message tiếng Việt:
- 401 → token sai/hết hạn (gợi ý comm-connect)
- 403 → bot thiếu quyền / chưa trong team
- timeout / lỗi mạng → mạng chậm, thử lại
KHÔNG log token (chỉ nằm trong header Authorization, không in ra).

CONTRACT update card (VERIFIED 06/07) — xem build_card_edit_payload():
route PUT .../card/{TARGET_laneId}/{cardId}?currentTeamId= với body edit-shape
snake_case (file_ids / is_complete / data:{tags,assignUsers}); laneId đích ở PATH.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_TIMEOUT = 12  # giây — mạng nội bộ; blueprint yêu cầu < 10s/thao tác.

# P2 A3 — hardening URL trước khi gửi Bearer bot token: bảo vệ secret khỏi TLS
# downgrade cleartext. URL đến từ credentials store (.mattermost/credentials.json,
# chmod 600, do `avatar comm-connect` ghi) → defense-in-depth cho lỗi cấu hình,
# KHÔNG phải SSRF remote.
#
# Chính sách hiện hành: host non-local CHỈ https; localhost / 127.0.0.1 cho cả
# http+https (dev local thường HTTP, loopback không sniff xa). Host nào cũng được.
#
# GHI ĐÈ D1 (Luke chốt trước đây: allowlist cứng {mm.nal.vn, localhost, 127.0.0.1}).
# Người chốt: nam@nal.vn — ngày 2026-09-21.
# Lý do: pack phục vụ nhiều Mattermost/chatops instance khác nhau, không chỉ
# mm.nal.vn; allowlist cứng chặn luôn instance hợp lệ. Host đích là do chính user
# khai qua `avatar comm-connect` → tin credentials store.
# Rủi ro CÒN LẠI đã chấp nhận: gõ nhầm host và userinfo-spoof
# (https://mm.nal.vn@evil.com → hostname thật evil.com) KHÔNG còn bị chặn; token
# sẽ đi tới host được khai. Lớp chắn duy nhất còn lại là bắt buộc https.
_LOCAL_HOSTS = {"localhost", "127.0.0.1"}


def _assert_safe_base_url(base_url: str) -> None:
    """Raise ValueError nếu base_url không hợp lệ. KHÔNG log token (chỉ host/scheme)."""
    parsed = urllib.parse.urlparse(base_url)
    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").lower()
    if scheme not in ("http", "https") or not host:
        raise ValueError(
            f"URL Mattermost không hợp lệ: {base_url!r}. "
            "Cần dạng https://<host> (hoặc http/https://localhost cho dev)."
        )
    is_local = host in _LOCAL_HOSTS
    if not is_local and scheme != "https":
        raise ValueError(
            f"URL Mattermost phải dùng https cho host non-local: {scheme}://{host}. "
            "Từ chối gửi bot token qua kết nối không mã hoá."
        )


class MattermostApiError(Exception):
    """Lỗi API — message tiếng Việt để command in thẳng cho user."""


class MattermostClient:
    """Client mỏng bọc urllib. base_url + token từ credentials store."""

    def __init__(self, base_url: str, token: str, team_id: str = ""):
        # P2 A3: validate URL (ép https cho host non-local) TRƯỚC khi dùng — gate
        # tại nguồn dựng base_url. KHÔNG gate `_url()` absolute-path branch
        # (latent, unreachable — mọi caller truyền path relative do code).
        _assert_safe_base_url(base_url)
        self.base_url = base_url.rstrip("/")
        self._token = token
        self.team_id = team_id

    # ── nội bộ ───────────────────────────────────────────────────────────
    def _headers(self, extra: dict | None = None) -> dict:
        h = {
            "Authorization": f"Bearer {self._token}",
            # Client web gửi kèm — plugin Kanban cần để parse body PUT đúng.
            "X-Requested-With": "XMLHttpRequest",
        }
        if extra:
            h.update(extra)
        return h

    def _request(self, method: str, url: str, *, json_body=None, raw_body=None,
                 headers=None, timeout=DEFAULT_TIMEOUT):
        data = None
        hdr = self._headers(headers)
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            hdr.setdefault("Content-Type", "application/json")
        elif raw_body is not None:
            data = raw_body
        req = urllib.request.Request(url, method=method, headers=hdr, data=data)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:300]
            raise MattermostApiError(self._friendly(exc.code, body)) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise MattermostApiError(
                f"Không kết nối được Mattermost ({exc}). Mạng chậm — thử lại."
            ) from exc

    @staticmethod
    def _friendly(code: int, body: str) -> str:
        if code == 401:
            return "Token bot sai hoặc hết hạn (401). Chạy 'avatar comm-connect'."
        if code == 403:
            return ("Bot thiếu quyền hoặc chưa được thêm vào team/channel (403). "
                    "Nhờ admin thêm bot @avatar vào team.")
        if code == 404:
            return f"Không tìm thấy tài nguyên (404): {body}"
        if code == 422:
            return f"Body request không hợp lệ (422): {body}"
        if code == 400 and "session" in body.lower():
            return "Token bot sai hoặc hết hạn (400 - phiên không hợp lệ). Chạy 'avatar comm-connect'."
        return f"Mattermost trả lỗi {code}: {body}"

    # ── public: JSON helpers ─────────────────────────────────────────────
    def get_json(self, path: str, timeout=DEFAULT_TIMEOUT):
        st, raw = self._request("GET", self._url(path), timeout=timeout)
        return json.loads(raw) if raw else None

    def post_json(self, path: str, body, timeout=DEFAULT_TIMEOUT):
        st, raw = self._request("POST", self._url(path), json_body=body, timeout=timeout)
        return json.loads(raw) if raw else None

    def put_json(self, path: str, body, timeout=DEFAULT_TIMEOUT):
        st, raw = self._request("PUT", self._url(path), json_body=body, timeout=timeout)
        return json.loads(raw) if raw else None

    def get_bytes(self, path: str, timeout=DEFAULT_TIMEOUT) -> bytes:
        st, raw = self._request("GET", self._url(path), timeout=timeout)
        return raw

    def post_multipart(self, path: str, body: bytes, boundary: str,
                       timeout=DEFAULT_TIMEOUT):
        st, raw = self._request(
            "POST", self._url(path), raw_body=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            timeout=timeout,
        )
        return json.loads(raw) if raw else None

    def _url(self, path: str) -> str:
        return path if path.startswith("http") else f"{self.base_url}{path}"

    # ── plugin path helpers ──────────────────────────────────────────────
    def kanban_base(self) -> str:
        return f"{self.base_url}/plugins/chatops-kanban-plugin"

    # ── file metadata ─────────────────────────────────────────────────────
    def resolve_file_names(self, file_ids: list[str]) -> list[dict]:
        """[{id, name}] — board API chỉ trả fileIds, KHÔNG có tên file.

        Gọi GET /api/v4/files/{id}/info MỖI file (per-file request — không có
        batch endpoint; đánh đổi tốc độ để lấy tên thật, user đã chấp nhận).
        Lỗi 1 file (404/mạng/...) → fallback {id, name: id[:8]+'…'}, KHÔNG
        raise để 1 file lỗi không làm hỏng cả list.
        """
        result = []
        for fid in file_ids:
            try:
                info = self.get_json(f"/api/v4/files/{fid}/info")
                name = (info or {}).get("name") or f"{fid[:8]}…"
            except MattermostApiError:
                name = f"{fid[:8]}…"
            result.append({"id": fid, "name": name})
        return result


# Field body KHÔNG được set qua argv — chỉ dùng nội bộ khi dựng edit-shape.
def build_card_edit_payload(card: dict, *, file_ids=None, description=None,
                            tags=None, assign_users=None) -> dict:
    """Dựng body edit-shape snake_case cho PUT update card (VERIFIED 06/07).

    `card` = card object từ board GET /c-{id}. GET trả **camelCase phẳng**
    (verified 06/07: fileIds/isComplete/assignUsers/tags ở root, KHÔNG có `data`
    nested) → đọc trực tiếp field camelCase. Body PUT lại là snake_case (file_ids/
    is_complete/data:{...}) — chính điểm dễ nhầm mà hàm này quy về một chỗ.

    Override field nào truyền field đó; None = giữ nguyên giá trị hiện tại của card.
    laneId đích KHÔNG nằm trong body (caller đặt ở PATH của URL).
    """
    return {
        "id": card["id"],
        "title": card.get("title", ""),
        "description": description if description is not None else card.get("description", ""),
        "reminder": card.get("reminder", 0),
        "is_complete": card.get("isComplete", False),
        "ownerOnly": card.get("ownerOnly", False),
        "deadline": card.get("deadline", ""),
        "data": {
            "tags": tags if tags is not None else card.get("tags", []),
            "assignUsers": assign_users if assign_users is not None
            else card.get("assignUsers", []),
        },
        "file_ids": file_ids if file_ids is not None else card.get("fileIds", []),
    }
