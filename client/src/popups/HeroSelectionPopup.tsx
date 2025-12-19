import React, { useState, useEffect } from 'react';
import '../styles/heroSelection.css';

interface Hero {
  id: string;
  name: string;
  description: string;
  specialty: string;
  rarity: string;
  base_stats: {
    hp: number;
    attack_melee: number;
    defense_melee: number;
    movement: number;
    range: number;
  };
  base_bonuses: {
    offensive_bonus: number;
    defensive_bonus: number;
    movement_bonus: number;
    moral_bonus: number;
    aura_radius: number;
  };
}

interface HeroSelectionPopupProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectHero: (heroId: string) => void;
  playerId: string;
}

const HeroSelectionPopup: React.FC<HeroSelectionPopupProps> = ({
  isOpen,
  onClose,
  onSelectHero,
  playerId
}) => {
  const [heroes, setHeroes] = useState<Record<string, Hero>>({});
  const [selectedHero, setSelectedHero] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isOpen) {
      fetchHeroes();
    }
  }, [isOpen]);

  const fetchHeroes = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/heroes/available');
      const data = await response.json();
      
      if (data.success) {
        setHeroes(data.heroes);
      } else {
        console.error('Erreur lors du chargement des héros:', data.message);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des héros:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = () => {
    if (selectedHero) {
      onSelectHero(selectedHero);
      onClose();
    }
  };

  const getSpecialtyIcon = (specialty: string) => {
    const icons = {
      offensive: '⚔️',
      defensive: '🛡️',
      movement: '🏃‍♂️',
      moral: '👑'
    };
    return icons[specialty as keyof typeof icons] || '⚡';
  };

  const getSpecialtyColor = (specialty: string) => {
    const colors = {
      offensive: '#e74c3c',
      defensive: '#3498db',
      movement: '#f39c12',
      moral: '#9b59b6'
    };
    return colors[specialty as keyof typeof colors] || '#95a5a6';
  };

  const getRarityColor = (rarity: string) => {
    const colors = {
      legendary: '#f1c40f',
      epic: '#9b59b6',
      rare: '#3498db',
      common: '#95a5a6'
    };
    return colors[rarity as keyof typeof colors] || '#95a5a6';
  };

  if (!isOpen) return null;

  return (
    <div className="hero-selection-overlay">
      <div className="hero-selection-popup">
        <div className="hero-selection-header">
          <h2>🏛️ Académie des Héros</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        <div className="hero-selection-content">
          <p className="selection-instruction">
            Choisissez votre premier héros légendaire. Chacun possède des spécialités uniques qui influenceront vos stratégies de bataille.
          </p>

          {loading ? (
            <div className="loading">Chargement des héros...</div>
          ) : (
            <div className="heroes-grid">
              {Object.entries(heroes).map(([heroId, hero]) => (
                <div
                  key={heroId}
                  className={`hero-card ${selectedHero === heroId ? 'selected' : ''}`}
                  onClick={() => setSelectedHero(heroId)}
                  style={{ 
                    borderColor: selectedHero === heroId ? getSpecialtyColor(hero.specialty) : '#ddd'
                  }}
                >
                  <div className="hero-card-header">
                    <div className="hero-name">{hero.name}</div>
                    <div 
                      className="hero-rarity"
                      style={{ color: getRarityColor(hero?.rarity || 'common') }}
                    >
                      ★ {(hero?.rarity || 'common').toUpperCase()}
                    </div>
                  </div>

                  <div className="hero-specialty">
                    <span 
                      className="specialty-icon"
                      style={{ color: getSpecialtyColor(hero.specialty) }}
                    >
                      {getSpecialtyIcon(hero.specialty)}
                    </span>
                    <span className="specialty-name">
                      Spécialité: {(hero?.specialty ? (hero.specialty.charAt(0).toUpperCase() + hero.specialty.slice(1)) : 'Aucune')}
                    </span>
                  </div>

                  <div className="hero-description">
                    {hero.description}
                  </div>

                  <div className="hero-stats">
                    <div className="stats-section">
                      <h4>📊 Statistiques</h4>
                      <div className="stats-grid">
                        <div className="stat">
                          <span>❤️ PV:</span>
                          <span>{hero?.base_stats?.hp ?? 0}</span>
                        </div>
                        <div className="stat">
                          <span>⚔️ Attaque:</span>
                          <span>{hero?.base_stats?.attack_melee ?? 0}</span>
                        </div>
                        <div className="stat">
                          <span>🛡️ Défense:</span>
                          <span>{hero?.base_stats?.defense_melee ?? 0}</span>
                        </div>
                        <div className="stat">
                          <span>🏃‍♂️ Mouvement:</span>
                          <span>{hero?.base_stats?.movement ?? 0}</span>
                        </div>
                      </div>
                    </div>

                    <div className="bonuses-section">
                      <h4>💎 Bonus d'Aura</h4>
                      <div className="bonuses-grid">
                        <div className="bonus">
                          <span>⚔️ Offensif:</span>
                          <span>+{hero?.base_bonuses?.offensive_bonus ?? 0}%</span>
                        </div>
                        <div className="bonus">
                          <span>🛡️ Défensif:</span>
                          <span>+{hero?.base_bonuses?.defensive_bonus ?? 0}%</span>
                        </div>
                        <div className="bonus">
                          <span>🏃‍♂️ Mouvement:</span>
                          <span>+{hero?.base_bonuses?.movement_bonus ?? 0}</span>
                        </div>
                        <div className="bonus">
                          <span>👑 Moral:</span>
                          <span>+{hero?.base_bonuses?.moral_bonus ?? 0}%</span>
                        </div>
                        <div className="bonus">
                          <span>📡 Rayon:</span>
                          <span>{hero?.base_bonuses?.aura_radius ?? 0} cases</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="hero-selection-footer">
          <button 
            className="cancel-button" 
            onClick={onClose}
          >
            Annuler
          </button>
          <button 
            className="confirm-button" 
            onClick={handleConfirm}
            disabled={!selectedHero}
            style={{
              backgroundColor: selectedHero ? getSpecialtyColor(heroes[selectedHero]?.specialty || '') : '#ccc'
            }}
          >
            Recruter {selectedHero ? heroes[selectedHero]?.name : 'un Héros'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default HeroSelectionPopup;
