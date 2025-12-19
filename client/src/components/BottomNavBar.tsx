import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import MenuPopup from './MenuPopup';
import NotificationJournalPopup from './NotificationJournalPopup';
import ProfilePopup from '../popups/ProfilePopup';
import SettingsPopup from '../popups/SettingsPopup';
import MessagesPopup from './MessagesPopup';
import { useUser } from '../hooks/useUser';
import { useMusicPlayer } from '../hooks/useMusicPlayer';
import { getApiUrl } from '../utils/api';
import './BottomNavBar.css';


interface BottomNavBarProps {
  activeCityId: string;
  activeIslandId: string;
  playerResources?: {
    gold?: number;
    research_points?: number;
    transport_ships?: number;
    diamonds?: number;
  };
  playerInfo?: {
    transport_ships_total?: number;
    transport_ships_available?: number;
  };
}

const BottomNavBar: React.FC<BottomNavBarProps> = ({ 
  activeCityId, 
  activeIslandId, 
  playerResources, 
  playerInfo 
}) => {
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isNotificationJournalOpen, setIsNotificationJournalOpen] = useState(false);
  const [isProfilePopupOpen, setIsProfilePopupOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isMessagesOpen, setIsMessagesOpen] = useState(false);
  const [unreadNotifications, setUnreadNotifications] = useState(0);
  const [unreadMessages, setUnreadMessages] = useState(0);
  const [hasChiefHouse, setHasChiefHouse] = useState(false); // Maison du Chef dans slot 17
  const [hasUnclaimedQuestRewards, setHasUnclaimedQuestRewards] = useState(false);
  const { user, logout } = useUser();
  const { isMuted, toggleMute } = useMusicPlayer();

  // Vérifier si le joueur a la Maison du Chef de Village dans le slot 17
  useEffect(() => {
    const checkChiefHouse = async () => {
      if (user?.id && activeCityId) {
        try {
          const response = await fetch(`/api/city/${activeCityId}/state`);
          if (response.ok) {
            const data = await response.json();
            
            // Chercher dans le tableau buildings
            const buildings = data.buildings || [];
            const chiefHouse = buildings.find((b: any) => b.slot_id === 'slot_17');
            
            const hasChief = chiefHouse?.name === 'Maison du Chef de Village' && chiefHouse?.level >= 1;
            setHasChiefHouse(hasChief);
          }
        } catch (error) {
          console.error('Erreur lors de la vérification de la Maison du Chef:', error);
        }
      }
    };

    checkChiefHouse();
  }, [user?.id, activeCityId]);

  // Charger le nombre de notifications non lues
  useEffect(() => {
    const loadUnreadCount = async () => {
      if (user?.id) {
        try {
          const response = await fetch(`/api/notifications/player/${user.id}/unread-count`);
          if (response.ok) {
            const data = await response.json();
            setUnreadNotifications(data.unread_count);
          }
        } catch (error) {
          console.error('Erreur lors du chargement des notifications:', error);
        }
      }
    };

    loadUnreadCount();

    // Actualiser périodiquement les notifications (toutes les 30 secondes)
    const interval = setInterval(loadUnreadCount, 30000);

    // Charger également les messages non lus
    const loadUnreadMessages = async () => {
      if (user?.id) {
        try {
          const response = await fetch(`${getApiUrl()}/api/messages/unread-count/${user.id}`);
          if (response.ok) {
            const data = await response.json();
            setUnreadMessages(data.unread_count || 0);
          }
        } catch (error) {
          console.error('Erreur lors du chargement des messages:', error);
        }
      }
    };

    loadUnreadMessages();
    const messagesInterval = setInterval(loadUnreadMessages, 30000);

    // Charger les récompenses de quêtes non réclamées
    const loadUnclaimedQuestRewards = async () => {
      if (user?.username) {
        try {
          const response = await fetch(`/api/quests/unclaimed?username=${user.username}`);
          if (response.ok) {
            const data = await response.json();
            const hasRewards = (data.unclaimed_rewards || []).length > 0;
            setHasUnclaimedQuestRewards(hasRewards);
          }
        } catch (error) {
          console.error('Erreur lors de la vérification des récompenses de quêtes:', error);
        }
      }
    };

    loadUnclaimedQuestRewards();
    const questRewardsInterval = setInterval(loadUnclaimedQuestRewards, 30000);

    // Écouter les événements de notification
    const handleNotificationUpdate = () => {
      loadUnreadCount();
    };

    const handleNotificationsRead = () => {
      setUnreadNotifications(0);
    };

    window.addEventListener('notificationUpdate', handleNotificationUpdate);
    window.addEventListener('notificationsRead', handleNotificationsRead);
    
    return () => {
      clearInterval(interval);
      clearInterval(messagesInterval);
      clearInterval(questRewardsInterval);
      window.removeEventListener('notificationUpdate', handleNotificationUpdate);
      window.removeEventListener('notificationsRead', handleNotificationsRead);
    };
  }, [user?.id, user?.username]);

  const handleMenuClick = () => {
    console.log('📋 [BottomNavBar] Menu ouvert');
    setIsMenuOpen(true);
  };

  const handleCloseMenu = () => {
    setIsMenuOpen(false);
  };

  const handleJournal = () => {
    setIsMenuOpen(false);
    setIsNotificationJournalOpen(true);
  };

  const handleCloseNotificationJournal = () => {
    setIsNotificationJournalOpen(false);
  };

  const handleArmy = () => {
    // Désactivé - Utiliser le bouton ⚔️ dans le HeaderBar
    setIsMenuOpen(false);
  };

  const handleResearch = () => {
    navigate('/research');
    setIsMenuOpen(false);
  };

  const handleLeaderboard = () => {
    navigate('/leaderboard');
    setIsMenuOpen(false);
  };

  const handleQuests = () => {
    navigate('/quests');
    setIsMenuOpen(false);
  };

  const handleMessage = () => {
    console.log('📬 [BottomNavBar] handleMessage appelé');
    setIsMessagesOpen(true);
    setIsMenuOpen(false);
    console.log('📬 [BottomNavBar] Popup messagerie ouvert');
  };

  const handleLogout = () => {
    logout();
    navigate('/');
    setIsMenuOpen(false);
  };

  const handleProfileClick = () => {
    setIsProfilePopupOpen(true);
  };

  const handleCloseProfilePopup = () => {
    setIsProfilePopupOpen(false);
  };

  const handleSettingsClick = () => {
    setIsMenuOpen(false);
    setIsSettingsOpen(true);
  };

  const handleCloseSettings = () => {
    setIsSettingsOpen(false);
  };

  const handleResourceClick = (resourceType: string) => {
    switch(resourceType) {
      case 'gold':
        // Déclencher l'événement pour ouvrir le popup d'or
        const goldEvent = new CustomEvent('openGoldPopup');
        window.dispatchEvent(goldEvent);
        break;
      case 'research_points':
        // Naviguer vers la page de recherche
        navigate('/research');
        break;
      case 'transport_ships':
        // Déclencher l'événement pour ouvrir le popup des transports
        const transportEvent = new CustomEvent('openTransportPopup');
        window.dispatchEvent(transportEvent);
        break;
      case 'diamonds':
        // Action pour les diamants (à définir selon les besoins)
        console.log('Clic sur diamants - action à définir');
        break;
    }
  };

  const formatNumber = (value: number | undefined): string => {
    if (!value) return "0";
    if (value < 10000) {
      return Math.floor(value).toString();
    } else if (value < 1000000) {
      const kValue = value / 1000;
      return kValue < 10 ? kValue.toFixed(1) + 'K' : Math.floor(kValue) + 'K';
    } else {
      const mValue = value / 1000000;
      return mValue < 10 ? mValue.toFixed(1) + 'M' : Math.floor(mValue) + 'M';
    }
  };

  return (
    <>
      <nav className="bottom-nav-bar">
        {/* LIGNE 1: Ressources du joueur */}
        <div className="nav-line nav-resources-line">
          <button onClick={handleProfileClick} className="nav-resource-btn" title="Profil">
            👤
          </button>
          
          {playerResources?.gold !== undefined && (
            <button 
              className="nav-resource-btn" 
              title="Or"
              onClick={() => handleResourceClick('gold')}
            >
              💰{formatNumber(playerResources.gold)}
            </button>
          )}
          
          {playerResources?.research_points !== undefined && (
            <button 
              className="nav-resource-btn" 
              title="Points de recherche"
              onClick={() => handleResourceClick('research_points')}
            >
              🔬{formatNumber(playerResources.research_points)}
            </button>
          )}
          
          {playerResources?.transport_ships !== undefined && (
            <button 
              className="nav-resource-btn" 
              title="Bateaux de transport"
              onClick={() => handleResourceClick('transport_ships')}
            >
              🚢{playerInfo ? 
                `${Math.floor(playerInfo.transport_ships_available || 0)}/${Math.floor(playerInfo.transport_ships_total || 0)}` :
                formatNumber(playerResources.transport_ships)
              }
            </button>
          )}
          
          {playerResources?.diamonds !== undefined && (
            <button 
              className="nav-resource-btn" 
              title="Diamants"
              onClick={() => handleResourceClick('diamonds')}
            >
              💎{formatNumber(playerResources.diamonds)}
            </button>
          )}
        </div>

        {/* LIGNE 2: Boutons de navigation */}
        <div className="nav-line nav-buttons-line">
          <button onClick={handleMenuClick} className="nav-btn">
            Menu
            {unreadNotifications > 0 && (
              <span className="notification-badge">{unreadNotifications}</span>
            )}
            {unreadMessages > 0 && (
              <span className="message-badge">{unreadMessages}</span>
            )}
          </button>
          <button onClick={() => navigate('/world')} className="nav-btn">Monde</button>
          <button onClick={() => navigate(`/island/${activeIslandId}`)} className="nav-btn">Île</button>
          <button onClick={() => navigate(`/city/${activeCityId}`)} className="nav-btn">Ville</button>
          <button 
            onClick={toggleMute} 
            style={{
              background: 'transparent',
              border: 'none',
              fontSize: '18px',
              cursor: 'pointer',
              padding: '4px 8px',
              opacity: 0.7,
              transition: 'opacity 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
            onMouseLeave={(e) => e.currentTarget.style.opacity = '0.7'}
            title={isMuted ? "Activer la musique" : "Couper la musique"}
          >
            {isMuted ? '🔇' : '🔊'}
          </button>
        </div>
      </nav>

      <MenuPopup
        isOpen={isMenuOpen}
        onClose={handleCloseMenu}
        onJournal={handleJournal}
        onArmy={handleArmy}
        onResearch={handleResearch}
        onLeaderboard={handleLeaderboard}
        onQuests={handleQuests}
        onMessage={handleMessage}
        onSettings={handleSettingsClick}
        onLogout={handleLogout}
        unreadNotifications={unreadNotifications}
        unreadMessages={unreadMessages}
        hasChiefHouse={hasChiefHouse}
      />
      
      <NotificationJournalPopup
        isOpen={isNotificationJournalOpen}
        onClose={handleCloseNotificationJournal}
      />

      <ProfilePopup
        isOpen={isProfilePopupOpen}
        onClose={handleCloseProfilePopup}
      />

      <SettingsPopup
        isOpen={isSettingsOpen}
        onClose={handleCloseSettings}
      />

      <MessagesPopup
        isOpen={isMessagesOpen}
        onClose={() => setIsMessagesOpen(false)}
      />
    </>
  );
};

export default BottomNavBar;
