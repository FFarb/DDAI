import { Routes, Route } from 'react-router-dom';
import ChatPage from './pages/ChatPage';
import RagPage from './pages/RagPage';
import ScriptsPage from './pages/ScriptsPage';
import SettingsPage from './pages/SettingsPage';
import TradingPage from './pages/TradingPage';
import Sidebar from './components/Sidebar';

function App() {
  return (
    <div className="layout">
      <Sidebar />
      <main className="content">
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/rag" element={<RagPage />} />
          <Route path="/scripts" element={<ScriptsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/trading" element={<TradingPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
