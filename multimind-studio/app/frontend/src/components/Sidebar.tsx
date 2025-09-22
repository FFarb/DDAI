import { NavLink } from 'react-router-dom';
import { CandlestickChart } from 'lucide-react';

const Sidebar = () => {
  return (
    <aside className="sidebar">
      <h2>MultiMind</h2>
      <nav>
        <NavLink to="/" end>
          Chat
        </NavLink>
        <NavLink to="/rag">RAG</NavLink>
        <NavLink to="/scripts">Scripts</NavLink>
        <NavLink to="/settings">Settings</NavLink>
        <NavLink to="/trading">
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
            <CandlestickChart size={16} />
            <span>Trading</span>
          </span>
        </NavLink>
      </nav>
    </aside>
  );
};

export default Sidebar;
