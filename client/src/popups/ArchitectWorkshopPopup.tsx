import React, { useState, useEffect } from 'react';
import '../styles/popups.css';

interface ArchitectWorkshopPopupProps {
  building: {
    name: string;
    level: number;
    status: string;
  };
  city: {
    id: string;
    name: string;
  };
  onClose: () => void;
  onCityDataChange: () => Promise<void>;
  onDevelop: () => Promise<void>;
  onDestroy: () => Promise<void>;
}

interface ArchitectBonuses {
  cost_reduction: number;
  time_reduction: number;
}

interface BuildingCost {
  base_cost: Record<string, number>;
  actual_cost: Record<string, number>;
  base_construction_time: number;
  actual_construction_time: number;
  savings: Record<string, number>;
  time_saved: number;
}

const ArchitectWorkshopPopup: React.FC<ArchitectWorkshopPopupProps> = ({
  building,
  city,
  onClose,
  onCityDataChange,
  onDevelop,
  onDestroy,
}) => {
  const [bonuses, setBonuses] = useState<ArchitectBonuses>({ cost_reduction: 0, time_reduction: 0 });
  const [buildingCosts, setBuildingCosts] = useState<Record<string, BuildingCost>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadArchitectData = async () => {
      try {
        setLoading(true);
        
        // Charger les bonus actuels de l'architecte
        const bonusRes = await fetch(`/api/city/${city.id}/architect-bonuses`);
        if (bonusRes.ok) {
          const bonusData = await bonusRes.json();
          setBonuses(bonusData);
        }

        // Charger les coûts des bâtiments avec bonus architecte
        const costsRes = await fetch(`/api/city/${city.id}/building-costs`);
        if (costsRes.ok) {
          const costsData = await costsRes.json();
          setBuildingCosts(costsData.buildings || {});
        }
      } catch (error) {
        console.error('Erreur lors du chargement des données architecte:', error);
      } finally {
        setLoading(false);
      }
    };

    loadArchitectData();
  }, [city.id, building.level]);

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const formatResource = (resource: string, amount: number) => (
    <span key={resource} className="popup-cost-item">
      <img src={`/assets/icons/${resource}.png`} alt={resource} className="popup-cost-icon" />
      {amount}
    </span>
  );

  const renderBonusSection = () => (
    <div className="architect-bonus-grid">
      <div className="architect-bonus-card">
        <div className="architect-bonus-title">Réduction des coûts</div>
        <div className="architect-bonus-value">-{(bonuses.cost_reduction * 100).toFixed(0)}%</div>
        <div className="architect-bonus-description">
          Les coûts de construction de tous les bâtiments sont réduits
        </div>
      </div>
      <div className="architect-bonus-card">
        <div className="architect-bonus-title">Réduction du temps</div>
        <div className="architect-bonus-value">-{(bonuses.time_reduction * 100).toFixed(0)}%</div>
        <div className="architect-bonus-description">
          Le temps de construction de tous les bâtiments est réduit
        </div>
      </div>
    </div>
  );

  const renderSavingsPreview = () => {
    const relevantBuildings = Object.entries(buildingCosts)
      .filter(([_, cost]) => Object.keys(cost.savings).length > 0 || cost.time_saved > 0)
      .slice(0, 6);

    if (relevantBuildings.length === 0) {
      return (
        <div className="architect-no-savings">
          Aucune économie détectée pour les bâtiments actuellement disponibles
        </div>
      );
    }

    return (
      <div className="architect-savings-grid">
        {relevantBuildings.map(([buildingName, cost]) => (
          <div key={buildingName} className="architect-savings-item">
            <div className="architect-savings-building">{buildingName}</div>
            <div className="architect-savings-cost">
              {Object.entries(cost.savings).map(([resource, amount]) => (
                <span key={resource}>
                  <img src={`/assets/icons/${resource}.png`} alt={resource} style={{width: 12}} />
                  -{amount}
                </span>
              ))}
            </div>
            {cost.time_saved > 0 && (
              <div className="architect-savings-time">-{formatTime(cost.time_saved)}</div>
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderLevelComparison = () => {
    const currentLevel = building.level || 1;
    const nextLevel = currentLevel + 1;

    // Bonus approximatifs par niveau (peut être ajusté selon la configuration)
    const currentCostReduction = currentLevel * 10;
    const currentTimeReduction = currentLevel * 10;
    const nextCostReduction = nextLevel * 10;
    const nextTimeReduction = nextLevel * 10;

    return (
      <div className="architect-level-comparison">
        <div className="architect-comparison-header">Comparaison des niveaux</div>
        <div className="architect-comparison-grid">
          <div className="architect-comparison-row">
            <div className="architect-comparison-cell label">Bonus</div>
            <div className="architect-comparison-cell">Actuel (Niv. {currentLevel})</div>
            <div className="architect-comparison-cell">Prochain (Niv. {nextLevel})</div>
            <div className="architect-comparison-cell">Gain</div>
          </div>
          <div className="architect-comparison-row">
            <div className="architect-comparison-cell label">Réduction coûts</div>
            <div className="architect-comparison-cell current">-{currentCostReduction}%</div>
            <div className="architect-comparison-cell next">-{nextCostReduction}%</div>
            <div className="architect-comparison-cell">+{nextCostReduction - currentCostReduction}%</div>
          </div>
          <div className="architect-comparison-row">
            <div className="architect-comparison-cell label">Réduction temps</div>
            <div className="architect-comparison-cell current">-{currentTimeReduction}%</div>
            <div className="architect-comparison-cell next">-{nextTimeReduction}%</div>
            <div className="architect-comparison-cell">+{nextTimeReduction - currentTimeReduction}%</div>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="popup-overlay" onClick={onClose}>
        <div className="popup-base architect-workshop-popup" onClick={(e) => e.stopPropagation()}>
          <button className="popup-close-button" onClick={onClose}>×</button>
          <div className="popup-content">
            <div style={{ textAlign: 'center', padding: '20px' }}>
              Chargement des données de l'Atelier d'Architecte...
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="popup-overlay" onClick={onClose}>
      <div className="popup-base architect-workshop-popup" onClick={(e) => e.stopPropagation()}>
        <button className="popup-close-button" onClick={onClose}>×</button>
        
        <div className="popup-header">
          <img 
            src="/assets/buildings/architect_workshop.png" 
            alt="Atelier d'Architecte" 
            className="popup-image"
          />
          <div className="popup-info">
            <div className="popup-title">Atelier d'Architecte</div>
            <div className="popup-level">Niveau {building.level}</div>
            <div className="popup-description">
              L'Atelier d'Architecte réduit les coûts et temps de construction de tous vos bâtiments
            </div>
          </div>
        </div>

        <div className="popup-content">
          {renderBonusSection()}

          <div className="architect-savings-section">
            <div className="architect-savings-title">
              💰 Aperçu des économies actuelles
            </div>
            {renderSavingsPreview()}
          </div>

          {renderLevelComparison()}
        </div>

        <div className="popup-buttons">
          <button 
            className="popup-button" 
            onClick={onDevelop}
            disabled={building.status === 'en_construction'}
          >
            {building.status === 'en_construction' ? 'En construction...' : 'Développer'}
          </button>
          <button 
            className="popup-button destroy" 
            onClick={onDestroy}
            disabled={building.status === 'en_construction'}
          >
            {building.level > 1 
              ? `Rétrograder (niveau ${building.level} → ${building.level - 1})` 
              : "Détruire définitivement"
            }
          </button>
        </div>
      </div>
    </div>
  );
};

export default ArchitectWorkshopPopup;
