import React from 'react';
import '../styles/WallInteractionPopup.css';
import { WallGroup, WallStats } from '../types/wallTypes';

interface WallInteractionPopupProps {
  isOpen: boolean;
  onClose: () => void;
  position: { q: number; r: number };
  wallGroup: WallGroup | null;
  wallStats: WallStats;
  onAttackWall?: (groupIndex: number, damage: number) => void;
  onOpenCombatPopup?: (wallGroup: WallGroup, wallStats: WallStats) => void;
  currentPlayer?: string;
}

const WallInteractionPopup: React.FC<WallInteractionPopupProps> = ({
  isOpen,
  onClose,
  position,
  wallGroup,
  wallStats,
  onAttackWall,
  onOpenCombatPopup,
  currentPlayer
}) => {
  if (!isOpen || !wallGroup) return null;

  const hpPercentage = (wallGroup.hp / wallGroup.max_hp) * 100;
  
  const getHpColor = () => {
    if (hpPercentage > 66) return '#27ae60'; // Vert
    if (hpPercentage > 33) return '#f39c12'; // Orange
    return '#e74c3c'; // Rouge
  };

  const handleAttack = () => {
    if (onOpenCombatPopup && wallGroup) {
      // Ouvrir le popup de combat au lieu d'attaquer directement
      onOpenCombatPopup(wallGroup, wallStats);
      onClose(); // Fermer le popup des murs
    }
  };

  return (
    <div className="wall-interaction-overlay" onClick={onClose}>
      <div className="wall-interaction-popup" onClick={e => e.stopPropagation()}>
        
        {/* Header */}
        <div className="wall-popup-header">
          <div className="wall-icon">🧱</div>
          <div className="wall-title">
            <h3>Groupe de Murs #{wallGroup.group_index + 1}</h3>
            <p>Position: ({position.q}, {position.r})</p>
          </div>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        {/* Informations du groupe */}
        <div className="wall-info-section">
          <div className="wall-hp-container">
            <div className="hp-label">Points de Vie</div>
            <div className="hp-bar-container">
              <div 
                className="hp-bar-fill" 
                style={{ 
                  width: `${hpPercentage}%`,
                  backgroundColor: getHpColor()
                }}
              ></div>
              <div className="hp-text">
                {wallGroup.hp} / {wallGroup.max_hp}
              </div>
            </div>
          </div>

          <div className="wall-stats-grid">
            <div className="stat-item">
              <span className="stat-icon">📐</span>
              <span className="stat-label">Positions:</span>
              <span className="stat-value">{wallGroup.total_positions}</span>
            </div>
            <div className="stat-item">
              <span className="stat-icon">🛡️</span>
              <span className="stat-label">Défense:</span>
              <span className="stat-value">+{wallStats.defense}</span>
            </div>
            <div className="stat-item">
              <span className="stat-icon">🏹</span>
              <span className="stat-label">Attaque:</span>
              <span className="stat-value">{wallStats.attack_ranged}</span>
            </div>
            <div className="stat-item">
              <span className="stat-icon">📏</span>
              <span className="stat-label">Portée:</span>
              <span className="stat-value">{wallStats.range}</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="wall-actions">
          {wallGroup.hp > 0 ? (
            <>
              <div className="action-info">
                <p>💡 Ce groupe de murs peut être attaqué par vos unités.</p>
                <p>🎯 Les unités de siège infligent des dégâts supplémentaires.</p>
              </div>
              
              {onOpenCombatPopup && (
                <button 
                  className="attack-wall-btn" 
                  onClick={handleAttack}
                  disabled={!currentPlayer}
                >
                  ⚔️ Attaquer ce groupe de murs
                </button>
              )}
            </>
          ) : (
            <div className="wall-destroyed">
              <p>💥 Ce groupe de murs a été détruit !</p>
              <p>✅ Les unités peuvent désormais passer par cette zone.</p>
            </div>
          )}
        </div>

        {/* Informations générales */}
        <div className="wall-general-info">
          <h4>ℹ️ Système de Fortification</h4>
          <div className="info-grid">
            <div className="info-item">
              <strong>Niveau de muraille:</strong> {wallGroup.wall_level}
            </div>
            <div className="info-item">
              <strong>Éléments totaux:</strong> {wallStats.nb_element}
            </div>
            <div className="info-item">
              <strong>Type de carte:</strong> {wallStats.battlefield_map}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WallInteractionPopup;