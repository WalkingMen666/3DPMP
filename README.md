# 3DPMP 開發者指南 (Developer Guide)

歡迎加入 **3D Printing and Model-sharing Platform (3DPMP)** 專案！這份文件將協助您快速建立開發環境並開始貢獻程式碼。

## 1. 專案簡介

3DPMP 是一個結合 3D 模型分享社群與專業代印服務的平台。

- **Backend**: Python 3.13 + Django 5.x + DRF (API Server)
- **Frontend**: Vue.js 3 + Vite + Vue Router (SPA)
- **Worker**: Celery + PrusaSlicer (非同步切片處理)
- **Database**: PostgreSQL 18
- **Cache/Broker**: Redis 7.4
- **Infrastructure**: Podman (podman-compose)

### 功能現況

| 模組 | 功能 | 狀態 |
|------|------|------|
| **認證系統** | 本地註冊/登入 | ✅ 完成 |
| | Google OAuth 登入 | ✅ 完成 |
| | Token 認證 | ✅ 完成 |
| **模型管理** | STL 檔案上傳 | ✅ 完成 |
| | 縮圖/圖片上傳 | ✅ 完成 |
| | 模型分類/標籤 | ✅ 完成 |
| | 公開審核流程 | ✅ 完成 |
| | 被拒模型重新提交 | ✅ 完成 |
| **Marketplace** | 瀏覽公開模型 | ✅ 完成 |
| | 分類/特色篩選 | ✅ 完成 |
| | 模型詳情頁 | ✅ 完成 |
| **使用者** | 個人 Dashboard | ✅ 完成 |
| | 頭像上傳 | ✅ 完成 |
| | Display Name 設定 | ✅ 完成 |
| **管理後台** | Admin Dashboard | ✅ 完成 |
| | 模型審核 (Approve/Reject) | ✅ 完成 |
| | 審核記錄查詢 | ✅ 完成 |
| **切片系統** | PrusaSlicer 整合 | ⏳ 部分完成 |
| | 自動估價 | ⏳ 待完成 |
| **購物車** | 加入購物車 | ⏳ 待完成 |
| | 材料選擇 | ⏳ 待完成 |
| **訂單系統** | 訂單建立 | ⏳ 待完成 |
| | 訂單快照 | ⏳ 待完成 |
| | 訂單狀態追蹤 | ⏳ 待完成 |
| **配送系統** | 配送選項管理 | ⏳ 待完成 |
| | 地址簿 | ⏳ 待完成 |
| **折扣系統** | 全站折扣 | ⏳ 待完成 |
| | 優惠券 | ⏳ 待完成 |

## 2. 環境需求

在開始之前，請確保您的系統已安裝以下工具：

- **Container Runtime**: [Podman](https://podman.io/) + podman-compose
- **Python**: 3.13+ (本地開發用)
- **Node.js**: 22.x (本地開發用)
- **Git**

## 3. 快速啟動 (使用容器)

這是最快預覽整個系統的方式。

### 首次啟動

```bash
# 建置並啟動所有服務
podman-compose up --build -d

# 執行資料庫遷移
podman-compose exec backend python manage.py makemigrations
podman-compose exec backend python manage.py migrate

# 建立管理員帳號
podman-compose exec backend python manage.py createsuperuser
```

### 日常啟動

```bash
podman-compose up -d
```

啟動後，您可以訪問：

| 服務 | 網址 |
|------|------|
| Frontend | http://localhost:8080 |
| Backend API | http://localhost:8080/api/ |
| Swagger API Docs | http://localhost:8080/api/docs/ |
| ReDoc | http://localhost:8080/api/redoc/ |
| Django Admin | http://localhost:8080/api/admin/ |

### 停止服務

```bash
podman-compose down

# 完全重置 (包含資料庫)
podman-compose down -v
```

---

## 4. 本地開發設定 (Local Development)

如果您需要開發特定功能，建議在本地運行該服務，以便獲得更快的除錯與熱重載 (Hot Reload) 體驗。

### 4.1 後端開發 (Backend)

後端位於 `backend/` 目錄。

```bash
cd backend

# 建立虛擬環境
python3 -m venv venv
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 設定環境變數 (連接容器內的 PostgreSQL)
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=3dpmp
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres

# 執行遷移與啟動伺服器
python manage.py migrate
python manage.py runserver
```

### 4.2 前端開發 (Frontend)

前端位於 `frontend/` 目錄。

```bash
cd frontend

# 安裝依賴
npm install

# 啟動開發伺服器
npm run dev
```

開發伺服器運行在 http://localhost:5173，API 請求會代理到 http://localhost:8000。

---

## 5. 專案結構說明

```text
3dprint/
├── backend/                    # Django 後端
│   ├── Dockerfile              # 後端容器定義 (含 PrusaSlicer)
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/                 # Django 專案設定
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── celery.py
│   │   └── wsgi.py
│   ├── apps/                   # Django 應用程式
│   │   ├── users/              # 使用者認證 (User, Customer, Employee)
│   │   ├── models/             # 3D 模型管理 (Model, ModelImage, ModelReviewLog)
│   │   ├── materials/          # 材料與購物車 (Material, CartItem)
│   │   ├── shipping/           # 配送選項 (ShippingOption, SavedAddress)
│   │   ├── orders/             # 訂單管理 (Order, OrderItem, OrderLog)
│   │   └── discounts/          # 折扣系統 (Discount, Coupon, GlobalDiscount)
│   └── docs/                   # 後端文件
│       └── MODELS_DEVIATIONS.md  # Models 與 DBML 差異說明
│
├── frontend/                   # Vue.js 前端
│   ├── Dockerfile              # 前端容器定義 (Build + Nginx)
│   ├── nginx.conf              # Nginx 設定 (API 代理)
│   ├── package.json
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/             # Vue Router 路由設定
│       └── views/              # 頁面元件
│           ├── HomeView.vue
│           ├── LoginView.vue
│           └── RegisterView.vue
│
├── docker-compose.yml          # 服務編排定義
├── database/                   # SQL 檔案
│   ├── schema.sql              # 資料庫結構定義
│   ├── seed_data.sql           # 範例資料
│   └── README.md               # SQL 使用說明
├── requirements.md             # 詳細需求規格 (含 DBML Schema)
├── version.md                  # 軟體版本矩陣
└── README.md                   # 本說明文件
```

## 6. Django Apps 說明

| App | 說明 | 主要 Models |
|-----|------|-------------|
| `users` | 使用者認證與角色 | User, Customer, Employee |
| `models` | 3D 模型上傳與審核 | Model, ModelImage, ModelReviewLog |
| `materials` | 材料定義與購物車 | Material, CartItem |
| `shipping` | 配送選項與地址簿 | ShippingOption, SavedAddress |
| `orders` | 訂單與快照機制 | Order, OrderItem, OrderLog |
| `discounts` | 折扣與優惠券系統 | Discount, GlobalDiscount, Coupon, IsAffected, CouponRedemption |

詳細的 Model 設計與 DBML 差異說明請參考：[backend/docs/MODELS_DEVIATIONS.md](backend/docs/MODELS_DEVIATIONS.md)

## 7. API 文件

本專案使用 **drf-spectacular** 自動產生 OpenAPI 文件：

- **Swagger UI**: http://localhost:8080/api/docs/
- **ReDoc**: http://localhost:8080/api/redoc/
- **OpenAPI Schema**: http://localhost:8080/api/schema/

## 8. 常用指令備忘

### 容器管理

```bash
# 重建容器 (修改 Dockerfile 後)
podman-compose build --no-cache
podman-compose up -d --force-recreate

# 查看 Log
podman-compose logs -f backend
podman-compose logs -f worker

# 進入容器
podman-compose exec backend bash
podman-compose exec db psql -U postgres -d 3dpmp
```

### Django 管理

```bash
# 建立新的 migrations
podman-compose exec backend python manage.py makemigrations

# 執行 migrations
podman-compose exec backend python manage.py migrate

# 建立超級使用者
podman-compose exec backend python manage.py createsuperuser

# Django shell
podman-compose exec backend python manage.py shell
```

### 資料庫操作

```bash
# 重置資料庫 (開發用)
podman-compose down -v
podman-compose up -d
podman-compose exec backend python manage.py migrate
```

## 9. 注意事項 (Podman 使用者)

本專案使用 **Ubuntu 25.04** 作為 Base Image，並使用 **PostgreSQL 18**。

- **SIGTERM 問題**: 已在 docker-compose.yml 設定 `stop_grace_period: 3s` 解決 Podman 關閉延遲問題
- **快取問題**: 修改程式碼後若容器未更新，執行 `podman-compose build --no-cache`
- **權限問題**: 若遇到 volume 權限錯誤，可嘗試 `podman unshare chown -R 999:999 ./data`

## 10. Google OAuth 設定

若要啟用 Google 登入功能，請依照以下步驟設定：

### 10.1 Google Cloud Console 設定

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立新專案或選擇現有專案
3. 啟用 **Google+ API** 或 **Google Identity Services**
4. 前往 **APIs & Services > Credentials**
5. 點擊 **Create Credentials > OAuth 2.0 Client ID**
6. 選擇 **Web application**
7. 設定 **Authorized JavaScript origins**：
   - 本地開發：`http://localhost:5173`
   - Docker 環境：`http://localhost:8080`
   - 生產環境：`https://your-domain.com`
8. 設定 **Authorized redirect URIs**：
   - `http://localhost:8000/api/auth/google/callback/`
   - `http://localhost:8080/api/auth/google/callback/`

### 10.2 後端環境變數設定

在 `backend/` 目錄下建立 `.env` 檔案：

```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

### 10.3 常見問題

**403 error: disallowed_useragent 或 origin_mismatch**
- 確認 JavaScript origins 包含您正在使用的網址
- 確認沒有多餘的斜線或端口號
- Google Cloud Console 設定變更可能需要 5-10 分鐘生效

**COOP (Cross-Origin-Opener-Policy) 問題**
- 本專案已設定 `same-origin-allow-popups` header
- 若仍有問題，請檢查瀏覽器 Console 錯誤訊息

## 11. 貢獻指南

1. Fork 此專案
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request
