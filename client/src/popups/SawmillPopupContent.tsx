import React from 'react';
import { CityBuilding, City } from '../types';
import { useProductionBuilding } from '../hooks/city/useProductionBuilding';
// Import supprimé : ProductionBuildingPopup.css obsolète

interface SawmillPopupContentProps {
  city: City;
  building: CityBuilding;
  onClose: () => void;
  onCityDataChange?: () => void;
}

const SawmillPopupContent: React.FC<SawmillPopupContentProps> = ({
  city,
  building,
  onClose,
  onCityDataChange,
}) => {
  const {
    production,
    loading,
    error,
    currentBonus,
    nextLevelBonus,
    canUpgrade,
    getBonusForLevel,
    upgradeBuilding
  } = useProductionBuilding({
    cityId: city.id,
    building,
    resourceType: 'wood',
    buildingType: 'sawmill'
  });

  const handleUpgrade = async () => {
    const success = await upgradeBuilding();
    if (success && onCityDataChange) {
      onCityDataChange();
    }
  };

  const buildingLevel = building?.level || 1;

  return (
    <div className="popup-content">
      <h3 className="popup-title">🪚 Scierie - Niveau {buildingLevel}</h3>
      
      {/* Bonus de production actuel */}
      <div className="popup-section highlight">
        <div className="popup-section-title">
          🌲 Bonus de production du bois
        </div>
        <div className="popup-section-subtitle">
          +{production.bonus}% de bonus appliqué à cette ville
        </div>
      </div>

      {/* Détails de production */}
      <div className="popup-section info">
        <div className="popup-section-title">📊 Production détaillée</div>
        <div className="popup-stats-grid">
          <div>🔥 Production de base: <strong>{production.baseProduction.toFixed(1)}/sec</strong></div>
          <div>⚡ Bonus Scierie: <strong>+{production.bonus}%</strong></div>
          <div>🎯 Production totale: <strong>{production.totalProduction.toFixed(1)}/sec</strong></div>
          <div>📈 Production/heure: <strong>{production.hourlyProduction.toLocaleString()}</strong></div>
        </div>
      </div>

      {/* Comparaison des niveaux */}
      <div className="popup-section warning">
        <div className="popup-section-title">🔄 Niveaux de la Scierie</div>
        <div className="popup-levels-comparison">
          {[1, 2, 3].map(level => {
            const bonus = getBonusForLevel(level);
            const isCurrentLevel = level === buildingLevel;
            const baseProduction = 10.0;
            const levelProduction = baseProduction * (1 + bonus / 100.0);
            
            return (
              <div 
                key={level} 
                className={`popup-level-item ${isCurrentLevel ? 'current' : ''}`}
              >
                <div className="popup-level-header">
                  Niveau {level} {isCurrentLevel && '(Actuel)'}
                </div>
                <div className="popup-level-details">
                  • Bonus: +{bonus}%<br/>
                  • Production: {levelProduction.toFixed(1)}/sec<br/>
                  • Gain/heure: {(levelProduction * 3600).toLocaleString()}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Amélioration */}
      {canUpgrade && (
        <div className="popup-section success">
          <div className="popup-section-title">⬆️ Amélioration disponible</div>
          <div className="popup-upgrade-info">
            <div>Passer au niveau {buildingLevel + 1} :</div>
            <div>• Bonus: +{currentBonus}% → +{nextLevelBonus}%</div>
            <div>• Production: {production.totalProduction.toFixed(1)}/sec → {(production.baseProduction * (1 + nextLevelBonus / 100.0)).toFixed(1)}/sec</div>
          </div>
          
          <button
            onClick={handleUpgrade}
            disabled={loading}
            className="popup-action-button primary"
          >
            {loading ? 'Amélioration...' : `Améliorer (Niveau ${buildingLevel + 1})`}
          </button>
        </div>
      )}

      {!canUpgrade && (
        <div className="popup-section success">
          <div className="popup-section-title">🏆 Niveau Maximum</div>
          <div>Cette Scierie est au niveau maximum et produit le bonus optimal de +{currentBonus}%</div>
        </div>
      )}

      {error && (
        <div className="popup-section error">
          <div className="popup-error-message">
            ⚠️ {error}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="popup-actions">
        <button
          onClick={onClose}
          className="popup-action-button secondary"
        >
          Fermer
        </button>
      </div>
    </div>
  );
};

export default SawmillPopupContent;
