import React from 'react';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

interface AppShellProps {
  children: React.ReactNode;
  breadcrumb?: string;
}

export const AppShell: React.FC<AppShellProps> = ({ children, breadcrumb }) => {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main-pane">
        <TopBar breadcrumb={breadcrumb} />
        <main className="page-container">
          {children}
        </main>
      </div>
    </div>
  );
};
