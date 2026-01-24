import React, { useEffect, useState } from 'react';
import './MilitaryExpensesPopup.css';
import { getApiUrl } from '../utils/api';

interface MilitaryExpensesPopupProps {
  onClose: () => void;
  playerId: string | null;
}

interface UnitExpense {
  unit_id: string;
  unit_name: string;
  count: number;
  gold_cost_per_hour_each: number;
  total_cost_per_hour: number;
}

interface MilitaryExpensesData {
  total_cost_per_hour: number;
  bonus_reduction_percent: number;
  total_cost_after_bonus: number;
  bonus_sources?: Array<{ source: string; reduction: number }>;
  units: UnitExpense[];
}

const MilitaryExpensesPopup: React.FC<MilitaryExpensesPopupProps> = ({ onClose, playerId }) => {
  const [data, setData] = useState<MilitaryExpensesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!playerId) {
        setError('ID joueur manquant');
        setLoading(false);
        return;
      }

      try {
        const apiUrl = getApiUrl();
        const response = await fetch(`${apiUrl}/api/game/military-expenses?player_id=${playerId}`);
        const result = await response.json();

        if (response.ok) {
          setData(result);
        } else {
          setError(result.error || 'Erreur lors du chargement');
        }
      } catch (err) {
        console.error('Erreur fetch military expenses:', err);
        setError('Erreur réseau');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [playerId]);

  const getUnitImage = (unitId: string) => {
    return (
      <img 
        src={`/assets/units/${unitId}.png`}
        alt={unitId}
        onError={(e) => {
          (e.target as HTMLImageElement).src = '/assets/units/default.png';
        }}
        style={{ width: '40px', height: '40px', objectFit: 'contain' }}
      />
    );
  };

  return (
    <div className="military-expenses-overlay" onClick={onClose}>
      <div className="military-expenses-popup" onClick={(e) => e.stopPropagation()}>
        <div className="military-expenses-header">
          <h2>💰 Dépenses Militaires</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="military-expenses-content">
          {loading && <div className="loading">Chargement...</div>}
          {error && <div className="error">{error}</div>}
          
          {data && (
            <>
              <div className="expenses-summary">
                <div className="summary-item">
                  <span className="summary-label">Coût de base :</span>
                  <span className="summary-value">{data.total_cost_per_hour.toFixed(1)} or/heure</span>
                </div>
                
                {data.bonus_reduction_percent > 0 && (
                  <>
                    <div className="summary-item bonus-detail">
                      <span className="summary-label">Réductions :</span>
                      <div className="bonus-list">
                        {data.bonus_sources && data.bonus_sources.map((bonus, idx) => (
                          <div key={idx} className="bonus-item">
                            <span className="bonus-source">✓ {bonus.source}</span>
                            <span className="bonus-value">-{bonus.reduction}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="summary-item total">
                      <span className="summary-label"><strong>Total après bonus :</strong></span>
                      <span className="summary-value final">{data.total_cost_after_bonus.toFixed(1)} or/heure</span>
                    </div>
                  </>
                )}
                
                {data.bonus_reduction_percent === 0 && (
                  <div className="summary-hint">
                    💡 Débloquez la recherche "Économie Militaire" ou choisissez la faction Fer pour réduire vos coûts !
                  </div>
                )}
              </div>

              <div className="units-list-header">
                <h3>Détail par unité</h3>
              </div>

              <div className="units-table">
                {data.units.length === 0 ? (
                  <div className="no-units">Aucune unité militaire</div>
                ) : (
                  <table>
                    <thead>
                      <tr>
                        <th>Unité</th>
                        <th>Nombre</th>
                        <th>Coût unitaire</th>
                        <th>Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.units.map((unit) => (
                        <tr key={unit.unit_id}>
                          <td className="unit-cell">
                            <span className="unit-icon">{getUnitImage(unit.unit_id)}</span>
                            <span className="unit-name">{unit.unit_name}</span>
                          </td>
                          <td className="number-cell">{unit.count}</td>
                          <td className="number-cell">{unit.gold_cost_per_hour_each} or/h</td>
                          <td className="total-cell">{unit.total_cost_per_hour.toFixed(1)} or/h</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default MilitaryExpensesPopup;
