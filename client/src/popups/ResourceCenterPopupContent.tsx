import React from 'react';
import { CityBuilding, City } from '../types';
import { useMultiResourceBuilding } from '../hooks/city/useMultiResourceBuilding';
// Import supprimé : ProductionBuildingPopup.css obsolète

interface ResourceCenterPopupContentProps {
  city: City;
  building: CityBuilding;
  onClose: () => void;
  onCityDataChange?: () => void;
}

const ResourceCenterPopupContent: React.FC<ResourceCenterPopupContentProps> = ({
  city,
  building,
  onClose,
  onCityDataChange,
}) => {
  // Ressources affectées par le Centre de Ressources
  const affectedResources = [
    { key: 'stone', name: 'Pierre', icon: '🪨' },
    { key: 'iron', name: 'Fer', icon: '⚙️' },
    { key: 'cereal', name: 'Céréales', icon: '🌾' },
    { key: 'papyrus', name: 'Papyrus', icon: '📜' }
  ];

  const {
    productionData,
    loading,
    error,
    currentBonus,
    nextLevelBonus,
    canUpgrade,
    getBonusForLevel,
    upgradeBuilding
  } = useMultiResourceBuilding({
    cityId: city.id,
    building,
    buildingType: 'resource_center',
    resources: affectedResources
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
      <h3 className="popup-title">🏭 Centre de Ressources - Niveau {buildingLevel}</h3>
      
      {/* Bonus de production actuel */}
      <div className="popup-section highlight">
        <div className="popup-section-title">
          ⚡ Bonus de production multi-ressources
        </div>
        <div className="popup-section-subtitle">
          +{currentBonus}% de bonus appliqué à toutes les ressources de base
        </div>
      </div>

      {/* Production détaillée par ressource */}
      <div className="popup-section info">
        <div className="popup-section-title">📊 Production par ressource</div>
        <div className="popup-resources-grid">
          {affectedResources.map(resource => {
            const data = productionData[resource.key];
            if (!data) return null;
            
            return (
              <div key={resource.key} className="popup-resource-item">
                <div className="popup-resource-header">
                  {resource.icon} {resource.name}
                </div>
                <div className="popup-resource-details">
                  {data.baseProduction > 0 ? (
                    <>
                      <div>Base: {data.baseProduction.toFixed(1)}/sec</div>
                      <div>Bonus: +{data.bonus}%</div>
                      <div>Total: <strong>{data.totalProduction.toFixed(1)}/sec</strong></div>
                      <div>Par heure: <strong>{data.hourlyProduction.toLocaleString()}</strong></div>
                    </>
                  ) : (
                    <>
                      <div>Bonus: +{data.bonus}%</div>
                      <div><em>Assignez des ouvriers aux sites de {resource.name.toLowerCase()} pour voir la production</em></div>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Comparaison des niveaux */}
      <div className="popup-section warning">
        <div className="popup-section-title">🔄 Niveaux du Centre de Ressources</div>
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
                  • Bonus: +{bonus}% sur toutes les ressources<br/>
                  • Production exemple: {levelProduction.toFixed(1)}/sec<br/>
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
            <div>• Amélioration sur toutes les ressources de base</div>
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
          <div>Ce Centre de Ressources est au niveau maximum et produit le bonus optimal de +{currentBonus}% sur toutes les ressources</div>
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

export default ResourceCenterPopupContent;
