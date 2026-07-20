from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session
import os
import json
from pathlib import Path

from app.models.quote import Quote

def number_to_korean(num: int) -> str:
    """숫자를 한글 금액 표기로 변환"""
    if num == 0:
        return "영"
    
    units = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]
    places = ["", "십", "백", "천"]
    groups = ["", "만", "억", "조"]
    
    def convert_group(group: int) -> str:
        if group == 0:
            return ""
        result = ""
        for i, place in enumerate(places):
            digit = (group // (10 ** i)) % 10
            if digit:
                if digit == 1 and i > 0:
                    result = place + result
                else:
                    result = units[digit] + place + result
        return result
    
    result_parts = []
    group_idx = 0
    while num > 0:
        group = num % 10000
        if group:
            part = convert_group(group)
            if groups[group_idx]:
                part += groups[group_idx]
            result_parts.append(part)
        num //= 10000
        group_idx += 1
    
    return "".join(reversed(result_parts))

def get_template_env() -> Environment:
    """Jinja2 템플릿 환경 설정"""
    template_dir = Path(__file__).parent.parent / "templates" / "quote"
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(['html', 'xml'])
    )
    env.filters['format_korean'] = number_to_korean
    return env

def render_quote_html(quote: Quote, db: Session) -> str:
    """견적서 HTML 렌더링"""
    env = get_template_env()
    template = env.get_template("base.html")
    
    # JSON 필드들 파싱 (문자열인 경우)
    def parse_json(val):
        if isinstance(val, str):
            return json.loads(val)
        return val
    
    customer = parse_json(quote.customer_info)
    supplier = parse_json(quote.supplier_info)
    items = quote.items  # relationship이므로 이미 객체 리스트
    totals = parse_json(quote.totals)
    
    # 템플릿에 전달할 컨텍스트 구성
    context = {
        "quote": quote,
        "customer": customer,
        "supplier": supplier,
        "items": items,
        "totals": totals,
        "design_key": quote.design_key,
        "watermark_text": quote.watermark_text or "",
        "quote_number": quote.quote_number or str(quote.id),
        "created_at": quote.created_at,
        "expires_at": quote.expires_at,
        "status": quote.status.value,
    }
    
    return template.render(**context)

def generate_quote_pdf(quote: Quote, db: Session) -> bytes:
    """
    WeasyPrint를 사용하여 HTML을 PDF로 변환
    CSS Paged Media 표준 지원으로 페이지 매김, 헤더/푸터, 워터마크 처리 가능
    """
    html_content = render_quote_html(quote, db)
    
    # 기본 CSS 경로
    base_css_path = Path(__file__).parent.parent / "templates" / "quote" / "css" / "quote-base.css"
    design_css_path = Path(__file__).parent.parent / "templates" / "quote" / "css" / f"design-{quote.design_key}.css"
    
    # CSS 리스트 구성
    stylesheets = []
    
    if base_css_path.exists():
        stylesheets.append(CSS(filename=str(base_css_path)))
    
    if design_css_path.exists():
        stylesheets.append(CSS(filename=str(design_css_path)))
    
    # 워터마크 CSS 동적 주입 (@page @bottom-center)
    if quote.watermark_text:
        watermark_css = CSS(string=f"""
            @page {{
                @bottom-center {{
                    content: "{quote.watermark_text}";
                    font-size: 8pt;
                    color: #999;
                    font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
                    width: 100%;
                    text-align: center;
                }}
            }}
        """)
        stylesheets.append(watermark_css)
    
    # PDF 생성 - base_url은 템플릿 디렉토리로 설정
    html_doc = HTML(string=html_content, base_url=str(Path(__file__).parent.parent / "templates"))
    pdf_bytes = html_doc.write_pdf(stylesheets=stylesheets)
    return pdf_bytes

def generate_quote_pdf_to_file(quote: Quote, db: Session, output_path: str) -> str:
    """PDF를 파일로 저장하고 경로 반환"""
    pdf_bytes = generate_quote_pdf(quote, db)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    
    return output_path
