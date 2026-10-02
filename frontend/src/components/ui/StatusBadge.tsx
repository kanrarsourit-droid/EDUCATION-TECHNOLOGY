import React from 'react';

export type BadgeTone = 'lime' | 'amber' | 'coral' | 'mint' | 'muted' | 'success' | 'warning' | 'error' | 'neutral' | 'accent';

export interface StatusBadgeProps {
  label: string;
  variant?: BadgeTone;
  status?: BadgeTone;
  withDot?: boolean;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  label,
  variant,
  status,
  withDot = true,
  className = '',
}) => {
  const rawTone = status || variant || 'lime';
  
  let mappedVariant = 'lime';
  if (rawTone === 'success' || rawTone === 'mint') mappedVariant = 'mint';
  else if (rawTone === 'warning' || rawTone === 'amber') mappedVariant = 'amber';
  else if (rawTone === 'error' || rawTone === 'coral') mappedVariant = 'coral';
  else if (rawTone === 'neutral' || rawTone === 'muted') mappedVariant = 'muted';
  else mappedVariant = 'lime';

  return (
    <span className={`badge badge-${mappedVariant} ${className}`.trim()}>
      {withDot && <span className="badge-dot" />}
      {label}
    </span>
  );
};
