import React, { useState, useEffect } from 'react';
import '../styles/WallPopupContent.css';

interface WallEffect {
  defense: number;
  wall_hp: number;
  attack_ranged: number;
  range: number;
  battlefield_map: string;
}

interface WallLevel {
  level: number;
  cost: Record<string, number>;
  construction_time: number;
  effect: WallEffect;
}

interface WallBuilding {
  description: string;
  image: string;
  category: string;
  required_research: string | null;
  max_instances: number;
  levels: WallLevel[];
}

interface City {
  id: string;
  name: string;
  resources?: Record<string, number>;
}

interface CityBuilding {
  name: string;
  level: number;
  slot_id: string;
}

interface WallPopupContentProps {
  city: City;
  building: CityBuilding;
  onClose: () => void;
  onCityDataChange?: () => void;
}

const WallPopupContent: React.FC<WallPopupContentProps> = ({
  city,
  building,
  onClose,
  onCityDataChange
}) => {
  const [wallData, setWallData] = useState<WallBuilding | null>(null);
  const [loading, setLoading] = useState(false);
  const [upgradeInProgress, setUpgradeInProgress] = useState(false);

  useEffect(() => {
    fetchWallData();
  }, []);

  const fetchWallData = async () => {
    try {
      const response = await fetch('/data/buildings.json');
      const data = await response.json();
      if (data.Muraille) {
        setWallData(data.Muraille);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des données de muraille:', error);
    }
  };

  const getCurrentLevel = () => {
    return wallData?.levels.find(level => level.level === building.level);
  };

  const getNextLevel = () => {
    if (building.level >= 10) return null;
    return wallData?.levels.find(level => level.level === building.level + 1);
  };

  const canAffordUpgrade = (nextLevel: WallLevel) => {
    if (!city.resources) return false;
    
    return Object.entries(nextLevel.cost).every(([resource, cost]) => {
      return (city.resources?.[resource] || 0) >= cost;
    });
  };

  const handleUpgrade = async () => {
    const nextLevel = getNextLevel();
    if (!nextLevel || upgradeInProgress) return;

    setUpgradeInProgress(true);
    setLoading(true);

    try {
      const response = await fetch(`/api/city/${city.id}/build`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          slot_id: building.slot_id,
          building: 'Muraille'
        }),
      });

      const result = await response.json();
      if (result.success) {
        // Rafraîchir les données de la ville
        if (onCityDataChange) {
          onCityDataChange();
        }
        console.log('Muraille améliorée avec succès !');
      } else {
        console.error('Erreur lors de l\'amélioration:', result.message);
      }
    } catch (error) {
      console.error('Erreur lors de l\'amélioration de la muraille:', error);
    } finally {
      setLoading(false);
      setUpgradeInProgress(false);
    }
  };

  if (!wallData) {
    return (
      <div className="wall-popup-content">
        <div className="loading">Chargement des données de muraille...</div>
      </div>
    );
  }

  const currentLevel = getCurrentLevel();
  const nextLevel = getNextLevel();

  return (
    <div className="wall-popup-content">
      <div className="wall-header">
        <div className="wall-image">
          <img src={wallData.image} alt="Muraille" />
        </div>
        <div className="wall-info">
          <h2>Muraille - Niveau {building.level}</h2>
          <p className="wall-description">{wallData.description}</p>
        </div>
      </div>

      {currentLevel && (
        <div className="current-stats">
          <h3>🏰 Statistiques Actuelles</h3>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-label">🛡️ Défense de ville:</span>
              <span className="stat-value">{currentLevel.effect.defense}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">💚 HP des murs:</span>
              <span className="stat-value">{currentLevel.effect.wall_hp}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">🏹 Attaque à distance:</span>
              <span className="stat-value">{currentLevel.effect.attack_ranged}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">🎯 Portée d'attaque:</span>
              <span className="stat-value">{currentLevel.effect.range}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">🗺️ Carte de bataille:</span>
              <span className="stat-value">{currentLevel.effect.battlefield_map}</span>
            </div>
          </div>
        </div>
      )}

      {nextLevel && (
        <div className="upgrade-section">
          <h3>⬆️ Amélioration Niveau {nextLevel.level}</h3>
          
          <div className="next-stats">
            <h4>📈 Nouvelles Statistiques</h4>
            <div className="stats-comparison">
              <div className="stat-comparison">
                <span className="stat-label">🛡️ Défense:</span>
                <span className="stat-change">
                  {currentLevel?.effect.defense} → {nextLevel.effect.defense}
                  <span className="improvement">+{nextLevel.effect.defense - (currentLevel?.effect.defense || 0)}</span>
                </span>
              </div>
              <div className="stat-comparison">
                <span className="stat-label">💚 HP murs:</span>
                <span className="stat-change">
                  {currentLevel?.effect.wall_hp} → {nextLevel.effect.wall_hp}
                  <span className="improvement">+{nextLevel.effect.wall_hp - (currentLevel?.effect.wall_hp || 0)}</span>
                </span>
              </div>
              <div className="stat-comparison">
                <span className="stat-label">🏹 Attaque:</span>
                <span className="stat-change">
                  {currentLevel?.effect.attack_ranged} → {nextLevel.effect.attack_ranged}
                  <span className="improvement">+{nextLevel.effect.attack_ranged - (currentLevel?.effect.attack_ranged || 0)}</span>
                </span>
              </div>
              <div className="stat-comparison">
                <span className="stat-label">🎯 Portée:</span>
                <span className="stat-change">
                  {currentLevel?.effect.range} → {nextLevel.effect.range}
                  {nextLevel.effect.range > (currentLevel?.effect.range || 0) && 
                    <span className="improvement">+{nextLevel.effect.range - (currentLevel?.effect.range || 0)}</span>
                  }
                </span>
              </div>
              <div className="stat-comparison">
                <span className="stat-label">🗺️ Carte:</span>
                <span className="stat-change">
                  {currentLevel?.effect.battlefield_map} → {nextLevel.effect.battlefield_map}
                </span>
              </div>
            </div>
          </div>

          <div className="upgrade-cost">
            <h4>💰 Coût d'amélioration</h4>
            <div className="resources-cost">
              {Object.entries(nextLevel.cost).map(([resource, cost]) => {
                const available = city.resources?.[resource] || 0;
                const canAfford = available >= cost;
                
                return (
                  <div key={resource} className={`resource-cost ${canAfford ? 'affordable' : 'unaffordable'}`}>
                    <img src={`/assets/icons/${resource}.png`} alt={resource} className="resource-icon" />
                    <span className="resource-amount">{cost}</span>
                    <span className="resource-available">({available})</span>
                  </div>
                );
              })}
            </div>
            <div className="construction-time">
              ⏱️ Temps de construction: {nextLevel.construction_time} minutes
            </div>
          </div>

          <div className="upgrade-actions">
            <button
              className={`upgrade-button ${canAffordUpgrade(nextLevel) ? 'enabled' : 'disabled'}`}
              onClick={handleUpgrade}
              disabled={!canAffordUpgrade(nextLevel) || upgradeInProgress || loading}
            >
              {loading ? '⏳ Amélioration...' : `⬆️ Améliorer au niveau ${nextLevel.level}`}
            </button>
          </div>
        </div>
      )}

      {building.level >= 10 && (
        <div className="max-level">
          <h3>👑 Niveau Maximum Atteint</h3>
          <p>Votre muraille a atteint son niveau maximum. Vos défenses sont légendaires !</p>
        </div>
      )}

      <div className="wall-info-section">
        <h3>ℹ️ Informations sur la Muraille</h3>
        <div className="info-content">
          <p><strong>🎯 Rôle:</strong> La muraille protège votre ville lors des attaques ennemies.</p>
          <p><strong>🗺️ Cartes de bataille:</strong> Chaque niveau débloque une carte de ville plus fortifiée.</p>
          <p><strong>🏹 Défense active:</strong> Les murs peuvent attaquer les unités ennemies à distance.</p>
          <p><strong>💚 Résistance:</strong> Plus le niveau est élevé, plus les murs résistent aux attaques.</p>
        </div>
      </div>

      <div className="popup-footer">
        <button className="close-button" onClick={onClose}>
          ❌ Fermer
        </button>
      </div>
    </div>
  );
};

export default WallPopupContent;