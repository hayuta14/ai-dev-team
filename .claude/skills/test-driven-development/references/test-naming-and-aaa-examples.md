# Ví dụ — đặt tên test + Arrange/Act/Assert

Minh hoạ cho 8 nguyên tắc ở `workflows/test-standards.md` — nội dung NAL Vietnam tách từ hub theo #231, KHÔNG phải hàng vendored như 2 file cạnh nó.

## Ví dụ

**Đúng** (tên mô tả + Arrange/Act/Assert):

```typescript
test("user_service_create_with_duplicate_email_throws_conflict", async () => {
  // Arrange
  const svc = new UserService(fakeRepo);
  await svc.create({ email: "a@nal.vn" });

  // Act + Assert
  await expect(svc.create({ email: "a@nal.vn" }))
    .rejects.toThrow(ConflictError);
});
```

```python
def test_health_take_damage_reduces_current_health():
    # Arrange
    health = HealthComponent(max_health=100, current_health=100)

    # Act
    health.take_damage(25)

    # Assert
    assert health.current_health == 75
```

**Sai**:

```typescript
test("test1", async () => {          // VI PHẠM: tên không mô tả
  const svc = new UserService(repo); // VI PHẠM: dùng repo thật (external state)
  const r = await svc.create({});    // VI PHẠM: không có arrange rõ
  expect(r).toBeTruthy();            // VI PHẠM: assert mơ hồ
});
```
