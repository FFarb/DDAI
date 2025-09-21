import { RouteObject } from 'react-router-dom';
import ChatPage from '../pages/ChatPage';
import RagPage from '../pages/RagPage';
import ScriptsPage from '../pages/ScriptsPage';
import SettingsPage from '../pages/SettingsPage';

export const routes: RouteObject[] = [
  { path: '/', element: <ChatPage /> },
  { path: '/rag', element: <RagPage /> },
  { path: '/scripts', element: <ScriptsPage /> },
  { path: '/settings', element: <SettingsPage /> },
];
