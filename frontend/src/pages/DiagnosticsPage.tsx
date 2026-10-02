import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/StatusBadge';
import { PageHeader } from '../components/ui/PageHeader';
import { DiagnosticTimeline, type DiagnosticStage } from '../components/learning/DiagnosticTimeline';
import {
  type AttemptResult,
  type ConceptItem,
  getConceptsByTopic,
  getConceptQuestions,
  getSubjects,
  getTopicsBySubject,
  type SafeQuestion,
  submitAttempt,
} from '../lib/api';

export const DiagnosticsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const requestedConceptId = searchParams.get('concept_id');

  // Curriculum data
  const [concepts, setConcepts] = useState<ConceptItem[]>([]);
  const [selectedConceptId, setSelectedConceptId] = useState<string>('');
  const [questions, setQuestions] = useState<SafeQuestion[]>([]);
  const [activeQuestionIndex, setActiveQuestionIndex] = useState(0);

  // Attempt inputs
  const [selectedChoice, setSelectedChoice] = useState<string>('');
  const [openResponseText, setOpenResponseText] = useState<string>('');
  const [reasoning, setReasoning] = useState<string>('');
  const [confidenceLevel, setConfidenceLevel] = useState<'low' | 'medium' | 'high'>('medium');

  // Lifecycle states
  const [loading, setLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [lastResult, setLastResult] = useState<AttemptResult | null>(null);
  const [parentAttemptId, setParentAttemptId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const activeQuestion: SafeQuestion | undefined = questions[activeQuestionIndex];

  // 1. Load concepts
  useEffect(() => {
    let mounted = true;
    async function initWorkspace() {
      try {
        setLoading(true);
        const subjects = await getSubjects();
        if (!mounted || subjects.length === 0) return;

        const math = subjects[0];
        const topics = await getTopicsBySubject(math.id);
        if (!mounted || topics.length === 0) return;

        const conceptList = await getConceptsByTopic(topics[0].id);
        if (mounted) {
          setConcepts(conceptList);
          const initialId =
            requestedConceptId && conceptList.some((c) => c.id === requestedConceptId)
              ? requestedConceptId
              : conceptList[0]?.id || '';
          setSelectedConceptId(initialId);
        }
      } catch (err) {
        console.error('Failed to initialize diagnostic workspace:', err);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    initWorkspace();
    return () => {
      mounted = false;
    };
  }, [requestedConceptId]);

  // 2. Load questions for selected concept
  useEffect(() => {
    if (!selectedConceptId) return;
    let mounted = true;

    async function loadQuestions() {
      try {
        setLoading(true);
        setLastResult(null);
        setParentAttemptId(null);
        setSelectedChoice('');
        setOpenResponseText('');
        setReasoning('');
        setErrorMsg(null);

        const qList = await getConceptQuestions(selectedConceptId);
        if (mounted) {
          setQuestions(qList);
          setActiveQuestionIndex(0);
        }
      } catch (err: any) {
        console.error('Failed to load questions:', err);
        if (mounted) setErrorMsg(err.message || 'Could not load diagnostic questions.');
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadQuestions();
    return () => {
      mounted = false;
    };
  }, [selectedConceptId]);

  // Confidence mapping
  const confidenceScore = confidenceLevel === 'low' ? 0.33 : confidenceLevel === 'medium' ? 0.66 : 1.0;

  // Handle diagnostic submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeQuestion) return;

    const answer =
      activeQuestion.question_type === 'multiple_choice' ? selectedChoice : openResponseText;

    if (!answer.trim()) {
      setErrorMsg('Please select or provide an answer before submitting.');
      return;
    }

    setErrorMsg(null);
    setIsAnalyzing(true);

    try {
      // Simulate restrained analysis transition
      await new Promise((res) => setTimeout(res, 600));

      const result = await submitAttempt({
        question_id: activeQuestion.id,
        student_answer: answer.trim(),
        student_reasoning: reasoning.trim() || undefined,
        confidence_score: confidenceScore,
        parent_attempt_id: parentAttemptId || undefined,
      });

      setLastResult(result);
    } catch (err: any) {
      console.error('Diagnostic submission failed:', err);
      setErrorMsg(err.message || 'Failed to record diagnostic attempt.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Handle retry
  const handleTryAgain = () => {
    if (!lastResult) return;
    setParentAttemptId(lastResult.id);
    setLastResult(null);
    setErrorMsg(null);
  };

  // Determine current timeline stage
  const getTimelineStage = (): DiagnosticStage => {
    if (!lastResult) {
      return reasoning ? 'reasoning' : 'question';
    }
    if (lastResult.is_correct === true) {
      return parentAttemptId ? 'repaired' : 'diagnosis';
    }
    return parentAttemptId ? 'retry' : 'intervention';
  };

  const choices = activeQuestion?.rubric?.choices || activeQuestion?.rubric?.options || [];

  return (
    <AppShell breadcrumb="Mathematics › Algebra › Expanding the Square of a Binomial">
      <PageHeader
        title="Scientific Diagnostic Workspace"
        subtitle="Analyze intermediate reasoning steps, identify conceptual flaws, and verify cognitive repair."
        actions={
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              CONCEPT:
            </span>
            <select
              className="select"
              style={{ width: 'auto', padding: '6px 12px', fontSize: '0.85rem' }}
              value={selectedConceptId}
              onChange={(e) => setSelectedConceptId(e.target.value)}
            >
              {concepts.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        }
      />

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
          <div className="spinner-ring" style={{ margin: '0 auto 16px' }} />
          <p>Loading diagnostic items...</p>
        </div>
      ) : !activeQuestion ? (
        <Card>
          <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No questions available for this concept.</p>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Main 2-Column Reasoning Workspace */}
          <div className="diagnostic-workspace-grid">
            {/* LEFT: QUESTION PANEL */}
            <Card className="question-panel" accent="lime">
              <div className="question-header-row">
                <span className="step-indicator">
                  {String(activeQuestionIndex + 1).padStart(2, '0')} / {String(questions.length).padStart(2, '0')}
                </span>
                <div style={{ display: 'flex', gap: 8 }}>
                  <StatusBadge label={activeQuestion.difficulty} variant="mint" />
                  <StatusBadge label={activeQuestion.question_type} variant="muted" />
                  {parentAttemptId && <StatusBadge label="Retry Chain" variant="amber" />}
                </div>
              </div>

              <div>
                <span style={{ fontSize: '0.74rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  DIAGNOSTIC TARGET
                </span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>
                  {activeQuestion.title}
                </h3>
              </div>

              {/* Prompt Box */}
              <div className="prompt-display-card">
                <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--lime)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  PROMPT
                </span>
                <div className="prompt-expression">{activeQuestion.prompt}</div>
              </div>

              {/* MCQ Options Selector */}
              {activeQuestion.question_type === 'multiple_choice' ? (
                <div>
                  <span className="form-label" style={{ marginBottom: 8 }}>Select candidate answer:</span>
                  <div className="mcq-choice-grid">
                    {choices.map((c, idx) => {
                      const val = c.label || c.text || String(idx);
                      const isSelected = selectedChoice === val;
                      return (
                        <div
                          key={idx}
                          className={`mcq-card-option ${isSelected ? 'selected' : ''}`}
                          onClick={() => !lastResult && setSelectedChoice(val)}
                        >
                          <span className="choice-key">{c.label || idx + 1}</span>
                          <span className="choice-label-text">{c.text}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="form-group">
                  <label className="form-label" htmlFor="formula-answer">Your algebraic expression:</label>
                  <input
                    id="formula-answer"
                    type="text"
                    className="input"
                    value={openResponseText}
                    onChange={(e) => setOpenResponseText(e.target.value)}
                    placeholder="e.g. x^2 + 6x + 9"
                    disabled={!!lastResult}
                  />
                </div>
              )}
            </Card>

            {/* RIGHT: REASONING & DIAGNOSIS PANEL */}
            <Card className="reasoning-panel" elevated>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--lime)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                  COGNITIVE REASONING LAYER
                </span>
                <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                  ATTEMPT #{lastResult ? lastResult.attempt_number : parentAttemptId ? '2' : '1'}
                </span>
              </div>

              {/* Restrained Analyzing State */}
              {isAnalyzing ? (
                <div className="analysis-animation-card">
                  <div className="analysis-spinner-row">
                    <span className="analysis-indicator" />
                    <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      ANALYZING REASONING PATH
                    </h4>
                  </div>
                  <ul className="analysis-checklist">
                    <li><span>✓</span> parsing mathematical structure</li>
                    <li><span>✓</span> evaluating applied transformation rules</li>
                    <li><span>✓</span> checking intermediate cross-term reasoning</li>
                    <li><span>✓</span> verifying conceptual consistency</li>
                  </ul>
                </div>
              ) : lastResult ? (
                /* Diagnostic Result & Targeted Intervention */
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  {lastResult.is_correct === true ? (
                    <div className="card card-accent-mint" style={{ background: 'var(--surface-elevated)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                        <span style={{ fontSize: '1.25rem' }}>✓</span>
                        <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--mint)' }}>
                          CONCEPT VALIDATED
                        </h4>
                      </div>
                      <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                        Your reasoning and expansion correctly applied the binomial theorem and preserved the essential <code style={{ color: 'var(--mint)', background: 'var(--mint-bg)', padding: '1px 5px', borderRadius: 4 }}>2ab</code> cross term.
                      </p>
                    </div>
                  ) : lastResult.is_correct === false ? (
                    <div className="intervention-card">
                      <div className="intervention-header">
                        <StatusBadge label="MISCONCEPTION DETECTED" variant="coral" />
                        <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--coral)' }}>
                          Missing Cross-Term Error
                        </h4>
                      </div>
                      <p style={{ fontSize: '0.88rem', color: 'var(--text-primary)', lineHeight: 1.5 }}>
                        You correctly squared each individual term, but treated <code style={{ color: 'var(--coral)' }}>(a + b)²</code> as <code style={{ color: 'var(--coral)' }}>a² + b²</code> without accounting for the cross terms.
                      </p>

                      {/* Interactive Educational Counter-Example Intervention */}
                      <div className="intervention-test-box">
                        <div style={{ color: 'var(--amber)', fontWeight: 600, marginBottom: 6 }}>
                          LET&apos;S TEST YOUR IDEA WITH NUMBERS:
                        </div>
                        <div>(2 + 3)² = ?</div>
                        <div style={{ color: 'var(--text-muted)', marginTop: 4 }}>
                          Applying your rule produces: 2² + 3² = 4 + 9 = <strong>13</strong>
                        </div>
                        <div style={{ color: 'var(--lime)', marginTop: 4 }}>
                          Actual calculation: (5)² = <strong>25</strong>
                        </div>
                        <div style={{ marginTop: 8, fontStyle: 'italic', color: 'var(--text-secondary)' }}>
                          Notice the discrepancy (25 - 13 = 12). Where did the 2 × (2 × 3) cross term go?
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="card" style={{ background: 'var(--surface-elevated)' }}>
                      <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
                        Diagnostic Submission Recorded
                      </h4>
                      <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)' }}>
                        Attempt #{lastResult.attempt_number} has been safely logged in your longitudinal ledger.
                      </p>
                    </div>
                  )}

                  {/* Actions post submission */}
                  <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
                    <Button variant="secondary" size="md" fullWidth onClick={handleTryAgain}>
                      🔄 Try Again (Submit Retry)
                    </Button>
                    {activeQuestionIndex < questions.length - 1 && (
                      <Button
                        variant="primary"
                        size="md"
                        fullWidth
                        onClick={() => {
                          setActiveQuestionIndex((prev) => prev + 1);
                          setLastResult(null);
                          setParentAttemptId(null);
                          setSelectedChoice('');
                          setOpenResponseText('');
                          setReasoning('');
                        }}
                      >
                        Next Diagnostic →
                      </Button>
                    )}
                  </div>
                </div>
              ) : (
                /* Primary Diagnostic Form */
                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                  <div className="form-group">
                    <label htmlFor="reasoning-text" className="form-label">
                      <span>Explain your step-by-step thinking:</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Why did you choose this?</span>
                    </label>
                    <textarea
                      id="reasoning-text"
                      className="textarea"
                      rows={4}
                      value={reasoning}
                      onChange={(e) => setReasoning(e.target.value)}
                      placeholder="I believe the middle term is generated by multiplying the two terms because..."
                    />
                  </div>

                  {/* Discrete Confidence Selector */}
                  <div>
                    <label className="form-label" style={{ marginBottom: 8 }}>
                      <span>Confidence Level:</span>
                      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--lime)' }}>
                        {confidenceLevel.toUpperCase()}
                      </span>
                    </label>
                    <div className="confidence-selector">
                      <button
                        type="button"
                        className={`confidence-tab tab-low ${confidenceLevel === 'low' ? 'active' : ''}`}
                        onClick={() => setConfidenceLevel('low')}
                      >
                        Low (Exploring)
                      </button>
                      <button
                        type="button"
                        className={`confidence-tab tab-medium ${confidenceLevel === 'medium' ? 'active' : ''}`}
                        onClick={() => setConfidenceLevel('medium')}
                      >
                        Medium (Fairly Sure)
                      </button>
                      <button
                        type="button"
                        className={`confidence-tab tab-high ${confidenceLevel === 'high' ? 'active' : ''}`}
                        onClick={() => setConfidenceLevel('high')}
                      >
                        High (Certain)
                      </button>
                    </div>
                  </div>

                  {errorMsg && <div className="alert alert-error">{errorMsg}</div>}

                  <Button type="submit" variant="primary" size="lg" fullWidth>
                    {parentAttemptId ? 'Submit Retry Attempt ⚡' : 'Submit Diagnostic Attempt ⚡'}
                  </Button>
                </form>
              )}
            </Card>
          </div>

          {/* Diagnostic Timeline */}
          <div style={{ marginTop: 8 }}>
            <div style={{ fontSize: '0.74rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              DIAGNOSTIC REPAIR PIPELINE
            </div>
            <DiagnosticTimeline currentStage={getTimelineStage()} />
          </div>
        </div>
      )}
    </AppShell>
  );
};
