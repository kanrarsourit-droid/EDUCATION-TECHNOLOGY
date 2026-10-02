import React, { useEffect, useState } from 'react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeader } from '../components/ui/PageHeader';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/StatusBadge';
import {
  type AttemptResult,
  type ConceptItem,
  getConceptsByTopic,
  getConceptQuestions,
  getStudentAttempts,
  getSubjects,
  getTopicsBySubject,
  type SafeQuestion,
  submitAttempt,
} from '../lib/api';

export const LearnTestPage: React.FC = () => {
  // Hierarchy loading states
  const [concepts, setConcepts] = useState<ConceptItem[]>([]);
  const [selectedConceptId, setSelectedConceptId] = useState<string>('');
  const [loadingConcepts, setLoadingConcepts] = useState(true);

  // Questions state
  const [questions, setQuestions] = useState<SafeQuestion[]>([]);
  const [activeQuestionIndex, setActiveQuestionIndex] = useState(0);
  const [loadingQuestions, setLoadingQuestions] = useState(false);

  // Attempt form inputs
  const [selectedMcqChoice, setSelectedMcqChoice] = useState<string>('');
  const [openAnswer, setOpenAnswer] = useState<string>('');
  const [reasoning, setReasoning] = useState<string>('');
  const [confidence, setConfidence] = useState<number>(0.8);

  // Retry / attempt tracking
  const [parentAttemptId, setParentAttemptId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<AttemptResult | null>(null);

  // Attempt history for current question
  const [history, setHistory] = useState<AttemptResult[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const activeQuestion: SafeQuestion | undefined = questions[activeQuestionIndex];

  // 1. Fetch Subject -> Topic -> Concepts hierarchy on mount
  useEffect(() => {
    let mounted = true;

    async function loadKnowledgeDomain() {
      try {
        setLoadingConcepts(true);
        const subjects = await getSubjects();
        const mathSubject = subjects.find(
          (s) => s.slug === 'mathematics' || s.name.toLowerCase() === 'mathematics'
        ) || subjects[0];

        if (!mathSubject) {
          throw new Error('No subjects found in the database.');
        }

        const topics = await getTopicsBySubject(mathSubject.id);
        const algebraTopic = topics.find(
          (t) => t.name.toLowerCase() === 'algebra'
        ) || topics[0];

        if (!algebraTopic) {
          throw new Error('No topics found for Mathematics.');
        }

        const conceptList = await getConceptsByTopic(algebraTopic.id);
        if (mounted) {
          setConcepts(conceptList);
          if (conceptList.length > 0) {
            setSelectedConceptId(conceptList[0].id);
          }
        }
      } catch (err: any) {
        console.error('Error loading concepts:', err);
        if (mounted) setSubmitError(err.message || 'Failed to load concept data.');
      } finally {
        if (mounted) setLoadingConcepts(false);
      }
    }

    loadKnowledgeDomain();
    return () => {
      mounted = false;
    };
  }, []);

  // 2. Load questions whenever selected concept changes
  useEffect(() => {
    if (!selectedConceptId) return;

    let mounted = true;
    async function loadQuestions() {
      try {
        setLoadingQuestions(true);
        setSubmitError(null);
        setLastResult(null);
        setParentAttemptId(null);
        setSelectedMcqChoice('');
        setOpenAnswer('');
        setReasoning('');

        const list = await getConceptQuestions(selectedConceptId);
        if (mounted) {
          setQuestions(list);
          setActiveQuestionIndex(0);
        }
      } catch (err: any) {
        console.error('Error loading questions:', err);
        if (mounted) setSubmitError(err.message || 'Failed to load questions.');
      } finally {
        if (mounted) setLoadingQuestions(false);
      }
    }

    loadQuestions();
    return () => {
      mounted = false;
    };
  }, [selectedConceptId]);

  // 3. Load attempt history for the active question
  useEffect(() => {
    if (!activeQuestion) return;
    const questionId = activeQuestion.id;

    let mounted = true;
    async function loadHistory(qId: string) {
      try {
        setLoadingHistory(true);
        const attempts = await getStudentAttempts({ question_id: qId, limit: 10 });
        if (mounted) {
          setHistory(attempts);
        }
      } catch (err) {
        console.error('Error loading attempt history:', err);
      } finally {
        if (mounted) setLoadingHistory(false);
      }
    }

    loadHistory(questionId);
    return () => {
      mounted = false;
    };
  }, [activeQuestion, lastResult]);

  // Handle attempt submission
  const handleSubmitAttempt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeQuestion) return;

    const answerToSubmit =
      activeQuestion.question_type === 'multiple_choice' ? selectedMcqChoice : openAnswer;

    if (!answerToSubmit.trim()) {
      setSubmitError('Please provide an answer before submitting.');
      return;
    }

    setSubmitting(true);
    setSubmitError(null);

    try {
      const result = await submitAttempt({
        question_id: activeQuestion.id,
        student_answer: answerToSubmit.trim(),
        student_reasoning: reasoning.trim() || undefined,
        confidence_score: confidence,
        parent_attempt_id: parentAttemptId || undefined,
      });

      setLastResult(result);
    } catch (err: any) {
      console.error('Submission failed:', err);
      setSubmitError(err.message || 'Failed to submit attempt.');
    } finally {
      setSubmitting(false);
    }
  };

  // Handle "Try Again" retry action
  const handleTryAgain = () => {
    if (!lastResult) return;
    setParentAttemptId(lastResult.id);
    setLastResult(null);
    setSubmitError(null);
  };

  const choices = activeQuestion?.rubric?.choices || activeQuestion?.rubric?.options || [];

  return (
    <AppShell breadcrumb="Diagnostic Practice Screen">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 24, maxWidth: 1200, margin: '0 auto' }}>
        <PageHeader
          badge={<StatusBadge status="accent" label="AUTHENTICATED DIAGNOSTIC API TESTBED" />}
          title="Diagnostic Practice Screen"
          subtitle="Direct interactive testbed for curriculum questions, reasoning verification, and parent-child attempt chaining."
        />

        {/* Concept Selector Header */}
        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
            <div>
              <span className="mono-sub" style={{ display: 'block', marginBottom: 4 }}>
                MATHEMATICS › ALGEBRA
              </span>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                Select Diagnostic Concept
              </h3>
            </div>
            {loadingConcepts ? (
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Loading concepts...</span>
            ) : (
              <select
                className="input-field"
                style={{ width: 'auto', minWidth: 260 }}
                value={selectedConceptId}
                onChange={(e) => setSelectedConceptId(e.target.value)}
              >
                {concepts.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            )}
          </div>
        </Card>

        {loadingQuestions ? (
          <Card>
            <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-secondary)' }}>
              Loading questions for this concept...
            </div>
          </Card>
        ) : questions.length === 0 ? (
          <Card>
            <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-secondary)' }}>
              No questions found for the selected concept.
            </div>
          </Card>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24, alignItems: 'start' }}>
            {/* Question Workspace */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <Card>
                {/* Question Navigation & Metadata */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: 14, borderBottom: '1px solid var(--border-color)', marginBottom: 16 }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--accent-lime)', fontWeight: 600 }}>
                    Question {activeQuestionIndex + 1} of {questions.length}
                  </div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <StatusBadge status="neutral" label={activeQuestion?.difficulty?.toUpperCase() || 'MEDIUM'} />
                    <StatusBadge status="neutral" label={activeQuestion?.question_type || 'MCQ'} />
                    {parentAttemptId && (
                      <StatusBadge status="warning" label="🔄 Retry Chained" />
                    )}
                  </div>
                </div>

                {/* Question Prompt */}
                <div style={{ background: 'var(--bg-secondary)', padding: '20px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', marginBottom: 20 }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
                    {activeQuestion?.title}
                  </h3>
                  <p style={{ fontSize: '1.25rem', color: 'var(--text-primary)', fontWeight: 500, margin: 0, fontFamily: 'var(--font-mono)' }}>
                    {activeQuestion?.prompt}
                  </p>
                </div>

                {submitError && (
                  <div style={{ padding: '12px 16px', background: 'rgba(255, 92, 103, 0.1)', border: '1px solid var(--accent-coral)', borderRadius: 'var(--radius-sm)', color: 'var(--accent-coral)', marginBottom: 16, fontSize: '0.85rem' }}>
                    {submitError}
                  </div>
                )}

                {/* Submitted Attempt Result Banner */}
                {lastResult ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 16, padding: 20, background: 'var(--bg-secondary)', border: `1px solid ${lastResult.is_correct ? 'var(--accent-mint)' : 'var(--accent-coral)'}`, borderRadius: 'var(--radius-sm)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <span style={{ fontSize: '1.6rem' }}>
                        {lastResult.is_correct === true ? '✓' : lastResult.is_correct === false ? '✗' : '●'}
                      </span>
                      <div>
                        <h4 style={{ margin: 0, fontSize: '1.1rem', color: lastResult.is_correct ? 'var(--accent-mint)' : 'var(--accent-coral)' }}>
                          {lastResult.is_correct === true
                            ? 'Correct Response'
                            : lastResult.is_correct === false
                            ? 'Incorrect / Misconception Detected'
                            : 'Attempt Recorded'}
                        </h4>
                        <p style={{ margin: '4px 0 0', fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                          Attempt #{lastResult.attempt_number} recorded in database.
                          {lastResult.parent_attempt_id && (
                            <span style={{ color: 'var(--accent-amber)' }}>
                              {' '}Parent: {lastResult.parent_attempt_id.slice(0, 8)}...
                            </span>
                          )}
                        </p>
                      </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, background: 'var(--bg-elevated)', padding: 14, borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontSize: '0.85rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Submitted Answer:</span>
                        <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)' }}>
                          {lastResult.student_answer}
                        </span>
                      </div>
                      {lastResult.student_reasoning && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                          <span style={{ color: 'var(--text-muted)' }}>Recorded Reasoning:</span>
                          <span style={{ fontStyle: 'italic', color: 'var(--text-secondary)' }}>
                            "{lastResult.student_reasoning}"
                          </span>
                        </div>
                      )}
                      {lastResult.confidence_score !== null && (
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: 'var(--text-muted)' }}>Calibrated Confidence:</span>
                          <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-lime)' }}>
                            {Math.round(lastResult.confidence_score * 100)}%
                          </span>
                        </div>
                      )}
                    </div>

                    <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
                      <Button variant="secondary" onClick={handleTryAgain}>
                        🔄 Try Again (Submit Retry Attempt)
                      </Button>
                      {activeQuestionIndex < questions.length - 1 && (
                        <Button
                          variant="primary"
                          onClick={() => {
                            setActiveQuestionIndex((prev) => prev + 1);
                            setLastResult(null);
                            setParentAttemptId(null);
                            setSelectedMcqChoice('');
                            setOpenAnswer('');
                            setReasoning('');
                          }}
                        >
                          Next Question →
                        </Button>
                      )}
                    </div>
                  </div>
                ) : (
                  /* Question Input Form */
                  <form onSubmit={handleSubmitAttempt} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                    {/* Multiple Choice Options */}
                    {activeQuestion?.question_type === 'multiple_choice' && (
                      <div>
                        <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 10 }}>
                          Select your answer:
                        </label>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
                          {choices.map((choice: any, idx: number) => {
                            const val = choice.label || choice.text || String(idx);
                            const isSelected = selectedMcqChoice === val;
                            return (
                              <button
                                type="button"
                                key={idx}
                                onClick={() => setSelectedMcqChoice(val)}
                                style={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: 12,
                                  padding: '12px 16px',
                                  background: isSelected ? 'var(--bg-elevated)' : 'var(--bg-secondary)',
                                  border: `1px solid ${isSelected ? 'var(--accent-lime)' : 'var(--border-color)'}`,
                                  borderRadius: 'var(--radius-sm)',
                                  color: 'var(--text-primary)',
                                  cursor: 'pointer',
                                  textAlign: 'left',
                                  transition: 'all 0.15s ease',
                                }}
                              >
                                <span
                                  style={{
                                    fontFamily: 'var(--font-mono)',
                                    fontWeight: 700,
                                    fontSize: '0.8rem',
                                    width: 24,
                                    height: 24,
                                    borderRadius: 4,
                                    background: isSelected ? 'var(--accent-lime)' : 'var(--border-color)',
                                    color: isSelected ? '#080A0D' : 'var(--text-secondary)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                  }}
                                >
                                  {choice.label || idx + 1}
                                </span>
                                <span style={{ fontSize: '0.95rem', fontFamily: 'var(--font-mono)' }}>{choice.text}</span>
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Open Response Input */}
                    {activeQuestion?.question_type === 'open_response' && (
                      <div>
                        <label htmlFor="open-answer" style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>
                          Your Answer:
                        </label>
                        <textarea
                          id="open-answer"
                          rows={3}
                          className="input-field"
                          value={openAnswer}
                          onChange={(e) => setOpenAnswer(e.target.value)}
                          placeholder="Write your algebraic expansion or final answer here..."
                          required
                        />
                      </div>
                    )}

                    {/* Student Reasoning Input */}
                    <div>
                      <label htmlFor="reasoning" style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>
                        Explain how you arrived at your answer:
                      </label>
                      <textarea
                        id="reasoning"
                        rows={3}
                        className="input-field"
                        value={reasoning}
                        onChange={(e) => setReasoning(e.target.value)}
                        placeholder="Explain your thinking step-by-step..."
                      />
                    </div>

                    {/* Confidence Slider */}
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                        <label htmlFor="confidence" style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                          Confidence Calibration:
                        </label>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--accent-lime)', fontWeight: 600 }}>
                          {Math.round(confidence * 100)}%
                        </span>
                      </div>
                      <input
                        id="confidence"
                        type="range"
                        min="0.0"
                        max="1.0"
                        step="0.05"
                        value={confidence}
                        onChange={(e) => setConfidence(parseFloat(e.target.value))}
                        style={{ width: '100%', accentColor: 'var(--accent-lime)', cursor: 'pointer' }}
                      />
                    </div>

                    {/* Submit Button */}
                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 12 }}>
                      <Button
                        type="submit"
                        variant="primary"
                        loading={submitting}
                        disabled={submitting}
                      >
                        {parentAttemptId ? 'Submit Retry Attempt' : 'Submit Attempt'}
                      </Button>
                    </div>
                  </form>
                )}
              </Card>
            </div>

            {/* Sidebar: Attempt History for this Question */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <Card title="Past Attempts">
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: -6, marginBottom: 16 }}>
                  Submissions recorded on this question:
                </p>

                {loadingHistory ? (
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Loading history...</div>
                ) : history.length === 0 ? (
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No previous attempts recorded yet.</div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {history.map((att) => (
                      <div
                        key={att.id}
                        style={{
                          padding: 12,
                          background: 'var(--bg-secondary)',
                          border: '1px solid var(--border-color)',
                          borderRadius: 'var(--radius-sm)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 6,
                          fontSize: '0.82rem',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-secondary)' }}>
                            Attempt #{att.attempt_number}
                          </span>
                          <StatusBadge
                            status={att.is_correct === true ? 'success' : att.is_correct === false ? 'error' : 'neutral'}
                            label={att.is_correct === true ? 'Correct' : att.is_correct === false ? 'Incorrect' : 'Submitted'}
                          />
                        </div>
                        <div style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                          <strong>Ans:</strong> {att.student_answer}
                        </div>
                        {att.student_reasoning && (
                          <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
                            "{att.student_reasoning}"
                          </div>
                        )}
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                          {new Date(att.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
};
