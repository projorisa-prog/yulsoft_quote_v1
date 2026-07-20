import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import QuoteForm from './components/QuoteForm';
import QuoteDetail from './components/QuoteDetail';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<QuoteForm />} />
        <Route path="/quote/:quoteId" element={<QuoteDetail />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;