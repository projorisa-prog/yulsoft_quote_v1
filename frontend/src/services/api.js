import axios from 'axios';

const API_BASE = '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 견적 미리보기
export const previewQuote = async (data) => {
  const response = await api.post('/quotes/preview', data);
  return response.data;
};

// 견적서 생성 및 저장
export const createQuote = async (data) => {
  const response = await api.post('/quotes', data);
  return response.data;
};

// 견적서 조회
export const getQuote = async (publicId) => {
  const response = await api.get(`/quotes/${publicId}`);
  return response.data;
};

// PDF 다운로드
export const downloadQuotePdf = async (publicId) => {
  const response = await api.get(`/quotes/${publicId}/pdf`, {
    responseType: 'blob',
  });
  return response.data;
};

// 공유 링크 생성
export const createShareLink = async (publicId) => {
  const response = await api.post(`/quotes/${publicId}/share-link`);
  return response.data;
};

// 헬스 체크
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;