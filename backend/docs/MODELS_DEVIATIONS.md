# Django Models 實作差異說明

本文件說明 Django Models 實作與 `requirements.md` 中 DBML Schema 的差異及其理由。

## 概覽

整體架構遵循 DBML 設計，但基於 Django ORM 特性、最佳實踐及實務考量進行了以下調整。

---

## 1. 欄位命名慣例

### 差異
| DBML | Django Implementation |
|------|----------------------|
| `user_id`, `model_id` 等 | `id` |
| `owner_id` (FK) | `owner` (ForeignKey) |
| `creation_date` | `created_at` |

### 理由
- **主鍵命名**: Django 慣例使用 `id` 而非 `{table}_id`，ORM 會自動處理資料表前綴
- **外鍵命名**: Django ForeignKey 欄位不需要 `_id` 後綴，ORM 會自動產生 `{field}_id` 欄位
- **時間戳記**: `created_at`/`updated_at` 是 Django 社群的標準命名慣例，搭配 `auto_now_add` 和 `auto_now`

---

## 2. User Model

### 差異
| DBML | Django Implementation |
|------|----------------------|
| `password_hash` | 使用 AbstractUser 內建的 `password` |
| `creation_date` | 使用 AbstractUser 內建的 `date_joined` |

### 理由
- Django AbstractUser 已內建完整的密碼雜湊機制（PBKDF2 + SHA256）
- `date_joined` 是 Django auth 標準欄位，與第三方套件（如 django-allauth）相容
- 避免重複實作已有的安全機制

---

## 3. Material Model

### 差異
| DBML | Django Implementation |
|------|----------------------|
| `density_g_cm2` | `density_g_cm3` |
| 無 | 新增 `is_active` 欄位 |
| 無 | 新增 `created_at`, `updated_at` |

### 理由
- **密度單位**: DBML 中的 `g/cm²` 是面積單位，但材料密度應為體積單位 `g/cm³`（這可能是 DBML 的筆誤）
- **軟刪除支援**: `is_active` 允許停用材料而不影響歷史訂單的關聯完整性
- **審計追蹤**: 時間戳記便於追蹤材料價格變動歷史

---

## 4. CartItem Model

### 差異
| DBML | Django Implementation |
|------|----------------------|
| 無唯一約束 | 新增 `unique_cart_item_per_customer` constraint |
| 無時間欄位 | 新增 `created_at`, `updated_at` |

### 理由
- **唯一約束**: 防止同一客戶對相同 model + material 組合重複加入購物車，改為更新數量
- **時間欄位**: 便於實作「購物車過期清理」功能及追蹤使用者行為

---

## 5. ShippingOption & SavedAddress

### 差異
| DBML | Django Implementation |
|------|----------------------|
| `type` 為自由字串 | `type` 使用 `ShippingType` TextChoices |
| 無 | SavedAddress 新增 `is_default` 欄位 |

### 理由
- **枚舉約束**: 使用 TextChoices 確保 shipping type 的一致性，避免拼寫錯誤
- **預設地址**: `is_default` 改善使用者體驗，結帳時自動選擇常用地址

---

## 6. Order & OrderItem

### 差異
| DBML | Django Implementation |
|------|----------------------|
| `status` 值未定義 | 使用 `OrderStatus` TextChoices 定義完整狀態機 |
| 無 | Order 新增 `notes`, `tracking_number`, `updated_at` |
| 無 | OrderItem 新增 `notes` |
| 無唯一約束 | OrderItem 新增 `unique_item_number_per_order` |

### 理由

**OrderStatus 狀態機定義:**
```
PENDING → CONFIRMED → PROCESSING → PRINTING → QUALITY_CHECK 
→ READY_TO_SHIP → SHIPPED → DELIVERED → COMPLETED
                ↘ CANCELLED / REFUNDED (可從多個狀態轉換)
```

- **狀態枚舉**: 明確定義訂單生命週期，支援前端狀態顯示和狀態轉換驗證
- **物流追蹤**: `tracking_number` 儲存物流單號，整合出貨通知
- **備註欄位**: 支援客戶特殊需求（如印刷方向、顏色深淺偏好）
- **項目序號約束**: 確保每筆訂單內的 `item_number` 不重複

---

## 7. OrderLog

### 差異
| DBML | Django Implementation |
|------|----------------------|
| 無 | 新增 `previous_status` 欄位 |
| 無 | 新增 `notes` 欄位 |

### 理由
- **前一狀態**: 便於追蹤狀態變更歷程，支援狀態轉換驗證和回滾分析
- **備註**: 允許員工記錄狀態變更原因（如退款理由、延遲說明）

---

## 8. Discount System

### 差異
| DBML | Django Implementation |
|------|----------------------|
| 無 | Discount 新增 `description`, `is_active` 欄位 |
| 無 | GlobalDiscount 新增 `priority` 欄位 |
| 無 | IsAffected 新增 `discount_amount` 欄位 |
| 無 | CouponRedemption 新增 `discount_snapshot_info`, `discount_amount` |

### 理由
- **描述**: 支援行銷文案顯示（如「夏季促銷：全站九折」）
- **啟用狀態**: 允許暫停折扣活動而不刪除設定
- **優先序**: 多個全域折扣時決定套用順序（先折固定金額再折百分比，或反之）
- **折扣金額**: 預先計算並儲存實際折扣金額，避免重複計算

---

## 9. Model App 命名

### 差異
使用 `label = 'printing_models'` 而非 Django 預設的 app label

### 理由
- `apps.models` 與 Django 內建的 `django.db.models` 模組名稱衝突
- 設定 `label = 'printing_models'` 避免命名空間衝突
- 資料表仍使用 `db_table = 'model'` 保持與 DBML 一致

---

## 10. 外鍵 on_delete 策略

| Model | Field | on_delete | 理由 |
|-------|-------|-----------|------|
| Model | owner | CASCADE | 用戶刪除時，其模型一併刪除 |
| ModelReviewLog | reviewer | PROTECT | 保留審核歷史，不允許刪除有審核記錄的員工 |
| CartItem | material | PROTECT | 購物車內有材料時不允許刪除該材料 |
| Order | customer | PROTECT | 訂單記錄永久保留，不允許刪除有訂單的客戶 |
| Order | assignee | SET_NULL | 員工離職時，訂單保留但負責人清空 |
| OrderItem | model | PROTECT | 保留訂單歷史，不允許刪除有訂單的模型 |
| CouponRedemption | coupon | PROTECT | 保留兌換記錄，不允許刪除有使用記錄的優惠券 |

---

## 11. 新增的索引與約束

以下約束在 DBML 中未明確定義，但為資料完整性所需：

```python
# CartItem: 防止重複項目
UniqueConstraint(fields=['customer', 'model', 'material'], name='unique_cart_item_per_customer')

# OrderItem: 確保項目序號唯一
UniqueConstraint(fields=['order', 'item_number'], name='unique_item_number_per_order')

# IsAffected: 防止同一折扣重複套用
UniqueConstraint(fields=['order', 'global_discount'], name='unique_global_discount_per_order')

# CouponRedemption: 透過 OneToOneField(order) 確保每訂單最多一張優惠券
```

---

## 12. 保留的 DBML 設計決策

以下重要設計原則完全遵循 DBML：

1. **UUID 主鍵**: 所有 Model 使用 UUID 作為主鍵
2. **快照機制**: `Order.ship_snapshot`, `OrderItem.price_snapshot`, `OrderItem.slicing_info_snapshot` 確保訂單資料不可變
3. **無外鍵至可變表**: Order 不直接關聯 ShippingOption 或 SavedAddress
4. **EER 特化**: User → Customer/Employee, Discount → GlobalDiscount/Coupon 使用 OneToOneField 實作
5. **M:N 記錄**: IsAffected 處理全域折扣與訂單的多對多關係
6. **1:1 優惠券**: CouponRedemption.order 的 unique constraint 強制每訂單最多一張優惠券

---

## 遷移注意事項

首次遷移時需執行：
```bash
podman-compose exec backend python manage.py makemigrations
podman-compose exec backend python manage.py migrate
```

若有既存資料，建議在開發環境重建資料庫：
```bash
podman-compose down -v  # 刪除 volume
podman-compose up -d
podman-compose exec backend python manage.py migrate
podman-compose exec backend python manage.py createsuperuser
```
