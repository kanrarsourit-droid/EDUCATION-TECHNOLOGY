import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { StatusBadge } from '../ui/StatusBadge';

export const Sidebar: React.FC = () => {
  const { user, student, signOut } = useAuth();
  const navigate = useNavigate();

  const handleSignOut = async () => {
    try {
      await signOut();
      navigate('/login');
    } catch (err) {
      console.error('Sign out error:', err);
    }
  };

  const displayName = student?.full_name || user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'Student';
  const initial = displayName.charAt(0).toUpperCase();

  return (
    <aside className="app-sidebar">
      <div>
        {/* Top Logo */}
        <div className="sidebar-logo">
          <span className="sidebar-logo-mark">◈</span>
          <div className="sidebar-logo-text">
            LEARNING<br />DEBUGGER
          </div>
        </div>

        {/* Primary Navigation */}
        <div className="sidebar-section-title">Diagnostic System</div>
        <ul className="sidebar-nav-list">
          <li>
            <NavLink
              to="/dashboard"
              className={({ isActive }) => `sidebar-nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="sidebar-nav-label">
                <span className="sidebar-icon">⬡</span>
                <span>Dashboard</span>
              </span>
            </NavLink>
          </li>
          <li>
            <NavLink
              to="/learn"
              className={({ isActive }) => `sidebar-nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="sidebar-nav-label">
                <span className="sidebar-icon">⌬</span>
                <span>Learn</span>
              </span>
            </NavLink>
          </li>
          <li>
            <NavLink
              to="/diagnostics"
              className={({ isActive }) => `sidebar-nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="sidebar-nav-label">
                <span className="sidebar-icon">⚡</span>
                <span>Diagnostics</span>
              </span>
              <StatusBadge label="Active" variant="lime" withDot={false} />
            </NavLink>
          </li>
          <li>
            <NavLink
              to="/progress"
              className={({ isActive }) => `sidebar-nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="sidebar-nav-label">
                <span className="sidebar-icon">📈</span>
                <span>Progress</span>
              </span>
            </NavLink>
          </li>
          <li>
            <NavLink
              to="/history"
              className={({ isActive }) => `sidebar-nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="sidebar-nav-label">
                <span className="sidebar-icon">⏱</span>
                <span>History</span>
              </span>
            </NavLink>
          </li>
        </ul>

        {/* Knowledge Domains / Subjects */}
        <div className="sidebar-section-title" style={{ marginTop: 12 }}>Subjects</div>
        <ul className="sidebar-nav-list">
          <li>
            <NavLink
              to="/learn"
              className={({ isActive }) => `sidebar-nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="sidebar-nav-label">
                <span className="sidebar-icon">∑</span>
                <span>Mathematics</span>
              </span>
              <StatusBadge label="Live" variant="lime" withDot={false} />
            </NavLink>
          </li>
          <li>
            <div className="sidebar-nav-item" style={{ opacity: 0.6, cursor: 'default' }}>
              <span className="sidebar-nav-label">
                <span className="sidebar-icon">⚛</span>
                <span>Physics</span>
              </span>
              <StatusBadge label="Soon" variant="muted" withDot={false} />
            </div>
          </li>
          <li>
            <div className="sidebar-nav-item" style={{ opacity: 0.6, cursor: 'default' }}>
              <span className="sidebar-nav-label">
                <span className="sidebar-icon">λ</span>
                <span>Programming</span>
              </span>
              <StatusBadge label="Soon" variant="muted" withDot={false} />
            </div>
          </li>
        </ul>
      </div>

      {/* Bottom Area: Settings & User Identity */}
      <div className="sidebar-footer">
        <NavLink
          to="/settings"
          className={({ isActive }) => `sidebar-nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="sidebar-nav-label">
            <span className="sidebar-icon">⚙</span>
            <span>Settings & Profile</span>
          </span>
        </NavLink>

        <div className="sidebar-user-card">
          <div className="user-avatar">{initial}</div>
          <div className="user-info">
            <span className="user-name">{displayName}</span>
            <span className="user-role">{student?.id ? `ID: ${student.id.slice(0, 8)}...` : 'Connecting...'}</span>
          </div>
        </div>

        <button
          onClick={handleSignOut}
          className="btn btn-outline btn-sm btn-full"
          style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}
        >
          Sign Out
        </button>
      </div>
    </aside>
  );
};
