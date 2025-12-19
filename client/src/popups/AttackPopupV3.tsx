import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import '../styles/AttackPopupV3Clean.css';
import { UnifiedBattleLoaderService } from '../services/UnifiedBattleLoaderService';
import SimpleBattlefieldV2 from '../components/SimpleBattlefieldV2';
import { getApiUrl } from '../utils/api';

// ===== TYPES =====
interface UnitStats {
  name?: string;
  attack: number;
  defense: number;
  health: number;
  attack_melee?: number;
  defense_melee?: number;
  hp?: number;
  movement: number;
  cost?: { [resource: string]: number };
  max_stack_size?: number;
}

interface HeroData {
  hero_id: string;
  instance_id: string;
  current_level: number;
  name?: string;
  status?: string;
  owner?: string;
  is_available?: boolean;
  calculated_stats?: {
    hp: number;
    attack_melee: number;
    defense_melee: number;
    defense_ranged: number;
    movement: number;
    range: number;
  };
  calculated_bonuses?: {
    offensive_bonus: number;
    defensive_bonus: number;
    movement_bonus: number;
    moral_bonus: number;
    aura_radius: number;
  };
}

interface City {
  id: string;
  name: string;
  owner: string;
  x: number;
  y: number;
}

interface AttackPopupV3Props {
  isOpen: boolean;
  onClose: () => void;
  attackerCity: City;
  targetCity: City;
  onBattleStart?: (battleData: any) => void;
  mode?: 'attack' | 'transport' | 'protect'; // Nouveau: modes transport et protect
  transportType?: 'attack' | 'movement'; // Type de transport si mode = transport
  player?: any; // Informations du joueur (nécessaire pour player_id)
}

// ===== COMPOSANT PRINCIPAL =====
const AttackPopupV3: React.FC<AttackPopupV3Props> = ({
  isOpen,
  onClose,
  attackerCity,
  targetCity,
  onBattleStart,
  mode = 'attack', // Mode par défaut: attaque
  transportType = 'movement', // Type de transport par défaut: déplacement
  player // Informations du joueur
}) => {
  
  // ===== ÉTATS =====
  const [selectedUnits, setSelectedUnits] = useState<{ [unitType: string]: number }>({});
  const [availableUnits, setAvailableUnits] = useState<{ [unitType: string]: number }>({});
  const [unitStats, setUnitStats] = useState<{ [unitType: string]: UnitStats }>({});
  const [selectedHeroes, setSelectedHeroes] = useState<{ [heroId: string]: boolean }>({});
  const [availableHeroes, setAvailableHeroes] = useState<{ [heroId: string]: HeroData }>({});
  // Variables de sélection de battlefield supprimées - sélection automatique côté serveur
  const [ships, setShips] = useState(1);
  const [loading, setLoading] = useState(false);
  const [isAttacking, setIsAttacking] = useState(false); // Protection double-clic
  const [simpleBattlefieldOpen, setSimpleBattlefieldOpen] = useState(false);
  const [simpleBattlefieldData, setSimpleBattlefieldData] = useState<any>(null);
  
  // États pour les informations de transport (mode transport uniquement)
  const [transportInfo, setTransportInfo] = useState<{
    distance: number;
    transport_time: number;
    transport_speed: number;
  } | null>(null);
  const [transportError, setTransportError] = useState<string>("");
  
  const isMobile = window.innerWidth <= 768;

  // Simple prévention du scroll derrière le popup
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = 'unset';
      };
    }
  }, [isOpen]);

  // Charger les informations de transport (distance, temps) pour TRANSPORT ET ATTAQUE
  useEffect(() => {
    if (!isOpen || !attackerCity?.id || !targetCity?.id) return;

    const loadTransportInfo = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/transport/distance/${attackerCity.id}/${targetCity.id}`);
        if (response.ok) {
          const data = await response.json();
          setTransportInfo({
            distance: data.distance,
            transport_time: data.transport_time,
            transport_speed: data.transport_speed
          });
          setTransportError("");
        } else {
          const errorData = await response.json();
          setTransportError(errorData.error || "Erreur lors du calcul de distance");
          setTransportInfo(null);
        }
      } catch (err) {
        setTransportError("Erreur de connexion lors du calcul de distance");
        setTransportInfo(null);
      }
    };

    loadTransportInfo();
  }, [mode, isOpen, attackerCity?.id, targetCity?.id]);

  // Fonction getBattlefieldDisplayName supprimée - sélection automatique côté serveur

  // ===== CHARGEMENT DES DONNÉES (COPIÉ DU V2 QUI MARCHE) =====
  useEffect(() => {
    if (isOpen && attackerCity) {
      loadUnitsData();
      loadUnitStats(); 
      loadHeroesData();
      // loadBattlefields() supprimé - sélection automatique côté serveur
    }
  }, [isOpen, attackerCity]);

  const loadUnitsData = async () => {
    try {
      if (!attackerCity?.id) {
        console.error('🏰 [V3] ERREUR: Pas d\'ID de ville attaquante!');
        setAvailableUnits({});
        return;
      }
      
      const response = await fetch(`${getApiUrl()}/api/military/city/units/${attackerCity.id}`);
      
      if (response.ok) {
        const unitsData = await response.json();
        
        if (unitsData.success && unitsData.garrison) {
          const garrison = unitsData.garrison;
          const attackerUnits: { [unitType: string]: number } = {};
          
          // COPIE EXACTE DU CODE V2 QUI MARCHE
          for (const [unitType, unitData] of Object.entries(garrison)) {
            if (typeof unitData === 'number') {
              attackerUnits[unitType] = unitData;
            }
            else if (unitData && typeof unitData === 'object' && 'quantity' in unitData) {
              attackerUnits[unitType] = (unitData as any).quantity || 0;
            }
          }
          
          setAvailableUnits(attackerUnits);
        } else {
          setAvailableUnits({});
        }
      } else {
        const errorText = await response.text();
        console.error('❌ [V3] Erreur HTTP unités:', response.status, response.statusText, errorText);
        setAvailableUnits({});
      }
    } catch (error) {
      console.error('❌ [V3] Erreur chargement unités:', error);
      setAvailableUnits({});
    }
  };

  const loadUnitStats = async () => {
    try {
      const statsResponse = await fetch(`${getApiUrl()}/api/v2/unit_stats`);
      if (statsResponse.ok) {
        const allStatsData = await statsResponse.json();
        const allUnitsStats = {
          ...(allStatsData.stone_age || {}),
          ...(allStatsData.classical_age || {}),
          ...(allStatsData.medieval_age || {}),
          ...(allStatsData.renaissance_age || {}),
          ...(allStatsData.napoleonic_age || {}),
          ...(allStatsData.enemy_units || {})
        };
        setUnitStats(allUnitsStats);
      }
    } catch (error) {
      // Silently handle error
    }
  };



  const loadHeroesData = async () => {
    try {
      // 1. Récupérer les héros en garnison depuis l'API
      const response = await fetch(`${getApiUrl()}/api/military/city/heroes/${attackerCity.id}`);
      
      if (response.ok) {
        const heroesData = await response.json();
        
        if (heroesData.success && heroesData.heroes) {
          // 2. Récupérer les stats complètes depuis player_heroes.json
          const playerHeroesResponse = await fetch(`${getApiUrl()}/api/v2/player_heroes`);
          let playerHeroesData = {};
          
          if (playerHeroesResponse.ok) {
            playerHeroesData = await playerHeroesResponse.json();
          }
          
          // 3. Déterminer le propriétaire (utiliser player.id au lieu de attackerCity.owner)
          const currentPlayerId = player?.id || 'player_1';
          
          const availableHeroesForAttack: { [key: string]: HeroData } = {};
          
          Object.entries(heroesData.heroes).forEach(([instanceId, basicHeroData]: [string, any]) => {
            // Vérifier si le héros appartient au joueur actuel et est disponible
            if ((basicHeroData.status === 'garrison' || basicHeroData.status === 'available') && 
                basicHeroData.owner === currentPlayerId) {
              
              // Récupérer les données complètes du héros
              const playerData = (playerHeroesData as any)[currentPlayerId];
              const fullHeroData = playerData?.heroes?.[instanceId];
              
              if (fullHeroData) {
                availableHeroesForAttack[instanceId] = {
                  ...basicHeroData,
                  hero_id: fullHeroData.hero_id,
                  instance_id: instanceId,
                  current_level: fullHeroData.current_level,
                  name: fullHeroData.name || fullHeroData.hero_id,
                  calculated_stats: fullHeroData.calculated_stats,
                  calculated_bonuses: fullHeroData.calculated_bonuses,
                  is_available: true
                };
              }
            }
          });
          
          setAvailableHeroes(availableHeroesForAttack);
        } else {
          setAvailableHeroes({});
        }
      } else {
        setAvailableHeroes({});
      }
    } catch (error) {
      setAvailableHeroes({});
    }
  };

  // Fonction loadBattlefields supprimée - sélection automatique côté serveur

  // ===== CALCUL DES STATISTIQUES DE TRANSPORT/ATTAQUE =====
  const getTransportStats = () => {
    // Fonctionne pour transport ET attaque

    const totalUnits = Object.values(selectedUnits).reduce((sum, count) => sum + count, 0);
    const totalHeroes = Object.values(selectedHeroes).filter(Boolean).length;
    const totalEntities = totalUnits + totalHeroes;
    
    // Constantes de transport (comme dans TransportPopup)
    const UNIT_CAPACITY_PER_SHIP = 50; // Unités par navire
    const LOADING_SPEED = 10; // Unités par seconde
    const DEFAULT_TRANSPORT_SPEED = 1.5; // Unités de distance par seconde
    
    const shipsNeeded = totalEntities > 0 ? Math.ceil(totalEntities / UNIT_CAPACITY_PER_SHIP) : 0;
    const shipsToSend = Math.max(shipsNeeded, ships); // Utilise les navires spécifiés ou le minimum requis
    const loadingTime = totalEntities / LOADING_SPEED;
    
    const distance = transportInfo?.distance || 100;
    const transportSpeed = transportInfo?.transport_speed || DEFAULT_TRANSPORT_SPEED;
    const transportTime = transportInfo?.transport_time || (distance / transportSpeed);

    return {
      totalEntities,
      totalUnits,
      totalHeroes,
      shipsNeeded,
      shipsToSend,
      loadingTime,
      transportTime,
      distance,
      transportSpeed
    };
  };

  // ===== LOGIQUE MÉTIER =====
  const handleUnitChange = (unitType: string, value: number) => {
    const available = availableUnits[unitType] || 0;
    const newValue = Math.max(0, Math.min(value, available));
    
    setSelectedUnits(prev => ({
      ...prev,
      [unitType]: newValue
    }));
  };

  const handleUnitGroupAdd = (unitType: string) => {
    const stats = unitStats[unitType];
    const maxStackSize = stats?.max_stack_size || 10;
    const available = availableUnits[unitType] || 0;
    const current = selectedUnits[unitType] || 0;
    const remaining = available - current;
    const toAdd = Math.min(maxStackSize, remaining);
    const newValue = current + toAdd;
    
    setSelectedUnits(prev => ({
      ...prev,
      [unitType]: newValue
    }));
  };

  const handleUnitGroupRemove = (unitType: string) => {
    const stats = unitStats[unitType];
    const maxStackSize = stats?.max_stack_size || 10;
    const current = selectedUnits[unitType] || 0;
    const toRemove = Math.min(maxStackSize, current);
    const newValue = current - toRemove;
    
    setSelectedUnits(prev => ({
      ...prev,
      [unitType]: newValue
    }));
  };

  const handleUnitManualInput = (unitType: string, value: string) => {
    const numValue = parseInt(value) || 0;
    handleUnitChange(unitType, numValue);
  };

  const handleHeroToggle = (heroId: string) => {
    setSelectedHeroes(prev => ({
      ...prev,
      [heroId]: !prev[heroId]
    }));
  };

  const canLaunchAttack = (): boolean => {
    const totalUnits = Object.values(selectedUnits).reduce((sum, count) => sum + count, 0);
    return totalUnits > 0 && !loading && !isAttacking;
  };

  // ===== ACTIONS =====
  const handleAttack = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!canLaunchAttack()) {
      return;
    }
    setIsAttacking(true);
    setLoading(true);

    try {
      // Récupérer les héros sélectionnés (utiliser instance_id comme dans V2)
      const selectedHeroIds = Object.entries(selectedHeroes)
        .filter(([_, isSelected]) => isSelected)
        .map(([instanceId, _]) => instanceId);

      // ✅ UTILISER LE SYSTÈME DE TRANSPORT D'UNITÉS POUR LES ATTAQUES
      const attackTransportData = {
        player_id: player?.id || attackerCity.owner, // ✅ Priorité au player.id si disponible
        source_city: attackerCity.id,
        destination_city: targetCity.id,
        units: selectedUnits,
        heroes: selectedHeroIds,
        type: 'attack',
        // battlefield_template_id retiré - sélection automatique côté serveur
        ships: ships  // ✅ Nombre de bateaux choisi par le joueur
      };


      // ✅ UTILISER L'API DE TRANSPORT D'UNITÉS AVEC TYPE ATTACK
      const response = await fetch(`${getApiUrl()}/api/unit-transports`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(attackTransportData)
      }).catch(error => {
        console.error('❌ [V3] Erreur fetch réseau:', error);
        alert('Erreur de réseau: ' + error.message);
        throw error;
      });
      
      // Gérer TOUTES les réponses HTTP (même les erreurs 400+)
      const result = await response.json();

      if (response.ok && result.success) {
        
        // Message de succès indiquant que l'attaque est en route
        alert('🚢 Attaque en route ! Les troupes arrivent à destination...');
        
        // Déclencher l'événement pour mettre à jour l'interface
        window.dispatchEvent(new CustomEvent('attackTransportCreated', { 
          detail: { 
            transportId: result.transport_id,
            location: targetCity.id 
          } 
        }));
        
        // Callback optionnel (peut causer fermeture du popup)
        if (onBattleStart) {
          onBattleStart({
            attackerCity,
            defenderCity: targetCity,
            transportId: result.transport_id,
            movementId: result.transport_id, // Utiliser transport_id comme movementId pour compatibilité
            battlefieldTemplateId: 'auto' // Sélection automatique côté serveur
          });
        }
        
        // Fermer le popup après avoir lancé l'attaque avec succès
        onClose();
      } else {
        alert('❌ Erreur: ' + (result.error || 'Erreur inconnue'));
      }

    } catch (error) {
      console.error('❌ [V3] Erreur réseau:', error);
      alert('❌ Erreur de connexion');
    } finally {
      setLoading(false);
      setIsAttacking(false);
    }
  };

  // Fonction pour gérer les transports d'unités
  const handleTransport = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!canLaunchAttack()) {
      return;
    }
    
    setIsAttacking(true);
    setLoading(true);

    try {
      // Récupérer les héros sélectionnés
      const selectedHeroIds = Object.entries(selectedHeroes)
        .filter(([_, isSelected]) => isSelected)
        .map(([instanceId, _]) => instanceId);

      // Préparer les données du transport
      const transportData = {
        player_id: player?.id,
        source_city: attackerCity.id,
        destination_city: targetCity.id,
        type: transportType,
        units: selectedUnits,
        heroes: selectedHeroIds,
        ships: ships
      };

      const response = await fetch(`${getApiUrl()}/api/unit-transports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(transportData),
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Transport ${transportType === 'attack' ? 'd\'attaque' : 'de déplacement'} lancé avec succès !`);
        onClose();
      } else {
        const errorData = await response.json();
        console.error('❌ [Transport] Erreur création transport:', errorData);
        alert(`Erreur: ${errorData.message || 'Impossible de créer le transport'}`);
      }
    } catch (error) {
      console.error('❌ [Transport] Erreur réseau:', error);
      alert('Erreur de connexion au serveur');
    } finally {
      setLoading(false);
      setIsAttacking(false);
    }
  };

  // Fonction pour gérer la protection d'une ville
  const handleProtect = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!canLaunchAttack()) {
      return;
    }
    
    setIsAttacking(true);
    setLoading(true);

    try {
      // Récupérer les héros sélectionnés
      const selectedHeroIds = Object.entries(selectedHeroes)
        .filter(([_, isSelected]) => isSelected)
        .map(([instanceId, _]) => instanceId);

      // Préparer les données de protection
      const protectData = {
        attacker_city_id: attackerCity.id,
        target_city_id: targetCity.id,
        player_id: player?.id || 'player_2',
        units: selectedUnits,
        heroes: selectedHeroIds,
        ships: ships
      };

      // Appeler l'endpoint de protection
      const response = await fetch('/api/unit-transports/protect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(protectData)
      });

      if (response.ok) {
        const result = await response.json();
        alert(`🛡️ Protection lancée vers ${targetCity.name} !`);
        onClose();
      } else {
        const errorData = await response.json();
        console.error('❌ [Protect] Erreur création protection:', errorData);
        alert(`Erreur: ${errorData.message || 'Impossible de créer la protection'}`);
      }
    } catch (error) {
      console.error('❌ [Protect] Erreur réseau:', error);
      alert('Erreur de connexion au serveur');
    } finally {
      setLoading(false);
      setIsAttacking(false);
    }
  };

  // Fonction pour ouvrir le battlefield tactique V2 avec SimpleBattlefieldV2
  const handleOpenBattlefield = async () => {
    try {
      if (!targetCity?.id) {
        alert('❌ Aucune ville cible sélectionnée.');
        return;
      }

      // Utiliser le BattleLoaderService pour charger la bataille
      const battle = await UnifiedBattleLoaderService.loadBattleFromCity(targetCity.id);
      
      if (battle) {
        // ✨ Utiliser total_units pré-calculé au lieu de boucler sur contributions
        let defenderUnits: { [unitType: string]: number } = {};
        
        if (battle.forces?.defenders) {
          // Pour chaque défenseur (ex: wild_camp, player_X, etc.)
          Object.values(battle.forces.defenders).forEach((defenderData: any) => {
            // Utiliser total_units si disponible, sinon fallback sur contributions
            if (defenderData.total_units) {
              Object.entries(defenderData.total_units).forEach(([unitType, count]) => {
                defenderUnits[unitType] = (defenderUnits[unitType] || 0) + (count as number);
              });
            } else if (defenderData.contributions && Array.isArray(defenderData.contributions)) {
              // Fallback: boucler sur contributions (rétrocompatibilité)
              defenderData.contributions.forEach((contrib: any) => {
                if (contrib.units) {
                  Object.entries(contrib.units).forEach(([unitType, count]) => {
                    defenderUnits[unitType] = (defenderUnits[unitType] || 0) + (count as number);
                  });
                }
              });
            }
          });
        }
        
        // Créer les données de bataille avec la bonne carte
        const battleInfo = {
          attackerCity: attackerCity,
          defenderCity: targetCity,
          attackerUnits: battle.forces?.attackers || {},
          defenderUnits: defenderUnits,
          movementId: null,
          battleId: battle.battleId,
          battlefieldTemplateId: battle.map || 'auto', // Sélection automatique côté serveur
          targetCityId: targetCity.id,
          gamePhase: 'deployment' as 'deployment' | 'battle' | 'victory',
          currentPlayer: 'attacker' as 'attacker' | 'defender'
        };
        
        // Ouvrir SimpleBattlefieldV2 via createPortal
        setSimpleBattlefieldData(battleInfo);
        setSimpleBattlefieldOpen(true);
        
        // Masquer les barres du jeu
        document.body.classList.add('battlefield-fullscreen');
        
        // Callback optionnel
        if (onBattleStart) {
          onBattleStart(battleInfo);
        }
      } else {
        alert('❌ Aucune bataille active trouvée pour cette ville.');
      }
    } catch (error) {
      console.error('❌ [V3] Erreur ouverture battlefield:', error);
      alert('❌ Erreur lors de l\'ouverture du battlefield.');
    }
  };

  if (!isOpen) return null;

  // Si SimpleBattlefieldV2 est ouvert, on l'isole complètement
  if (simpleBattlefieldOpen && simpleBattlefieldData) {
    const battlefieldContent = (
      <div 
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          zIndex: 2147483648, // Plus élevé que tout
          background: '#000',
          pointerEvents: 'auto' // S'assurer que les événements de souris fonctionnent
        }}

      >
        <SimpleBattlefieldV2
          battleId={simpleBattlefieldData.battleId}
          gamePhase={simpleBattlefieldData.gamePhase}
          currentPlayer={simpleBattlefieldData.currentPlayer}
          battlefieldTemplateId={simpleBattlefieldData.battlefieldTemplateId}
          attackerUnits={simpleBattlefieldData.attackerUnits}
          defenderUnits={simpleBattlefieldData.defenderUnits}
          targetCityId={simpleBattlefieldData.targetCityId}
          initialRound={simpleBattlefieldData.initialRound}
          initialCurrentPlayer={simpleBattlefieldData.initialCurrentPlayer}
          onClose={() => {
            setSimpleBattlefieldOpen(false);
            document.body.classList.remove('battlefield-fullscreen');
          }}
        />
      </div>
    );
    
    // Rendre via portail pour isoler complètement du popup
    return createPortal(battlefieldContent, document.body);
  }

  const modalContent = (
    <div 
      className="popup-overlay attack-popup"
      onClick={onClose}
      onWheel={(e) => {
        e.preventDefault();
        e.stopPropagation();
      }}
      onTouchMove={(e) => {
        if (e.touches.length > 1) e.preventDefault();
      }}
    >
      <div 
        className="popup-content" 
        onClick={(e) => e.stopPropagation()}
        onWheel={(e) => {
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            e.stopPropagation();
          }
        }}
      >
        
        <div className="popup-header">
          <h2>
            {mode === 'transport' ? (
              transportType === 'attack' ? `⚔️ Transport d'attaque vers ${targetCity.name}` : `🚚 Déplacer unités vers ${targetCity.name}`
            ) : mode === 'protect' ? (
              `🛡️ Protéger ${targetCity.name}`
            ) : (
              `⚔️ Attaquer ${targetCity.name}`
            )}
          </h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="popup-info">
          <span style={{ fontSize: '1.15em' }}><strong>De:</strong> {attackerCity.name}</span>
          <span style={{ fontSize: '1.15em' }}><strong>Vers:</strong> {targetCity.name}</span>
          {mode === 'transport' && (
            <div className="transport-description" style={{marginTop: '5px', fontSize: '12px', color: '#666'}}>
              {transportType === 'attack' ? 
                'Les unités reviendront automatiquement après le combat' : 
                'Les unités seront transférées définitivement'
              }
            </div>
          )}
        </div>

        <div className="section">
          <h3>🛡️ Unités</h3>
          
          <div className="units-list-ikariam">
            {Object.entries(unitStats).map(([unitType, stats]) => {
              const available = availableUnits[unitType] || 0;
              const selected = selectedUnits[unitType] || 0;
              const maxStackSize = stats?.max_stack_size || 10;
              
              if (available === 0) return null;
              
              return (
                <div key={unitType} className="unit-row-ikariam">
                  {/* Colonne: Nombre + Icône */}
                  <div className="unit-icon-column">
                    <div className="unit-count-display">
                      {available}
                    </div>
                    <img 
                      src={`/assets/units/${unitType}.png`}
                      alt={stats.name || unitType}
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = '/assets/units/default.png';
                      }}
                      className="unit-icon-img"
                    />
                  </div>
                  
                  {/* Nom + Stats */}
                  <div className="unit-info-column">
                    <div className="unit-name-compact">
                      {stats.name || unitType}
                    </div>
                    <div className="unit-stats-compact">
                      <span className="stat-hp">❤️{stats.hp || stats.health || 0}</span>
                      <span className="stat-attack">⚔️{stats.attack_melee || stats.attack || 0}</span>
                      <span className="stat-defense">🛡️{stats.defense_melee || stats.defense || 0}</span>
                    </div>
                  </div>
                  
                  {/* Slider */}
                  <div className="unit-slider-container">
                    <input
                      type="range"
                      min="0"
                      max={available}
                      value={selected}
                      onChange={(e) => handleUnitChange(unitType, parseInt(e.target.value))}
                      className="unit-slider-compact"
                    />
                  </div>
                  
                  {/* Boutons groupes complets */}
                  <div className="unit-group-controls">
                    <button 
                      className="group-btn minus"
                      onClick={() => handleUnitGroupRemove(unitType)}
                      disabled={selected === 0}
                      title={`Retirer ${Math.min(maxStackSize, selected)} unités`}
                    >
                      -{Math.min(maxStackSize, selected)}
                    </button>
                    <button 
                      className="group-btn plus"
                      onClick={() => handleUnitGroupAdd(unitType)}
                      disabled={selected >= available}
                      title={`Ajouter ${Math.min(maxStackSize, available - selected)} unités`}
                    >
                      +{Math.min(maxStackSize, available - selected)}
                    </button>
                  </div>
                  
                  {/* Input manuel */}
                  <div className="unit-manual-input">
                    <input
                      type="number"
                      min="0"
                      max={available}
                      value={selected}
                      onChange={(e) => handleUnitManualInput(unitType, e.target.value)}
                      className="manual-input"
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="section">
          <h3>🦸 Héros</h3>
          <div className="heroes-list">
            {Object.entries(availableHeroes).map(([heroId, hero]) => (
              <label key={heroId} className="hero-item">
                <input
                  type="checkbox"
                  checked={selectedHeroes[heroId] || false}
                  onChange={() => handleHeroToggle(heroId)}
                  disabled={!hero.is_available}
                />
                <div className="hero-info">
                  <div className="hero-name">
                    {hero.name || 'Héros'} (Niv. {hero.current_level})
                  </div>
                  {hero.calculated_stats && (
                    <div className="hero-stats">
                      ❤️ {hero.calculated_stats.hp} | 
                      ⚔️ {hero.calculated_stats.attack_melee} | 
                      🛡️ {hero.calculated_stats.defense_melee}
                    </div>
                  )}
                  {hero.calculated_bonuses && (
                    <div className="hero-bonuses">
                      🔥 +{hero.calculated_bonuses.offensive_bonus}% | 
                      🛡️ +{hero.calculated_bonuses.defensive_bonus}% | 
                      💪 +{hero.calculated_bonuses.moral_bonus}% moral
                    </div>
                  )}
                </div>
              </label>
            ))}
            {Object.keys(availableHeroes).length === 0 && (
              <p className="empty-message">Aucun héros disponible</p>
            )}
          </div>
        </div>

        <div className="section">
          <h3>⛵ Bateaux</h3>
          <div className="ships-controls">
            <button onClick={() => setShips(Math.max(1, ships - 1))}>-</button>
            <span>{ships} bateau(x)</span>
            <button onClick={() => setShips(ships + 1)}>+</button>
          </div>
          
          {/* Infos de transport */}
          {(() => {
            const stats = getTransportStats();
            return stats ? (
              <div style={{ marginTop: '10px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                <div style={{ background: 'rgba(255, 255, 255, 0.5)', padding: '6px', borderRadius: '4px', border: '1px solid var(--bg-secondary)', fontSize: '12px', textAlign: 'center' }}>
                  Distance: <strong>{stats.distance.toFixed(1)}u</strong>
                </div>
                <div style={{ background: 'rgba(255, 255, 255, 0.5)', padding: '6px', borderRadius: '4px', border: '1px solid var(--bg-secondary)', fontSize: '12px', textAlign: 'center' }}>
                  Vitesse: <strong>{stats.transportSpeed.toFixed(2)}u/s</strong>
                </div>
                <div style={{ background: 'rgba(255, 255, 255, 0.5)', padding: '6px', borderRadius: '4px', border: '1px solid var(--bg-secondary)', fontSize: '12px', textAlign: 'center' }}>
                  Chargement: <strong>{stats.loadingTime.toFixed(1)}s</strong>
                </div>
                <div style={{ background: 'rgba(255, 255, 255, 0.5)', padding: '6px', borderRadius: '4px', border: '1px solid var(--bg-secondary)', fontSize: '12px', textAlign: 'center' }}>
                  Voyage: <strong>{stats.transportTime.toFixed(1)}s</strong>
                </div>
              </div>
            ) : null;
          })()}
        </div>

        {/* Section statistiques de transport/attaque - Version compacte */}
        {(() => {
          const stats = getTransportStats();
          return stats ? (
            <div className="section compact-stats">
              <h3>⚔️ {mode === 'transport' ? 'Résumé du transport' : 'Résumé de l\'attaque'}</h3>
              {transportError && (
                <div className="error-compact">⚠️ {transportError}</div>
              )}
              
              <div className="stats-grid-compact" style={{ gap: '8px' }}>
                <div className="stat-compact">Total: <strong>{stats.totalEntities}</strong></div>
                <div className="stat-compact">Bateaux: <strong>{stats.shipsNeeded}/{stats.shipsToSend}</strong></div>
                <div className="stat-compact">Temps avant attaque: <strong>{(stats.transportTime + stats.loadingTime).toFixed(1)}s</strong></div>
              </div>
              
              <div className="units-summary-compact">
                🎯 {stats.totalUnits} unité{stats.totalUnits > 1 ? 's' : ''} + {stats.totalHeroes} héros
              </div>
            </div>
          ) : null;
        })()}

        <div className="actions">
          {mode === 'attack' && (
            <>
              <button 
                className="btn btn-attack" 
                onClick={handleAttack}
                disabled={!canLaunchAttack()}
              >
                {loading ? '⏳ Attaque...' : '⚔️ Attaquer'}
              </button>
              <button 
                className="btn btn-preview" 
                onClick={handleOpenBattlefield}
                disabled={false}
              >
                🏛️ Aperçu
              </button>
            </>
          )}
          <button className="btn btn-cancel" onClick={onClose}>
            ❌ Annuler
          </button>
          {mode === 'transport' && (
            <button 
              className="btn btn-attack" 
              onClick={handleTransport}
              disabled={!canLaunchAttack()}
            >
              {loading ? '⏳ Transport...' : (
                transportType === 'attack' ? '⚔️ Lancer transport d\'attaque' : '🚚 Déplacer les unités'
              )}
            </button>
          )}
          {mode === 'protect' && (
            <button 
              className="btn btn-protect" 
              onClick={handleProtect}
              disabled={!canLaunchAttack()}
            >
              {loading ? '⏳ Protection...' : '🛡️ Protéger la ville'}
            </button>
          )}
        </div>

      </div>
    </div>
  );

  // Rendre le popup dans un portail pour contourner le z-index du header
  return createPortal(modalContent, document.body);
};

export default AttackPopupV3;