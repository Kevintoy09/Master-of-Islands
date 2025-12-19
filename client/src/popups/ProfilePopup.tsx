import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../hooks/useUser';

interface ProfilePopupProps {
  isOpen: boolean;
  onClose: () => void;
}

const ProfilePopup: React.FC<ProfilePopupProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const { user, logout } = useUser();

  if (!isOpen) return null;

  const handleLogout = () => {
    logout();
    navigate('/login');
    onClose();
  };

  const handleSettings = () => {
    navigate('/settings');
    onClose();
  };

  const handleStats = () => {
    navigate('/leaderboard');
    onClose();
  };

  const overlayStyle: React.CSSProperties = {
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100vw',
    height: '100vh',
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 9999,
  };

  const popupStyle: React.CSSProperties = {
    position: 'relative',
    width: '90%',
    maxWidth: '400px',
    background: 'linear-gradient(135deg, #2c1810 0%, #1a0f0a 100%)',
    border: '3px solid #8b7355',
    borderRadius: '12px',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(139, 115, 85, 0.5)',
    padding: '24px',
    fontFamily: 'Arial, sans-serif',
  };

  const headerStyle: React.CSSProperties = {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#e8d7c3',
    textAlign: 'center',
    marginBottom: '20px',
    textShadow: '2px 2px 4px rgba(0, 0, 0, 0.8)',
  };

  const closeButtonStyle: React.CSSProperties = {
    position: 'absolute',
    top: '12px',
    right: '12px',
    background: 'transparent',
    border: 'none',
    color: '#e8d7c3',
    fontSize: '28px',
    cursor: 'pointer',
    lineHeight: '1',
    padding: '4px 8px',
    transition: 'all 0.2s',
  };

  const userInfoStyle: React.CSSProperties = {
    background: 'rgba(139, 115, 85, 0.2)',
    border: '1px solid #8b7355',
    borderRadius: '8px',
    padding: '16px',
    marginBottom: '20px',
    color: '#e8d7c3',
  };

  const usernameStyle: React.CSSProperties = {
    fontSize: '20px',
    fontWeight: 'bold',
    marginBottom: '8px',
    color: '#ffd700',
    textShadow: '1px 1px 2px rgba(0, 0, 0, 0.8)',
  };

  const userDetailStyle: React.CSSProperties = {
    fontSize: '14px',
    color: '#c9b89a',
    marginBottom: '4px',
  };

  const buttonStyle: React.CSSProperties = {
    display: 'block',
    width: '100%',
    padding: '12px',
    margin: '10px 0',
    fontSize: '16px',
    fontWeight: '600',
    background: 'linear-gradient(135deg, #8b7355 0%, #6d5a44 100%)',
    color: '#e8d7c3',
    border: '2px solid #8b7355',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.3s',
    textAlign: 'center',
    boxShadow: '0 4px 8px rgba(0, 0, 0, 0.3)',
  };

  const logoutButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    background: 'linear-gradient(135deg, #8b2e2e 0%, #6b1e1e 100%)',
    border: '2px solid #a03434',
    marginTop: '20px',
  };

  return (
    <div style={overlayStyle} onClick={onClose}>
      <div style={popupStyle} onClick={(e) => e.stopPropagation()}>
        <button
          style={closeButtonStyle}
          onClick={onClose}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = '#ffd700';
            e.currentTarget.style.transform = 'scale(1.1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = '#e8d7c3';
            e.currentTarget.style.transform = 'scale(1)';
          }}
        >
          ×
        </button>

        <div style={headerStyle}>👤 Profil</div>

        <div style={userInfoStyle}>
          <div style={usernameStyle}>{user?.username || 'Joueur'}</div>
          <div style={userDetailStyle}>🆔 ID: {user?.id || 'N/A'}</div>
        </div>

        <button
          style={buttonStyle}
          onClick={handleStats}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'linear-gradient(135deg, #a08866 0%, #8b7355 100%)';
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 6px 12px rgba(0, 0, 0, 0.4)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'linear-gradient(135deg, #8b7355 0%, #6d5a44 100%)';
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.3)';
          }}
        >
          📊 Statistiques
        </button>

        <button
          style={buttonStyle}
          onClick={handleSettings}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'linear-gradient(135deg, #a08866 0%, #8b7355 100%)';
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 6px 12px rgba(0, 0, 0, 0.4)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'linear-gradient(135deg, #8b7355 0%, #6d5a44 100%)';
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.3)';
          }}
        >
          ⚙️ Paramètres
        </button>

        <button
          style={logoutButtonStyle}
          onClick={handleLogout}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'linear-gradient(135deg, #a83b3b 0%, #8b2e2e 100%)';
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 6px 12px rgba(0, 0, 0, 0.5)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'linear-gradient(135deg, #8b2e2e 0%, #6b1e1e 100%)';
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.3)';
          }}
        >
          🚪 Se déconnecter
        </button>
      </div>
    </div>
  );
};

export default ProfilePopup;
