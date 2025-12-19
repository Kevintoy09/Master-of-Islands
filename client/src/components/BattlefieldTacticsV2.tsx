import React, { useState, useEffect, useCallback } from 'react';
import { CompactUnit } from '../types/index';
import UnitInfoPopup from './UnitInfoPopup';
import { extractUnitType } from '../utils/combatUtils';
import { getApiUrl } from '../utils/api';
import { useTurnLock } from '../context/TurnLockContext';
import { useUser } from '../hooks/useUser';

type GridPosition = [number, number];

interface UnitData {
  id: string;
  position: GridPosition;
  team: 'attacker' | 'defender';
}

interface BattlefieldTacticsV2Props {
  battlefield: any;
  units: UnitData[];
  selectedUnitId: string | null;
  onUnitMove: (unitId: string, newPosition: GridPosition) => void;
  onClearSelection: () => void;
  hexToPixel?: (q: number, r: number) => { x: number; y: number };
  battlefieldBounds?: { minX: number; maxX: number; minY: number; maxY: number; width: number; height: number };
  getHeroAuraForUnit?: (unit: any, position: { q: number; r: number }) => { inAura: boolean; bonuses: any; hero: any };
  // Props pour le combat
  currentTurnPlayer?: string;
  battleParticipants?: any;
  actualBattleId?: string;
  currentRound?: number;
  loadBattleUnits?: () => Promise<void>;
  setSelectedUnit?: (unit: any) => void;
  attackRequestData?: {attacker: any, defender: any} | null;
  onAttackComplete?: () => void;
  // Props pour déplacer le combat popup hors du zoom
  setCombatPopupOpen?: (open: boolean) => void;
  setCombatData?: (data: any) => void;
  onAttackRequest?: (attacker: CompactUnit, defender: CompactUnit) => Promise<void>;
}

interface UnitStats {
  movement: number;
  [key: string]: any;
}

interface AgeStats {
  [unitType: string]: UnitStats;
}

interface AllUnitStats {
  [age: string]: AgeStats;
}

// Coûts de mouvement maintenant récupérés dynamiquement depuis battlefield.terrainDefinitions

export const BattlefieldTacticsV2: React.FC<BattlefieldTacticsV2Props> = ({
  battlefield,
  units,
  selectedUnitId,
  onUnitMove,
  onClearSelection,
  hexToPixel: hexToPixelProp,
  battlefieldBounds,
  getHeroAuraForUnit, // Fonction pour récupérer les auras des héros
  currentTurnPlayer,
  battleParticipants,
  actualBattleId,
  currentRound,
  loadBattleUnits,
  setSelectedUnit,
  attackRequestData,
  onAttackComplete,
  // 🎯 Props pour déplacer le combat popup
  setCombatPopupOpen: setCombatPopupOpenProp,
  setCombatData: setCombatDataProp,
  onAttackRequest
}) => {
  // � Hook utilisateur (pour vérifier le player connecté)
  const { user } = useUser();
  
  // �🔒 Hook de verrouillage des tours
  const { canControlUnit } = useTurnLock();
  
  // États pour le mouvement
  const [unitStats, setUnitStats] = useState<AllUnitStats>({});
  const [accessibleHexes, setAccessibleHexes] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);

  // 🎯 États pour le combat maintenant gérés par SimpleBattlefieldV2 (évite le zoom)
  // Utiliser les props si disponibles, sinon fallback local
  const [localCombatPopupOpen, setLocalCombatPopupOpen] = useState(false);
  const [localCombatData, setLocalCombatData] = useState<{
    attacker: CompactUnit | null;
    defender: CompactUnit | null;
    attackerStats: any | null;
    defenderStats: any | null;
  }>({
    attacker: null,
    defender: null,
    attackerStats: null,
    defenderStats: null
  });
  
  // Utiliser les props externes si disponibles
  const setCombatPopupOpen = setCombatPopupOpenProp || setLocalCombatPopupOpen;
  const setCombatData = setCombatDataProp || setLocalCombatData;
  const combatPopupOpen = setCombatPopupOpenProp ? false : localCombatPopupOpen; // Toujours false si géré par parent
  const combatData = setCombatDataProp ? localCombatData : localCombatData; // Utiliser local data même si props existent
  const [unitStatsCombat, setUnitStatsCombat] = useState<any>(null);
  const [heroesData, setHeroesData] = useState<any>(null);
  const [battleLocation, setBattleLocation] = useState<string>('');

  // États pour le popup d'informations d'unité
  const [unitInfoPopupOpen, setUnitInfoPopupOpen] = useState(false);
  const [selectedUnitForInfo, setSelectedUnitForInfo] = useState<any>(null);

  useEffect(() => {
    const loadUnitStats = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/v2/unit_stats`);
        const stats = await response.json();
        setUnitStats(stats);
        setUnitStatsCombat(stats); // Utiliser les mêmes stats pour le combat
        setIsLoading(false);
      } catch (error) {
        setIsLoading(false);
      }
    };

    loadUnitStats();
  }, []);

  // Charger les données de héros
  useEffect(() => {
    const loadHeroesData = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/v2/player_heroes`);
        const data = await response.json();
        setHeroesData(data);
      } catch (error) {
        setHeroesData(null);
      }
    };
    
    loadHeroesData();
  }, []);

  // Charger la location de la bataille depuis l'API
  useEffect(() => {
    const loadBattleLocation = async () => {
      if (!actualBattleId) {
        setBattleLocation('');
        return;
      }

      try {
        const response = await fetch(`${getApiUrl()}/api/v2/battles/data`);
        const battlesData = await response.json();
        
        if (battlesData[actualBattleId] && battlesData[actualBattleId].location) {
          setBattleLocation(battlesData[actualBattleId].location);
        } else {
          setBattleLocation('');
        }
      } catch (error) {
        setBattleLocation('');
      }
    };

    loadBattleLocation();
  }, [actualBattleId]);

  // Fonction extractUnitType supprimée - on utilise celle de combatUtils qui gère correctement les nouveaux formats

  const getUnitMovement = useCallback((unitId: string): number => {
    const unitType = extractUnitType(unitId);
    const defaultMovement = 3;
    let baseMovement = defaultMovement;

    // Trouver l'unité dans la liste des unités du battlefield
    const unit = units.find(u => u.id === unitId);
    
    // Si c'est un héros avec heroData.calculated_stats, utiliser ces stats
    if (unit && (unit as any).heroData?.calculated_stats?.movement) {
      baseMovement = (unit as any).heroData.calculated_stats.movement;
    } else {
      // Sinon, récupérer le mouvement de base depuis les stats d'unités normales
      if (unitStats.classical_age && unitStats.classical_age[unitType]) {
        baseMovement = unitStats.classical_age[unitType].movement || defaultMovement;
      } else {
        for (const age of Object.keys(unitStats)) {
          if (unitStats[age][unitType]) {
            baseMovement = unitStats[age][unitType].movement || defaultMovement;
            break;
          }
        }
      }
    }

    // Appliquer les bonus de héros si disponible
    if (getHeroAuraForUnit) {
      const unit = units.find(u => u.id === unitId);
      if (unit) {
        const position = { q: unit.position[0], r: unit.position[1] };
        
        // Créer un objet unité compatible avec getHeroAuraForUnit
        const unitForAura = { unitId: unit.id, ...unit };
        const auraResult = getHeroAuraForUnit(unitForAura, position);
        
        if (auraResult.inAura && auraResult.bonuses?.movement_bonus) {
          const heroMovementBonus = auraResult.bonuses.movement_bonus;
          return baseMovement + heroMovementBonus;
        }
      }
    }
    return baseMovement;
  }, [units, unitStats, getHeroAuraForUnit]);

  // Fonction pour récupérer les stats d'un héros
  const getHeroStats = useCallback((heroUnitId: string) => {
    if (!heroesData) return null;
    
    let instanceId = '';
    
    // Extraction de l'instanceId selon le format
    let heroKey = '';
    
    // Nouveau format: attacker_player_1_hero_player_1_hero_1
    if (heroUnitId.includes('_hero_') && (heroUnitId.startsWith('attacker_') || heroUnitId.startsWith('defender_'))) {
      const parts = heroUnitId.split('_');
      const heroIndex = parts.indexOf('hero');
      
      if (heroIndex !== -1 && heroIndex < parts.length - 2) {
        const heroPlayerPart = parts[heroIndex + 1]; // player_1
        const heroNumberPart = parts[heroIndex + 2]; // hero_1
        
        if (heroPlayerPart && heroNumberPart) {
          heroKey = `hero_${heroPlayerPart}_${heroNumberPart}`;
          instanceId = `${heroPlayerPart}_${heroNumberPart}`;
        }
      }
    } else if (heroUnitId.includes('_hero_hero_')) {
      const parts = heroUnitId.split('_hero_hero_');
      if (parts.length === 2) {
        instanceId = parts[1];
        heroKey = `hero_${instanceId}`;
      }
    } else if (heroUnitId.startsWith('hero_attacker_') || heroUnitId.startsWith('hero_defender_')) {
      const parts = heroUnitId.split('_');
      if (parts.length >= 4) {
        instanceId = parts.slice(2).join('_');
        heroKey = `hero_${instanceId}`;
      }
    } else if (heroUnitId.startsWith('hero_hero_')) {
      // Cas spécial : l'ID commence déjà par hero_hero_ (double préfixe)
      heroKey = heroUnitId.substring(5); // Enlever le premier "hero_" 
      instanceId = heroKey.substring(5); // Enlever le deuxième "hero_"
    } else if (heroUnitId.startsWith('hero_')) {
      // L'ID est déjà correctement formaté
      heroKey = heroUnitId;
      instanceId = heroUnitId.substring(5);
    }
    
    if (!heroKey) return null;
    
    // Chercher dans player_heroes.json
    for (const playerId in heroesData) {
      const playerData = heroesData[playerId];
      if (playerData.heroes && playerData.heroes[heroKey]) {
        const hero = playerData.heroes[heroKey];
        return {
          type: 'hero',
          name: `${hero.hero_id} (Héros)`,
          count: 1,
          hp: hero.calculated_stats.hp,
          attack_melee: hero.calculated_stats.attack_melee,
          defense_melee: hero.calculated_stats.defense_melee,
          attack_ranged: 0,
          defense_ranged: hero.calculated_stats.defense_ranged,
          category: 'hero',
          special_abilities: [`Aura de moral (+${hero.calculated_bonuses.moral_bonus})`]
        };
      }
    }
    
    return null;
  }, [heroesData]);

  // Fonctions de combat
  const handleAttackRequest = useCallback(async (attacker: CompactUnit, defender: CompactUnit) => {
    if (!unitStatsCombat) {
      return;
    }

    // Vérifier que l'unité attaquante appartient au joueur actuel
    if (currentTurnPlayer && battleParticipants) {
      // Protection RENFORCÉE contre unitId undefined
      let safeUnitId = '';
      if (!attacker.unitId) {
        console.error('❌ attacker.unitId est undefined:', attacker);
        // Essayer de récupérer l'ID depuis d'autres propriétés
        safeUnitId = (attacker as any).id || 'unknown_unit';
        (attacker as any).unitId = safeUnitId;
      } else {
        safeUnitId = attacker.unitId;
      }
      
      // Protection supplémentaire - s'assurer que safeUnitId est une string
      if (typeof safeUnitId !== 'string') {
        console.error('❌ safeUnitId n\'est pas une string:', safeUnitId);
        safeUnitId = String(safeUnitId) || 'fallback_unit';
      }
      
      // Déterminer si c'est un attaquant ou défenseur
      const attackerRole = safeUnitId.startsWith('attacker_') || safeUnitId.includes('_attacker_') ? 'attacker' : 'defender';
      
      const unitOwner = attackerRole === 'attacker' ? battleParticipants?.attacker_id : battleParticipants?.defender_id;
      const canAttack = currentTurnPlayer === unitOwner;
      
      if (!canAttack) {
        alert(`⚠️ C'est le tour de ${currentTurnPlayer}. Cette unité appartient à ${unitOwner} !`);
        return;
      }
    }

    try {
      // Convertir les CompactUnit en format attendu par CombatPopup
      const attackerType = extractUnitType(attacker.unitId);
      const defenderType = extractUnitType(defender.unitId);

      // Chercher les stats dans toutes les ères
      let attackerStats = null;
      let defenderStats = null;
      
      // Traitement spécial pour les héros
      if (attackerType === 'hero') {
        attackerStats = getHeroStats(attacker.unitId);
      }
      
      if (defenderType === 'hero') {
        defenderStats = getHeroStats(defender.unitId);
      }
      
      // Pour les unités normales, chercher dans unit_stats.json
      for (const era of Object.keys(unitStatsCombat)) {
        if (!attackerStats && unitStatsCombat[era][attackerType]) {
          attackerStats = {
            type: attackerType,
            name: unitStatsCombat[era][attackerType].name,
            count: attacker.unitCount || 1,
            hp: attacker.hp || unitStatsCombat[era][attackerType].hp,
            attack_melee: unitStatsCombat[era][attackerType].attack_melee,
            defense_melee: unitStatsCombat[era][attackerType].defense_melee,
            attack_ranged: unitStatsCombat[era][attackerType].attack_ranged,
            defense_ranged: unitStatsCombat[era][attackerType].defense_ranged,
            category: unitStatsCombat[era][attackerType].category,
            special_abilities: unitStatsCombat[era][attackerType].special_abilities || []
          };
        }
        if (!defenderStats && unitStatsCombat[era][defenderType]) {
          defenderStats = {
            type: defenderType,
            name: unitStatsCombat[era][defenderType].name,
            count: defender.unitCount || 1,
            hp: defender.hp || unitStatsCombat[era][defenderType].hp,
            attack_melee: unitStatsCombat[era][defenderType].attack_melee,
            defense_melee: unitStatsCombat[era][defenderType].defense_melee,
            attack_ranged: unitStatsCombat[era][defenderType].attack_ranged,
            defense_ranged: unitStatsCombat[era][defenderType].defense_ranged,
            category: unitStatsCombat[era][defenderType].category,
            special_abilities: unitStatsCombat[era][defenderType].special_abilities || []
          };
        }
      }
      
      if (!attackerStats || !defenderStats) {
        // Créer des stats de fallback pour les héros si getHeroStats a échoué
        if (!attackerStats && attackerType === 'hero') {
          // Création stats fallback pour attaquant héros
          attackerStats = {
            type: 'hero',
            name: 'Héros',
            count: 1,
            hp: 1000,
            attack_melee: 25,
            defense_melee: 20,
            attack_ranged: 0,
            defense_ranged: 15,
            category: 'hero',
            special_abilities: ['Héros puissant']
          };
        }
        
        if (!defenderStats && defenderType === 'hero') {
          defenderStats = {
            type: 'hero',
            name: 'Héros',
            count: 1,
            hp: 1000,
            attack_melee: 25,
            defense_melee: 20,
            attack_ranged: 0,
            defense_ranged: 15,
            category: 'hero',
            special_abilities: ['Héros puissant']
          };
        }
        
        // Si on n'a toujours pas les stats après les fallbacks, alors return
        if (!attackerStats || !defenderStats) {
          return;
        }
      }

      // Ouvrir le popup de combat
      setCombatData({
        attacker,
        defender,
        attackerStats,
        defenderStats
      });
      setCombatPopupOpen(true);
      
    } catch (error) {
      console.error('❌ [handleAttackRequest] Erreur:', error);
    }
  }, [unitStatsCombat, currentTurnPlayer, battleParticipants, getHeroStats, setCombatData, setCombatPopupOpen]);

  // Traiter les demandes d'attaque depuis BattlefieldVisualsV2
  useEffect(() => {
    if (attackRequestData) {
      // Protection contre les objets mal formés
      if (!attackRequestData.attacker || !attackRequestData.defender) {
        console.error('❌ attackRequestData mal formé:', attackRequestData);
        onAttackComplete?.();
        return;
      }

      // S'assurer que les unitId sont présents
      if (!attackRequestData.attacker.unitId) {
        console.log('🔧 Correction attackRequestData.attacker.unitId');
        attackRequestData.attacker.unitId = (attackRequestData.attacker as any).id || 'unknown_attacker';
      }
      if (!attackRequestData.defender.unitId) {
        console.log('🔧 Correction attackRequestData.defender.unitId');
        attackRequestData.defender.unitId = (attackRequestData.defender as any).id || 'unknown_defender';
      }

      handleAttackRequest(attackRequestData.attacker, attackRequestData.defender);
      onAttackComplete?.(); // Nettoyer les données d'attaque
    }
  }, [attackRequestData, handleAttackRequest, onAttackComplete]);

  // Fonction pour appliquer les résultats du combat
  const handleConfirmCombat = async (result: any) => {
    if (!combatData.attacker || !combatData.defender || !actualBattleId) {
      return;
    }

    try {
      // Calculer le nombre d'unités tuées
      const previousCount = combatData.defender?.unitCount || result.survivingUnits + (result.survivingUnits > 0 ? 2 : result.survivingUnits); // Estimation
      const kills = previousCount - result.survivingUnits;
      
      // Préparer les données pour l'API de bataille
      const combatAction = {
        battlefield_id: actualBattleId,
        unit_id: combatData.attacker.unitId,
        round: currentRound,
        action: {
          type: 'attack',
          target: combatData.defender.unitId,
          damage_dealt: result.damage,
          attacker_position: combatData.attacker.position,
          defender_position: combatData.defender.position,
          previous_count: combatData.defender?.unitCount || 10 // Nombre d'unités avant l'attaque
        },
        target_new_state: {
          position: combatData.defender.position,
          hp: result.isDefenderHero ? result.remainingHP : undefined,
          count: result.isDefenderHero ? undefined : result.survivingUnits,
          status: result.survivingUnits > 0 ? 'active' : 'eliminated'
        }
      };

      // Envoyer à l'API de bataille V2 (nouvelle route)
      const response = await fetch(`${getApiUrl()}/api/v2/battle/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(combatAction)
      });

      if (response.ok) {
        // Recharger les données depuis le serveur (comme lors du déplacement d'unité)
        if (loadBattleUnits) {
          await loadBattleUnits();
        }
        
        // Forcer un re-render des statistiques et de l'affichage
        if (setSelectedUnit) {
          setSelectedUnit(null);
        }

        // Nettoyer les données d'attaque dans le composant parent
        if (onAttackComplete) {
          onAttackComplete();
        }
      }

    } catch (error) {
      // Erreur silencieuse
    } finally {
      // Fermer le popup
      setCombatPopupOpen(false);
      setCombatData({ attacker: null, defender: null, attackerStats: null, defenderStats: null });
    }
  };

  const getTerrainAt = (q: number, r: number): string => {
    // Trouver la cellule correspondante dans le battlefield
    const hexCell = battlefield?.hexCells?.find((cell: any) => cell.q === q && cell.r === r);
    return hexCell?.terrain || 'plains';
  };

  const getMovementCost = useCallback((q: number, r: number): number => {
    // Chercher directement dans les terrainDefinitions du battlefield
    const hexCell = battlefield?.hexCells?.find((cell: any) => cell.q === q && cell.r === r);
    if (hexCell && hexCell.movementBonus !== undefined) {
      // movementBonus est un modificateur : -2 = coût +2, 0 = coût normal (1.0)
      return Math.max(0.1, 1.0 - hexCell.movementBonus); // Minimum 0.1 pour éviter division par 0
    }
    return 1.0; // Coût par défaut si terrain non trouvé
  }, [battlefield]);

  const isHexOccupied = useCallback((q: number, r: number, excludeUnitId?: string): boolean => {
    return units.some(unit => 
      unit.id !== excludeUnitId && 
      unit.position[0] === q && 
      unit.position[1] === r
    );
  }, [units]);

  const calculateAccessibleHexes = useCallback((startQ: number, startR: number, maxMovement: number, currentSelectedUnitId?: string): Set<string> => {
    const accessible = new Set<string>();
    const visited = new Set<string>();
    const queue: Array<{q: number, r: number, cost: number}> = [{q: startQ, r: startR, cost: 0}];

    // Récupérer les cases valides de la carte depuis battlefield.hexCells
    const validHexes = new Set<string>();
    if (battlefield?.hexCells) {
      battlefield.hexCells.forEach((cell: any) => {
        validHexes.add(`${cell.q},${cell.r}`);
      });
    }

    // Fonction pour vérifier si une case est dans la carte
    const isValidHex = (q: number, r: number): boolean => {
      return validHexes.has(`${q},${r}`);
    };

    while (queue.length > 0) {
      queue.sort((a, b) => a.cost - b.cost);
      const current = queue.shift()!;
      const key = `${current.q},${current.r}`;

      if (visited.has(key)) continue;
      visited.add(key);

      // Ne considérer comme accessible que si c'est dans la carte ET dans la limite de mouvement
      if (current.cost <= maxMovement && isValidHex(current.q, current.r)) {
        accessible.add(key);
      }

      const neighbors = [
        {q: current.q + 1, r: current.r},
        {q: current.q - 1, r: current.r},
        {q: current.q, r: current.r + 1},
        {q: current.q, r: current.r - 1},
        {q: current.q + 1, r: current.r - 1},
        {q: current.q - 1, r: current.r + 1}
      ];

      for (const neighbor of neighbors) {
        // Ne traiter que les cases valides de la carte
        if (!isValidHex(neighbor.q, neighbor.r)) continue;
        
        const neighborKey = `${neighbor.q},${neighbor.r}`;
        if (visited.has(neighborKey)) continue;

        const movementCost = getMovementCost(neighbor.q, neighbor.r);
        const newCost = current.cost + movementCost;

        if (newCost > maxMovement) continue;
        if (isHexOccupied(neighbor.q, neighbor.r, currentSelectedUnitId)) continue;

        queue.push({q: neighbor.q, r: neighbor.r, cost: newCost});
      }
    }

    return accessible;
  }, [battlefield, units, getMovementCost, isHexOccupied]);

  useEffect(() => {
    if (!selectedUnitId || isLoading) {
      setAccessibleHexes(new Set());
      return;
    }

    const selectedUnit = units.find(unit => unit.id === selectedUnitId);
    if (!selectedUnit) {
      setAccessibleHexes(new Set());
      return;
    }

    // 🔒 VÉRIFICATION DU VERROUILLAGE
    // Extraire le propriétaire de l'unité (player_X ou wild_camp)
    let unitOwner = '';
    if (selectedUnitId.includes('wild_camp')) {
      unitOwner = 'wild_camp';
    } else {
      const parts = selectedUnitId.split('_');
      if (parts.length >= 3 && parts[1] === 'player') {
        unitOwner = `${parts[1]}_${parts[2]}`;
      }
    }
    
    const connectedPlayerId = user?.id || '';
    
    // Vérifier avec le joueur CONNECTÉ, pas currentTurnPlayer
    if (!canControlUnit(unitOwner, connectedPlayerId)) {
      // Unité verrouillée - pas de mouvements possibles
      setAccessibleHexes(new Set());
      return;
    }

    const movement = getUnitMovement(selectedUnitId);
    const [q, r] = selectedUnit.position;
    
    const accessible = calculateAccessibleHexes(q, r, movement, selectedUnitId);
    setAccessibleHexes(accessible);
  }, [selectedUnitId, units, unitStats, isLoading, battlefield, getUnitMovement, calculateAccessibleHexes, canControlUnit, currentTurnPlayer]);

  const handleHexClick = (q: number, r: number) => {
    if (!selectedUnitId) return;

    const hexKey = `${q},${r}`;
    if (!accessibleHexes.has(hexKey)) {
      onClearSelection();
      return;
    }

    // 🎯 Vérifier que l'unité existe encore avant de la déplacer
    const unitExists = units.find(u => u.id === selectedUnitId);
    if (unitExists) {
      onUnitMove(selectedUnitId, [q, r]);
    } else {
      // Unité désélectionnée, annulation du déplacement
    }
    onClearSelection();
  };

  const isHexAccessible = (q: number, r: number): boolean => {
    const hexKey = `${q},${r}`;
    return accessibleHexes.has(hexKey);
  };

  // Convertir coordonnées hex vers pixels (utiliser la fonction du parent ou fallback)
  const hexToPixel = hexToPixelProp || ((q: number, r: number) => {
    const size = 25; // Taille réduite pour que tout rentre
    const x = size * (3/2 * q);
    const y = size * (Math.sqrt(3)/2 * q + Math.sqrt(3) * r);
    return { x: x + 1200, y: y + 400 }; // Centrage dans viewBox 2400x1600 (fallback)
  });

  // Obtenir les points d'un hexagone
  const getHexagonPoints = (x: number, y: number) => {
    const size = 25; // Même taille que dans hexToPixel
    const points = [];
    for (let i = 0; i < 6; i++) {
      const angle = (Math.PI / 3) * i;
      const px = x + size * Math.cos(angle);
      const py = y + size * Math.sin(angle);
      points.push(`${px},${py}`);
    }
    return points.join(' ');
  };

  // Générer la grille d'hexagones accessibles
  const renderAccessibleHexes = (): React.ReactElement[] => {
    if (!selectedUnitId || accessibleHexes.size === 0) return [];

    const hexElements: React.ReactElement[] = [];
    Array.from(accessibleHexes).forEach(hexKey => {
      const [q, r] = hexKey.split(',').map(Number);
      const { x, y } = hexToPixel(q, r);
      const points = getHexagonPoints(x, y);

      hexElements.push(
        <polygon
          key={hexKey}
          points={points}
          fill="rgba(0, 255, 0, 0.3)"
          stroke="rgba(0, 255, 0, 0.6)"
          strokeWidth="2"
          style={{ cursor: 'pointer', pointerEvents: 'auto' }}
          onClick={() => {
            // Gérer le déplacement vers cette case
            if (selectedUnitId && onUnitMove) {
              // 🎯 Vérifier que l'unité existe encore avant de la déplacer
              const unitExists = units.find(u => u.id === selectedUnitId);
              if (unitExists) {
                // 🔧 SOLUTION CHIRURGICALE: Vérifier si l'unité est déjà sur cette position
                const currentPosition = unitExists.position;
                const newPosition = [q, r];
                
                if (currentPosition[0] === newPosition[0] && currentPosition[1] === newPosition[1]) {
                  onClearSelection(); // Désélectionner au lieu de déplacer
                  return;
                }
                
                onUnitMove(selectedUnitId, [q, r]);
              } else {
                // Unité désélectionnée, annulation du déplacement
              }
            }
          }}
        />
      );
    });
    return hexElements;
  };

  return (
    <div className="battlefield-tactics-overlay">
      {/* Overlay SVG pour afficher les cases accessibles */}
      <svg 
        width="1200" 
        height="800" 
        viewBox={battlefieldBounds ? 
          `${battlefieldBounds.minX} ${battlefieldBounds.minY} ${battlefieldBounds.width} ${battlefieldBounds.height}` : 
          "0 0 2400 1600"
        }
        style={{ 
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none', // Ne pas bloquer les clics par défaut
          zIndex: 5 // Entre BattlefieldVisualsV2 (zIndex: 2) et la grille de base
        }}
      >
        {renderAccessibleHexes()}
      </svg>

      {/* 🎯 Combat Popup maintenant géré dans SimpleBattlefieldV2 pour éviter le zoom */}
      
      {unitInfoPopupOpen && selectedUnitForInfo && (
        <UnitInfoPopup
          isOpen={unitInfoPopupOpen}
          unit={selectedUnitForInfo}
          terrainEffects={{
            attack_bonus: 0,
            defense_bonus: 0,
            movement_cost: 1,
            terrain_name: "Terrain neutre"
          }}
          unitBaseStats={(() => {
            // Extraire le type d'unité pour chercher les stats de base
            const unitIdStr = (selectedUnitForInfo as any).unitId || (selectedUnitForInfo as any).id || '';
            const unitType = extractUnitType(unitIdStr);
            console.log('🔍 [BattlefieldTacticsV2] unitIdStr:', unitIdStr, 'unitType:', unitType);
            
            // Chercher dans les différents âges
            if (unitStats && unitType) {
              if (unitStats.classical_age && unitStats.classical_age[unitType]) {
                console.log('✅ Stats trouvées dans classical_age');
                return unitStats.classical_age[unitType];
              }
              if (unitStats.napoleonic_age && unitStats.napoleonic_age[unitType]) {
                console.log('✅ Stats trouvées dans napoleonic_age');
                return unitStats.napoleonic_age[unitType];
              }
              if (unitStats.enemy_units && unitStats.enemy_units[unitType]) {
                console.log('✅ Stats trouvées dans enemy_units');
                return unitStats.enemy_units[unitType];
              }
            }
            console.warn('❌ [BattlefieldTacticsV2] Stats non trouvées pour:', unitType, 'unitStats keys:', unitStats ? Object.keys(unitStats) : 'null');
            return null;
          })()}
          onClose={() => setUnitInfoPopupOpen(false)}
        />
      )}
    </div>
  );
};

export default BattlefieldTacticsV2;
