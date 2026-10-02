import React from 'react';

export type DiagnosticStage = 'question' | 'reasoning' | 'diagnosis' | 'intervention' | 'retry' | 'repaired';

interface DiagnosticTimelineProps {
  currentStage: DiagnosticStage;
}

const STAGES: { key: DiagnosticStage; label: string }[] = [
  { key: 'question', label: 'Question' },
  { key: 'reasoning', label: 'Reasoning' },
  { key: 'diagnosis', label: 'Diagnosis' },
  { key: 'intervention', label: 'Intervention' },
  { key: 'retry', label: 'Retry' },
  { key: 'repaired', label: 'Repaired' },
];

export const DiagnosticTimeline: React.FC<DiagnosticTimelineProps> = ({ currentStage }) => {
  const currentIndex = STAGES.findIndex((s) => s.key === currentStage);

  return (
    <div className="diag-timeline">
      {STAGES.map((s, idx) => {
        const isActive = s.key === currentStage;
        const isPast = idx < currentIndex;

        return (
          <React.Fragment key={s.key}>
            <div className={`diag-node ${isActive ? 'diag-node-active' : ''}`}>
              <span
                className="diag-node-dot"
                style={{
                  backgroundColor: isActive
                    ? 'var(--lime)'
                    : isPast
                    ? 'var(--text-muted)'
                    : 'var(--border-subtle)',
                }}
              />
              <span>{s.label}</span>
            </div>
            {idx < STAGES.length - 1 && <span className="diag-arrow-separator">→</span>}
          </React.Fragment>
        );
      })}
    </div>
  );
};
