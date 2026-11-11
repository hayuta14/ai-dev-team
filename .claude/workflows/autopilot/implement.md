# Autopilot — Implement playbook

> Dùng bởi adapter `implement-v1`: CLI nạp file này theo kind ticket (`implement`). Nguồn: dogfood V2.1 lần 5, F-30 (worker viết code rồi mới hỏi).

## Hỏi trước khi code

- Acceptance của ticket này có dòng "gặp quyết định X ⇒ needs_decision" mà X chưa có trong mục "## Quyết định đã chốt cho ticket này" của prompt ⇒ trả needs_decision TRƯỚC khi viết hay sửa file code. Code viết trong attempt kết thúc bằng needs_decision bị controller reset bỏ.
- X đã có trong mục đó ⇒ code theo đúng option đã chọn, không hỏi lại.
- Mỗi needs_decision chỉ MỘT quyết định — options, `recommended_option_id`, `boundary_claims` theo output contract ở `escalation.md`.
