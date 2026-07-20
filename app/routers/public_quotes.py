from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import json
from datetime import datetime, timedelta

from app.database import get_db
from app.models.quote import Quote, QuoteItem, QuoteStatus, User, UserPlan
from app.schemas.quote import (
    QuoteCreateRequest, QuotePreviewResponse, QuoteCreateResponse,
    QuoteDetail, QuoteItemOutput, Totals, QuoteStatus as QuoteStatusEnum,
    CustomerInfo, SupplierInfo, CalculationInput
)
from app.services.calculation import calculate_quote, recalc_quote_from_snapshot
from app.services.pdf_generator import generate_quote_pdf

router = APIRouter(prefix="/api/v1/quotes", tags=["Public Quotes"])


# ---------- Helper Functions ----------

def generate_quote_number(db: Session, user_id: str) -> str:
    """견적번호 생성: YYMM-SEQ (회원별 시퀀스)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.quote_seq += 1
    db.commit()
    
    now = datetime.now()
    return f"{now.strftime('%y%m')}-{user.quote_seq:04d}"


def generate_temp_quote_number() -> str:
    """비회원 견적번호: TEMP-UUID 앞 8자리"""
    return f"TEMP-{str(uuid.uuid4())[:8].upper()}"


def apply_watermark(user: Optional[User]) -> str:
    """워터마크 텍스트 결정: 비회원/무료플랜은 워터마크 표시"""
    if not user or user.plan == UserPlan.FREE:
        return "Powered by 율소프트 | www.yulsoft.kr"
    return ""


# ---------- Public API Endpoints ----------

@router.post(
    "/preview",
    response_model=QuotePreviewResponse,
    summary="견적 산출 미리보기 (DB 저장 안 함)",
    description="입력값으로만 산출 로직을 실행하여 합계와 항목별 금액을 반환합니다. 비회원/회원 모두 이용 가능.",
    status_code=status.HTTP_200_OK
)
def preview_quote(request: QuoteCreateRequest):
    """견적 미리보기 - 계산 로직만 실행, DB 저장 안 함"""
    try:
        # 프리셋 빈도 적용 (서버 사이드에서 days 변환)
        if request.preset_frequency:
            from app.services.calculation import apply_preset_frequency
            request.calculation.items = apply_preset_frequency(
                request.calculation.items, request.preset_frequency
            )
        
        items, totals = calculate_quote(request.calculation)
        
        # 응답용 아이템 변환 (calculate_quote에서 이미 QuoteItemOutput 반환)
        output_items = [
            QuoteItemOutput(
                area=item.area,
                task=item.task,
                days=item.days,
                qty=item.qty,
                unit_price=item.unit_price,
                total_price=item.total_price,
                exclude_area=item.exclude_area,
                memo=item.memo,
                id=item.id,
                sort_order=item.sort_order
            ) for item in items
        ]
        
        return QuotePreviewResponse(totals=totals, items=output_items)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calculation error: {str(e)}")


@router.post(
    "",
    response_model=QuoteCreateResponse,
    summary="견적서 생성 및 저장 (PDF 생성 트리거)",
    description="견적서를 DB에 저장하고 Public ID를 반환합니다. 비회원은 TEMP-번호, 회원은 YYMM-SEQ 번호가 부여됩니다.",
    status_code=status.HTTP_201_CREATED
)
def create_quote(request: QuoteCreateRequest, db: Session = Depends(get_db)):
    """견적서 생성 및 저장"""
    try:
        # 1. 프리셋 빈도 적용
        if request.preset_frequency:
            from app.services.calculation import apply_preset_frequency
            request.calculation.items = apply_preset_frequency(
                request.calculation.items, request.preset_frequency
            )
        
        # 2. 산출 로직 실행
        items, totals = calculate_quote(request.calculation)
        
        # 3. 공급자 정보 결정 (회원이면 DB에서, 비회원이면 요청값 사용)
        supplier_info = request.supplier
        user = None
        quote_number = None
        
        # TODO: 실제 인증 연동 시 현재 사용자 조회 로직으로 변경
        # 현재는 비회원 기준으로 구현
        
        if not supplier_info:
            # 비회원이면서 공급자 미입력 시 기본값 (나중에 설정에서 가져오도록 수정)
            supplier_info = SupplierInfo(
                biz_reg_no="1234567890",
                company_name="율소프트",
                ceo_name="대표자명",
                address="서울시 강남구",
                business_type="소프트웨어 개발",
                business_item="프로그램 개발 및 공급",
                phone="010-0000-0000",
                email="admin@yulsoft.kr"
            )
        
        # 4. 유효기간 계산
        expires_at = datetime.utcnow() + timedelta(days=request.expires_days)
        
        # 5. 워터마크 텍스트
        watermark = apply_watermark(user)
        
        # 6. Quote 엔티티 생성 (UUID를 문자열로 변환)
        quote_id = str(uuid.uuid4())
        quote = Quote(
            id=quote_id,
            quote_number=quote_number or generate_temp_quote_number(),
            user_id=user.id if user else None,
            status=QuoteStatus.COMPLETED,  # 생성 즉시 COMPLETED (PDF 생성 완료 시점)
            # JSON 필드들을 ensure_ascii=False로 저장하여 한글 보존
            customer_info=json.dumps(request.customer.model_dump(), ensure_ascii=False),
            supplier_info=json.dumps(supplier_info.model_dump(), ensure_ascii=False),
            calculation_snapshot=json.dumps(request.calculation.model_dump(), ensure_ascii=False),
            totals=json.dumps(totals.model_dump(), ensure_ascii=False),
            watermark_text=watermark,
            design_key=request.design_key.value,
            expires_at=expires_at
        )
        
        db.add(quote)
        db.flush()  # ID 생성을 위해 flush
        
        # 7. QuoteItem 엔티티들 생성
        for idx, item in enumerate(items):
            quote_item = QuoteItem(
                id=str(uuid.uuid4()),
                quote_id=quote_id,
                sort_order=idx,
                area=item.area,
                task=item.task,
                days=json.dumps(item.days, ensure_ascii=False),
                qty=item.qty,
                unit_price=item.unit_price,
                total_price=item.total_price,
                exclude_area=item.exclude_area,
                memo=item.memo
            )
            db.add(quote_item)
        
        db.commit()
        db.refresh(quote)
        
        # 8. PDF 생성 (비동기로 처리하는 것이 좋으나 MVP에서는 동기 처리)
        pdf_url = None
        try:
            pdf_bytes = generate_quote_pdf(quote, db)
            # TODO: S3/R2 업로드 후 Presigned URL 반환
            # 현재는 로컬 파일로 저장하거나 바이트 반환
            pdf_url = f"/api/v1/quotes/{quote_id}/pdf"
        except Exception as pdf_error:
            # PDF 생성 실패해도 견적서는 저장됨
            print(f"PDF generation failed: {pdf_error}")
        
        return QuoteCreateResponse(
            id=quote_id,
            quote_number=quote.quote_number,
            status=quote.status,
            pdf_url=pdf_url,
            expires_at=quote.expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create quote: {str(e)}")


@router.get(
    "/{public_id}",
    response_model=QuoteDetail,
    summary="견적서 조회 (웹 뷰/공유용)",
    description="Public ID로 견적서를 조회합니다. 만료된 견적은 EXPIRED 상태여도 조회 가능."
)
def get_quote(public_id: str, db: Session = Depends(get_db)):
    """견적서 상세 조회"""
    quote = db.query(Quote).filter(Quote.id == public_id).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # 만료 체크 (상태 업데이트는 배치에서 처리)
    if quote.expires_at < datetime.utcnow() and quote.status != QuoteStatus.EXPIRED:
        quote.status = QuoteStatus.EXPIRED
        db.commit()
    
    # 응답 구성 - JSON 필드 파싱
    items = [
        QuoteItemOutput(
            area=item.area,
            task=item.task,
            days=json.loads(item.days) if isinstance(item.days, str) else item.days,
            qty=item.qty,
            unit_price=item.unit_price,
            total_price=item.total_price,
            exclude_area=item.exclude_area,
            memo=item.memo,
            id=item.id,
            sort_order=item.sort_order
        ) for item in quote.items
    ]
    
    # QuoteSummary 필수 필드 추가
    customer_info = json.loads(quote.customer_info) if isinstance(quote.customer_info, str) else quote.customer_info
    supplier_info = json.loads(quote.supplier_info) if isinstance(quote.supplier_info, str) else quote.supplier_info
    calculation_snapshot = json.loads(quote.calculation_snapshot) if isinstance(quote.calculation_snapshot, str) else quote.calculation_snapshot
    totals_data = json.loads(quote.totals) if isinstance(quote.totals, str) else quote.totals
    
    customer_name = customer_info.get('name', '')
    customer_phone = customer_info.get('phone', '')
    grand_total = totals_data.get('grand_total', 0)
    
    return QuoteDetail(
        id=quote.id,
        quote_number=quote.quote_number,
        status=quote.status,
        customer_name=customer_name,
        customer_phone=customer_phone,
        grand_total=grand_total,
        customer_info=CustomerInfo(**customer_info),
        supplier_info=SupplierInfo(**supplier_info),
        calculation=CalculationInput(**calculation_snapshot),
        items=items,
        totals=Totals(**totals_data),
        watermark_text=quote.watermark_text,
        design_key=quote.design_key,
        expires_at=quote.expires_at,
        created_at=quote.created_at,
        updated_at=quote.updated_at
    )


@router.get(
    "/{public_id}/pdf",
    summary="PDF 다운로드",
    description="견적서 PDF를 다운로드합니다. 워터마크 적용 여부는 회원/비회원/플랜에 따라 자동 결정됩니다."
)
def download_quote_pdf(public_id: str, db: Session = Depends(get_db)):
    """PDF 다운로드"""
    quote = db.query(Quote).filter(Quote.id == public_id).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # 만료된 견적도 PDF 다운로드는 허용 (단, 워터마크는 유지)
    
    try:
        pdf_bytes = generate_quote_pdf(quote, db)
        
        filename = f"quote_{quote.quote_number or quote.id}.pdf"
        
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.post(
    "/{public_id}/share-link",
    summary="공유 링크 생성/갱신",
    description="Presigned URL 또는 Short Link를 생성합니다. (MVP에서는 Public ID 기반 URL 반환)"
)
def create_share_link(public_id: str, db: Session = Depends(get_db)):
    """공유 링크 생성"""
    quote = db.query(Quote).filter(Quote.id == public_id).first()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # MVP: 단순 Public URL 반환 (추후 S3 Presigned URL 또는 Short Link 서비스로 확장)
    share_url = f"/api/v1/quotes/{public_id}"
    pdf_url = f"/api/v1/quotes/{public_id}/pdf"
    
    return {
        "share_url": share_url,
        "pdf_url": pdf_url,
        "expires_at": quote.expires_at
    }
