from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.database import create_tables
from app.controllers import auth, users, campaigns, businesses, chat, ai, uploads

app = FastAPI(
    title="Juka 揪咖 API",
    description="幫助使用者即時揪團購物、共乘省錢的行動平台",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup static file serving for uploaded files
uploads_dir = os.path.join(os.getcwd(), settings.UPLOAD_FOLDER)
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["認證"])
app.include_router(users.router, prefix="/users", tags=["使用者"])
app.include_router(campaigns.router, prefix="/campaigns", tags=["揪團活動"])
app.include_router(businesses.router, prefix="/businesses", tags=["商家"])
app.include_router(chat.router, prefix="/chat", tags=["聊天"])
app.include_router(ai.router, prefix="/ai", tags=["AI功能"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["檔案上傳"])

@app.on_event("startup")
async def startup_event():
    create_tables()

@app.get("/", tags=["健康檢查"])
async def root():
    return {"message": "歡迎使用 Juka 揪咖 API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 