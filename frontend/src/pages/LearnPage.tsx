import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/StatusBadge';
import { ProgressBar } from '../components/ui/ProgressBar';
import { PageHeader } from '../components/ui/PageHeader';
import {
  type ConceptItem,
  getConceptsByTopic,
  getSubjects,
  getTopicsBySubject,
  type SubjectItem,
  type TopicItem,
} from '../lib/api';

export const LearnPage: React.FC = () => {
  const [selectedSubject, setSelectedSubject] = useState<SubjectItem | null>(null);
  const [topics, setTopics] = useState<TopicItem[]>([]);
  const [conceptsByTopic, setConceptsByTopic] = useState<Record<string, ConceptItem[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function loadCurriculum() {
      try {
        setLoading(true);
        const subList = await getSubjects();
        if (!mounted) return;

        if (subList.length > 0) {
          const activeSub = subList[0];
          setSelectedSubject(activeSub);

          const topicList = await getTopicsBySubject(activeSub.id);
          if (!mounted) return;
          setTopics(topicList);

          const conceptsMap: Record<string, ConceptItem[]> = {};
          await Promise.all(
            topicList.map(async (topic) => {
              const cList = await getConceptsByTopic(topic.id);
              conceptsMap[topic.id] = cList;
            })
          );

          if (mounted) {
            setConceptsByTopic(conceptsMap);
          }
        }
      } catch (err) {
        console.error('Failed to load curriculum hierarchy:', err);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadCurriculum();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <AppShell breadcrumb="Curriculum Browser › Mathematics">
      <PageHeader
        title="Curriculum Knowledge Browser"
        subtitle="Explore mathematical concept nodes, diagnostic coverage, and cognitive models."
        actions={
          <Link to="/diagnostics">
            <Button variant="primary" size="md">
              Launch Diagnostics ⚡
            </Button>
          </Link>
        }
      />

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
          <div className="spinner-ring" style={{ margin: '0 auto 16px' }} />
          <p>Querying verified curriculum structure from Supabase...</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
          {/* Subject Header Banner */}
          <Card accent="lime">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
              <div>
                <span className="badge badge-lime" style={{ marginBottom: 6 }}>Active Knowledge Domain</span>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {selectedSubject?.name || 'Mathematics'}
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: 4 }}>
                  {selectedSubject?.description || 'Foundational mathematics and algebraic structures.'}
                </p>
              </div>

              <div style={{ display: 'flex', gap: 24, fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
                <div>
                  <div style={{ color: 'var(--text-muted)' }}>TOPICS</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>{topics.length}</div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)' }}>CONCEPTS</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--lime)' }}>
                    {Object.values(conceptsByTopic).reduce((acc, curr) => acc + curr.length, 0)}
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Topics and Concepts List */}
          {topics.map((topic) => {
            const concepts = conceptsByTopic[topic.id] || [];

            return (
              <div key={topic.id} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ fontSize: '0.9rem', color: 'var(--lime)', fontFamily: 'var(--font-mono)' }}>◈ Topic:</span>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {topic.name}
                  </h3>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>— {topic.description}</span>
                </div>

                <div className="grid-cols-2">
                  {concepts.map((concept) => (
                    <Card key={concept.id} interactive>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                        <div>
                          <span style={{ fontSize: '0.74rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                            Concept Unit
                          </span>
                          <h4 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>
                            {concept.name}
                          </h4>
                        </div>
                        <StatusBadge label="Calibrated" variant="lime" />
                      </div>

                      <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 16 }}>
                        {concept.description || 'Deep diagnostic conceptual mastery targeting specific reasoning steps.'}
                      </p>

                      <div style={{ marginBottom: 16 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', fontFamily: 'var(--font-mono)', marginBottom: 6 }}>
                          <span style={{ color: 'var(--text-muted)' }}>Diagnostic Target</span>
                          <span style={{ color: 'var(--lime)', fontWeight: 600 }}>2 Problems Ready</span>
                        </div>
                        <ProgressBar value={78} color="lime" height={5} />
                      </div>

                      <Link to={`/diagnostics?concept_id=${concept.id}`}>
                        <Button variant="primary" size="sm" fullWidth>
                          Start Diagnostic Workspace ⚡
                        </Button>
                      </Link>
                    </Card>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </AppShell>
  );
};
