import React, { useState } from 'react';
import { useUser } from '../hooks/useUser';
import './SettingsPopup.css';

interface SettingsPopupProps {
  isOpen: boolean;
  onClose: () => void;
}

const SettingsPopup: React.FC<SettingsPopupProps> = ({ isOpen, onClose }) => {
  const { user } = useUser();
  const [showTutorialConfirm, setShowTutorialConfirm] = useState(false);
  const [tutorialResetting, setTutorialResetting] = useState(false);

  if (!isOpen) return null;

  const handleResetTutorial = async () => {
    if (!user?.id) return;

    setTutorialResetting(true);
    try {
      const response = await fetch(`/api/tutorial/reset/${user.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      const data = await response.json();

      if (data.success) {
        alert('✅ Tutoriel réinitialisé ! Rechargez la page pour le recommencer.');
        setShowTutorialConfirm(false);
        onClose();
      } else {
        alert('❌ Erreur lors de la réinitialisation du tutoriel.');
      }
    } catch (error) {
      console.error('Erreur reset tutoriel:', error);
      alert('❌ Erreur réseau.');
    } finally {
      setTutorialResetting(false);
    }
  };

  return (
    <div className="settings-popup-overlay" onClick={onClose}>
      <div className="settings-popup-content" onClick={(e) => e.stopPropagation()}>
        <div className="settings-popup-header">
          <h2>⚙️ Options du jeu</h2>
          <button className="settings-close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="settings-popup-body">
          {/* Section Tutoriel */}
          <div className="settings-section">
            <h3>📚 Tutoriel</h3>
            <p className="settings-description">
              Réinitialisez le tutoriel pour le refaire depuis le début et récupérer toutes les récompenses.
            </p>
            
            {!showTutorialConfirm ? (
              <button 
                className="settings-btn settings-btn-primary"
                onClick={() => setShowTutorialConfirm(true)}
              >
                🔄 Recommencer le tutoriel
              </button>
            ) : (
              <div className="settings-confirm-box">
                <p className="settings-confirm-text">
                  ⚠️ Êtes-vous sûr ? Le tutoriel redémarrera dès le prochain chargement de page.
                </p>
                <div className="settings-confirm-actions">
                  <button 
                    className="settings-btn settings-btn-danger"
                    onClick={handleResetTutorial}
                    disabled={tutorialResetting}
                  >
                    {tutorialResetting ? '⏳ Réinitialisation...' : '✅ Oui, réinitialiser'}
                  </button>
                  <button 
                    className="settings-btn settings-btn-secondary"
                    onClick={() => setShowTutorialConfirm(false)}
                    disabled={tutorialResetting}
                  >
                    ❌ Annuler
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Section Audio (à venir) */}
          <div className="settings-section settings-section-disabled">
            <h3>🔊 Audio</h3>
            <p className="settings-description">
              Réglages des sons et de la musique (prochainement)
            </p>
            <div className="settings-disabled-overlay">
              <span>Bientôt disponible</span>
            </div>
          </div>

          {/* Section Notifications (à venir) */}
          <div className="settings-section settings-section-disabled">
            <h3>🔔 Notifications</h3>
            <p className="settings-description">
              Gérez vos notifications dans le jeu (prochainement)
            </p>
            <div className="settings-disabled-overlay">
              <span>Bientôt disponible</span>
            </div>
          </div>

          {/* Section Graphismes (à venir) */}
          <div className="settings-section settings-section-disabled">
            <h3>🎨 Graphismes</h3>
            <p className="settings-description">
              Qualité graphique et performances (prochainement)
            </p>
            <div className="settings-disabled-overlay">
              <span>Bientôt disponible</span>
            </div>
          </div>
        </div>

        <div className="settings-popup-footer">
          <button className="settings-btn settings-btn-close" onClick={onClose}>
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPopup;
