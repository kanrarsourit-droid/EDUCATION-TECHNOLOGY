import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/StatusBadge';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { getStudentAttempts, type AttemptResult } from '../lib/api';

export const HistoryPage: React.FC = () => {
  const [attempts, setAttempts] = useState<AttemptResult[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function loadHistory() {
      try {
        setLoading(true);
        const list = await getStudentAttempts({ limit: 50 });
        if (mounted) {
          setAttempts(list);
          if (list.length > 0) setExpandedId(list[0].id);
        }
      } catch (err) {
        console.error('Failed to load history:', err);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadHistory();
    return () => {
      mounted = false;
    };
  }, []);

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <AppShell breadcrumb="Attempt Ledger › Longitudinal History">
      <PageHeader
        title="Diagnostic History & Ledger"
        subtitle="Chronological log of submitted problem attempts, diagnostic evaluations, and cognitive retry chains."
        actions={
          <Link to="/diagnostics">
            <Button variant="primary" size="md">
              New Diagnostic Attempt ⚡
            </Button>
          </Link>
        }
      />

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
          <div className="spinner-ring" style={{ margin: '0 auto 16px' }} />
          <p>Loading attempt ledger from Supabase...</p>
        </div>
      ) : attempts.length === 0 ? (
        <Card>
          <EmptyState
            icon="⏱"
            title="No diagnostic history recorded yet"
            description="Your learning ledger logs intermediate reasoning, identified misconceptions, and verified concept repairs."
            action={
              <Link to="/diagnostics">
                <Button variant="primary" size="md">
                  Run First Diagnostic Check
                </Button>
              </Link>
            }
          />
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {attempts.map((att) => {
            const isExpanded = expandedId === att.id;
            const isRetry = !!att.parent_attempt_id;
            const dateStr = new Date(att.created_at).toLocaleDateString(undefined, {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
            });
            const timeStr = new Date(att.created_at).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            });

            return (
              <Card
                key={att.id}
                accent={att.is_correct === true ? 'mint' : att.is_correct === false ? 'coral' : undefined}
                style={{ padding: '18px 22px' }}
              >
                {/* Attempt Row Header */}
                <div
                  style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
                  onClick={() => toggleExpand(att.id)}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)', minWidth: 80 }}>
                      {dateStr}
                    </div>

                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.96rem' }}>
                          Expanding the Square of a Binomial
                        </span>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                          Attempt #{att.attempt_number}
                        </span>
                        {isRetry && <StatusBadge label="Retry Linked" variant="amber" />}
                      </div>
                      <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: 2 }}>
                        Answer: <code style={{ color: 'var(--text-primary)' }}>{att.student_answer}</code>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                    <StatusBadge
                      label={
                        att.is_correct === true
                          ? isRetry
                            ? 'Concept Repaired'
                            : 'Validated'
                          : att.is_correct === false
                          ? 'Misconception Detected'
                          : 'Recorded'
                      }
                      variant={att.is_correct === true ? 'mint' : att.is_correct === false ? 'coral' : 'muted'}
                    />
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      {isExpanded ? '▲' : '▼'}
                    </span>
                  </div>
                </div>

                {/* Expanded Details Drawer */}
                {isExpanded && (
                  <div style={{ marginTop: 18, paddingTop: 16, borderTop: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14 }}>
                      <div className="card card-elevated" style={{ padding: '12px 14px' }}>
                        <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                          SUBMITTED REASONING
                        </span>
                        <p style={{ fontSize: '0.86rem', color: 'var(--text-primary)', marginTop: 4, fontStyle: att.student_reasoning ? 'normal' : 'italic' }}>
                          {att.student_reasoning || 'No written explanation provided for this attempt.'}
                        </p>
                      </div>

                      <div className="card card-elevated" style={{ padding: '12px 14px' }}>
                        <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                          CONFIDENCE RATING
                        </span>
                        <p style={{ fontSize: '0.86rem', color: 'var(--lime)', marginTop: 4, fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                          {att.confidence_score !== null ? `${Math.round(att.confidence_score * 100)}% Confidence` : 'Not recorded'}
                        </p>
                      </div>

                      <div className="card card-elevated" style={{ padding: '12px 14px' }}>
                        <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                          AUDIT RECORD
                        </span>
                        <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 4, fontFamily: 'var(--font-mono)' }}>
                          ID: {att.id.slice(0, 14)}...<br />
                          Logged at: {timeStr}
                        </p>
                      </div>
                    </div>

                    {isRetry && att.parent_attempt_id && (
                      <div style={{ background: 'var(--bg-secondary)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', fontSize: '0.82rem', color: 'var(--amber)', fontFamily: 'var(--font-mono)' }}>
                        🔗 Retried from Parent Attempt: {att.parent_attempt_id}
                      </div>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </AppShell>
  );
};
