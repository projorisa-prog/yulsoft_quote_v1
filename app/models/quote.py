import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column, String, Enum, DateTime, ForeignKey, Integer, JSON, Text, UniqueConstraint
)
# from sqlalchemy.dialects.postgresql import UUID, JSONB  # SQLite 호환을 위해 제거
from sqlalchemy.orm import relationship, declarative_base

from app.database import Base

class QuoteStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"
    CONVERTED = "CONVERTED"
    EXPIRED = "EXPIRED"

class UserPlan(str, enum.Enum):
    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"

class BuildingType(str, enum.Enum):
    APT = "APT"
    OFFICETEL = "OFFICETEL"
    OFFICE = "OFFICE"
    STORE = "STORE"
    FACTORY = "FACTORY"
    ETC = "ETC"

class DayOfWeek(str, enum.Enum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"

# SQLite 호환을 위해 UUID는 String(36)으로, JSONB는 JSON으로 변경
class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=True)
    ceo_name = Column(String(100), nullable=True)
    biz_reg_no = Column(String(10), unique=True, index=True, nullable=True)  # 하이픈 제외 10자리
    company_address = Column(JSON, nullable=True)  # {postal_code, address, detail_address}
    phone = Column(String(20), nullable=True)
    plan = Column(Enum(UserPlan), default=UserPlan.FREE, nullable=False)
    quote_seq = Column(Integer, default=0, nullable=False)  # 견적번호 시퀀스 (회원별)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    quotes = relationship("Quote", back_populates="owner", cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="owner", cascade="all, delete-orphan")

class Quote(Base):
    __tablename__ = "quotes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # Public ID (URL용)
    quote_number = Column(String(50), unique=True, index=True, nullable=True)  # 회원: YYMM-SEQ, 비회원: TEMP-UUID
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)  # 비회원시 NULL
    status = Column(Enum(QuoteStatus), default=QuoteStatus.DRAFT, nullable=False, index=True)
    
    # JSON 스냅샷 필드들 (SQLite/PostgreSQL 호환)
    customer_info = Column(JSON, nullable=False)  # CustomerInfo 스키마
    supplier_info = Column(JSON, nullable=False)  # SupplierInfo 스키마 (스냅샷)
    calculation_snapshot = Column(JSON, nullable=False)  # CalculationInput 스키마 (재계산용)
    totals = Column(JSON, nullable=False)  # Totals 스키마
    
    watermark_text = Column(String(255), nullable=True)  # 비회원: "Powered by 율소프트"
    design_key = Column(String(20), default="classic", nullable=False)  # classic, modern, color
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="quotes")
    items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan", order_by="QuoteItem.sort_order")
    designs = relationship("QuoteDesign", back_populates="quote", cascade="all, delete-orphan")

class QuoteItem(Base):
    __tablename__ = "quote_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_id = Column(String(36), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)
    
    area = Column(String(100), nullable=False)       # 청소구역 (예: 거실, 화장실)
    task = Column(String(200), nullable=False)       # 청소내용 (예: 바닥 청소, 유리 닦기)
    days = Column(JSON, nullable=False)             # 요일 배열 ["MON", "WED", "FRI"]
    qty = Column(Integer, default=1, nullable=False) # 수량/횟수
    unit_price = Column(Integer, default=0, nullable=False) # 단가 (원)
    total_price = Column(Integer, default=0, nullable=False) # 금액 (qty * unit_price)
    exclude_area = Column(String(200), nullable=True) # 제외구역
    memo = Column(Text, nullable=True)               # 비고

    quote = relationship("Quote", back_populates="items")

class QuoteDesign(Base):
    """디자인 스냅샷 (MVP에서는 design_key로 대체 가능하나, 향후 커스텀 CSS 저장용)"""
    __tablename__ = "quote_designs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_id = Column(String(36), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False)
    design_key = Column(String(20), nullable=False)
    custom_css = Column(Text, nullable=True)  # 향후 커스텀 CSS 저장용
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    quote = relationship("Quote", back_populates="designs")

class Template(Base):
    """자주 쓰는 항목 템플릿 (유료 기능 PRO 이상)"""
    __tablename__ = "templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)  # 예: "표준 주 2회 오피스 청소"
    items = Column(JSON, nullable=False)  # QuoteItem 배열 템플릿
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="templates")