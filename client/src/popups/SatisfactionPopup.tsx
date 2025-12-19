import React, { useState, useEffect } from 'react';
import './SatisfactionPopup.css';

interface SatisfactionData {
  satisfaction: number;
  satisfaction_factors: {
    bonus?: { [key: string]: number };
    malus?: { [key: string]: number };
  };
  current_population: number;
  max_capacity: number;
  food_capacity: number;
  windmill_food_supply: number;
  hygiene_percent: number;
  has_plague: boolean;
  cereal_multiplier: number;
  cereal_needed: number;
}

interface SatisfactionPopupProps {
  cityId: string;
  cityName: string;
  onClose: () => void;
}

const SatisfactionPopup: React.FC<SatisfactionPopupProps> = ({
  cityId,
  cityName,
  onClose,
}) => {
  const [satisfactionData, setSatisfactionData] = useState<SatisfactionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSatisfactionData();
  }, [cityId]);

  const fetchSatisfactionData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/city/${cityId}/population`);
      
      
      
      
      if (!response.ok) {
        const errorText = await response.text();
        
        throw new Error(`Erreur ${response.status}: ${response.statusText} - ${errorText}`);
      }
      
      const responseText = await response.text();
      
      
      if (!responseText.trim()) {
        throw new Error('Réponse vide du serveur');
      }
      
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        console.error('JSON parse error:', parseError);
        
        throw new Error(`Réponse invalide du serveur: ${responseText.substring(0, 100)}...`);
      }
      
      
      
      // Essayer différentes structures de données
      if (data.info) {
        
        
        setSatisfactionData(data.info);
      } else if (data.satisfaction !== undefined) {
        
        setSatisfactionData(data);
      } else {
        console.warn('Structure de données inattendue:', data);
        throw new Error('Structure de données inattendue dans la réponse');
      }
      
      setError(null);
    } catch (err) {
      console.error('Erreur lors du chargement des données de satisfaction:', err);
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    } finally {
      setLoading(false);
    }
  };

  const curePlague = async () => {
    try {
      const response = await fetch(`/api/city/${cityId}/cure-plague`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }
      await fetchSatisfactionData(); // Recharger les données
    } catch (err) {
      console.error('Erreur lors de la guérison de la peste:', err);
      setError(err instanceof Error ? err.message : 'Erreur lors de la guérison');
    }
  };

  const formatFactorName = (factor: string): string => {
    const translations: { [key: string]: string } = {
      'academy': 'Académie',
      'thermes': 'Thermes',
      'windmill': 'Moulin',
      'impot': 'Taux d\'imposition favorable',
      'hygiene': 'Hygiène',
      'market': 'Marché',
      'embassy': 'Ambassade',
      'plague': 'Peste active',
      'population': 'Densité de population',
      'famine': 'Famine',
      'food_surplus': 'Surplus alimentaire',
      'research': 'Recherches (Puits, Philosophie...)',
    };
    return translations[factor] || factor;
  };

  if (loading) {
    return (
      <div className="satisfaction-popup-overlay">
        <div className="satisfaction-popup">
          <div className="satisfaction-popup-header">
            <h2>Satisfaction - {cityName}</h2>
            <button className="close-button" onClick={onClose}>×</button>
          </div>
          <div className="satisfaction-popup-content">
            <div className="loading">Chargement des données de satisfaction...</div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="satisfaction-popup-overlay">
        <div className="satisfaction-popup">
          <div className="satisfaction-popup-header">
            <h2>Satisfaction - {cityName}</h2>
            <button className="close-button" onClick={onClose}>×</button>
          </div>
          <div className="satisfaction-popup-content">
            <div className="error">
              Erreur: {error}
              <button onClick={fetchSatisfactionData} className="retry-button">
                Réessayer
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!satisfactionData) {
    return null;
  }

  const satisfactionLevel = satisfactionData.satisfaction;
  const satisfactionColor = 
    satisfactionLevel >= 75 ? '#4CAF50' : 
    satisfactionLevel >= 50 ? '#FF9800' : '#F44336';

  return (
    <div className="satisfaction-popup-overlay">
      <div className="satisfaction-popup">
        <div className="satisfaction-popup-header">
          <h2>Satisfaction - {cityName}</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        
        <div className="satisfaction-popup-content">
          {/* Satisfaction totale */}
          <div className="satisfaction-summary">
            <h3 style={{ color: satisfactionColor }}>
              Satisfaction totale : {Math.round(satisfactionLevel)} / 100
            </h3>
            <div className="satisfaction-bar">
              <div 
                className="satisfaction-fill" 
                style={{ 
                  width: `${Math.max(0, Math.min(100, satisfactionLevel))}%`,
                  backgroundColor: satisfactionColor 
                }}
              />
            </div>
          </div>

          {/* Bonus */}
          {satisfactionData.satisfaction_factors?.bonus && Object.keys(satisfactionData.satisfaction_factors.bonus).length > 0 && (
            <div className="satisfaction-section bonus">
              <h4>✅ Bonus :</h4>
              <ul>
                {Object.entries(satisfactionData.satisfaction_factors.bonus).map(([factor, value]) => (
                  <li key={factor} className="bonus-item">
                    + {formatFactorName(factor)} : +{value}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Malus */}
          {satisfactionData.satisfaction_factors?.malus && Object.keys(satisfactionData.satisfaction_factors.malus).length > 0 && (
            <div className="satisfaction-section malus">
              <h4>❌ Malus :</h4>
              <ul>
                {Object.entries(satisfactionData.satisfaction_factors.malus).map(([factor, value]) => (
                  <li key={factor} className="malus-item">
                    - {formatFactorName(factor)} : -{value}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Informations détaillées */}
          <div className="satisfaction-details">
            <h4>📊 Détails :</h4>
            <div className="detail-grid">
              <div className="detail-item">
                <span>Population actuelle :</span>
                <span>{Math.floor(satisfactionData.current_population)}</span>
              </div>
              <div className="detail-item">
                <span>Capacité maximale :</span>
                <span>{Math.floor(satisfactionData.max_capacity)} habitants</span>
              </div>
              <div className="detail-item">
                <span>Capacité alimentaire :</span>
                <span>{Math.floor(satisfactionData.food_capacity)} habitants</span>
              </div>
              <div className="detail-item">
                <span>Approvisionnement moulin :</span>
                <span>{Math.floor(satisfactionData.windmill_food_supply)} habitants</span>
              </div>
              <div className="detail-item">
                <span>Multiplicateur moulin :</span>
                <span>×{satisfactionData.cereal_multiplier.toFixed(2)}</span>
              </div>
              <div className="detail-item">
                <span>Niveau d'hygiène :</span>
                <span className={satisfactionData.hygiene_percent >= 50 ? 'good' : 'poor'}>
                  {Math.round(satisfactionData.hygiene_percent)}%
                </span>
              </div>
            </div>
          </div>

          {/* Alerte peste */}
          {satisfactionData.has_plague && (
            <div className="plague-alert">
              <h4>⚠️ ALERTE PESTE !</h4>
              <p>La peste affecte votre ville ! Construisez des Thermes pour améliorer l'hygiène.</p>
              <button onClick={curePlague} className="cure-plague-button">
                Guérir la peste (coût en or)
              </button>
            </div>
          )}



          {/* Explications */}
          <div className="satisfaction-explanation">
            <h4>ℹ️ Comment ça marche :</h4>
            <ul>
              <li><strong>Satisfaction 0-25 :</strong> Crise démographique (-50% croissance)</li>
              <li><strong>Satisfaction 25-50 :</strong> Déclin (-25% croissance)</li>
              <li><strong>Satisfaction 50-75 :</strong> Croissance normale</li>
              <li><strong>Satisfaction 75-100 :</strong> Boom démographique (+25% croissance)</li>
            </ul>
          </div>

          {/* Bouton fermer */}
          <div className="satisfaction-actions">
            <button onClick={onClose} className="close-action-button">
              Fermer
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SatisfactionPopup;
