import React, { useState, useEffect } from 'react';

interface WindmillPopupContentProps {
  city: any;
  building: any;
  onClose: () => void;
  onCityDataChange?: () => void;
}

const WindmillPopupContent: React.FC<WindmillPopupContentProps> = ({
  city,
  building,
  onClose,
  onCityDataChange
}) => {
  const [cerealBonus, setCerealBonus] = useState(0); // Slider du moulin (céréales/h)
  const [confirmedBonus, setConfirmedBonus] = useState(0); // Bonus confirmé côté serveur
  const [loading, setLoading] = useState(false);
  const [buildingData, setBuildingData] = useState<any>(null); // Données du bâtiment depuis l'API

  // Récupérer le bonus actuel et les données du bâtiment depuis le serveur
  const fetchCurrentBonus = async () => {
    try {
      const response = await fetch(`/api/city/${city.id}/state`);
      if (response.ok) {
        const cityData = await response.json();
        const currentBonus = cityData?.windmill_cereal_bonus || 0;
        setCerealBonus(currentBonus);
        setConfirmedBonus(currentBonus);
        
        // Trouver le moulin dans les bâtiments de la ville
        const windmill = cityData?.buildings?.find((b: any) => b.name === 'Windmill');
        if (windmill) {
          setBuildingData(windmill);
        }
        
        return currentBonus;
      } else {
        console.error(`Erreur HTTP lors de la récupération du bonus:`, response.status);
      }
    } catch (error) {
      console.error('Erreur lors de la récupération du bonus:', error);
    }
    return cerealBonus;
  };

  // Récupérer le bonus au montage du composant
  useEffect(() => {
    if (city?.id) {
      fetchCurrentBonus();
    }
  }, [city?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // Fonction pour changer le bonus de céréales
  const handleBonusChange = async (newBonus: number) => {
    if (loading || newBonus === confirmedBonus) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/city/${city.id}/windmill-bonus`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bonus: newBonus })
      });
      
      console.log('[WINDMILL POST] Response status:', response.status);
      
      if (response.ok) {
        const result = await response.json();
        console.log('[WINDMILL POST] Result:', result);
        
        if (result.success) {
          setCerealBonus(newBonus);
          setConfirmedBonus(newBonus);
          
          // Mettre à jour l'objet city pour synchronisation
          if (city && typeof city === 'object') {
            city.windmill_cereal_bonus = newBonus;
          }
          
          // Re-synchroniser
          setTimeout(() => {
            fetchCurrentBonus();
          }, 100);
          
          // Notifier le changement
          if (onCityDataChange) {
            onCityDataChange();
          }
        } else {
          console.error('Échec de mise à jour du bonus');
        }
      } else {
        console.error('Erreur HTTP lors de la mise à jour:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Erreur lors du changement du bonus:', error);
    } finally {
      setLoading(false);
    }
  };

  // Calcul des effets du bâtiment
  const currentLevel = building?.level || 1;
  const maxCerealBonus = buildingData?.effect?.cereal_bonus_per_hour || 0;

  // Informations de population
  const popUnfed = city?.resources?.population_unfed || 0;
  const popNourishedByTownhall = city?.resources?.pop_nourished_by_townhall || 0;
  const currentPopulation = city?.resources?.population_total || 0;

  // Calcul de la consommation de céréales
  // Consommation = (pop_unfed × 0.1) + windmill_bonus
  const baseCerealConsumption = popUnfed * 0.1; // En céréales/h
  const totalCerealConsumption = baseCerealConsumption + cerealBonus;
  const satisfactionBonus = cerealBonus; // 1 point de satisfaction par céréale/h

  return (
    <div className="popup-content">
      {/* Ration de nourriture (slider) */}
      <div className="popup-section highlight">
        <div className="popup-section-title">🌾 Ration de nourriture supplémentaire :</div>
        
        {maxCerealBonus > 0 ? (
          <>
            <div style={{ margin: '10px 0' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Consommation bonus : {cerealBonus.toFixed(1)} céréales/h
              </label>
              <input
                type="range"
                min="0"
                max={maxCerealBonus}
                step="1"
                value={cerealBonus}
                onChange={(e) => {
                  const newValue = parseFloat(e.target.value);
                  setCerealBonus(newValue);
                }}
                disabled={loading}
                style={{ width: '100%' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8em', color: '#666' }}>
                <span>0 (Min)</span>
                <span>{maxCerealBonus} (Max - Niveau {currentLevel})</span>
              </div>
            </div>

            {/* Boutons */}
            <div className="popup-button-group" style={{ marginTop: '10px' }}>
              <button
                onClick={() => handleBonusChange(cerealBonus)}
                disabled={loading || cerealBonus === confirmedBonus}
                className="popup-action-button primary"
              >
                {loading ? 'Application...' : 'Appliquer'}
              </button>
              <button
                onClick={() => setCerealBonus(confirmedBonus)}
                disabled={loading}
                className="popup-action-button secondary"
              >
                Annuler
              </button>
            </div>

            {/* Effets */}
            <div style={{ marginTop: '15px', fontSize: '0.9em', backgroundColor: '#f8f9fa', padding: '10px', borderRadius: '5px' }}>
              <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>💡 Effets :</div>
              <div>• Consommation de base : {baseCerealConsumption.toFixed(1)} céréales/h ({popUnfed} pop × 0.1)</div>
              <div>• Consommation bonus : {cerealBonus.toFixed(1)} céréales/h</div>
              <div style={{ fontWeight: 'bold', color: '#d9534f' }}>• Total : {totalCerealConsumption.toFixed(1)} céréales/h</div>
              <div style={{ color: '#5cb85c', fontWeight: 'bold', marginTop: '5px' }}>• Bonus de satisfaction : +{satisfactionBonus} points</div>
            </div>

            <div style={{ marginTop: '10px', fontSize: '0.85em', color: '#666', fontStyle: 'italic' }}>
              ℹ️ Plus vous augmentez la ration, plus la population est satisfaite. Si vous manquez de céréales, le bonus se réinitialise automatiquement à 0.
            </div>
          </>
        ) : (
          <div style={{ padding: '20px', textAlign: 'center', color: '#666', fontStyle: 'italic' }}>
            ⚠️ Ce moulin n'a pas de capacité de bonus. Vérifiez que le bâtiment est bien terminé et configuré correctement.
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="popup-actions">
        <button
          onClick={onClose}
          className="popup-action-button secondary"
        >
          Fermer
        </button>
      </div>
    </div>
  );
};

export default WindmillPopupContent;

