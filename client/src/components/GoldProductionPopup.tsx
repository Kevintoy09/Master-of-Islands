import React, { useState, useEffect } from 'react';
import { useUser } from '../hooks/useUser';
import { getResourceEmoji, getUIEmoji } from '../constants/resourceIcons';
import { getApiUrl } from '../utils/api';
import './GoldProductionPopup.css';

interface GoldProductionPopupProps {
  onClose: () => void;
  onOpenMilitaryExpenses?: () => void;
  currentGold?: number;
  militaryExpenses?: number;
}

interface CityGoldInfo {
  city_id: string;
  city_name: string;
  population_free: number;
  tax_rate: number;
  gold_per_second: number;
}

interface GoldProductionInfo {
  total_gold_per_second: number;
  cities: CityGoldInfo[];
}

const GoldProductionPopup: React.FC<GoldProductionPopupProps> = ({ 
  onClose, 
  onOpenMilitaryExpenses,
  currentGold = 0,
  militaryExpenses = 0
}) => {
  const [goldInfo, setGoldInfo] = useState<GoldProductionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useUser();

  // Fonction pour formater les nombres avec des espaces comme séparateurs de milliers
  const formatNumber = (num: number): string => {
    const rounded = Math.floor(num);
    return rounded.toLocaleString('fr-FR').replace(/,/g, ' ');
  };

  // Fonction pour formater les taux d'imposition
  const formatTaxRate = (rate: number): string => {
    return `${rate} or/heure par habitant`;
  };

  // Charger les informations de production d'or
  const loadGoldInfo = async () => {
    try {
      setLoading(true);
      setError(null);

      if (!user?.id) {
        throw new Error('Utilisateur non connecté');
      }

      const response = await fetch(`${getApiUrl()}/api/game/gold-production?player_id=${user.id}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      const data = await response.json();
      
      // Validation des données
      if (!data || typeof data.total_gold_per_second !== 'number' || !Array.isArray(data.cities)) {
        throw new Error('Format de données invalide reçu du serveur');
      }

      setGoldInfo(data);
    } catch (err) {
      console.error('Erreur lors du chargement des informations d\'or:', err);
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGoldInfo();
  }, []);

  if (loading) {
    return (
      <div className="gold-production-popup-overlay" onClick={onClose}>
        <div className="gold-production-popup" onClick={(e) => e.stopPropagation()}>
          <div className="gold-production-popup-header">
            <div className="gold-production-popup-title">
              {getResourceEmoji('gold')} Production d'or
            </div>
            <button className="close-button" onClick={onClose}>
              ✕
            </button>
          </div>
          <div className="gold-production-popup-content">
            <div className="loading">Chargement...</div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="gold-production-popup-overlay" onClick={onClose}>
        <div className="gold-production-popup" onClick={(e) => e.stopPropagation()}>
          <div className="gold-production-popup-header">
            <div className="gold-production-popup-title">
              {getResourceEmoji('gold')} Production d'or
            </div>
            <button className="close-button" onClick={onClose}>
              ✕
            </button>
          </div>
          <div className="gold-production-popup-content">
            <div className="error">Erreur: {error}</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="gold-production-popup-overlay" onClick={onClose}>
      <div className="gold-production-popup" onClick={(e) => e.stopPropagation()}>
        <div className="gold-production-popup-header">
          <div className="gold-production-popup-title">
            {getResourceEmoji('gold')} Production d'or
          </div>
          <button className="close-button" onClick={onClose}>
            ✕
          </button>
        </div>
        
        <div className="gold-production-popup-content">
          {/* Production totale */}
          <div className="gold-total-section">
            <h3>{getUIEmoji('statistics')} Situation financière</h3>
            
            <div className="total-gold-row">
              <span className="total-label">Or dans les caisses :</span>
              <span className="total-value gold">{currentGold.toFixed(0)} or</span>
            </div>
            
            <div className="total-gold-row">
              <span className="total-label">Production globale :</span>
              <span className="total-value positive">+{goldInfo?.total_gold_per_second?.toFixed(2) || '0.00'} or/heure</span>
            </div>
            
            <div className="total-gold-row">
              <span className="total-label">Dépenses militaires :</span>
              <span className="total-value negative">-{militaryExpenses.toFixed(2)} or/heure</span>
            </div>
            
            <div className="total-gold-row balance-row">
              <span className="total-label"><strong>Solde net :</strong></span>
              <span className={`total-value ${(goldInfo?.total_gold_per_second || 0) - militaryExpenses >= 0 ? 'positive' : 'negative'}`}>
                <strong>{((goldInfo?.total_gold_per_second || 0) - militaryExpenses >= 0 ? '+' : '')}{((goldInfo?.total_gold_per_second || 0) - militaryExpenses).toFixed(2)} or/heure</strong>
              </span>
            </div>
            
            {/* Avertissement si déficit */}
            {(goldInfo?.total_gold_per_second || 0) - militaryExpenses < 0 && (
              <div className="warning-box">
                <div className="warning-icon">⚠️</div>
                <div className="warning-text">
                  <strong>Attention !</strong> Vos dépenses dépassent vos revenus.<br/>
                  {currentGold > 0 ? (
                    <>
                      Plus d'or dans <strong>{Math.floor(currentGold / Math.abs((goldInfo?.total_gold_per_second || 0) - militaryExpenses))}</strong> heures.<br/>
                      <span className="warning-consequence">Si vous ne pouvez pas payer vos unités, elles vont partir !</span>
                    </>
                  ) : (
                    <span className="warning-consequence">Vos caisses sont vides ! Vos unités vont partir !</span>
                  )}
                </div>
              </div>
            )}
            
            {/* Bouton vers dépenses militaires */}
            {onOpenMilitaryExpenses && (
              <button 
                className="military-expenses-button"
                onClick={onOpenMilitaryExpenses}
              >
                💰 Détail des dépenses militaires
              </button>
            )}
          </div>

          {/* Détail par ville */}
          <div className="cities-gold-section">
            <h3>{getUIEmoji('city')} Détail par ville</h3>
            
            {goldInfo?.cities && goldInfo.cities.length > 0 ? (
              <div className="cities-list">
                {goldInfo.cities.map((city, index) => (
                  <div key={city.city_id} className="city-gold-row">
                    <div className="city-info">
                      <div className="city-name">{city.city_name}</div>
                      <div className="city-details">
                        <span className="detail-item">
                          Population libre: <strong>{formatNumber(city.population_free)}</strong>
                        </span>
                        <span className="detail-item">
                          Taux d'imposition: <strong>{formatTaxRate(city.tax_rate)}</strong>
                        </span>
                      </div>
                    </div>
                    <div className="city-production">
                      <span className="production-value">
                        +{city.gold_per_second.toFixed(2)} or/heure
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-cities">Aucune ville ne génère d'or actuellement</div>
            )}
          </div>

          {/* Explication du calcul */}
          <div className="gold-explanation-section">
            <h4>{getUIEmoji('info')} Calcul de la production</h4>
            <div className="explanation-text">
              <p>La production d'or de chaque ville est calculée selon :</p>
              <p><strong>Or/heure = Population libre × Taux d'imposition</strong></p>
              <p>Le taux d'imposition peut être modifié dans l'Hôtel de Ville de chaque cité.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GoldProductionPopup;
