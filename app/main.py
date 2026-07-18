from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.routers import public_quotes

# Lifespan 이벤트 핸들러 (FastAPI 0.9.0+ 권장 방식)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: 데이터베이스 테이블 생성
    # 주의: 프로덕션에서는 Alembic 마이그레이션을 사용하는 것이 권장됩니다.
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: 필요시 정리 로직 추가 (예: connection pool 닫기)

app = FastAPI(title="Yulsoft Quotation System MVP", lifespan=lifespan)

# 라우터 등록 (router에 이미 prefix가 있으므로 prefix 제거)
app.include_router(public_quotes.router)

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Yulsoft API Server is running."}

@app.get("/api/v1/health")
def health_check():
    return {"status": "UP"}