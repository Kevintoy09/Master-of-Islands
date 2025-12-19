import React, { useState, useEffect } from 'react';
import { PillageService, PillageableResources, PillageResult } from '../services/PillageService';
import './PillagePopup.css';

interface PillagePopupProps {
  isOpen: boolean;
  onClose: () => void;
  battleId: string;
  cityId: string;
  cityName: string;
  attackerShips: number; // Nombre de bateaux utilisés dans l'attaque
  attackerId?: string; // ID de l'attaquant
  onPillageComplete?: (result: PillageResult) => void;
}

const PillagePopup: React.FC<PillagePopupProps> = ({
  isOpen,
  onClose,
  battleId,
  cityId,
  cityName,
  attackerShips,
  attackerId = 'player_2',
  onPillageComplete
}) => {
  const [pillableResources, setPillableResources] = useState<PillageableResources>({});
  const [selectedShips, setSelectedShips] = useState(Math.min(attackerShips, 3)); // Par défaut 3 ou le nombre disponible
  const [preview, setPreview] = useState<PillageResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState<string>('');

  // Charger les données de pillage au montage
  useEffect(() => {
    if (isOpen && cityId) {
      loadPillageData();
    }
  }, [isOpen, cityId]);

  // Mettre à jour l'aperçu quand le nombre de bateaux change
  useEffect(() => {
    if (pillableResources && Object.keys(pillableResources).length > 0) {
      updatePreview();
    }
  }, [selectedShips, pillableResources]);

  const loadPillageData = async () => {
    setLoading(true);
    setError('');
    
    try {
      const data = await PillageService.getPillageData(cityId, attackerId);
      setPillableResources(data);
    } catch (err: any) {
      setError('Erreur lors du chargement des données de pillage: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const updatePreview = () => {
    const result = PillageService.calculatePillageDistribution(pillableResources, selectedShips);
    setPreview(result);
  };

  const handleExecutePillage = async () => {
    if (!preview || preview.totalPillable === 0) {
      setError('Aucune ressource à piller');
      return;
    }

    setExecuting(true);
    setError('');

    try {
      const result = await PillageService.executePillage({
        battleId,
        cityId,
        shipsCount: selectedShips,
        attackerId
      });

      // Notification de succès
      alert(`Pillage réussi ! ${PillageService.formatPillageDisplay(result)}`);
      
      // Callback optionnel
      if (onPillageComplete) {
        onPillageComplete(result);
      }

      onClose();
    } catch (err: any) {
      setError('Erreur lors du pillage: ' + err.message);
    } finally {
      setExecuting(false);
    }
  };



  if (!isOpen) return null;

  return (
    <div className="popup-overlay" onClick={onClose}>
      <div className="popup-base pillage-popup" onClick={(e) => e.stopPropagation()}>
        <button onClick={onClose} className="popup-close-button">×</button>
        
        <div className="pillage-header">
          <h3>💰 Piller {cityName}</h3>
          <div className="pillage-subtitle">
            Victoire remportée ! Vous pouvez maintenant piller les ressources non sécurisées.
          </div>
        </div>

        {error && (
          <div className="pillage-error">
            ⚠️ {error}
          </div>
        )}

        {loading ? (
          <div className="pillage-loading">
            <p>Chargement des données de pillage...</p>
          </div>
        ) : (
          <>
            {/* Configuration du pillage */}
            <div className="pillage-section">
              <h4>🚢 Bateaux de transport</h4>
              <div className="ships-controls">
                <label>
                  Nombre de bateaux à utiliser:
                  <input
                    type="range"
                    min="1"
                    max={attackerShips}
                    value={selectedShips}
                    onChange={(e) => setSelectedShips(parseInt(e.target.value))}
                    className="ships-slider"
                  />
                  <span className="ships-count">{selectedShips} / {attackerShips}</span>
                </label>
              </div>
              <div className="transport-info">
                <small>
                  Capacité de transport: {selectedShips * 500} ressources
                  (500 par bateau)
                </small>
              </div>
            </div>

            {/* Aperçu des ressources pillables */}
            <div className="pillage-section">
              <h4>📦 Ressources disponibles</h4>
              {Object.keys(pillableResources).length === 0 ? (
                <p className="no-resources">Aucune ressource pillable trouvée.</p>
              ) : (
                <div className="pillable-resources-table">
                  <div className="table-header">
                    <div>Ressource</div>
                    <div>Actuel</div>
                    <div>Sécurisé</div>
                    <div>Pillable</div>
                    <div>Tu prendras</div>
                  </div>
                  {Object.entries(pillableResources).map(([resource, data]) => {
                    const willTake = preview?.resourcesPillaged[resource] || 0;
                    return (
                      <div key={resource} className="table-row">
                        <div className="resource-name">
                          {PillageService.getResourceEmoji(resource)}
                        </div>
                        <div>{data.current}</div>
                        <div className="secure-amount">{data.secure}</div>
                        <div className="pillable-amount">{data.pillable}</div>
                        <div className="will-take">
                          <strong>{willTake}</strong>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Résumé du pillage */}
            {preview && preview.totalPillable > 0 && (
              <div className="pillage-section pillage-summary">
                <h4>📊 Résumé du pillage</h4>
                <div className="summary-stats">
                  <div className="stat-item">
                    <span className="stat-label">Total pillable:</span>
                    <span className="stat-value">{preview.totalPillable}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Capacité transport:</span>
                    <span className="stat-value">{preview.transportCapacity}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Efficacité:</span>
                    <span className="stat-value">
                      {Math.round(preview.distributionRatio * 100)}%
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Bateaux utilisés:</span>
                    <span className="stat-value">{preview.shipsUsed}</span>
                  </div>
                </div>
                
                {preview.distributionRatio < 1 && (
                  <div className="distribution-warning">
                    ⚠️ Capacité insuffisante - Distribution proportionnelle appliquée
                  </div>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="pillage-actions">
              <button 
                onClick={onClose} 
                className="btn-cancel"
                disabled={executing}
              >
                Annuler
              </button>
              <button 
                onClick={handleExecutePillage}
                className="btn-pillage"
                disabled={executing || !preview || preview.totalPillable === 0}
              >
                {executing ? '⏳ Pillage...' : '💰 Piller !'}
              </button>
              

            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default PillagePopup;