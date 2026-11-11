#!/usr/bin/env python3
"""Scan TypeScript files for weak types and unsafe assertions.

Detects:
- Hard violations: `: any`, `as any`, `as unknown as`, `@ts-ignore`, `@ts-nocheck`,
  `Function` type, `Object` type, `{}` as type
- Soft violations: `Promise<any>`, `Record<string, any>`, `any[]`,
  `@ts-expect-error` without comment, `as X` cast, non-null assertion `!`

One finding per construct: `as unknown as X` is only the double cast, `: any[]`
is only the any array.

Usage:
    python3 scan-typescript-files-for-weak-types-and-assertions.py \\
      --files "src/api.ts src/utils.ts" \\
      --format markdown

    git diff --name-only HEAD | python3 ... --stdin-files

Architecture (v0.4 refactor):
Scanner logic — file walk, comment-skip, finding render — lives in the
shared scripts/source_code_scanner_framework_base.py module. This file only
declares the TS-specific PATTERNS list and a couple of exception hooks.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Locate the shared framework. Same layout contract used by all team-ai-pack
# scripts: <root>/skills/<skill>/scripts/<this> → <root>/scripts/.
# If Avatar CLI ever changes that contract, this will fail loud at import time.
SCRIPT_DIR = Path(__file__).resolve().parent
TEAM_PACK_SCRIPTS = SCRIPT_DIR.parent.parent.parent / "scripts"
if not (TEAM_PACK_SCRIPTS / "source_code_scanner_framework_base.py").is_file():
    raise RuntimeError(
        f"team-ai-pack scanner framework not found at {TEAM_PACK_SCRIPTS}. "
        f"Expected layout: <root>/scripts/ and <root>/skills/<skill>/scripts/<file>. "
        f"If Avatar CLI changed the sync structure, set TEAM_PACK_ROOT env var."
    )
sys.path.insert(0, str(TEAM_PACK_SCRIPTS))

from source_code_scanner_framework_base import (  # noqa: E402
    SourceCodeScanner,
    read_files_from_args,
)


# TS pattern catalog: (regex, severity, label, suggestion)
PATTERNS = [
    # CRITICAL
    (re.compile(r"@ts-nocheck"), "CRITICAL", "@ts-nocheck",
     "Bỏ — fix từng error thay vì tắt cả file."),
    (re.compile(r"\bas\s+unknown\s+as\s+\w"), "CRITICAL", "double cast (as unknown as)",
     "Dùng schema validate (zod, valibot) thay vì double cast."),

    # HIGH
    (re.compile(r":\s*any\b(?![\w\[])"), "HIGH", "any type annotation",
     "Thay `any` bằng type rõ ràng hoặc `unknown` + type guard."),
    (re.compile(r"(?<!\bunknown\s)\bas\s+any\b"), "HIGH", "as any cast",
     "Dùng `satisfies` nếu khẳng định shape, hoặc type guard nếu narrow."),
    (re.compile(r"@ts-ignore"), "HIGH", "@ts-ignore",
     "Đổi sang `@ts-expect-error <reason>` để document + báo lỗi khi không còn cần."),
    (re.compile(r":\s*Function\b"), "HIGH", "Function type",
     "Thay bằng signature cụ thể: `(arg: X) => Y`."),
    (re.compile(r":\s*Object\b"), "HIGH", "Object type",
     "Thay bằng `Record<K, V>` hoặc interface cụ thể."),
    (re.compile(r":\s*\{\s*\}(?!\w)"), "HIGH", "empty object {} type",
     "Nghĩa thực là 'any non-nullish' — dùng `Record<string, unknown>` hoặc interface."),

    # MEDIUM
    (re.compile(r"Promise<any>"), "MEDIUM", "Promise<any>",
     "Specify resolved type: `Promise<User>` thay vì `Promise<any>`."),
    (re.compile(r"Record<string,\s*any>"), "MEDIUM", "Record<string, any>",
     "Thay `any` bằng union cụ thể: `Record<string, string | number>`."),
    (re.compile(r"Array<any>|any\[\]"), "MEDIUM", "any array",
     "Thay bằng `Array<X>` hoặc `unknown[]` + type guard khi truy cập."),
    (re.compile(r"@ts-expect-error\s*$", re.MULTILINE), "MEDIUM",
     "@ts-expect-error without reason",
     "Thêm reason: `@ts-expect-error <lý do + ticket ref>`."),

    # LOW
    (re.compile(r"(?<!\bunknown\s)\bas\s+[A-Z]\w*"), "LOW", "as cast",
     "Xem xét `satisfies` thay vì `as` để giữ type info."),
    # `x!.y`, `f()!;`, `a[0]!)` — not `!=`/`!==`/logical not (`!flag`).
    (re.compile(r"[\w\])]!(?=[.\[;,)])|[\])]!\s*$"), "LOW", "non-null assertion (!)",
     "Kiểm tra null tường minh (`if (!el) throw ...`) hoặc dùng `?.` thay vì `!`."),
]

# Ép stdio về UTF-8. Claude Code gửi/nhận JSON UTF-8, còn Python trên Windows lấy bảng mã
# locale cho pipe: cp932 nuốt dấu `\` của JSON và không mã hoá được tiếng Việt.
for _stream, _errors in ((sys.stdin, "surrogateescape"), (sys.stdout, "backslashreplace"),
                         (sys.stderr, "backslashreplace")):
    try:
        _stream.reconfigure(encoding="utf-8", errors=_errors)
    except Exception:  # luồng bị thay (test double) hoặc đã đóng: giữ nguyên
        pass


class TypeScriptScanner(SourceCodeScanner):
    """TS-specific scanner — adds `@ts-*` magic-comment exception."""
    rules = PATTERNS
    accepted_extensions = {".ts", ".tsx"}
    skip_dot_d_ts = True  # declaration files often legitimately use `any`
    report_title = "Type Safety Scan Result"

    def is_comment_exception(self, label: str, line: str, col_start: int) -> bool:
        """Keep `@ts-*` findings even when they appear inside a comment."""
        return label.startswith("@ts-")

    def should_skip_finding(self, severity: str, is_test: bool, is_example: bool) -> bool:
        # type-safety-check doesn't downgrade for test files — type bugs in tests
        # are still bugs.
        return False


def main() -> int:
    files, output_format = read_files_from_args()
    # Filter to existing TS files
    files = [f for f in files if f.suffix in TypeScriptScanner.accepted_extensions and f.exists()]
    if not files:
        if output_format == "markdown":
            print(f"## {TypeScriptScanner.report_title}\n\nKhông có file .ts/.tsx để scan.\n")
        else:
            print('{"files_scanned": 0, "findings_count": 0, "findings": []}')
        return 0

    scanner = TypeScriptScanner()
    all_findings = []
    for f in files:
        all_findings.extend(scanner.scan_file(f))

    if output_format == "markdown":
        print(scanner.render_markdown(all_findings, len(files), scanner.report_title))
    else:
        print(scanner.render_json(all_findings, len(files)))

    return scanner.exit_code_for_findings(all_findings)


if __name__ == "__main__":
    sys.exit(main())
