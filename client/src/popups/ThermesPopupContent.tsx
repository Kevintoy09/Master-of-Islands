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
    if (!city?.id || curePlagueCooldown) return;
    
    const population = populationInfo?.current_population || 0;
    const cost = 2 * population;
    
    if (!populationInfo?.has_plague || population > cleanlinessCapacity || playerGold < cost) {
      setResultMessage({ text: 'Conditions non réunies pour guérir la peste', type: 'error' });
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`/api/city/${city.id}/cure-plague`, {
        method: 'POST',
      });
      
      if (response.ok) {
        const result = await response.json();
        
        if (result.success) {
          setResultMessage({ text: 'Succès ! La peste a disparu.', type: 'success' });
          await fetchPopulationInfo();
          await fetchPlayerGold();
          onCityDataChange?.();
        } else {
          setResultMessage({ text: 'Échec… La peste persiste.', type: 'error' });
          setCurePlagueCooldown(true);
          setTimeout(() => setCurePlagueCooldown(false), 5000);
        }
      } else {
        setResultMessage({ text: `Erreur HTTP: ${response.status}`, type: 'error' });
      }
    } catch (error) {
      console.error('Erreur lors de la guérison de la peste:', error);
      setResultMessage({ text: 'Erreur lors de la guérison', type: 'error' });
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
    if (hygiene > 100) return { text: 'Excellente hygiène', color: 'excellent', bonus: '+5 satisfaction' };
    if (hygiene >= 70) return { text: 'Bonne hygiène', color: 'good', bonus: '' };
    if (hygiene >= 50) return { text: 'Attention : hygiène insuffisante', color: 'warning', bonus: '' };
    return { text: 'Danger : risque élevé de peste !', color: 'danger', bonus: '' };
  };

  const hygieneStatus = getHygieneStatus(hygienePercent);
  const cureDisabled = !hasPlague || population > cleanlinessCapacity || playerGold < (2 * population) || curePlagueCooldown || loading;

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
          <span className="hygiene-label">Hygiène de la population :</span>
          <span className="hygiene-value">{Math.round(hygienePercent)}%</span>
        </div>
        <div className={`hygiene-status ${hygieneStatus.color}`}>
          {hygieneStatus.text}
          {hygieneStatus.bonus && <span className="hygiene-bonus"> ({hygieneStatus.bonus})</span>}
        </div>

        {/* Barre d'hygiène avec zones colorées */}
        <div className="hygiene-zones">
          <div className="zone excellent"></div>
          <div className="zone good"></div>
          <div className="zone warning"></div>
          <div className="zone danger"></div>
        </div>
        <div className="hygiene-thresholds">
          <span>100%</span>
          <span>70%</span>
          <span>50%</span>
        </div>
      </div>

      {/* État de la peste */}
      <div className="plague-section">
        {hasPlague ? (
          <div className="plague-active">
            <strong>⚠️ PESTE ACTIVE !</strong>
          </div>
        ) : (
          <div className="plague-inactive">
            ✅ Aucune peste dans la ville
          </div>
        )}
      </div>

      {/* Bouton de guérison */}
      <div className="cure-section">
        <button 
          className={`cure-button ${cureDisabled ? 'disabled' : ''}`}
          onClick={tryPlagueCure}
          disabled={cureDisabled}
        >
          {getCureButtonText(hasPlague, hygienePercent, playerGold, population, curePlagueCooldown, loading)}
        </button>
        
        {resultMessage.text && (
          <div className={`result-message ${resultMessage.type}`}>
            {resultMessage.text}
          </div>
        )}
      </div>
    </div>
  );
};

function getCureButtonText(hasPlague: boolean, hygiene: number, gold: number, population: number, cooldown: boolean, loading: boolean): string {
  if (loading) return 'Traitement en cours...';
  if (!hasPlague) return 'Aucune peste à soigner';
  if (hygiene < 100) return 'Hygiène insuffisante';
  if (gold < 2 * population) return `Or insuffisant (${2 * population} requis)`;
  if (cooldown) return 'Nouvelle tentative dans 5s';
  return `Soigner la peste (${2 * population} or)`;
}

export default ThermesPopupContent;
