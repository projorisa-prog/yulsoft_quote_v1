from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal
from datetime import datetime, date
from enum import Enum
import uuid
from decimal import Decimal

# ========== Enums ==========
class DayOfWeek(str, Enum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"

class PresetFrequency(str, Enum):
    WEEKLY_1 = "WEEKLY_1"  # 주 1회
    WEEKLY_2 = "WEEKLY_2"  # 주 2회
    WEEKLY_3 = "WEEKLY_3"  # 주 3회
    WEEKLY_5 = "WEEKLY_5"  # 주 5회 (월~금)
    DAILY = "DAILY"        # 매일

PRESET_DAYS_MAP = {
    PresetFrequency.WEEKLY_1: [DayOfWeek.MON],
    PresetFrequency.WEEKLY_2: [DayOfWeek.MON, DayOfWeek.THU],
    PresetFrequency.WEEKLY_3: [DayOfWeek.MON, DayOfWeek.WED, DayOfWeek.FRI],
    PresetFrequency.WEEKLY_5: [DayOfWeek.MON, DayOfWeek.TUE, DayOfWeek.WED, DayOfWeek.THU, DayOfWeek.FRI],
    PresetFrequency.DAILY: list(DayOfWeek),
}

class QuoteStatus(str, Enum):
    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"
    CONVERTED = "CONVERTED"
    EXPIRED = "EXPIRED"

class DesignKey(str, Enum):
    CLASSIC = "classic"
    MODERN = "modern"
    COLOR = "color"

class DiscountType(str, Enum):
    NONE = "NONE"
    PERCENT = "PERCENT"
    AMOUNT = "AMOUNT"

class UserPlan(str, Enum):
    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"

class BuildingType(str, Enum):
    APT = "APT"
    OFFICETEL = "OFFICETEL"
    OFFICE = "OFFICE"
    STORE = "STORE"
    FACTORY = "FACTORY"
    ETC = "ETC"


# ========== Input Schemas (Request) ==========

class CustomerInfo(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., pattern=r"^01[0-9]-?\d{4}-?\d{4}$")
    email: Optional[EmailStr] = None
    address: str = Field(..., min_length=1, max_length=200)
    detail_address: Optional[str] = Field(None, max_length=200)
    building_type: BuildingType
    area_pyeong: Optional[float] = Field(None, ge=0)  # 평수 (면적 단가 계산용 옵션)

class SupplierInfo(BaseModel):
    biz_reg_no: str = Field(..., pattern=r"^\d{10}$")  # 하이픈 제외 10자리
    company_name: str = Field(..., min_length=1, max_length=200)
    ceo_name: str = Field(..., min_length=1, max_length=100)
    address: str = Field(..., min_length=1, max_length=200)
    business_type: str = Field(..., min_length=1, max_length=100)
    business_item: str = Field(..., min_length=1, max_length=200)
    phone: str = Field(..., pattern=r"^01[0-9]-?\d{4}-?\d{4}$|^0[2-9]\d{1}-?\d{3,4}-?\d{4}$")
    email: EmailStr

class QuoteItemInput(BaseModel):
    area: str = Field(..., min_length=1, max_length=100)
    task: str = Field(..., min_length=1, max_length=200)
    days: List[DayOfWeek] = Field(..., min_items=1)
    qty: int = Field(default=1, ge=1)
    unit_price: int = Field(default=0, ge=0)
    exclude_area: Optional[str] = Field(None, max_length=200)
    memo: Optional[str] = None

class CalculationInput(BaseModel):
    items: List[QuoteItemInput] = Field(..., min_items=1)
    discount_type: DiscountType = DiscountType.NONE
    discount_value: int = Field(default=0, ge=0)
    vat_included: bool = False  # 단가 VAT 포함 여부
    vat_rate: float = Field(default=0.1, ge=0, le=1)

class QuoteCreateRequest(BaseModel):
    customer: CustomerInfo
    supplier: Optional[SupplierInfo] = None  # 비회원은 입력받음, 회원은 DB에서 조회
    calculation: CalculationInput
    design_key: DesignKey = DesignKey.CLASSIC
    expires_days: int = Field(default=30, ge=1, le=365)
    preset_frequency: Optional[PresetFrequency] = None  # UI 프리셋 버튼용 (서버에서 days로 변환)

class QuoteUpdateRequest(BaseModel):
    customer: Optional[CustomerInfo] = None
    supplier: Optional[SupplierInfo] = None
    calculation: Optional[CalculationInput] = None
    design_key: Optional[DesignKey] = None
    expires_days: Optional[int] = Field(None, ge=1, le=365)
    status: Optional[QuoteStatus] = None  # 상태 변경용 (DRAFT <-> COMPLETED 등)


# ========== Output Schemas (Response) ==========

class QuoteItemOutput(QuoteItemInput):
    id: uuid.UUID
    sort_order: int
    total_price: int

    class Config:
        from_attributes = True

class Totals(BaseModel):
    subtotal: int
    discount_amount: int
    taxable_amount: int
    vat_amount: int
    grand_total: int

class QuoteSummary(BaseModel):
    id: uuid.UUID
    quote_number: Optional[str]
    status: QuoteStatus
    customer_name: str
    customer_phone: str
    grand_total: int
    design_key: DesignKey
    expires_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QuoteDetail(QuoteSummary):
    customer_info: CustomerInfo
    supplier_info: SupplierInfo
    calculation: CalculationInput
    items: List[QuoteItemOutput]
    totals: Totals
    watermark_text: Optional[str]

    class Config:
        from_attributes = True

class QuoteCreateResponse(BaseModel):
    id: uuid.UUID
    quote_number: Optional[str]
    status: QuoteStatus
    pdf_url: Optional[str] = None  # PDF 다운로드 URL (Presigned URL 등)
    expires_at: datetime

class QuotePreviewResponse(BaseModel):
    totals: Totals
    items: List[QuoteItemOutput]


# ========== Auth Schemas ==========
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    company_name: Optional[str] = None
    ceo_name: Optional[str] = None
    biz_reg_no: Optional[str] = Field(None, pattern=r"^\d{10}$")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[uuid.UUID] = None


# ========== Template Schemas ==========
class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    items: List[QuoteItemInput] = Field(..., min_items=1)

class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    items: Optional[List[QuoteItemInput]] = None

class TemplateOutput(BaseModel):
    id: uuid.UUID
    name: str
    items: List[QuoteItemInput]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== Company Info Schemas ==========
class CompanyInfoUpdate(BaseModel):
    company_name: Optional[str] = None
    ceo_name: Optional[str] = None
    biz_reg_no: Optional[str] = Field(None, pattern=r"^\d{10}$")
    company_address: Optional[dict] = None  # {postal_code, address, detail_address}
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    business_type: Optional[str] = None
    business_item: Optional[str] = None

class CompanyInfoOutput(BaseModel):
    company_name: Optional[str]
    ceo_name: Optional[str]
    biz_reg_no: Optional[str]
    company_address: Optional[dict]
    phone: Optional[str]
    email: Optional[EmailStr]
    business_type: Optional[str]
    business_item: Optional[str]

    class Config:
        from_attributes = True