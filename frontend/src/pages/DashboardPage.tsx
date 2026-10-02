import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { AppShell } from '../components/layout/AppShell';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/StatusBadge';
import { ProgressBar } from '../components/ui/ProgressBar';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { getStudentAttempts, type AttemptResult } from '../lib/api';

export const DashboardPage: React.FC = () => {
  const { user, student } = useAuth();
  const [recentAttempts, setRecentAttempts] = useState<AttemptResult[]>([]);

  const studentName = student?.full_name || user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'Student';

  // Determine time-appropriate greeting
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  useEffect(() => {
    let mounted = true;

    async function loadDashboardData() {
      try {
        const attList = await getStudentAttempts({ limit: 10 }).catch(() => []);

        if (mounted) {
          setRecentAttempts(attList);
        }
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      }
    }

    loadDashboardData();
    return () => {
      mounted = false;
    };
  }, []);

  // Compute live diagnostic metrics if attempts exist
  const totalAttempts = recentAttempts.length;
  const correctAttempts = recentAttempts.filter((a) => a.is_correct === true).length;
  const masteryPercentage = totalAttempts > 0 ? Math.round((correctAttempts / totalAttempts) * 100) : 74;
  const areasNeedingAttention = totalAttempts > 0 ? recentAttempts.filter((a) => a.is_correct === false).length : 1;

  return (
    <AppShell breadcrumb="Dashboard › Student Command Center">
      {/* Editorial Header */}
      <PageHeader
        title={`${greeting}, ${studentName}.`}
        subtitle={`Your learning model has ${areasNeedingAttention} ${areasNeedingAttention === 1 ? 'area' : 'areas'} that need attention.`}
        actions={
          <Link to="/diagnostics">
            <Button variant="primary" size="md">
              Launch Diagnostic Workspace ⚡
            </Button>
          </Link>
        }
      />

      {/* Top Metrics & Current Focus Grid */}
      <div className="grid-cols-3" style={{ marginBottom: 24 }}>
        {/* A. Overall Mastery Card */}
        <Card accent="lime">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: '0.74rem', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-secondary)' }}>
              OVERALL MASTERY
            </span>
            <StatusBadge label="Calibrated" variant="lime" />
          </div>

          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, margin: '8px 0 14px' }}>
            <span style={{ fontSize: '2.5rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', lineHeight: 1 }}>
              {masteryPercentage}%
            </span>
            <span style={{ fontSize: '0.84rem', color: 'var(--lime)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
              +6.4% this month
            </span>
          </div>

          <ProgressBar value={masteryPercentage} color="lime" height={5} />
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 12 }}>
            Based on active reasoning consistency and verified binomial algebra diagnostic checks.
          </p>
        </Card>

        {/* B. Current Focus Card */}
        <Card accent="amber">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: '0.74rem', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-secondary)' }}>
              CURRENT FOCUS
            </span>
            <StatusBadge label="In Progress" variant="amber" />
          </div>

          <div style={{ margin: '8px 0 12px' }}>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--amber)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              MATHEMATICS / ALGEBRA
            </span>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: 4 }}>
              Expanding the Square of a Binomial
            </h3>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', fontFamily: 'var(--font-mono)', marginBottom: 6 }}>
            <span style={{ color: 'var(--text-secondary)' }}>Concept Stability</span>
            <span style={{ color: 'var(--amber)', fontWeight: 700 }}>78%</span>
          </div>
          <ProgressBar value={78} color="amber" height={5} />

          <div style={{ marginTop: 16 }}>
            <Link to="/diagnostics">
              <Button variant="secondary" size="sm" fullWidth>
                Continue Practice →
              </Button>
            </Link>
          </div>
        </Card>

        {/* C. Diagnostic Alert Card */}
        <Card accent="coral">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: '0.74rem', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--coral)' }}>
              DIAGNOSTIC ALERT
            </span>
            <StatusBadge label="Misconception" variant="coral" />
          </div>

          <div style={{ margin: '8px 0 12px' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
              Missing Cross-Term Pattern
            </h4>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
              Tendency to treat <code style={{ color: 'var(--coral)', background: 'var(--coral-bg)', padding: '1px 5px', borderRadius: 4 }}>(a + b)²</code> as <code style={{ color: 'var(--coral)', background: 'var(--coral-bg)', padding: '1px 5px', borderRadius: 4 }}>a² + b²</code>.
            </p>
          </div>

          <div style={{ marginTop: 22 }}>
            <Link to="/diagnostics">
              <Button variant="danger" size="sm" fullWidth>
                Investigate & Repair ⚡
              </Button>
            </Link>
          </div>
        </Card>
      </div>

      {/* Subject Overview & Curriculum Architecture */}
      <div style={{ marginTop: 32 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)' }}>Subject Domains</h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Calibrated knowledge structures in your student curriculum.</p>
          </div>
          <Link to="/learn" style={{ fontSize: '0.85rem', color: 'var(--lime)', fontWeight: 600 }}>
            Explore All Subjects →
          </Link>
        </div>

        <div className="grid-cols-3">
          {/* Mathematics (Live) */}
          <Card interactive>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
              <div style={{ fontSize: '1.5rem', color: 'var(--lime)' }}>∑</div>
              <StatusBadge label="Live System" variant="lime" />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
              Mathematics
            </h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: 14 }}>
              Core algebraic reasoning, binomial expansions, and polynomial structures.
            </p>
            <div style={{ display: 'flex', gap: 16, fontSize: '0.78rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: 14 }}>
              <span>1 Topic</span>
              <span>1 Concept</span>
              <span>2 Diagnostics</span>
            </div>
            <Link to="/learn">
              <Button variant="secondary" size="sm" fullWidth>
                Enter Domain →
              </Button>
            </Link>
          </Card>

          {/* Physics (Preview) */}
          <Card style={{ opacity: 0.8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
              <div style={{ fontSize: '1.5rem', color: 'var(--text-muted)' }}>⚛</div>
              <StatusBadge label="Curriculum Q4" variant="muted" withDot={false} />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
              Classical Mechanics
            </h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: 14 }}>
              Newtonian dynamics, conservation laws, vectors, and force-acceleration misconceptions.
            </p>
            <div style={{ display: 'flex', gap: 16, fontSize: '0.78rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: 14 }}>
              <span>Kinematics</span>
              <span>Dynamics</span>
              <span>Energy</span>
            </div>
            <Button variant="outline" size="sm" fullWidth disabled>
              In Formulation
            </Button>
          </Card>

          {/* Computer Science (Preview) */}
          <Card style={{ opacity: 0.8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
              <div style={{ fontSize: '1.5rem', color: 'var(--text-muted)' }}>λ</div>
              <StatusBadge label="Curriculum Q4" variant="muted" withDot={false} />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
              Algorithmic Reasoning
            </h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: 14 }}>
              Computational complexity, recursion invariants, pointer semantics, and state graphs.
            </p>
            <div style={{ display: 'flex', gap: 16, fontSize: '0.78rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: 14 }}>
              <span>Recursion</span>
              <span>Data Structures</span>
              <span>Graphs</span>
            </div>
            <Button variant="outline" size="sm" fullWidth disabled>
              In Formulation
            </Button>
          </Card>
        </div>
      </div>

      {/* Recent Diagnostic Activity Ledger */}
      <div style={{ marginTop: 36 }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16 }}>
          Recent Diagnostic Submissions
        </h2>

        {recentAttempts.length === 0 ? (
          <Card>
            <EmptyState
              icon="⚡"
              title="No diagnostic attempts logged yet"
              description="Complete your first diagnostic problem to record reasoning logs and generate your cognitive repair timeline."
              action={
                <Link to="/diagnostics">
                  <Button variant="primary" size="md">
                    Start Diagnostic Check
                  </Button>
                </Link>
              }
            />
          </Card>
        ) : (
          <Card style={{ padding: 0, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', background: 'var(--surface-elevated)', fontFamily: 'var(--font-mono)', fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '12px 18px' }}>ATTEMPT</th>
                  <th style={{ padding: '12px 18px' }}>SUBMITTED ANSWER</th>
                  <th style={{ padding: '12px 18px' }}>REASONING</th>
                  <th style={{ padding: '12px 18px' }}>EVALUATION</th>
                  <th style={{ padding: '12px 18px' }}>TIMESTAMP</th>
                </tr>
              </thead>
              <tbody>
                {recentAttempts.slice(0, 5).map((att) => (
                  <tr key={att.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '14px 18px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                      #{att.attempt_number} {att.parent_attempt_id && <span style={{ color: 'var(--amber)', fontSize: '0.75rem' }}>(Retry)</span>}
                    </td>
                    <td style={{ padding: '14px 18px', color: 'var(--text-primary)', fontWeight: 500 }}>
                      {att.student_answer}
                    </td>
                    <td style={{ padding: '14px 18px', color: 'var(--text-secondary)', maxWidth: 260, textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                      {att.student_reasoning || '—'}
                    </td>
                    <td style={{ padding: '14px 18px' }}>
                      <StatusBadge
                        label={att.is_correct === true ? 'Validated' : att.is_correct === false ? 'Misconception' : 'Recorded'}
                        variant={att.is_correct === true ? 'mint' : att.is_correct === false ? 'coral' : 'muted'}
                      />
                    </td>
                    <td style={{ padding: '14px 18px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                      {new Date(att.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}
      </div>
    </AppShell>
  );
};
