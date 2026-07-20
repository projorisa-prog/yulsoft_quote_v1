import { useState } from 'react';
import { previewQuote, createQuote } from '../services/api';

const DAYS_OF_WEEK = [
  { value: 'MON', label: '월' },
  { value: 'TUE', label: '화' },
  { value: 'WED', label: '수' },
  { value: 'THU', label: '목' },
  { value: 'FRI', label: '금' },
  { value: 'SAT', label: '토' },
  { value: 'SUN', label: '일' },
];

const PRESET_FREQUENCIES = [
  { value: 'WEEKLY_1', label: '주 1회' },
  { value: 'WEEKLY_2', label: '주 2회' },
  { value: 'WEEKLY_3', label: '주 3회' },
  { value: 'WEEKLY_5', label: '주 5회 (월~금)' },
  { value: 'DAILY', label: '매일' },
];

const BUILDING_TYPES = [
  { value: 'APT', label: '아파트' },
  { value: 'OFFICETEL', label: '오피스텔' },
  { value: 'OFFICE', label: '사무실' },
  { value: 'STORE', label: '상가' },
  { value: 'FACTORY', label: '공장' },
  { value: 'ETC', label: '기타' },
];

const DESIGN_KEYS = [
  { value: 'classic', label: '클래식' },
  { value: 'modern', label: '모던' },
  { value: 'color', label: '컬러' },
];

const initialItem = {
  area: '',
  task: '',
  days: ['MON'],
  qty: 1,
  unit_price: 0,
  exclude_area: '',
  memo: '',
};

const initialCustomer = {
  name: '',
  phone: '',
  email: '',
  address: '',
  detail_address: '',
  building_type: 'APT',
  area_pyeong: 0,
};

const initialCalculation = {
  items: [initialItem],
  discount_type: 'NONE',
  discount_value: 0,
  vat_included: false,
  vat_rate: 0.1,
};

export default function QuoteForm({ onQuoteCreated }) {
  const [step, setStep] = useState(1); // 1: 입력, 2: 미리보기, 3: 완료
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [previewData, setPreviewData] = useState(null);
  
  const [customer, setCustomer] = useState(initialCustomer);
  const [calculation, setCalculation] = useState(initialCalculation);
  const [design_key, setDesignKey] = useState('classic');
  const [expires_days, setExpiresDays] = useState(30);
  const [preset_frequency, setPresetFrequency] = useState('');

  const updateCustomer = (field, value) => {
    setCustomer(prev => ({ ...prev, [field]: value }));
  };

  const addItem = () => {
    setCalculation(prev => ({ ...prev, items: [...prev.items, initialItem] }));
  };

  const removeItem = (index) => {
    if (calculation.items.length <= 1) return;
    setCalculation(prev => ({ ...prev, items: prev.items.filter((_, i) => i !== index) }));
  };

  const updateItem = (index, field, value) => {
    setCalculation(prev => {
      const newItems = [...prev.items];
      newItems[index] = { ...newItems[index], [field]: value };
      return { ...prev, items: newItems };
    });
  };

  const updateCalculation = (field, value) => {
    setCalculation(prev => ({ ...prev, [field]: value }));
  };

  const handlePreview = async () => {
    setLoading(true);
    setError('');
    try {
      const data = { customer, calculation, design_key, expires_days, preset_frequency: preset_frequency || undefined };
      const result = await previewQuote(data);
      setPreviewData(result);
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.detail || '미리보기 실패');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    setLoading(true);
    setError('');
    try {
      const data = { customer, calculation, design_key, expires_days, preset_frequency: preset_frequency || undefined };
      const result = await createQuote(data);
      setStep(3);
      onQuoteCreated?.(result);
    } catch (err) {
      setError(err.response?.data?.detail || '견적 생성 실패');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => setStep(1);

  const formatNumber = (num) => num.toLocaleString();

  if (step === 2) {
    return (
      <div className="quote-preview">
        <h2>견적 미리보기</h2>
        {error && <div className="error">{error}</div>}
        <table>
          <thead>
            <tr>
              <th>구역</th>
              <th>작업</th>
              <th>요일</th>
              <th>수량</th>
              <th>단가</th>
              <th>금액</th>
            </tr>
          </thead>
          <tbody>
            {previewData.items.map((item, idx) => (
              <tr key={item.id || idx}>
                <td>{item.area}</td>
                <td>{item.task}</td>
                <td>{item.days.join(', ')}</td>
                <td>{item.qty}</td>
                <td>{formatNumber(item.unit_price)}</td>
                <td>{formatNumber(item.total_price)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="totals">
          <div>소계: {formatNumber(previewData.totals.subtotal)}원</div>
          <div>할인: -{formatNumber(previewData.totals.discount_amount)}원</div>
          <div>과세표준: {formatNumber(previewData.totals.taxable_amount)}원</div>
          <div>VAT: {formatNumber(previewData.totals.vat_amount)}원</div>
          <div className="grand-total">합계: {formatNumber(previewData.totals.grand_total)}원</div>
        </div>
        <div className="actions">
          <button onClick={handleBack} disabled={loading}>수정</button>
          <button onClick={handleCreate} disabled={loading} className="primary">
            {loading ? '생성 중...' : '견적서 생성'}
          </button>
        </div>
      </div>
    );
  }

  if (step === 3) {
    return (
      <div className="quote-complete">
        <h2>견적서가 생성되었습니다!</h2>
        <button onClick={() => setStep(1)} className="primary">새 견적 작성</button>
      </div>
    );
  }

  return (
    <div className="quote-form">
      <h2>견적서 작성</h2>
      {error && <div className="error">{error}</div>}
      
      <fieldset>
        <legend>고객 정보</legend>
        <div className="field">
          <label>이름 *</label>
          <input value={customer.name} onChange={e => updateCustomer('name', e.target.value)} required />
        </div>
        <div className="field">
          <label>전화번호 *</label>
          <input type="tel" value={customer.phone} onChange={e => updateCustomer('phone', e.target.value)} placeholder="010-1234-5678" required />
        </div>
        <div className="field">
          <label>이메일</label>
          <input type="email" value={customer.email} onChange={e => updateCustomer('email', e.target.value)} />
        </div>
        <div className="field">
          <label>주소 *</label>
          <input value={customer.address} onChange={e => updateCustomer('address', e.target.value)} required />
        </div>
        <div className="field">
          <label>상세주소</label>
          <input value={customer.detail_address} onChange={e => updateCustomer('detail_address', e.target.value)} />
        </div>
        <div className="field">
          <label>건물 유형</label>
          <select value={customer.building_type} onChange={e => updateCustomer('building_type', e.target.value)}>
            {BUILDING_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>
        <div className="field">
          <label>평수</label>
          <input type="number" min="0" step="0.1" value={customer.area_pyeong} onChange={e => updateCustomer('area_pyeong', parseFloat(e.target.value) || 0)} />
        </div>
      </fieldset>

      <fieldset>
        <legend>작업 항목</legend>
        {calculation.items.map((item, idx) => (
          <div key={idx} className="item-row">
            <div className="field">
              <label>구역 *</label>
              <input value={item.area} onChange={e => updateItem(idx, 'area', e.target.value)} required />
            </div>
            <div className="field">
              <label>작업 *</label>
              <input value={item.task} onChange={e => updateItem(idx, 'task', e.target.value)} required />
            </div>
            <div className="field">
              <label>요일 *</label>
              <div className="day-checkboxes">
                {DAYS_OF_WEEK.map(day => (
                  <label key={day.value}>
                    <input
                      type="checkbox"
                      checked={item.days.includes(day.value)}
                      onChange={e => {
                        const newDays = e.target.checked
                          ? [...item.days, day.value]
                          : item.days.filter(d => d !== day.value);
                        updateItem(idx, 'days', newDays);
                      }}
                    />
                    {day.label}
                  </label>
                ))}
              </div>
            </div>
            <div className="field">
              <label>수량</label>
              <input type="number" min="1" value={item.qty} onChange={e => updateItem(idx, 'qty', parseInt(e.target.value) || 1)} />
            </div>
            <div className="field">
              <label>단가</label>
              <input type="number" min="0" value={item.unit_price} onChange={e => updateItem(idx, 'unit_price', parseInt(e.target.value) || 0)} />
            </div>
            <div className="field">
              <label>제외구역</label>
              <input value={item.exclude_area} onChange={e => updateItem(idx, 'exclude_area', e.target.value)} />
            </div>
            <div className="field">
              <label>메모</label>
              <input value={item.memo} onChange={e => updateItem(idx, 'memo', e.target.value)} />
            </div>
            {calculation.items.length > 1 && (
              <button type="button" className="remove-btn" onClick={() => removeItem(idx)}>삭제</button>
            )}
          </div>
        ))}
        <button type="button" onClick={addItem} className="secondary">항목 추가</button>
      </fieldset>

      <fieldset>
        <legend>계산 설정</legend>
        <div className="field">
          <label>할인 유형</label>
          <select value={calculation.discount_type} onChange={e => updateCalculation('discount_type', e.target.value)}>
            <option value="NONE">없음</option>
            <option value="PERCENT">%</option>
            <option value="AMOUNT">금액</option>
          </select>
        </div>
        <div className="field">
          <label>할인 값</label>
          <input type="number" min="0" value={calculation.discount_value} onChange={e => updateCalculation('discount_value', parseInt(e.target.value) || 0)} />
        </div>
        <div className="field">
          <label>
            <input type="checkbox" checked={calculation.vat_included} onChange={e => updateCalculation('vat_included', e.target.checked)} />
            단가에 VAT 포함
          </label>
        </div>
        <div className="field">
          <label>VAT 비율</label>
          <input type="number" min="0" max="1" step="0.01" value={calculation.vat_rate} onChange={e => updateCalculation('vat_rate', parseFloat(e.target.value) || 0.1)} />
        </div>
      </fieldset>

      <fieldset>
        <legend>기타 설정</legend>
        <div className="field">
          <label>디자인</label>
          <select value={design_key} onChange={e => setDesignKey(e.target.value)}>
            {DESIGN_KEYS.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
          </select>
        </div>
        <div className="field">
          <label>유효기간 (일)</label>
          <input type="number" min="1" max="365" value={expires_days} onChange={e => setExpiresDays(parseInt(e.target.value) || 30)} />
        </div>
        <div className="field">
          <label>프리셋 빈도</label>
          <select value={preset_frequency} onChange={e => setPresetFrequency(e.target.value)}>
            <option value="">선택 안 함</option>
            {PRESET_FREQUENCIES.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
          </select>
          <small>선택 시 요일이 자동 설정됩니다</small>
        </div>
      </fieldset>

      <div className="actions">
        <button onClick={handlePreview} disabled={loading} className="primary">
          {loading ? '계산 중...' : '미리보기'}
        </button>
      </div>
    </div>
  );
}