from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple

from app.schemas.quote import (
    CalculationInput, QuoteItemInput, QuoteItemOutput, Totals, DiscountType
)

def calculate_quote(data: CalculationInput) -> Tuple[List[QuoteItemOutput], Totals]:
    """
    견적 산출 로직 (결정론적, 정수 연산만 사용)
    
    Args:
        data: 산출 입력값 (항목 리스트, 할인 타입/값, 부가세 설정)
    
    Returns:
        tuple: (계산된 항목 리스트, 합계 정보)
    """
    items = data.items
    subtotal = 0
    output_items = []
    
    # 1. 품목별 금액 계산 (정수 연산)
    for idx, item in enumerate(items):
        total_price = item.qty * item.unit_price
        subtotal += total_price
        
        output_items.append(QuoteItemOutput(
            area=item.area,
            task=item.task,
            days=item.days,
            qty=item.qty,
            unit_price=item.unit_price,
            total_price=total_price,
            exclude_area=item.exclude_area,
            memo=item.memo,
            id=__import__('uuid').uuid4(),  # 임시 ID
            sort_order=idx
        ))

    # 2. 할인 계산
    discount_amount = 0
    if data.discount_type == DiscountType.PERCENT:
        # 할인율 적용: 소계 * 할인율 / 100 (정수 나눗셈)
        discount_amount = int(subtotal * data.discount_value / 100)
    elif data.discount_type == DiscountType.AMOUNT:
        # 정액 할인: 소계를 초과하지 않도록 최소값 적용
        discount_amount = min(data.discount_value, subtotal)
    
    taxable_amount = subtotal - discount_amount

    # 3. 부가세 계산 (국세청 기준: 공급가액 * 0.1 -> 원단위 반올림)
    # Decimal을 사용하여 부동소수점 오차 방지, ROUND_HALF_UP(0.5 올림) 적용
    vat_rate = Decimal(str(data.vat_rate))
    taxable_decimal = Decimal(str(taxable_amount))
    vat_amount = int(
        (taxable_decimal * vat_rate).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    )
    
    grand_total = taxable_amount + vat_amount

    totals = Totals(
        subtotal=subtotal,
        discount_amount=discount_amount,
        taxable_amount=taxable_amount,
        vat_amount=vat_amount,
        grand_total=grand_total
    )
    
    return output_items, totals


def recalc_quote_from_snapshot(calculation_snapshot: dict) -> Tuple[List[QuoteItemOutput], Totals]:
    """
    저장된 calculation_snapshot(JSON)을 받아 재계산 수행
    (견적 수정 시, 단가/수량 변경 후 재계산용)
    """
    data = CalculationInput(**calculation_snapshot)
    return calculate_quote(data)


def apply_preset_frequency(items: List[QuoteItemInput], preset) -> List[QuoteItemInput]:
    """
    프리셋 빈도(WEEKLY_1, WEEKLY_2 등)를 항목들의 days 필드에 적용
    프론트엔드에서 프리셋 버튼 클릭 시 서버/클라이언트 양쪽에서 사용 가능
    """
    from app.schemas.enums import PresetFrequency, DayOfWeek, PRESET_MAP
    
    if isinstance(preset, str):
        preset = PresetFrequency(preset)
    
    days = PRESET_MAP.get(preset, [])
    
    for item in items:
        item.days = days.copy()  # 리스트 복사하여 할당
    
    return items