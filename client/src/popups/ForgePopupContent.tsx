import React, { useState, useEffect } from 'react';
import { useUser } from '../hooks/useUser';
import { getResourceEmoji } from '../constants/resourceIcons';
import './ForgePopupContent.css';

interface City {
  id: string;
  name: string;
  owner: string | null;
}

interface CityBuilding {
  name: string;
}

interface ForgeData {
  success: boolean;
  forge_level: number;
  max_improvement_level: number;
  available_units: string[];
  base_stats: { [unitType: string]: { [statName: string]: number } };
  enhanced_stats: { [unitType: string]: { [statName: string]: { base: number; enhanced: number; bonus_percent: number } } };
  current_improvements: { [unitType: string]: { [improvementType: string]: number } };
  resources: { gold: number; wood: number; stone: number; iron: number };
  available_improvements: { [unitType: string]: string[] };
  upgrade_costs: { [level: string]: { [resource: string]: number } };
  improvement_config: { 
    max_improvement_points_per_unit: number;
    bonus_progression: number[];
  };
}

interface ForgeConfig {
  success: boolean;
  config: {
    available_improvements: { [unitType: string]: string[] };
    upgrade_costs: { [level: string]: { [resource: string]: number } };
    bonus_levels: { [level: number]: number };
  };
}

interface ForgePopupContentProps {
  city: City;
  building: CityBuilding;
  onClose: () => void;
  onCityDataChange?: () => void;
}

const ForgePopupContent: React.FC<ForgePopupContentProps> = ({ 
  city, 
  building, 
  onClose, 
  onCityDataChange 
}) => {
  const { user } = useUser();
  const [forgeData, setForgeData] = useState<ForgeData | null>(null);
  const [config, setConfig] = useState<ForgeConfig['config'] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUnit, setSelectedUnit] = useState<string | null>(null);

  // Noms d'affichage
  const unitNames: { [key: string]: string } = {
    'infantry_light': '⚔️ Infanterie Légère',
    'infantry_heavy': '🛡️ Infanterie Lourde',
    'archer': '🏹 Archer',
    'slinger': '🎯 Frondeur',
    'cavalry_light': '🐎 Cavalerie Légère',
    'cavalry_heavy': '🐴 Cavalerie Lourde',
    'ballista': '🎯 Baliste',
    'catapult': '💥 Catapulte'
  };

  const improvementNames: { [key: string]: string } = {
    'attack_melee': '⚔️ Attaque Corps-à-corps',
    'defense_melee': '🛡️ Défense Corps-à-corps',
    'attack_ranged': '🏹 Attaque à Distance',
    'defense_ranged': '🛡️ Défense à Distance'
  };

  useEffect(() => {
    loadData();
  }, [user?.id]);

  const loadData = async () => {
    if (!user?.id) return;
    
    setLoading(true);
    try {
      // Charger les données du joueur et la config en parallèle
      const [dataResponse, configResponse] = await Promise.all([
        fetch(`/api/unit-improvements/forge-data/${user.id}`),
        fetch('/api/unit-improvements/config')
      ]);

      const data = await dataResponse.json();
      const configData = await configResponse.json();

      if (data.success && configData.success) {
        setForgeData(data);
        setConfig(configData.config);
        setError(null);
      } else {
        setError('Erreur lors du chargement des données');
      }
    } catch (err) {
      console.error('Erreur chargement forge:', err);
      setError('Impossible de charger les données de la forge');
    } finally {
      setLoading(false);
    }
  };

  const bonusToPoints = (bonus: number): number => {
    if (!forgeData || bonus <= 0) return 0;
    
    // Utiliser bonus_progression du backend pour calcul cumulatif inverse
    const bonusProgression = forgeData.improvement_config?.bonus_progression || [10, 8, 6, 4, 3];
    
    // Calcul inverse : trouver combien de points donnent ce bonus cumulatif
    let cumulativeBonus = 0;
    for (let points = 1; points <= Math.min(5, bonusProgression.length); points++) {
      cumulativeBonus += bonusProgression[points - 1];
      if (cumulativeBonus === bonus) {
        return points;
      }
    }
    return 0;
  };

  const getTotalPointsUsed = (unitImprovements: { [key: string]: number }): number => {
    return Object.values(unitImprovements).reduce((total, bonus) => total + bonusToPoints(bonus), 0);
  };

  const canUpgrade = (unitType: string, improvementType: string): boolean => {
    if (!forgeData) return false;
    
    const unitImprovements = forgeData.current_improvements[unitType] || {};
    const currentBonus = unitImprovements[improvementType] || 0;
    const currentPoints = bonusToPoints(currentBonus);
    const totalPoints = getTotalPointsUsed(unitImprovements);
    
    const maxPoints = forgeData.improvement_config?.max_improvement_points_per_unit || 5;
    return currentPoints < maxPoints && totalPoints < maxPoints;
  };

  const canDowngrade = (unitType: string, improvementType: string): boolean => {
    if (!forgeData) return false;
    const currentBonus = forgeData.current_improvements[unitType]?.[improvementType] || 0;
    return currentBonus > 0;
  };

  const getNextUpgradeCost = (unitType: string, improvementType: string): { gold: number; wood: number; stone: number; iron: number } | null => {
    if (!forgeData || !canUpgrade(unitType, improvementType)) return null;
    
    const unitImprovements = forgeData.current_improvements[unitType] || {};
    const currentBonus = unitImprovements[improvementType] || 0;
    const currentPoints = bonusToPoints(currentBonus);
    const nextLevel = currentPoints + 1;
    
    const costs = forgeData.upgrade_costs[nextLevel.toString()];
    if (!costs) return null;
    
    return {
      gold: costs.gold || 0,
      wood: costs.wood || 0,
      stone: costs.stone || 0,
      iron: costs.iron || 0
    };
  };

  const handleUpgrade = async (unitType: string, improvementType: string) => {
    if (!user?.id) return;

    try {
      const response = await fetch('/api/unit-improvements/upgrade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_id: user.id,
          unit_type: unitType,
          improvement_type: improvementType
        })
      });

      const result = await response.json();
      if (result.success) {
        await loadData();
        onCityDataChange?.();
      } else {
        setError(result.message || 'Erreur lors de l\'amélioration');
      }
    } catch (err) {
      console.error('Erreur upgrade:', err);
      setError('Impossible d\'effectuer l\'amélioration');
    }
  };

  const handleDowngrade = async (unitType: string, improvementType: string) => {
    if (!user?.id) return;

    try {
      const response = await fetch('/api/unit-improvements/downgrade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_id: user.id,
          unit_type: unitType,
          improvement_type: improvementType
        })
      });

      const result = await response.json();
      if (result.success) {
        await loadData();
        onCityDataChange?.();
      } else {
        setError(result.message || 'Erreur lors de la réduction');
      }
    } catch (err) {
      console.error('Erreur downgrade:', err);
      setError('Impossible d\'effectuer la réduction');
    }
  };

  if (loading) {
    return (
      <div className="forge-popup-overlay">
        <div className="forge-popup-content">
          <div className="loading">🔄 Chargement de la forge...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="forge-popup-overlay">
        <div className="forge-popup-content">
          <div className="error">❌ {error}</div>
          <button onClick={onClose} className="close-button">Fermer</button>
        </div>
      </div>
    );
  }

  if (!forgeData || !config) {
    return null;
  }

  // Fonction pour rendre la vue de sélection des unités
  const renderUnitSelection = () => (
    <div className="unit-selection-view">
      <div className="forge-info">
        <p><strong>Forge niveau {forgeData.forge_level}</strong> - Niveau d'amélioration max: {forgeData.max_improvement_level}</p>
        <p><strong>Unités disponibles :</strong> Sélectionnez une unité pour voir ses caractéristiques et améliorations</p>
      </div>

      <div className="available-units-grid">
        {forgeData.available_units.map(unitType => {
          const unitStats = forgeData.base_stats[unitType];
          const unitImprovements = forgeData.current_improvements[unitType] || {};
          const hasImprovements = Object.keys(unitImprovements).length > 0;
          const totalPointsUsed = getTotalPointsUsed(unitImprovements);

          return (
            <div 
              key={unitType}
              className={`unit-selection-card ${hasImprovements ? 'improved' : ''}`}
              onClick={() => setSelectedUnit(unitType)}
            >
              <div className="unit-icon">
                {unitNames[unitType]?.split(' ')[0] || '⚔️'}
              </div>
              <div className="unit-name">
                {unitNames[unitType]?.substring(2) || unitType}
              </div>
              {hasImprovements && (
                <div className="improvement-indicator">
                  ⭐ {totalPointsUsed}/{forgeData.improvement_config.max_improvement_points_per_unit} pts
                </div>
              )}
              <div className="unit-base-stats">
                <div className="stat-mini">⚔️ {unitStats?.attack_melee || 0}</div>
                <div className="stat-mini">🛡️ {unitStats?.defense_melee || 0}</div>
                <div className="stat-mini">🏹 {unitStats?.attack_ranged || 0}</div>
                <div className="stat-mini">🛡️ {unitStats?.defense_ranged || 0}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  // Fonction pour rendre la vue de détail d'une unité
  const renderUnitDetails = () => {
    if (!selectedUnit || !forgeData.base_stats[selectedUnit]) return null;

    const unitStats = forgeData.base_stats[selectedUnit];
    const enhancedStats = forgeData.enhanced_stats[selectedUnit];
    const unitImprovements = forgeData.current_improvements[selectedUnit] || {};
    const totalPointsUsed = getTotalPointsUsed(unitImprovements);

    return (
      <div className="unit-details-view">
        <div className="unit-details-header">
          <button 
            onClick={() => setSelectedUnit(null)}
            className="back-button"
          >
            ← Retour
          </button>
          <h3>{unitNames[selectedUnit] || selectedUnit}</h3>
          <div className="points-counter">
            Points: {totalPointsUsed}/{forgeData.improvement_config.max_improvement_points_per_unit}
          </div>
        </div>

        <div className="forge-config-info">
          <p><strong>Système d'amélioration :</strong> Maximum {forgeData.improvement_config.max_improvement_points_per_unit} points par unité</p>
          <p><strong>Bonus par niveau :</strong> {forgeData.improvement_config.bonus_progression.map((bonus, index) => `Niv.${index + 1}=+${bonus}%`).join(', ')}</p>
        </div>

        <div className="unit-stats-section">
          <h4>📊 Caractéristiques de base</h4>
          <div className="stats-grid">
            {Object.entries(unitStats).map(([statName, baseValue]) => {
              const enhanced = enhancedStats?.[statName];
              const currentBonus = unitImprovements[statName] || 0;

              // Filtrer les stats qui ne changent pas (health et movement ne sont pas améliorables)
              const isImprovableStat = forgeData.available_improvements[selectedUnit]?.includes(statName);
              if (!isImprovableStat && currentBonus === 0) {
                return null; // Ne pas afficher les stats non améliorables sans bonus
              }

              return (
                <div key={statName} className="stat-item">
                  <span className="stat-name">
                    {improvementNames[statName] || statName}
                  </span>
                  <span className="stat-values">
                    {typeof baseValue === 'number' ? baseValue.toFixed(1) : baseValue} → {
                      enhanced?.enhanced !== undefined ? 
                        (typeof enhanced.enhanced === 'number' ? enhanced.enhanced.toFixed(1) : enhanced.enhanced) : 
                        (typeof baseValue === 'number' ? baseValue.toFixed(1) : baseValue)
                    }
                    {currentBonus > 0 && <span className="bonus"> (+{currentBonus}%)</span>}
                  </span>
                </div>
              );
            }).filter(Boolean)}
          </div>
        </div>

        <div className="unit-improvements-section">
          <h4>⚡ Améliorations disponibles</h4>
          <div className="improvements-list">
            {forgeData.available_improvements[selectedUnit]?.map(improvementType => {
              const currentBonus = unitImprovements[improvementType] || 0;
              const currentPoints = bonusToPoints(currentBonus);
              const upgradeCost = getNextUpgradeCost(selectedUnit, improvementType);

              return (
                <div key={improvementType} className="improvement-item">
                  <div className="improvement-info">
                    <span className="improvement-name">
                      {improvementNames[improvementType]}
                    </span>
                    <span className="improvement-value">
                      +{currentBonus}% ({currentPoints} pts)
                    </span>
                    {upgradeCost && (
                      <span className="upgrade-cost">
                        Coût: {upgradeCost.gold}{getResourceEmoji('gold')} {upgradeCost.wood}{getResourceEmoji('wood')} {upgradeCost.stone}{getResourceEmoji('stone')} {upgradeCost.iron}{getResourceEmoji('iron')}
                      </span>
                    )}
                  </div>
                  
                  <div className="improvement-controls">
                    <button
                      onClick={() => handleDowngrade(selectedUnit, improvementType)}
                      disabled={!canDowngrade(selectedUnit, improvementType)}
                      className="btn-downgrade"
                      title="Réduire"
                    >
                      ▼
                    </button>
                    
                    <button
                      onClick={() => handleUpgrade(selectedUnit, improvementType)}
                      disabled={!canUpgrade(selectedUnit, improvementType)}
                      className="btn-upgrade"
                      title="Améliorer"
                    >
                      ▲
                    </button>
                  </div>
                </div>
              );
            }) || []}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="forge-popup-overlay">
      <div className="forge-popup-content">
        <div className="forge-header">
          <div className="forge-title">
            <h2>🔨 {building.name}</h2>
            <p>Ville de {city.name}</p>
          </div>
          <button onClick={onClose} className="close-button">✕</button>
        </div>

        {selectedUnit ? renderUnitDetails() : renderUnitSelection()}
      </div>
    </div>
  );
};

export default ForgePopupContent;