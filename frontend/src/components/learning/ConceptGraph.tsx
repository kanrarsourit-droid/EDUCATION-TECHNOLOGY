import React from 'react';

interface ConceptNode {
  id: string;
  name: string;
  masteryPct: number;
  status: 'mastered' | 'review' | 'misconception';
}

interface ConceptGraphProps {
  rootName?: string;
  concepts?: ConceptNode[];
}

export const ConceptGraph: React.FC<ConceptGraphProps> = ({
  rootName = 'Algebra',
  concepts = [
    { id: '1', name: 'Linear Equations', masteryPct: 91, status: 'mastered' },
    { id: '2', name: 'Quadratic Equations', masteryPct: 64, status: 'review' },
    { id: '3', name: 'Binomial Expansion', masteryPct: 78, status: 'mastered' },
  ],
}) => {
  return (
    <div className="concept-graph-container">
      <div className="graph-tree">
        {/* Root Topic Node */}
        <div className="graph-node graph-node-root">
          <div className="graph-node-title">{rootName}</div>
          <span className="badge badge-muted" style={{ fontSize: '0.7rem' }}>Topic Core</span>
        </div>

        {/* Tree Branch Visual Connector */}
        <div style={{ color: 'var(--border-medium)', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', lineHeight: 1 }}>
          │<br />
          ┌─────────┼─────────┐
        </div>

        {/* Child Concept Nodes */}
        <div className="graph-children-row">
          {concepts.map((concept) => {
            const statusClass =
              concept.status === 'mastered'
                ? 'graph-node-mastered'
                : concept.status === 'review'
                ? 'graph-node-review'
                : 'graph-node-misconception';

            const pctClass =
              concept.status === 'mastered'
                ? 'pct-lime'
                : concept.status === 'review'
                ? 'pct-amber'
                : 'pct-coral';

            return (
              <div key={concept.id} className={`graph-node ${statusClass}`}>
                <div className="graph-node-title">{concept.name}</div>
                <div className={`graph-node-pct ${pctClass}`}>{concept.masteryPct}%</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
