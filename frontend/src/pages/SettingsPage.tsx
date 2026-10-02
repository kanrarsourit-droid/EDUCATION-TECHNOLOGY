import React, { useState } from 'react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeader } from '../components/ui/PageHeader';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useAuth } from '../context/AuthContext';

export const SettingsPage: React.FC = () => {
  const { student, user, signOut } = useAuth();

  // Local state for learning preferences
  const [reasoningDepth, setReasoningDepth] = useState<'detailed' | 'concise'>('detailed');
  const [showCounterExamples, setShowCounterExamples] = useState<boolean>(true);
  const [autoAdvanceRetry, setAutoAdvanceRetry] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  const handleSavePreferences = (e: React.FormEvent) => {
    e.preventDefault();
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (err) {
      console.error('Sign out error:', err);
    }
  };

  return (
    <AppShell breadcrumb="System / Settings">
      <div style={{ maxWidth: 960, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
        <PageHeader
          badge={<StatusBadge status="neutral" label="CONFIGURATION" />}
          title="System Settings"
          subtitle="Manage your diagnostic profile, reasoning preferences, and authentication parameters."
        />

        {saveSuccess && (
          <div
            style={{
              padding: '12px 16px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(101, 230, 176, 0.1)',
              border: '1px solid var(--accent-mint)',
              color: 'var(--accent-mint)',
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span>✓</span>
            <span>Preferences saved successfully to local session.</span>
          </div>
        )}

        {/* 1. Profile Section */}
        <Card title="Student Profile">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 20 }}>
            <div>
              <span className="mono-sub" style={{ display: 'block', marginBottom: 6 }}>STUDENT NAME</span>
              <div style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                {student?.full_name || 'Anonymous Student'}
              </div>
            </div>

            <div>
              <span className="mono-sub" style={{ display: 'block', marginBottom: 6 }}>EMAIL ADDRESS</span>
              <div style={{ fontSize: '0.95rem', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                {user?.email || 'N/A'}
              </div>
            </div>

            <div>
              <span className="mono-sub" style={{ display: 'block', marginBottom: 6 }}>STUDENT ID</span>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                {student?.id || 'Pending provisioning'}
              </div>
            </div>

            <div>
              <span className="mono-sub" style={{ display: 'block', marginBottom: 6 }}>PROFILE STATUS</span>
              <div style={{ marginTop: 2 }}>
                <StatusBadge status="success" label="Active & Provisioned" />
              </div>
            </div>
          </div>
        </Card>

        {/* 2. Learning Preferences */}
        <Card title="Diagnostic & Reasoning Preferences">
          <form onSubmit={handleSavePreferences} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
                Reasoning Prompt Depth
              </label>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 12 }}>
                Controls whether the diagnostic workspace prompts for step-by-step intermediate explanations.
              </p>
              <div style={{ display: 'flex', gap: 12 }}>
                <button
                  type="button"
                  onClick={() => setReasoningDepth('detailed')}
                  style={{
                    flex: 1,
                    padding: '12px 16px',
                    borderRadius: 'var(--radius-sm)',
                    background: reasoningDepth === 'detailed' ? 'rgba(182, 242, 58, 0.08)' : 'var(--bg-elevated)',
                    border: `1px solid ${reasoningDepth === 'detailed' ? 'var(--accent-lime)' : 'var(--border-color)'}`,
                    color: reasoningDepth === 'detailed' ? 'var(--accent-lime)' : 'var(--text-primary)',
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 4 }}>Detailed Reasoning</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    Requires structured explanations, confidence calibration, and intermediate steps.
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setReasoningDepth('concise')}
                  style={{
                    flex: 1,
                    padding: '12px 16px',
                    borderRadius: 'var(--radius-sm)',
                    background: reasoningDepth === 'concise' ? 'rgba(182, 242, 58, 0.08)' : 'var(--bg-elevated)',
                    border: `1px solid ${reasoningDepth === 'concise' ? 'var(--accent-lime)' : 'var(--border-color)'}`,
                    color: reasoningDepth === 'concise' ? 'var(--accent-lime)' : 'var(--text-primary)',
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 4 }}>Concise Summary</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    Faster workflow with streamlined single-box reasoning input.
                  </div>
                </button>
              </div>
            </div>

            <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: 16 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={showCounterExamples}
                  onChange={(e) => setShowCounterExamples(e.target.checked)}
                  style={{
                    width: 18,
                    height: 18,
                    accentColor: 'var(--accent-lime)',
                    cursor: 'pointer',
                  }}
                />
                <div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    Auto-display targeted counter-examples upon misconception detection
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Shows numeric or symbolic paradoxes to disconfirm faulty rules immediately.
                  </div>
                </div>
              </label>
            </div>

            <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: 16 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={autoAdvanceRetry}
                  onChange={(e) => setAutoAdvanceRetry(e.target.checked)}
                  style={{
                    width: 18,
                    height: 18,
                    accentColor: 'var(--accent-lime)',
                    cursor: 'pointer',
                  }}
                />
                <div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    Sequential retry chaining
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Automatically link subsequent attempt submissions to parent diagnostic attempts.
                  </div>
                </div>
              </label>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
              <Button type="submit" variant="primary" size="sm">
                Save Preferences
              </Button>
            </div>
          </form>
        </Card>

        {/* 3. Appearance */}
        <Card title="Appearance & Diagnostics Theme">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              Learning Debugger adheres to a scientific, high-contrast Dark Obsidian and Graphite design system engineered for prolonged diagnostic work.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
              <div
                style={{
                  padding: 16,
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 14, height: 14, borderRadius: 3, background: 'var(--bg-primary)', border: '1px solid var(--border-color)' }} />
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>Dark Obsidian</span>
                </div>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>#080A0D (Primary Canvas)</span>
              </div>

              <div
                style={{
                  padding: 16,
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 14, height: 14, borderRadius: 3, background: 'var(--accent-lime)' }} />
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>Electric Lime</span>
                </div>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>#B6F23A (System Accent)</span>
              </div>

              <div
                style={{
                  padding: 16,
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 14, height: 14, borderRadius: 3, background: 'var(--accent-coral)' }} />
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>Coral Warning</span>
                </div>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>#FF5C67 (Misconceptions)</span>
              </div>

              <div
                style={{
                  padding: 16,
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 14, height: 14, borderRadius: 3, background: 'var(--accent-mint)' }} />
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>Mint Success</span>
                </div>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>#65E6B0 (Repairs / Mastery)</span>
              </div>
            </div>
          </div>
        </Card>

        {/* 4. Authentication & System Status */}
        <Card title="Authentication & Infrastructure">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16 }}>
              <div
                style={{
                  padding: '14px 16px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                }}
              >
                <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: 4 }}>
                  IDENTITY PROVIDER
                </div>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  Supabase Auth (JWT & OAuth)
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--accent-mint)', marginTop: 4 }}>
                  ● Session Verified
                </div>
              </div>

              <div
                style={{
                  padding: '14px 16px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                }}
              >
                <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: 4 }}>
                  DIAGNOSTIC BACKEND
                </div>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  FastAPI REST Engine
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--accent-mint)', marginTop: 4 }}>
                  ● Connected (127.0.0.1:8000)
                </div>
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                paddingTop: 16,
                borderTop: '1px solid var(--border-color)',
              }}
            >
              <div>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  Sign Out of Learning Debugger
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  Terminates local session tokens and redirects to the login gateway.
                </div>
              </div>

              <Button variant="danger" size="sm" onClick={handleSignOut}>
                Sign Out
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </AppShell>
  );
};
