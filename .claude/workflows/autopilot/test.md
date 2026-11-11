# Autopilot — Test playbook (chạy suite, đọc, phân loại)

> Dùng bởi adapter `test-v1`: CLI nạp file này theo kind ticket (`test`). Cùng hợp đồng với mode `run` của agent `tester` (`agents/tester.md`); phiên này KHÔNG spawn agent đó (`maxInternalSubagents: 0`), tự áp các bước dưới.

## Ai làm gì

- **Controller** chạy lại `verification_recipe` sau khi nhận result và tự sinh report; exit khác 0 ⇒ attempt bị từ chối. `exit_code`/`sha256` worker khai KHÔNG được dùng để quyết.
- **Phiên này** chạy suite để QUAN SÁT, đọc hết output, phân loại từng fail và khai đúng trạng thái. Giá trị của phiên là `summary` + `uncovered_areas[]` + `remaining_work[]` chính xác, không phải con số xanh.

## Trình tự

1. **Typecheck trước nếu repo có cấu hình** (`npm run typecheck` khi `package.json` có script đó; `deno check <entry>` khi repo có `deno.json`). Không có cấu hình ⇒ ghi "typecheck: không cấu hình" vào `uncovered_areas`. Lỗi kiểu được báo trước test, không thay test.
2. **Chạy đúng recipe đã duyệt** (lệnh trong mục "Lệnh recipe được cấp thêm" của prompt, hoặc `npm test`/`pytest` khi recipe chính là lệnh đó). Không tự chọn lệnh khác, không thu hẹp phạm vi để cho xanh.
3. **Đọc hết output**, lấy dòng tổng (`Tests  N failed | M passed` với Vitest, `N passed, M failed` với pytest). Với mỗi fail: tên test, `file:line`, 1–5 dòng message.
4. **Phân loại mỗi fail** theo file mà lát đã đổi — `changed_files` của các ticket trong mục Output dependencies của prompt, hoặc `git -C <worktree> log --name-only` trên các commit của chúng (`base_sha` của attempt là HEAD lúc bắt đầu, nên `base_sha..HEAD` rỗng): file test (hoặc symbol nó gọi) nằm trong file đã đổi ⇒ `mới`; có trong baseline exceptions của prompt ⇒ `có sẵn (baseline)`; còn lại ⇒ `có sẵn (chưa kiểm)`, vì phiên không checkout base để chứng minh.
5. **Flaky**: fail có thể chạy lại MỘT lần, riêng lẻ, theo tên (`npm test -- <file> -t "<tên>"`, `pytest <file>::<tên>`). Lần hai pass ⇒ ghi `flaky` kèm cả hai kết quả; vẫn KHÔNG tính là xanh.
6. **Khai result**:
   - Recipe exit 0, không flaky ⇒ `outcome: done`.
   - Có fail (kể cả flaky, kể cả có sẵn) ⇒ `outcome: failed`, `error_class` nêu số fail mới / có sẵn / flaky. Controller cũng sẽ đỏ trên cùng recipe; khai `done` là khai sai.
   - Fail có sẵn ngoài phạm vi ticket ⇒ thêm vào `remaining_work[]` (ticket sửa riêng, do người hoặc plan quyết), không lờ đi.
   - `evidence[]` đúng 1 mục theo session prompt (`recipe_id`, `report_path` = `report_glob`, `sha256` placeholder 64 số 0, `exit_code` quan sát được).

## Không làm

- Không sửa code, test, fixture, snapshot (phiên không có Edit; `-u`/`--update-snapshots`, `.only`, skip, nới timeout đều cấm).
- Không lặp lại suite tới khi xanh; ngoài một lần chạy lại theo bước 5.
- Không in secret/dữ liệu cá nhân mà test fail in ra; che rồi ghi đã che.
- Không kết luận "test tốt" khi suite xanh; suite xanh chỉ nói các test hiện có pass (xem `testaudit.md` cho câu hỏi test có thể đỏ không).
