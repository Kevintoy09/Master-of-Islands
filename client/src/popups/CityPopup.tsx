



import React, { useState, useEffect } from 'react';
import AttackPopupV3 from './AttackPopupV3';

// Charger buildings.json une seule fois au chargement du module
let buildingsDataCache: any = null;
async function getBuildingsData() {
  if (!buildingsDataCache) {
    try {
      const response = await fetch('/data/buildings.json');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      buildingsDataCache = await response.json();
    } catch (error) {
      console.error('Erreur chargement buildings.json:', error);
      buildingsDataCache = {};
    }
  }
  return buildingsDataCache;
}

const btnStyle: React.CSSProperties = {
  display: 'block', 
  width: '100%', 
  padding: '8px 12px', 
  margin: '4px 0', 
  fontSize: 14,
  background: 'linear-gradient(135deg, #8b7355 0%, #6d5a44 100%)', 
  color: '#e8d7c3', 
  border: '1px solid #8b7355', 
  borderRadius: 6,
  cursor: 'pointer', 
  fontFamily: 'inherit', 
  fontWeight: 500, 
  transition: 'all 0.2s'
};





interface CityPopupProps {
  city: any;
  player: any;
  ownedCities: any[];
  currentActiveCity?: any; // Ville active du header bar
  isOpen: boolean;
  onClose: () => void;
  onColonize?: (city: any) => void;
  onEnterCity?: (city: any) => void;
  onViewCity?: (city: any) => void;
  onSendMessage?: (city: any) => void;
  onTransportGoods?: (city: any) => void;
  onAttackCity?: (city: any) => void;
  // Ajoutez d'autres callbacks selon vos besoins
}

const CityPopup: React.FC<CityPopupProps> = ({
  city,
  player,
  ownedCities,
  currentActiveCity,
  isOpen,
  onClose,
  onColonize,
  onEnterCity,
  onViewCity,
  onSendMessage,
  onTransportGoods,
  onAttackCity,
}) => {
  // États pour le popup d'attaque supprimés - utilisation de V3 seulement
  
  // État pour les données du joueur propriétaire
  const [ownerData, setOwnerData] = useState<any>(null);
  
  // États pour le popup d'attaque V3
  const [showAttackPopupV3, setShowAttackPopupV3] = useState(false);
  const [attackerCityV3, setAttackerCityV3] = useState<any>(null);
  const [popupMode, setPopupMode] = useState<'attack' | 'transport' | 'protect'>('attack');
  const [ambassade, setAmbassade] = useState<any>(null);

  // Charger les données du joueur propriétaire
  useEffect(() => {
    const loadOwnerData = async () => {
      if (!city?.owner && !city?.ownerId) {
        setOwnerData(null);
        return;
      }

      try {
        const ownerId = city.owner || city.ownerId;
        
        // Charger les informations de base du joueur
        const playersResponse = await fetch('/api/players');
        
        if (!playersResponse.ok) {
          throw new Error(`Erreur HTTP: ${playersResponse.status}`);
        }
        
        const playersData = await playersResponse.json();
        const players = playersData.players || playersData;
        
        const ownerInfo = players.find((p: any) => 
          p.id === ownerId || p.name === ownerId || p.username === ownerId
        );
        
        if (ownerInfo) {
          // Charger les statistiques enrichies (construction_points, military_power)
          try {
            const progressionResponse = await fetch(`/api/progression/${ownerInfo.id}`);
            if (progressionResponse.ok) {
              const progressionData = await progressionResponse.json();
              if (progressionData.success && progressionData.scores) {
                // Fusionner les données de base avec les scores calculés
                setOwnerData({
                  ...ownerInfo,
                  construction_points: progressionData.scores.construction_points,
                  military_power: progressionData.scores.military_power
                });
                return;
              }
            }
          } catch (err) {
            console.warn('Impossible de charger les statistiques enrichies:', err);
          }
          
          // Si l'API progression échoue, utiliser les données de base
          setOwnerData(ownerInfo);
        } else {
          setOwnerData(null);
        }
      } catch (error) {
        console.error('Erreur lors du chargement des données du joueur:', error);
        setOwnerData(null);
      }
    };

    if (isOpen && city) {
      loadOwnerData();
    }
  }, [isOpen, city, city?.owner, city?.ownerId]);

  // Charger les données de l'ambassade avec effect depuis buildings.json
  useEffect(() => {
    const loadAmbassadeData = async () => {
      const buildingsData = await getBuildingsData();
      
      // Recherche de l'ambassade dans les villes du joueur
      function normalize(str: string): string {
        return String(str || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
      }
      
      for (const ownedCity of ownedCities) {
        for (const building of ownedCity.buildings || []) {
          const normalizedName = normalize(building.name);
          
          if (normalizedName.includes('ambassade')) {
            // Enrichir avec les données de buildings.json
            const buildingConfig = buildingsData['Ambassade'];
            
            if (buildingConfig?.levels) {
              const levelData = buildingConfig.levels.find((l: any) => l.level === building.level);
              
              const enrichedBuilding = {
                ...building,
                effect: levelData?.effect || {}
              };
              setAmbassade(enrichedBuilding);
              return;
            }
          }
        }
      }
      setAmbassade(null);
    };

    if (isOpen && ownedCities.length > 0) {
      loadAmbassadeData();
    }
  }, [isOpen, ownedCities]);

  // Early return après tous les hooks
  if (!isOpen || !city) return null;

  // Variables dérivées (après hooks, avant return)
  const isUnoccupied = !city.owner;
  const coloniesPossedees = Math.max(0, ownedCities.length - 1);
  const maxColoniesAutorisees = ambassade?.effect?.max_colonies || 0;
  // Vérifie si le joueur actif possède la ville (destination)
  const isOwner = city.owner && player && (city.owner === player.id || city.ownerId === player.id);

  // Vérifie si le joueur possède la ville source (currentActiveCity)
  const ownsActiveCity = currentActiveCity && player && (
    currentActiveCity.owner === player.id || 
    currentActiveCity.ownerId === player.id ||
    currentActiveCity.owner === player.name ||
    currentActiveCity.ownerId === player.name
  );

  // Fonction pour gérer l'attaque V2 d'une ville
  const handleAttackCityV2 = async (targetCity: any) => {
    try {
      
      if (!player?.id) {
        alert('Aucun joueur connecté.');
        return;
      }

      if (!currentActiveCity) {
        alert('Aucune ville active sélectionnée. Veuillez sélectionner une ville dans la barre d\'en-haut.');
        return;
      }

      // Récupérer l'état complet de la ville active (avec bâtiments)
        const response = await fetch(`/api/city/${currentActiveCity.id}/state`);
      
      const cityData = await response.json();
      
      if (!response.ok) {
        throw new Error(cityData.message || cityData.error || 'Impossible de récupérer les données de la ville');
      }

      const buildings = cityData.buildings || [];
      
      // Vérifier que la ville a un port
      const hasPort = buildings.some((building: any) => 
        building && building.name && 
        building.name.toLowerCase().includes('port') && 
        building.level >= 1
      );
      
      if (!hasPort) {
        alert(`[V2] Votre ville active "${currentActiveCity.name}" n'a pas de port. Vous devez construire un port pour pouvoir attaquer.`);
        return;
      }

      // Vérifier que la ville a des casernes
      const hasBarracks = buildings.some((building: any) => 
        building && building.name && 
        building.name.toLowerCase().includes('caserne') && 
        building.level >= 1
      );
      
      if (!hasBarracks) {
        alert(`[V2] Votre ville active "${currentActiveCity.name}" n'a pas de casernes. Vous devez construire des casernes pour avoir des unités militaires.`);
        return;
      }

      // Préparer les données de la ville attaquante avec les détails complets
      const attackingCity = {
        id: cityData.id,
        name: cityData.name,
        owner: cityData.owner, // Ajouter le propriétaire
        resources: cityData.resources || {},
        buildings: buildings
      };

      // V2 supprimé - redirection vers V3
      handleAttackCityV3(targetCity);
      
    } catch (err: any) {
      console.error('❌ [V2] Erreur complète handleAttackCityV2:', {
        error: err,
        message: err.message,
        stack: err.stack,
        currentActiveCity,
        targetCity
      });
      alert('[V2] Erreur lors de la préparation de l\'attaque : ' + err.message);
    }
  };

  // Fonction pour gérer l'attaque V3 d'une ville (VERSION PROPRE)
  const handleAttackCityV3 = async (targetCity: any) => {
    try {
      if (!currentActiveCity) {
        alert('[V3] Aucune ville active sélectionnée. Veuillez sélectionner une ville depuis laquelle attaquer.');
        return;
      }

      // Préparer les données de base (plus simple que V2)
      const attackingCity = {
        id: currentActiveCity.id,
        name: currentActiveCity.name,
        owner: player.id,
        x: currentActiveCity.x,
        y: currentActiveCity.y
      };

      setAttackerCityV3(attackingCity);
      setPopupMode('attack');
      setShowAttackPopupV3(true);

    } catch (err: any) {
      console.error('❌ [V3] Erreur handleAttackCityV3:', err);
      alert('[V3] Erreur lors de la préparation de l\'attaque : ' + err.message);
    }
  };

  // Fonction pour gérer la protection V3 d'une ville (NOUVELLE FONCTIONNALITÉ)
  const handleProtectCityV3 = async (targetCity: any) => {
    try {
      if (!currentActiveCity) {
        alert('[V3] Aucune ville active sélectionnée. Veuillez sélectionner une ville depuis laquelle protéger.');
        return;
      }

      // Préparer les données de base (identique à l'attaque)
      const protectingCity = {
        id: currentActiveCity.id,
        name: currentActiveCity.name,
        owner: player.id,
        x: currentActiveCity.x,
        y: currentActiveCity.y
      };

      setAttackerCityV3(protectingCity);
      setPopupMode('protect'); // Nouveau mode pour la protection
      setShowAttackPopupV3(true);

    } catch (err: any) {
      console.error('❌ [V3] Erreur handleProtectCityV3:', err);
      alert('[V3] Erreur lors de la préparation de la protection : ' + err.message);
    }
  };

  // Fonction pour gérer l'ouverture du popup de transport d'unités
  const handleMoveUnits = () => {
    if (!currentActiveCity) {
      alert('Aucune ville active sélectionnée. Veuillez sélectionner une ville depuis laquelle déplacer les unités.');
      return;
    }

    if (!ownsActiveCity) {
      alert(`Vous ne pouvez déplacer des unités que depuis vos propres villes. La ville ${currentActiveCity.name} appartient à ${currentActiveCity.owner || currentActiveCity.ownerId || 'un autre joueur'}.`);
      return;
    }



    // Utiliser AttackPopupV3 en mode transport
    setAttackerCityV3({
      id: currentActiveCity.id,
      name: currentActiveCity.name,
      owner: player.id,
      x: currentActiveCity.x,
      y: currentActiveCity.y
    });
    setPopupMode('transport');
    setShowAttackPopupV3(true);
  };



  return (
    <>
      {isOpen && (
        <>
        {/* Zone de clic invisible pour fermer le popup */}
        <div style={{
          position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', zIndex: 9998
        }} onClick={onClose} />
        {/* Conteneur du popup */}
        <div className="city-popup-overlay" style={{
          position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', zIndex: 9999,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          pointerEvents: 'none' // Permet de cliquer à travers l'overlay
        }}>
          <div className="city-popup-window" style={{
            background: '#2c2c2c', borderRadius: 12, boxShadow: '0 8px 32px rgba(139, 115, 85, 0.4)', 
            border: '2px solid #8b7355', padding: 20, 
            minWidth: '280px', maxWidth: '320px', width: '85vw',
            color: '#e8d7c3', position: 'relative', fontFamily: 'inherit',
            pointerEvents: 'auto',
            margin: '20px'
          }} onClick={e => e.stopPropagation()}>
            <div style={{display: 'flex', alignItems: 'center', marginBottom: 12}}>
              <h2 style={{fontSize: 18, fontWeight: 'bold', margin: 0, color: '#d4c4a8'}}>{city.name || `Ville ${city.id}`}</h2>
            </div>
            <div style={{marginBottom: 15, background: 'rgba(139, 115, 85, 0.2)', padding: '10px', borderRadius: '8px', border: '1px solid #8b7355'}}>
              <div style={{fontSize: '14px', marginBottom: '4px'}}><span style={{color: '#d4c4a8'}}>ID :</span> {city.id}</div>
              {city.owner && (
                <>
                  <div style={{fontSize: '14px', marginBottom: '4px'}}>
                    <span style={{color: '#d4c4a8'}}>Joueur :</span> {ownerData?.username || 'Chargement...'}
                  </div>
                  <div style={{fontSize: '14px', marginBottom: '4px'}}>
                    <span style={{color: '#d4c4a8'}}>Points Construction :</span> {ownerData?.construction_points || 0}
                  </div>
                  <div style={{fontSize: '14px'}}>
                    <span style={{color: '#d4c4a8'}}>Puissance Armée :</span> {ownerData?.military_power || 0}
                  </div>
                </>
              )}
            </div>
            <div style={{marginBottom: 12}}>
              {!city.owner ? (
                !player ? (
                  <div style={{color: '#ffb'}}>Aucun joueur connecté.</div>
                ) : !ambassade ? (
                  <div style={{color: '#ffb'}}>Construisez une Ambassade pour coloniser.</div>
                ) : coloniesPossedees >= maxColoniesAutorisees ? (
                  <div style={{color: '#ffb'}}>Limite de colonies atteinte ({coloniesPossedees}/{maxColoniesAutorisees}). Améliorez l'Ambassade.</div>
                ) : (
                  <button className="city-popup-btn" style={btnStyle} onClick={() => onColonize && onColonize(city)}>
                    Coloniser cette ville
                  </button>
                )
              ) : (
                <>
                  <button
                    className="city-popup-btn"
                    style={isOwner ? btnStyle : { ...btnStyle, opacity: 0.5, cursor: 'not-allowed' }}
                    onClick={() => {
                      if (isOwner && onEnterCity) {
                        console.log('CityPopup: Entrer dans la ville cliqué, ville:', city);
                        onEnterCity(city);
                      } else {
                        console.log('CityPopup: Bouton désactivé ou callback manquant');
                      }
                    }}
                    disabled={!isOwner}
                  >
                    {isOwner ? 'Entrer dans la ville' : 'Vous n’êtes pas propriétaire de cette ville'}
                  </button>
                  <button className="city-popup-btn" style={btnStyle} onClick={() => onViewCity && onViewCity(city)}>Voir la ville</button>
                  <button 
                    className="city-popup-btn" 
                    style={btnStyle} 
                    onClick={() => {
                      const ownerId = city.owner || city.ownerId;
                      if (ownerId) {
                        // Déclencher l'événement pour ouvrir le popup de messages
                        const messageEvent = new CustomEvent('openMessagesPopup', { 
                          detail: { recipientId: ownerId } 
                        });
                        window.dispatchEvent(messageEvent);
                        onClose();
                      }
                    }}
                  >
                    ✉️ Envoyer un message
                  </button>
                  <button className="city-popup-btn" style={btnStyle} onClick={() => onTransportGoods && onTransportGoods(city)}>Transporter des marchandises</button>
                  <button 
                    className="city-popup-btn" 
                    style={ownsActiveCity ? btnStyle : { ...btnStyle, opacity: 0.5, cursor: 'not-allowed' }}
                    onClick={handleMoveUnits}
                    disabled={!ownsActiveCity}
                    title={ownsActiveCity ? "Déplacer des unités vers cette ville" : "Vous devez sélectionner une de vos villes comme source"}
                  >
                    🚚 Déplacer unités
                  </button>
                  <button className="city-popup-btn" style={{...btnStyle, opacity: 0.5}} disabled>Envoyer un espion</button>
                  {!isOwner && (
                    <>
                      <button 
                        className="city-popup-btn" 
                        style={{
                          ...btnStyle, 
                          background: 'linear-gradient(90deg, #d32f2f, #f44336)',
                          boxShadow: '0 2px 8px rgba(211, 47, 47, 0.3)'
                        }} 
                        onClick={() => handleAttackCityV3(city)}
                      >
                        ⚔️ Attaquer la ville
                      </button>
                      <button 
                        className="city-popup-btn" 
                        style={{
                          ...btnStyle, 
                          background: 'linear-gradient(90deg, #1976d2, #2196f3)',
                          boxShadow: '0 2px 8px rgba(25, 118, 210, 0.3)'
                        }} 
                        onClick={() => handleProtectCityV3(city)}
                      >
                        🛡️ Protéger la ville
                      </button>
                    </>
                  )}
                </>
              )}
            </div>
            <button onClick={onClose} style={{position: 'absolute', top: 8, right: 12, background: 'rgba(139, 115, 85, 0.3)', color: '#e8d7c3', border: '1px solid #8b7355', fontSize: 18, cursor: 'pointer', borderRadius: '4px', width: '24px', height: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center'}} title="Fermer">×</button>
          </div>
        </div>
        </>
      )}

      {/* Popup d'attaque V2 */}
      {/* Popup V2 supprimé - utilisation de V3 seulement */}

      {/* Popup d'attaque V3 - NOUVEAU ET PROPRE */}
      {showAttackPopupV3 && attackerCityV3 && (
        <AttackPopupV3
          isOpen={showAttackPopupV3}
          onClose={() => {
            setShowAttackPopupV3(false);
            setAttackerCityV3(null);
          }}
          attackerCity={attackerCityV3}
          targetCity={city}
          mode={popupMode}
          transportType={popupMode === 'transport' ? 'movement' : undefined}
          player={player}
        />
      )}


    </>
  );

// ... pas d'accolade ici

};

export default CityPopup;
