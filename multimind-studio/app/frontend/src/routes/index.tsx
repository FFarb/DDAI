import { RouteObject } from 'react-router-dom';
import ChatPage from '../pages/ChatPage';
import RagPage from '../pages/RagPage';
import ScriptsPage from '../pages/ScriptsPage';
import SettingsPage from '../pages/SettingsPage';
import TradingPage from '../pages/TradingPage';

export const routes: RouteObject[] = [
  { path: '/', element: <ChatPage /> },
  { path: '/rag', element: <RagPage /> },
  { path: '/scripts', element: <ScriptsPage /> },
  { path: '/settings', element: <SettingsPage /> },
  { path: '/trading', element: <TradingPage /> },
];
