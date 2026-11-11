# Autopilot — Testaudit (test có thể fail không?)

> Nguồn: spec nâng cấp §C2. Dùng bởi adapter `testaudit-v1` (kind `test`). Chỉ đọc + ghi báo cáo vào staging. **KHÔNG mutation.**

## Câu hỏi của phiên này

Suite xanh chứng minh điều gì? Nếu một test không thể đỏ dù code sai, thì nó xanh không có nghĩa gì cả. Phiên này soi đúng câu đó trên các test thuộc diff candidate.

## Giới hạn — đọc trước khi bắt đầu

Cách nghiêm ngặt để trả lời là **mutation**: phá có chủ ý một hành vi trong code sản phẩm, chạy recipe, kỳ vọng recipe ĐỎ; recipe vẫn xanh ⇒ test không bắt được bug đó.

**Phiên này KHÔNG làm vậy, và cũng không có quyền để làm.** Không adapter nào trong `command-adapters.md` được cấp quyền ghi ngoài `.avatar/attempt-output/**`; cấp quyền ghi `src/` cho đúng cái adapter có nhiệm vụ phá code là quyền rộng nhất bảng đổi lấy lý do yếu nhất (quyết định của user, 2026-09-15).

Hệ quả phải nói thẳng trong report, không được lờ đi:

- **BẮT được:** test không thể fail do cấu trúc — assertion bị `skip`/`only`, thân test rỗng, test không hề gọi tới code đã đổi, assert vào hằng số thay vì vào kết quả, `try/catch` nuốt lỗi rồi pass.
- **KHÔNG bắt được:** test chạy thật, assert thật, nhưng assert **sai thứ** (đúng cú pháp, sai ý nghĩa). Muốn bắt lớp này phải có mutation thật — là phase khác, kèm câu hỏi về quyền.

Report của bạn **phải** nêu giới hạn này trong `uncovered_areas[]`. Nói "test ổn" mà không kèm giới hạn là vi phạm điều cấm 6 của `evidence-discipline.md`.

## Trình tự bắt buộc

1. **Lấy diff candidate**: `git -C <repo> diff <base>...HEAD`. Tách hai nhóm: file **test** đã đổi/thêm, và file **code sản phẩm** đã đổi.

2. **Với mỗi file test trong diff, đọc nguyên văn** (Read, không đoán từ tên). Tìm:
   - `it.skip` / `xit` / `describe.skip` / `it.only` / `test.skip` / `@pytest.mark.skip` — assertion bị vô hiệu hoá. (Verifier đã chặn lớp này ở diff qua `containsDisabledAssertion`; vẫn kiểm để báo cáo đầy đủ, và vì test có thể đã bị skip từ TRƯỚC diff.)
   - Thân test rỗng, hoặc chỉ có lời gọi mà không có `expect`/`assert` nào.
   - `expect(true).toBe(true)` và mọi biến thể assert vào hằng số.
   - `try { ... } catch { }` bao quanh phần đáng lẽ phải fail.

3. **Đối chiếu ngược: mỗi hàm/hành vi đã đổi trong code sản phẩm có test nào THỰC SỰ gọi tới không?** Grep tên hàm/ký hiệu trong file test. Không hit ⇒ vùng code đổi mà không test nào chạm — phát hiện đáng giá nhất của phiên này.

4. **Đối chiếu với `acceptance[]` của ticket** (nếu ticket có khai): điều kiện nào không có test tương ứng thì nêu ra.

5. **Viết báo cáo** vào `.avatar/attempt-output/<run_id>/testaudit-report.md` (`<run_id>` nguyên văn từ binding). Mỗi phát hiện: đường dẫn file + tên test + lý do nó không thể fail. Không có phát hiện thì ghi rõ "không tìm thấy dấu hiệu nào ở các lớp đã liệt kê" — kèm giới hạn ở mục trên.

6. **`evidence[]` để rỗng `[]`.** Phiên này không chạy recipe đã duyệt. `summary` nêu số file test đã đọc + số phát hiện. `uncovered_areas[]` nêu giới hạn "không mutation".

## Không làm

- **Không sửa bất kỳ file nào ngoài staging** — không sửa test, không sửa code sản phẩm, không "thử phá xem sao".
- Không chạy recipe, không chạy suite (adapter này không được cấp `Bash(npm test*)`/`Bash(pytest*)`).
- Không kết luận "test tốt" / "coverage đủ" — bạn đo được sự VẮNG MẶT của một số lớp lỗi, không đo được sự hiện diện của chất lượng.
- Không đề xuất sửa test bằng `proposed_changes` trong phiên này; báo cáo là đầu ra, việc sửa thuộc ticket `fix`/`testcase` do người hoặc plan quyết định.
