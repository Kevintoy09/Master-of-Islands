import React from 'react';
import styles from './ConstructionTimer.module.css';
import { formatDetailedTime } from '../utils/timeUtils';

interface ConstructionTimerProps {
  timeRemaining: number; // en secondes
  showInstantFinish?: boolean;
  onInstantFinish?: () => void;
}

const ConstructionTimer: React.FC<ConstructionTimerProps> = ({
  timeRemaining,
  showInstantFinish = false,
  onInstantFinish
}) => {


  const timeFormatted = formatDetailedTime(Math.max(0, timeRemaining));
  const isUrgent = timeRemaining <= 60; // Moins d'une minute
  const isCritical = timeRemaining <= 10; // Moins de 10 secondes

  return (
    <div className={styles.timerContainer}>
      <div 
        className={`${styles.timer} ${isUrgent ? styles.urgent : ''} ${isCritical ? styles.critical : ''}`}
      >
        <div className={styles.timerIcon}>🕐</div>
        <div className={styles.timerText}>
          {timeFormatted.display}
        </div>
        {showInstantFinish && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onInstantFinish?.();
            }}
            className={styles.instantButton}
            title="Terminer instantanément la construction"
          >
            ⚡
          </button>
        )}
      </div>
    </div>
  );
};

export default ConstructionTimer;
