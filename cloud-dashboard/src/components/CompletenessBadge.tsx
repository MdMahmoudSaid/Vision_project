import React from 'react';

interface CompletenessBadgeProps {
  status: 'complete' | 'missing_departure' | 'missing_arrival' | 'no_record';
}

export const CompletenessBadge: React.FC<CompletenessBadgeProps> = ({ status }) => {
  let text = '';
  let bgColor = '';
  let color = '';

  switch (status) {
    case 'complete':
      text = 'Complet';
      bgColor = '#d4edda';
      color = '#155724';
      break;
    case 'missing_departure':
      text = 'Départ manquant';
      bgColor = '#fff3cd';
      color = '#856404';
      break;
    case 'missing_arrival':
      text = 'Arrivée manquante';
      bgColor = '#fff3cd';
      color = '#856404';
      break;
    case 'no_record':
      text = 'Aucun enregistrement';
      bgColor = '#f8d7da';
      color = '#721c24';
      break;
  }

  return (
    <span style={{
      padding: '0.25rem 0.5rem',
      borderRadius: '4px',
      fontSize: '0.875rem',
      fontWeight: 'bold',
      backgroundColor: bgColor,
      color: color,
      display: 'inline-block'
    }}>
      {text}
    </span>
  );
};
