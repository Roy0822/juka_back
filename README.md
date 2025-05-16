📌 Note: This repository was reuploaded and commit history reset for demonstration purposes. Only parts of the projects are included in this repository and info such as API keys and env are hidden already, hence this project cannot be used. This repository is created solely for the purpose of submitting transfer application materials for the Department of Computer Science and Information Engineering at NTU（臺灣大學資訊工程學系 轉學書面審查報告用）. Any other form of use is strictly prohibited. Please respect the intended usage and do not repurpose or distribute this code for any other purposes.




# Juka 揪咖 Backend API

Juka 揪咖是一個即時揪團購物、共乘省錢的行動平台，幫助使用者尋找附近的好友進行各種團購活動。

## 主要功能

- 使用者 GPS 位置上傳與更新
- 揪團活動（Campaign）的建立與搜尋
- 即時聊天（基於 WebSocket）
- 推送通知（Firebase Cloud Messaging）
- AI 生成文案建議
- 商家資訊管理
- 使用者社交互動（評價、好友）

## 技術架構

- FastAPI 為 Web 框架
- SQLAlchemy + PostgreSQL / PostGIS 為資料庫
- Firebase Cloud Messaging (FCM) 為推送服務
- WebSocket 為即時通訊
- Google OAuth 認證
- Docker 部署

## 安裝與運行

### 環境需求

- Python 3.8+
- PostgreSQL 13+ (with PostGIS extension)
- Docker (選用)

### 設定 .env 檔案

在專案根目錄建立 `.env` 檔案並填入以下設定：

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/juka_db
APP_ENV=development
AI_SERVER_URL=http://ai-server.example.com
AI_ACCESS_TOKEN=your_ai_access_token_here
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback/google
APP_SCHEME=juka://
SECRET_KEY=your_secret_key_here

# Firebase 推送通知設定
FCM_AUTH_METHOD=service_account  # 選項: service_account, server_key
FCM_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-project-id",...}
# 或使用檔案路徑: FCM_SERVICE_ACCOUNT_JSON=/path/to/service-account.json

# 舊式 FCM 伺服器金鑰（不建議使用）
# FCM_AUTH_METHOD=server_key
# FCM_SERVER_KEY=your_fcm_server_key_here

# 檔案上傳設定 (可選)
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=10485760
STORAGE_TYPE=local
PUBLIC_URL_PREFIX=http://localhost:8000

# S3 設定 (若使用 S3 儲存)
# STORAGE_TYPE=s3
# S3_BUCKET=your-bucket-name
# S3_REGION=ap-northeast-1
# S3_ACCESS_KEY=your-access-key
# S3_SECRET_KEY=your-secret-key
# PUBLIC_URL_PREFIX=https://cdn.example.com
```

### Firebase Cloud Messaging 設定

系統支援三種方式設置 Firebase Admin SDK 憑證：

1. **放置 JSON 檔案在專案根目錄**：
   - 將 Firebase Admin SDK 服務帳號 JSON 檔案命名為 `Juka Firebase Admin SDK.json` 並放在專案根目錄
   - 這是最簡單的方法，系統會自動檢測並使用此檔案

2. **透過 .env 使用 JSON 字串**：
   - 在 .env 中設定 `FCM_SERVICE_ACCOUNT_JSON` 為 JSON 字串：
     ```
     FCM_AUTH_METHOD=service_account
     FCM_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-project-id",...}
     ```

3. **透過 .env 指定檔案路徑**：
   - 在 .env 中設定 `FCM_SERVICE_ACCOUNT_JSON` 為檔案路徑：
     ```
     FCM_AUTH_METHOD=service_account
     FCM_SERVICE_ACCOUNT_JSON=/path/to/service-account.json
     ```

在開發環境下，若未設定 Firebase 憑證，系統將在不使用 FCM 的情況下運作，所有推送通知會以模擬方式在終端機上顯示。

### 在遠端資料庫設定 PostGIS

1. 連接到您的遠端 PostgreSQL 資料庫伺服器
2. 執行提供的 SQL 腳本以安裝 PostGIS 擴展：
   ```
   psql -h your-remote-db-server -U username -d juka_db -f setup_postgis_remote.sql
   ```
   或直接將腳本內容複製到 psql 命令列執行

### 在本機運行

1. 安裝相依套件：
   ```
   pip install -r requirements.txt
   ```

2. 啟動 PostgreSQL 並建立資料庫：
   ```
   createdb juka_db
   ```

3. 初始化 PostGIS 擴展：
   ```
   psql -d juka_db -f initialize_postgis.sql
   ```

4. 初始化資料庫表格：
   ```
   python init_db.py
   ```

5. 啟動 API 伺服器：
   ```
   uvicorn app.main:app --reload
   ```

6. 訪問 API 文檔：http://localhost:8000/docs

### 使用 Docker 運行

1. 建置 Docker 映像：
   ```
   docker build -t juka-backend .
   ```

2. 運行容器：
   ```
   docker run -p 8000:8000 --env-file .env juka-backend
   ```

### 使用 Docker Compose 運行

1. 確保您的 `.env` 檔案中 `DATABASE_URL` 指向遠端資料庫伺服器：
   ```
   DATABASE_URL=postgresql://username:password@your-remote-db-server:5432/juka_db
   ```

2. 啟動 API 服務：
   ```
   docker-compose up
   ```

3. 訪問 API 文檔：http://localhost:8000/docs

## API 文檔

主要 API 端點：

- `/auth` - 認證相關端點
- `/users` - 使用者管理
- `/campaigns` - 揪團活動
- `/businesses` - 商家資訊
- `/chat` - 聊天功能
- `/ai` - AI 生成功能

詳細 API 文檔請訪問運行中的 Swagger 文檔：http://localhost:8000/docs

## 開發模式功能

在開發環境下 (`APP_ENV=development`)，系統提供以下方便開發的功能：

- `/auth/dev-login` - 快速使用開發者帳號登入
- Google OAuth 登入流程的 early return
- 模擬 FCM 推送與 AI 服務整合 
