import React, { useState, useEffect } from 'react';
import { useUser } from '../hooks/useUser';
import './ThermesPopupContent.css';

interface ThermesPopupContentProps {
  city: any;
  building: any;
  onClose: () => void;
  onCityDataChange?: () => void;
}

const ThermesPopupContent: React.FC<ThermesPopupContentProps> = ({
  city,
  building,
  onClose,
  onCityDataChange,
}) => {
  const { user } = useUser();
  const [populationInfo, setPopulationInfo] = useState<any>(null);
  const [playerGold, setPlayerGold] = useState<number>(0);
  const [buildingData, setBuildingData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [curePlagueCooldown, setCurePlagueCooldown] = useState(false);
  const [resultMessage, setResultMessage] = useState<{ text: string; type: 'success' | 'error' | null }>({ text: '', type: null });

  // Données du bâtiment Thermes
  const buildingLevel = building?.level || 1;
  const cleanlinessCapacity = buildingData?.cleanliness_capacity || 0;
  const satisfactionBonus = buildingData?.satisfaction_bonus || 0;

  // Charger les données de population et d'hygiène
  useEffect(() => {
    fetchBuildingData();
    fetchPopulationInfo();
    fetchPlayerGold();
    const interval = setInterval(() => {
      fetchPopulationInfo();
      fetchPlayerGold();
    }, 10000); // Mise à jour toutes les 10 secondes
    return () => clearInterval(interval);
  }, [city?.id, buildingLevel]);

  const fetchBuildingData = async () => {
    try {
      const response = await fetch('/data/buildings.json');
      if (response.ok) {
        const data = await response.json();
        const thermesLevels = data.Thermes?.levels || [];
        const levelData = thermesLevels.find((l: any) => l.level === buildingLevel);
        if (levelData?.effect) {
          setBuildingData(levelData.effect);
        }
      }
    } catch (error) {
      console.error('Erreur lors du chargement des données du bâtiment:', error);
    }
  };

  const fetchPopulationInfo = async () => {
    if (!city?.id) return;
    
    try {
      const response = await fetch(`/api/city/${city.id}/population`);
      if (response.ok) {
        const data = await response.json();
        setPopulationInfo(data.info);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des données de population:', error);
    }
  };

  const fetchPlayerGold = async () => {
    if (!user?.id) return;

    try {
      const response = await fetch(`/api/player/${user.id}`);
      if (response.ok) {
        const data = await response.json();
        const gold = data.player_info?.gold || data.gold || 0;
        setPlayerGold(gold);
      }
    } catch (error) {
      console.error('Erreur lors du chargement de l\'or du joueur:', error);
    }
  };

  const tryPlagueCure = async () => {
    if (!city?.id || curePlagueCooldown || !hasPlague) return;

    setLoading(true);
    setResultMessage({ text: '', type: null });
    
    try {
      const response = await fetch(`/api/city/${city.id}/cure-plague`, {
        method: 'POST',
      });
      
      if (response.ok) {
        const result = await response.json();
        
        if (result.success) {
          setResultMessage({ text: `✓ Peste soignée ! (${result.cost} or dépensé)`, type: 'success' });
          await fetchPopulationInfo();
          await fetchPlayerGold();
          onCityDataChange?.();
        } else {
          setResultMessage({ text: `✗ Échec du traitement (${result.cost} or perdu)`, type: 'error' });
          await fetchPlayerGold();
          setCurePlagueCooldown(true);
          setTimeout(() => setCurePlagueCooldown(false), 5000);
        }
      } else {
        const errorData = await response.json();
        setResultMessage({ text: errorData.message || 'Erreur', type: 'error' });
      }
    } catch (error) {
      console.error('Erreur lors de la guérison de la peste:', error);
      setResultMessage({ text: 'Erreur réseau', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  // Effacer le message après 3 secondes
  useEffect(() => {
    if (resultMessage.text) {
      const timer = setTimeout(() => {
        setResultMessage({ text: '', type: null });
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [resultMessage]);

  const population = populationInfo?.current_population || 0;
  const maxCapacity = populationInfo?.max_capacity || 0;
  const hygienePercent = populationInfo?.hygiene_percent || 100;
  const hasPlague = populationInfo?.has_plague || false;

  const getHygieneStatus = (hygiene: number) => {
    if (hygiene >= 80) return { text: 'Excellente', color: 'excellent', bonus: '+10', icon: '✨' };
    if (hygiene >= 60) return { text: 'Bonne', color: 'good', bonus: '+5', icon: '✓' };
    if (hygiene >= 40) return { text: 'Médiocre', color: 'warning', bonus: '-5', icon: '⚠️' };
    return { text: 'Catastrophique', color: 'danger', bonus: '-15', icon: '☠️' };
  };

  const hygieneStatus = getHygieneStatus(hygienePercent);
  const cureCost = Math.max(1, Math.floor(playerGold * 0.10));
  const cureDisabled = !hasPlague || curePlagueCooldown || loading;

  return (
    <div className="thermes-popup-content">
      <div className="thermes-header">
        <h3>Thermes de la ville</h3>
        <div className="thermes-level">Niveau des Thermes : {buildingLevel}</div>
      </div>

      {/* Informations de base */}
      <div className="thermes-stats">
        <div className="stat-item">
          <span className="stat-label">Capacité de propreté :</span>
          <span className="stat-value">{cleanlinessCapacity}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Population actuelle :</span>
          <span className="stat-value">{population}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Bonus satisfaction :</span>
          <span className="stat-value">+{satisfactionBonus}</span>
        </div>
      </div>

      {/* Barre de population avec indicateur de capacité */}
      <div className="population-bar-section">
        <div className="population-bar-container">
          <div className="population-bar">
            <div 
              className="population-fill" 
              style={{ width: `${Math.min(100, (population / maxCapacity) * 100)}%` }}
            />
            <div 
              className="cleanliness-indicator" 
              style={{ left: `${Math.min(100, (cleanlinessCapacity / maxCapacity) * 100)}%` }}
            />
          </div>
          <div className="population-labels">
            <span className="cleanliness-label" style={{ left: `${Math.min(100, (cleanlinessCapacity / maxCapacity) * 100)}%` }}>
              {cleanlinessCapacity}
            </span>
            <span className="max-label">Max : {maxCapacity}</span>
          </div>
        </div>
      </div>

      {/* État d'hygiène */}
      <div className="hygiene-section">
        <div className="hygiene-info">
          <span className="hygiene-label">Hygiène :</span>
          <span className={`hygiene-value ${hygieneStatus.color}`}>
            {hygieneStatus.icon} {Math.round(hygienePercent)}% - {hygieneStatus.text}
          </span>
        </div>
        <div className="hygiene-impact">
          Satisfaction : <strong className={hygieneStatus.bonus.startsWith('+') ? 'positive' : 'negative'}>
            {hygieneStatus.bonus}
          </strong>
        </div>

        {/* Barre d'hygiène avec zones colorées */}
        <div className="hygiene-bar-wrapper">
          <div className="hygiene-bar">
            <div 
              className={`hygiene-fill ${hygieneStatus.color}`}
              style={{ width: `${Math.min(100, hygienePercent)}%` }}
            />
          </div>
          <div className="hygiene-zones">
            <div className="zone excellent" title="80%+ : +10 satisfaction"></div>
            <div className="zone good" title="60-80% : +5 satisfaction"></div>
            <div className="zone warning" title="40-60% : -5 satisfaction"></div>
            <div className="zone danger" title="<40% : -15 satisfaction + risque peste"></div>
          </div>
          <div className="hygiene-thresholds">
            <span>80%</span>
            <span>60%</span>
            <span>40%</span>
            <span>0%</span>
          </div>
        </div>
      </div>

      {/* État de la peste */}
      {hasPlague ? (
        <div className="plague-active-section">
          <div className="plague-header">
            <span className="plague-icon">☠️</span>
            <strong>PESTE ACTIVE</strong>
          </div>
          <div className="plague-effects">
            <div className="effect-item danger">
              <span className="effect-icon">💀</span>
              <span>-20 satisfaction</span>
            </div>
            <div className="effect-item danger">
              <span className="effect-icon">⚰️</span>
              <span>Fort ralentissement croissance</span>
            </div>
          </div>
          <div className="cure-info">
            <div className="cure-cost">Traitement : <strong>{cureCost} or</strong> (10% de votre or)</div>
            <div className="cure-chance">Réussite : <strong>50%</strong></div>
            <div className="cure-warning">⚠️ L'or est perdu même en cas d'échec</div>
          </div>
          <button 
            className={`cure-button ${cureDisabled ? 'disabled' : ''}`}
            onClick={tryPlagueCure}
            disabled={cureDisabled}
          >
            {getCureButtonText(hasPlague, cureCost, playerGold, curePlagueCooldown, loading)}
          </button>
          
          {resultMessage.text && (
            <div className={`result-message ${resultMessage.type}`}>
              {resultMessage.text}
            </div>
          )}
        </div>
      ) : (
        <div className="plague-inactive-section">
          <div className="no-plague">
            <span className="check-icon">✓</span>
            <span>Aucune peste</span>
          </div>
          
          {/* Informations préventives */}
          <div className={`plague-prevention ${hygienePercent < 40 && population > 50 ? 'at-risk' : ''}`}>
            <div className="prevention-title">
              {hygienePercent < 40 && population > 50 ? (
                <>⚠️ <strong>Risque actuel de peste</strong></>
              ) : (
                <>📋 <strong>Prévention peste</strong></>
              )}
            </div>
            
            <div className="prevention-conditions">
              <div className="condition-title">Déclenchement si :</div>
              <div className="conditions-list">
                <div className={`condition-item ${hygienePercent < 40 ? 'danger' : 'ok'}`}>
                  <span className="condition-icon">{hygienePercent < 40 ? '✗' : '✓'}</span>
                  <span>Hygiène &lt; 40%</span>
                  <span className="condition-value">({Math.round(hygienePercent)}%)</span>
                </div>
                <div className={`condition-item ${population > 50 ? 'danger' : 'ok'}`}>
                  <span className="condition-icon">{population > 50 ? '✗' : '✓'}</span>
                  <span>Population &gt; 50</span>
                  <span className="condition-value">({population})</span>
                </div>
              </div>
            </div>
            
            <div className="prevention-consequences">
              <div className="consequence-title">Conséquences :</div>
              <div className="consequence-item death">💀 <strong>25%</strong> de la population libre meurt</div>
              <div className="consequence-item malus">📉 <strong>-35</strong> satisfaction (-15 hygiène, -20 peste)</div>
              <div className="consequence-item block">� Fort ralentissement de la croissance</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

function getCureButtonText(hasPlague: boolean, cost: number, gold: number, cooldown: boolean, loading: boolean): string {
  if (loading) return '⏳ Traitement en cours...';
  if (!hasPlague) return 'Aucune peste';
  if (gold < cost) return `Or insuffisant (${cost} requis)`;
  if (cooldown) return 'Nouvelle tentative dans 5s';
  return `🏥 Tenter le traitement (${cost} or)`;
}

export default ThermesPopupContent;
