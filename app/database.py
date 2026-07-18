import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Render PostgreSQL DATABASE_URL 환경 변수 읽기 (postgres:// -> postgresql:// 변환 포함)
DATABASE_URL = os.getenv("DATABASE_URL", "")

# 로컬 개발용 SQLite 폴백 (DATABASE_URL이 없거나 postgres 연결 실패 시)
USE_SQLITE = False
if not DATABASE_URL:
    USE_SQLITE = True
    DATABASE_URL = "sqlite:///./quotation.db"
    print("[INFO] Using SQLite for local development")
else:
    # Render PostgreSQL은 postgres:// 스키마를 postgresql://로 변환 (SQLAlchemy 1.4+ 호환성)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLAlchemy Engine 생성
# SQLite인 경우: check_same_thread=False 필요, pool 설정 불필요
# PostgreSQL인 경우: pool_pre_ping, pool_recycle 설정
if USE_SQLITE:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    # pool_pre_ping=True: 커넥션 풀에서 연결 유효성 검사 (Render PostgreSQL 유휴 연결 끊김 방지)
    # pool_recycle=300: 5분마다 연결 재사용 (Render free tier 유휴 타임아웃 대비)
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False  # 프로덕션에서는 False, 개발 시 True로 설정하여 SQL 로그 확인 가능
    )

# SessionLocal: DB 세션 생성을 위한 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base: ORM 모델의 베이스 클래스
Base = declarative_base()


# Dependency: FastAPI Depends에서 사용할 DB 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()