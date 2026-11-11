# Project Documentation Management

### Roadmap & Changelog Maintenance
- **Project Roadmap** (`./docs/development-roadmap.md`): Living document tracking project phases, milestones, and progress
- **Project Changelog** (`./docs/project-changelog.md`): Detailed record of all significant changes, features, and fixes
- **System Architecture** (`./docs/system-architecture.md`): components, data flow, integrations and deployment of the repo
- **Code Standards** (`./docs/code-standards.md`): conventions and patterns the repo's code follows

### Cụm trạng thái khi copy hàng changelog / mục memory

- Copy hàng (hoặc mục) sang version mới ⇒ **soi lại MỌI cụm trạng thái** (`⏳`, `CHƯA phát hành`, `chờ chốt`, `CÒN TREO`, `TODO`), không chỉ đổi số: cờ có **hạn dùng**, thừa kế nguyên văn = cờ chết sống lại.
- ⚠️ Gỡ cờ mà **giữ nguyên văn** cụm cờ trong `~~gạch ngang~~` / blockquote / HTML comment là **KHÔNG GỠ** — vô hình với người đọc nhưng vẫn hit khi `grep`. Diễn đạt lại phần lịch sử, đừng trích.
- **BẮT BUỘC:** đọc `.claude/workflows/documentation-drift-status-flag-checklist.md` **TRƯỚC KHI** thêm/sửa hàng changelog, hoặc khi sửa `plans/*/plan.md`.

### Automatic Updates Required
- **After Feature Implementation**: Update roadmap progress status and changelog entries
- **After Major Milestones**: Review and adjust roadmap phases, update success metrics
- **After Bug Fixes**: Document fixes in changelog with severity and impact
- **After Security Updates**: Record security improvements and version updates

### Documentation Triggers
The `project-manager` agent updates the roadmap and changelog **of a repo that keeps them** (or when the caller passes `ROADMAP: create`) when:
- A development phase status changes (e.g., from "In Progress" to "Complete")
- Major features are implemented or released
- Significant bugs are resolved or security patches applied
- Project timeline or scope adjustments are made
- External dependencies or breaking changes occur

### Update Protocol
1. **Before Updates**: Always read current roadmap and changelog status
2. **During Updates**: Maintain version consistency and proper formatting
3. **After Updates**: Verify links, dates, and cross-references are accurate
4. **Quality Check**: Ensure updates align with actual implementation progress

### Plans

Plan lưu ở `plans/YYYYMMDD-HHmm-ten-plan/`.

**BẮT BUỘC:** đọc `.claude/skills/planning/references/plan-organization.md` **TRƯỚC KHI** tạo/sửa **bất kỳ** file nào trong `plans/`.
