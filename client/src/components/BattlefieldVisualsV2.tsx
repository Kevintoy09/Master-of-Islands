/**
 * BattlefieldVisualsV2.tsx
 * 
 * Système de visualisation des unités sur le champ de bataille V2
 * - Lecture du fichier battlesv2.json ultra-compact
 * - Affichage optimisé avec icônes spécifiques par type d'unité
 * - Gestion spéciale des héros (HP + aura animée)
 * - Compatibilité avec unit_stats.json pour les icônes
 */

import React, { useState, useEffect, useCallback } from 'react';
import { CompactUnit } from '../types/index';
import { canAttackTarget, areEnemies, extractUnitType } from '../utils/combatUtils';
import { useUnitsActed } from '../hooks/useUnitsActed';
import { getPlayerColor, getPlayerColorClass } from '../utils/playerColors';
import { extractUnitInfo } from './UnitInfoPopup';
import { useTurnLock } from '../context/TurnLockContext';
import { useUser } from '../hooks/useUser';
import { useHeroAura } from '../hooks/useHeroAura';
import { useUnitStats } from '../hooks/useUnitStats';
import { getUnitIcon } from '../constants/unitIcons';
import './BattlefieldVisualsV2.css';

interface CompactBattle {
  battleId: string;
  timestamp: number;
  current_round: number;
  current_player: string;
  teams: {
    [teamKey: string]: CompactUnit[];
  };
}

interface BattlefieldVisualsV2Props {
  battleData: CompactBattle | null;
  onUnitClick?: (unit: CompactUnit) => void;
  onAttackRequest?: (attacker: CompactUnit, defender: CompactUnit) => void;
  selectedUnit?: CompactUnit | null;
  hexToPixel?: (q: number, r: number) => { x: number; y: number };
  battlefieldBounds?: { minX: number; maxX: number; minY: number; maxY: number; width: number; height: number };
  currentTurnPlayer?: string;
  battleParticipants?: { attacker_id: string; defender_id: string };
  participants?: { attackers: string[]; defenders: string[] }; // Liste complète des participants
  refreshTrigger?: any; // Pour déclencher le refresh des unités ayant agi
  // ✨ NOUVEAU: Callback pour exposer la fonction d'aura aux composants externes
  onHeroAuraReady?: (getHeroAuraFn: (unit: any, position: { q: number; r: number }) => any) => void;
}

export const BattlefieldVisualsV2: React.FC<BattlefieldVisualsV2Props> = ({
  battleData,
  onUnitClick,
  onAttackRequest,
  selectedUnit,
  hexToPixel: hexToPixelProp,
  battlefieldBounds,
  currentTurnPlayer,
  battleParticipants,
  participants,
  refreshTrigger,
  onHeroAuraReady
}) => {

  const [hoveredUnitId, setHoveredUnitId] = useState<string | null>(null);
  
  // � Hook utilisateur (pour vérifier le player connecté)
  const { user } = useUser();
  
  // �🔒 Hook de verrouillage des tours
  const { canControlUnit } = useTurnLock();
  
  // ✨ Charger les stats d'unités pour récupérer les ranges
  const unitStatsData = useUnitStats();
  
  // ✨ NOUVEAU: Utilisation du hook useHeroAura pour gérer les auras
  const { unitsInHeroAura, getHeroAuraForUnitSync, heroesDataCache } = useHeroAura(battleData, battleData?.battleId, participants);

  // ✨ Exposer la fonction d'aura aux composants externes (avec useCallback pour éviter les boucles)
  React.useEffect(() => {
    if (onHeroAuraReady && getHeroAuraForUnitSync) {
      onHeroAuraReady(getHeroAuraForUnitSync);
    }
  }, [onHeroAuraReady, getHeroAuraForUnitSync]); // Dépendances stables grâce à useCallback
  
  // Hook pour récupérer les unités qui ont déjà agi ce round
  const { hasUnitActed, refreshUnitsActed } = useUnitsActed(
    battleData?.battleId || null,
    refreshTrigger || battleData?.current_round // Refresh sur changement de trigger ou round
  );

  const extractPlayerFromUnitId = (unitId: string): string => {
    const parts = unitId.split('_');
    // Gérer player_X
    if (parts.length >= 3 && parts[1] === 'player') {
      return `${parts[1]}_${parts[2]}`;
    }
    // Gérer wild_camp (barbares)
    if (parts.includes('wild_camp')) {
      return 'wild_camp';
    }
    return '';
  };

  // Gestion du clic sur une unité avec logique de combat
  const handleUnitClick = async (clickedUnit: CompactUnit) => {
    // 🔒 VÉRIFICATION DU VERROUILLAGE DES TOURS
    const clickedUnitPlayer = extractPlayerFromUnitId(clickedUnit.unitId);
    const connectedPlayerId = user?.id || '';
    
    // Vérifier si c'est une unité ennemie
    const isEnemyUnit = clickedUnitPlayer !== connectedPlayerId;
    
    // CAS 1: Clic sur unité ennemie AVEC une unité sélectionnée → ATTAQUE (toujours permis)
    if (isEnemyUnit && selectedUnit) {
      // Continuer vers la logique d'attaque (plus bas dans le code)
    }
    // CAS 2: Clic sur unité ennemie SANS unité sélectionnée → BLOQUER (sélection interdite)
    else if (isEnemyUnit && !selectedUnit) {
      return;
    }
    // CAS 3: Clic sur VOTRE unité → Vérifier avec canControlUnit
    else if (!isEnemyUnit && !canControlUnit(clickedUnitPlayer, connectedPlayerId)) {
      return;
    }
    
    // Si c'est la même unité, désélectionner
    if (selectedUnit && selectedUnit.unitId === clickedUnit.unitId) {
      onUnitClick?.({ ...clickedUnit, __deselect: true } as any); 
      return;
    }
    
    // Vérifier que l'unité cliquée appartient au joueur actuel OU que ce soit une attaque
    const isEnemyClick = currentTurnPlayer && clickedUnitPlayer && clickedUnitPlayer !== currentTurnPlayer;
    
    // Si on clique sur une unité ennemie sans avoir d'unité sélectionnée, on ignore
    if (isEnemyClick && !selectedUnit) {
      return;
    }
    
    // Si on clique sur une unité ennemie avec une unité sélectionnée, c'est une attaque
    if (isEnemyClick && selectedUnit) {
      // Continuer vers la logique d'attaque plus bas
    } else if (isEnemyClick) {
      // Unité ennemie cliquée sans sélection active, ignorer
      return;
    }
    
    // Si aucune unité sélectionnée, sélectionner cette unité
    if (!selectedUnit) {
      onUnitClick?.(clickedUnit);
      return;
    }

    // Si ce sont des unités ennemies, vérifier la portée d'attaque
    if (areEnemies(selectedUnit, clickedUnit)) {
      // Unités ennemies détectées
      
      try {
        const attackResult = await canAttackTarget(
          selectedUnit, 
          selectedUnit.position, 
          clickedUnit.position
        );
        
        if (attackResult.canAttack) {
          onAttackRequest?.(selectedUnit, clickedUnit);
        }
      } catch (error) {
        // Erreur silencieuse
      }
    } else {
      // Même équipe ou autre cas : sélectionner la nouvelle unité
      onUnitClick?.(clickedUnit);
    }
  };

  // Extraire le type d'unité depuis l'unitId (utilise la fonction utilitaire robuste)
  const getUnitType = (unitId: string): string => {
    return extractUnitType(unitId);
  };

  // Obtenir le range d'une unité depuis unit_stats.json
  const getUnitRangeFromStats = (unitType: string): number => {
    if (!unitStatsData) return 1; // Fallback
    
    // Chercher dans classical_age
    if (unitStatsData.classical_age?.[unitType]?.range) {
      return unitStatsData.classical_age[unitType].range;
    }
    
    // Chercher dans enemy_units
    if (unitStatsData.enemy_units?.[unitType]?.range) {
      return unitStatsData.enemy_units[unitType].range;
    }
    
    return 1; // Fallback par défaut
  };

  // Convertir coordonnées hex vers pixels (utiliser la fonction du parent ou fallback)
  const hexToPixel = hexToPixelProp || ((q: number, r: number) => {
    const size = 25; // Taille réduite pour que tout rentre
    const x = size * (3/2 * q);
    const y = size * (Math.sqrt(3)/2 * q + Math.sqrt(3) * r);
    // Ajustement pour centrage parfait (fallback si pas de prop)
    return { x: x + 1200 - 0, y: y + 400 - 0}; // Centrage dans viewBox 2400x1600
  });

  if (!battleData) {
    return null; // ⭐ Plus de texte de chargement qui prend de la place
  }

  return (
    <div className="battlefield-visuals-v2">
      <svg 
        width="1200" 
        height="800" 
        viewBox={battlefieldBounds ? 
          `${battlefieldBounds.minX} ${battlefieldBounds.minY} ${battlefieldBounds.width} ${battlefieldBounds.height}` : 
          "0 0 2400 1600"
        }
        className="battlefield-svg"
        style={{ 
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none' // Permettre le drag de la grille en arrière-plan
        }}
      >
        {/* Rendu des unités par équipe */}
        {Object.entries(battleData.teams).map(([teamKey, units]) => {
          return (
          <g key={teamKey} className={`team-${teamKey}`}>
            {units.map((unit, index) => {
              const unitType = getUnitType(unit.unitId);
              const icon = getUnitIcon(unitType);
              const isHero = unitType === 'hero';
              const isInHeroAura = unitsInHeroAura.has(unit.unitId);
              
              // Debug silencieux
              const { x, y } = hexToPixel(unit.position[0], unit.position[1]);
              
              // ✅ NOUVEAU: Extraction du playerId et détermination de la couleur
              const unitInfo = extractUnitInfo(unit.unitId);
              const playerColor = getPlayerColor(unitInfo.playerId, unitInfo.team);
              const playerColorClass = getPlayerColorClass(unitInfo.playerId, unitInfo.team);
              const unitHasActed = hasUnitActed(unit.unitId);
              // Vérifier si l'unité appartient au joueur actuel
              const isCurrentPlayerUnit = unitInfo.playerId === currentTurnPlayer;
              
              return (
                <g
                  key={unit.unitId}
                  className={`unit-group${hoveredUnitId === unit.unitId ? ' hovered' : ''} ${playerColorClass}`}
                  onMouseEnter={() => setHoveredUnitId(unit.unitId)}
                  onMouseLeave={() => setHoveredUnitId(null)}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleUnitClick(unit);
                  }}
                  style={{ 
                    cursor: 'pointer', 
                    pointerEvents: 'auto',
                    position: 'relative',
                    zIndex: 1000, // TRÈS élevé pour être au-dessus de tout
                    transition: 'transform 0.18s cubic-bezier(.4,2,.6,1)'
                  }}
                >
                  {/* Cercle de base coloré selon le joueur */}
                  <circle
                    cx={x}
                    cy={y}
                    r="18"
                    className={`unit-base`}
                    strokeWidth="1"
                  />
                  
                  {/* Indicateur d'aura héros - ICÔNE COURONNE UNIQUEMENT */}
                  {isInHeroAura && !isHero && (
                    <g>
                      {/* Icône couronne plus grande et visible */}
                      <text
                        x={x + 15}
                        y={y - 15}
                        textAnchor="middle"
                        dominantBaseline="central"
                        fontSize="16"
                        fill="#FFD700"
                        stroke="#000"
                        strokeWidth="0.5"
                        style={{ pointerEvents: 'none', fontWeight: 'bold' }}
                      >
                        👑
                      </text>
                    </g>
                  )}
                  
                  {/* Icône de l'unité */}
                  <text
                    x={x}
                    y={y - 15}
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
                    x={x}
                    y={y + 3}
                    textAnchor="middle"
                    dominantBaseline="central"
                    fill={isCurrentPlayerUnit && !unitHasActed ? "#00FF00" : "white"} // Vert si c'est mon tour ET je n'ai pas joué
                    style={{ 
                      pointerEvents: 'none', 
                      fontWeight: isCurrentPlayerUnit && !unitHasActed ? 800 : 400, // Gras si peut jouer
                      fontFamily: 'Arial, sans-serif',
                      fontSize: '19px'
                    }}
                  >
                    {isHero && unit.hp !== undefined ? `${unit.hp}` : unit.unitCount || 1}
                  </text>
                  
                  {/* Aura spéciale pour les héros */}
                  {/* Cercle d'aura héros supprimé */}
                  
                  {/* Anneau de sélection */}
                  {selectedUnit?.unitId === unit.unitId && (() => {
                    let selectionRadius = 28; // Rayon par défaut pour unité normale
                    
                    if (isHero && heroesDataCache) {
                      // HÉROS: Utiliser l'aura_radius
                      // Utiliser la même logique d'extraction que getHeroAuraForUnitSync
                      let heroKey = unit.unitId;
                      
                      if (unit.unitId.includes('_hero_hero_')) {
                        // Format: attacker_player_1_hero_hero_1760731775_d086a0
                        // On veut extraire: hero_1760731775_d086a0
                        const match = unit.unitId.match(/_hero_(hero_[^_]+_[^_]+)$/);
                        if (match) {
                          heroKey = match[1]; // hero_1760731775_d086a0
                        }
                      } else if (unit.unitId.includes('_hero_') && !unit.unitId.includes('_hero_hero_')) {
                        // Ancien format: attacker_player_1_hero_player_1_hero_1
                        const parts = unit.unitId.split('_');
                        const heroIndex = parts.indexOf('hero');
                        
                        if (heroIndex !== -1 && heroIndex < parts.length - 1) {
                          const heroPlayerPart = parts[heroIndex - 1]; // player_1
                          const heroIdPart = parts[heroIndex + 1]; // player_1
                          const heroNumberPart = parts[heroIndex + 2]; // hero_1 ou 1
                          
                          if (heroPlayerPart && heroIdPart && heroNumberPart) {
                            heroKey = `hero_${heroIdPart}_${heroNumberPart}`;
                          }
                        }
                      }
                      
                      // Chercher les données du héros
                      let heroData = null;
                      for (const playerId in heroesDataCache) {
                        const playerData = heroesDataCache[playerId];
                        if (playerData.heroes && playerData.heroes[heroKey]) {
                          heroData = playerData.heroes[heroKey];
                          break;
                        }
                      }
                      
                      if (heroData?.calculated_bonuses?.aura_radius) {
                        // Calculer le rayon pour bien représenter l'aura
                        const hexDistance = 60; // Distance entre centres d'hexagones
                        selectionRadius = heroData.calculated_bonuses.aura_radius * hexDistance;
                      } else {
                        selectionRadius = 48; // Fallback pour héros sans données
                      }
                    } else {
                      // UNITÉ NORMALE: Utiliser la portée d'attaque (range)
                      const unitRange = getUnitRangeFromStats(unitType);
                      const hexDistance = 60; // Distance entre centres d'hexagones
                      selectionRadius = unitRange * hexDistance;
                    }
                    
                    return (
                      <circle
                        cx={x}
                        cy={y}
                        r={selectionRadius}
                        fill="none"
                        stroke="#FFD700"
                        strokeWidth="3"
                        opacity="0.8"
                        className={isHero ? "selection-ring hero-aura-selection" : "selection-ring"}
                      />
                    );
                  })()}
                </g>
              );
            })}
          </g>
          );
        })}
      </svg>
    </div>
  );
};

export default BattlefieldVisualsV2;