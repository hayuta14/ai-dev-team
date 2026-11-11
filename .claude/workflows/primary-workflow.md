# Quy trình chính (Primary Workflow)


#### 1. Triển khai code (Code Implementation)
- Trước khi bắt đầu, delegate cho agent `planner` để tạo implementation plan với TODO tasks trong thư mục `./plans`.
- Chỉ dùng agent `researcher` (0–2 song song, mỗi agent một câu hỏi) khi có câu hỏi kỹ thuật bên ngoài cần bằng chứng, rồi báo cáo lại cho `planner` để hoàn thiện plan.
- Viết code sạch, dễ đọc, dễ bảo trì.
- Tuân theo architectural pattern đã có.
- Implement feature đúng theo specification.
- Xử lý edge case và scenario lỗi.
- **KHÔNG** tạo file "enhanced" mới — sửa trực tiếp vào file hiện hữu.
- **[QUAN TRỌNG]** Sau khi tạo/sửa file code, chạy compile command/script để check lỗi compile.

#### 2. Kiểm thử (Testing)
- Delegate cho agent `tester` để chạy test và phân tích báo cáo tổng hợp.
  - Viết unit test toàn diện.
  - Đảm bảo coverage cao.
  - Test các scenario lỗi.
  - Validate yêu cầu performance.
- Test là yếu tố then chốt để đảm bảo chất lượng và độ tin cậy của code, **KHÔNG** bỏ qua test fail chỉ để pass build.
- **QUAN TRỌNG:** Đảm bảo không dùng fake data, mock, mánh khoé, giải pháp tạm để pass build hoặc GitHub Actions.
- **QUAN TRỌNG:** Luôn fix các test fail theo recommendation và delegate `tester` chạy lại, chỉ kết thúc session khi tất cả test đã pass. Truyền `RANGE` cho `tester` để nó phân loại fail `new` / `pre-existing`; fail `pre-existing` (có sẵn trước thay đổi) thì báo user, không tự sửa trong phạm vi task và không bỏ qua.

#### 3. Chất lượng code (Code Quality)
- Sau khi xong implementation, delegate cho agent `code-reviewer` để review code.
- Tuân theo coding standard và convention.
- Viết code self-documenting (tự giải thích).
- Thêm comment có ý nghĩa cho logic phức tạp.
- Tối ưu cho performance và maintainability.

#### 4. Tích hợp (Integration)
- Luôn tuân theo plan do `planner` đưa ra.
- Đảm bảo tích hợp mượt với code có sẵn.
- Tuân thủ chính xác API contract.
- Giữ backward compatibility.
- Document các breaking change.
- Delegate cho agent `docs-manager` để cập nhật docs trong thư mục `./docs` nếu có.

#### 5. Debug (Debugging)
- Khi user báo bug/issue trên server hoặc CI/CD pipeline, delegate cho agent `debugger` để chạy test và phân tích báo cáo tổng hợp.
- Đọc báo cáo từ `debugger`, implement fix.
- Delegate cho agent `tester` chạy test và phân tích báo cáo.
- Nếu `tester` báo test fail, fix theo recommendation và lặp lại từ **Bước 2**.
