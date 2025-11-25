# 3DPMP 開發者指南 (Developer Guide)

歡迎加入 **3D Printing and Model-sharing Platform (3DPMP)** 專案！這份文件將協助您快速建立開發環境並開始貢獻程式碼。

## 1. 專案簡介

3DPMP 是一個結合 3D 模型分享社群與專業代印服務的平台。

* **Backend**: Python 3.13 + Django 5.x (API Server)
* **Frontend**: Vue.js 3 + Vite (SPA)
* **Worker**: Celery + PrusaSlicer (非同步切片處理)
* **Database**: PostgreSQL 18
* **Infrastructure**: Docker / Podman

## 2. 環境需求

在開始之前，請確保您的系統已安裝以下工具：

* **Container Runtime**: [Podman](https://podman.io/) (推薦) 或 Docker
* **Python**: 3.13+
* **Node.js**: 20.x 或 22.x
* **Git**

## 3. 快速啟動 (使用容器)

這是最快預覽整個系統的方式。我們使用 `docker-compose` (或 `podman-compose`) 來編排服務。

### 啟動服務

```bash
# 使用 Docker Compose
docker-compose up --build

# 或者使用 Podman
podman-compose up --build
```

啟動後，您可以訪問：

* **Frontend**: [http://localhost:8080](http://localhost:8080)
* **Backend API**: [http://localhost:8000/api/](http://localhost:8000/api/) (需先實作 API)

### 停止服務

```bash
docker-compose down
# 或
podman-compose down
```

---

## 4. 本地開發設定 (Local Development)

如果您需要開發特定功能，建議在本地運行該服務，以便獲得更快的除錯與熱重載 (Hot Reload) 體驗。

### 4.1 後端開發 (Backend)

後端位於 `backend/` 目錄。

1. **進入目錄**

   ```bash
   cd backend
   ```

2. **建立虛擬環境**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # venv\Scripts\activate   # Windows
   ```

3. **安裝依賴**

   ```bash
   pip install -r requirements.txt
   ```

4. **設定環境變數**

   確保您的資料庫設定正確。開發時可以使用 SQLite 或連接到 Docker 啟動的 Postgres。

5. **執行遷移與啟動伺服器**

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

### 4.2 前端開發 (Frontend)

前端位於 `frontend/` 目錄。

1. **進入目錄**

   ```bash
   cd frontend
   ```

2. **安裝依賴**

   ```bash
   npm install
   ```

3. **啟動開發伺服器**

   ```bash
   npm run dev
   ```

   開發伺服器通常運行在 [http://localhost:5173](http://localhost:5173)。

---

## 5. 專案結構說明

```text
3dprint/
├── backend/                # Django 後端程式碼
│   ├── Dockerfile          # 後端容器定義 (含 PrusaSlicer)
│   ├── manage.py
│   └── requirements.txt
├── frontend/               # Vue.js 前端程式碼
│   ├── Dockerfile          # 前端容器定義 (Build + Nginx)
│   ├── nginx.conf          # 容器內的 Nginx 設定
│   ├── package.json
│   └── src/
├── docker-compose.yml      # 服務編排定義
├── requirements.md         # 詳細需求規格
├── version.md              # 軟體版本矩陣
└── README.md               # 本說明文件
```

## 6. 注意事項 (Podman 使用者)

本專案在 `version.md` 中指定使用 **Ubuntu 25.04** 作為 Base Image，並使用 **PostgreSQL 18**。

如果您使用 **Podman**：

* **權限問題**: 如果遇到資料庫掛載權限錯誤 (Permission Denied)，這是因為 Podman 預設使用 Rootless 模式。您可能需要在 `docker-compose.yml` 的 db 服務中加入 `userns_mode: keep-id`，或手動調整 volume 權限。
* **網路**: Podman 的網路行為與 Docker 略有不同，但在標準 Compose 設定下通常能正常運作。

## 7. 常用指令備忘

* **重建容器**: `docker-compose up --build`
* **查看 Log**: `docker-compose logs -f [service_name]` (例如 `docker-compose logs -f backend`)
* **進入容器**: `docker-compose exec backend /bin/bash`
