import React from 'react';
import { Link, useLocation } from 'react-router-dom';

interface TopBarProps {
  breadcrumb?: string;
}

export const TopBar: React.FC<TopBarProps> = ({ breadcrumb }) => {
  const location = useLocation();

  const getSectionTitle = () => {
    if (breadcrumb) return breadcrumb;
    const path = location.pathname;
    if (path.startsWith('/dashboard')) return 'Dashboard › Student Command Center';
    if (path.startsWith('/learn/test') || path.startsWith('/diagnostics')) return 'Mathematics › Algebra › Expanding the Square of a Binomial';
    if (path.startsWith('/learn')) return 'Curriculum Browser › Mathematics';
    if (path.startsWith('/progress')) return 'Diagnostic Model › Conceptual Progress';
    if (path.startsWith('/history')) return 'Attempt Ledger › Longitudinal History';
    if (path.startsWith('/settings')) return 'System › Student Configuration';
    return 'Learning Debugger';
  };

  return (
    <header className="app-topbar">
      <div className="topbar-left">
        <span style={{ color: 'var(--lime)', fontSize: '0.8rem' }}>◈</span>
        <span className="topbar-crumb-active">{getSectionTitle()}</span>
      </div>

      <div className="topbar-right">
        <div className="system-status-indicator">
          <span className="status-dot-pulse" />
          <span>Diagnostic Engine Ready</span>
        </div>

        {!location.pathname.startsWith('/diagnostics') && !location.pathname.startsWith('/learn/test') && (
          <Link to="/diagnostics" className="btn btn-primary btn-sm">
            Launch Diagnostic ⚡
          </Link>
        )}
      </div>
    </header>
  );
};
