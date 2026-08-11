import { Routes, Route, Navigate } from 'react-router-dom';
import LoginChoicePage from './pages/LoginChoicePage';
import CorporateLoginPage from './pages/CorporateLoginPage';
import VisitorSmsPage from './pages/VisitorSmsPage';
import VisitorRoomPage from './pages/VisitorRoomPage';
import SuccessPage from './pages/SuccessPage';

// Le portail expose un flux volontairement simple : choix du type de
// connexion, puis formulaire dedie, puis page de confirmation. Les
// parametres MAC/IP transmis par l'equipement Wi-Fi (voir
// context/WifiParamsContext.tsx) sont conserves tout au long de ce parcours,
// meme si l'utilisateur navigue directement sur une URL profonde.
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LoginChoicePage />} />
      <Route path="/corporate" element={<CorporateLoginPage />} />
      <Route path="/visitor/sms" element={<VisitorSmsPage />} />
      <Route path="/visitor/room" element={<VisitorRoomPage />} />
      <Route path="/success" element={<SuccessPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
