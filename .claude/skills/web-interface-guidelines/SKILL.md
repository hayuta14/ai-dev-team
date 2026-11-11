---
name: web-interface-guidelines
description: Vercel's Web Interface Guidelines - 104 review rules for UI code (accessibility, focus states, forms, animation, typography, images, performance, navigation state, touch, safe areas, dark mode, locale/i18n, hydration, copy, anti-patterns), findings as `file:line`. Use when reviewing or finishing HTML/CSS/React/Next.js UI code, or when ui-ux-designer runs review mode. Vendored offline copy; for design decisions (palette, fonts, style) use `ui-ux-pro-max`. Triggers (VI): "soát UI", "review giao diện", "kiểm tra accessibility".
license: MIT (see LICENSE, Copyright (c) 2025 Vercel Labs)
---

# Web Interface Guidelines (vendored)

`command.md` in this directory is the upstream rule set, verbatim: [vercel-labs/web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines) `command.md` @ `434b7f91364665f2f733b310ec54809bf8f37937` (2026-10-05). Do not edit it here; changes go upstream.

## Use

1. Read `command.md` §Rules (17 groups, 104 rules) and §Output Format.
2. Read the target files; check each rule that applies to them. Upstream's `$ARGUMENTS` is the file list you were given.
3. Report findings grouped by file as `file:line - issue`, `✓ pass` for a clean file, as §Output Format shows. Contrast ratios, overflow and screenshots are not in these rules: `ui-ux-designer` measures them (its §Validation).

## Update

```bash
SHA=<new upstream commit>
curl -fsS -o /tmp/wig-command.md https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/$SHA/command.md
diff skills/web-interface-guidelines/command.md /tmp/wig-command.md   # read the diff before replacing
```
Replace the file, update the SHA here and in `skills/THIRD_PARTY_NOTICES.md`.
