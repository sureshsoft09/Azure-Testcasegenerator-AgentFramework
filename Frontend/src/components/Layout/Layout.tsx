import { NavLink } from 'react-router-dom';
import {
  MdDashboard, MdAutoAwesome, MdBuildCircle,
  MdMoveToInbox, MdBarChart,
} from 'react-icons/md';
import './Layout.css';

const NAV_ITEMS = [
  { to: '/dashboard', icon: <MdDashboard size={17} />, label: 'Dashboard' },
  { to: '/generate',  icon: <MdAutoAwesome size={17} />, label: 'Generate' },
  { to: '/enhance',   icon: <MdBuildCircle size={17} />, label: 'Enhance' },
  { to: '/migrate',   icon: <MdMoveToInbox size={17} />, label: 'Migrate' },
  { to: '/analytics', icon: <MdBarChart size={17} />,    label: 'Analytics' },
];

interface LayoutProps { children: React.ReactNode; }

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="layout">
      {/* ─── Top Navigation Bar ─────────────────────────────────────── */}
      <header className="topbar">
        {/* Brand (logo + title) */}
        <div className="topbar-brand">
          <img
            src="/Cognizant-logo.png"
            alt="Cognizant"
            className="brand-logo-img"
          />
          <div className="topbar-divider-thin" />
          <div className="brand-text">
            <div className="brand-sub">AI TestGen · Multi-Agent Framework</div>
          </div>
        </div>

        {/* Divider */}
        <div className="topbar-divider" />

        {/* Navigation tabs */}
        <nav className="topbar-nav">
          {NAV_ITEMS.map(({ to, icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => `topnav-item${isActive ? ' active' : ''}`}
            >
              {icon}
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Right side badge */}
        <div className="topbar-right">
          <div className="status-pill">
            <span className="status-dot" />
            <span>Live</span>
          </div>
        </div>
      </header>

      {/* ─── Page Content ──────────────────────────────────────────── */}
      <main className="main-content">
        <div className="content-inner">{children}</div>
      </main>
    </div>
  );
}
