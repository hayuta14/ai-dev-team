#!/usr/bin/env python3
"""Append a tech-debt entry to .claude/state/tech-debt.md.

Rewritten from Bash to Python (#8 — state-file helper consolidation).

NAL priority formula:  (impact + risk) × (6 - effort)

Each numeric input is 1-5. Priority output range is 4 (low) to 50 (top).

Usage:
    python3 append-tech-debt-entry-to-state-file.py \\
      --description "Hardcoded webhook secret in tests" \\
      --location "packages/api/src/__tests__/sepay.test.ts:42" \\
      --category "security" \\
      --reason "Test was failing locally, used hardcoded for speed" \\
      --suggested-fix "Move to test fixture loader, generate per-test secret" \\
      --impact 3 --risk 4 --effort 2 \\
      [--estimate "2h"] \\
      [--state-dir ".claude/state"]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Import shared file-lock helper from team-ai-pack scripts/.
SCRIPT_DIR = Path(__file__).resolve().parent
# TEAM_PACK_ROOT (khi set) thắng layout tương đối — thông báo lỗi dưới đây hướng user tới nó.
_TEAM_PACK_ROOT = os.environ.get("TEAM_PACK_ROOT")
TEAM_PACK_SCRIPTS = (
    Path(_TEAM_PACK_ROOT) / "scripts" if _TEAM_PACK_ROOT
    else SCRIPT_DIR.parent.parent.parent / "scripts"
)
if not (TEAM_PACK_SCRIPTS / "state_file_lock_with_fcntl_posix.py").is_file():
    raise RuntimeError(
        f"team-ai-pack shared scripts/ not found at {TEAM_PACK_SCRIPTS}. "
        f"Expected layout: <root>/scripts/ and <root>/skills/<skill>/scripts/<file>. "
        f"If Avatar CLI changed the sync structure, set TEAM_PACK_ROOT env var."
    )
sys.path.insert(0, str(TEAM_PACK_SCRIPTS))
from state_file_lock_with_fcntl_posix import locked_state_file  # noqa: E402

VALID_CATEGORIES = [
    "code", "architecture", "test", "dependency",
    "documentation", "infrastructure", "type", "security",
]

# Ép stdio về UTF-8. Claude Code gửi/nhận JSON UTF-8, còn Python trên Windows lấy bảng mã
# locale cho pipe: cp932 nuốt dấu `\` của JSON và không mã hoá được tiếng Việt.
for _stream, _errors in ((sys.stdin, "surrogateescape"), (sys.stdout, "backslashreplace"),
                         (sys.stderr, "backslashreplace")):
    try:
        _stream.reconfigure(encoding="utf-8", errors=_errors)
    except Exception:  # luồng bị thay (test double) hoặc đã đóng: giữ nguyên
        pass


def _priority_band(priority: int) -> str:
    if priority >= 30:
        return "TOP (next sprint)"
    if priority >= 15:
        return "MED (within quarter)"
    return "LOW (parked)"


def _initial_debt_md() -> str:
    return """# Tech Debt Backlog

**Last updated:** _PLACEHOLDER_
**Total items:** 0
**Top-priority items (≥30):** 0

## Active Items

## Resolved Items

(Items moved here when fixed, with resolution note + commit/PR link)
"""


def _next_td_id(text: str) -> str:
    """Find the highest TD-NNN id already in the file and return the next one."""
    ids = [int(m.group(1)) for m in re.finditer(r"^### TD-(\d+)", text, re.MULTILINE)]
    next_n = (max(ids) + 1) if ids else 1
    return f"TD-{next_n:03d}"


def _format_entry(
    td_id: str,
    description: str,
    location: str,
    category: str,
    reason: str,
    suggested_fix: str,
    impact: int,
    risk: int,
    effort: int,
    estimate: str,
    stamp: str,
    priority: int,
    band: str,
) -> str:
    """Build the markdown entry block (without leading blank line)."""
    lines = [
        "",
        f"### {td_id} — {description}",
        f"- **Priority:** {priority} ({band})",
        f"- **Category:** {category}",
    ]
    if location:
        lines.append(f"- **Location:** {location}")
    lines.extend([
        f"- **Reason created:** {reason}",
        f"- **Suggested fix:** {suggested_fix}",
        f"- **Score:** Impact={impact}, Risk={risk}, Effort={effort}",
    ])
    if estimate:
        lines.append(f"- **Estimate:** {estimate}")
    lines.extend([
        f"- **Logged:** {stamp}",
        "- **Status:** open",
    ])
    return "\n".join(lines) + "\n"


def _insert_before_resolved_section(text: str, entry: str) -> str:
    """Splice entry into Active Items, immediately before the '## Resolved Items'
    section header.

    Anchors at start AND end of line so it never matches descriptions like
    '## Resolved Items Archive' or any other heading that begins with the
    same words. Allows trailing whitespace on the header line (CRLF + spaces).
    """
    m = re.search(r"^## Resolved Items[ \t]*\r?$", text, re.MULTILINE)
    if not m:
        return text.rstrip() + "\n" + entry
    return text[:m.start()] + entry + text[m.start():]


def _update_header_stats(text: str, total: int, top_count: int, stamp: str) -> str:
    text = re.sub(
        r"^\*\*Last updated:\*\*.*$",
        f"**Last updated:** {stamp}",
        text, count=1, flags=re.MULTILINE,
    )
    text = re.sub(
        r"^\*\*Total items:\*\*.*$",
        f"**Total items:** {total}",
        text, count=1, flags=re.MULTILINE,
    )
    text = re.sub(
        r"^\*\*Top-priority items \(≥30\):\*\*.*$",
        f"**Top-priority items (≥30):** {top_count}",
        text, count=1, flags=re.MULTILINE,
    )
    return text


def _count_top_priority(text: str) -> int:
    return len(re.findall(r"\*\*Priority:\*\* (3[0-9]|4[0-9]|50)\b", text))


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a tech-debt entry.")
    parser.add_argument("--description", required=True, help="One-line description")
    parser.add_argument("--location", default="", help="Path:line or component name")
    parser.add_argument("--category", default="code",
                        choices=VALID_CATEGORIES, help="Debt category")
    parser.add_argument("--reason", required=True, help="Why the shortcut was taken")
    parser.add_argument("--suggested-fix", required=True, help="How to resolve")
    parser.add_argument("--impact", required=True, type=int, choices=range(1, 6),
                        help="Impact score 1-5")
    parser.add_argument("--risk", required=True, type=int, choices=range(1, 6),
                        help="Risk score 1-5")
    parser.add_argument("--effort", required=True, type=int, choices=range(1, 6),
                        help="Effort score 1-5 (lower = easier)")
    parser.add_argument("--estimate", default="", help="Effort estimate e.g. '2h'")
    parser.add_argument("--state-dir", default=".claude/state", help="State directory")
    args = parser.parse_args()

    priority = (args.impact + args.risk) * (6 - args.effort)
    band = _priority_band(priority)

    state_dir = Path(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    debt_file = state_dir / "tech-debt.md"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Lock to prevent concurrent-session races (M-5).
    with locked_state_file(debt_file):
        # Read or initialize
        if debt_file.exists():
            text = debt_file.read_text(encoding="utf-8")
        else:
            text = _initial_debt_md()

        td_id = _next_td_id(text)
        entry = _format_entry(
            td_id, args.description, args.location, args.category,
            args.reason, args.suggested_fix,
            args.impact, args.risk, args.effort,
            args.estimate, stamp, priority, band,
        )
        text = _insert_before_resolved_section(text, entry)

        total = len(re.findall(r"^### TD-\d+", text, re.MULTILINE))
        top_count = _count_top_priority(text)
        text = _update_header_stats(text, total, top_count, stamp)

        debt_file.write_text(text, encoding="utf-8")

    print(f"✓ Tech debt logged: {td_id}")
    print(f"  Priority: {priority} ({band})")
    print(f"  Category: {args.category}")
    if args.location:
        print(f"  Location: {args.location}")
    print()
    print(f"  File: {debt_file}")
    print(f"  Total items now: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
