import React from 'react';
import '../styles/UnitDetailPopup.css';

interface UnitStats {
  name: string;
  category: string;
  hp: number;
  attack_melee: number;
  defense_melee: number;
  attack_ranged: number;
  defense_ranged: number;
  range: number;
  movement: number;
  weight: number;
  food_consumption: number;
  gold_cost_per_hour: number;
  max_stack_size: number;
  production_cost: {
    wood?: number;
    stone?: number;
    iron?: number;
    horse?: number;
    population?: number;
    gunpowder?: number;
    gold?: number;
  };
  production_time: number;
  description?: string;
}

interface UnitDetailPopupProps {
  isOpen: boolean;
  onClose: () => void;
  unit: UnitStats;
  unitType: string;
  allUnits?: Array<[string, UnitStats]>;
  onUnitChange?: (unitType: string) => void;
}

const UnitDetailPopup: React.FC<UnitDetailPopupProps> = ({ isOpen, onClose, unit, unitType, allUnits, onUnitChange }) => {
  if (!isOpen) return null;

  const getCategoryName = (category: string): string => {
    const categories: Record<string, string> = {
      infantry: 'Infanterie',
      ranged: 'Distance',
      cavalry: 'Cavalerie',
      artillery: 'Artillerie',
      siege: 'Siège',
      support: 'Support'
    };
    return categories[category] || category;
  };

  return (
    <div className="unit-detail-overlay" onClick={onClose}>
      <div className="unit-detail-popup" onClick={(e) => e.stopPropagation()}>
        <button className="close-button" onClick={onClose}>✕</button>
        
        {/* Barre d'icônes d'unités en haut */}
        {allUnits && allUnits.length > 0 && (
          <div className="unit-icons-bar">
            {allUnits.map(([uType, u]) => (
              <div 
                key={uType}
                className={`unit-icon-mini ${uType === unitType ? 'active' : ''}`}
                onClick={() => onUnitChange && onUnitChange(uType)}
                title={u.name}
              >
                <img 
                  src={`/assets/units/${uType}.png`}
                  alt={u.name}
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/assets/units/default.png';
                  }}
                />
              </div>
            ))}
          </div>
        )}
        
        <div className="unit-detail-content">
          {/* Partie gauche: Titre, Image et coûts */}
          <div className="unit-detail-left">
            <h2 className="unit-detail-name-left">{unit.name}</h2>
            <p className="unit-detail-category-left">{getCategoryName(unit.category)}</p>
            
            <div className="unit-detail-image">
              <img 
                src={`/assets/units/${unitType}.png`}
                alt={unit.name}
                onError={(e) => {
                  (e.target as HTMLImageElement).src = '/assets/units/default.png';
                }}
              />
            </div>
            
            <div className="unit-detail-costs">
              <h3>Coût de production</h3>
              <div className="detail-costs-grid">
                {unit.production_cost.population && (
                  <div className="detail-cost-item">
                    <span className="cost-icon">👥</span>
                    <span className="cost-value">{unit.production_cost.population}</span>
                  </div>
                )}
                {unit.production_cost.wood && (
                  <div className="detail-cost-item">
                    <span className="cost-icon">🪵</span>
                    <span className="cost-value">{unit.production_cost.wood}</span>
                  </div>
                )}
                {unit.production_cost.stone && (
                  <div className="detail-cost-item">
                    <span className="cost-icon">🪨</span>
                    <span className="cost-value">{unit.production_cost.stone}</span>
                  </div>
                )}
                {unit.production_cost.iron && (
                  <div className="detail-cost-item">
                    <span className="cost-icon">⚙️</span>
                    <span className="cost-value">{unit.production_cost.iron}</span>
                  </div>
                )}
                {unit.production_cost.horse && (
                  <div className="detail-cost-item">
                    <span className="cost-icon">🐎</span>
                    <span className="cost-value">{unit.production_cost.horse}</span>
                  </div>
                )}
                {unit.production_cost.gunpowder && (
                  <div className="detail-cost-item">
                    <span className="cost-icon">💣</span>
                    <span className="cost-value">{unit.production_cost.gunpowder}</span>
                  </div>
                )}
                {unit.production_cost.gold && (
                  <div className="detail-cost-item">
                    <span className="cost-icon">💰</span>
                    <span className="cost-value">{unit.production_cost.gold}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Partie droite: Stats et description */}
          <div className="unit-detail-right">
            <div className="unit-stats-grid">
              <div className="stat-row">
                <span className="stat-label">Points de vie:</span>
                <span className="stat-value">{unit.hp}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Attaque au corps à corps:</span>
                <span className="stat-value">{unit.attack_melee}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Défense au corps à corps:</span>
                <span className="stat-value">{unit.defense_melee}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Attaque à distance:</span>
                <span className="stat-value">{unit.attack_ranged}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Défense à distance:</span>
                <span className="stat-value">{unit.defense_ranged}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Portée:</span>
                <span className="stat-value">{unit.range}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Déplacement:</span>
                <span className="stat-value">{unit.movement}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Poids:</span>
                <span className="stat-value">{unit.weight}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Consommation:</span>
                <span className="stat-value">{unit.food_consumption} nourriture/h</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Coût d'entretien:</span>
                <span className="stat-value">{unit.gold_cost_per_hour} or/h</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Taille de stack max:</span>
                <span className="stat-value">{unit.max_stack_size}</span>
              </div>
            </div>

            {unit.description && (
              <div className="unit-description">
                <h3>Description</h3>
                <p>{unit.description}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UnitDetailPopup;
