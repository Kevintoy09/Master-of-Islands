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
  const [cerealMultiplier, setCerealMultiplier] = useState(1); // Valeur par défaut, sera mise à jour par fetchCurrentMultiplier
  const [confirmedMultiplier, setConfirmedMultiplier] = useState(1); // Multiplicateur confirmé côté serveur
  const [loading, setLoading] = useState(false);

  // Récupérer le multiplicateur actuel depuis le serveur
  const fetchCurrentMultiplier = async () => {
    try {
      const response = await fetch(`/api/city/${city.id}/state`);
      if (response.ok) {
        const cityData = await response.json();
        const currentMultiplier = cityData?.windmill_cereal_multiplier || 1;
        setCerealMultiplier(currentMultiplier);
        setConfirmedMultiplier(currentMultiplier); // Mise à jour du multiplicateur confirmé
        return currentMultiplier;
      } else {
        console.error(`Erreur HTTP lors de la récupération du multiplicateur:`, response.status);
      }
    } catch (error) {
      console.error('Erreur lors de la récupération du multiplicateur:', error);
    }
    return cerealMultiplier;
  };

  // Récupérer le multiplicateur au montage du composant
  useEffect(() => {
    if (city?.id) {
      fetchCurrentMultiplier();
    }
  }, [city?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // Fonction pour changer le multiplicateur de céréales
  const handleMultiplierChange = async (newMultiplier: number) => {
    if (loading || newMultiplier === confirmedMultiplier) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/city/${city.id}/windmill-multiplier`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ multiplier: newMultiplier })
      });
      
      if (response.ok) {
        const result = await response.json();
        
        if (result.success) {
          setCerealMultiplier(newMultiplier);
          setConfirmedMultiplier(newMultiplier); // Mise à jour du multiplicateur confirmé
          
          // IMPORTANT: Mettre à jour l'objet city pour synchroniser avec les autres popups
          if (city && typeof city === 'object') {
            city.windmill_cereal_multiplier = newMultiplier;
          }
          
          // Forcer une re-synchronisation pour s'assurer que la valeur est correcte
          setTimeout(() => {
            fetchCurrentMultiplier();
          }, 100);
          
          // Notifier le changement de données de ville
          if (onCityDataChange) {
            onCityDataChange();
          }
        } else {
          console.error('Échec de mise à jour du multiplicateur');
        }
      } else {
        console.error('Erreur HTTP lors de la mise à jour:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Erreur lors du changement du multiplicateur:', error);
    } finally {
      setLoading(false);
    }
  };

  // Calcul des effets du bâtiment
  const currentLevel = building?.level || 1;
  const foodSupply = building?.effect?.food_supply || 0;
  const maxMultiplier = building?.effect?.cereal_consumption_multiplier || 2;

  // Informations de population
  const popNourishedByWindmill = city?.resources?.pop_nourished_by_windmill || 0;
  const currentPopulation = city?.resources?.population_total || 0;
  // const totalCerealConsumption = city?.resources?.cereal_needed || 0; // Unused for now

  // Calcul de l'effet du multiplicateur sur la consommation
  const baseConsumptionRate = 0.1; // Doit correspondre à POPULATION_CONSTANTS["CEREAL_CONSUMPTION_PER_PERSON"]
  const popNotFedByTownHall = Math.max(0, currentPopulation - (city?.resources?.pop_nourished_by_townhall || 0));
  const popUsingWindmill = Math.min(popNotFedByTownHall, popNourishedByWindmill);
  const cerealConsumptionByWindmill = popUsingWindmill * baseConsumptionRate * cerealMultiplier;

  // DEBUG : Vérifier l'état du bouton Appliquer
  const isButtonDisabled = loading || cerealMultiplier === confirmedMultiplier;
  return (
    <div className="popup-content">
      {/* Titre et informations de base */}
      <div className="popup-header">
        <h3>{building?.name || 'Moulin'} - Niveau {currentLevel}</h3>
      </div>

      {/* Statistiques du moulin */}
      <div className="popup-section">
        <div className="popup-section-title">Capacité alimentaire :</div>
        <div className="popup-stats-grid">
          <div>Population nourrie : {Math.floor(popNourishedByWindmill)}</div>
          <div>Capacité totale : {foodSupply}</div>
        </div>
      </div>

      {/* Contrôle du multiplicateur de céréales */}
      <div className="popup-section highlight">
        <div className="popup-section-title">Multiplicateur de consommation :</div>
        
        {/* Slider pour le multiplicateur */}
        <div style={{ margin: '10px 0' }}>
          <label style={{ display: 'block', marginBottom: '5px' }}>
            Multiplicateur actuel : ×{cerealMultiplier.toFixed(2)}
          </label>
          <div style={{ fontSize: '0.8em', color: '#666', marginBottom: '5px' }}>
            DEBUG: slider={cerealMultiplier.toFixed(2)}, confirmé={confirmedMultiplier.toFixed(2)}, bouton={isButtonDisabled ? 'désactivé' : 'actif'}
          </div>
          <input
            type="range"
            min="1"
            max={maxMultiplier}
            step="0.1"
            value={cerealMultiplier}
            onChange={(e) => {
              const newValue = parseFloat(e.target.value);
              setCerealMultiplier(newValue);
            }}
            disabled={loading}
            style={{ width: '100%' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8em', color: '#666' }}>
            <span>1.0 (Min)</span>
            <span>{maxMultiplier.toFixed(1)} (Max)</span>
          </div>
        </div>

        {/* Boutons de validation */}
        <div className="popup-button-group" style={{ marginTop: '10px' }}>
          <button
            onClick={() => {
              handleMultiplierChange(cerealMultiplier);
            }}
            disabled={isButtonDisabled}
            className="popup-action-button primary"
          >
            {loading ? 'Application...' : 'Appliquer'}
          </button>
          <button
            onClick={() => setCerealMultiplier(confirmedMultiplier)}
            disabled={loading}
            className="popup-action-button secondary"
          >
            Annuler
          </button>
        </div>

        {/* Informations sur l'effet */}
        <div style={{ marginTop: '10px', fontSize: '0.9em' }}>
          <div>• Consommation par hab. : {(baseConsumptionRate * cerealMultiplier * 360).toFixed(1)} céréales/h</div>
          <div>• Population utilisant le moulin : {Math.floor(popUsingWindmill)}</div>
          <div>• Consommation totale moulin : {(cerealConsumptionByWindmill * 360).toFixed(1)} céréales/h</div>
          <div>• Bonus de satisfaction : +{Math.floor(cerealMultiplier * 10)} points</div>
        </div>
      </div>

      {/* Informations de débogage */}
      <div style={{ fontSize: '0.8em', color: '#666', marginTop: '10px' }}>
        Debug: multiplier={cerealMultiplier}, max={maxMultiplier}, loading={loading}
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

