from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session
import os
from pathlib import Path

from app.models.quote import Quote

def get_template_env() -> Environment:
    """Jinja2 템플릿 환경 설정"""
    template_dir = Path(__file__).parent.parent / "templates" / "quote"
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(['html', 'xml'])
    )
    return env


def render_quote_html(quote: Quote, db: Session) -> str:
    """견적서 HTML 렌더링"""
    env = get_template_env()
    template = env.get_template("base.html")
    
    # 템플릿에 전달할 컨텍스트 구성
    context = {
        "quote": quote,
        "customer": quote.customer_info,
        "supplier": quote.supplier_info,
        "items": quote.items,
        "totals": quote.totals,
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
    
    # PDF 생성
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


def generate_quote_png(quote: Quote, db: Session) -> bytes:
    """
    이미지(PNG) 생성 - 카카오톡 공유용 썸네일 등
    Playwright 또는 headless chrome 필요 (MVP에서는 WeasyPrint로 PDF 생성 후 변환하거나 생략)
    """
    # TODO: Playwright 도입 시 구현
    # from playwright.async_api import async_playwright
    # html = render_quote_html(quote, db)
    # async with async_playwright() as p:
    #     browser = await p.chromium.launch()
    #     page = await browser.new_page()
    #     await page.set_content(html)
    #     png = await page.screenshot(full_page=True)
    #     return png
    raise NotImplementedError("PNG generation requires Playwright. Implement later.")