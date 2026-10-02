import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  accent?: 'lime' | 'amber' | 'coral' | 'mint';
  elevated?: boolean;
  interactive?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  accent,
  elevated = false,
  interactive = false,
  className = '',
  ...props
}) => {
  const accentClass = accent ? `card-accent-${accent}` : '';
  const elevatedClass = elevated ? 'card-elevated' : '';
  const interactiveClass = interactive ? 'card-interactive' : '';

  return (
    <div
      className={`card ${accentClass} ${elevatedClass} ${interactiveClass} ${className}`.trim()}
      {...props}
    >
      {children}
    </div>
  );
};
