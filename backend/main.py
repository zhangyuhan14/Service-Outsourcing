from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.routers import detection

app = FastAPI(title="Detection Backend", version="1.0", description="Industrial Detection Backend Service")

# 初始化数据库
Base.metadata.create_all(bind=engine)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 路由
app.include_router(detection.router)

@app.get("/")
def root():
    return {"message": "Detection backend is running"}