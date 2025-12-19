import React, { useState, useEffect } from 'react';
import './PopulationManagementPopup.css';

interface PopulationManagementPopupProps {
  cityId: string;
  cityName: string;
  onClose: () => void;
}

interface PopulationData {
  population_total: number;
  population_free: number;
  max_capacity: number;
  workers_assigned: {
    [key: string]: number;
  };
  island_info?: {
    base_resource: string;
    advanced_resource: string;
  };
}

const PopulationManagementPopup: React.FC<PopulationManagementPopupProps> = ({
  cityId,
  cityName,
  onClose,
}) => {
  const [populationData, setPopulationData] = useState<PopulationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPopulationData();
  }, [cityId]);

  const fetchPopulationData = async () => {
    try {
      setLoading(true);
      
      // Récupérer les données de population détaillées
      const populationResponse = await fetch(`/api/city/${cityId}/population`);
      if (!populationResponse.ok) {
        throw new Error(`Erreur ${populationResponse.status}: ${populationResponse.statusText}`);
      }
      const populationData = await populationResponse.json();
      
      // Récupérer les données complètes de la ville pour workers_assigned et island_info
      const cityResponse = await fetch(`/api/city/${cityId}/state`);
      if (!cityResponse.ok) {
        throw new Error(`Erreur ${cityResponse.status}: ${cityResponse.statusText}`);
      }
      const cityData = await cityResponse.json();
      
      // Combiner les données
      const populationInfo = {
        population_total: populationData.info?.current_population || 0,
        population_free: populationData.population_free || 0,
        max_capacity: populationData.info?.max_capacity || 0,
        workers_assigned: cityData.workers_assigned || {},
        island_info: cityData.island_info || {}
      };
      
      setPopulationData(populationInfo);
      setError(null);
    } catch (err) {
      console.error('Erreur lors du chargement des données de population:', err);
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    } finally {
      setLoading(false);
    }
  };

  const getResourceDisplayName = (resourceKey: string): string => {
    const translations: { [key: string]: string } = {
      'academy': 'Académie',
      'wood': 'Forêt',
      'stone': 'Carrière de pierre',
      'iron': 'Mine de fer',
      'cereal': 'Ferme de céréales',
      'glass': 'Verrerie',
      'marble': 'Carrière de marbre',
      'crystal': 'Mine de cristal'
    };
    return translations[resourceKey] || resourceKey;
  };

  if (loading) {
    return (
      <div className="population-popup-overlay">
        <div className="population-popup">
          <div className="population-popup-header">
            <h2>Gestion de la population - {cityName}</h2>
            <button className="close-button" onClick={onClose}>×</button>
          </div>
          <div className="population-popup-content">
            <div className="loading">Chargement des données de population...</div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="population-popup-overlay">
        <div className="population-popup">
          <div className="population-popup-header">
            <h2>Gestion de la population - {cityName}</h2>
            <button className="close-button" onClick={onClose}>×</button>
          </div>
          <div className="population-popup-content">
            <div className="error">Erreur: {error}</div>
            <button onClick={fetchPopulationData} className="retry-button">
              Réessayer
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!populationData) {
    return null;
  }

  const totalAssigned = Object.values(populationData.workers_assigned).reduce((sum, workers) => sum + workers, 0);
  const actualFreePopulation = Math.max(0, populationData.population_total - totalAssigned);

  return (
    <div className="population-popup-overlay">
      <div className="population-popup">
        <div className="population-popup-header">
          <h2>Gestion de la population - {cityName}</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        
        <div className="population-popup-content">
          {/* Résumé de la population */}
          <div className="population-summary">
            <h3>📊 Résumé de la population</h3>
            <div className="summary-grid">
              <div className="summary-item">
                <span className="summary-label">Capacité maximale :</span>
                <span className="summary-value">{Math.floor(populationData.max_capacity)}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Population actuelle :</span>
                <span className="summary-value">{Math.floor(populationData.population_total)}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Population libre :</span>
                <span className="summary-value free-population">{Math.floor(actualFreePopulation)}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Population affectée :</span>
                <span className="summary-value">{Math.floor(totalAssigned)}</span>
              </div>
            </div>
          </div>

          {/* Détail des affectations */}
          <div className="population-assignments">
            <h3>👥 Répartition par secteur</h3>
            <div className="assignments-list">
              {Object.entries(populationData.workers_assigned).map(([resource, workers]) => (
                <div key={resource} className="assignment-item">
                  <span className="assignment-resource">
                    • {getResourceDisplayName(resource)} :
                  </span>
                  <span className="assignment-workers">
                    {Math.floor(workers)} habitant{workers > 1 ? 's' : ''}
                  </span>
                </div>
              ))}
              
              {Object.keys(populationData.workers_assigned).length === 0 && (
                <div className="no-assignments">
                  Aucune population affectée actuellement
                </div>
              )}
            </div>
          </div>

          {/* Informations sur l'île */}
          {populationData.island_info && (
            <div className="island-info">
              <h3>🏝️ Ressources de l'île</h3>
              <div className="island-resources">
                {populationData.island_info.base_resource && (
                  <div className="island-resource">
                    <span>Ressource de base : </span>
                    <strong>{getResourceDisplayName(populationData.island_info.base_resource)}</strong>
                  </div>
                )}
                {populationData.island_info.advanced_resource && (
                  <div className="island-resource">
                    <span>Ressource avancée : </span>
                    <strong>{getResourceDisplayName(populationData.island_info.advanced_resource)}</strong>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="population-actions">
            <button onClick={onClose} className="close-action-button">
              Fermer
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PopulationManagementPopup;
