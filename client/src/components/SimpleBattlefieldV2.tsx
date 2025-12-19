
/**
 * SimpleBattlefieldV2.tsx
 * Composant principal pour l'affichage et l'interaction avec le champ de bataille
 */
import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useBattlefieldLogic } from '../hooks/useBattlefieldLogic';
import UnitDeploymentPopupV2 from './UnitDeploymentPopupV2';
import UnitInfoPopup from './UnitInfoPopup';
import { extractUnitType } from '../utils/combatUtils';
import { getApiUrl } from '../utils/api';
import CombatPopup from './CombatPopup';
import WallInteractionPopup from '../popups/WallInteractionPopup';
import { BattlefieldVisualsV2 } from './BattlefieldVisualsV2';
import BattlefieldTacticsV2 from './BattlefieldTacticsV2';
import PillagePopup from '../popups/PillagePopup';
import { PillageService, VictoryData } from '../services/PillageService';
import { UnifiedBattleLoaderService } from '../services/UnifiedBattleLoaderService';
import AIDebugPopup from '../popups/AIDebugPopup';
import { useWallCombat } from '../hooks/useWallCombat';
import { CompactUnit } from '../types/index';
import { useUser } from '../hooks/useUser';
import CombatTutorialPopup from '../popups/CombatTutorialPopup';
import './SimpleBattlefieldV2.css';

interface SimpleBattlefieldV2Props {
  onUnitSelect?: (unit: any | null) => void;
  onHexSelect?: (hex: any) => void;
  gamePhase: 'deployment' | 'battle' | 'victory';
  currentPlayer: 'attacker' | 'defender';
  attackerUnits?: { [unitType: string]: number };
  defenderUnits?: { [unitType: string]: number };
  targetCityId?: string;
  battleId?: string;
  initialRound?: number;
  initialCurrentPlayer?: string;
  onRoundChange?: (round: number, player: string) => void;
  onStatsChange?: (attackerStats: { units: number, moral: number }, defenderStats: { units: number, moral: number }) => void;
  battlefieldTemplateId?: string;
  onClose?: () => void;
}

const SimpleBattlefieldV2: React.FC<SimpleBattlefieldV2Props> = (props) => {
  const { user } = useUser();

  const handleReturnJourneyAll = async () => {
    try {
      // 1. Lancer le voyage retour (qui maintenant fait tout : unités + rapport + suppression)
      await UnifiedBattleLoaderService.returnAllTransports(props.battleId || '');
      
      setTimeout(() => {
        if (props.onClose) {
          props.onClose();
        }
      }, 500);
    } catch (error) {
      // Fermer quand même en cas d'erreur
      if (props.onClose) {
        props.onClose();
      }
    }
  };

  // Système de zoom molette simplifié
  const [zoomLevel, setZoomLevel] = useState(1);
  const MIN_ZOOM = 0.5;
  const MAX_ZOOM = 3;
  
  const [turnTimeRemaining, setTurnTimeRemaining] = useState<number | null>(null);
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const endTurnCalledRef = useRef(false);  // Flag pour éviter les appels multiples
  const autoDeployTriggeredRef = useRef(false);  // Flag pour éviter le déploiement auto multiple
  
  const handleWheelZoom = useCallback((event: React.WheelEvent) => {
    event.preventDefault();
    event.stopPropagation();
    
    const zoomDelta = event.deltaY > 0 ? -0.1 : 0.1;
    setZoomLevel(prevZoom => {
      const newZoom = prevZoom + zoomDelta;
      return Math.min(Math.max(newZoom, MIN_ZOOM), MAX_ZOOM);
    });
  }, []);

  const {
    // États
    localGamePhase,
    setLocalGamePhase,
    selectedHex,
    selectedUnit,
    setSelectedUnit,
    selectedCompactUnit,
    setSelectedCompactUnit,
    showUnitPanel,
    setShowUnitPanel,
    battleGrid,
    battleUnits,
    battleData,
    actualBattleId,
    currentRound,
    currentTurnPlayer,
    setCurrentTurnPlayer,  // Pour mettre à jour depuis le timer
    currentBattlefield,
    battleParticipants,
    attackerStats,
    defenderStats,
    deploymentPopupOpen,
    setDeploymentPopupOpen,
    selectedTeam,
    wallInteractionPopupOpen,
    setWallInteractionPopupOpen,
    selectedWallPosition,
    setSelectedWallPosition,
    getWallGroupAtPosition,
    getWallStats,
    attackWallGroup,
    
    // unitsInHeroAura et getHeroAuraForUnitSync maintenant gérés dans BattlefieldVisualsV2

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
    endTurn,
    startBattle,
    onUnitMove,
    handleAutoDeployment,  // 🤖 Déploiement automatique

    // Utilitaires
    actualGamePhase,
    targetCityId,
    battlefieldTemplateId,
    backgroundImage,  // 🖼️ Image de fond
    updateBattleGrid,
    loadBattleUnits
  } = useBattlefieldLogic(props);

  // Fonction d'aura héros
  const [heroAuraFunction, setHeroAuraFunction] = useState<((unit: any, position: { q: number; r: number }) => any) | null>(null);
  
  // État pour les attaques
  const [attackRequestData, setAttackRequestData] = useState<{attacker: CompactUnit, defender: CompactUnit} | null>(null);
  
  // État local pour tracker les unités ayant attaqué (indépendant de battleUnits)
  const [unitsAttackedThisTurn, setUnitsAttackedThisTurn] = useState<Set<string>>(new Set());
  
  // États pour le popup d'informations d'unité
  const [unitInfoPopupOpen, setUnitInfoPopupOpen] = useState(false);
  const [selectedUnitForInfo, setSelectedUnitForInfo] = useState<any | null>(null);
  const [unitStats, setUnitStats] = useState<any>(null);
  
  // États pour le popup combat
  const [combatPopupOpen, setCombatPopupOpen] = useState(false);
  
  // États pour le popup de pillage
  const [pillagePopupOpen, setPillagePopupOpen] = useState(false);
  const [victoryData, setVictoryData] = useState<VictoryData | null>(null);
  const [aiDebugOpen, setAiDebugOpen] = useState(false);
  const [tutorialOpen, setTutorialOpen] = useState(false);
  

  
  const [combatData, setCombatData] = useState<{
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

  // État pour gérer l'attente de confirmation de combat IA
  const [waitingForAICombatConfirm, setWaitingForAICombatConfirm] = useState(false);
  const [aiCombatResolver, setAiCombatResolver] = useState<((value?: any) => void) | null>(null);
  
  // Remettre à zéro les attaques au changement de tour
  useEffect(() => {
    setUnitsAttackedThisTurn(new Set());
    endTurnCalledRef.current = false;  // Réinitialiser le flag à chaque changement de tour
    autoDeployTriggeredRef.current = false;  // Réinitialiser le flag de déploiement auto
  }, [currentRound, currentTurnPlayer]);

  // ⏱️ Timer automatique de 20 secondes pour avancer le tour
  useEffect(() => {

    // Démarrer le timer en phase deployment OU battle
    if ((actualGamePhase !== 'battle' && actualGamePhase !== 'deployment') || !actualBattleId) {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
        timerIntervalRef.current = null;
      }
      // Ne PAS réinitialiser le timer à 20s, garder la valeur actuelle
      return;
    }



    // Fonction pour récupérer le temps restant depuis le serveur
    const fetchTurnTimer = async () => {
      try {
        const url = `${getApiUrl()}/api/v2/battle/turn-timer/${actualBattleId}`;
        
        const response = await fetch(url);
        
        // 🚨 NOUVEAU : Détecter si la battlefield n'existe plus (404)
        if (response.status === 404) {
          if (timerIntervalRef.current) {
            clearInterval(timerIntervalRef.current);
            timerIntervalRef.current = null;
          }
          
          // Afficher un message immédiat
          alert('⚔️ La bataille est terminée !\n\nVous pouvez maintenant fermer cette fenêtre.');
          return;
        }
        
        if (response.ok) {
          const text = await response.text();
          
          try {
            const data = JSON.parse(text);
            
            // ⚠️ PRIORITAIRE: Vérifier si la bataille est terminée (côté serveur)
            if (data.is_battle_completed || data.battle_ended) {
              if (timerIntervalRef.current) {
                clearInterval(timerIntervalRef.current);
                timerIntervalRef.current = null;
              }
              return;
            }
            
            if (data.success) {
              // ⏸️ Si timer en pause, afficher 999 et ne pas déclencher l'auto-pass
              if (data.is_paused || data.timer_paused) {
                setTurnTimeRemaining(999);
                return; // Arrêter ici, pas d'auto-pass
              }
              
              const remaining = Math.max(0, Math.ceil(data.remaining_seconds));
              setTurnTimeRemaining(remaining);
              
              // ✅ Mettre à jour le current_player depuis le timer
              if (data.current_player && data.current_player !== currentTurnPlayer) {
                setCurrentTurnPlayer(data.current_player);
              }
              
              // ⏰ TEMPS ÉCOULÉ → Action automatique puis passage au tour suivant
              if (data.is_expired || remaining <= 0) {
                
                // Empêcher les appels multiples
                if (endTurnCalledRef.current) {
                  return;
                }
                
                endTurnCalledRef.current = true;
                
                // 🛡️ SÉCURITÉ : Réinitialiser le flag après 5 secondes pour éviter les deadlocks
                setTimeout(() => {
                  endTurnCalledRef.current = false;
                }, 5000);
                
                // 🤖 ACTION AUTOMATIQUE selon la phase
                const hasNoUnitsDeployed = (battleUnits?.length || 0) === 0;
                
                // DEPLOYMENT uniquement si Round 1 ET phase deployment
                if (currentRound === 1 && actualGamePhase === 'deployment' && hasNoUnitsDeployed) {
                  // Phase déploiement : déployer automatiquement
                  await handleAutoDeployment(endTurn);
                  
                  if (loadBattleUnits) {
                    await loadBattleUnits();
                  }
                  
                  // Petit délai pour laisser React re-render
                  await new Promise(resolve => setTimeout(resolve, 500));
                  
                  // NE PAS appeler endTurn() ici, laisser le timer continuer pour le prochain joueur
                  endTurnCalledRef.current = false; // Réinitialiser pour le prochain tour
                } else {
                  // Phase combat : passer le tour
                  endTurn();
                  
                  setTimeout(async () => {
                    if (loadBattleUnits) {
                      await loadBattleUnits();
                    }
                    // Réinitialiser le flag
                    endTurnCalledRef.current = false;
                  }, 800);
                }
              }
            }
          } catch (parseError) {
            endTurnCalledRef.current = false;
          }
        }
      } catch (error) {
        endTurnCalledRef.current = false;
      }
    };

    fetchTurnTimer();

    timerIntervalRef.current = setInterval(fetchTurnTimer, 1000);

    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
        timerIntervalRef.current = null;
      }
    };
  }, [actualGamePhase, actualBattleId, pillagePopupOpen]);

  const { handleWallCombatPopup, handleWallDamage } = useWallCombat({
    selectedCompactUnit,
    battleUnits,
    setCombatData,
    setCombatPopupOpen,
    attackWallGroup,
    actualBattleId,
    unitStats
  });
  
  // Fonction stable pour éviter la boucle infinie dans useEffect
  const onHeroAuraReady = useCallback((getHeroAuraFn: any) => {
    setHeroAuraFunction(() => getHeroAuraFn);
  }, []);
  
  // Écouter l'événement d'ouverture automatique du popup de pillage
  useEffect(() => {
    const handleOpenPillagePopup = (event: CustomEvent) => {
      setVictoryData(event.detail);
      setPillagePopupOpen(true);
    };

    window.addEventListener('openPillagePopup', handleOpenPillagePopup as any);

    return () => {
      window.removeEventListener('openPillagePopup', handleOpenPillagePopup as any);
    };
  }, []);
  
  // Charger les stats d'unités une seule fois au démarrage
  useEffect(() => {
    const loadUnitStats = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/v2/unit_stats`);
        if (response.ok) {
          const data = await response.json();
          setUnitStats(data);
        }
      } catch (error) {
        // Erreur silencieuse pour les stats d'unités
      }
    };
    
    loadUnitStats();
  }, []);
  
  // Fonction pour gérer les demandes d'attaque
  const handleAttackRequest = useCallback((attacker: CompactUnit, defender: CompactUnit, isAIAction?: boolean): Promise<void> => {
    return new Promise((resolve) => {
      // Vérifier si l'unité a déjà attaqué ce tour
      if (unitsAttackedThisTurn.has(attacker.unitId)) {
        resolve(); // Refuser l'attaque silencieusement
        return;
      }
      
      if (isAIAction) {
        // Mode IA : configurer l'attente de confirmation
        setWaitingForAICombatConfirm(true);
        setAiCombatResolver(() => resolve);
      }
      setAttackRequestData({ attacker, defender });
    });
  }, [unitsAttackedThisTurn]);

  // Fonction pour récupérer le terrain réel d'une position
  const getTerrainAtPosition = useCallback((position: [number, number]): string => {
    if (!battleGrid || battleGrid.length === 0) {
      return 'plains'; // Fallback par défaut
    }
    
    const [q, r] = position;
    const hexCell = battleGrid.find(cell => cell.q === q && cell.r === r);
    
    if (hexCell && hexCell.terrain) {
      return hexCell.terrain;
    }
    
    return 'plains';
  }, [battleGrid]);

  const [touchState, setTouchState] = useState({
    isZooming: false,
    isPanning: false,
    lastTouchX: 0,
    lastTouchY: 0,
    initialDistance: 0,
    initialZoom: 1
  });

  const getTouchDistance = (touches: React.TouchList) => {
    if (touches.length < 2) return 0;
    const touch1 = touches[0];
    const touch2 = touches[1];
    return Math.sqrt(
      Math.pow(touch2.clientX - touch1.clientX, 2) + 
      Math.pow(touch2.clientY - touch1.clientY, 2)
    );
  };

  const handleTouchStart = useCallback((event: React.TouchEvent) => {
    if (event.touches.length === 2) {
      // Zoom avec 2 doigts
      const distance = getTouchDistance(event.touches);
      setTouchState({
        isZooming: true,
        isPanning: false,
        lastTouchX: 0,
        lastTouchY: 0,
        initialDistance: distance,
        initialZoom: zoomLevel
      });
    } else if (event.touches.length === 1) {
      // Pan avec 1 doigt
      const touch = event.touches[0];
      setTouchState({
        isZooming: false,
        isPanning: true,
        lastTouchX: touch.clientX,
        lastTouchY: touch.clientY,
        initialDistance: 0,
        initialZoom: zoomLevel
      });
    }
  }, [zoomLevel]);

  const handleTouchMove = useCallback((event: React.TouchEvent) => {
    if (touchState.isZooming && event.touches.length === 2) {
      // Zoom avec 2 doigts
      event.preventDefault();
      
      const currentDistance = getTouchDistance(event.touches);
      if (touchState.initialDistance > 0) {
        const ratio = currentDistance / touchState.initialDistance;
        const newZoom = Math.min(Math.max(touchState.initialZoom * ratio, MIN_ZOOM), MAX_ZOOM);
        setZoomLevel(newZoom);
      }
      
    } else if (touchState.isPanning && event.touches.length === 1) {
      // Pan avec 1 doigt
      event.preventDefault();
      
      const touch = event.touches[0];
      const deltaX = touch.clientX - touchState.lastTouchX;
      const deltaY = touch.clientY - touchState.lastTouchY;
      
      if (Math.abs(deltaX) > 0 || Math.abs(deltaY) > 0) {
        // Calculer et appliquer le nouvel offset
        const newViewOffset = { 
          x: viewOffset.x + deltaX, 
          y: viewOffset.y + deltaY 
        };
        setViewOffset(newViewOffset);
        
        // Mettre à jour la position tactile
        setTouchState(prev => ({
          ...prev,
          lastTouchX: touch.clientX,
          lastTouchY: touch.clientY
        }));
      }
    }
  }, [touchState, setViewOffset, viewOffset, MIN_ZOOM, MAX_ZOOM]);

  const handleTouchEnd = useCallback((event: React.TouchEvent) => {
    if (event.touches.length === 0) {
      // Plus de touches, tout arrêter
      setTouchState({
        isZooming: false,
        isPanning: false,
        lastTouchX: 0,
        lastTouchY: 0,
        initialDistance: 0,
        initialZoom: 1
      });
    } else if (event.touches.length === 1 && touchState.isZooming) {
      // Passage de 2 doigts à 1 doigt = arrêter zoom, commencer pan
      const touch = event.touches[0];
      setTouchState({
        isZooming: false,
        isPanning: true,
        lastTouchX: touch.clientX,
        lastTouchY: touch.clientY,
        initialDistance: 0,
        initialZoom: zoomLevel
      });
    }
  }, [touchState.isZooming, zoomLevel]);

  useEffect(() => {
    const handleResize = () => {
      const vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty('--vh', `${vh}px`);
      
      const container = document.querySelector('.battlefield-mobile-container');
      if (container) {
        const topbarHeight = 56;
        const bottombarHeight = 40;
        const mobileNavHeight = 60;
        const availableHeight = window.innerHeight - topbarHeight - bottombarHeight - mobileNavHeight;
        (container as HTMLElement).style.height = `${Math.max(200, availableHeight)}px`;
      }
    };

    handleResize();
    
    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleResize);
    
    const delayedResize = () => {
      setTimeout(handleResize, 300);
    };
    window.addEventListener('orientationchange', delayedResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleResize);
      window.removeEventListener('orientationchange', delayedResize);
    };
  }, []);

  // Fonction pour confirmer un combat
  const handleConfirmCombat = async (result: any) => {
    if (!combatData.attacker || !combatData.defenderStats || !actualBattleId) {
      return;
    }

    try {
      // Cas spécial : attaque d'un mur
      if (combatData.defenderStats.isWall) {
        const success = await handleWallDamage(result, combatData.defenderStats);
        if (success) {
          // Enregistrer l'action dans l'historique de bataille
          const damageAmount = result.damage;
          const wallCombatAction = {
            battlefield_id: actualBattleId,
            unit_id: combatData.attacker.unitId,
            round: currentRound,
            action: {
              type: 'attack_wall',
              wall_group_id: `wall_group_${combatData.defenderStats.wallGroup.group_index}`,
              damage_dealt: damageAmount,
              wall_hp_before: combatData.defenderStats.wallGroup.hp,
              wall_hp_after: Math.max(0, combatData.defenderStats.wallGroup.hp - damageAmount),
              destroyed: (combatData.defenderStats.wallGroup.hp - damageAmount) <= 0,
            }
          };

          fetch(`${getApiUrl()}/api/v2/battle/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(wallCombatAction)
          });
        }
        setCombatPopupOpen(false);
        return;
      }

      // Combat normal entre unités
      if (!combatData.defender) {
        return;
      }

      // Calculer le nombre d'unités tuées
      const previousCount = combatData.defender?.unitCount || result.survivingUnits + (result.survivingUnits > 0 ? 2 : result.survivingUnits);
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
          previous_count: combatData.defender?.unitCount
        },
        target_new_state: {
          position: combatData.defender.position,
          hp: result.isDefenderHero ? result.remainingHP : undefined,
          count: result.isDefenderHero ? undefined : result.survivingUnits,
          status: result.survivingUnits > 0 ? 'active' : 'eliminated'
        }
      };

      // Envoyer à l'API de bataille V2
      const response = await fetch(`${getApiUrl()}/api/v2/battle/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(combatAction)
      });

      if (response.ok) {
        const responseData = await response.json();
        
        // 🎯 ALERTES IMMÉDIATES POUR VICTOIRES
        if (responseData.victory_detected) {
          if (responseData.victory_type === 'elimination') {
            alert('🎯 VICTOIRE PAR ÉLIMINATION TOTALE ! L\'ennemi n\'a plus d\'unités !');
          } else if (responseData.victory_type === 'moral_breakdown') {
            alert('💔 VICTOIRE PAR EFFONDREMENT DU MORAL ! L\'ennemi a perdu tout moral !');
          }
        }
        
        // Utiliser le service pour détecter la victoire
        const victoryResult = await PillageService.detectVictoryFromResponse(responseData, actualBattleId);
        
        if (victoryResult.hasVictory && victoryResult.victoryData) {
          setVictoryData(victoryResult.victoryData);
          setPillagePopupOpen(true);
        }
        
        // Recharger les données depuis le serveur
        await loadBattleUnits();
        // Forcer un re-render des statistiques et de l'affichage
        setSelectedUnit(null);
      }

    } catch (error) {
    } finally {
      // Marquer l'unité comme ayant attaqué seulement après confirmation du combat
      if (combatData.attacker) {
        const attackerUnitId = combatData.attacker.unitId;
        setUnitsAttackedThisTurn(prev => new Set(prev).add(attackerUnitId));
      }
      
      setCombatPopupOpen(false);
      setAttackRequestData(null);
      
      // Si on attendait une confirmation d'IA, résoudre la promesse
      if (waitingForAICombatConfirm && aiCombatResolver) {
        aiCombatResolver();
        setWaitingForAICombatConfirm(false);
        setAiCombatResolver(null);
      }
    }
  };
  
  // Fonction pour ouvrir le popup d'informations d'unité
  const handleOpenUnitInfo = useCallback(() => {
    if (!selectedCompactUnit) {
      alert('Veuillez d\'abord sélectionner une unité sur le champ de bataille');
      return;
    }
    
    // Trouver l'unité complète avec toutes ses données
    const fullUnit = battleUnits?.find(unit => {
      return (
        (unit.unitId && unit.unitId === selectedCompactUnit?.unitId) ||
        (unit.id && unit.id === selectedCompactUnit?.id) ||
        (unit.id && unit.id === selectedCompactUnit?.unitId) ||
        (unit.unitId && unit.unitId === selectedCompactUnit?.id)
      );
    });
    
    setSelectedUnitForInfo(fullUnit || selectedCompactUnit);
    setUnitInfoPopupOpen(true);
  }, [selectedCompactUnit, battleUnits]);

  // Fonction sécurisée pour les auras de héros
  const safeHeroAuraFunction = useCallback((unit: any, position: { q: number; r: number }) => {
    if (heroAuraFunction && typeof heroAuraFunction === 'function') {
      return heroAuraFunction(unit, position);
    }
    return { inAura: false, bonuses: null, hero: null };
  }, [heroAuraFunction]);

  // Déselectionner automatiquement toutes les unités quand le tour change
  const prevCurrentTurnPlayer = useRef(currentTurnPlayer);
  useEffect(() => {
    if (prevCurrentTurnPlayer.current !== currentTurnPlayer) {
      prevCurrentTurnPlayer.current = currentTurnPlayer;
      setSelectedUnit(null);
      setSelectedCompactUnit(null);
    }
  }, [currentTurnPlayer]);

  // Auto-fit zoom à l'ouverture
  useEffect(() => {
    if (battleGrid && battleGrid.length > 0) {
      try {
        // Calculer les dimensions de la grille
        const minQ = Math.min(...battleGrid.map(hex => hex.q));
        const maxQ = Math.max(...battleGrid.map(hex => hex.q));
        const minR = Math.min(...battleGrid.map(hex => hex.r));
        const maxR = Math.max(...battleGrid.map(hex => hex.r));
        
        const size = 25;
        const topLeftRaw = {
          x: size * (3/2 * minQ),
          y: size * (Math.sqrt(3)/2 * minQ + Math.sqrt(3) * minR)
        };
        const bottomRightRaw = {
          x: size * (3/2 * maxQ),
          y: size * (Math.sqrt(3)/2 * maxQ + Math.sqrt(3) * maxR)
        };
        
        const gridWidth = Math.abs(bottomRightRaw.x - topLeftRaw.x) + (size * 3);
        const gridHeight = Math.abs(bottomRightRaw.y - topLeftRaw.y) + (size * 3);
        
        const availableWidth = window.innerWidth;
        const availableHeight = window.innerHeight - 45 - 60;
        
        const zoomX = availableWidth / gridWidth;
        const zoomY = availableHeight / gridHeight;
        const baseOptimal = Math.min(zoomX, zoomY, MAX_ZOOM);
        
        let targetZoom;
        if (baseOptimal < 0.6) {
          targetZoom = baseOptimal * 1.4;
        } else if (baseOptimal < 1.0) {
          targetZoom = baseOptimal * 1.2;
        } else {
          targetZoom = baseOptimal * 1.0;
        }
        
        const finalZoom = Math.min(Math.max(targetZoom, 0.8), 1.8);
        setZoomLevel(finalZoom);
        
      } catch (error) {
        setZoomLevel(1.2);
      }
    }
  }, [battleGrid]);

  // Calcul dynamique des dimensions et offsets
  const getBattlefieldBounds = () => {
    if (!battleGrid || !Array.isArray(battleGrid) || battleGrid.length === 0) {
      return { 
        minX: 0, maxX: 2400, minY: 0, maxY: 1600,
        centerX: 1200, centerY: 800,
        width: 2400, height: 1600
      };
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
    
    const width = maxX - minX;
    const height = maxY - minY;
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    
    return { minX, maxX, minY, maxY, centerX, centerY, width, height };
  };

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

  const getWallGroupNumber = (hex: any): number | null => {
    if (!battleData?.wall_system?.wall_groups || hex.terrain !== 'wall') {
      return null;
    }

    const wallGroups = battleData.wall_system.wall_groups;
    
    // Chercher dans quel groupe se trouve cette position
    for (const [groupKey, groupData] of Object.entries(wallGroups)) {
      const positions = (groupData as any).positions || [];
      // Convertir les positions backend [row, col] vers frontend {q, r}
      const frontendPositions = positions.map(([row, col]: [number, number]) => ({ q: col, r: row }));
      
      if (frontendPositions.some((pos: {q: number; r: number}) => pos.q === hex.q && pos.r === hex.r)) {
        return (groupData as any).group_index + 1; // +1 pour afficher #1, #2, etc.
      }
    }
    
    return null;
  };

  const battlefieldBounds = getBattlefieldBounds();

  return (
    <div 
      className="simple-battlefield-v2-fullscreen"
      style={{ 
        width: '100vw', 
        height: '100vh', 
        overflow: 'hidden',
        position: 'fixed',
        top: 0,
        left: 0,
        zIndex: 10000
      }}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onTouchCancel={handleTouchEnd}
    >
      {/* ========== BANDEAU SUPÉRIEUR COMPACT MOBILE ========== */}
      <div className="battlefield-topbar">
        {/* ATTAQUANT */}
        <div className="topbar-team attacker">
          <div className="team-title"><span className="title-text">ATT</span><span className="title-icon">⚔️</span></div>
          <div className="team-stats-compact">
            <div className="battlefield-stat-compact">
              <span className="battlefield-stat-label">Unités</span>
              <span className="battlefield-stat-num">{attackerStats.units}</span>
            </div>
            <div className="battlefield-stat-compact">
              <span className="battlefield-stat-label">Moral</span>
              <div className="moral-compact">
                <div className="moral-bar-mini">
                  <div className="moral-fill" style={{ width: `${Math.min(100, attackerStats.moral)}%` }}></div>
                </div>
                <span className="battlefield-stat-num">{attackerStats.moral}</span>
              </div>
            </div>
          </div>
        </div>

        {/* CENTRE - ROUND & TIMER */}
        <div className="topbar-center-compact">
          <div className="round-compact">Round {currentRound}</div>
          
          {/* Badge joueur actif */}
          <div className={`player-badge-mini ${currentTurnPlayer ? 
            (battleParticipants && battleParticipants.attacker_id === currentTurnPlayer ? 'att' : 'def') : 
            (props.currentPlayer === 'attacker' ? 'att' : 'def')
          }`}>
            {currentTurnPlayer ? 
              (battleParticipants && battleParticipants.attacker_id === currentTurnPlayer ? 'ATT' : 'DÉF') : 
              (props.currentPlayer === 'attacker' ? 'ATT' : 'DÉF')
            }
          </div>

          {/* Timer mini */}
          {(actualGamePhase === 'battle' || actualGamePhase === 'deployment') && turnTimeRemaining !== null && (
            <div className="timer-mini" style={{
              background: `conic-gradient(
                ${turnTimeRemaining <= 5 ? '#ff4444' : '#4CAF50'} ${(turnTimeRemaining / 20) * 360}deg,
                #2c3e50 ${(turnTimeRemaining / 20) * 360}deg
              )`
            }}>
              <span>{turnTimeRemaining}</span>
            </div>
          )}
        </div>

        {/* DÉFENSEUR */}
        <div className="topbar-team defender">
          <div className="team-title"><span className="title-text">DÉF</span><span className="title-icon">🛡️</span></div>
          <div className="team-stats-compact">
            {/* Moral en premier pour symétrie avec attaquant */}
            <div className="battlefield-stat-compact">
              <span className="battlefield-stat-label">Moral</span>
              <div className="moral-compact">
                <div className="moral-bar-mini">
                  <div className="moral-fill" style={{ width: `${Math.min(100, defenderStats.moral)}%` }}></div>
                </div>
                <span className="battlefield-stat-num">{defenderStats.moral}</span>
              </div>
            </div>
            {/* Unités en second */}
            <div className="battlefield-stat-compact">
              <span className="battlefield-stat-label">Unités</span>
              <span className="battlefield-stat-num">{defenderStats.units}</span>
            </div>
          </div>
        </div>
      </div>



      {/* ========== CHAMP DE BATAILLE PRINCIPAL AVEC ZOOM ========== */}
      <div 
        className="battlefield-container battlefield-mobile-container"
        style={{
          position: 'fixed',
          bottom: '104px', /* Hauteur bottombar (40px) + espace navigation mobile (60px) + marge (4px) */
          left: 0,
          right: 0,
          overflow: 'hidden',
          /* S'assurer que le contenu ne déborde pas sous la barre de navigation */
          marginBottom: 'env(safe-area-inset-bottom, 60px)'
        }}
        onWheel={handleWheelZoom}
      >
        {/* CONTENEUR GLOBAL CENTRÉ POUR TOUTES LES COUCHES */}
        <div className="battlefield-layers-container" style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transform: `translate(${viewOffset.x}px, ${viewOffset.y}px) scale(${zoomLevel})`,
          transformOrigin: 'center center',
          transition: 'transform 0.1s ease-out'
        }}>
          
          {/* COUCHE 1 : Grille hexagonale (base) */}
          <div className="hexagonal-grid-container" style={{ 
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)'
          }}>
            <svg
              className="hexagonal-grid"
              width="100%"
              height="100%"
              viewBox={`${battlefieldBounds.minX} ${battlefieldBounds.minY} ${battlefieldBounds.width} ${battlefieldBounds.height}`}
              preserveAspectRatio="xMidYMid meet"
              style={{
                cursor: 'default'
              }}
              onMouseDown={(e: React.MouseEvent) => {
                e.preventDefault();
                setTouchState(prev => ({ ...prev, isPanning: false }));
                handleMouseDown(e);
              }}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
            >
              {/* 🎭 ClipPath pour masquer l'image hors de la grille */}
              <defs>
                <clipPath id="gridClipPath">
                  {battleGrid.map((hex) => {
                    const { x, y } = hexToPixel(hex.q, hex.r);
                    const points = getHexagonPoints(x, y);
                    return <polygon key={`clip-${hex.q}-${hex.r}`} points={points} />;
                  })}
                </clipPath>
              </defs>
              
              {/* 🖼️ Image de fond */}
              {backgroundImage && (
                <image
                  href={`/assets/battlefield_images/${backgroundImage}`}
                  x={battlefieldBounds.minX}
                  y={battlefieldBounds.minY}
                  width={battlefieldBounds.width}
                  height={battlefieldBounds.height}
                  clipPath="url(#gridClipPath)"
                  preserveAspectRatio="xMidYMid slice"
                />
              )}

            {battleGrid.map((hex, index) => {
              const { x, y } = hexToPixel(hex.q, hex.r);
              const points = getHexagonPoints(x, y);
              const isSelected = selectedHex && selectedHex.q === hex.q && selectedHex.r === hex.r;
              const wallGroupNumber = getWallGroupNumber(hex);

              return (
                <g key={`${hex.q}-${hex.r}`}>
                  <polygon
                    points={points}
                    className={`hex ${hex.terrain} ${hex.zone} ${isSelected ? 'selected' : ''}`}
                    onClick={() => handleHexClick(hex)}
                    style={{
                      fill: getTerrainColor(hex.terrain),
                      opacity: 0.4,
                      stroke: isSelected ? '#ffd700' : '#ffffff',
                      strokeWidth: isSelected ? 3 : 1.5,
                      cursor: 'pointer',
                      filter: isSelected ? 'brightness(1.2) drop-shadow(0 0 12px rgba(255, 215, 0, 0.9))' : 'none',
                      transition: 'all 0.3s ease'
                    }}
                  />

                  {/* Icône de terrain */}
                  <text
                    x={x}
                    y={y + 2}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fontSize="12"
                    fill="#000"
                    style={{ pointerEvents: 'none', textShadow: '1px 1px 2px rgba(255,255,255,0.8)' }}
                  >
                    {hex.terrain === 'base-attack' ? '⚔️' :
                     hex.terrain === 'base-defense' ? '🛡️' :
                     hex.terrain === 'wall' && wallGroupNumber ? `#${wallGroupNumber}` :
                     ''}
                  </text>
                </g>
              );
            })}
            </svg>
          </div>

        {/* COUCHE 2 : Unités de bataille (BattlefieldVisualsV2) */}
        <div className="battlefield-layer" style={{ 
          zIndex: 20, 
          pointerEvents: 'none',
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)'
        }}>
          <BattlefieldVisualsV2
            battleData={battleData}
            onUnitClick={(unit) => {
              // Gestion de la désélection
              if (unit && (unit as any).__deselect) {
                setSelectedCompactUnit(null); // Désélectionner
              } else {
                setSelectedCompactUnit(unit); // Sélection normale
              }
            }}
            onAttackRequest={handleAttackRequest}
            selectedUnit={selectedCompactUnit}
            hexToPixel={hexToPixel}
            battlefieldBounds={getBattlefieldBounds()}
            currentTurnPlayer={currentTurnPlayer}
            onHeroAuraReady={onHeroAuraReady}
            battleParticipants={battleParticipants}
            participants={currentBattlefield?.participants}
            refreshTrigger={battleData} // Refresh quand battleData change
          />
        </div>

        {/* COUCHE 3 : Système tactique - déplacement & combat (BattlefieldTacticsV2) */}
        <div className="battlefield-layer" style={{ 
          zIndex: 30,
          pointerEvents: 'none', // Permettre aux événements de traverser cette couche par défaut
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)'
        }}>
          <BattlefieldTacticsV2
            battlefield={{ hexCells: battleGrid }}
            units={battleUnits}
            selectedUnitId={selectedCompactUnit ? selectedCompactUnit.unitId : null}
            onUnitMove={onUnitMove}
            onClearSelection={() => setSelectedCompactUnit(null)}
            hexToPixel={hexToPixel}
            battlefieldBounds={getBattlefieldBounds()}
            getHeroAuraForUnit={safeHeroAuraFunction}
            currentTurnPlayer={currentTurnPlayer}
            battleParticipants={battleParticipants}
            currentRound={currentRound}
            actualBattleId={actualBattleId}
            loadBattleUnits={loadBattleUnits}
            setSelectedUnit={setSelectedUnit}
            attackRequestData={attackRequestData}
            onAttackComplete={() => setAttackRequestData(null)}
            onAttackRequest={handleAttackRequest}
            // Props pour le combat
            setCombatPopupOpen={setCombatPopupOpen}
            setCombatData={setCombatData}
          />
        </div>
        
      </div> {/* Fin du conteneur global centré */}
    </div>

      {/* ========== BANDEAU INFÉRIEUR FIXE ========== */}
      <div className="battlefield-bottombar" style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 100,
        height: '60px'
      }}>
        <div className="bottombar-section bottombar-info">
          {selectedHex ? (
            <>
              <span className="bottombar-coords">Case : ({selectedHex.q}, {selectedHex.r})</span>
              {(() => {
                const hex = battleGrid.find(h => h.q === selectedHex.q && h.r === selectedHex.r);
                if (!hex) return <span className="bottombar-terrain">Terrain : Inconnu</span>;
                
                return (
                  <>
                    <span className="bottombar-terrain">Terrain : {hex.terrain}</span>
                    {(() => {
                      const bonuses = [];
                      if (hex.defenseBonus && hex.defenseBonus !== 0) {
                        bonuses.push(hex.defenseBonus > 0 ? `🛡️+${hex.defenseBonus}` : `🛡️${hex.defenseBonus}`);
                      }
                      if (hex.attackPenalty && hex.attackPenalty !== 0) {
                        bonuses.push(hex.attackPenalty > 0 ? `⚔️+${hex.attackPenalty}` : `⚔️${hex.attackPenalty}`);
                      }
                      if (hex.movementBonus && hex.movementBonus !== 0) {
                        bonuses.push(hex.movementBonus > 0 ? `🦶+${hex.movementBonus}` : `🦶${hex.movementBonus}`);
                      }
                      
                      return bonuses.length > 0 ? (
                        <span className="bottombar-bonuses">{bonuses.join(' ')}</span>
                      ) : (
                        <span className="bottombar-bonuses">Aucun modificateur</span>
                      );
                    })()}
                  </>
                );
              })()}
            </>
          ) : (
            <span className="bottombar-hint">Cliquez sur une case pour voir les infos terrain</span>
          )}
        </div>
        <div className="bottombar-section bottombar-actions">
          {/* Bouton Tutoriel de Combat - Position 1 */}
          <button 
            className="btn-compact" 
            onClick={() => setTutorialOpen(true)}
            style={{ 
              backgroundColor: '#ffc107', 
              color: '#000',
              fontWeight: 'bold',
              fontSize: '18px',
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              border: '2px solid #fff',
              boxShadow: '0 2px 8px rgba(255, 193, 7, 0.4)'
            }}
            title="Guide du système de combat"
          >
            ?
          </button>

          {/* Bouton Info Unité - Position 2 */}
          <button 
            className="btn-compact" 
            onClick={handleOpenUnitInfo}
            style={{ 
              backgroundColor: '#3498db', 
              color: 'white',
              fontWeight: 'bold',
              fontSize: '18px',
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              border: '2px solid #fff',
              boxShadow: '0 2px 8px rgba(52, 152, 219, 0.4)'
            }}
            title="Voir les informations de l'unité sélectionnée"
          >
            ℹ️
          </button>

          {actualGamePhase === 'battle' && (() => {
            const isMyTurn = currentTurnPlayer === user?.id;
            return (
              <button 
                className="btn-compact btn-info" 
                onClick={endTurn}
                disabled={!isMyTurn}
                style={{ 
                  backgroundColor: isMyTurn ? '#17a2b8' : '#6c757d', 
                  color: 'white',
                  cursor: isMyTurn ? 'pointer' : 'not-allowed',
                  opacity: isMyTurn ? 1 : 0.5
                }}
                title={isMyTurn ? "Terminer votre tour" : "Ce n'est pas votre tour !"}
              >
                Fin de tour {!isMyTurn ? '🔒' : ''}
              </button>
            );
          })()}

          
          {/* Bouton Se Rendre (détection automatique de l'équipe du joueur) */}
          {actualBattleId && user?.id && (actualGamePhase === 'battle' || actualGamePhase === 'deployment') && (() => {
            // Détecter si le joueur connecté est attaquant ou défenseur
            const isAttacker = battleParticipants?.attacker_id === user.id;
            const isDefender = battleParticipants?.defender_id === user.id;
            
            // Si le joueur n'est ni attaquant ni défenseur, ne pas afficher le bouton
            if (!isAttacker && !isDefender) return null;
            
            const playerRole = isAttacker ? 'attacker' : 'defender';
            const apiEndpoint = isAttacker ? 'auto-attacker' : 'auto';
            const confirmMessage = isAttacker 
              ? '⚠️ Voulez-vous vous rendre ?\n\n❌ Vous perdrez la bataille et vos unités seront redistribuées.\n\nCette action est IRRÉVERSIBLE !'
              : '⚠️ Voulez-vous vous rendre ?\n\n❌ Vous perdrez la bataille et vos unités seront redistribuées.\n\nCette action est IRRÉVERSIBLE !';
            
            return (
              <button 
                className="btn-compact" 
                style={{ 
                  backgroundColor: '#e74c3c', 
                  color: 'white',
                  border: 'none',
                  marginRight: '5px'
                }}
                onClick={async () => {
                  try {
                    if (window.confirm(confirmMessage)) {
                      const surrenderResponse = await fetch(`${getApiUrl()}/api/v2/battle/surrender/${actualBattleId}/${apiEndpoint}`, {
                        method: 'POST'
                      });
                      const data = await surrenderResponse.json();
                      
                      if (data.success) {
                        const serverMessage = data.surrender_details?.detailed_message || data.detailed_message || data.message || 'Vous vous êtes rendu !';
                        alert(`${serverMessage}\n\n✅ Bataille terminée !`);
                        
                        // Détecter victoire après reddition
                        const victoryResult = await PillageService.detectVictoryFromSurrender(data, actualBattleId);
                        
                        if (victoryResult.hasVictory && victoryResult.victoryData) {
                          if (window.confirm('🏆 Victoire ! Voulez-vous ouvrir le popup de pillage pour collecter les ressources ?\n\n🎁 Vous pourrez choisir quelles ressources prendre.')) {
                            setVictoryData(victoryResult.victoryData);
                            setPillagePopupOpen(true);
                          }
                        }
                      } else {
                        alert(`❌ Erreur: ${data.error}`);
                      }
                    }
                  } catch (error) {
                    alert('❌ Erreur lors de la reddition.');
                  }
                }}
                title="Se rendre et perdre la bataille"
              >
                🏳️ Se rendre
              </button>
            );
          })()}
          
          {/* Boutons Voyage Retour */}
          {actualBattleId && (
            <>
              <button 
                className="btn-compact" 
                style={{ 
                  backgroundColor: '#007bff', 
                  color: 'white',
                  border: 'none',
                  marginRight: '5px'
                }}
                onClick={handleReturnJourneyAll}
                title="Retour de TOUS les transports de la bataille"
              >
                Voyage Retour
              </button>
            </>
          )}
          

          <button 
            className="btn-compact" 
            style={{backgroundColor: '#9b59b6', color: 'white', border: 'none', marginRight: '5px'}}
            onClick={() => {
              const password = prompt('🔒 Mot de passe requis pour accéder au panneau AI Debug:');
              if (password === 'admin8') {
                setAiDebugOpen(true);
              } else if (password !== null) {
                alert('❌ Mot de passe incorrect !');
              }
            }}
            title="Panneau de debug IA (protégé par mot de passe)"
          >
            🤖 AI Debug
          </button>
          <button className="btn-compact btn-secondary" onClick={() => props.onClose && props.onClose()}>Fermer</button>
        </div>
      </div>

      {/* Popup de déploiement */}
      {deploymentPopupOpen && (() => {
        return (
          <UnitDeploymentPopupV2
            isOpen={deploymentPopupOpen}
            onClose={() => setDeploymentPopupOpen(false)}
            selectedHex={selectedHex}
            team={selectedTeam || 'attacker'}
            onDeployUnit={handleDeployUnit}
            targetCityId={targetCityId}
            battlefieldTemplateId={battlefieldTemplateId}
            battleId={actualBattleId}
            onDeploymentComplete={() => {
              loadBattleUnits();
            }}
          />
        );
      })()}

      {/* Popup d'informations d'unité */}
      {unitInfoPopupOpen && selectedUnitForInfo && (() => {
        // Extraire le type d'unité à partir de l'ID de façon centralisée
        const unitIdStr = selectedUnitForInfo.unitId || selectedUnitForInfo.id || '';
        // Utiliser la fonction centrale d'extraction pour couvrir tous les formats
        const unitType = extractUnitType(unitIdStr || '');
        
        // Chercher les stats dans les différents âges
        let unitBaseStats = null;
        
        if (unitStats && unitType) {
          // Essayer classical_age d'abord
          if (unitStats.classical_age && unitStats.classical_age[unitType]) {
            unitBaseStats = unitStats.classical_age[unitType];
          }
          // Puis napoleonic_age
          else if (unitStats.napoleonic_age && unitStats.napoleonic_age[unitType]) {
            unitBaseStats = unitStats.napoleonic_age[unitType];
          }
          // Puis enemy_units
          else if (unitStats.enemy_units && unitStats.enemy_units[unitType]) {
            unitBaseStats = unitStats.enemy_units[unitType];
          }
          else {
          }
        }
        
        // Calculer les effets de terrain si possible
        let terrainEffects = null;
        const unitPosition = selectedUnitForInfo.position;
        if (unitPosition && battleGrid) {
          const hex = battleGrid.find(h => h.q === unitPosition[0] && h.r === unitPosition[1]);
          if (hex) {
            terrainEffects = {
              attack_bonus: hex.attackPenalty || 0,
              defense_bonus: hex.defenseBonus || 0,
              movement_cost: hex.movementBonus || 0,
              terrain_name: hex.terrain || 'inconnu'
            };
          }
        }
        
        // Créer un objet serverUnits pour le popup
        const serverUnits = battleUnits?.reduce((acc, unit) => {
          const unitKey = unit.unitId || unit.id;
          if (unitKey) {
            acc[unitKey] = unit;
          }
          return acc;
        }, {} as any);
        
        return (
          <UnitInfoPopup
            isOpen={unitInfoPopupOpen}
            onClose={() => {
              setUnitInfoPopupOpen(false);
              setSelectedUnitForInfo(null);
            }}
            unit={selectedUnitForInfo}
            unitBaseStats={unitBaseStats}
            terrainEffects={terrainEffects}
            serverUnits={serverUnits}
            heroAuraFunction={heroAuraFunction || undefined}
          />
        );
      })()}

      {combatPopupOpen && combatData.attackerStats && combatData.defenderStats && (
        <CombatPopup
          isOpen={combatPopupOpen}
          attacker={combatData.attackerStats}
          defender={combatData.defenderStats}
          attackerPosition={combatData.attacker?.position ? { q: combatData.attacker.position[0], r: combatData.attacker.position[1] } : null}
          defenderPosition={combatData.defender?.position ? { q: combatData.defender.position[0], r: combatData.defender.position[1] } : null}
          terrainAttacker={combatData.attacker?.position ? getTerrainAtPosition(combatData.attacker.position) : 'plains'}
          terrainDefender={combatData.defender?.position ? getTerrainAtPosition(combatData.defender.position) : 'plains'}
          onConfirmCombat={handleConfirmCombat}
          onCancel={() => setCombatPopupOpen(false)}
          attackerUnit={combatData.attacker}
          defenderUnit={combatData.defender}
          battlefieldId={actualBattleId}
          attackerId={combatData.attacker?.unitId}
          defenderId={combatData.defender?.unitId}
          battleParticipants={battleParticipants}
          isInHeroAura={safeHeroAuraFunction}
        />
      )}

      {pillagePopupOpen && victoryData && (
        <PillagePopup
          isOpen={pillagePopupOpen}
          onClose={() => {
            setPillagePopupOpen(false);
            setVictoryData(null);
          }}
          battleId={victoryData.battle_id}
          cityId={victoryData.defender_city_id}
          cityName={`Ville ${victoryData.defender_city_id}`}
          attackerShips={victoryData.attacker_ships}
          attackerId={victoryData.attacker_id}

          onPillageComplete={() => {
            setPillagePopupOpen(false);
            setVictoryData(null);
            // Pillage terminé - l'utilisateur peut maintenant choisir de terminer manuellement la bataille
          }}
        />
      )}

      {wallInteractionPopupOpen && selectedWallPosition && (
        <WallInteractionPopup
          isOpen={wallInteractionPopupOpen}
          onClose={() => {
            setWallInteractionPopupOpen(false);
            setSelectedWallPosition(null);
          }}
          position={selectedWallPosition}
          wallGroup={getWallGroupAtPosition(selectedWallPosition)}
          wallStats={getWallStats()}
          onAttackWall={attackWallGroup}
          onOpenCombatPopup={handleWallCombatPopup}
          currentPlayer={user?.id || undefined}
        />
      )}

      {aiDebugOpen && actualBattleId && (
        <AIDebugPopup
          battleId={actualBattleId}
          onClose={() => setAiDebugOpen(false)}
          deployedUnits={battleUnits || []}
        />
      )}

      <CombatTutorialPopup
        isOpen={tutorialOpen}
        onClose={() => setTutorialOpen(false)}
      />
    </div>
  );
};

export default SimpleBattlefieldV2;