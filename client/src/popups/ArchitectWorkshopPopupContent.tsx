import React, { useState, useEffect } from 'react';
import './ArchitectWorkshopPopupContent.css';

interface ArchitectWorkshopPopupContentProps {
  building: {
    name: string;
    level: number;
    status?: string;
    slot_id: string;
  };
  city: {
    id: string;
    name: string;
  };
  onClose: () => void;
  onCityDataChange?: () => void;
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

const ArchitectWorkshopPopupContent: React.FC<ArchitectWorkshopPopupContentProps> = ({
  building,
  city,
  onClose,
  onCityDataChange,
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

  const renderBonusSection = () => (
    <div className="architect-bonus-section">
      <h4>🏗️ Bonus actuels</h4>
      <div className="architect-bonus-cards">
        <div className="architect-bonus-card">
          <div className="architect-bonus-icon">💰</div>
          <div className="architect-bonus-content">
            <div className="architect-bonus-title">Coûts</div>
            <div className="architect-bonus-value">-{Math.round(bonuses.cost_reduction)}%</div>
          </div>
        </div>
        <div className="architect-bonus-card">
          <div className="architect-bonus-icon">⏱️</div>
          <div className="architect-bonus-content">
            <div className="architect-bonus-title">Temps</div>
            <div className="architect-bonus-value">-{Math.round(bonuses.time_reduction)}%</div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderSavingsPreview = () => {
    const relevantBuildings = Object.entries(buildingCosts)
      .filter(([_, cost]) => Object.keys(cost.savings).length > 0 || cost.time_saved > 0)
      .slice(0, 4); // Réduire pour mobile

    if (relevantBuildings.length === 0) {
      return (
        <div className="architect-no-savings">
          <div className="architect-empty-icon">📋</div>
          <div>Aucune économie disponible actuellement</div>
        </div>
      );
    }

    return (
      <div className="architect-savings-grid">
        {relevantBuildings.map(([buildingName, cost]) => (
          <div key={buildingName} className="architect-savings-item">
            <div className="architect-savings-building">{buildingName}</div>
            <div className="architect-savings-details">
              {Object.entries(cost.savings).length > 0 && (
                <div className="architect-savings-cost">
                  {Object.entries(cost.savings).slice(0, 2).map(([resource, amount]) => (
                    <span key={resource} className="architect-savings-resource">
                      <img src={`/assets/icons/${resource}.png`} alt={resource} />
                      -{amount}
                    </span>
                  ))}
                  {Object.entries(cost.savings).length > 2 && (
                    <span className="architect-savings-more">+{Object.entries(cost.savings).length - 2}</span>
                  )}
                </div>
              )}
              {cost.time_saved > 0 && (
                <div className="architect-savings-time">⏱️ -{formatTime(cost.time_saved)}</div>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderLevelComparison = () => {
    const currentLevel = building.level || 1;
    const nextLevel = currentLevel + 1;

    // Bonus approximatifs par niveau
    const currentCostReduction = currentLevel * 10;
    const currentTimeReduction = currentLevel * 10;
    const nextCostReduction = nextLevel * 10;
    const nextTimeReduction = nextLevel * 10;

    return (
      <div className="architect-level-section">
        <h4>📈 Évolution des bonus</h4>
        <div className="architect-level-comparison">
          <div className="architect-level-row architect-level-header">
            <div className="architect-level-cell">Bonus</div>
            <div className="architect-level-cell">Niv. {currentLevel}</div>
            <div className="architect-level-cell">Niv. {nextLevel}</div>
            <div className="architect-level-cell">Gain</div>
          </div>
          <div className="architect-level-row">
            <div className="architect-level-cell">💰 Coûts</div>
            <div className="architect-level-cell current">-{currentCostReduction}%</div>
            <div className="architect-level-cell next">-{nextCostReduction}%</div>
            <div className="architect-level-cell gain">+{nextCostReduction - currentCostReduction}%</div>
          </div>
          <div className="architect-level-row">
            <div className="architect-level-cell">⏱️ Temps</div>
            <div className="architect-level-cell current">-{currentTimeReduction}%</div>
            <div className="architect-level-cell next">-{nextTimeReduction}%</div>
            <div className="architect-level-cell gain">+{nextTimeReduction - currentTimeReduction}%</div>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="architect-loading">
        <div className="architect-loading-spinner">⚙️</div>
        <div>Chargement des données d'architecture...</div>
      </div>
    );
  }

  return (
    <div className="architect-content">
      <div className="architect-description">
        <p>🏗️ L'Atelier d'Architecte optimise tous vos projets de construction en réduisant les coûts et délais.</p>
      </div>

      {renderBonusSection()}

      <div className="architect-savings-section">
        <h4>💡 Aperçu des économies</h4>
        {renderSavingsPreview()}
      </div>

      {renderLevelComparison()}
    </div>
  );
};

export default ArchitectWorkshopPopupContent;
