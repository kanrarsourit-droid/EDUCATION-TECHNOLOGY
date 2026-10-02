import React from 'react';

interface ProgressBarProps {
  value: number; // 0 to 100
  color?: 'lime' | 'amber' | 'coral' | 'mint';
  height?: number;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  color = 'lime',
  height = 6,
  className = '',
}) => {
  const clampedValue = Math.min(Math.max(value, 0), 100);
  const colorClass = `progress-fill-${color}`;

  return (
    <div
      className={`progress-track ${className}`.trim()}
      style={{ height }}
      role="progressbar"
      aria-valuenow={clampedValue}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        className={`progress-fill ${colorClass}`}
        style={{ width: `${clampedValue}%` }}
      />
    </div>
  );
};
