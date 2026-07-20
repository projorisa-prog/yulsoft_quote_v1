from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI(title="Yulsoft Quotation System MVP")

# 정적 파일 서빙 (프론트엔드 빌드 결과)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/api/v1/health")
def health_check():
    return {"status": "UP"}

# API 라우터 등록
from app.routers import public_quotes
app.include_router(public_quotes.router)

# SPA 라우팅을 위한 catch-all (GET 요청만 처리, API 경로 제외)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # API 경로는 제외
    if full_path.startswith("api/") or full_path.startswith("static/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
    index_path = "app/static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "healthy", "message": "Yulsoft API Server is running."}