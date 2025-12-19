import React, { useState, useEffect, useCallback } from 'react';
import { getPlayerColor, getPlayerColorClass } from '../utils/playerColors';
import { extractUnitType } from '../utils/combatUtils';
import { getApiUrl } from '../utils/api';
import './BattleReplayViewer.css';

interface BattleReplayViewerProps {
  battleId: string;
  onClose: () => void;
}

interface MapData {
  template: any;
  terrainDefinitions: { [code: string]: { name: string; defenseBonus: number; attackPenalty: number; movementBonus: number } };
  hexMap: string[];
}

interface ReplayData {
  metadata: {
    location: string;
    participants: {
      attackers: string[];
      defenders: string[];
    };
    result: string;
    date: number;
  };
  rounds: Array<{
    round: number;
    current_player: string;
    turns: Array<{
      player: string;
      actions: any[];
      board_state: any;
      attacker_stats: { units: number; moral: number };
      defender_stats: { units: number; moral: number };
    }>;
  }>;
}

const BattleReplayViewer: React.FC<BattleReplayViewerProps> = ({ battleId, onClose }) => {
  const [replayData, setReplayData] = useState<ReplayData | null>(null);
  const [mapData, setMapData] = useState<MapData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rawBattleData, setRawBattleData] = useState<any | null>(null);
  
  // Navigation state
  const [currentRound, setCurrentRound] = useState(0);
  const [currentTurn, setCurrentTurn] = useState(0);
  const [zoom, setZoom] = useState(80);

  // Get initial units state from round 1 "from" positions
  const getInitialUnitsState = (battleData: any): {[playerId: string]: any[]} => {
    const initialUnits: {[playerId: string]: any[]} = {};
    
    if (battleData.rounds_history && battleData.rounds_history.round_1) {
      const firstRoundMoves = battleData.rounds_history.round_1.moves || [];
      
      firstRoundMoves.forEach((move: any) => {
        if (move.move && move.move.from) {
          const playerId = move.unitId.includes('wild_camp') ? 'wild_camp' : 
                          move.unitId.includes('player_4') ? 'player_4' : 'unknown';
          
          if (!initialUnits[playerId]) initialUnits[playerId] = [];
          
          // Trouver les vraies données de cette unité dans les teams finales
          const finalUnit = battleData.teams[playerId]?.find((u: any) => u.unitId === move.unitId);
          
          initialUnits[playerId].push({
            unitId: move.unitId,
            position: move.move.from,
            unitCount: finalUnit?.unitCount || (move.unitId.includes('hero') ? undefined : 8),
            hp: finalUnit?.hp
          });
        }
      });
    }
    
    return initialUnits;
  };

  // Calculate units state at specific round
  const calculateUnitsAtRound = (battleData: any, targetRound: number): {[playerId: string]: any[]} => {
    if (targetRound === 0 || !battleData.rounds_history) {
      return getInitialUnitsState(battleData);
    }
    
    // Pour les autres rounds, partir de l'état initial et appliquer les mouvements
    const unitsState = JSON.parse(JSON.stringify(getInitialUnitsState(battleData))); // Copie profonde
    
    // Appliquer tous les rounds jusqu'au round cible
    for (let r = 1; r <= targetRound; r++) {
      const roundKey = `round_${r}`;
      const roundData = battleData.rounds_history[roundKey];
      
      if (roundData && roundData.moves) {
        roundData.moves.forEach((move: any) => {
          // Trouver l'unité dans l'état actuel
          for (const playerId in unitsState) {
            const unit = unitsState[playerId].find((u: any) => u.unitId === move.unitId);
            if (unit) {
              // Appliquer le mouvement
              if (move.move) {
                unit.position = move.move.to;
              }
              
              // Appliquer les dégâts d'attaque
              if (move.attack && move.attack.kills) {
                if (unit.unitId.includes('hero')) {
                  // Pour les héros, réduire les HP
                  unit.hp = Math.max(0, (unit.hp || 1000) - move.attack.kills * 100);
                } else {
                  // Pour les unités normales, réduire le unitCount
                  unit.unitCount = Math.max(0, (unit.unitCount || 8) - move.attack.kills);
                }
              }
              break;
            }
          }
        });
      }
    }
    
    return unitsState;
  };

  // Fonction pour convertir les vraies données de bataille en format replay
  const convertBattleDataToReplay = (battleData: any): ReplayData => {
    const rounds: any[] = [];
    
    // Détecter toutes les unités et leurs positions initiales depuis le premier round
    const allUnits: {[unitId: string]: any} = {};
    
    if (battleData.rounds_history && battleData.rounds_history.round_1) {
      const firstRoundMoves = battleData.rounds_history.round_1.moves || [];
      
      // Collecter les positions initiales depuis les "from" du premier round
      firstRoundMoves.forEach((move: any) => {
        if (move.move && move.move.from) {
          const playerId = move.unitId.includes('wild_camp') ? 'wild_camp' : 'player_4';
          const unitCount = move.unitId.includes('hero') ? 1 : 8;
          
          allUnits[move.unitId] = {
            unitId: move.unitId,
            position: move.move.from,
            unitCount: unitCount,
            playerId: playerId
          };
        }
      });
    }
    

    
    // Créer d'abord un état initial (round 0)
    const initialTeams: {[playerId: string]: any[]} = {
      player_4: [],
      wild_camp: []
    };
    
    Object.values(allUnits).forEach((unit: any) => {
      initialTeams[unit.playerId].push({
        unitId: unit.unitId,
        position: unit.position,
        unitCount: unit.unitCount
      });
    });
    
    rounds.push({
      round: 0,
      current_player: 'player_4',
      turns: [{
        player: 'player_4',
        actions: [],
        board_state: {
          units: initialTeams,
          current_round: 0,
          current_player: 'player_4'
        },
        attacker_stats: { units: initialTeams.player_4.length * 8, moral: 100 },
        defender_stats: { units: initialTeams.wild_camp.length * 6, moral: 100 }
      }]
    });
    
    // Maintenant traiter chaque round d'historique
    if (battleData.rounds_history) {
      Object.keys(battleData.rounds_history).forEach((roundKey, roundIndex) => {
        const roundData = battleData.rounds_history[roundKey];
        const moves = roundData.moves || [];
        
        // Appliquer les mouvements pour calculer les nouvelles positions
        moves.forEach((move: any) => {
          if (move.move && allUnits[move.unitId]) {
            allUnits[move.unitId].position = move.move.to;
          }
        });
        
        // Créer les teams avec les nouvelles positions
        const currentTeams: {[playerId: string]: any[]} = {
          player_4: [],
          wild_camp: []
        };
        
        Object.values(allUnits).forEach((unit: any) => {
          currentTeams[unit.playerId].push({
            unitId: unit.unitId,
            position: unit.position,
            unitCount: unit.unitCount
          });
        });
        
        rounds.push({
          round: roundIndex + 1,
          current_player: 'player_4',
          turns: [{
            player: 'player_4',
            actions: moves,
            board_state: {
              units: currentTeams,
              current_round: roundIndex + 1,
              current_player: 'player_4'
            },
            attacker_stats: { units: currentTeams.player_4.length * 8, moral: 100 - roundIndex * 5 },
            defender_stats: { units: currentTeams.wild_camp.length * 6, moral: 90 - roundIndex * 5 }
          }]
        });
      });
    }
    
    return {
      metadata: {
        location: battleData.location || 'unknown',
        participants: {
          attackers: ['player_4'],
          defenders: ['wild_camp']
        },
        result: 'ongoing',
        date: battleData.timestamp || Date.now()
      },
      rounds: rounds
    };
  };

  // Load replay data and map
  useEffect(() => {
    const loadReplayData = async () => {
      try {
        setLoading(true);
        
        // 1. Charger les VRAIES données de bataille depuis battlesv2.json
        const battleResponse = await fetch(`${getApiUrl()}/api/v2/battles/data`);
        const battlesResult = await battleResponse.json();
        
        const battleData = battlesResult[battleId];
        if (!battleData) {
          throw new Error(`Bataille ${battleId} non trouvée dans battlesv2.json`);
        }
        

        
        // 2. Charger les données du battlefield pour récupérer la map
        const battlefieldResponse = await fetch(`${getApiUrl()}/api/v2/battlefields/all`);
        const battlefieldsResult = await battlefieldResponse.json();
        
        if (battlefieldsResult.success && battlefieldsResult.battlefields[battleId]) {
          const battlefield = battlefieldsResult.battlefields[battleId];
          
          // 3. Charger la map correspondante
          const mapName = battlefield.map;

          
          const mapResponse = await fetch(`${getApiUrl()}/data/battlefields/${mapName}.json`);
          const map = await mapResponse.json();
          

          setMapData(map);
        }
        
        // 4. Sauvegarder les données brutes ET convertir en format ReplayData
        setRawBattleData(battleData);
        const replayData = convertBattleDataToReplay(battleData);

        setReplayData(replayData);
        setError(null);
      } catch (err) {
        console.error('Erreur chargement replay:', err);
        setError(err instanceof Error ? err.message : 'Erreur inconnue');
      } finally {
        setLoading(false);
      }
    };

    loadReplayData();
  }, [battleId]);

  // Navigation functions
  const goToNextTurn = useCallback(() => {
    if (!replayData) return;
    
    const currentRoundData = replayData.rounds[currentRound];
    if (!currentRoundData) return;
    
    if (currentTurn < currentRoundData.turns.length - 1) {
      setCurrentTurn(currentTurn + 1);
    } else if (currentRound < replayData.rounds.length - 1) {
      setCurrentRound(currentRound + 1);
      setCurrentTurn(0);
    }
  }, [replayData, currentRound, currentTurn]);

  const goToPreviousTurn = useCallback(() => {
    if (currentTurn > 0) {
      setCurrentTurn(currentTurn - 1);
    } else if (currentRound > 0) {
      setCurrentRound(currentRound - 1);
      const prevRoundData = replayData?.rounds[currentRound - 1];
      if (prevRoundData) {
        setCurrentTurn(prevRoundData.turns.length - 1);
      }
    }
  }, [replayData, currentRound, currentTurn]);

  const goToNextRound = useCallback(() => {
    if (!replayData) return;
    
    if (currentRound < replayData.rounds.length - 1) {
      setCurrentRound(currentRound + 1);
      setCurrentTurn(0);
    }
  }, [replayData, currentRound]);

  const goToPreviousRound = useCallback(() => {
    if (currentRound > 0) {
      setCurrentRound(currentRound - 1);
      setCurrentTurn(0);
    }
  }, [currentRound]);

  // Get current turn data
  const getCurrentTurnData = useCallback(() => {
    if (!replayData || !replayData.rounds[currentRound]) return null;
    
    const roundData = replayData.rounds[currentRound];
    const turnData = roundData.turns[currentTurn];
    
    if (!turnData) return null;
    
    const isLastTurn = currentRound === replayData.rounds.length - 1 && 
                       currentTurn === roundData.turns.length - 1;
    const isFirstTurn = currentRound === 0 && currentTurn === 0;
    

    
    return {
      round: roundData.round,
      current_player: roundData.current_player,
      turn: turnData,
      isLastTurn,
      isFirstTurn
    };
  }, [replayData, currentRound, currentTurn]);

  // Fonctions utilitaires pour la grille hexagonale
  const hexToPixel = (q: number, r: number) => {
    const size = 25;
    const x = size * (3/2 * q);
    const y = size * (Math.sqrt(3)/2 * q + Math.sqrt(3) * r);
    return { x, y };
  };

  const getHexagonPoints = (x: number, y: number) => {
    const size = 25;
    const points = [];
    for (let i = 0; i < 6; i++) {
      const angle = (Math.PI / 3) * i;
      const px = x + size * Math.cos(angle);
      const py = y + size * Math.sin(angle);
      points.push(`${px},${py}`);
    }
    return points.join(' ');
  };

  const getTerrainColor = (terrain: string) => {
    switch (terrain) {
      case 'plains': return '#9acd32';
      case 'forest': return '#228b22';
      case 'hill': return '#daa520';
      case 'mountain': return '#8b7d6b';
      case 'river': return '#4169e1';
      case 'marsh': return '#6b8e23';
      case 'road': return '#8b7355';
      case 'village': return '#cd853f';
      case 'base-attack': return '#dc143c';
      case 'base-defense': return '#4169e1';
      case 'wall': return '#8b4513';
      default: return '#9acd32';
    }
  };

  // Convertir la map en grille hexagonale
  const battleGrid = React.useMemo(() => {
    if (!mapData) return [];
    
    const hexCells = [];
    for (let r = 0; r < mapData.hexMap.length; r++) {
      for (let q = 0; q < mapData.hexMap[r].length; q++) {
        const terrainCode = mapData.hexMap[r][q];
        const terrainDef = mapData.terrainDefinitions[terrainCode];
        
        if (terrainDef) {
          hexCells.push({
            q, r,
            terrain: terrainDef.name,
            zone: 'battlefield'
          });
        }
      }
    }
    return hexCells;
  }, [mapData]);

  // Bounds pour la map
  const getBattlefieldBounds = () => {
    if (!battleGrid || battleGrid.length === 0) {
      return { minX: 0, maxX: 800, minY: 0, maxY: 600, width: 800, height: 600 };
    }
    
    const size = 25;
    const pixels = battleGrid.map(hex => {
      const x = size * (3/2 * hex.q);
      const y = size * (Math.sqrt(3)/2 * hex.q + Math.sqrt(3) * hex.r);
      return { x, y };
    });
    
    const minX = Math.min(...pixels.map(p => p.x)) - size * 2;
    const maxX = Math.max(...pixels.map(p => p.x)) + size * 2; 
    const minY = Math.min(...pixels.map(p => p.y)) - size * 2;
    const maxY = Math.max(...pixels.map(p => p.y)) + size * 2;
    
    return { minX, maxX, minY, maxY, width: maxX - minX, height: maxY - minY };
  };

  const currentData = getCurrentTurnData();

  if (loading) {
    return (
      <div className="battle-replay-viewer">
        <div className="replay-loading">
          <div className="loading-spinner"></div>
          <p>Chargement du replay de bataille...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="battle-replay-viewer">
        <div className="replay-error">
          <h3>❌ Erreur</h3>
          <p>{error}</p>
          <button onClick={onClose} className="btn-close">Fermer</button>
        </div>
      </div>
    );
  }

  if (!replayData || !currentData) {
    return (
      <div className="battle-replay-viewer">
        <div className="replay-error">
          <h3>❌ Données manquantes</h3>
          <p>Impossible de charger les données du replay</p>
          <button onClick={onClose} className="btn-close">Fermer</button>
        </div>
      </div>
    );
  }

  return (
    <div className="battle-replay-viewer">
      {/* Header with stats */}
      <div className="replay-header">
        <div className="stats-row">
          <div className="attacker-stats">
            <span className="stats-label">Attaquant:</span>
            <span className="units-count">{currentData.turn.attacker_stats.units} unités</span>
            <span className="moral-count">{currentData.turn.attacker_stats.moral} moral</span>
          </div>
          
          <div className="round-info">
            <span className="round-text">Round {currentData.round}</span>
            <span className="turn-text">Tour {currentData.current_player}</span>
            <span className="zoom-text">🔍 Zoom: {zoom}%</span>
          </div>
          
          <div className="defender-stats">
            <span className="stats-label">Défenseur:</span>
            <span className="units-count">{currentData.turn.defender_stats.units} unités</span>
            <span className="moral-count">{currentData.turn.defender_stats.moral} moral</span>
          </div>
        </div>
      </div>

      {/* Battlefield visualization */}
      <div className="replay-battlefield">
        <div style={{ position: 'relative', width: '100%', height: '100%' }}>
          
          {/* COUCHE 1 : Grille hexagonale (background) */}
          {battleGrid.length > 0 && (
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              zIndex: 1
            }}>
              <svg
                width="100%"
                height="100%"
                viewBox={`${getBattlefieldBounds().minX} ${getBattlefieldBounds().minY} ${getBattlefieldBounds().width} ${getBattlefieldBounds().height}`}
                preserveAspectRatio="xMidYMid meet"
                style={{ cursor: 'default' }}
              >
                {battleGrid.map((hex, index) => {
                  const { x, y } = hexToPixel(hex.q, hex.r);
                  const points = getHexagonPoints(x, y);
                  
                  return (
                    <g key={`${hex.q}-${hex.r}`}>
                      <polygon
                        points={points}
                        style={{
                          fill: getTerrainColor(hex.terrain),
                          stroke: '#8b7355',
                          strokeWidth: 1,
                          opacity: 0.8
                        }}
                      />
                      
                      {/* Icône de terrain */}
                      <text
                        x={x}
                        y={y + 2}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fontSize="10"
                        fill="#000"
                        style={{ pointerEvents: 'none', textShadow: '1px 1px 2px rgba(255,255,255,0.8)' }}
                      >
                        {hex.terrain === 'forest' ? '🌲' :
                         hex.terrain === 'hill' ? '⛰️' :
                         hex.terrain === 'mountain' ? '🏔️' :
                         hex.terrain === 'river' ? '🌊' :
                         hex.terrain === 'marsh' ? '🐸' :
                         hex.terrain === 'road' ? '🛤️' :
                         hex.terrain === 'village' ? '🏘️' :
                         hex.terrain === 'base-attack' ? '⚔️' :
                         hex.terrain === 'base-defense' ? '🛡️' : '🌾'}
                      </text>
                    </g>
                  );
                })}
                
                {/* UNITÉS DIRECTEMENT DEPUIS LES DONNÉES BATTLE (battlesv2.json) */}
                {rawBattleData && rawBattleData.teams && (() => {
                  const allUnits: any[] = [];
                 
                  // CALCULER L'ÉTAT ACTUEL SELON LE ROUND SÉLECTIONNÉ
                  const currentUnits = calculateUnitsAtRound(rawBattleData, currentRound);
                  
                  // Utiliser les unités calculées pour ce round
                  Object.entries(currentUnits).forEach(([playerId, playerUnits]) => {
                    if (Array.isArray(playerUnits)) {
                      playerUnits.forEach((unit: any) => {
                        if (unit && unit.position) {
                          // Déterminer l'équipe selon unitId
                          const team = unit.unitId.includes('attacker') ? 'attacker' : 'defender';
                          
                          allUnits.push({
                            ...unit,
                            playerId: playerId,
                            team: team
                          });
                        }
                      });
                    }
                  });
                  
                  return allUnits.map((unit: any, index: number) => {
                    const pos = hexToPixel(unit.position[0], unit.position[1]);
                    
                    // UTILISER LES FONCTIONS CENTRALISÉES
                    const unitType = unit.type || extractUnitType(unit.unitId);
                    const isHero = unit.unitId.includes('hero') || unitType === 'hero';
                    
                    // Utiliser le système de couleurs centralisé
                    const playerId = `player_${unit.playerId}`;
                    const playerColor = getPlayerColor(playerId, unit.team);
                    const playerColorClass = getPlayerColorClass(playerId, unit.team);
                    
                    // Système d'icônes simplifié pour le replay
                    const getIcon = (type: string) => {
                      const icons: {[key: string]: string} = {
                        'infantry': '⚔️', 'archer': '🏹', 'cavalry': '🐎', 'hero': '�'
                      };
                      return icons[type] || icons['infantry'];
                    };
                    const icon = getIcon(unitType);
                    
                    return (
                      <g key={`unit-${index}-${unit.playerId}`} className={`unit-group ${playerColorClass}`}>
                        {/* Cercle de base coloré selon le joueur */}
                        <circle
                          cx={pos.x}
                          cy={pos.y}
                          r="18"
                          fill={String(playerColor.primary) || '#4169E1'}
                          stroke={isHero ? "#FFD700" : "#000"}
                          strokeWidth={isHero ? "3" : "2"}
                          style={{ opacity: 1.0 }}
                        />
                        
                        {/* Icône de l'unité */}
                        <text
                          x={pos.x}
                          y={pos.y - 15}
                          textAnchor="middle"
                          dominantBaseline="central"
                          className="unit-icon"
                          fill="white"
                          style={{ pointerEvents: 'none', fontWeight: 'bold' }}
                        >
                          {isHero ? '👑' : icon}
                        </text>
                        
                        {/* Nombre d'unités ou HP des héros */}
                        <text
                          x={pos.x}
                          y={pos.y + 3}
                          textAnchor="middle"
                          dominantBaseline="central"
                          fill="#00FF00"
                          style={{ 
                            pointerEvents: 'none', 
                            fontWeight: 800,
                            fontFamily: 'Arial, sans-serif',
                            fontSize: '19px'
                          }}
                        >
                          {isHero && unit.hp !== undefined ? `${unit.hp}` : unit.unitCount || 1}
                        </text>
                      </g>
                    );
                  });
                })()}
              </svg>
            </div>
          )}
          
        </div>
      </div>

      {/* Navigation controls */}
      <div className="replay-controls">
        <button 
          onClick={goToPreviousRound}
          disabled={currentData.isFirstTurn}
          className="replay-btn round-btn"
          title="Round précédent"
        >
          ◄◄ Round Préc
        </button>
        
        <button 
          onClick={goToPreviousTurn}
          disabled={currentData.isFirstTurn}
          className="replay-btn turn-btn"
          title="Tour précédent"
        >
          ◄ Préc
        </button>
        
        <button 
          onClick={goToNextTurn}
          disabled={currentData.isLastTurn}
          className="replay-btn turn-btn"
          title="Tour suivant"
        >
          Suiv ►
        </button>
        
        <button 
          onClick={goToNextRound}
          disabled={currentData.isLastTurn}
          className="replay-btn round-btn"
          title="Round suivant"
        >
          Round Suiv ►►
        </button>
        
        <button 
          onClick={onClose}
          className="replay-btn close-btn"
          title="Fermer"
        >
          ✕ Fermer
        </button>
      </div>
    </div>
  );
};

export default BattleReplayViewer;
