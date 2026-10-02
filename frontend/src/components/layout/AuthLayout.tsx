import React from 'react';

interface AuthLayoutProps {
  children: React.ReactNode;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ children }) => {
  return (
    <div className="auth-split-wrapper">
      {/* Left Branding & Conceptual Pipeline */}
      <aside className="auth-brand-pane">
        <div className="auth-brand-header">
          <span className="brand-symbol">◈</span>
          <h1 className="brand-title-lg">LEARNING DEBUGGER</h1>
          <p className="brand-tagline">
            Understand what you know.<br />
            Find what you don&apos;t.
          </p>
        </div>

        {/* Diagnostic Pipeline Diagram */}
        <div className="auth-pipeline-container">
          <div className="pipeline-caption">Conceptual Diagnostic Architecture</div>
          <div className="pipeline-flow">
            <div className="pipeline-step">
              <span className="step-num">01</span>
              <span className="step-label">DIAGNOSTIC QUESTION</span>
            </div>
            <div className="step-arrow">↓</div>

            <div className="pipeline-step">
              <span className="step-num">02</span>
              <span className="step-label">STUDENT REASONING</span>
            </div>
            <div className="step-arrow">↓</div>

            <div className="pipeline-step pipeline-step-active">
              <span className="step-num">03</span>
              <span className="step-label">MISCONCEPTION DETECTION</span>
            </div>
            <div className="step-arrow">↓</div>

            <div className="pipeline-step">
              <span className="step-num">04</span>
              <span className="step-label">TARGETED INTERVENTION</span>
            </div>
            <div className="step-arrow">↓</div>

            <div className="pipeline-step">
              <span className="step-num">05</span>
              <span className="step-label">CONCEPTUAL REPAIR</span>
            </div>
          </div>
        </div>

        <div className="auth-brand-footer">
          Research-grade educational diagnostics · Supabase Auth Protected
        </div>
      </aside>

      {/* Right Auth Form Pane */}
      <main className="auth-form-pane">
        <div className="auth-card-inner">
          {children}
        </div>
      </main>
    </div>
  );
};
