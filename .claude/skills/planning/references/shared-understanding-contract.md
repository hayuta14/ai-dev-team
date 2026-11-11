# Shared Understanding Contract

Contract quy định cấu trúc + luật của `shared-understanding.md` (SU). SU là **intent đã được chốt** cho một plan, KHÔNG phải bản thân plan. Planner consume SU làm nguồn authoritative immutable.

---

## 15 section BẮT BUỘC (đúng thứ tự, giữ nguyên tên tiếng Anh)

1. **Goal & Business Value** — mục tiêu + giá trị kinh doanh.
2. **In Scope** — nằm trong phạm vi.
3. **Out of Scope** — rõ ràng nằm ngoài phạm vi.
4. **User-visible Outcome** — người dùng thấy/dùng được gì.
5. **Acceptance Criteria** — tiêu chí nghiệm thu (phải measurable).
6. **Codebase Facts** — sự thật về code hiện hữu (từ Scout/GitNexus).
7. **External Constraints & Prior Art** — ràng buộc ngoài + tham chiếu tiền lệ.
8. **Existing Patterns to Preserve** — pattern hiện có cần giữ.
9. **Assumptions** — giả định đang dựa vào.
10. **Risks & Failure Modes** — rủi ro + chế độ hỏng.
11. **Technical Decisions Agreed** — quyết định kỹ thuật đã đồng thuận (có evidence).
12. **Human Decisions Required** — quyết định cần con người trả lời.
13. **Dissent & Resolved Objections** — bất đồng + objection đã xử lý (kèm rationale).
14. **Evidence Index** — chỉ mục nguồn cho mọi claim.
15. **Council Status** — trạng thái hiện tại của SU.

Thiếu section hoặc sai thứ tự = SU không hợp lệ.

---

## Evidence rules

Mọi claim quan trọng phải trỏ về Evidence Index. Ba loại evidence:

- **Internal** — repo + file + line/symbol/process. **Ưu tiên GitNexus** (context/impact/process) hơn grep thô.
- **External** — direct authoritative URL + accessed date/version. Không dùng nguồn mơ hồ.
- **User intent** — reference tới task text / spec / explicit answer của user. **KHÔNG copy raw conversation** vào SU.

---

## Council Status enum (chỉ 5 giá trị)

- **DRAFT** — mới tạo từ discovery, chưa review.
- **CHALLENGED** — đã inline review, còn technical điểm cần merge/chốt.
- **WAITING_USER_DECISION** — còn Human Decision chờ user trả lời.
- **CONFIRMED** — user đã xác nhận, đủ điều kiện làm nguồn cho Planner.
- **DRIFTED** — nội dung đã đổi sau CONFIRMED (hoặc bị Planner reopen), phải challenge/confirm lại.

Không có giá trị nào khác.

---

## 5 điều kiện CHẶN CONFIRMED

SU **KHÔNG được** set CONFIRMED nếu còn bất kỳ điều nào:

1. Còn **technical correction chưa xử lý**.
2. **Human Decisions Required** còn item user **chưa trả lời**.
3. **Acceptance criteria không measurable**.
4. **Scope mâu thuẫn user intent**.
5. **Evidence quan trọng chỉ là suy đoán** (không có nguồn internal/external/user-intent thật).

Còn bất kỳ điều nào → giữ CHALLENGED hoặc WAITING_USER_DECISION.

---

## Immutable / DRIFTED rule

- SU **sau khi user xác nhận là immutable intent**.
- Nội dung SU đổi → `shared_understanding_sha256` **phải đổi** + status → **DRIFTED**.
- SU đang DRIFTED **KHÔNG được** dùng làm nguồn authoritative. Phải **challenge/confirm lại** (quay về Phase 2/4) trước khi Planner dùng.
