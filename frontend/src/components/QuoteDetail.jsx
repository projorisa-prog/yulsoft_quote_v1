import { useState, useEffect } from 'react';
import { getQuote, downloadQuotePdf } from '../services/api';

const formatNumber = (num) => num?.toLocaleString() || '0';

const DAY_LABELS = {
  MON: '월', TUE: '화', WED: '수', THU: '목',
  FRI: '금', SAT: '토', SUN: '일'
};

const DESIGN_LABELS = {
  classic: '클래식',
  modern: '모던',
  color: '컬러'
};

export default function QuoteDetail({ quoteId, onBack }) {
  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [pdfLoading, setPdfLoading] = useState(false);

  useEffect(() => {
    if (quoteId) {
      loadQuote();
    }
  }, [quoteId]);

  const loadQuote = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getQuote(quoteId);
      setQuote(data);
    } catch (err) {
      setError(err.response?.data?.detail || '견적서 조회 실패');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = async () => {
    setPdfLoading(true);
    try {
      const blob = await downloadQuotePdf(quoteId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `견적서_${quote?.quote_number || quoteId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      alert('PDF 다운로드 실패: ' + (err.response?.data?.detail || err.message));
    } finally {
      setPdfLoading(false);
    }
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    alert('링크가 복사되었습니다.');
  };

  const formatDays = (days) => {
    if (!days || !days.length) return '';
    return days.map(d => DAY_LABELS[d] || d).join(', ');
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric', month: 'long', day: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  const getStatusBadge = (status) => {
    const styles = {
      DRAFT: 'status-draft',
      COMPLETED: 'status-completed',
      CONVERTED: 'status-converted',
      EXPIRED: 'status-expired'
    };
    const labels = {
      DRAFT: '임시저장',
      COMPLETED: '완료',
      CONVERTED: '계약전환',
      EXPIRED: '만료'
    };
    return <span className={`status-badge ${styles[status] || ''}`}>{labels[status] || status}</span>;
  };

  if (loading) {
    return <div className="quote-detail loading">로딩 중...</div>;
  }

  if (error || !quote) {
    return (
      <div className="quote-detail error">
        <h2>견적서를 찾을 수 없습니다</h2>
        <p>{error || '존재하지 않는 견적서입니다.'}</p>
        <button onClick={onBack} className="btn secondary">뒤로 가기</button>
      </div>
    );
  }

  const customer = quote.customer_info || {};
  const supplier = quote.supplier_info || {};
  const items = quote.items || [];
  const totals = quote.totals || {};

  return (
    <div className="quote-detail">
      <div className="quote-header">
        <div className="header-left">
          <h1 className="quote-title">견적서</h1>
          {getStatusBadge(quote.status)}
        </div>
        <div className="header-meta">
          <div className="quote-number">
            <span className="label">견적번호</span>
            <span className="value">{quote.quote_number}</span>
          </div>
          <div className="quote-date">
            <span className="label">작성일</span>
            <span className="value">{formatDate(quote.created_at)}</span>
          </div>
          <div className="quote-expires">
            <span className="label">유효기간</span>
            <span className="value">{formatDate(quote.expires_at)}</span>
          </div>
        </div>
      </div>

      <div className="quote-body">
        <div className="info-grid">
          <div className="info-block customer">
            <h3>고객 정보</h3>
            <div className="info-item">
              <span className="label">이름</span>
              <span className="value">{customer.name}</span>
            </div>
            <div className="info-item">
              <span className="label">전화</span>
              <span className="value">{customer.phone}</span>
            </div>
            {customer.email && (
              <div className="info-item">
                <span className="label">이메일</span>
                <span className="value">{customer.email}</span>
              </div>
            )}
            <div className="info-item">
              <span className="label">주소</span>
              <span className="value">{customer.address} {customer.detail_address || ''}</span>
            </div>
            <div className="info-item">
              <span className="label">건물유형</span>
              <span className="value">{customer.building_type}</span>
            </div>
            {customer.area_pyeong && (
              <div className="info-item">
                <span className="label">평수</span>
                <span className="value">{customer.area_pyeong}평</span>
              </div>
            )}
          </div>

          <div className="info-block supplier">
            <h3>공급자 정보</h3>
            <div className="info-item">
              <span className="label">상호</span>
              <span className="value">{supplier.company_name}</span>
            </div>
            <div className="info-item">
              <span className="label">대표자</span>
              <span className="value">{supplier.ceo_name}</span>
            </div>
            <div className="info-item">
              <span className="label">사업자번호</span>
              <span className="value">{supplier.biz_reg_no}</span>
            </div>
            <div className="info-item">
              <span className="label">주소</span>
              <span className="value">{supplier.address}</span>
            </div>
            <div className="info-item">
              <span className="label">업태</span>
              <span className="value">{supplier.business_type}</span>
            </div>
            <div className="info-item">
              <span className="label">종목</span>
              <span className="value">{supplier.business_item}</span>
            </div>
            <div className="info-item">
              <span className="label">연락처</span>
              <span className="value">{supplier.phone}</span>
            </div>
            <div className="info-item">
              <span className="label">이메일</span>
              <span className="value">{supplier.email}</span>
            </div>
          </div>
        </div>

        <div className="items-section">
          <h3>작업 내역</h3>
          <table className="items-table">
            <thead>
              <tr>
                <th>No.</th>
                <th>구역</th>
                <th>작업 내용</th>
                <th>요일</th>
                <th>수량</th>
                <th>단가</th>
                <th>금액</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, idx) => (
                <tr key={item.id || idx}>
                  <td>{idx + 1}</td>
                  <td>{item.area}</td>
                  <td>{item.task}</td>
                  <td>{formatDays(item.days)}</td>
                  <td className="text-right">{formatNumber(item.qty)}</td>
                  <td className="text-right">{formatNumber(item.unit_price)}</td>
                  <td className="text-right total">{formatNumber(item.total_price)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="summary-section">
          <table className="summary-table">
            <tr>
              <th>공급가액</th>
              <td className="text-right">{formatNumber(totals.subtotal)} 원</td>
            </tr>
            {totals.discount_amount > 0 && (
              <tr className="discount-row">
                <th>할인금액</th>
                <td className="text-right">- {formatNumber(totals.discount_amount)} 원</td>
              </tr>
            )}
            <tr>
              <th>과세표준</th>
              <td className="text-right">{formatNumber(totals.taxable_amount)} 원</td>
            </tr>
            <tr>
              <th>부가가치세 (10%)</th>
              <td className="text-right">{formatNumber(totals.vat_amount)} 원</td>
            </tr>
            <tr className="grand-total">
              <th>합계 금액</th>
              <td className="text-right">{formatNumber(totals.grand_total)} 원</td>
            </tr>
          </table>
          <div className="amount-in-words">
            <strong>금액 합계: </strong>
            {totals.grand_total ? (() => {
              const units = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구'];
              const places = ['', '십', '백', '천'];
              const groups = ['', '만', '억', '조'];
              
              function convertGroup(group) {
                if (group === 0) return '';
                let result = '';
                for (let i = 0; i < places.length; i++) {
                  const digit = Math.floor(group / Math.pow(10, i)) % 10;
                  if (digit) {
                    if (digit === 1 && i > 0) {
                      result = places[i] + result;
                    } else {
                      result = units[digit] + places[i] + result;
                    }
                  }
                }
                return result;
              }
              
              let num = totals.grand_total;
              let resultParts = [];
              let groupIdx = 0;
              while (num > 0) {
                const group = num % 10000;
                if (group) {
                  let part = convertGroup(group);
                  if (groups[groupIdx]) part += groups[groupIdx];
                  resultParts.push(part);
                }
                num = Math.floor(num / 10000);
                groupIdx++;
              }
              return resultParts.reverse().join('') + '원정';
            })() : '영원정'}
          </div>
        </div>

        <div className="footer-section">
          <div className="footer-grid">
            <div className="sign-block customer-sign">
              <span className="sign-label">공급자</span>
              <div className="sign-line">
                <span className="sign-name">{supplier.company_name} (인)</span>
              </div>
              <div className="sign-details">
                <div className="sign-detail-row">
                  <span className="sign-detail-label">대표자</span>
                  <span className="sign-detail-value">{supplier.ceo_name}</span>
                </div>
                <div className="sign-detail-row">
                  <span className="sign-detail-label">사업자등록번호</span>
                  <span className="sign-detail-value">{supplier.biz_reg_no}</span>
                </div>
                <div className="sign-detail-row">
                  <span className="sign-detail-label">주소</span>
                  <span className="sign-detail-value">{supplier.address}</span>
                </div>
                <div className="sign-detail-row">
                  <span className="sign-detail-label">연락처</span>
                  <span className="sign-detail-value">{supplier.phone}</span>
                </div>
              </div>
            </div>
            <div className="sign-block customer-info-sign">
              <span className="sign-label">고객</span>
              <div className="sign-line">
                <span className="sign-name">{customer.name} (인)</span>
              </div>
              <div className="sign-details">
                <div className="sign-detail-row">
                  <span className="sign-detail-label">연락처</span>
                  <span className="sign-detail-value">{customer.phone}</span>
                </div>
                <div className="sign-detail-row">
                  <span className="sign-detail-label">주소</span>
                  <span className="sign-detail-value">{customer.address} {customer.detail_address || ''}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {quote.watermark_text && (
          <div className="watermark-notice">
            {quote.watermark_text}
          </div>
        )}
      </div>

      <div className="action-bar">
        <button onClick={handleDownloadPdf} disabled={pdfLoading} className="btn primary">
          {pdfLoading ? '다운로드 중...' : 'PDF 다운로드'}
        </button>
        <button onClick={handleCopyLink} className="btn secondary">
          링크 복사
        </button>
        <button onClick={onBack} className="btn secondary">
          목록으로
        </button>
      </div>
    </div>
  );
}