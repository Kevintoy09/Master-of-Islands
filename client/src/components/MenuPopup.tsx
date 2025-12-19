import React from 'react';
import '../styles/menu.css';

interface MenuPopupProps {
  isOpen: boolean;
  onClose: () => void;
  onJournal: () => void;
  onArmy: () => void;
  onResearch: () => void;
  onLeaderboard: () => void;
  onQuests?: () => void;
  onMessage: () => void;
  onSettings?: () => void;
  onLogout: () => void;
  unreadNotifications?: number; // Nombre de notifications non lues
  unreadMessages?: number; // Nombre de messages non lus
  hasChiefHouse?: boolean; // True si la Maison du Chef est construite (slot 17)
}

const MenuPopup: React.FC<MenuPopupProps> = ({
  isOpen,
  onClose,
  onJournal,
  onArmy,
  onResearch,
  onLeaderboard,
  onQuests,
  onMessage,
  onSettings,
  onLogout,
  unreadNotifications = 0,
  unreadMessages = 0,
  hasChiefHouse = false
}) => {
  if (!isOpen) return null;

  return (
    <div className="popup-overlay" onClick={onClose}>
      <div className="popup-base menu-popup" onClick={(e) => e.stopPropagation()}>
        <button className="popup-close-button" onClick={onClose}>×</button>
        
        <div className="popup-content">
          <h3 className="popup-title">Menu Principal</h3>
          
          <div className="menu-buttons">
            <button onClick={onJournal} className="menu-button">
              <span className="menu-icon">📋</span>
              <span>Journal</span>
              {unreadNotifications > 0 && (
                <span className="notification-badge">{unreadNotifications}</span>
              )}
            </button>
            
            <button onClick={onArmy} className="menu-button">
              <span className="menu-icon">⚔️</span>
              <span>Armée</span>
            </button>
            
            <button onClick={onResearch} className="menu-button">
              <span className="menu-icon">🔬</span>
              <span>Recherche</span>
            </button>
            
            <button onClick={onLeaderboard} className="menu-button">
              <span className="menu-icon">🏆</span>
              <span>Statistiques</span>
            </button>
            
            {hasChiefHouse && onQuests && (
              <button onClick={onQuests} className="menu-button">
                <span className="menu-icon">📜</span>
                <span>Quêtes</span>
              </button>
            )}
            
            <button onClick={onMessage} className="menu-button">
              <span className="menu-icon">✉️</span>
              <span>Messages</span>
              {unreadMessages > 0 && (
                <span className="notification-badge">{unreadMessages}</span>
              )}
            </button>
            
            {onSettings && (
              <button onClick={onSettings} className="menu-button">
                <span className="menu-icon">⚙️</span>
                <span>Options du jeu</span>
              </button>
            )}
            
            <button onClick={onLogout} className="menu-button logout-button">
              <span className="menu-icon">🚪</span>
              <span>Déconnexion</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MenuPopup;
