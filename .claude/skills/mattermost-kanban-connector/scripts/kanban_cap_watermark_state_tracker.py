#!/usr/bin/env python3
"""Mốc cap QUAN SÁT ĐƯỢC qua nhiều lần chạy — bắt chiều cap GIẢM (#216).

Vì sao cần: `truncation_report` (module cạnh đây) chỉ bắt được cap TĂNG — lane trả
> hằng số ⇒ hằng đã lỗi thời. Chiều GIẢM (vd server đổi 10 → 5) đi qua HOÀN TOÀN
IM LẶNG vì mọi lane trả ≤ 5 nên cả `>= 10` lẫn `> 10` đều sai. Trong MỘT snapshot
không có phép đo nào phân biệt "lane bị cắt ở 5" với "lane có đúng 5 card thật"
— nhưng qua NHIỀU lần chạy thì có: nếu từng quan sát một lane đầy ĐÚNG cap rồi
sau đó KHÔNG lane nào chạm tới mức ấy nữa, đó là dấu hiệu cap đã tụt.

⚠️ ĐIỂM MÙ CÓ CHỦ Ý — phải đọc trước khi tin cờ này: board **vơi thật** (người ta
archive bớt card) cho ĐÚNG cùng dấu hiệu. Đây là NGHI NGỜ, không phải kết luận.
Vì vậy cảnh báo **kêu đúng MỘT lần** rồi tự đặt lại mốc (xem `check_and_update_
watermark`): cảnh báo kêu mãi mà thao tác bình thường không tắt được thì thành
nhiễu, mà nhiễu giết đúng mục tiêu của #194.

Tách khỏi `kanban_board_truncation_cap_detector.py` để module đó giữ đúng cam kết
trong docstring của nó: THUẦN, không import gì, không I/O. Mọi đọc/ghi file nằm ở
đây.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

# State nằm ở `.claude/state/` — thư mục này bị `.gitignore` chặn ở mọi repo của
# workspace, nên KHÔNG lọt commit. ⚠️ Sạch là nhờ `.gitignore`, KHÔNG nhờ vị trí:
# thiếu `CLAUDE_PROJECT_DIR` thì đường dẫn bám CWD, chạy trong repo sẽ đẻ file
# `.claude/state/` NGAY TRONG cây repo đó.
_STATE_RELATIVE_PATH = Path(".claude") / "state" / "kanban-cap-watermark.json"


def default_state_path() -> Path:
    """Đường dẫn state mặc định.

    Ưu tiên `CLAUDE_PROJECT_DIR` (biến hook luôn trỏ workspace root) vì script có
    thể bị gọi từ CWD bất kỳ — `cd src/<repo>` rồi chạy sẽ ghi state lạc chỗ nếu
    bám CWD. Không có biến thì mới lùi về CWD; `getcwd()` cũng nằm trong `try` vì
    module này tự nhận "fail-safe tuyệt đối" — cwd bị xoá là ném `FileNotFoundError`.
    """
    root = os.environ.get("CLAUDE_PROJECT_DIR")
    if not root:
        try:
            root = os.getcwd()
        except OSError:
            root = "."
    return Path(root) / _STATE_RELATIVE_PATH


def _read_watermark(state_path: Path):
    """Mốc đã ghi, hoặc None khi chưa có/không đọc được.

    FAIL-SAFE: state hỏng, thiếu quyền, JSON sai kiểu (`"10"`, `true`, `10.9`,
    `null`, list) — tất cả đều trả None chứ KHÔNG ném. Cảnh báo phụ trợ tuyệt đối
    không được làm chết công cụ chính. `bool` bị loại riêng vì `True` là `int`
    trong Python, lọt vào sẽ thành mốc `1`.
    """
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        value = data.get("observed_max")
        return value if isinstance(value, int) and not isinstance(value, bool) else None
    except (OSError, ValueError, AttributeError):
        return None


def _write_watermark(state_path: Path, observed_max: int, previous) -> None:
    """Ghi mốc mới. FAIL-SAFE y hệt `_read_watermark` — nuốt mọi lỗi I/O.

    HAI vế riêng biệt, đừng gộp thành một lời khai chung:

    1. **Người ĐỌC** — `os.replace` lo. Rename trong cùng filesystem là thao tác
       nguyên tử trên POSIX ⇒ ai đọc `state_path` chỉ thấy bản CŨ hoặc bản MỚI,
       không thấy file rỗng/nửa vời. (Con số `~0,8%` đo hồi phase-01 tả đường
       `write_text` thẳng — 2 thì: truncate rồi mới ghi — tức đường ĐÃ BỎ, KHÔNG
       tả trạng thái sau bản vá này.)
    2. **Người GHI** — tên tmp mang PID lo. Dùng chung MỘT tên tmp thì tiến trình
       B truncate đúng file mà tiến trình A đang `os.replace` để promote ⇒ state
       nhận JSON CỤT. `_read_watermark` nuốt `ValueError` nên mốc mất KHÔNG dấu
       vết, máy đó mù vĩnh viễn với đợt cap tụt kế tiếp (đúng "Điểm mù 2" của
       #216). Mỗi tiến trình ghi tmp riêng thì không ai giẫm lên tmp của ai.

    Không dùng file lock: đắt hơn giá trị, và đẻ file `.lock` rác trong state dir.
    """
    tmp_path = state_path.parent / f"{state_path.name}.tmp.{os.getpid()}"
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.write_text(
            json.dumps({"observed_max": observed_max, "previous_observed_max": previous},
                       ensure_ascii=False),
            encoding="utf-8",
        )
        os.replace(tmp_path, state_path)
    except OSError:
        try:
            tmp_path.unlink()
        except OSError:
            pass


def check_and_update_watermark(observed_max: int, cap: int, state_path=None) -> dict:
    """So số quan sát lần này với mốc cao nhất từng thấy, rồi cập nhật mốc.

    Trả dict LUÔN ĐỦ 4 key (key vắng mặt im lặng chính là loài lỗi #194):
    `cap_drop_suspected` · `watermark` (mốc TRƯỚC lần chạy này, None nếu chưa có)
    · `observed_max` · `state_path` (đường dẫn ĐÃ phân giải — để `cap_drop_hint`
    khỏi phân giải lại và in ra đường dẫn khác với chỗ thật sự ghi).

    Vị từ nghi ngờ cần ĐỦ BA VẾ:
    1. mốc cũ >= cap ⇒ đã từng thấy một lane đầy tới ngưỡng cắt (board chưa bao
       giờ chạm cap thì việc nó vơi đi KHÔNG mang thông tin gì về cap);
    2. lần này max < mốc cũ ⇒ không còn lane nào chạm tới mức ấy;
    3. lần này max < cap ⇒ board KHÔNG còn chạm ngưỡng cắt hiện hành. Thiếu vế
       này thì mốc 12 / cap 10 / quan sát 11 cũng kêu, dù 11 > cap nghĩa là cap
       không thể đã tụt xuống dưới 11.

    Nghi ngờ bật ⇒ mốc **đặt lại về mức quan sát mới** thay vì giữ mốc cũ: cảnh
    báo kêu MỘT lần rồi thôi, cap tụt thêm nấc nữa mới kêu tiếp. Không nghi ⇒ mốc
    chỉ tăng (high-water mark).
    """
    path = Path(state_path) if state_path is not None else default_state_path()
    previous = _read_watermark(path)
    suspected = (
        previous is not None
        and previous >= cap
        and observed_max < previous
        and observed_max < cap
    )
    baseline = previous if previous is not None else 0
    _write_watermark(path, observed_max if suspected else max(baseline, observed_max), previous)
    return {
        "cap_drop_suspected": suspected,
        "watermark": previous,
        "observed_max": observed_max,
        "state_path": path,
    }


def cap_drop_hint(verdict, cap: int) -> str | None:
    """Câu cảnh báo nghi cap GIẢM, hoặc None khi không nghi.

    KHÔNG nhận card/board làm tham số ⇒ không thể rò tiêu đề ticket ra log (cùng
    kỷ luật với `cap_changed_hint`). Đường dẫn lấy từ `verdict` chứ không tự phân
    giải lại — caller truyền `state_path` cho hàm kia mà quên hàm này thì câu
    cảnh báo sẽ chỉ sai chỗ.
    """
    if not verdict["cap_drop_suspected"]:
        return None
    return (
        f"⚠️  NGHI cap phía server đã GIẢM: từng quan sát lane đầy "
        f"{verdict['watermark']} card (>= cap {cap}), lần này lane đông nhất chỉ "
        f"{verdict['observed_max']}. Nếu đúng, digest đang đọc TRANG ĐẦU mà tưởng "
        "là cả board — `truncated` sẽ nói dối im lặng. ⚠️ Board VƠI THẬT (archive "
        "bớt card) cho cùng dấu hiệu này ⇒ đây là NGHI NGỜ, không phải kết luận. "
        f"Mốc đã tự đặt lại về {verdict['observed_max']} — cảnh báo này chỉ kêu "
        f"MỘT lần, chỉ kêu lại nếu cap tụt thêm nấc nữa. State: {verdict['state_path']}"
    )
