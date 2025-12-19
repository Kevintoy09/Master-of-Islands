import React, { useState } from 'react';
import './HeroDetailPopup.css';

interface HeroDetailPopupProps {
  hero: any;
  cityId: string;
  onClose: () => void;
  onHeroUpdated?: () => void;
}

const HeroDetailPopup: React.FC<HeroDetailPopupProps> = ({ 
  hero, 
  cityId, 
  onClose, 
  onHeroUpdated 
}) => {
  const [isLevelingUp, setIsLevelingUp] = useState(false);
  const [heroData, setHeroData] = useState(hero);

  // Calculer l'XP nécessaire pour le prochain niveau
  const getNextLevelXp = () => {
    if (!heroData.experience_table) return null;
    
    const nextLevel = heroData.current_level + 1;
    const nextLevelData = heroData.experience_table.find((exp: any) => exp.level === nextLevel);
    return nextLevelData ? nextLevelData.xp_required : null;
  };

  // Vérifier si le héros peut monter de niveau
  const canLevelUp = () => {
    const nextLevelXp = getNextLevelXp();
    return nextLevelXp !== null && heroData.current_experience >= nextLevelXp;
  };

  // Calculer la progression XP pour la barre
  const getXpProgress = () => {
    if (!heroData.experience_table) return 0;
    
    const currentLevelData = heroData.experience_table.find((exp: any) => exp.level === heroData.current_level);
    const nextLevelXp = getNextLevelXp();
    
    if (!currentLevelData) return 0;
    
    // Si niveau max atteint
    if (!nextLevelXp) return 100;
    
    const currentXp = heroData.current_experience - currentLevelData.xp_required;
    const xpNeeded = nextLevelXp - currentLevelData.xp_required;
    
    if (xpNeeded <= 0) return 100;
    
    return Math.min((currentXp / xpNeeded) * 100, 100);
  };

  // Fonction pour monter de niveau
  const handleLevelUp = async () => {
    if (!canLevelUp()) return;
    
    setIsLevelingUp(true);
    
    try {
      const response = await fetch('/api/heroes/level-up', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          instance_id: heroData.instance_id,
          city_id: cityId
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setHeroData(data.hero);
        if (onHeroUpdated) {
          onHeroUpdated();
        }
      } else {
        alert('Erreur lors du level up: ' + data.message);
      }
    } catch (error) {
      console.error('Erreur level up:', error);
      alert('Erreur lors du level up');
    } finally {
      setIsLevelingUp(false);
    }
  };

  const getSpecialtyIcon = (specialty: string) => {
    const icons = {
      offensive: '⚔️',
      defensive: '🛡️', 
      movement: '🏃‍♂️',
      support: '🎯'
    };
    return icons[specialty as keyof typeof icons] || '⚡';
  };

  const getSpecialtyColor = (specialty: string) => {
    const colors = {
      offensive: '#e74c3c',
      defensive: '#3498db',
      movement: '#f39c12',
      support: '#9b59b6'
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

  return (
    <div className="hero-detail-overlay">
      <div className="hero-detail-popup">
        <div className="hero-detail-header">
          <button className="close-btn" onClick={onClose}>×</button>
          <div className="hero-title-section">
            <div className="hero-portrait">
              <div 
                className="hero-specialty-badge-large"
                style={{ backgroundColor: getSpecialtyColor(heroData.specialty) }}
              >
                {getSpecialtyIcon(heroData.specialty)}
              </div>
            </div>
            <div className="hero-title-info">
              <h2 className="hero-name">{heroData.name}</h2>
              <div className="hero-meta">
                <span 
                  className="hero-rarity"
                  style={{ color: getRarityColor(heroData.rarity) }}
                >
                  ★ {heroData.rarity?.toUpperCase()}
                </span>
                <span className="hero-specialty">
                  {getSpecialtyIcon(heroData.specialty)} {heroData.specialty}
                </span>
              </div>
              <p className="hero-description">{heroData.description}</p>
            </div>
          </div>
        </div>

        <div className="hero-detail-content">
          {/* Section Niveau et XP */}
          <div className="hero-section">
            <h3 className="section-title">📈 Progression</h3>
            <div className="level-section">
              <div className="level-info">
                <span className="current-level">Niveau {heroData.current_level}</span>
                <span className="xp-info">
                  {heroData.current_experience} / {getNextLevelXp() || 'MAX'} XP
                </span>
              </div>
              <div className="xp-bar">
                <div 
                  className="xp-progress" 
                  style={{ width: `${getXpProgress()}%` }}
                ></div>
              </div>
              <div className="level-up-section">
                {canLevelUp() ? (
                  <button 
                    className="level-up-btn available"
                    onClick={handleLevelUp}
                    disabled={isLevelingUp}
                  >
                    {isLevelingUp ? (
                      <>🔄 Amélioration en cours...</>
                    ) : (
                      <>🎉 Monter au niveau {heroData.current_level + 1}</>
                    )}
                  </button>
                ) : getNextLevelXp() ? (
                  <div className="level-up-info">
                    <div className="xp-needed">
                      <span className="xp-needed-text">
                        ⏳ {getNextLevelXp() - heroData.current_experience} XP manquant pour le niveau {heroData.current_level + 1}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="level-up-info">
                    <span className="max-level">👑 Niveau maximum atteint !</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Section Progression par Niveau */}
          <div className="hero-section">
            <h3 className="section-title">📊 Progression par Niveau</h3>
            <div className="progression-info">
              {heroData.progression && (
                <div className="progression-grid">
                  <div className="progression-category">
                    <h4 className="progression-category-title">⚔️ Stats de Combat</h4>
                    <div className="progression-items">
                      {heroData.progression.hp_per_level && (
                        <div className="progression-item">
                          <span className="progression-icon">❤️</span>
                          <span className="progression-text">+{heroData.progression.hp_per_level} PV par niveau</span>
                        </div>
                      )}
                      {heroData.progression.attack_per_level && (
                        <div className="progression-item">
                          <span className="progression-icon">⚔️</span>
                          <span className="progression-text">+{heroData.progression.attack_per_level} Attaque par niveau</span>
                        </div>
                      )}
                      {heroData.progression.defense_melee_per_level && (
                        <div className="progression-item">
                          <span className="progression-icon">🛡️</span>
                          <span className="progression-text">+{heroData.progression.defense_melee_per_level} Déf. Mêlée par niveau</span>
                        </div>
                      )}
                      {heroData.progression.defense_ranged_per_level && (
                        <div className="progression-item">
                          <span className="progression-icon">🏹</span>
                          <span className="progression-text">+{heroData.progression.defense_ranged_per_level} Déf. Distance par niveau</span>
                        </div>
                      )}
                      {heroData.progression.movement_per_level && heroData.progression.movement_per_level > 0 && (
                        <div className="progression-item">
                          <span className="progression-icon">🏃‍♂️</span>
                          <span className="progression-text">+{heroData.progression.movement_per_level} Mouvement par niveau</span>
                        </div>
                      )}
                      {heroData.progression.range_per_level && heroData.progression.range_per_level > 0 && (
                        <div className="progression-item">
                          <span className="progression-icon">🎯</span>
                          <span className="progression-text">+{heroData.progression.range_per_level} Portée par niveau</span>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="progression-category">
                    <h4 className="progression-category-title">✨ Bonus d'Aura</h4>
                    <div className="progression-items">
                      {heroData.progression.offensive_bonus_per_level && (
                        <div className="progression-item">
                          <span className="progression-icon">⚔️</span>
                          <span className="progression-text">+{heroData.progression.offensive_bonus_per_level}% Bonus Offensif par niveau</span>
                        </div>
                      )}
                      {heroData.progression.defensive_bonus_per_level && (
                        <div className="progression-item">
                          <span className="progression-icon">🛡️</span>
                          <span className="progression-text">+{heroData.progression.defensive_bonus_per_level}% Bonus Défensif par niveau</span>
                        </div>
                      )}
                      {heroData.progression.moral_bonus_per_level && (
                        <div className="progression-item">
                          <span className="progression-icon">💪</span>
                          <span className="progression-text">+{heroData.progression.moral_bonus_per_level}% Bonus Moral par niveau</span>
                        </div>
                      )}
                      {heroData.progression.movement_bonus_per_level && heroData.progression.movement_bonus_per_level > 0 && (
                        <div className="progression-item">
                          <span className="progression-icon">🏃‍♂️</span>
                          <span className="progression-text">+{heroData.progression.movement_bonus_per_level} Mouvement par niveau</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Section Stats */}
          <div className="hero-section">
            <h3 className="section-title">⚔️ Statistiques de Combat</h3>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">❤️</div>
                <div className="stat-info">
                  <span className="stat-label">Points de Vie</span>
                  <span className="stat-value">{heroData.calculated_stats?.hp}</span>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">⚔️</div>
                <div className="stat-info">
                  <span className="stat-label">Attaque Mêlée</span>
                  <span className="stat-value">{heroData.calculated_stats?.attack_melee}</span>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">🛡️</div>
                <div className="stat-info">
                  <span className="stat-label">Défense Mêlée</span>
                  <span className="stat-value">{heroData.calculated_stats?.defense_melee}</span>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">🏹</div>
                <div className="stat-info">
                  <span className="stat-label">Défense Distance</span>
                  <span className="stat-value">{heroData.calculated_stats?.defense_ranged}</span>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">🏃‍♂️</div>
                <div className="stat-info">
                  <span className="stat-label">Mouvement</span>
                  <span className="stat-value">{heroData.calculated_stats?.movement}</span>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">🎯</div>
                <div className="stat-info">
                  <span className="stat-label">Portée</span>
                  <span className="stat-value">{heroData.calculated_stats?.range}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Section Bonus */}
          <div className="hero-section">
            <h3 className="section-title">✨ Bonus d'Aura</h3>
            <div className="bonuses-grid">
              <div className="bonus-card">
                <div className="bonus-icon">⚔️</div>
                <div className="bonus-info">
                  <span className="bonus-label">Bonus Offensif</span>
                  <span className="bonus-value">+{heroData.calculated_bonuses?.offensive_bonus}%</span>
                </div>
              </div>
              <div className="bonus-card">
                <div className="bonus-icon">🛡️</div>
                <div className="bonus-info">
                  <span className="bonus-label">Bonus Défensif</span>
                  <span className="bonus-value">+{heroData.calculated_bonuses?.defensive_bonus}%</span>
                </div>
              </div>
              <div className="bonus-card">
                <div className="bonus-icon">💪</div>
                <div className="bonus-info">
                  <span className="bonus-label">Bonus Moral</span>
                  <span className="bonus-value">+{heroData.calculated_bonuses?.moral_bonus}%</span>
                </div>
              </div>
              <div className="bonus-card">
                <div className="bonus-icon">🌟</div>
                <div className="bonus-info">
                  <span className="bonus-label">Rayon d'Aura</span>
                  <span className="bonus-value">{heroData.calculated_bonuses?.aura_radius}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Section Historique */}
          <div className="hero-section">
            <h3 className="section-title">🏆 Historique de Combat</h3>
            <div className="battle-stats">
              <div className="battle-stat">
                <span className="battle-icon">🎯</span>
                <span className="battle-label">Batailles</span>
                <span className="battle-value">{heroData.battles_fought}</span>
              </div>
              <div className="battle-stat">
                <span className="battle-icon">🏆</span>
                <span className="battle-label">Victoires</span>
                <span className="battle-value">{heroData.victories}</span>
              </div>
              <div className="battle-stat">
                <span className="battle-icon">💀</span>
                <span className="battle-label">Ennemis tués</span>
                <span className="battle-value">{heroData.units_killed}</span>
              </div>
              <div className="battle-stat">
                <span className="battle-icon">📉</span>
                <span className="battle-label">Unités perdues</span>
                <span className="battle-value">{heroData.units_lost}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HeroDetailPopup;