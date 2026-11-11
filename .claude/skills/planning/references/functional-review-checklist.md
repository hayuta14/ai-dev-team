# Functional Review Checklist (Inline)

Checklist 4 góc nhìn để **Main tự đối chiếu** draft Shared Understanding (SU) ở Phase 3 — thay cho 4-lens council. **KHÔNG spawn agent** cho bước này; Main đọc SU và tự trả lời từng nhóm câu hỏi.

Đây là bước **đối chiếu draft SU**, không phải review code, không chạy gì.

---

## Góc 1 — Business

- Problem/value đã rõ chưa? Đúng vấn đề cần giải?
- **Actors** (ai dùng, ai bị ảnh hưởng) đã liệt kê đủ?
- **Business rules** ràng buộc nghiệp vụ đã nêu?
- **User journeys** chính đã cover?
- **Scope / out-of-scope** phân định rõ, không mơ hồ?
- **Acceptance criteria** có **measurable** không (đo được, không mông lung)?

## Góc 2 — Backend

- **API** contract (endpoint, request/response) có ràng buộc gì?
- **Data** model / schema / migration cần đụng tới?
- **Integration** với service/hệ thống khác?
- **Auth** (authN/authZ) yêu cầu gì?
- **Security** (input validation, data protection) điểm nào?
- **Operations** (logging, rate limit, error handling, observability)?

## Góc 3 — Frontend

- **User flow** trên UI có mạch lạc?
- **UI states** (loading / empty / error / success) đã tính?
- **Client contracts** (kiểu dữ liệu, API call qua đúng layer) khớp backend?
- **Accessibility / responsiveness** có yêu cầu gì cần ghi vào SU?

## Góc 4 — Test

- **Risk-based test strategy**: chỗ rủi ro cao test kỹ hơn.
- **Testability**: thiết kế có test được không?
- **Edge / failure cases** đã liệt kê?
- **Requirement-to-verification traceability**: mỗi requirement map được tới cách verify?

---

## Output mỗi góc nhìn

Mỗi góc phải cho ra 4 loại:

- **confirmed claims** — điểm trong SU đã đúng, có evidence.
- **corrections** — sửa lại, **kèm evidence**.
- **objections** — phản đối (nếu không evidence → sẽ bị reject, ghi rationale vào Dissent).
- **DECISION_REQUIRED** — điều phải hỏi user, không tự quyết.

Sau khi xong cả 4 góc: Main tổng hợp thành `per_lens_counts` (đếm nguyên mỗi ô lens×disposition, KHÔNG nội dung text) ghi vào projection state — xem protocol Phase 3 + appendix §3.

---

## Ranh giới rõ (bắt buộc tuân)

- **KHÔNG chạy test** ở bước review này.
- **KHÔNG áp TDD** ở bước này — chỉ **đối chiếu draft SU**, chưa tới lúc viết test.
- **Consensus chỉ dùng cho technical facts CÓ evidence.**
- Các nhóm sau **PHẢI là DECISION_REQUIRED** (hỏi user, KHÔNG lấy đa số):
  - pricing / billing
  - legal / compliance
  - data-residency
  - target metric không có trong spec
  - build-vs-buy
  - business scope
