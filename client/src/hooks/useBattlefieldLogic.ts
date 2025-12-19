/**
 * useBattlefieldLogic.ts
 * 
 * Hook custom qui encapsule tou  // État des données
  const [dataState, setDataState] = useState({
    currentBattlefield: null as any,
    currentBattlefieldTemplate: null as BattlefieldTemplate | null,
    battleGrid: [] as HexCell[],
    battleUnits: [] as any[],
    battleData: null as any
  });
  
  // État du drag & drop
  const [dragState, setDragState] = useState({
    isDragging: false,
    dragStart: null as { x: number, y: number } | null,
    viewOffset: { x: 0, y: 0 },
    lastMousePos: { x: 0, y: 0 }
  });er du battlefield :
 * - Gestion des états (phases, rounds, unités,       // Calculer les auras après chargement des unités
      calculateUnitsInHeroAura();
    }ment des données (battlefield templates, unités de bataille)
 * - Gestionnaires d'événements (sélection, déploiement, combat)
 * - Appels API (déplacement, fin de bataille)
 * - Système de drag/navigation
 * 
 * Sépare clairement la logique de l'affichage pour améliorer la maintenabilité
 */

import { useState, useEffect } from 'react';
import { Unit, HexCell } from '../types/index';
import { BattlefieldAdapter, type StandardizedBattlefield } from '../utils/BattlefieldAdapter';
import { initializeBattleColors } from '../utils/playerColors';
import { getApiUrl } from '../utils/api';

// Interface locale pour BattlefieldTemplate
interface BattlefieldTemplate {
  id: string;
  name: string;
  description: string;
  size: { width: number; height: number };
  difficulty: string;
  hexCells?: HexCell[];
  deploymentZones?: any;
  terrainDefinitions?: any;
  backgroundImage?: string;
}

interface UseBattlefieldLogicProps {
  gamePhase?: 'deployment' | 'battle' | 'victory';
  currentPlayer?: 'attacker' | 'defender';
  attackerUnits?: { [unitType: string]: number };
  defenderUnits?: { [unitType: string]: number };
  targetCityId?: string;
  battleId?: string;
  initialRound?: number;
  initialCurrentPlayer?: string;
  onRoundChange?: (round: number, player: string) => void;
  onStatsChange?: (attackerStats: { units: number, moral: number }, defenderStats: { units: number, moral: number }) => void;
  battlefieldTemplateId?: string;
}

export const useBattlefieldLogic = ({
  gamePhase = 'deployment',
  currentPlayer = 'attacker',
  attackerUnits = {},
  defenderUnits = {},
  targetCityId,
  battleId,
  initialRound,
  initialCurrentPlayer,
  battlefieldTemplateId = 'default_working'
}: UseBattlefieldLogicProps) => {
  
  // ========== CONSTANTES ==========
  const GRID_SIZE = 30; // Taille de la grille de bataille
  
  // ========== ÉTATS REGROUPÉS PAR THÈME ==========
  
  // 🎮 ÉTAT DE L'UI ET INTERACTIONS
  const [uiState, setUiState] = useState({
    selectedHex: null as {q: number, r: number} | null,
    selectedUnit: null as Unit | null,
    selectedCompactUnit: null as any,
    hoveredHex: null as {q: number, r: number} | null,
    showUnitPanel: false,
    deploymentPopupOpen: false,
    selectedTeam: null as 'attacker' | 'defender' | null,
    wallInteractionPopupOpen: false,
    selectedWallPosition: null as {q: number, r: number} | null
  });
  
  // État de la bataille
  const [battleState, setBattleState] = useState({
    gamePhase: 'battle' as 'deployment' | 'battle' | 'victory',
    currentRound: initialRound || 1,
    currentPlayer: initialCurrentPlayer || '',
    attackerStats: { units: 0, moral: 100 },
    defenderStats: { units: 0, moral: 100 },
    actualBattleId: battleId || 'bfv2_06p7982f'
  });
  
  // 🗂️ ÉTAT DES DONNÉES
  const [dataState, setDataState] = useState({
    currentBattlefield: null as any,
    currentBattlefieldTemplate: null as BattlefieldTemplate | null,
    battleGrid: [] as HexCell[],
    battleUnits: [] as any[],
    battleData: null as any,
    backgroundImage: null as string | null
  });
  
  // 🖱️ ÉTAT DU DRAG & DROP
  const [dragState, setDragState] = useState({
    isDragging: false,
    dragStart: null as { x: number, y: number } | null,
    viewOffset: { x: 0, y: 0 },
    lastMousePos: { x: 0, y: 0 }
  });
  
  // 🏆 ÉTAT DES AURAS HÉROS DÉPLACÉ vers BattlefieldVisualsV2.tsx

  // ========== GETTERS/SETTERS POUR COMPATIBILITÉ ==========
  // Permettent d'utiliser les anciens noms sans casser le code existant
  
  // UI State getters/setters
  const selectedHex = uiState.selectedHex;
  const setSelectedHex = (value: any) => setUiState(prev => ({ ...prev, selectedHex: value }));
  const selectedUnit = uiState.selectedUnit;
  const setSelectedUnit = (value: any) => setUiState(prev => ({ ...prev, selectedUnit: value }));
  const selectedCompactUnit = uiState.selectedCompactUnit;
  const setSelectedCompactUnit = (value: any) => setUiState(prev => ({ ...prev, selectedCompactUnit: value }));
  const hoveredHex = uiState.hoveredHex;
  const setHoveredHex = (value: any) => setUiState(prev => ({ ...prev, hoveredHex: value }));
  const showUnitPanel = uiState.showUnitPanel;
  const setShowUnitPanel = (value: any) => setUiState(prev => ({ ...prev, showUnitPanel: value }));
  const deploymentPopupOpen = uiState.deploymentPopupOpen;
  const setDeploymentPopupOpen = (value: any) => setUiState(prev => ({ ...prev, deploymentPopupOpen: value }));
  const selectedTeam = uiState.selectedTeam;
  const setSelectedTeam = (value: any) => setUiState(prev => ({ ...prev, selectedTeam: value }));
  const wallInteractionPopupOpen = uiState.wallInteractionPopupOpen;
  const setWallInteractionPopupOpen = (value: any) => setUiState(prev => ({ ...prev, wallInteractionPopupOpen: value }));
  const selectedWallPosition = uiState.selectedWallPosition;
  const setSelectedWallPosition = (value: any) => setUiState(prev => ({ ...prev, selectedWallPosition: value }));

  // Battle State getters/setters
  const localGamePhase = battleState.gamePhase;
  const setLocalGamePhase = (value: any) => setBattleState(prev => ({ ...prev, gamePhase: value }));
  const currentRound = battleState.currentRound;
  const setCurrentRound = (value: any) => setBattleState(prev => ({ ...prev, currentRound: value }));
  const roundCurrentPlayer = battleState.currentPlayer;
  const setRoundCurrentPlayer = (value: any) => setBattleState(prev => ({ ...prev, currentPlayer: value }));
  const attackerStats = battleState.attackerStats;
  const setAttackerStats = (value: any) => setBattleState(prev => ({ ...prev, attackerStats: value }));
  const defenderStats = battleState.defenderStats;
  const setDefenderStats = (value: any) => setBattleState(prev => ({ ...prev, defenderStats: value }));
  const actualBattleId = battleState.actualBattleId;
  const setActualBattleId = (value: any) => setBattleState(prev => ({ ...prev, actualBattleId: value }));

  // Data State getters/setters
  const currentBattlefield = dataState.currentBattlefield;
  const setCurrentBattlefield = (value: any) => setDataState(prev => ({ ...prev, currentBattlefield: value }));
  const currentBattlefieldTemplate = dataState.currentBattlefieldTemplate;
  const setCurrentBattlefieldTemplate = (value: any) => setDataState(prev => ({ ...prev, currentBattlefieldTemplate: value }));
  const battleGrid = dataState.battleGrid;
  const setBattleGrid = (value: any) => setDataState(prev => ({ ...prev, battleGrid: value }));
  const battleUnits = dataState.battleUnits;
  const setBattleUnits = (value: any) => setDataState(prev => ({ ...prev, battleUnits: value }));
  const battleData = dataState.battleData;
  const setBattleData = (value: any) => setDataState(prev => ({ ...prev, battleData: value }));
  const backgroundImage = dataState.backgroundImage;
  const setBackgroundImage = (value: string | null) => setDataState(prev => ({ ...prev, backgroundImage: value }));

  // Drag State getters/setters
  const isDragging = dragState.isDragging;
  const setIsDragging = (value: any) => setDragState(prev => ({ ...prev, isDragging: value }));
  const dragStart = dragState.dragStart;
  const setDragStart = (value: any) => setDragState(prev => ({ ...prev, dragStart: value }));
  const viewOffset = dragState.viewOffset;
  const setViewOffset = (value: any) => {
    setDragState(prev => ({ 
      ...prev, 
      viewOffset: typeof value === 'function' ? value(prev.viewOffset) : value 
    }));
  };
  const lastMousePos = dragState.lastMousePos;
  const setLastMousePos = (value: any) => setDragState(prev => ({ ...prev, lastMousePos: value }));

  // Hero Aura state déplacé vers BattlefieldVisualsV2 via useHeroAura hook

  // ========== CHARGEMENT DES DONNÉES ==========
  
  // Auto-détection de l'ID de bataille depuis battlefields_v2.json par targetCityId
  useEffect(() => {
    const detectBattleId = async () => {
      if (battleId) {
        setBattleState(prev => ({ ...prev, actualBattleId: battleId }));
        return;
      }
      
      try {
        // 1. Si on a un targetCityId, chercher d'abord par ville dans battlefields_v2.json
        if (targetCityId) {

          
          const battlefieldsResponse = await fetch(`${getApiUrl()}/data/battlefields_v2.json`);
          const allBattlefields = await battlefieldsResponse.json();
          
          // Chercher la bataille correspondante à cette ville avec status 'battle_ready'
          for (const [battlefieldId, battlefield] of Object.entries(allBattlefields)) {
            const battleData = battlefield as any;
            if (battleData.location === targetCityId && battleData.status === 'battle_ready') {
              setActualBattleId(battlefieldId);
              return;
            }
          }
          
          // Chercher aussi avec d'autres status au cas où
          for (const [battlefieldId, battlefield] of Object.entries(allBattlefields)) {
            const battleData = battlefield as any;
            if (battleData.location === targetCityId) {
              setActualBattleId(battlefieldId);
              return;
            }
          }
        }
        
        // 2. Fallback SEULEMENT si pas de targetCityId
        if (!targetCityId) {
          const battlefieldsResponse = await fetch(`${getApiUrl()}/data/battlefields_v2.json`);
          const allBattlefields = await battlefieldsResponse.json();
          
          const battlefieldIds = Object.keys(allBattlefields);
          const selectedId = battlefieldIds[0];
          
          if (selectedId) {
            setBattleState(prev => ({ ...prev, actualBattleId: selectedId }));
          }
        }
      } catch (error) {
        // Erreur silencieuse pour l'auto-détection
      }
    };
    
    detectBattleId();
  }, [battleId, targetCityId]);
  
  useEffect(() => {
    if (battlefieldTemplateId) {
      loadBattlefieldData();
    } else {
      // Charger les données de fallback immédiatement
      setBattleGrid([
        { q: 0, r: 0, terrain: 'plains', unit: undefined, zone: 'battlefield', defenseBonus: 0, attackPenalty: 0, movementBonus: 0 },
        { q: 1, r: 0, terrain: 'forest', unit: undefined, zone: 'battlefield', defenseBonus: 0, attackPenalty: 0, movementBonus: 0 },
        { q: -1, r: 1, terrain: 'hill', unit: undefined, zone: 'attacker-base', defenseBonus: 0, attackPenalty: 0, movementBonus: 0 },
        { q: 0, r: 1, terrain: 'hill', unit: undefined, zone: 'battlefield', defenseBonus: 0, attackPenalty: 0, movementBonus: 0 },
        { q: 1, r: -1, terrain: 'river', unit: undefined, zone: 'defender-base', defenseBonus: 0, attackPenalty: 0, movementBonus: 0 },
      ]);
    }
  }, [battlefieldTemplateId]);

  // Charger les données des unités depuis battlesv2.json
  useEffect(() => {
    if (battleState.actualBattleId) {
      loadBattleUnits();
      loadBattlefieldStats(); // Charger également les stats réelles
      // Synchroniser l'état avec le serveur après chargement
      syncBattleStateFromServer();
    }
  }, [battleState.actualBattleId]);

  // 🔄 RAFRAÎCHISSEMENT AUTOMATIQUE - Synchroniser avec le serveur
  useEffect(() => {
    if (battleState.actualBattleId) {
      const interval = setInterval(() => {
        syncBattleStateFromServer(); // Round, current_player
        loadBattlefieldStats(); // Moral, nb unités
        loadBattleUnits(); // ⚡ RECHARGER LES POSITIONS DES UNITÉS (IA)
      }, 2000); // Toutes les 2 secondes pour être réactif

      return () => clearInterval(interval);
    }
  }, [battleState.actualBattleId]);

  // 🔄 Recharger les unités quand le round change (nouvelles positions)
  useEffect(() => {
    if (battleState.actualBattleId && currentRound > 1) {
      loadBattleUnits();
    }
  }, [currentRound]);

  // Les calculs d'aura sont maintenant gérés dans BattlefieldVisualsV2 via useHeroAura

  // ========== FONCTIONS DE CHARGEMENT ==========

  const loadBattlefieldStats = async () => {
    try {
      const apiResponse = await fetch(`${getApiUrl()}/api/v2/battle/stats/${actualBattleId}`);
      if (apiResponse.ok) {
        const statsData = await apiResponse.json();
        setAttackerStats({ 
          units: statsData.attacker?.units || 0, 
          moral: statsData.attacker?.moral !== undefined ? statsData.attacker.moral : 100 
        });
        setDefenderStats({ 
          units: statsData.defender?.units || 0, 
          moral: statsData.defender?.moral !== undefined ? statsData.defender.moral : 100 
        });
      } else {
        // Stats par défaut en cas d'erreur
        setAttackerStats({ units: 0, moral: 100 });
        setDefenderStats({ units: 0, moral: 100 });
      }
    } catch (error) {
      console.error('❌ [STATS] Erreur fetch:', error); // 🔍 DEBUG
      // Stats par défaut en cas d'erreur
      setAttackerStats({ units: 0, moral: 100 });
      setDefenderStats({ units: 0, moral: 100 });
    }
  };

  // ✨ Fonctions d'aura héros déplacées vers BattlefieldVisualsV2.tsx (hook useHeroAura)

  // ✨ Toutes les fonctions d'aura héros ont été déplacées vers BattlefieldVisualsV2.tsx

  const loadBattlefieldData = async () => {
    try {
      console.log('🔍 [LOAD-BATTLEFIELD] battlefieldTemplateId:', battlefieldTemplateId);
      console.log('🔍 [LOAD-BATTLEFIELD] actualBattleId:', actualBattleId);
      
      if (actualBattleId) {
        try {
          const battlefieldDataResponse = await fetch(`${getApiUrl()}/api/v2/battlefields/data`);
          if (battlefieldDataResponse.ok) {
            const battlefieldsData = await battlefieldDataResponse.json();
            const currentBattleData = battlefieldsData[actualBattleId];
            if (currentBattleData) {
              setCurrentBattlefield(currentBattleData);
            }
          }
        } catch (error) {
          console.error('Erreur chargement battlefield data:', error);
        }
      }
      
      // 🎯 CORRECTION : Charger la bataille EN COURS (pas le template) pour voir les murs détruits
      const adapter = new BattlefieldAdapter();
      
      // D'abord essayer de charger la bataille en cours avec hex map modifiée
      let standardizedBattlefield: StandardizedBattlefield | null = null;
      
      if (actualBattleId) {
        try {
          const battlefieldsResponse = await fetch(`${getApiUrl()}/data/battlefields_v2.json`);
          if (battlefieldsResponse.ok) {
            const battlesData = await battlefieldsResponse.json();
            const currentBattle = battlesData[actualBattleId];
            console.log('🔍 [LOAD-BATTLEFIELD] currentBattle trouvée:', !!currentBattle);
            console.log('🔍 [LOAD-BATTLEFIELD] currentBattle.hexMap:', !!currentBattle?.hexMap);
            
            if (currentBattle?.hexMap) {
              // Charger d'abord le template pour avoir la structure complète
              const templateResponse = await fetch(`${getApiUrl()}/data/battlefields/${battlefieldTemplateId}.json`);
              const templateData = await templateResponse.json();
              
              // 🖼️ Extraire backgroundImage du template
              const bgImage = templateData?.template?.backgroundImage;
              console.log('🖼️ [HOOK] Template chargé:', templateData?.template?.id);
              console.log('🖼️ [HOOK] backgroundImage cherché:', bgImage);
              if (bgImage) {
                console.log('✅ [HOOK] backgroundImage trouvée:', bgImage);
                setBackgroundImage(bgImage);
              } else {
                console.warn('⚠️ [HOOK] Pas de backgroundImage dans template.deploymentZones');
              }
              
              // Créer un battlefield avec la hex map modifiée de la bataille
              const battlefieldWithModifiedMap = {
                ...templateData,
                hexMap: currentBattle.hexMap  // Utiliser la hex map modifiée
              };
              
              standardizedBattlefield = await adapter.loadBattlefield(battlefieldWithModifiedMap);

            }
          }
        } catch (error) {

        }
      }
      
      // Fallback sur le template si pas de bataille modifiée
      if (!standardizedBattlefield) {
        const battlefieldPath = `${getApiUrl()}/data/battlefields/${battlefieldTemplateId}.json`;
        
        // 🖼️ Charger aussi l'image de fond pour le fallback
        try {
          const fallbackResponse = await fetch(battlefieldPath);
          const fallbackData = await fallbackResponse.json();
          const bgImage = fallbackData?.template?.backgroundImage;
          console.log('🖼️ [HOOK-FALLBACK] backgroundImage:', bgImage);
          if (bgImage) {
            setBackgroundImage(bgImage);
          }
        } catch (e) {
          console.error('❌ [HOOK-FALLBACK] Erreur chargement image:', e);
        }
        
        standardizedBattlefield = await adapter.loadBattlefield(battlefieldPath);

      }
      
      // Conversion vers le format attendu par le composant
      if (standardizedBattlefield && standardizedBattlefield.hexCells) {
        const battleGridWithUnits = standardizedBattlefield.hexCells.map(cell => ({
          q: cell.q,
          r: cell.r,
          terrain: cell.terrain as any, // Cast temporaire pour compatibilité  
          unit: undefined,
          zone: (cell.zone === 'battlefield' ? 'battlefield' : 
                cell.zone === 'attacker-base' ? 'attacker-base' : 
                cell.zone === 'defender-base' ? 'defender-base' : 'battlefield') as any,
          defenseBonus: cell.defenseBonus,
          attackPenalty: cell.attackPenalty,
          movementBonus: cell.movementBonus
        }));
        
        setBattleGrid(battleGridWithUnits);

        
        // Afficher les statistiques de performance
        const stats = adapter.getPerformanceStats(standardizedBattlefield);

      } else {
        // Fallback sur battlefield minimal
        setBattleGrid([
          { q: 0, r: 0, terrain: 'plains', unit: undefined, zone: 'battlefield', defenseBonus: 0, attackPenalty: 0, movementBonus: 0 },
          { q: 1, r: 0, terrain: 'forest', unit: undefined, zone: 'battlefield', defenseBonus: 0, attackPenalty: 0, movementBonus: 0 },
          { q: -1, r: 1, terrain: 'hill', unit: undefined, zone: 'attacker-base', defenseBonus: 0, attackPenalty: 0, movementBonus: 0 },
        ]);
      }
    } catch (error) {
      // Fallback sur un battlefield minimal
      setBattleGrid([
        { q: 0, r: 0, terrain: 'plains', unit: undefined, zone: 'battlefield', defenseBonus: 0, attackPenalty: 0, movementBonus: 0 },
        { q: 1, r: 0, terrain: 'forest', unit: undefined, zone: 'battlefield', defenseBonus: 0, attackPenalty: 0, movementBonus: 0 },
        { q: -1, r: 1, terrain: 'hill', unit: undefined, zone: 'attacker-base', defenseBonus: 0, attackPenalty: 0, movementBonus: 0 },
        { q: 0, r: 1, terrain: 'hill', unit: undefined, zone: 'battlefield', defenseBonus: 0, attackPenalty: 0, movementBonus: 0 },
        { q: 1, r: -1, terrain: 'river', unit: undefined, zone: 'defender-base', defenseBonus: 0, attackPenalty: 0, movementBonus: 0 },
      ]);
    }
  };

  const loadBattleUnits = async () => {
    try {
      // Essayer d'abord l'API puis fallback sur le fichier local
      let data;
      try {
        const response = await fetch(`${getApiUrl()}/api/v2/battle/get-positions/${actualBattleId}`);
        if (response.ok) {
          data = await response.json();
        } else {
          throw new Error('API non accessible');
        }
      } catch (apiError) {

        // Fallback: charger directement depuis le fichier local
        const response = await fetch(`${getApiUrl()}/data/battlesv2.json`);
        const allBattles = await response.json();
        data = allBattles[actualBattleId];
      }
      
      if (data && data.teams) {
        // Charger les données des héros pour enrichir les unités
        let heroesData = {};
        try {
          const heroesResponse = await fetch(`${getApiUrl()}/api/v2/player_heroes`);
          if (heroesResponse.ok) {
            heroesData = await heroesResponse.json();
          }
        } catch (error) {
        }
        
        // Extraire toutes les unités de toutes les équipes dans un tableau plat
        const allUnits = [];
        for (const [teamKey, units] of Object.entries(data.teams)) {
          for (const unit of units as any[]) {
            const unitData: any = {
              id: unit.unitId,
              position: unit.position,
              team: teamKey.includes('attacker') ? 'attacker' : 'defender',
              unitCount: unit.unitCount,
              hp: unit.hp
            };
            
            // Détecter et enrichir les héros
            if (unit.hp && !unit.unitCount) {
              // C'est un héros (a hp mais pas unitCount)
              unitData.type = 'hero';
              
              // Extraire l'ID du héros pour chercher dans player_heroes
              let heroKey = '';
              const unitId = unit.unitId;
              
              // Si l'ID commence déjà par "hero_", c'est probablement déjà la bonne clé
              if (unitId.startsWith('hero_')) {
                heroKey = unitId;
              }
              // Si c'est un ID complexe avec "_hero_", extraire la partie héros
              else if (unitId.includes('_hero_')) {
                const parts = unitId.split('_');
                const heroIndex = parts.indexOf('hero');
                if (heroIndex !== -1) {
                  // Prendre tout à partir de "hero"
                  const heroElements = parts.slice(heroIndex);
                  heroKey = heroElements.join('_');
                }
              }
              
              // Chercher les données du héros
              for (const playerId in heroesData) {
                const playerData = (heroesData as any)[playerId];
                if (playerData.heroes && playerData.heroes[heroKey]) {
                  unitData.heroData = playerData.heroes[heroKey];
                  unitData.name = `${playerData.heroes[heroKey].hero_id} (Héros)`;
                  
                  // ✅ CORRECTION: Utiliser les HP réels de player_heroes.json
                  if (playerData.heroes[heroKey].calculated_stats?.hp) {
                    unitData.hp = playerData.heroes[heroKey].calculated_stats.hp;
                  }
                  
                  break;
                }
              }
            }
            
            allUnits.push(unitData);
          }
        }
        setBattleUnits(allUnits);
        setBattleData(data); // Met à jour la donnée brute pour BattlefieldVisualsV2
        
        // Déterminer la phase selon le round
        const currentRound = data.current_round || 1;
        setCurrentRound(currentRound); // 🔄 IMPORTANT: Mettre à jour le round affiché
        if (currentRound === 1) {
          setLocalGamePhase('deployment');
        } else {
          setLocalGamePhase('battle');
        }
        
        // Charger les participants depuis battlefields_v2.json pour l'initialisation des couleurs
        try {
          const battlefieldsResponse = await fetch(`${getApiUrl()}/data/battlefields_v2.json`);
          const battlefieldsData = await battlefieldsResponse.json();
          const battlefieldInfo = battlefieldsData[actualBattleId];
          
          if (battlefieldInfo) {
            const combinedData = {
              ...data,
              participants: battlefieldInfo.participants,
              wall_system: battlefieldInfo.wall_system || null,
              // ⏱️ TIMER: Ajouter les données de fin de bataille pour arrêter le timer
              surrender_info: battlefieldInfo.surrender_info,
              completed_at: battlefieldInfo.completed_at,
              status: battlefieldInfo.status
            };
            setBattleData(combinedData); // Met à jour avec les données de mur
            initializeBattleColors(combinedData);
          } else {
            initializeBattleColors(data);
          }
        } catch (error) {
          initializeBattleColors(data);
        }
      } else {

      }
    } catch (error) {
    }
  };

  // ========== GESTIONNAIRES D'ÉVÉNEMENTS ==========
  
  const handleOpenDeploymentPopup = () => {
    // Déterminer l'équipe en fonction de la zone de l'hexagone sélectionné
    if (selectedHex) {
      const hexData = battleGrid.find(h => h.q === selectedHex.q && h.r === selectedHex.r);
      if (hexData) {
        if (hexData.zone === 'attacker-base' || hexData.terrain === 'base-attack') {
          setSelectedTeam('attacker');
        } else if (hexData.zone === 'defender-base' || hexData.terrain === 'base-defense') {
          setSelectedTeam('defender');
        } else {
          setSelectedTeam('attacker'); // Par défaut
        }
      }
    }
    
    setDeploymentPopupOpen(true);
  };

  const handleDeployUnit = (unitGroup: any, hexPosition: { q: number, r: number }) => {
    // Déploiement local uniquement - la sauvegarde se fait via saveDeployedPositions
    const deploy = async () => {
      try {
        // Pas d'appel API ici - la sauvegarde se fait dans saveDeployedPositions
        // Recharge la grille et les unités
        await loadBattleUnits();
        await loadBattlefieldStats(); // Actualiser aussi les stats
      } catch (e) {
      } finally {
        setDeploymentPopupOpen(false);
      }
    };
    deploy();
  };

  // ========== GESTIONNAIRES DE SOURIS/DRAG ==========

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
    setLastMousePos({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging && dragStart) {
      const deltaX = e.clientX - lastMousePos.x;
      const deltaY = e.clientY - lastMousePos.y;
      setViewOffset((prev: any) => ({
        x: (prev.x || 0) + deltaX,
        y: (prev.y || 0) + deltaY
      }));
      setLastMousePos({ x: e.clientX, y: e.clientY });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setDragStart(null);
  };

  // Helper pour récupérer le groupe de mur à une position
  const getWallGroupAtPositionHelper = (position: {q: number, r: number}) => {
    if (!dataState.battleData?.wall_system?.wall_groups) return null;
    
    const wallGroups = dataState.battleData.wall_system.wall_groups;
    for (const [groupKey, groupData] of Object.entries(wallGroups)) {
      const positions = (groupData as any).positions || [];
      // Vérifier si la position existe dans ce groupe
      const positionExists = positions.some((pos: [number, number]) => 
        pos[0] === position.q && pos[1] === position.r
      );
      if (positionExists) {
        return { key: groupKey, ...(groupData as any) };
      }
    }
    return null;
  };

  const handleHexClick = (hex: HexCell) => {
    if (!isDragging) {
      setSelectedHex({ q: hex.q, r: hex.r });
      
      // 🧱 Détecter clic sur mur
      if (hex.terrain === 'wall') {
        setSelectedWallPosition({ q: hex.q, r: hex.r });
        setWallInteractionPopupOpen(true);
      } else {
        // Vérifier s'il y a des données de mur à cette position
        const wallGroup = getWallGroupAtPositionHelper({ q: hex.q, r: hex.r });
        if (wallGroup) {
          setSelectedWallPosition({ q: hex.q, r: hex.r });
          setWallInteractionPopupOpen(true);
        }
      }
    }
  };

  // ========== ACTIONS DE BATAILLE ==========

    // Helper pour vérifier si une position est occupée selon les données client
  const isPositionOccupiedByUnits = (position: [number, number], excludingUnitId?: string): boolean => {
    if (!battleUnits || !Array.isArray(battleUnits)) {
      return false; // Si pas de données, considérer libre (fallback)
    }
    
    return battleUnits.some((unit: any) => {
      // Ignorer l'unité qui se déplace
      if (excludingUnitId && (unit.unitId === excludingUnitId || unit.id === excludingUnitId)) {
        return false;
      }
      
      // Vérifier si cette unité occupe la position
      return unit.position && 
             unit.position[0] === position[0] && 
             unit.position[1] === position[1];
    });
  };

  // Helper pour trouver une position alternative libre (recherche en spirale avec validation client)
  const findAlternativePosition = (targetPosition: [number, number], fromPosition: [number, number], excludingUnitId?: string): [number, number] | null => {
    // D'abord vérifier si la position cible est libre
    if (!isPositionOccupiedByUnits(targetPosition, excludingUnitId)) {
      return targetPosition;
    }
    
    // Positions déjà testées pour éviter les doublons
    const testedPositions = new Set<string>();
    testedPositions.add(`${targetPosition[0]},${targetPosition[1]}`); // Position cible déjà testée
    
    // Recherche en spirale par rayons croissants
    for (let radius = 1; radius <= 3; radius++) {
      const candidates: [number, number][] = [];
      
      // Générer positions du rayon actuel
      for (let dx = -radius; dx <= radius; dx++) {
        for (let dy = -radius; dy <= radius; dy++) {
          // Inclure seulement les positions sur le périmètre du rayon actuel
          if (Math.abs(dx) === radius || Math.abs(dy) === radius) {
            const newPos: [number, number] = [targetPosition[0] + dx, targetPosition[1] + dy];
            const key = `${newPos[0]},${newPos[1]}`;
            
            // Vérifier limites et éviter doublons
            if (!testedPositions.has(key) && 
                newPos[0] >= 0 && newPos[0] < GRID_SIZE && 
                newPos[1] >= 0 && newPos[1] < GRID_SIZE &&
                !(newPos[0] === fromPosition[0] && newPos[1] === fromPosition[1])) {
              candidates.push(newPos);
              testedPositions.add(key);
            }
          }
        }
      }
      
      // Trier par proximité à la position d'origine pour préférer les positions proches
      candidates.sort((a, b) => {
        const distA = Math.abs(a[0] - fromPosition[0]) + Math.abs(a[1] - fromPosition[1]);
        const distB = Math.abs(b[0] - fromPosition[0]) + Math.abs(b[1] - fromPosition[1]);
        return distA - distB;
      });

      // Tester chaque candidat de ce rayon avec validation client
      for (const candidate of candidates) {
        if (!isPositionOccupiedByUnits(candidate, excludingUnitId)) {
          return candidate;
        }
      }
    }
    
    return null;
  };

  const handleUnitMove = async (unitId: string, fromPosition: [number, number], toPosition: [number, number], retryCount: number = 0): Promise<void> => {
    // 🛡️ VALIDATION PRÉVENTIVE CÔTÉ CLIENT
    if (retryCount === 0) { // Seulement au premier essai pour éviter les boucles
      if (isPositionOccupiedByUnits(toPosition, unitId)) {
        const alternativePosition = findAlternativePosition(toPosition, fromPosition, unitId);
        if (alternativePosition) {
          return await handleUnitMove(unitId, fromPosition, alternativePosition, 1); // Marquer comme retry pour éviter re-validation
        } else {
          return;
        }
      }
    }
    
    const requestBody = {
      battle_id: actualBattleId,
      unit_id: unitId,
      from_position: fromPosition,
      to_position: toPosition
    };

    try {
      // Utiliser l'endpoint battle/move avec validation des collisions
      const response = await fetch(`${getApiUrl()}/api/v2/battle/move`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const result = await response.json();
        
        // Recharger les données depuis le serveur
        await loadBattleUnits();
        
        // Désélectionner l'unité pour éviter les conflits
        setSelectedCompactUnit(null);
        
      } else {
        // Essayer de lire le message d'erreur du serveur
        try {
          const errorData = await response.json();
          console.error('❌ Erreur déplacement:', errorData);
          
          // Si c'est une erreur de collision et qu'on n'a pas encore fait de retry
          if (errorData.error && errorData.error.includes('Position occupée') && retryCount < 3) {
            // Premier retry : recharger les données pour avoir l'état à jour
            if (retryCount === 0) {
              if (loadBattleUnits) {
                await loadBattleUnits();
              }
              // Attendre un peu pour que les données se stabilisent
              await new Promise(resolve => setTimeout(resolve, 200));
            }
            
            const alternativePosition = findAlternativePosition(toPosition, fromPosition, unitId);
            
            if (alternativePosition) {
              // Réessayer avec la position alternative
              return await handleUnitMove(unitId, fromPosition, alternativePosition, retryCount + 1);
            } else {
            }
          }
          
        } catch (e) {
        }
        
        // Ne pas afficher d'alert pour les erreurs de l'IA, juste loguer
        if (retryCount === 0) {
        }
      }
    } catch (error) {
      if (retryCount === 0) {
        alert('❌ Erreur réseau lors du déplacement');
      }
    }
  };

  // Fonction pour terminer le tour et passer au joueur suivant
  const handleEndTurn = async () => {
    if (!actualBattleId) {
      alert('⚠️ Aucune bataille active');
      return;
    }

    try {

      
      const response = await fetch(`${getApiUrl()}/api/v2/battle/end-turn/${actualBattleId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        let result;
        try {
          result = await response.json();
        } catch (parseError) {
          console.error('❌ Erreur parsing JSON de la réponse:', parseError);
          const text = await response.text();
          console.error('🔍 Contenu brut de la réponse:', text);
          alert('⚠️ Erreur de communication avec le serveur. Vérifiez la console pour plus de détails.');
          return;
        }

        // 🏆 VÉRIFIER VICTOIRE AUTOMATIQUE (clic virtuel)
        if (result.victory_detected) {
          
          // 🔍 Déterminer le camp du joueur humain (player_XX vs wild_camp)
          const isPlayerAttacker = result.surrender_result?.surrendering_player?.startsWith('player_') 
            ? result.surrender_result.surrendering_team !== 'attackers' 
            : result.winner_team === 'attackers';
          
          const playerWon = isPlayerAttacker 
            ? result.winner_team === 'attackers' 
            : result.winner_team === 'defenders';
          
          const playerSurrendered = result.surrender_result?.surrendering_player?.startsWith('player_');
          
          // Si c'est une victoire attaquant (défenseur moral=0 ou unités=0) → Pillage automatique
          if (result.winner_team === 'attackers' && result.surrender_result?.success) {
            
            // Message adapté selon la perspective du joueur ET le type de victoire
            let message;
            if (playerWon) {
              if (result.victory_type === 'moral_breakdown') {
                message = `🏆 Victoire par effondrement du moral !\n\nL'ennemi a perdu tout courage.`;
              } else if (result.victory_type === 'elimination') {
                message = `🏆 Victoire par élimination !\n\nToutes les troupes ennemies ont été éliminées.`;
              } else {
                message = `🏆 Victoire ! Vous avez remporté la bataille !`;
              }
            } else if (playerSurrendered) {
              if (result.victory_type === 'moral_breakdown') {
                message = `☠️ Défaite par effondrement du moral !\n\nVos troupes ont perdu tout courage et ont fui le combat.`;
              } else if (result.victory_type === 'elimination') {
                message = `☠️ Défaite par élimination !\n\nVous n'avez pas déployé vos troupes à temps.`;
              } else {
                message = `☠️ Défaite ! Vos troupes ont été vaincues.`;
              }
            } else {
              message = `☠️ Défaite ! Vos troupes ont été vaincues.`;
            }
            
            // Utiliser le message client (pas le message serveur)
            alert(`${message}\n\n✅ Bataille terminée !`);
            
            // Pillage seulement si le joueur humain a gagné
            if (playerWon) {
              try {
                // Importer PillageService
                const { PillageService } = await import('../services/PillageService');
                
                // DEBUG: Voir les données
                
                // Utiliser la même fonction que les boutons
                const victoryResult = await PillageService.detectVictoryFromSurrender(result.surrender_result, actualBattleId);
                
                if (victoryResult.hasVictory && victoryResult.victoryData) {
                  // Demander confirmation comme les boutons
                  if (window.confirm('🏆 Victoire ! Voulez-vous ouvrir le popup de pillage pour collecter les ressources ?\n\n🎁 Vous pourrez choisir quelles ressources prendre.')) {
                    
                    // Émettre l'événement avec les vraies victoryData du service
                    const event = new CustomEvent('openPillagePopup', { 
                      detail: victoryResult.victoryData 
                    });
                    window.dispatchEvent(event);
                  }
                } else {
                }
                
              } catch (error) {
                alert('✅ Victoire ! Le popup de pillage n\'a pas pu s\'ouvrir automatiquement.');
              }
            }
            
          } else if (result.winner_team === 'defenders' && result.surrender_result?.success) {
            // Victoire défenseurs (attaquant se rend, pas de pillage)
            
            // Message adapté selon la perspective du joueur ET le type de victoire
            let message;
            if (playerWon) {
              if (result.victory_type === 'moral_breakdown') {
                message = `🏆 Victoire par effondrement du moral !\n\nL'attaquant a perdu tout courage.`;
              } else if (result.victory_type === 'elimination') {
                message = `🏆 Victoire par élimination !\n\nL'attaquant n'a pas déployé de troupes.`;
              } else {
                message = `🏆 Victoire ! Vous avez défendu avec succès !`;
              }
            } else if (playerSurrendered) {
              if (result.victory_type === 'moral_breakdown') {
                message = `☠️ Défaite par effondrement du moral !\n\nVos troupes ont perdu tout courage et ont fui le combat.`;
              } else if (result.victory_type === 'elimination') {
                message = `☠️ Défaite par élimination !\n\nVotre attaque a échoué - vous n'avez pas déployé vos troupes à temps.`;
              } else {
                message = `☠️ Défaite ! Votre attaque a échoué.`;
              }
            } else {
              message = `☠️ Défaite ! Votre attaque a échoué.`;
            }
            
            // Utiliser le message client (pas le message serveur)
            alert(`${message}\n\n✅ Bataille terminée !`);
          } else if (result.winner_team === 'draw') {
            // Match nul - aucun joueur n'a déployé d'unités
            alert(`⚔️ Match nul !\n\nAucune des deux équipes n'a déployé de troupes.\n\n✅ Bataille terminée !`);
          } else {
            // Message de victoire générique (ne devrait jamais arriver)
            const victoryMessage = result.message || `🏆 Victoire ${result.winner_team} !`;
            alert(victoryMessage);
          }
          
          // Recharger complètement l'état après victoire
          await syncBattleStateFromServer();
          await loadBattleUnits();
          await loadBattlefieldStats();
          
          return; // Sortir ici, pas besoin du reste
        }

        // Cas normal (pas de victoire) : comportement habituel
        // Synchroniser l'état depuis le serveur pour être sûr
        await syncBattleStateFromServer();
        
        // Recharger les données
        await loadBattleUnits();
        
        // Recharger les stats pour mettre à jour le moral dans l'interface
        // NOUVEAU : Délai pour laisser le serveur traiter le moral
        setTimeout(async () => {
          await loadBattlefieldStats();
        }, 500);  // 500ms de délai
        
        // Suppression de l'alert de confirmation fin de tour

      } else {
        const errorData = await response.json();
        alert(`❌ Erreur fin de tour: ${errorData.error}`);
      }
    } catch (error) {
      console.error('❌ Erreur lors de la fin de tour:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erreur inconnue';
      alert(`❌ Erreur réseau lors de la fin de tour: ${errorMessage}`);
    }
  };

  // Fonction pour démarrer la bataille (passer de deployment à battle)
  const handleStartBattle = async () => {
    if (!actualBattleId) {
      alert('⚠️ Aucune bataille active');
      return;
    }

    try {

      
      const response = await fetch(`${getApiUrl()}/api/v2/battle/start/${actualBattleId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const result = await response.json();
        
        console.log('🚀 [START BATTLE] Résultat:', result);
        
        // Passer en phase battle
        setLocalGamePhase('battle');
        
        // Mettre à jour les rounds (devrait être 2)
        setCurrentRound(result.current_round || 2);
        setRoundCurrentPlayer(result.current_player);
        
        console.log(`🚀 [START BATTLE] Round mis à jour: ${result.current_round}`);
        
        // Recharger les données
        await loadBattleUnits();
        
        // Suppression de l'alert de confirmation démarrage bataille
      } else {
        const errorData = await response.json();
        alert(`❌ Erreur démarrage: ${errorData.error}`);
      }
    } catch (error) {
      alert('❌ Erreur réseau lors du démarrage de bataille');
    }
  };

  // Fonction pour synchroniser l'état de bataille depuis le serveur
  const syncBattleStateFromServer = async () => {
    if (!actualBattleId) {
      return;
    }
    
    try {
      const response = await fetch(`${getApiUrl()}/api/v2/battle/status/${actualBattleId}`);
      
      if (response.ok) {
        const result = await response.json();
        
        // Synchroniser l'état local avec le serveur
        setCurrentRound(result.current_round || 1);
        setRoundCurrentPlayer(result.current_player);
      } else {
      }
    } catch (error) {
    }
  };

  // 🤖 Fonction de déploiement automatique (toutes les unités)
  const handleAutoDeployment = async (endTurnFunc: () => Promise<void>) => {
    try {
      // Importer le service de déploiement
      const { SimpleDeploymentService } = await import('../services/SimpleDeploymentService');
      const deploymentService = new SimpleDeploymentService();
      
      // 1️⃣ Charger les données du battlefield
      const battlefieldsResponse = await fetch(`${getApiUrl()}/data/battlefields_v2.json`);
      const battlefieldsData = await battlefieldsResponse.json();
      const battlefield = battlefieldsData[actualBattleId];
      
      if (!battlefield) return;
      
      // Récupérer le template_id du battlefield
      const templateId = battlefield.template_id || 'simple_plains_10x10';
      
      // 2️⃣ Charger battlesv2.json pour vérifier qui a déjà déployé
      const battlesResponse = await fetch(`${getApiUrl()}/api/v2/battles/data`);
      const battlesData = await battlesResponse.json();
      const battleData = battlesData[actualBattleId];
      
      if (!battleData) return;
      
      // Déterminer qui doit déployer en fonction des unités dans teams
      const attackers = battlefield.participants?.attackers || [];
      const defenders = battlefield.participants?.defenders || [];
      
      let currentPlayerId = null;
      let currentTeam: 'attacker' | 'defender' = 'attacker';
      
      // Vérifier si l'attaquant a des unités déployées dans teams
      let attackerHasDeployed = false;
      const teams = battleData.teams || {};
      
      for (const teamKey in teams) {
        const teamUnits = teams[teamKey];
        if (Array.isArray(teamUnits) && teamUnits.length > 0) {
          // Vérifier si c'est un attaquant
          for (const attackerId of attackers) {
            if (teamKey.includes(attackerId) || teamKey.includes('attacker')) {
              attackerHasDeployed = true;
              break;
            }
          }
        }
        if (attackerHasDeployed) break;
      }
      
      if (!attackerHasDeployed) {
        // L'attaquant n'a pas encore déployé
        currentPlayerId = attackers[0];
        currentTeam = 'attacker';
      } else {
        // L'attaquant a déployé, vérifier le défenseur
        let defenderHasDeployed = false;
        
        for (const teamKey in teams) {
          const teamUnits = teams[teamKey];
          if (Array.isArray(teamUnits) && teamUnits.length > 0) {
            // Vérifier si c'est un défenseur
            for (const defenderId of defenders) {
              if (teamKey.includes(defenderId) || teamKey.includes('defender')) {
                defenderHasDeployed = true;
                break;
              }
            }
          }
          if (defenderHasDeployed) break;
        }
        
        if (!defenderHasDeployed) {
          // Le défenseur doit déployer
          currentPlayerId = defenders[0];
          currentTeam = 'defender';
        } else {
          // Tout le monde a déployé, on skip (le round va passer automatiquement)
          return;
        }
      }
      
      if (!currentPlayerId) return;
      
      // 3️⃣ Récupérer les unit_counts
      const unitCountsResponse = await fetch(`${getApiUrl()}/api/v2/battle/${actualBattleId}/unit-counts`);
      if (!unitCountsResponse.ok) return;
      
      const unitCountsData = await unitCountsResponse.json();
      if (!unitCountsData.success || !unitCountsData.available_units) return;
      
      // 4️⃣ Déployer SEULEMENT le joueur actuel
      await deployPlayerUnits(currentPlayerId, currentTeam, unitCountsData.available_units, deploymentService, templateId);
      
      // 5️⃣ Attendre que les données se mettent à jour sur le serveur
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // 6️⃣ Toujours appeler endTurn, que ce soit attacker ou defender
      await endTurnFunc();
      
    } catch (error) {
      console.error('❌ [AUTO-DEPLOY] Erreur:', error);
    }
  };
  
  // Fonction helper pour déployer les unités d'un joueur
  const deployPlayerUnits = async (
    playerId: string, 
    team: 'attacker' | 'defender', 
    availableUnits: any,
    deploymentService: any,
    templateId: string
  ) => {
    const playerUnits = availableUnits[playerId];
    if (!playerUnits) {
      return;
    }
    
    // Séparer les héros des unités normales
    const units: { [unitType: string]: number } = {};
    const heroesCount = playerUnits.heroes?.available || 0;
    
    Object.entries(playerUnits).forEach(([unitType, counts]: [string, any]) => {
      if (unitType !== 'heroes' && counts.available > 0) {
        units[unitType] = counts.available;
      }
    });
    
    if (Object.keys(units).length === 0 && heroesCount === 0) {
      return;
    }

    // Charger le battlefield pour récupérer le map ID
    const battlefieldResponse = await fetch(`${getApiUrl()}/api/v2/battlefields/data`);
    const battlefieldsData = await battlefieldResponse.json();
    const battlefield = battlefieldsData[actualBattleId];
    
    if (!battlefield || !battlefield.map) return;
    
    // Charger la map pour avoir les deploymentZones
    const mapResponse = await fetch(`${getApiUrl()}/data/battlefields/${battlefield.map}.json`);
    const mapData = await mapResponse.json();
    
    // Utiliser deploymentZones (format: {attacker: {infantry: [[q,r]], ranged: [[q,r]]}, defender: {...}})
    const deploymentZones = mapData.template?.deploymentZones || mapData.deploymentZones;
    if (!deploymentZones) return;
    
    const teamZone = team === 'attacker' ? deploymentZones.attacker : deploymentZones.defender;
    if (!teamZone) return;
    
    // Consolider toutes les hexes de toutes les catégories (infantry, ranged, cavalry)
    const validHexes: any[] = [];
    Object.values(teamZone).forEach((categoryHexes: any) => {
      if (Array.isArray(categoryHexes)) {
        categoryHexes.forEach(([q, r]) => {
          validHexes.push({ q, r });
        });
      }
    });
    
    if (validHexes.length === 0) return;
    
    // Créer les UnitGroup
    const deployedUnits: any[] = [];
    let hexIndex = 0;
    
    // Déployer les unités normales
    Object.entries(units).forEach(([unitType, count], index) => {
      if (count > 0) {
        const hex = validHexes[hexIndex % validHexes.length];
        deployedUnits.push({
          id: `auto_${team}_${playerId}_${unitType}_${index}`,
          type: unitType,
          count: count,
          team: team,
          deployedPosition: { q: hex.q, r: hex.r },
          isHero: false
        });
        hexIndex++;
      }
    });
    
    // Déployer les héros s'il y en a
    if (heroesCount > 0) {
      try {
        // Récupérer les héros du joueur depuis battlefields_v2
        const heroIds = battlefield.forces[team === 'attacker' ? 'attackers' : 'defenders'][playerId]?.contributions
          ?.flatMap((c: any) => c.heroes || []) || [];
        
        for (let i = 0; i < Math.min(heroesCount, heroIds.length); i++) {
          const hex = validHexes[hexIndex % validHexes.length];
          deployedUnits.push({
            id: `auto_${team}_${playerId}_hero_${heroIds[i]}`,
            type: 'hero',
            count: 1,
            team: team,
            deployedPosition: { q: hex.q, r: hex.r },
            isHero: true,
            heroId: heroIds[i]
          });
          hexIndex++;
        }
      } catch (error) {
        console.error('[AUTO-DEPLOY] Erreur déploiement héros:', error);
      }
    }
    
    // Sauvegarder
    await deploymentService.saveDeployedPositions(actualBattleId, deployedUnits, team, currentRound);
  };

  const handleUnitMove_OLD = async (unitId: string, fromPosition: [number, number], toPosition: [number, number]) => {
    try {
      
      const requestBody = {
        unit_id: unitId,
        position: toPosition
      };
      
      const response = await fetch(`${getApiUrl()}/api/v2/battle/${actualBattleId}/move_unit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const result = await response.json();
        
        // Simple : recharger les données depuis le serveur
        await loadBattleUnits();
        
        // Désélectionner l'unité pour éviter les conflits
        setSelectedCompactUnit(null);
        
      } else {
        // Essayer de lire le message d'erreur du serveur
        try {
          const errorData = await response.json();
        } catch (e) {
        }
        alert('❌ Erreur lors du déplacement de l\'unité');
      }
    } catch (error) {
      alert('❌ Erreur réseau lors du déplacement');
    }
  };

  const handleEndBattleV2 = async () => {
    
    if (!actualBattleId) {
      alert('⚠️ Aucune bataille active trouvée');
      return;
    }

    if (!window.confirm('🏁 Voulez-vous vraiment terminer cette bataille ?\n\n✅ Toutes les troupes seront renvoyées vers leurs villes d\'origine\n✅ Un rapport de bataille sera créé\n✅ La bataille sera supprimée')) {
      return;
    }

    try {
      
      const response = await fetch(`${getApiUrl()}/api/v2/battle/end/${actualBattleId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      const result = await response.json();

      if (result.success) {
        
        // Calculer le nombre total d'unités renvoyées avec vérifications de sécurité
        let totalUnitsReturned = 0;
        let playersAffected = 0;
        
        if (result.troops_returned && typeof result.troops_returned === 'object') {
          playersAffected = Object.keys(result.troops_returned).length;
          totalUnitsReturned = Object.values(result.troops_returned).reduce((total: number, troopData: any) => {
            if (troopData?.units && typeof troopData.units === 'object') {
              return total + Object.values(troopData.units).reduce((sum: number, count: any) => sum + (Number(count) || 0), 0);
            }
            return total;
          }, 0);
        }
        
        alert(`✅ Bataille terminée avec succès !\n\n📋 Rapport: ${result.report_id || 'N/A'}\n🏠 ${totalUnitsReturned} unités renvoyées vers ${result.cities_updated || 0} villes\n👥 ${playersAffected} joueurs concernés`);
        
        // Changer le phase de jeu vers victoire
        setLocalGamePhase('victory');
        
      } else {
        alert(`❌ Erreur lors de la fin de bataille:\n${result.error}`);
      }
    } catch (error) {
      alert('❌ Erreur de connexion lors de la fin de bataille');
    }
  };

  // ========== VALEURS DE RETOUR ==========
  return {
    // États
    localGamePhase,
    setLocalGamePhase,
    selectedHex,
    setSelectedHex,
    selectedUnit,
    setSelectedUnit,
    selectedCompactUnit,
    setSelectedCompactUnit,
    hoveredHex,
    setHoveredHex,
    showUnitPanel,
    setShowUnitPanel,
    battleGrid,
    battleUnits,
    battleData,
    actualBattleId,
    currentRound,
    currentTurnPlayer: roundCurrentPlayer,
    setCurrentTurnPlayer: setRoundCurrentPlayer,  // Exposer le setter pour mise à jour
    currentBattlefield,
    attackerStats,
    defenderStats,
    deploymentPopupOpen,
    setDeploymentPopupOpen,
    selectedTeam,
    // unitsInHeroAura et getHeroAuraForUnitSync maintenant dans BattlefieldVisualsV2

    // Système de drag
    isDragging,
    viewOffset,
    setViewOffset,

    // Gestionnaires d'événements
    handleOpenDeploymentPopup,
    handleDeployUnit,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    handleHexClick,
    handleUnitMove,
    handleEndBattleV2,
    handleAutoDeployment,  // 🤖 Déploiement automatique


    // Ajout d'un objet participants compatible avec le composant
    battleParticipants: (() => {
      // Utiliser currentBattlefield si disponible
      if (currentBattlefield && currentBattlefield.participants) {
        const attackerId = currentBattlefield.participants.attackers?.[0];
        const defenderId = currentBattlefield.participants.defenders?.[0];
        if (attackerId && defenderId) {
          return {
            attacker_id: attackerId,
            attacker_name: `Attaquant (${attackerId})`,
            defender_id: defenderId,
            defender_name: `Défenseur (${defenderId})`,
          };
        }
      }
      
      // Chercher les participants dans les forces du currentBattlefield 
      if (currentBattlefield && currentBattlefield.forces) {
        const attackersData = currentBattlefield.forces.attackers || {};
        const defendersData = currentBattlefield.forces.defenders || {};
        const attackerId = Object.keys(attackersData)[0];
        const defenderId = Object.keys(defendersData)[0];
        if (attackerId && defenderId) {
          return {
            attacker_id: attackerId,
            attacker_name: `Attaquant (${attackerId})`,
            defender_id: defenderId,
            defender_name: `Défenseur (${defenderId})`,
          };
        }
      }
      return {
        attacker_id: 'unknown_attacker',
        attacker_name: 'Attaquant (inconnu)',
        defender_id: 'unknown_defender',
        defender_name: 'Défenseur (inconnu)',
      };
    })(),

    // Adaptateur pour SimpleBattlefieldV2 : (unitId, newPosition) => void
    onUnitMove: (unitId: string, newPosition: [number, number]) => {
      // Trouver la position actuelle de l'unité (essayer plusieurs formats d'ID)
      let unit = battleUnits.find(u => u.unitId === unitId);
      if (!unit) {
        unit = battleUnits.find(u => u.id === unitId);
      }
      
      const fromPosition = unit?.position || [0, 0]; // Par défaut [0,0] si pas trouvé
      
      // Debug pour identifier le problème
      if (!unit) {
      } else {
      }
      
      // Appeler la vraie fonction asynchrone
      handleUnitMove(unitId, fromPosition, newPosition);
    },
    endTurn: handleEndTurn,
    startBattle: handleStartBattle,
    syncBattleState: syncBattleStateFromServer,

    // Utilitaires
    actualGamePhase: localGamePhase,
    targetCityId,
    battlefieldTemplateId,
    backgroundImage,  // 🖼️ Image de fond depuis le template
    
    // Fonctions de mise à jour de la grille
    updateBattleGrid: setBattleGrid,
    loadBattleUnits: loadBattleUnits,

    // 🧱 NOUVELLES FONCTIONS POUR LES MURS
    wallInteractionPopupOpen,
    setWallInteractionPopupOpen,
    selectedWallPosition,
    setSelectedWallPosition,
    
    // Fonction pour récupérer le groupe de mur à une position
    getWallGroupAtPosition: (position: {q: number, r: number}) => {
      if (!dataState.battleData?.wall_system?.wall_groups) {
        return null;
      }
      
      const wallGroups = dataState.battleData.wall_system.wall_groups;
      
      for (const [groupKey, groupData] of Object.entries(wallGroups)) {
        const positions = (groupData as any).positions || [];
        // Vérifier si la position existe dans ce groupe
        // Backend: [row, col], Frontend: {q: col, r: row}
        const positionExists = positions.some((pos: [number, number]) => 
          pos[1] === position.q && pos[0] === position.r
        );
        if (positionExists) {
          return { key: groupKey, ...(groupData as any) };
        }
      }
      return null;
    },
    
    // Fonction pour récupérer les stats des murs
    getWallStats: () => {
      return battleData?.wall_system?.wall_stats || null;
    },
    
    // Fonction pour attaquer un groupe de murs
    attackWallGroup: async (groupIndex: number, damage: number) => {
      try {
        if (!actualBattleId) {
          throw new Error('Aucune bataille active');
        }

        const response = await fetch(`${getApiUrl()}/api/wall/attack`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            battle_id: actualBattleId,
            group_index: groupIndex,
            damage: damage,
            attacker_unit_id: roundCurrentPlayer || 'player_1'
          }),
        });

        if (!response.ok) {
          throw new Error(`Erreur HTTP: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.success) {
          // Recharger les données de bataille pour mettre à jour l'affichage
          await loadBattlefieldData();
          await loadBattleUnits();
          
          if (result.destroyed) {
            alert(`🧱 Groupe de murs ${groupIndex + 1} détruit ! Le passage est maintenant libre.`);
          } else {
            alert(`🧱 Dégâts infligés: ${result.damage_dealt}. HP restants: ${result.remaining_hp}/${result.max_hp}`);
          }
        } else {
          throw new Error(result.error || 'Erreur lors de l\'attaque des murs');
        }

        // Fermer le popup
        setWallInteractionPopupOpen(false);
        setSelectedWallPosition(null);
      } catch (error) {
        alert(`❌ Erreur lors de l'attaque des murs: ${error}`);
      }
    }
  };
};
