/**
 * useBattleNotifications.ts
 * Hook personnalisé pour gérer les notifications de bataille
 */
import { useState, useEffect, useCallback } from 'react';

export interface BattleNotification {
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
  read: boolean;
}

export const useBattleNotifications = (playerId: string | undefined) => {
  const [notifications, setNotifications] = useState<BattleNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const [selectedNotification, setSelectedNotification] = useState<BattleNotification | null>(null);

  // Polling des notifications toutes les 30 secondes
  useEffect(() => {
    if (!playerId) return;

    const fetchNotifications = async () => {
      try {
        const response = await fetch(`/api/battles/notifications/${playerId}`);
        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            setNotifications(data.notifications || []);
            setUnreadCount(data.unread_count || 0);
          }
        }
      } catch (error) {
        // Erreur silencieuse - normal si pas de notifications
      }
    };

    // Charger immédiatement
    fetchNotifications();

    // Puis toutes les 30 secondes
    const interval = setInterval(fetchNotifications, 30000);

    return () => clearInterval(interval);
  }, [playerId]);

  // Marquer une notification comme lue
  const handleMarkNotificationRead = useCallback(async (notificationId: string) => {
    if (!playerId) return;

    try {
      const response = await fetch('/api/battles/notifications/mark-read', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          playerId: playerId,
          notificationIds: [notificationId]
        })
      });

      if (response.ok) {
        // Mettre à jour localement
        setNotifications(prev => 
          prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
        );
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error('Erreur marquage notification:', error);
    }
  }, [playerId]);

  return {
    notifications,
    unreadCount,
    showNotifications,
    setShowNotifications,
    selectedNotification,
    setSelectedNotification,
    handleMarkNotificationRead
  };
};
