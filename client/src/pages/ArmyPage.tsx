import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import BattleReplayViewer from '../components/BattleReplayViewer';
import { useUser } from '../hooks/useUser';
import { getApiUrl } from '../utils/api';
import '../styles/theme.css';
import './ArmyPage.css';

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

const ArmyPage: React.FC = () => {
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
      case 'battle_ready': return 'Prêt au combat';
      case 'in_progress': return 'En cours';
      case 'completed': return 'Terminé';
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

  const handleOpenBattlefield = async (battleId: string, status: string) => {
    if (status !== 'completed') {
      try {
        // Charger les données de battlefield pour obtenir la location
        const response = await fetch(`${getApiUrl()}/api/military/battlefield_v2/${battleId}`);
        if (response.ok) {
          const data = await response.json();
          const location = data.battlefield?.location;
          
          if (location && location.startsWith('wild_camp_')) {
            // Camp des sauvages - extraire le numéro de l'île depuis le nom du village
            const villageNumber = location.split('_')[2];
            const islandId = villageNumber || '2'; // Fallback vers île 2
            
            // Utiliser navigate au lieu de window.location.href pour éviter le rechargement
            navigate(`/island/${islandId}?openAttack=${location}&battleId=${battleId}`);
          } else if (location && location.startsWith('city_id_')) {
            // Ville de joueur - il faut chercher l'île qui contient cette ville
            try {
              const universeResponse = await fetch(`${getApiUrl()}/api/universe`);
              if (universeResponse.ok) {
                const universeData = await universeResponse.json();
                
                // Chercher l'île qui contient cette ville
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

  if (loading) {
    return (
        <div className="army-page">
          <div className="loading">Chargement des opérations militaires...</div>
        </div>
    );
  }

  return (
    <>
      <div className="army-page">
        <div className="army-header">
          <h1>🏛️ Armée - Opérations Militaires</h1>
          <p>Gérez vos batailles et suivez l'évolution de vos campagnes militaires</p>
        </div>

        {battles.length === 0 ? (
          <div className="no-battles">
            <h3>Aucune opération militaire en cours</h3>
            <p>Vos batailles et missions militaires apparaîtront ici.</p>
          </div>
        ) : (
          <div className="battles-table">
            <div className="table-header">
              <div className="col-mission">Mission</div>
              <div className="col-ships">Bateaux</div>
              <div className="col-units">Unités</div>
              <div className="col-origin">Origine</div>
              <div className="col-destination">Destination</div>
              <div className="col-status">Status</div>
              <div className="col-actions">Actions</div>
            </div>

            {battles.map((battle) => (
              <div key={battle.battleId} className="battle-row">
                <div className="col-mission">
                  <span className="mission-type">{battle.missionType}</span>
                  <small className="battle-id">{battle.battleId}</small>
                </div>
                
                <div className="col-ships">
                  🚢 {battle.transportShips}
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
                
                <div className="col-status">
                  <span 
                    className="status-badge"
                    style={{ backgroundColor: getStatusColor(battle.status) }}
                  >
                    {getStatusText(battle.status)}
                  </span>
                </div>
                
                <div className="col-actions">
                  <button
                    className={`action-btn ${battle.status === 'completed' ? 'disabled' : 'primary'}`}
                    onClick={() => handleOpenBattlefield(battle.battleId, battle.status)}
                    disabled={battle.status === 'completed'}
                    title={battle.status === 'completed' ? 'Bataille terminée' : 'Ouvrir le champ de bataille'}
                  >
                    🎮 Ouvrir
                  </button>
                  
                  <button
                    className="action-btn secondary"
                    onClick={() => handleShowSummary(battle.battleId)}
                    title="Voir le résumé détaillé"
                  >
                    📊 Résumé
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
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

export default ArmyPage;
