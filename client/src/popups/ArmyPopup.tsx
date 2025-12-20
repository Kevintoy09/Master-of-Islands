import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BattleReplayViewer from '../components/BattleReplayViewer';
import { useUser } from '../hooks/useUser';
import { getApiUrl } from '../utils/api';
import { RESOURCE_EMOJIS } from '../constants/resourceIcons';
import '../styles/theme.css';
import '../pages/ArmyPage.css';

interface BattleInfo {
  battleId: string;
  location: string;
  status: 'battle_ready' | 'in_progress' | 'completed';
  created_at: number;
  participants: {
    attackers: string[];
    defenders: string[];
  };
  forces: {
    attackers: { [playerId: string]: any };
    defenders: { [playerId: string]: any };
  };
  missionType: string;
  origin: string;
  destination: string;
  transportShips: number;
  totalUnits: number;
}

interface ArmyPopupProps {
  onClose: () => void;
}

const ArmyPopup: React.FC<ArmyPopupProps> = ({ onClose }) => {
  const { user } = useUser();
  const navigate = useNavigate();
  const [battles, setBattles] = useState<BattleInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [showReplay, setShowReplay] = useState(false);
  const [selectedBattleId, setSelectedBattleId] = useState<string | null>(null);

  useEffect(() => {
    if (user?.id) {
      fetchPlayerBattles();
    }
  }, [user?.id]);

  const fetchPlayerBattles = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/battles/player/${user?.id}`);
      if (response.ok) {
        const data = await response.json();
        setBattles(data.battles || []);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des batailles:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'battle_ready': return 'En attente';
      case 'in_progress': return 'En cours';
      case 'completed': return 'Terminée';
      default: return status;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'battle_ready': return '#4CAF50';
      case 'in_progress': return '#FF9800';
      case 'completed': return '#757575';
      default: return '#000';
    }
  };

  const formatBattleDate = (timestamp: number) => {
    if (!timestamp) return 'Date inconnue';
    const date = new Date(timestamp * 1000); // Convertir timestamp Unix en millisecondes
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${day}/${month}/${year} ${hours}:${minutes}`;
  };

  const handleOpenBattlefield = async (battleId: string, status: string) => {
    if (status !== 'completed') {
      onClose(); // Fermer le popup avant de naviguer
      try {
        const response = await fetch(`${getApiUrl()}/api/military/battlefield_v2/${battleId}`);
        if (response.ok) {
          const data = await response.json();
          const location = data.battlefield?.location;
          
          if (location && location.startsWith('wild_camp_')) {
            const villageNumber = location.split('_')[2];
            const islandId = villageNumber || '2';
            navigate(`/island/${islandId}?openAttack=${location}&battleId=${battleId}`);
          } else if (location && location.startsWith('city_id_')) {
            try {
              const universeResponse = await fetch(`${getApiUrl()}/api/universe`);
              if (universeResponse.ok) {
                const universeData = await universeResponse.json();
                const targetIsland = universeData.islands.find((island: any) => 
                  island.elements && island.elements.some((element: any) => element.id === location)
                );
                
                if (targetIsland) {
                  navigate(`/island/${targetIsland.id}?openAttack=${location}&battleId=${battleId}`);
                } else {
                  alert('Île contenant la ville cible non trouvée');
                }
              } else {
                alert('Erreur lors de la recherche de l\'île cible');
              }
            } catch (error) {
              console.error('Erreur lors de la recherche de l\'île:', error);
              alert('Erreur lors de la recherche de l\'île cible');
            }
          } else {
            alert('Type de bataille non supporté : ' + location);
          }
        }
      } catch (error) {
        console.error('Erreur lors du chargement de la bataille:', error);
        alert('Erreur lors de l\'ouverture de la bataille');
      }
    }
  };

  const handleShowSummary = (battleId: string) => {
    setSelectedBattleId(battleId);
    setShowReplay(true);
  };

  return (
    <>
      {/* Overlay */}
      <div 
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}
        onClick={onClose}
      >
        {/* Popup Content */}
        <div 
          style={{
            backgroundColor: '#2a1810',
            borderRadius: '12px',
            maxWidth: '900px',
            width: '100%',
            maxHeight: '90vh',
            overflow: 'auto',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
            position: 'relative'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Bouton de fermeture */}
          <button
            onClick={onClose}
            style={{
              position: 'absolute',
              top: '15px',
              right: '15px',
              background: '#8b4513',
              border: '2px solid #A0522D',
              borderRadius: '50%',
              width: '40px',
              height: '40px',
              fontSize: '20px',
              color: '#f4e4bc',
              cursor: 'pointer',
              zIndex: 10,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)'
            }}
            title="Fermer"
          >
            ✕
          </button>

          {/* Contenu du popup */}
          <div style={{ padding: '30px' }}>
            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#f4e4bc' }}>
                Chargement des opérations militaires...
              </div>
            ) : (
              <>
                <div className="army-header" style={{ marginBottom: '30px' }}>
                  <h1 style={{ color: '#f4e4bc', marginBottom: '10px' }}>🏛️ Armée - Opérations Militaires</h1>
                  <p style={{ color: '#ccc' }}>Gérez vos batailles et suivez l'évolution de vos campagnes militaires</p>
                </div>

                {battles.length === 0 ? (
                  <div className="no-battles" style={{ textAlign: 'center', padding: '40px', color: '#f4e4bc' }}>
                    <h3>Aucune opération militaire en cours</h3>
                    <p style={{ color: '#ccc' }}>Vos batailles et missions militaires apparaîtront ici.</p>
                  </div>
                ) : (
                  <div className="battles-table">
                    {/* Suppression des titres de colonnes */}

                    {battles.map((battle) => (
                      <div key={battle.battleId} className="battle-row">
                        <div className="col-mission">
                          <span className="mission-type">{battle.missionType}</span>
                          <small className="battle-id">{formatBattleDate(battle.created_at)}</small>
                        </div>
                        
                        <div className="col-ships">
                          {RESOURCE_EMOJIS.transport_ships} {battle.transportShips}
                        </div>
                        
                        <div className="col-units">
                          ⚔️ {battle.totalUnits}
                        </div>
                        
                        <div className="col-origin">
                          📍 {battle.origin}
                        </div>
                        
                        <div className="col-destination">
                          🎯 {battle.destination}
                        </div>
                        
                        <div className="col-actions">
                          <button
                            className={`action-btn ${battle.status === 'completed' ? 'disabled' : 'primary'}`}
                            onClick={() => handleOpenBattlefield(battle.battleId, battle.status)}
                            disabled={battle.status === 'completed'}
                            title={battle.status === 'completed' ? 'Bataille terminée' : 'Ouvrir le champ de bataille'}
                          >
                            ⚔️ Ouvrir
                          </button>
                          
                          <button
                            className="action-btn secondary"
                            onClick={() => handleShowSummary(battle.battleId)}
                            title="Voir le résumé détaillé"
                          >
                            � Résumé
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
      
      {/* Battle Replay Viewer */}
      {showReplay && selectedBattleId && (
        <BattleReplayViewer
          battleId={selectedBattleId}
          onClose={() => {
            setShowReplay(false);
            setSelectedBattleId(null);
          }}
        />
      )}
    </>
  );
};

export default ArmyPopup;
