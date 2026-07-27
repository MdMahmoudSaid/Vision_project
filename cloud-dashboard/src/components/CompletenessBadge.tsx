import React from 'react';

interface CompletenessBadgeProps {
  status: 'complete' | 'missing_departure' | 'missing_arrival' | 'no_record';
}

const STATUS_META: Record<CompletenessBadgeProps['status'], { text: string; tone: 'go' | 'caution' | 'stop' }> = {
  complete: { text: 'Complet', tone: 'go' },
  missing_departure: { text: 'Départ manquant', tone: 'caution' },
  missing_arrival: { text: 'Arrivée manquante', tone: 'caution' },
  no_record: { text: 'Aucun enregistrement', tone: 'stop' },
};

export const CompletenessBadge: React.FC<CompletenessBadgeProps> = ({ status }) => {
  const meta = STATUS_META[status];
  return <span className={`status-tag status-tag--${meta.tone}`}>{meta.text}</span>;
};
