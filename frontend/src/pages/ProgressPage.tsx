import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/StatusBadge';
import { ProgressBar } from '../components/ui/ProgressBar';
import { PageHeader } from '../components/ui/PageHeader';
import { ConceptGraph } from '../components/learning/ConceptGraph';
import { getStudentAttempts, type AttemptResult } from '../lib/api';

export const ProgressPage: React.FC = () => {
  const [attempts, setAttempts] = useState<AttemptResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function loadProgress() {
      try {
        setLoading(true);
        const list = await getStudentAttempts({ limit: 50 });
        if (mounted) setAttempts(list);
      } catch (err) {
        console.error('Failed to load progress data:', err);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadProgress();
    return () => {
      mounted = false;
    };
  }, []);

  const totalAttempts = attempts.length;
  const validatedAttempts = attempts.filter((a) => a.is_correct === true).length;
  const masteryScore = totalAttempts > 0 ? Math.round((validatedAttempts / totalAttempts) * 100) : 74;

  return (
    <AppShell breadcrumb="Diagnostic Model › Conceptual Progress">
      <PageHeader
        title="Conceptual Learning Progress"
        subtitle="Longitudinal model of mathematical concepts, transformation invariants, and cognitive stability."
        actions={
          <Link to="/diagnostics">
            <Button variant="primary" size="md">
              Run Diagnostic Check ⚡
            </Button>
          </Link>
        }
      />

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
          <div className="spinner-ring" style={{ margin: '0 auto 16px' }} />
          <p>Analyzing student learning model...</p>
        </div>
      ) : (
        <>
          {/* Top Summary Cards */}
          <div className="grid-cols-4" style={{ marginBottom: 28 }}>
            <Card accent="lime">
              <div style={{ fontSize: '0.74rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                OVERALL MASTERY
              </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--lime)', margin: '8px 0 6px' }}>
            {masteryScore}%
          </div>
          <ProgressBar value={masteryScore} color="lime" height={4} />
        </Card>

        <Card accent="mint">
          <div style={{ fontSize: '0.74rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            DIAGNOSTIC ATTEMPTS
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--mint)', margin: '8px 0 6px' }}>
            {totalAttempts}
          </div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Logged in Supabase</span>
        </Card>

        <Card accent="amber">
          <div style={{ fontSize: '0.74rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            CONCEPTS TRACKED
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--amber)', margin: '8px 0 6px' }}>
            1
          </div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Algebra / Binomials</span>
        </Card>

        <Card accent="coral">
          <div style={{ fontSize: '0.74rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            REPAIRED PATTERNS
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--coral)', margin: '8px 0 6px' }}>
            {attempts.some((a) => a.parent_attempt_id && a.is_correct) ? '1' : '0'}
          </div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Cognitive Flaws Resolved</span>
        </Card>
      </div>

      {/* Concept Relationship Graph */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Conceptual Relationship Architecture
            </h3>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
              Hierarchical mapping of core algebra nodes and their current stability ratings.
            </p>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <StatusBadge label="Mastered (>75%)" variant="lime" />
            <StatusBadge label="Needs Review" variant="amber" />
          </div>
        </div>

        <ConceptGraph
          rootName="Algebra (Mathematics)"
          concepts={[
            { id: '1', name: 'Linear Equations', masteryPct: 91, status: 'mastered' },
            { id: '2', name: 'Quadratic Forms', masteryPct: 64, status: 'review' },
            { id: '3', name: 'Binomial Expansion', masteryPct: 78, status: 'mastered' },
          ]}
        />
      </div>

      {/* Detailed Concept Mastery Table */}
      <div>
        <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
          Concept Diagnostic Stability
        </h3>

        <Card style={{ padding: 0, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', background: 'var(--surface-elevated)', fontFamily: 'var(--font-mono)', fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                <th style={{ padding: '12px 18px' }}>CONCEPT</th>
                <th style={{ padding: '12px 18px' }}>DOMAIN</th>
                <th style={{ padding: '12px 18px' }}>MASTERY</th>
                <th style={{ padding: '12px 18px' }}>STATUS</th>
                <th style={{ padding: '12px 18px', textAlign: 'right' }}>ACTION</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                <td style={{ padding: '14px 18px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  Expanding the Square of a Binomial
                </td>
                <td style={{ padding: '14px 18px', color: 'var(--text-secondary)' }}>
                  Mathematics › Algebra
                </td>
                <td style={{ padding: '14px 18px', width: 200 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <ProgressBar value={78} color="lime" height={5} />
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', color: 'var(--lime)', fontWeight: 700 }}>
                      78%
                    </span>
                  </div>
                </td>
                <td style={{ padding: '14px 18px' }}>
                  <StatusBadge label="In Review" variant="lime" />
                </td>
                <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                  <Link to="/diagnostics">
                    <Button variant="secondary" size="sm">
                      Check Diagnostics →
                    </Button>
                  </Link>
                </td>
              </tr>
            </tbody>
          </table>
        </Card>
      </div>
      </>
      )}
    </AppShell>
  );
};
