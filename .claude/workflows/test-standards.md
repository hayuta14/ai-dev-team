# Test Standards

> Quy tắc viết test chung của tổ chức. Áp dụng cho mọi dự án, mọi ngôn ngữ.

## Nguyên tắc cốt lõi

- **Đặt tên test:** theo pattern `test_[hệ thống]_[tình huống]_[kết quả mong đợi]` — đọc tên là biết test gì.
- **Cấu trúc Arrange / Act / Assert** rõ ràng trong mọi test.
- **Unit test KHÔNG phụ thuộc external state** (filesystem, network, database).
- **Integration test phải tự dọn dẹp** sau khi chạy.
- **Performance test phải nêu ngưỡng chấp nhận** và fail nếu vượt.
- **Test data định nghĩa trong test hoặc fixture riêng** — không dùng shared mutable state.
- **Mock external dependency** — test phải nhanh và deterministic.
- **Mỗi bug fix phải có regression test** đủ sức bắt lại đúng bug gốc.

## Ví dụ

Ví dụ minh hoạ cho 8 quy tắc trên — cả TypeScript lẫn Python, cả ca đúng lẫn ca sai — nằm ở file reference của skill `test-driven-development`.

**BẮT BUỘC:** đọc `.claude/skills/test-driven-development/references/test-naming-and-aaa-examples.md` **TRƯỚC KHI** viết ca test đầu tiên.
