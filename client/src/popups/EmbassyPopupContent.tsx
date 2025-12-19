import React, { useState, useEffect } from 'react';
import { useUser } from '../hooks/useUser';

interface EmbassyPopupContentProps {
  city: any;
  building: any;
  onClose: () => void;
  onCityDataChange?: () => void;
}

const EmbassyPopupContent: React.FC<EmbassyPopupContentProps> = ({
  city,
  building,
  onClose,
  onCityDataChange,
}) => {
  const { user } = useUser();
  const [playerColonies, setPlayerColonies] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const buildingLevel = building?.level || 1;
  const maxColonies = building?.effect?.max_colonies || 1;
  const image = building?.image || 'assets/buildings/ambassade.png';
  const description = building?.description || "Permet de fonder et de gérer des colonies. Chaque niveau augmente le nombre maximum de colonies.";

  // Charger le nombre de colonies du joueur
  useEffect(() => {
    const loadPlayerColonies = async () => {
      if (!user?.id) return;
      
      try {
        const response = await fetch(`/api/auth/player/${user.id}/cities`);
        if (response.ok) {
          const data = await response.json();
          setPlayerColonies(data.cities.length);
        }
      } catch (err) {
        console.error('Erreur chargement colonies:', err);
      }
    };

    loadPlayerColonies();
  }, [user?.id]);

  const handleColonize = async () => {
    if (!user?.id) return;

    setLoading(true);
    setError(null);

    try {
      // Cette fonction devrait déclencher le processus de colonisation
      // Pour l'instant, on affiche juste un message
      setError('Fonctionnalité de colonisation à implémenter');
      
      // TODO: Implémenter la logique de colonisation
      // const response = await fetch(`/api/player/${user.id}/colonize`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ city_id: city.id })
      // });
      
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="popup-content">
      <h3 className="popup-title">Ambassade - Niveau {buildingLevel}</h3>
      <img src={image} alt="Ambassade" style={{width: '80px', marginBottom: '10px'}} />
      
      <div className="popup-section info">
        <div>{description}</div>
      </div>
      
      <div className="popup-stats-grid">
        <div>🏝️ Colonies autorisées : <strong>{maxColonies}</strong></div>
        <div>🌍 Colonies fondées : <strong>{playerColonies}</strong></div>
      </div>
      
      <div className="popup-section warning">
        <button
          onClick={handleColonize}
          disabled={playerColonies >= maxColonies || loading}
          className="popup-action-button primary roman-button"
        >
          {loading ? 'Colonisation...' : 'Coloniser une ville libre'}
        </button>
        
        {playerColonies >= maxColonies && (
          <div className="popup-error-message">
            Limite de colonies atteinte pour ce niveau
          </div>
        )}
        
        {error && (
          <div className="popup-error-message">
            ⚠️ {error}
          </div>
        )}
      </div>
      
      <div className="popup-actions">
        <button onClick={onClose} className="popup-action-button secondary roman-button">
          Fermer
        </button>
      </div>
    </div>
  );
};

export default EmbassyPopupContent;
