import { NavLink } from 'react-router-dom';

const Sidebar = () => {
  return (
    <aside className="sidebar">
      <h2>MultiMind</h2>
      <NavLink to="/" end>
        Chat
      </NavLink>
      <NavLink to="/rag">RAG</NavLink>
      <NavLink to="/scripts">Scripts</NavLink>
      <NavLink to="/settings">Settings</NavLink>
    </aside>
  );
};

export default Sidebar;
