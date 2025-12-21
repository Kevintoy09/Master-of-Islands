import React, { useState, useEffect } from 'react';
import { useUser } from '../hooks/useUser';
import { getUIEmoji } from '../constants/resourceIcons';
import './NotificationJournalPopup.css';

interface Notification {
  date: string;
  type: string;
  detail: string;
}

interface NotificationJournalPopupProps {
  isOpen: boolean;
  onClose: () => void;
}

const NotificationJournalPopup: React.FC<NotificationJournalPopupProps> = ({ isOpen, onClose }) => {
  const { user } = useUser();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (isOpen) {
      loadNotifications();
    }
  }, [user?.id, isOpen]);

  const loadNotifications = async () => {
    if (!user?.id) return;
    
    try {
      setLoading(true);
      const response = await fetch(`/api/notifications/player/${user.id}`);
      
      if (response.ok) {
        const data = await response.json();
        setNotifications(data.notifications || []);
      } else {
        setError('Erreur lors du chargement des notifications');
      }
    } catch (err) {
      setError('Erreur de connexion');
      console.error('Erreur notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async () => {
    if (!user?.id) return;
    
    try {
      await fetch(`/api/notifications/player/${user.id}/mark-read`, {
        method: 'POST'
      });
      
      // Recharger les notifications pour mettre à jour l'affichage
      await loadNotifications();
      
      // Déclencher une mise à jour des badges de notification
      window.dispatchEvent(new CustomEvent('notificationsRead'));
    } catch (err) {
      console.error('Erreur marquage lu:', err);
    }
  };

  const handleClose = () => {
    markAsRead();
    onClose();
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'transport': return getUIEmoji('ship');
      case 'batiment': return getUIEmoji('building');
      case 'recherche': return getUIEmoji('research');
      case 'attaque': return getUIEmoji('military');
      case 'message': return getUIEmoji('message');
      default: return getUIEmoji('general');
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'transport': return 'Transport';
      case 'batiment': return 'Bâtiment';
      case 'recherche': return 'Recherche';
      case 'attaque': return 'Attaque';
      case 'message': return 'Message';
      default: return 'Notification';
    }
  };

  return (
    <>
      {isOpen && (
        <div className="popup-overlay" onClick={handleClose}>
          <div className="notification-journal-popup" onClick={e => e.stopPropagation()}>
            <div className="popup-header">
              <h2 className="popup-title">
                📋 Journal des notifications
              </h2>
              <button className="popup-close-button" onClick={handleClose}>
                ×
              </button>
            </div>

            <div className="popup-content">
              {loading && (
                <div className="loading-message">
                  Chargement des notifications...
                </div>
              )}

              {error && (
                <div className="error-message">
                  {error}
                </div>
              )}

              {!loading && !error && notifications.length === 0 && (
                <div className="empty-message">
                  <div className="empty-icon">📭</div>
                  <p>Aucune notification pour le moment</p>
                </div>
              )}

              {!loading && !error && notifications.length > 0 && (
                <div className="notifications-table">
                  <div className="table-header">
                    <div className="col-date">Date</div>
                    <div className="col-type">Type</div>
                    <div className="col-detail">Détail</div>
                  </div>
                  
                  <div className="table-body">
                    {notifications.map((notification, index) => {
                      // Séparer la date et l'heure
                      const dateParts = notification.date.split(' à ');
                      const dateOnly = dateParts[0]; // Ex: "21/12/2025"
                      const timeOnly = dateParts[1] || ''; // Ex: "10h00"
                      
                      return (
                      <div key={index} className="table-row">
                        <div className="col-date">
                          <div className="date-line">{dateOnly}</div>
                          <div className="time-line">{timeOnly}</div>
                        </div>
                        <div className="col-type">
                          <span className="type-badge">
                            <span className="type-icon">
                              {getTypeIcon(notification.type)}
                            </span>
                            <span className="type-label">
                              {getTypeLabel(notification.type)}
                            </span>
                          </span>
                        </div>
                        <div className="col-detail">
                          {notification.detail}
                        </div>
                      </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            <div className="popup-footer">
              <button className="btn-secondary" onClick={handleClose}>
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default NotificationJournalPopup;
