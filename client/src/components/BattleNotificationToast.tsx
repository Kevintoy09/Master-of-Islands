/**
 * BattleNotificationToast.tsx
 * Toast global pour afficher automatiquement les résultats de bataille
 */
import React, { useEffect, useState } from 'react';
import { useBattleNotifications } from '../hooks/useBattleNotifications';
import { useUser } from '../hooks/useUser';
import BattleResultPopup from '../popups/BattleResultPopup';
import './BattleNotificationToast.css';

const BattleNotificationToast: React.FC = () => {
  const { user } = useUser();
  const {
    notifications,
    unreadCount,
    selectedNotification,
    setSelectedNotification,
    handleMarkNotificationRead
  } = useBattleNotifications(user?.id || undefined);

  const [visibleToast, setVisibleToast] = useState<any>(null);
  const [lastNotifId, setLastNotifId] = useState<string>('');

  // Détecter les nouvelles notifications non lues
  useEffect(() => {
    if (notifications.length === 0 || unreadCount === 0) return;

    // Prendre la plus récente notification non lue
    const latestUnread = notifications.find(n => !n.read);
    
    if (latestUnread && latestUnread.id !== lastNotifId) {
      setLastNotifId(latestUnread.id);
      setVisibleToast(latestUnread);

      // Auto-fermer après 10 secondes
      const timeout = setTimeout(() => {
        setVisibleToast(null);
      }, 10000);

      return () => clearTimeout(timeout);
    }
  }, [notifications, unreadCount, lastNotifId]);

  const handleToastClick = () => {
    if (visibleToast) {
      setSelectedNotification(visibleToast);
      setVisibleToast(null);
    }
  };

  const handleCloseToast = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (visibleToast) {
      handleMarkNotificationRead(visibleToast.id);
      setVisibleToast(null);
    }
  };

  return (
    <>
      {/* Toast notification */}
      {visibleToast && (
        <div className="battle-toast-container">
          <div 
            className={`battle-toast ${visibleToast.type}`}
            onClick={handleToastClick}
          >
            <button 
              className="battle-toast-close" 
              onClick={handleCloseToast}
            >
              ×
            </button>
            
            <div className="battle-toast-icon">
              {visibleToast.type === 'victory' ? '🏆' : '💀'}
            </div>
            
            <div className="battle-toast-content">
              <div className="battle-toast-title">
                {visibleToast.type === 'victory' ? 'VICTOIRE !' : 'DÉFAITE'}
              </div>
              <div className="battle-toast-battle">
                {visibleToast.battleName}
              </div>
              <div className="battle-toast-stats">
                <span>⚔️ {visibleToast.unitsSent} unités</span>
                <span>💀 {visibleToast.casualties} pertes</span>
              </div>
              <div className="battle-toast-action">
                Cliquer pour voir les détails
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Popup détaillé */}
      {selectedNotification && (
        <BattleResultPopup
          notification={selectedNotification}
          onClose={() => setSelectedNotification(null)}
          onMarkRead={handleMarkNotificationRead}
        />
      )}
    </>
  );
};

export default BattleNotificationToast;
