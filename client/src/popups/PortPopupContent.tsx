import React, { useState, useEffect } from 'react';
import { useUser } from '../hooks/useUser';
import TransportPopup from './TransportPopup';
import TransportsListPopup from './TransportsListPopup';
import { useTransportConstants } from '../hooks/useTransportConstants';

interface PortPopupContentProps {
  city: any; // Type à améliorer plus tard
  building: any; // Données du bâtiment port
  onClose: () => void;
  onCityDataChange?: () => void; // Fonction pour notifier les changements
}

interface CityInfo {
  id: string;
  name: string;
  island_id: string;
  island_coords?: [number, number];
}

interface PlayerInfo {
  id: string;
  transport_ships_total: number;
  transport_ships_available: number;
}

const PortPopupContent: React.FC<PortPopupContentProps> = ({
  city,
  building,
  onClose,
  onCityDataChange,
}) => {
  const { user } = useUser();
  const { constants: transportConstants, loading: constantsLoading } = useTransportConstants();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // États pour les données du port
  const [playerCities, setPlayerCities] = useState<CityInfo[]>([]);
  const [playerInfo, setPlayerInfo] = useState<PlayerInfo | null>(null);
  const [goldAvailable, setGoldAvailable] = useState(0);
  const [transportSpeed, setTransportSpeed] = useState<number>(0); // Sera mis à jour avec les constantes
  
  // Mettre à jour la vitesse de transport quand les constantes sont chargées
  useEffect(() => {
    if (transportConstants) {
      setTransportSpeed(transportConstants.transport_speed);
    }
  }, [transportConstants]);
  
  // États pour le popup de transport
  const [showTransportPopup, setShowTransportPopup] = useState(false);
  const [selectedDestinationCity, setSelectedDestinationCity] = useState<CityInfo | null>(null);
  
  // État pour le popup de liste des transports
  const [showTransportsList, setShowTransportsList] = useState(false);
  
  // Données de base du bâtiment
  const buildingLevel = building?.level || 1;
  
  // Calculs basés sur le niveau
  const loadingSpeed = getLoadingSpeed(buildingLevel);
  const nextShipPrice = getNextShipPrice(playerInfo?.transport_ships_total || 0);
  const upgradePrice = getUpgradePrice(buildingLevel);

  // Charger les données initiales
  const loadInitialData = React.useCallback(async () => {
    if (!user?.id || !city?.id) return;
    
    try {
      // Charger les données des villes du joueur et la vitesse de transport
      await Promise.all([
        loadPlayerCities(),
        loadPlayerInfo(),
        loadCityResources(),
        loadTransportSpeed()
      ]);
    } catch (err) {
      console.error('Erreur chargement données initiales:', err);
    }
  }, [user?.id, city?.id]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Mise à jour automatique des données toutes les 15 secondes
  useEffect(() => {
    if (!user?.id || !city?.id) return;

    const interval = setInterval(() => {
      loadInitialData();
    }, 15000);

    return () => clearInterval(interval);
  }, [loadInitialData]);

  const loadPlayerCities = async () => {
    if (!user?.id) return;
    
    try {
      const response = await fetch(`/api/auth/player/${user.id}/cities`);
      if (response.ok) {
        const data = await response.json();
        // Filtrer pour exclure la ville actuelle
        const otherCities = data.cities.filter((c: CityInfo) => c.id !== city?.id);
        setPlayerCities(otherCities);
      }
    } catch (err) {
      console.error('Erreur chargement villes du joueur:', err);
    }
  };

  const loadPlayerInfo = async () => {
    if (!user?.id) return;
    
    try {
      const response = await fetch(`/api/player/${user.id}`);
      if (response.ok) {
        const data = await response.json();
        setPlayerInfo({
          id: data.player_info?.id,
          transport_ships_total: data.player_info?.transport_ships_total || 0,
          transport_ships_available: data.player_info?.transport_ships_available || 0
        });
      }
    } catch (err) {
      console.error('Erreur chargement informations joueur:', err);
    }
  };

  const loadCityResources = async () => {
    if (!city?.id || !user?.id) return;
    
    try {
      // Charger les informations du joueur pour l'or
      const playerResponse = await fetch(`/api/player/${user.id}/info`);
      if (playerResponse.ok) {
        const playerData = await playerResponse.json();
        setGoldAvailable(playerData.player_info?.gold || 0);
      }
    } catch (err) {
      console.error('Erreur chargement ressources joueur:', err);
    }
  };

  const loadTransportSpeed = async () => {
    try {
      const response = await fetch('/api/transport/constants');
      if (response.ok) {
        const data = await response.json();
        setTransportSpeed(data.transport_speed || transportConstants?.transport_speed);
      }
    } catch (err) {
      console.error('Erreur chargement vitesse transport:', err);
      // Utiliser les constantes du hook en cas d'erreur
      if (transportConstants?.transport_speed) {
        setTransportSpeed(transportConstants.transport_speed);
      }
    }
  };

  const buyShip = async () => {
    if (!user?.id || !city?.id) {
      setError('Données manquantes pour l\'achat');
      return;
    }

    if (goldAvailable < nextShipPrice) {
      setError(`Or insuffisant. Requis: ${nextShipPrice}, disponible: ${Math.floor(goldAvailable)}`);
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/player/${user.id}/buy-ship`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          city_id: city.id
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Erreur lors de l\'achat du bateau');
      }
      
      const result = await response.json();
      
      // Mettre à jour les données locales
      if (result.player_info) {
        setPlayerInfo(result.player_info);
      }
      if (result.new_gold !== undefined) {
        setGoldAvailable(result.new_gold);
      }
      
      // Recharger toutes les données
      await loadInitialData();
      
      // Notifier le parent pour qu'il recharge ses données
      if (onCityDataChange) {
        onCityDataChange();
      }
      
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const openTransportPopup = (destinationCity: CityInfo) => {
    setSelectedDestinationCity(destinationCity);
    setShowTransportPopup(true);
  };

  // Gestionnaire appelé après création d'un transport
  const handleTransportCreated = React.useCallback(async () => {
    try {
      // Recharger les informations du joueur (nombre de bateaux disponibles)
      await loadPlayerInfo();
      
      // Notifier le Layout pour rafraîchir les données du HeaderBar
      window.dispatchEvent(new CustomEvent('refreshPlayerInfo'));
      
      // Notifier le parent que les données ont changé (pour compatibilité)
      if (onCityDataChange) {
        onCityDataChange();
      }
    } catch (err) {
      console.error('Erreur lors du rafraîchissement après transport:', err);
    }
  }, [loadPlayerInfo, onCityDataChange]);

  return (
    <div className="popup-content">
      <h3 className="popup-title">Port - Niveau {buildingLevel}</h3>
      
      {/* Informations du port */}
      <div className="popup-stats-grid">
        <div>⚓ Niveau du port : <strong>{buildingLevel}</strong></div>
        <div>📦 Vitesse de chargement : <strong>{loadingSpeed} unités/sec</strong></div>
        <div>🚢 Vitesse de transport : <strong>{transportSpeed} unités/sec</strong></div>
        <div>💰 Or disponible : <strong>{Math.floor(goldAvailable)}</strong></div>
      </div>

      {/* Informations des bateaux */}
      <div className="popup-section info">
        <div className="popup-section-title">🚢 Flotte de bateaux</div>
        <div className="popup-stats-grid">
          <div>Bateaux de transport : <strong>{playerInfo?.transport_ships_available || 0}/{playerInfo?.transport_ships_total || 0}</strong></div>
        </div>
      </div>

      {/* Achat de bateau */}
      <div className="popup-section warning">
        <div className="popup-section-title">🛒 Acheter un bateau</div>
        <div>Prix du prochain bateau : <strong>{nextShipPrice} or</strong></div>
        <div>Prix amélioration port : <strong>{upgradePrice} or</strong></div>
        
        <div className="popup-input-group" style={{ marginTop: '10px' }}>
          <button
            onClick={buyShip}
            disabled={loading || goldAvailable < nextShipPrice}
            className={`popup-action-button ${goldAvailable >= nextShipPrice ? 'primary' : ''} roman-button`}
            style={{
              opacity: (loading || goldAvailable < nextShipPrice) ? 0.6 : 1,
              cursor: (loading || goldAvailable < nextShipPrice) ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Achat en cours...' : `Acheter un bateau (${nextShipPrice} or)`}
          </button>
        </div>
        
        {error && (
          <div className="popup-error-message">
            ⚠️ {error}
          </div>
        )}
      </div>

      {/* Liste des villes de destination */}
      <div className="popup-section highlight">
        <div className="popup-section-title">🗺️ Villes de destination</div>
        {playerCities.length === 0 ? (
          <div className="popup-section-details">
            Aucune autre ville disponible pour le transport.
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: 'var(--spacing-sm)',
            marginTop: 'var(--spacing-sm)'
          }}>
            {playerCities.map((cityInfo) => (
              <button
                key={cityInfo.id}
                onClick={() => openTransportPopup(cityInfo)}
                className="roman-button"
                disabled={!playerInfo?.transport_ships_available || playerInfo.transport_ships_available <= 0}
                style={{
                  opacity: (!playerInfo?.transport_ships_available || playerInfo.transport_ships_available <= 0) ? 0.6 : 1,
                  cursor: (!playerInfo?.transport_ships_available || playerInfo.transport_ships_available <= 0) ? 'not-allowed' : 'pointer'
                }}
              >
                <div className="roman-subtitle" style={{ marginBottom: '4px' }}>{cityInfo.name}</div>
                <div className="roman-text" style={{ fontSize: '0.8em' }}>
                  {cityInfo.island_coords ? 
                    `Île (${cityInfo.island_coords[0]},${cityInfo.island_coords[1]})` : 
                    `Île ${cityInfo.island_id || 'inconnue'}`
                  }
                </div>
              </button>
            ))}
          </div>
        )}
        
        {playerCities.length > 0 && (!playerInfo?.transport_ships_available || playerInfo.transport_ships_available <= 0) && (
          <div className="popup-section-details" style={{ color: 'var(--roman-red)', marginTop: '10px' }}>
            ⚠️ Aucun bateau disponible pour le transport
          </div>
        )}
      </div>

      {/* Section des transports en cours */}
      <div className="popup-section info">
        <div className="popup-section-title">🚛 Transports en cours</div>
        <div className="popup-section-details" style={{ marginBottom: '10px' }}>
          Gérez vos transports de marchandises entre vos villes
        </div>
        
        <div className="popup-input-group">
          <button
            onClick={() => setShowTransportsList(true)}
            className="popup-action-button secondary roman-button"
          >
            📋 Voir les transports en cours
          </button>
        </div>
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

      {/* Popup de transport */}
      {showTransportPopup && selectedDestinationCity && (
        <TransportPopup
          sourceCity={{
            id: city.id,
            name: city.name,
            resources: city.resources || {},
            buildings: city.buildings || []
          }}
          destinationCity={selectedDestinationCity}
          onClose={() => {
            setShowTransportPopup(false);
            setSelectedDestinationCity(null);
          }}
          onTransportCreated={handleTransportCreated}
        />
      )}

      {/* Popup de liste des transports */}
      {showTransportsList && (
        <TransportsListPopup
          onClose={() => setShowTransportsList(false)}
        />
      )}
    </div>
  );
};

// Fonctions utilitaires basées sur le code Kivy
function getLoadingSpeed(level: number): number {
  // Vitesse de chargement basée sur les vraies valeurs du buildings.json
  const loadingSpeeds = {
    1: 10,
    2: 14,
    3: 19
  };
  return loadingSpeeds[level as keyof typeof loadingSpeeds] || 10;
}

function getNextShipPrice(currentShips: number): number {
  // Prix exponentiel basé sur le nombre de bateaux (commence à 0)
  const base = 100;
  return Math.ceil(base * Math.pow(1.5, currentShips));
}

function getUpgradePrice(level: number): number {
  // Prix d'amélioration du port
  return 200 * level;
}

export default PortPopupContent;
