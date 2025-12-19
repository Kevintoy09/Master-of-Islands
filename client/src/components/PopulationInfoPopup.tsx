import React, { useState, useEffect } from 'react';
import { getUIEmoji } from '../constants/resourceIcons';
import './PopulationInfoPopup.css';

interface PopulationInfoPopupProps {
  cityId: string;
  cityName: string;
  onClose: () => void;
}

interface PopulationInfo {
  population_total: number;
  population_free: number;
  max_capacity: number;
  workers_assigned: {
    [key: string]: number;
  };
  growth_rate?: number;
  satisfaction?: number;
}

const PopulationInfoPopup: React.FC<PopulationInfoPopupProps> = ({
  cityId,
  cityName,
  onClose
}) => {
  const [populationInfo, setPopulationInfo] = useState<PopulationInfo>({
    population_total: 0,
    population_free: 0,
    max_capacity: 0,
    workers_assigned: {},
    growth_rate: 0,
    satisfaction: 50
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Charger les informations de population
  useEffect(() => {
    loadPopulationInfo();
  }, [cityId]);

  const loadPopulationInfo = async () => {
    if (!cityId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      
      // Récupérer les données de population
      const response = await fetch(`/api/city/${cityId}/population`);
      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Validation et valeurs par défaut pour éviter les erreurs
      const validatedData: PopulationInfo = {
        population_total: data.population_total || 0,
        population_free: data.population_free || 0,
        max_capacity: data.max_capacity || 0,
        workers_assigned: data.workers_assigned || {},
        growth_rate: data.growth_rate || 0,
        satisfaction: data.satisfaction || 50
      };
      
      setPopulationInfo(validatedData);
      
    } catch (err) {
      console.error('Erreur lors du chargement des informations de population:', err);
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    } finally {
      setLoading(false);
    }
  };

  // Fonction pour formater les nombres avec des espaces comme séparateurs de milliers
  const formatNumber = (num: number): string => {
    const rounded = Math.floor(num);
    return rounded.toLocaleString('fr-FR').replace(/,/g, ' ');
  };

  if (loading) {
    return (
      <div className="population-info-popup-overlay" onClick={onClose}>
        <div className="population-info-popup" onClick={(e) => e.stopPropagation()}>
          <div className="population-info-popup-header">
            <div className="population-info-popup-title">
              🏘️ Population - {cityName}
            </div>
            <button className="close-button" onClick={onClose}>
              ✕
            </button>
          </div>
          <div className="population-info-popup-content">
            <div className="loading">Chargement...</div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="population-info-popup-overlay" onClick={onClose}>
        <div className="population-info-popup" onClick={(e) => e.stopPropagation()}>
          <div className="population-info-popup-header">
            <div className="population-info-popup-title">
              {getUIEmoji('city')} Population - {cityName}
            </div>
            <button className="close-button" onClick={onClose}>
              ✕
            </button>
          </div>
          <div className="population-info-popup-content">
            <div className="error">Erreur: {error}</div>
          </div>
        </div>
      </div>
    );
  }

  const totalAssigned = populationInfo.workers_assigned 
    ? Object.values(populationInfo.workers_assigned).reduce((sum, workers) => sum + workers, 0)
    : 0;
  const actualFreePopulation = populationInfo.population_free;

  return (
    <div className="population-info-popup-overlay" onClick={onClose}>
      <div className="population-info-popup" onClick={(e) => e.stopPropagation()}>
        <div className="population-info-popup-header">
          <div className="population-info-popup-title">
            {getUIEmoji('city')} Population - {cityName}
          </div>
          <button className="close-button" onClick={onClose}>
            ✕
          </button>
        </div>
        
        <div className="population-info-popup-content">
          {/* Statistiques principales */}
          <div className="population-stats-section">
            <div className="stat-row">
              <span className="stat-label">Population :</span>
              <span className="stat-value">{formatNumber(populationInfo.population_total)}</span>
            </div>
            
            <div className="stat-row">
              <span className="stat-label">Capacité max :</span>
              <span className="stat-value">{formatNumber(populationInfo.max_capacity)}</span>
            </div>
            
            <div className="stat-row">
              <span className="stat-label">Libre :</span>
              <span className="stat-value free">{formatNumber(actualFreePopulation)}</span>
            </div>
            
            <div className="stat-row">
              <span className="stat-label">Affectée :</span>
              <span className="stat-value assigned">{formatNumber(totalAssigned)}</span>
            </div>
          </div>

          {/* Croissance de population */}
          <div className="population-growth-section">
            <h3>{getUIEmoji('trend_up')} Croissance de population :</h3>
            <div className="growth-row">
              <span className="growth-label">• Croissance réelle :</span>
              <span className="growth-value">
                {populationInfo.growth_rate !== undefined 
                  ? `+${populationInfo.growth_rate.toFixed(3)} hab/heure`
                  : '+0.000 hab/heure'
                }
              </span>
            </div>
          </div>

          {/* Satisfaction */}
          <div className="population-satisfaction-section">
            <div className="satisfaction-row">
              <span className="satisfaction-label">Satisfaction :</span>
              <span className="satisfaction-value">
                {populationInfo.satisfaction !== undefined 
                  ? `${Math.floor(populationInfo.satisfaction)} / 100`
                  : '50 / 100'
                }
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PopulationInfoPopup;
