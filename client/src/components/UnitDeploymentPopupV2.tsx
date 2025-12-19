/**
 * UnitDeploymentPopupV2.tsx
 * 
 * DESCRIPTION : Version V2 simplifiée et optimisée du popup de déploiement des troupes
 * - Conservation de toutes les fonctionnalités essentielles de l'original
 * - Code simplifié et plus lisible
 * - Interface moderne et responsive
 * - Gestion automatique de l'orientation des troupes
 * - Déploiement par drag & drop ou clic simple
 * 
 * CRÉÉ : Version parallèle sans utiliser le code précédent
 * STYLES : Centralisés dans UnitDeploymentPopupV2.css
 */
import React, { useState, useEffect, useRef } from 'react';
import { HexCell, UnitGroup } from '../types/index';
import usePreventZoom, { handleOverlayWheel, handleContentWheel } from '../hooks/usePreventZoom';
import './UnitDeploymentPopupV2.css';
import { SimpleDeploymentService } from '../services/SimpleDeploymentService';

// =============================================================================
// UTILITAIRES POUR L'AFFICHAGE DES UNITÉS
// =============================================================================

// Configuration des icônes d'unités
const getCategoryIcon = (category: string) => {
  switch (category) {
    case 'infantry': return '⚔️';
    case 'ranged': return '🏹';
    case 'cavalry': return '🐎';
    case 'siege': return '🏛️';
    case 'hero': return '👑';
    default: return '⚔️';
  }
};

const getUnitConfig = (unitType: string, unitStats: any) => {
  const unitStat = unitStats[unitType];
  
  if (!unitStat) {
    return { name: unitType, icon: '⚔️', maxStack: 10 };
  }

  let icon = getCategoryIcon(unitStat.category);
  if (unitType === 'slinger') {
    icon = '🪃';
  }
  
  const maxStack = unitStat.max_stack_size || 10;
  
  return {
    name: unitStat.name,
    icon: icon,
    maxStack: maxStack
  };
};

// Formater l'affichage des unités avec groupement par max_stack_size
const formatUnitDisplay = (unitType: string, totalCount: number, unitStats: any) => {
  if (totalCount <= 0) {
    return null;
  }
  
  const config = getUnitConfig(unitType, unitStats);
  const unitStat = unitStats[unitType];
  
  if (!unitStat) {
    return null;
  }

  // Créer les groupes d'unités
  const groups = [];
  let remainingUnits = totalCount;

  while (remainingUnits > 0) {
    const groupSize = Math.min(remainingUnits, config.maxStack);
    groups.push({
      icon: config.icon,
      count: groupSize,
      category: unitStat.category
    });
    remainingUnits -= groupSize;
  }

  const result = {
    name: config.name,
    totalCount,
    groups,
    category: unitStat.category
  };
  

  return result;
};

// Calculer le temps restant avant l'arrivée des renforts
const calculateTimeToArrival = (arrivalTime: number) => {
  const currentTime = Math.floor(Date.now() / 1000); // Timestamp actuel en secondes
  const timeLeft = arrivalTime - currentTime;
  
  if (timeLeft <= 0) {
    return "Arrivé !";
  }
  
  const hours = Math.floor(timeLeft / 3600);
  const minutes = Math.floor((timeLeft % 3600) / 60);
  const seconds = timeLeft % 60;
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds}s`;
  } else {
    return `${seconds}s`;
  }
};

// Helper pour créer des UnitGroup avec toutes les propriétés requises
const createUnitGroup = (data: {
  id: string;
  type: string; 
  name: string;
  count: number;
  maxStack: number;
  team: 'attacker' | 'defender';
  icon: string;
  status: 'arrived' | 'en_route';
}): UnitGroup => ({
  ...data,
  detailedType: data.type,
  health: 100,
  maxHealth: 100,
  attack: 10,
  defense: 8,
  movement: 3,
  morale: 100,
  hasMovedThisTurn: false
});

interface UnitDeploymentPopupV2Props {
  isOpen: boolean;
  onClose: () => void;
  selectedHex: { q: number, r: number } | null;
  team: 'attacker' | 'defender';
  onDeployUnit: (unitGroup: UnitGroup, hexPosition: { q: number, r: number }) => void;
  targetCityId?: string;
  battlefieldTemplateId?: string;
  battleId?: string;
  deployedUnitsFromBattlefield?: { [unitType: string]: number };
  onDeploymentComplete?: () => void; // ✅ Nouvelle prop pour rafraîchir après déploiement complet
}

const UnitDeploymentPopupV2: React.FC<UnitDeploymentPopupV2Props> = ({
  isOpen,
  onClose,
  selectedHex,
  team,
  onDeployUnit,
  targetCityId,
  battlefieldTemplateId,
  battleId,
  deployedUnitsFromBattlefield = {},
  onDeploymentComplete
}) => {
  // ========== FONCTION UTILITAIRE POUR CONSOLIDER LES UNITÉS ==========
  const consolidateUnitsFromContributions = (playerData: any): { [unitType: string]: number } => {
    if (!playerData) {
      return {};
    }
    
    // Si c'est l'ancienne structure (compatibilité)
    if (playerData.units && !playerData.contributions) {
      return playerData.units;
    }
    
    // Nouvelle structure avec contributions
    if (playerData.contributions && Array.isArray(playerData.contributions)) {
      const consolidatedUnits: { [unitType: string]: number } = {};
      
      playerData.contributions.forEach((contribution: any) => {
        if (contribution.units) {
          Object.entries(contribution.units).forEach(([unitType, count]) => {
            const oldValue = consolidatedUnits[unitType] || 0;
            consolidatedUnits[unitType] = oldValue + (count as number);
          });
        }
      });
      
      return consolidatedUnits;
    }
    
    return {};
  };

  // ========== FONCTIONS DE GESTION DE SÉLECTION ==========
  const toggleHeroSelection = (playerId: string, heroId: string) => {
    setSelectedHeroes(prev => {
      const playerHeroes = prev[playerId] || [];
      const isSelected = playerHeroes.includes(heroId);
      
      return {
        ...prev,
        [playerId]: isSelected 
          ? playerHeroes.filter(id => id !== heroId)
          : [...playerHeroes, heroId]
      };
    });
  };

  // ========== FONCTION UTILITAIRE POUR CONSOLIDER LES HÉROS ==========
  const consolidateHeroesFromContributions = (playerData: any): any[] => {
    if (!playerData) return [];
    
    // Si c'est l'ancienne structure (compatibilité)
    if (playerData.heroes && !playerData.contributions) {
      return playerData.heroes || [];
    }
    
    // Nouvelle structure avec contributions
    if (playerData.contributions && Array.isArray(playerData.contributions)) {
      const allHeroes: any[] = [];
      
      playerData.contributions.forEach((contribution: any) => {
        if (contribution.heroes && Array.isArray(contribution.heroes)) {
          allHeroes.push(...contribution.heroes);
        }
      });
      
      return allHeroes;
    }
    
    return [];
  };

  const [loading, setLoading] = useState(false);
  const [unitStats, setUnitStats] = useState<any>({});
  const [deployedHeroes, setDeployedHeroes] = useState<{[heroInstanceId: string]: boolean}>({});

  // États pour le système V2
  const [formattedUnits, setFormattedUnits] = useState<{[unitType: string]: any}>({});
  const [availableHeroes, setAvailableHeroes] = useState<any[]>([]);
  const [troopsOnTheWay, setTroopsOnTheWay] = useState<{[unitType: string]: number}>({});
  const [reinforcementDetails, setReinforcementDetails] = useState<any[]>([]);
  const [playerGroups, setPlayerGroups] = useState<{ [playerId: string]: { units: any, heroes: any[], playerId: string } }>({});
  
  // États pour la sélection des unités (maintenant par groupes)
  const [selectedUnits, setSelectedUnits] = useState<{ [playerId: string]: { [groupId: string]: boolean } }>({});
  const [selectedHeroes, setSelectedHeroes] = useState<{ [playerId: string]: string[] }>({});

  // État pour l'orientation dynamique
  const [deploymentOrientation, setDeploymentOrientation] = useState<{
    friendlyBase: {q: number, r: number} | null;
    enemyBase: {q: number, r: number} | null;
    direction: {q: number, r: number} | null;
    friendlyBases?: Array<{q: number, r: number}>;
    enemyBases?: Array<{q: number, r: number}>;
  }>({
    friendlyBase: null,
    enemyBase: null,
    direction: null
  });

  // Fonction pour sélectionner automatiquement toutes les unités et héros
  const selectAllUnitsAndHeroes = () => {
    // Sélectionner toutes les unités par groupes
    const newSelectedUnits: { [playerId: string]: { [groupId: string]: boolean } } = {};
    const newSelectedHeroes: { [playerId: string]: string[] } = {};
    
    Object.entries(playerGroups).forEach(([playerId, playerData]) => {
      newSelectedUnits[playerId] = {};
      newSelectedHeroes[playerId] = [];
      
      // Sélectionner tous les groupes d'unités
      Object.entries(playerData.units).forEach(([unitType, count]) => {
        const unitCount = count as number;
        if (unitCount > 0) {
          const maxStackSize = unitStats[unitType]?.max_stack_size || 10;
          let remaining = unitCount;
          let groupIndex = 0;
          
          while (remaining > 0) {
            const groupId = `${playerId}_${unitType}_${groupIndex}`;
            newSelectedUnits[playerId][groupId] = true;
            remaining -= Math.min(remaining, maxStackSize);
            groupIndex++;
          }
        }
      });
      
      // Sélectionner tous les héros
      playerData.heroes.forEach((hero: any) => {
        const heroId = hero.instanceId || hero;
        newSelectedHeroes[playerId].push(heroId);
      });
    });
    
    setSelectedUnits(newSelectedUnits);
    setSelectedHeroes(newSelectedHeroes);
  };

  // =============================================================================
  // SECTION 2: CHARGEMENT DES UNITÉS RÉELLES
  // =============================================================================
  
  // Import optimisé de l'API
  const { getApiUrl } = require('../utils/api');

  // Protection contre les appels multiples simultanés
  const [isLoadingUnits, setIsLoadingUnits] = useState(false);
  
  const loadRealUnitsFromBattlefield = async () => {
    if (isLoadingUnits) {
      return;
    }
    
    setIsLoadingUnits(true);
    
    try {
      // Utiliser la fonction utilitaire pour l'URL
      const baseURL = getApiUrl();
      
      // Étape 1 : Trouver le bon battle_id
      const battlesResponse = await fetch(`${baseURL}/api/v2/battles/data`);
      const battlesData = await battlesResponse.json();
      
      // Trouver la bataille active pour cette ville
      let actualBattleId: string = battleId || '';
      
      if (targetCityId && !battleId) {
        // Chercher par ville via API serveur
        for (const [id, battleData] of Object.entries(battlesData)) {
          const battle = battleData as any;
          if (battle.location === targetCityId) {
            actualBattleId = id;
            break;
          }
        }
      }
      
      if (!actualBattleId) {
        return;
      }
      
      // 🔸 ÉTAPE 2 : Charger les unit_counts via la nouvelle API
      const unitCountsResponse = await fetch(`${baseURL}/api/v2/battle/${actualBattleId}/unit-counts`);
      
      if (!unitCountsResponse.ok) {
      }
      
      const unitCountsData = await unitCountsResponse.json();
      
      if (!unitCountsData.success) {
        return;
      }
      let playerGroups: { [playerId: string]: { units: any, heroes: any[], playerId: string } } = {};
      let formattedUnits: {[unitType: string]: any} = {};
      let availableHeroes: any[] = [];
      
      // Charger les données des héros réels
      const heroesResponse = await fetch(`${baseURL}/api/v2/player_heroes`);
      const heroesData = await heroesResponse.json();
      
      // Charger les stats des unités pour le formatage
      const unitStatsResponse = await fetch(`${baseURL}/api/v2/unit_stats`);
      const allStatsData = await unitStatsResponse.json();
      const allUnitsStats = {
        ...(allStatsData.stone_age || {}),
        ...(allStatsData.classical_age || {}),
        ...(allStatsData.medieval_age || {}),
        ...(allStatsData.renaissance_age || {}),
        ...(allStatsData.napoleonic_age || {}),
        ...(allStatsData.enemy_units || {})
      };
      setUnitStats(allUnitsStats);
      
      // Récupérer les participants pour filtrer par team
      const battlefieldsResponse = await fetch(`${baseURL}/api/v2/battlefields/data`);
      const battlefieldsData = await battlefieldsResponse.json();
      
      const battlefield = battlefieldsData[actualBattleId];
      if (!battlefield || !battlefield.participants) {
        return;
      }
      
      const attackers = battlefield.participants.attackers || [];
      const defenders = battlefield.participants.defenders || [];
      
      // Déterminer quels joueurs appartiennent à cette team
      const teamPlayers = team === 'attacker' ? attackers : defenders;
      
      // Traiter chaque joueur depuis unit_counts (FILTRÉ par team)
      const unit_counts = unitCountsData.unit_counts || {};
      Object.entries(unit_counts).forEach(([playerId, playerUnits]: [string, any]) => {
        // FILTRE: Ne traiter que les joueurs de cette team
        if (!teamPlayers.includes(playerId)) {
          return;
        }
        
        const availableUnits: { [unitType: string]: number } = {};
        const availablePlayerHeroes: any[] = [];
        
        Object.entries(playerUnits).forEach(([unitType, counts]: [string, any]) => {
          if (unitType === 'heroes') {
            // Traiter les héros - utiliser les vrais IDs depuis player_heroes.json
            const totalHeroes = counts.total || 0;
            const deployedHeroes = counts.deployed || 0;
            const availableHeroCount = totalHeroes - deployedHeroes;
            
            // Récupérer les vrais héros depuis player_heroes.json
            if (heroesData[playerId] && heroesData[playerId].heroes && availableHeroCount > 0) {
              const playerHeroes = heroesData[playerId].heroes;
              
              // Prendre les premiers héros disponibles (limité par availableHeroCount)
              const heroIds = Object.keys(playerHeroes).slice(0, availableHeroCount);
              
              heroIds.forEach(heroId => {
                const heroData = playerHeroes[heroId];
                availablePlayerHeroes.push({
                  id: heroId,
                  instanceId: heroId,  // VRAI ID du héros
                  name: `${heroData.hero_id} (Héros)`,
                  level: heroData.current_level || 1,
                  playerId: playerId,
                  stats: heroData.calculated_stats || { hp: 100, attack: 20, defense: 15 }
                });
              });
            } else if (availableHeroCount > 0) {
              // Fallback si pas de données héros (garder l'ancien comportement pour compatibilité)
              for (let i = 0; i < availableHeroCount; i++) {
                const heroInstanceId = `${playerId}_hero_${i+1}`;
                availablePlayerHeroes.push({
                  id: heroInstanceId,
                  instanceId: heroInstanceId,
                  name: `Héros ${i+1}`,
                  level: 1,
                  playerId: playerId,
                  stats: { hp: 150, attack: 20, defense: 15 }
                });
              }
            }
          } else {
            // Traiter les unités
            const totalUnits = counts.total || 0;
            const deployedUnits = counts.deployed || 0;
            const availableCount = totalUnits - deployedUnits;
            
            if (availableCount > 0) {
              availableUnits[unitType] = availableCount;
              
              // Formater pour l'affichage global
              const displayData = formatUnitDisplay(unitType, availableCount, allUnitsStats);
              if (displayData) {
                if (!formattedUnits[unitType]) {
                  formattedUnits[unitType] = displayData;
                } else {
                  formattedUnits[unitType].totalCount += availableCount;
                }
              }
            }
          }
        });
        
        // Stocker les données par joueur
        playerGroups[playerId] = {
          units: availableUnits,
          heroes: availablePlayerHeroes,
          playerId: playerId
        };
        
        // Ajouter les héros au pool global
        availableHeroes.push(...availablePlayerHeroes);
      });
      
      // =============================================================================
      // 4. METTRE À JOUR LES ÉTATS
      // =============================================================================
      setFormattedUnits(formattedUnits);
      setAvailableHeroes(availableHeroes);
      setTroopsOnTheWay({}); // Pas de renforts dans cette version simplifiée
      setReinforcementDetails([]); // Pas de renforts dans cette version simplifiée
      setPlayerGroups(playerGroups);
      

      
    } catch (error) {
      // Erreur silencieuse
    } finally {
      setIsLoadingUnits(false);
    }
  };

  // =============================================================================
  // SECTION 3: CALCUL D'ORIENTATION ET CHARGEMENT DU BATTLEFIELD (ancien code)
  // =============================================================================
  
  const calculateDeploymentOrientation = async () => {
    if (!battlefieldTemplateId) {
      return;
    }
    
    try {
      // Charge les données de battlefield depuis l'API
      const response = await fetch(`/api/battlefield/terrain-definitions/${battlefieldTemplateId}`);
      
      if (!response.ok) {
        return;
      }
      
      const data = await response.json();
      const hexCells = data.success ? data.terrain_definitions?.hexCells : [];
      
      if (!hexCells?.length) {
        return;
      }
      
      // Trouver les camps de base
      let attackBases = hexCells.filter((hex: any) => hex.terrain === 'base-attack');
      let defenseBases = hexCells.filter((hex: any) => hex.terrain === 'base-defense');
      
      // Fallback avec positions connues si nécessaire
      if (attackBases.length === 0) {
        const knownAttackPositions = [
          {q: 0, r: 4}, {q: 0, r: 5}, {q: 0, r: 6}, {q: 0, r: 7},
          {q: 1, r: 3}, {q: 2, r: 2}
        ];
        attackBases = knownAttackPositions
          .map(pos => hexCells.find((hex: any) => hex.q === pos.q && hex.r === pos.r))
          .filter((hex): hex is HexCell => hex !== undefined);
      }
      
      if (defenseBases.length === 0) {
        const knownDefensePositions = [
          {q: 14, r: 6}, {q: 13, r: 6}, {q: 12, r: 6}, 
          {q: 14, r: 5}, {q: 13, r: 5}, {q: 12, r: 5}
        ];
        defenseBases = knownDefensePositions
          .map(pos => hexCells.find((hex: any) => hex.q === pos.q && hex.r === pos.r))
          .filter((hex): hex is HexCell => hex !== undefined);
      }

      // Calculer l'orientation
      if (attackBases.length > 0 && defenseBases.length > 0) {
        const friendlyBases = team === 'attacker' ? attackBases : defenseBases;
        const enemyBases = team === 'attacker' ? defenseBases : attackBases;
        
        const friendlyCenter = {
          q: Math.round(friendlyBases.reduce((sum: number, base: any) => sum + base.q, 0) / friendlyBases.length),
          r: Math.round(friendlyBases.reduce((sum: number, base: any) => sum + base.r, 0) / friendlyBases.length)
        };
        
        const enemyCenter = {
          q: Math.round(enemyBases.reduce((sum: number, base: any) => sum + base.q, 0) / enemyBases.length),
          r: Math.round(enemyBases.reduce((sum: number, base: any) => sum + base.r, 0) / enemyBases.length)
        };
        
        const direction = {
          q: enemyCenter.q - friendlyCenter.q,
          r: enemyCenter.r - friendlyCenter.r
        };
        
        setDeploymentOrientation({
          friendlyBase: friendlyCenter,
          enemyBase: enemyCenter,
          direction,
          friendlyBases: friendlyBases.map((base: any) => ({ q: base.q, r: base.r })),
          enemyBases: enemyBases.map((base: any) => ({ q: base.q, r: base.r }))
        });
        
      }
    } catch (error) {
      // Erreur silencieuse
    }
  };

  // =============================================================================
  // SECTION 2: CHARGEMENT DES DONNÉES DE DÉPLOIEMENT
  // =============================================================================
  
  const loadDeploymentData = async () => {
    if (!targetCityId) {
      return;
    }
    
    setLoading(true);
    
    try {
      // Utiliser la fonction API existante
      const baseURL = getApiUrl();
      
      // Charger les données d'arrivée des unités
      const arrivedResponse = await fetch(`${baseURL}/api/military/city/${targetCityId}/arrived_units`);
      if (!arrivedResponse.ok) {
        throw new Error('Impossible de charger les unités arrivées');
      }
      
      const arrivedData = await arrivedResponse.json();
      
      // Charger les statistiques des unités
      const statsResponse = await fetch(`${baseURL}/api/military/units/stats`);
      if (statsResponse.ok) {
        const stats = await statsResponse.json();
        setUnitStats(stats.units || {});
      }
      
      // Convertir les données en format UnitGroup[]
      const unitsArray: UnitGroup[] = [];
      
      if (arrivedData.success && arrivedData.arrived_units) {
        Object.entries(arrivedData.arrived_units).forEach(([unitType, count]: [string, any]) => {
          if (count > 0) {
            unitsArray.push(createUnitGroup({
              id: `${unitType}_group`,
              type: unitType,
              name: unitType.charAt(0).toUpperCase() + unitType.slice(1),
              count: count,
              maxStack: 10,
              team,
              icon: `🪖`, // Icon par défaut
              status: 'arrived' as const
            }));
          }
        });
      }
      
    } catch (error) {
      // Erreur silencieuse
    } finally {
      setLoading(false);
    }
  };

  // =============================================================================
  // SECTION 3: DÉPLOIEMENT SIMPLE AVEC ZONES PRÉDÉFINIES
  // =============================================================================
  const simpleDeploymentServiceRef = useRef<SimpleDeploymentService | null>(null);

  const handleAutoDeployAll = async () => {
    if (!battlefieldTemplateId || !team) {
      alert('Impossible de déployer automatiquement : informations manquantes');
      return;
    }
    if (Object.keys(selectedUnits).length === 0 && Object.keys(selectedHeroes).length === 0) {
      alert('Aucune unité ou héros sélectionné pour le déploiement');
      return;
    }

    setLoading(true);
    try {
      // Initialiser le nouveau service simple
      if (!simpleDeploymentServiceRef.current) {
        simpleDeploymentServiceRef.current = new SimpleDeploymentService();
      }
      const deploymentService = simpleDeploymentServiceRef.current;

      // Charger les zones de déploiement depuis le battlefield
      await deploymentService.loadBattlefieldTemplate(battlefieldTemplateId);

      // Créer la liste des unités sélectionnées pour déploiement
      const selectedUnitGroups: any[] = [];

      // 1. Traiter les unités sélectionnées en utilisant max_stack_size
      for (const [playerId, playerSelections] of Object.entries(selectedUnits)) {
        if (!playerSelections || Object.keys(playerSelections).length === 0) continue;
        
        const playerData = playerGroups[playerId];
        const playerUnits = (playerData as any)?.units || {};
        
        // Parcourir les sélections de ce joueur
        Object.entries(playerSelections).forEach(([groupId, isSelected]) => {
          if (isSelected) {
            const parts = groupId.split('_');
            if (parts.length >= 3) {
              const unitTypeParts = parts.slice(2, -1);
              const unitType = unitTypeParts.join('_');
              
              if (playerUnits[unitType] && playerUnits[unitType] > 0) {
                const unitStat = unitStats[unitType];
                if (unitStat) {
                  // Calculer la vraie taille du groupe sélectionné
                  const maxStackSize = unitStat.max_stack_size || 10;
                  const groupIndex = parseInt(parts[parts.length - 1]);
                  
                  // Recalculer quelle est la taille de ce groupe spécifique
                  const totalCount = playerUnits[unitType];
                  let currentGroupSize = maxStackSize;
                  let remaining = totalCount;
                  
                  for (let i = 0; i <= groupIndex; i++) {
                    if (i === groupIndex) {
                      // C'est le groupe qu'on veut
                      currentGroupSize = Math.min(remaining, maxStackSize);
                      break;
                    }
                    remaining -= maxStackSize;
                  }
                  
                  const groupSize = currentGroupSize;
                  
                  const unitGroup = {
                    id: `${team}_${playerId}_${unitType}_${Date.now()}_${Math.random()}`,
                    type: unitType,
                    detailedType: unitType,
                    name: unitStat.name || unitType,
                    count: groupSize,
                    maxStack: maxStackSize,
                    team,
                    category: unitStat.category || 'infantry',
                    playerId,
                    // Propriétés UnitGroup requises
                    health: unitStat.health || 100,
                    maxHealth: unitStat.health || 100,
                    attack: unitStat.attack || 10,
                    defense: unitStat.defense || 8,
                    movement: unitStat.movement || 3,
                    morale: 100,
                    status: 'arrived' as const
                  };
                  selectedUnitGroups.push(unitGroup);
                }
              }
            }
          }
        });
      }

      // 2. Traiter les héros sélectionnés
      for (const [playerId, selectedHeroIds] of Object.entries(selectedHeroes)) {
        if (!selectedHeroIds || selectedHeroIds.length === 0) continue;
        
        const playerData = playerGroups[playerId];
        const playerHeroes = (playerData as any)?.heroes || [];
        
        for (const heroId of selectedHeroIds) {
          if (deployedHeroes[heroId]) continue; // Déjà déployé
          
          const hero = playerHeroes.find((h: any) => {
            return typeof h === 'string' ? h === heroId : h.instanceId === heroId;
          });
          
          if (hero) {
            const heroData = typeof hero === 'string' ? {
              instanceId: hero,
              name: hero.replace('hero_', '').slice(0, 10) + '...',
              stats: { health: 150, attack: 20, defense: 15 }
            } : hero;
            
            const heroGroup = {
              id: `${team}_${playerId}_hero_${heroData.instanceId}`,
              type: 'hero',
              detailedType: 'hero',
              name: heroData.name || 'Héros',
              count: 1,
              maxStack: 1,
              team,
              category: 'hero',
              playerId,
              isHero: true,
              heroData: {
                ...heroData,
                instanceId: heroData.instanceId,  // ✅ S'assurer que l'instanceId est correct
                realHeroId: heroData.instanceId  // ✅ Ajouter un champ explicite pour le vrai ID
              },
              // Propriétés UnitGroup requises - utiliser calculated_stats directement
              health: heroData.calculated_stats?.hp || 150,
              maxHealth: heroData.calculated_stats?.hp || 150,
              attack: heroData.calculated_stats?.attack_melee || 20,
              defense: heroData.calculated_stats?.defense_melee || 15,
              movement: heroData.calculated_stats?.movement || 4,
              morale: 100,
              status: 'arrived' as const
            };
            selectedUnitGroups.push(heroGroup);
          }
        }
      }

      // 3. Déployer automatiquement dans les zones prédéfinies
      const deploymentResult = await deploymentService.deployUnitsAutomatically(
        selectedUnitGroups,
        team,
        unitStats,
        (unitGroup: any, position: { q: number; r: number }) => {
          onDeployUnit(unitGroup, position);
          
          // Marquer les héros comme déployés
          if (unitGroup.isHero && unitGroup.heroData) {
            const heroId = unitGroup.heroData.instanceId || unitGroup.heroData;
            setDeployedHeroes(prev => ({...prev, [heroId]: true}));
          }
        },
        battleId // Passer le battleId pour charger les positions existantes
      );

      // 4. Sauvegarder les positions sur le serveur
      if (battleId && deploymentResult.deployed.length > 0) {
        try {
          await deploymentService.saveDeployedPositions(battleId, deploymentResult.deployed, team, 1);
          
          // ✅ Rafraîchir le battlefield pour visualiser les troupes déployées
          if (onDeploymentComplete) {
            onDeploymentComplete();
          }
        } catch (saveError) {
          // Erreur silencieuse
        }
      }

      // 5. Enlever les unités déployées du popup
      if (deploymentResult.deployed.length > 0) {
        // Mettre à jour les données pour supprimer les unités déployées
        const newPlayerGroups = { ...playerGroups };
        
        deploymentResult.deployed.forEach((deployedUnit: any) => {
          const playerId = deployedUnit.playerId;
          if (newPlayerGroups[playerId]) {
            const unitType = deployedUnit.type;
            if (newPlayerGroups[playerId].units[unitType]) {
              newPlayerGroups[playerId].units[unitType] = Math.max(0, 
                newPlayerGroups[playerId].units[unitType] - deployedUnit.count
              );
              
              // Supprimer complètement si 0
              if (newPlayerGroups[playerId].units[unitType] === 0) {
                delete newPlayerGroups[playerId].units[unitType];
              }
            }
          }
        });
        
        setPlayerGroups(newPlayerGroups);
        
        // Réinitialiser les sélections
        setSelectedUnits({});
        setSelectedHeroes({});
      }

      const message = `Déploiement terminé !\n✅ Déployées: ${deploymentResult.deployed.length}\n❌ Non déployées: ${deploymentResult.notDeployed.length}`;
      alert(message);

    } catch (error) {
      alert('Erreur lors du déploiement tactique.');
    } finally {
      setLoading(false);
    }
  };

  // =============================================================================
  // SECTION 4: GESTION DES ÉVÉNEMENTS ET CONTRÔLES - HOOK UNIQUE
  // =============================================================================
  
  // UN SEUL FICHIER pour gérer tout l'anti-zoom !
  usePreventZoom(isOpen);

  // =============================================================================
  // SECTION 5: EFFECTS ET LIFECYCLE
  // =============================================================================
  
  useEffect(() => {
    if (isOpen) {
      calculateDeploymentOrientation();
      loadRealUnitsFromBattlefield();
    }
  }, [isOpen, targetCityId, team, battlefieldTemplateId, battleId]);
  
  // Auto-sélectionner toutes les unités quand les données sont chargées
  useEffect(() => {
    if (Object.keys(playerGroups).length > 0 && unitStats && Object.keys(unitStats).length > 0) {
      selectAllUnitsAndHeroes();
    }
  }, [playerGroups, unitStats]);

  // =============================================================================
  // SECTION 6: RENDU DU COMPOSANT
  // =============================================================================
  
  if (!isOpen) {
    return null;
  }

  return (
    <div 
      className="unit-deployment-popup-v2-overlay"
      onWheel={handleOverlayWheel}
    >
      <div 
        className="unit-deployment-popup-v2-container"
        onClick={(e) => e.stopPropagation()}
        onWheel={handleContentWheel}
      >
        {/* En-tête */}
        <div className="unit-deployment-popup-v2-header">
          <h2>🚀 Déploiement des Troupes </h2>
          <p className="team-info">
            Équipe: <span className={`team-${team}`}>{team === 'attacker' ? 'Attaquant' : 'Défenseur'}</span>
          </p>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        {/* Bandeau position supprimé pour plus d'espace */}

        {/* Zone de contenu */}
        <div className="unit-deployment-popup-v2-content">
          {loading ? (
            <div className="loading-section">
              <div className="loading-spinner"></div>
              <p>Chargement des troupes...</p>
            </div>
          ) : (
            <>
              {/* =================================================================== */}
              {/* SECTION 1: UNITÉS DISPONIBLES AVEC GROUPEMENT MAX_STACK_SIZE */}
              {/* =================================================================== */}
              <div className="units-section">
                <h3>📍 Unités Disponibles</h3>
                
                {Object.keys(playerGroups).length === 0 ? (
                  <div className="no-units">
                    <p>Aucune unité disponible pour le déploiement</p>

                  </div>
                ) : (
                  <div className="players-list">
                    {Object.entries(playerGroups).map(([playerId, playerData]) => (
                      <div key={playerId} className="player-group">
                        <div className="player-header">
                          <h4>👤 {playerId}</h4>
                        </div>
                        
                        {/* Unités de ce joueur */}
                        {Object.keys(playerData.units).length > 0 && (
                          <div className="player-units">
                            {Object.entries(playerData.units).map(([unitType, count]) => {
                              const unitStat = unitStats[unitType];
                              const unitConfig = getUnitConfig(unitType, unitStats);
                              const totalCount = count as number;
                              
                              if (!unitStat) return null;
                              
                              // Créer les groupes basés sur max_stack_size
                              const maxStackSize = unitStat.max_stack_size || 10;
                              const groups = [];
                              let remaining = totalCount;
                              let groupIndex = 0;
                              
                              while (remaining > 0) {
                                const groupSize = Math.min(remaining, maxStackSize);
                                groups.push({
                                  id: `${playerId}_${unitType}_${groupIndex}`,
                                  size: groupSize,
                                  index: groupIndex,
                                  unitType: unitType
                                });
                                remaining -= groupSize;
                                groupIndex++;
                              }
                              
                              return (
                                <div key={unitType} className="unit-type-section">
                                  <div className="unit-type-header">
                                    <span className="unit-type-name">{unitConfig.name}</span>
                                    <span className="unit-type-total">({totalCount} total)</span>
                                  </div>
                                  
                                  <div className="unit-groups-row">
                                    {groups.map((group) => {
                                      const groupId = group.id;
                                      const isSelected = selectedUnits[playerId]?.[groupId] || false;
                                      
                                      return (
                                        <div 
                                          key={group.id}
                                          className={`unit-group-icon ${isSelected ? 'selected' : 'unselected'}`}
                                          onClick={() => {
                                            setSelectedUnits(prev => ({
                                              ...prev,
                                              [playerId]: {
                                                ...prev[playerId],
                                                [groupId]: !isSelected
                                              }
                                            }));
                                          }}
                                          title={`${isSelected ? 'Désélectionner' : 'Sélectionner'} ce groupe de ${group.size} ${unitConfig.name}`}
                                        >
                                          <div className={`unit-icon-small ${unitStat.category}`}>
                                            <span className="unit-icon-emoji">{unitConfig.icon}</span>
                                          </div>
                                          <div className="unit-group-count" title={`Groupe ${group.index} (${group.size} unités)`}>
                                            {group.size}
                                          </div>
                                          <div className="selection-overlay">
                                            {isSelected ? '✓' : ''}
                                          </div>
                                        </div>
                                      );
                                    })}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        )}
                        
                        {/* Héros de ce joueur */}
                        {playerData.heroes.length > 0 && (
                          <div className="player-heroes">
                            <h5>🦸‍♂️ Héros:</h5>
                            <div className="unit-groups-row">
                              {playerData.heroes.map((hero: any, index: number) => {
                                const heroId = hero.instanceId || hero;
                                const isSelected = selectedHeroes[playerId]?.includes(heroId) || false;
                                
                                return (
                                  <div 
                                    key={index} 
                                    className={`unit-group-icon ${isSelected ? 'selected' : 'unselected'}`}
                                    onClick={() => toggleHeroSelection(playerId, heroId)}
                                    title={`Cliquer pour ${isSelected ? 'désélectionner' : 'sélectionner'} ${hero.name || heroId}`}
                                  >
                                    <div className="unit-icon">👑</div>
                                    <div className="unit-count">1</div>
                                    {isSelected && <div className="selection-overlay">✓</div>}
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* =================================================================== */}
              {/* SECTION RÉSUMÉ DE SÉLECTION */}
              {/* =================================================================== */}
              <div className="selection-summary">
                <h4>📋 Sélection</h4>
                
                {(() => {
                  let totalSelectedUnits = 0;
                  let totalSelectedHeroes = 0;
                  
                  // Compter les unités sélectionnées en recalculant les groupes
                  Object.entries(selectedUnits).forEach(([playerId, playerSelections]) => {
                    if (playerGroups[playerId]) {
                      Object.entries(playerGroups[playerId].units).forEach(([unitType, count]) => {
                        const unitStat = unitStats[unitType];
                        if (!unitStat) return;
                        
                        const totalCount = count as number;
                        const maxStackSize = unitStat.max_stack_size || 10;
                        let remaining = totalCount;
                        let groupIndex = 0;
                        
                        while (remaining > 0) {
                          const groupSize = Math.min(remaining, maxStackSize);
                          const groupId = `${playerId}_${unitType}_${groupIndex}`;
                          
                          if (playerSelections[groupId]) {
                            totalSelectedUnits += groupSize;
                          }
                          
                          remaining -= groupSize;
                          groupIndex++;
                        }
                      });
                    }
                  });
                  
                  // Compter les héros sélectionnés
                  Object.values(selectedHeroes).forEach(playerHeroes => {
                    totalSelectedHeroes += playerHeroes.length;
                  });
                  
                  if (totalSelectedUnits === 0 && totalSelectedHeroes === 0) {
                    return (
                      <div className="no-selection">
                        <p>🔄 Sélectionnez des unités et/ou héros pour le déploiement</p>
                      </div>
                    );
                  }
                  
                  return (
                    <div className="selection-details">
                      <div className="selection-stats">
                        <div className="stat-item">
                          <span className="stat-icon">⚔️</span>
                          <span className="stat-value">{totalSelectedUnits}</span>
                          <span className="stat-label">unités sélectionnées</span>
                        </div>
                        
                        <div className="stat-item">
                          <span className="stat-icon">👑</span>
                          <span className="stat-value">{totalSelectedHeroes}</span>
                          <span className="stat-label">héros sélectionnés</span>
                        </div>
                      </div>
                      
                      <div className="deployment-actions">
                        <button 
                          className="clear-selection-btn"
                          onClick={() => {
                            setSelectedUnits({});
                            setSelectedHeroes({});
                          }}
                        >
                          🧹 Effacer la Sélection
                        </button>
                      </div>
                    </div>
                  );
                })()}
              </div>

              {/* =================================================================== */}
              {/* SECTION 4: UNITÉS EN CHEMIN (RENFORTS) */}
              {/* =================================================================== */}
              <div className="reinforcements-section">
                <h4>🚚 En Chemin</h4>
                
                {reinforcementDetails.length === 0 ? (
                  <div className="no-reinforcements">
                    <p>Aucun renfort en chemin actuellement</p>
                  </div>
                ) : (
                  <div className="reinforcements-list">
                    {reinforcementDetails.map((reinforcement, index) => (
                      <div key={index} className="reinforcement-entry">
                        <div className="reinforcement-header">
                          <div className="reinforcement-route">
                            📍 {reinforcement.fromCity} → {reinforcement.toCity}
                          </div>
                          <div className="reinforcement-timer">
                            ⏰ Arrivée dans: {calculateTimeToArrival(reinforcement.arrivalTime)}
                          </div>
                        </div>
                        
                        <div className="reinforcement-units">
                          {Object.entries(reinforcement.units).map(([unitType, count]) => {
                            const config = getUnitConfig(unitType, unitStats);
                            return (
                              <div key={unitType} className="reinforcement-unit">
                                <div className="reinforcement-unit-icon">{config.icon}</div>
                                <div className="reinforcement-unit-info">
                                  <div className="reinforcement-unit-name">{config.name}</div>
                                  <div className="reinforcement-unit-count">x{count as number}</div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="actions-section">
                <button 
                  className="auto-deploy-button"
                  onClick={handleAutoDeployAll}
                  disabled={Object.keys(formattedUnits).length === 0}
                >
                  🚀 Déployer la Sélection
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default UnitDeploymentPopupV2;