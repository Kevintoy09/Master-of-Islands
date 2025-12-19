import React, { useState, useEffect } from 'react';
import { useAutoUpdatePopulation } from '../hooks/useAutoUpdatePopulation';

// Architecture corrigée - or géré au niveau joueur, plus au niveau ville
interface TownHallPopupContentProps {
  city: any; // Remplacer par un vrai type si disponible
  onRename: (newName: string) => void;
  onOpenSatisfaction: () => void;
  onOpenPopulation: () => void;
}

const TownHallPopupContent: React.FC<TownHallPopupContentProps> = ({
  city,
  onRename,
  onOpenSatisfaction,
  onOpenPopulation,
}) => {
  const [cityName, setCityName] = useState(city?.name || '');
  const [renameValue, setRenameValue] = useState(city?.name || '');
  const [goldRate, setGoldRate] = useState(city?.gold_rate || 1);
  const [windmillMultiplier, setWindmillMultiplier] = useState(1); // Multiplicateur du moulin
  const [loading, setLoading] = useState(false);

  // Hook pour la mise à jour automatique de la population
  const { populationData } = useAutoUpdatePopulation({
    cityId: city?.id,
    enabled: true
  });

  // Fonction pour récupérer le gold_rate actuel depuis le serveur
  const fetchCurrentGoldRate = async () => {
    try {
      const response = await fetch(`/api/city/${city.id}/state`);
      if (response.ok) {
        const cityData = await response.json();
        const currentGoldRate = cityData?.gold_rate || 1;
        setGoldRate(currentGoldRate);
        return currentGoldRate;
      }
    } catch (error) {
      console.error('Erreur lors de la récupération du gold_rate:', error);
    }
    return goldRate;
  };

  // Fonction pour récupérer le multiplicateur du moulin depuis le serveur
  const fetchWindmillMultiplier = async () => {
    try {
      const response = await fetch(`/api/city/${city.id}/windmill-multiplier`);
      if (response.ok) {
        const data = await response.json();
        const multiplier = data?.multiplier || 1;
        setWindmillMultiplier(multiplier);
        return multiplier;
      }
    } catch (error) {
      console.error('Erreur lors de la récupération du multiplicateur du moulin:', error);
    }
    return windmillMultiplier;
  };

  // Récupérer les données au montage du composant
  useEffect(() => {
    if (city?.id) {
      fetchCurrentGoldRate();
      fetchWindmillMultiplier();
    }
  }, [city?.id]);

  useEffect(() => {
    setCityName(city?.name || '');
    setRenameValue(city?.name || '');
    
    // Seulement mettre à jour si city a un gold_rate valide
    const cityGoldRate = city?.gold_rate;
    if (cityGoldRate && cityGoldRate > 0) {
      setGoldRate(cityGoldRate);
    }
    
    // Rafraîchir le multiplicateur du moulin si la ville change
    if (city?.id) {
      fetchWindmillMultiplier();
    }
  }, [city?.name, city?.gold_rate, city?.windmill_cereal_multiplier, city?.id]);

  // Fonction pour changer le taux d'impôt
  const handleGoldRateChange = async (newRate: number) => {
    if (loading || newRate === goldRate) return;
    setLoading(true);
    try {
      const response = await fetch(`/api/city/${city.id}/gold-rate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gold_rate: newRate })
      });
      
      if (response.ok) {
        const result = await response.json();
        
        if (result.success) {
          setGoldRate(newRate);
          
          // Forcer une re-synchronisation pour s'assurer que la valeur est correcte
          setTimeout(() => {
            fetchCurrentGoldRate();
          }, 100);
        } else {
          console.error('Échec de mise à jour du taux d\'impôt');
        }
      } else {
        console.error('Erreur HTTP lors de la mise à jour:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Erreur lors du changement du taux d\'impôt:', error);
    } finally {
      setLoading(false);
    }
  };

  // Utiliser les données mises à jour automatiquement
  const currentPopulation = city?.resources?.population_total || 0; // Utiliser uniquement les données serveur
  const populationInfo = populationData?.info;
  
  // État de blocage de croissance
  const isGrowthBlocked = city?.resources?.growth_blocked_no_cereal || false;
  const currentCereal = city?.resources?.cereal || 0;
  
  // Détection préventive : afficher le bouton dès que conditions réunies (avant même le tick)
  const foodCapacity = (city?.resources?.pop_nourished_by_townhall || 0) + (city?.resources?.pop_nourished_by_windmill || 0);
  const shouldShowBlockWarning = isGrowthBlocked || (currentPopulation >= foodCapacity && currentCereal < 1);
  
  // Données dynamiques (adapter selon structure réelle)
  const populationAssigned = city?.workers_assigned
    ? (Object.values(city.workers_assigned) as number[]).reduce((a, b) => a + b, 0)
    : 0;
  const populationFree = Math.max(0, (populationData?.info?.current_population || 0) - populationAssigned); // Ne peut pas être négative
  const maxPopulation = populationInfo?.max_capacity || city?.max_population || 0;
  const popNourishedByTownHall = city?.resources?.pop_nourished_by_townhall || 0;
  const popNourishedByWindmill = city?.resources?.pop_nourished_by_windmill || 0;
  const totalNourished = popNourishedByTownHall + popNourishedByWindmill;
  const cerealNeeded = city?.resources?.cereal_needed || 0;
  const multiplicateur = windmillMultiplier;
  const satisfaction = (populationData?.info as any)?.satisfaction || city?.satisfaction || 0;
  
  // Calculs pour la croissance de population
  const baseGrowthRate = populationInfo?.base_growth_per_hour || 0; // Croissance de base de l'Hôtel de Ville
  const satisfactionBonus = ((satisfaction - 50) / 50) * 100; // Bonus en % (-100% à +100%)
  
  // Utiliser la croissance réelle calculée par le serveur (déjà en /sec)
  const realGrowthPerSecond = populationInfo?.growth_per_second || 0;
  
  // Calcul du taux de croissance de l'or (1 or/habitant/heure × gold_rate)
  const goldGrowthPerHour = populationFree * goldRate;

  // Fonction pour débloquer la croissance manuellement
  const handleUnblockGrowth = async () => {
    if (loading) return;
    setLoading(true);
    try {
      const response = await fetch(`/api/city/${city.id}/unblock-growth`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Mettre à jour localement sans recharger la page
        if (city?.resources) {
          city.resources.growth_blocked_no_cereal = false;
        }
        alert('✅ Croissance de population débloquée !');
      } else {
        alert(`❌ ${result.message}`);
      }
    } catch (error) {
      console.error('Erreur lors du déblocage de la croissance:', error);
      alert('❌ Erreur lors du déblocage de la croissance');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="popup-content">
      {/* Renommer la ville */}
      <div className="popup-input-group">
        <span>Nom de la ville :</span>
        <input
          type="text"
          value={renameValue}
          onChange={e => setRenameValue(e.target.value)}
          className="popup-text-input"
          style={{ width: 120 }}
        />
        <button
          onClick={() => {
            if (renameValue.trim() && renameValue !== cityName) onRename(renameValue.trim());
          }}
          className="popup-action-button primary"
        >
          Renommer
        </button>
      </div>

      {/* Informations population */}
      <div className="popup-stats-grid">
        <div>Population : {Math.floor(currentPopulation)}</div>
        <div>Capacité max : {Math.floor(maxPopulation)}</div>
        <div>Libre : {Math.floor(populationFree)}</div>
        <div>Affectée : {Math.floor(populationAssigned)}</div>
      </div>

      {/* Croissance de population */}
      {populationInfo && (
        <div className="popup-section highlight">
          <div className="popup-section-title">Croissance de population :</div>
          <div>• Base : +{baseGrowthRate.toFixed(1)}/h</div>
          <div>• Bonus satisfaction : {satisfactionBonus >= 0 ? '+' : ''}{satisfactionBonus.toFixed(0)}%</div>
          <div>• Croissance estimée : {realGrowthPerSecond >= 0 ? '+' : ''}{populationInfo.real_growth_per_hour.toFixed(2)} hab/h</div>
          
          {/* Bouton de déblocage si croissance bloquée */}
          {shouldShowBlockWarning && (
            <div style={{marginTop: 12, padding: '8px', backgroundColor: '#663300', borderRadius: 4, border: '1px solid #aa5500'}}>
              <div style={{color: '#ffaa00', marginBottom: 6, fontWeight: 'bold'}}>
                {isGrowthBlocked ? '🔒 Croissance bloquée (manque de céréales)' : '⚠️ Croissance bientôt bloquée'}
              </div>
              {currentCereal >= 1 && isGrowthBlocked ? (
                <button 
                  onClick={handleUnblockGrowth}
                  disabled={loading}
                  className="popup-action-button primary"
                  style={{width: '100%', backgroundColor: '#22aa22', fontWeight: 'bold'}}
                >
                  ✅ Relancer la croissance ({currentCereal.toFixed(0)} céréales disponibles)
                </button>
              ) : currentCereal < 1 ? (
                <div style={{color: '#ff6666', fontSize: '0.9em', fontStyle: 'italic'}}>
                  Vous devez obtenir au moins 1 céréale pour continuer la croissance
                </div>
              ) : (
                <div style={{color: '#ffaa00', fontSize: '0.9em', fontStyle: 'italic'}}>
                  La croissance sera bloquée au prochain tick si céréales &lt; 1
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Informations nourriture */}
      <div className="popup-section info">
        <div>Population actuelle : {Math.floor(currentPopulation)}</div>
        <div>Population nourrie : {Math.floor(totalNourished)}</div>
        <div>• Hôtel de Ville : {Math.floor(popNourishedByTownHall)}</div>
        <div>• Moulin : {Math.floor(popNourishedByWindmill)}</div>
        <div>Restant à nourrir : {Math.max(0, Math.floor(currentPopulation - totalNourished))}</div>
        {Math.floor(currentPopulation - totalNourished) > 0 && (
          <div style={{color: '#ff6b6b', fontSize: '0.9em', fontStyle: 'italic'}}>
            ⚠️ Population limitée par la capacité des bâtiments
          </div>
        )}
        <div>Consommation de céréales : {(cerealNeeded * 360).toFixed(1)} céréales/h</div>
        <div>Conso. par habitant : 0.1 céréales/h × {multiplicateur.toFixed(2)} = {(0.1 * multiplicateur).toFixed(2)} céréales/h</div>
      </div>

      {/* Satisfaction et gestion */}
      <div className="popup-stats-grid">
        <div>
          Satisfaction : {satisfaction} / 100
          <button onClick={onOpenSatisfaction} className="popup-action-button primary" style={{marginLeft: 8, padding: '2px 6px', fontSize: '0.9em'}}>
            Détail
          </button>
        </div>
        <div>
          <button onClick={onOpenPopulation} className="popup-action-button primary">
            Gestion population
          </button>
        </div>
      </div>

      {/* Système de taux d'impôt */}
      <div className="popup-section">
        <div className="popup-section-title">Taux d'impôt :</div>
        <div className="popup-button-group" style={{marginBottom: 8}}>
          {[1, 2, 3].map(rate => (
            <button
              key={rate}
              onClick={() => handleGoldRateChange(rate)}
              disabled={loading}
              className={`popup-action-button ${goldRate === rate ? 'selected' : 'secondary'}`}
              style={{
                backgroundColor: goldRate === rate ? '#4a90e2' : '#666',
                width: 60,
                margin: '0 4px'
              }}
            >
              {rate} or
            </button>
          ))}
        </div>
        <div className="popup-section highlight">
          <strong>Taux de croissance de l'or : {goldGrowthPerHour} or/h</strong>
        </div>
      </div>
    </div>
  );
};

export default TownHallPopupContent;
