# Autopilot — Testcase playbook (RED)

> Dùng bởi adapter `testcase-v1`: CLI nạp file này theo kind ticket (`testcase`). Nguồn: dogfood V2.1 lần 3, F-15.

## RED phải là assertion fail

- Test mới phải đỏ vì **thiếu hành vi** (assertion), không vì import hay cú pháp. Verifier từ chối RED khi output (stdout + stderr) chứa ở **bất kỳ đâu** `ImportError`, `ModuleNotFoundError`, `Cannot find module`, `module not found` hoặc `SyntaxError` (không phân biệt hoa thường).
- Code đích chưa có mà `allowed_paths` chỉ gồm file test ⇒ **không** tạo stub/module rỗng ngoài `allowed_paths` cho import được; dùng một trong 2 mẫu dưới.

## Bộ RED phủ hành vi chính

- Bộ RED có ≥ 1 ca **hành vi chính** của symbol đích — ví dụ đầu tiên trong BLUEPRINT `## Hành vi`, assert **giá trị** đầu ra cho đầu vào điển hình (không chỉ kiểm không lỗi), kể cả khi `acceptance[]` chỉ liệt kê ca biên.
- **Không** viết test cho nhánh thuộc `## Quyết định mở` chưa chốt — nhánh đó chờ quyết định, test sau khi chốt.

## Mẫu 1 — symbol mới trong module có sẵn

```python
import pkg.mod as mod
fn = getattr(mod, "new_name", None)
self.assertTrue(callable(fn), "pkg.mod.new_name chưa có")
self.assertEqual(fn(2), 4)
```

JS/TS: `import * as mod from "../src/mod.js"` (module có sẵn) rồi `expect(typeof (mod as Record<string, unknown>).newName).toBe("function")`.

## Mẫu 2 — module mới

```python
import importlib.util
self.assertIsNotNone(importlib.util.find_spec("pkg.newmod"), "pkg.newmod chưa có")
newmod = importlib.import_module("pkg.newmod")
```

Package cha (`pkg`) phải có sẵn — thiếu cha thì `find_spec` ném lỗi import; khi đó assert từng tầng theo thứ tự (`"pkg"`, `"pkg.sub"`, `"pkg.sub.newmod"`). JS/TS (specifier là biến, không literal — tsc không báo thiếu module): `const specifier = "../src/new-mod.js"; let mod: unknown; try { mod = await import(specifier); } catch { mod = undefined; } expect(mod).toBeDefined();`

## Không làm

- Không import tên đích ở đầu file (`from pkg.mod import new_name`, `import { newName } from …`): thiếu tên là lỗi import ngay lúc nạp test.
- Không in message lỗi gốc (`print(e)`, `console.log(err)`, `self.fail(str(e))`): message đó chứa đúng chữ verifier chặn.
- Message tự viết, tên test, comment trong file test (traceback in lại source) cũng không chứa các chữ trên — viết "chưa có".
