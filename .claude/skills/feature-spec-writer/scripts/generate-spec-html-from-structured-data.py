#!/usr/bin/env python3
"""Generate NAL feature spec HTML from structured JSON data.

Usage:
    python3 generate-spec-html-from-structured-data.py \\
      --data spec-data.json \\
      --output docs/specs/20260529-vendor-payout-batching.html

JSON schema example: see example-spec-input-data-for-testing-the-generator.json

Skill-specific renderers (approaches, risks, open_questions) stay here;
shared boilerplate (esc, render_li_list, render_paragraphs, validate_required,
main_runner) lives in scripts/html_template_renderer_common_utilities.py
to eliminate ~80 lines of duplication with system-design generator.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE_PATH = SKILL_DIR / "templates" / "nal-feature-spec-html-template-with-avatar-styling.html"

# Locate team-ai-pack scripts/ (shared utilities) relative to this file.
# Both standalone repo and Avatar-CLI-synced layouts share the same shape:
#   <root>/scripts/                         <- target
#   <root>/skills/<skill>/scripts/<this>    <- here, so target = parents[2] / "scripts"
# If Avatar CLI ever changes that contract, this will fail loud at import time.
# TEAM_PACK_ROOT (khi set) thắng layout tương đối — thông báo lỗi dưới đây hướng user tới nó.
_TEAM_PACK_ROOT = os.environ.get("TEAM_PACK_ROOT")
TEAM_PACK_SCRIPTS = (
    Path(_TEAM_PACK_ROOT) / "scripts" if _TEAM_PACK_ROOT
    else SCRIPT_DIR.parent.parent.parent / "scripts"
)
if not (TEAM_PACK_SCRIPTS / "html_template_renderer_common_utilities.py").is_file():
    raise RuntimeError(
        f"team-ai-pack shared scripts/ not found at {TEAM_PACK_SCRIPTS}. "
        f"Expected layout: <root>/scripts/ and <root>/skills/<skill>/scripts/<file>. "
        f"If Avatar CLI changed the sync structure, set TEAM_PACK_ROOT env var."
    )
sys.path.insert(0, str(TEAM_PACK_SCRIPTS))

from html_template_renderer_common_utilities import (  # noqa: E402
    esc,
    render_li_list,
    render_paragraphs,
    main_runner,
)

# Ép stdio về UTF-8. Claude Code gửi/nhận JSON UTF-8, còn Python trên Windows lấy bảng mã
# locale cho pipe: cp932 nuốt dấu `\` của JSON và không mã hoá được tiếng Việt.
for _stream, _errors in ((sys.stdin, "surrogateescape"), (sys.stdout, "backslashreplace"),
                         (sys.stderr, "backslashreplace")):
    try:
        _stream.reconfigure(encoding="utf-8", errors=_errors)
    except Exception:  # luồng bị thay (test double) hoặc đã đóng: giữ nguyên
        pass


def render_approaches(approaches: list[dict]) -> str:
    """Render the candidate approaches table body rows."""
    if not approaches:
        return "<tr><td colspan='5'><em>(chưa định nghĩa approach)</em></td></tr>"
    rows = []
    for a in approaches:
        decision = a.get("decision", "").lower()
        if decision == "recommended":
            badge = '<span class="badge recommended">Khuyến nghị</span>'
        elif decision == "rejected":
            badge = '<span class="badge high">Bỏ qua</span>'
        else:
            badge = '<span class="badge med">Đang xem xét</span>'
        pros = "<br>".join(f"• {esc(p)}" for p in a.get("pros", []))
        cons = "<br>".join(f"• {esc(c)}" for c in a.get("cons", []))
        rows.append(
            f"<tr>"
            f"<td><strong>{esc(a.get('name', ''))}</strong></td>"
            f"<td>{esc(a.get('description', ''))}</td>"
            f"<td>{pros}</td>"
            f"<td>{cons}</td>"
            f"<td>{badge}</td>"
            f"</tr>"
        )
    return "".join(rows)


def render_risks(risks: list[dict]) -> str:
    """Render the risks table body rows."""
    if not risks:
        return "<tr><td colspan='4'><em>(chưa định nghĩa risk)</em></td></tr>"
    rows = []
    for r in risks:
        impact = r.get("impact", "low").lower()
        likelihood = r.get("likelihood", "low").lower()
        rows.append(
            f"<tr>"
            f"<td>{esc(r.get('risk', ''))}</td>"
            f"<td><span class='badge {impact}'>{impact.upper()}</span></td>"
            f"<td><span class='badge {likelihood}'>{likelihood.upper()}</span></td>"
            f"<td>{esc(r.get('mitigation', ''))}</td>"
            f"</tr>"
        )
    return "".join(rows)


def render_open_questions(questions: list[str]) -> str:
    """Render the open-questions list items."""
    if not questions:
        return "<li><em>(không còn câu hỏi chưa giải)</em></li>"
    return "".join(f"<li>{esc(q)}</li>" for q in questions)


def build_replacements(data: dict) -> dict[str, str]:
    """Map every {{PLACEHOLDER}} in the template to its rendered HTML."""
    constraints = data.get("constraints", {}) or {}
    return {
        "{{TITLE}}": esc(data.get("title", "Untitled Spec")),
        "{{ELEVATOR_PITCH}}": esc(data.get("elevator_pitch", "")),
        "{{AUTHOR}}": esc(data.get("author", "TBD")),
        "{{STATUS}}": esc(data.get("status", "Draft")),
        "{{TARGET_USERS}}": esc(data.get("target_users", "TBD")),
        "{{DEADLINE}}": esc(data.get("deadline", "TBD")),
        "{{VERSION}}": esc(data.get("version", "v0.1")),
        "{{DATE}}": datetime.now().strftime("%Y-%m-%d"),
        "{{OVERVIEW_HTML}}": render_paragraphs(data.get("overview_paragraphs", [])),
        "{{IN_SCOPE_ITEMS}}": render_li_list(data.get("in_scope", [])),
        "{{OUT_OF_SCOPE_ITEMS}}": render_li_list(data.get("out_of_scope", [])),
        "{{ACCEPTANCE_ITEMS}}": render_li_list(data.get("acceptance_criteria", [])),
        "{{CONSTRAINTS_TECHNICAL}}": render_li_list(constraints.get("technical", [])),
        "{{CONSTRAINTS_PERFORMANCE}}": render_li_list(constraints.get("performance", [])),
        "{{CONSTRAINTS_BUSINESS}}": render_li_list(constraints.get("business", [])),
        "{{CONSTRAINTS_COMPATIBILITY}}": render_li_list(constraints.get("compatibility", [])),
        "{{APPROACHES_ROWS}}": render_approaches(data.get("approaches", [])),
        "{{RECOMMENDED_APPROACH_RATIONALE}}": esc(
            data.get("recommended_approach_rationale", "TBD")
        ),
        "{{RISKS_ROWS}}": render_risks(data.get("risks", [])),
        "{{OPEN_QUESTIONS_ITEMS}}": render_open_questions(data.get("open_questions", [])),
    }


REQUIRED_FIELDS = ["title", "elevator_pitch", "in_scope", "acceptance_criteria"]


if __name__ == "__main__":
    sys.exit(
        main_runner(
            description="Generate NAL feature spec HTML from structured JSON data.",
            required_fields=REQUIRED_FIELDS,
            template_path=TEMPLATE_PATH,
            build_replacements=build_replacements,
            output_label="Spec HTML",
        )
    )
