/**
 * BattleResultPopup.tsx
 * Popup d'affichage des résultats de bataille
 */
import React, { useEffect } from 'react';
import './BattleResultPopup.css';

interface BattleNotification {
  id: string;
  battleId: string;
  playerId: string;
  type: 'victory' | 'defeat';
  timestamp: number;
  battleName: string;
  winnerTeam: string;
  victoryType: string;
  playerTeam: string;
  unitsSent: number;
  casualties: number;
  pillage?: { [resource: string]: number };
  read: boolean;
}

interface BattleResultPopupProps {
  notification: BattleNotification;
  onClose: () => void;
  onMarkRead: (notificationId: string) => void;
}

const BattleResultPopup: React.FC<BattleResultPopupProps> = ({ notification, onClose, onMarkRead }) => {
  const isVictory = notification.type === 'victory';
  
  // 🔒 Empêcher le scroll du background sur mobile
  useEffect(() => {
    const preventScroll = (e: TouchEvent) => {
      if (e.target === document.body || !(e.target as HTMLElement).closest('.battle-result-popup')) {
        e.preventDefault();
      }
    };

    document.addEventListener('touchmove', preventScroll, { passive: false });
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('touchmove', preventScroll);
      document.body.style.overflow = '';
    };
  }, []);
  
  const handleClose = () => {
    // Marquer comme lu avant de fermer
    if (!notification.read) {
      onMarkRead(notification.id);
    }
    onClose();
  };

  const getVictoryTypeText = (type: string): string => {
    switch (type) {
      case 'elimination':
        return 'Élimination complète';
      case 'moral_breakdown':
        return 'Effondrement du moral';
      case 'surrender':
        return 'Abandon';
      default:
        return type;
    }
  };

  const survivalRate = notification.unitsSent > 0
    ? ((notification.unitsSent - notification.casualties) / notification.unitsSent * 100).toFixed(0)
    : '0';

  return (
    <div className="battle-result-overlay" onClick={handleClose}>
      <div 
        className="battle-result-popup" 
        onClick={(e) => e.stopPropagation()}
        style={{
          maxHeight: 'calc(100vh - 120px)',
          overflowY: 'auto'
        }}
      >
        {/* En-tête */}
        <div className={`battle-result-header ${isVictory ? 'victory' : 'defeat'}`}>
          <div className="battle-result-icon">
            {isVictory ? '🏆' : '💀'}
          </div>
          <div className="battle-result-title">
            <h2>{isVictory ? 'VICTOIRE' : 'DÉFAITE'}</h2>
            <div className="battle-result-name">{notification.battleName}</div>
          </div>
          <button className="battle-result-close" onClick={handleClose}>×</button>
        </div>

        {/* Corps */}
        <div className="battle-result-body">
          {/* Type de victoire */}
          <div className="battle-result-section">
            <div className="battle-result-label">Type de victoire</div>
            <div className="battle-result-value">{getVictoryTypeText(notification.victoryType)}</div>
          </div>

          {/* Équipe gagnante */}
          <div className="battle-result-section">
            <div className="battle-result-label">Vainqueur</div>
            <div className="battle-result-value">
              {notification.winnerTeam === 'attackers' ? '⚔️ Attaquants' : '🛡️ Défenseurs'}
            </div>
          </div>

          {/* Statistiques */}
          <div className="battle-result-stats">
            <div className="battle-stat-card">
              <div className="battle-stat-label">Unités envoyées</div>
              <div className="battle-stat-value">{notification.unitsSent}</div>
            </div>
            <div className="battle-stat-card casualties">
              <div className="battle-stat-label">Pertes</div>
              <div className="battle-stat-value">{notification.casualties}</div>
            </div>
            <div className="battle-stat-card survival">
              <div className="battle-stat-label">Taux de survie</div>
              <div className="battle-stat-value">{survivalRate}%</div>
            </div>
          </div>

          {/* Pillage (si victoire) */}
          {isVictory && notification.pillage && Object.keys(notification.pillage).length > 0 && (
            <div className="battle-result-section pillage-section">
              <div className="battle-result-label">💰 Butin pillé</div>
              <div className="battle-pillage-list">
                {Object.entries(notification.pillage).map(([resource, amount]) => (
                  <div key={resource} className="pillage-item">
                    <span className="pillage-resource">{resource}</span>
                    <span className="pillage-amount">+{amount}</span>
                  </div>
                ))}
              </div>
              <div className="pillage-total">
                Total : {Object.values(notification.pillage).reduce((sum, val) => sum + val, 0)} ressources
              </div>
            </div>
          )}

          {/* Date */}
          <div className="battle-result-timestamp">
            {new Date(notification.timestamp).toLocaleString('fr-FR')}
          </div>
        </div>

        {/* Pied */}
        <div className="battle-result-footer">
          <button className="battle-result-btn" onClick={handleClose}>
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
};

export default BattleResultPopup;
