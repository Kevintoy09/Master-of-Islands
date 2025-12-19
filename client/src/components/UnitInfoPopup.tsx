import React, { useState, useEffect } from 'react';
import { Unit } from '../types/index';
import { getUnitStatsWithForgeBonus, extractUnitType } from '../utils/combatUtils';
import { getApiUrl } from '../utils/api';
import './UnitInfoPopup.css';
import usePreventZoom, { handleOverlayWheel, handleContentWheel } from '../hooks/usePreventZoom';

// Fonction utilitaire simple pour extraire playerId et team depuis l'unitId
export const extractUnitInfo = (unitId: string) => {
  if (!unitId) return { playerId: null, team: null };
  
  const parts = unitId.split('_');
  let playerId = 'player_1';
  let team = 'attacker';
  
  // Extraire team
  if (parts.includes('defender')) team = 'defender';
  
  // Extraire playerId - gérer player_X et wild_camp
  const playerMatch = unitId.match(/player_(\d+)/);
  if (playerMatch) {
    playerId = `player_${playerMatch[1]}`;
  } else if (unitId.includes('wild_camp')) {
    playerId = 'wild_camp';
  }
  
  return { playerId, team };
};

interface TerrainEffects {
  attack_bonus: number;
  defense_bonus: number;
  movement_cost: number;
  terrain_name: string;
}

interface UnitInfoPopupProps {
  isOpen: boolean;
  unit: Unit | null;
  terrainEffects: TerrainEffects | null;
  unitBaseStats: any; // Stats depuis unit_stats.json
  onClose: () => void;
  serverUnits?: any; // ✅ Ajout des unités serveur pour obtenir la position réelle
  playerId?: string; // ✅ NOUVEAU: ID du joueur pour les bonus de forge
  heroAuraFunction?: (unit: any, position: { q: number; r: number }) => { inAura: boolean; bonuses: any; hero: any }; // ✅ Fonction pour calculer les bonus héros
}

// Fonction utilitaire pour formater les calculs avec l'effectif en gris
const formatCalculation = (baseValue: number | string, unitCount: number, total: number) => {
  return (
    <>
      {baseValue} × <span className="unit-count">{unitCount}</span> = {total}
    </>
  );
};

const formatComplexCalculation = (calculation: string, unitCount: number) => {
  // Remplacer " × X = " par " × <span class="unit-count">X</span> = "
  const parts = calculation.split(` × ${unitCount} = `);
  if (parts.length === 2) {
    return (
      <>
        {parts[0]} × <span className="unit-count">{unitCount}</span> = {parts[1]}
      </>
    );
  }
  return calculation;
};

const UnitInfoPopup: React.FC<UnitInfoPopupProps> = ({
  isOpen,
  unit,
  terrainEffects,
  unitBaseStats,
  onClose,
  serverUnits,
  heroAuraFunction,
  playerId
}) => {
  // ✅ État pour les stats avec bonus de forge (DOIT être appelé avant tout return conditionnel)
  const [forgeEnhancedStats, setForgeEnhancedStats] = useState<any>(null);
  
  // ✅ État pour les stats des héros chargées depuis player_heroes.json
  const [heroStatsFromAPI, setHeroStatsFromAPI] = useState<any>(null);

  // ✅ NOUVEAU: État pour les bonus héros
  const [heroBonuses, setHeroBonuses] = useState<{ inAura: boolean; bonuses: any; hero: any } | null>(null);

  // ✅ AJOUT: Hook pour empêcher le zoom (même fonctionnement que popup déploiement)
  usePreventZoom(isOpen);

  // ✅ Charger les stats avec bonus de forge (DOIT être appelé avant tout return conditionnel)
  useEffect(() => {
    const loadForgeStats = async () => {
      if (unit) {
        try {
          // ✅ NOUVEAU: Extraire le type d'unité depuis unitId
          const unitAny = unit as any;
          const possibleUnitId = unitAny.unitId || unitAny.id || unitAny.unit_id;
          let unitType = unitAny.type;
          let extractedPlayerId = playerId; // Utiliser le playerId passé en props d'abord
          
          if (!unitType && possibleUnitId) {
            const parts = possibleUnitId.split('_');
            if (parts[0] === 'hero') {
              unitType = 'hero';
              // ✅ NOUVEAU: Extraire le playerId depuis unitId si pas fourni en props
              if (!extractedPlayerId) {
                extractedPlayerId = parts[1] === 'attacker' ? 'player_3' : 'player_2';  // ✅ CORRECTION: Inverser le mapping
              }
            } else {
              // ✅ CORRECTION: Pour "attacker_player_3_infantry_light_1759082469276_0"
              // On veut extraire "infantry_light" qui est après "player_X"
              let teamIndex = -1;
              for (let i = 0; i < parts.length; i++) {
                if (parts[i] === 'attacker' || parts[i] === 'defender') {
                  teamIndex = i;
                  break;
                }
              }
              
              if (teamIndex !== -1 && parts.length > teamIndex + 2) {
                // teamIndex = 0 (attacker), parts[1] = "player", parts[2] = "3", parts[3] = "slinger"
                
                // ✅ CORRECTION: Reconstruire playerId correctement comme "player_3"
                if (!extractedPlayerId && parts.length > teamIndex + 2) {
                  if (parts[teamIndex + 2].match(/^\d+$/)) {
                    // Format "player_3": reconstruire
                    extractedPlayerId = `${parts[teamIndex + 1]}_${parts[teamIndex + 2]}`;
                    const unitTypeStart = teamIndex + 3; // Après "player_3"
                    const unitTypeParts = [];
                    
                    // Continuer jusqu'à trouver un timestamp ou la fin
                    for (let i = unitTypeStart; i < parts.length; i++) {
                      if (parts[i].match(/^\d{13,}$/)) break; // Arrêter au timestamp
                      unitTypeParts.push(parts[i]);
                    }
                    unitType = unitTypeParts.join('_');
                  } else {
                    // Format simple: playerId directement
                    extractedPlayerId = parts[teamIndex + 1];
                    const unitTypeStart = teamIndex + 2;
                    const unitTypeParts = [];
                    
                    for (let i = unitTypeStart; i < parts.length; i++) {
                      if (parts[i].match(/^\d{13,}$/)) break;
                      unitTypeParts.push(parts[i]);
                    }
                    unitType = unitTypeParts.join('_');
                  }
                }
              }
            }
          }
          
          if (unitType && extractedPlayerId) {
            const enhancedStats = await getUnitStatsWithForgeBonus(unitType, extractedPlayerId);
            setForgeEnhancedStats(enhancedStats);
          }
        } catch (error) {
          console.error('Erreur chargement stats forge pour popup:', error);
          setForgeEnhancedStats(null);
        }
      }
    };
    
    if (isOpen && unit) {
      loadForgeStats();
    }
  }, [isOpen, unit, playerId]);

  // ✅ NOUVEAU: Calculer les bonus héros quand le popup s'ouvre
  useEffect(() => {
    const calculateHeroBonuses = () => {
      if (unit && heroAuraFunction && serverUnits) {
        try {
          const unitAny = unit as any;
          const possibleUnitId = unitAny.unitId || unitAny.id || unitAny.unit_id;
          
          // Trouver la position de l'unité depuis serverUnits (objet plat)
          let unitPosition = null;
          console.log('🔍 [UnitInfoPopup] Recherche unitId:', possibleUnitId);
          console.log('🔍 [UnitInfoPopup] serverUnits structure:', serverUnits);
          
          if (serverUnits && possibleUnitId) {
            // serverUnits est un objet plat {unitId: unit}
            const foundUnit = serverUnits[possibleUnitId];
            if (foundUnit && foundUnit.position) {
              unitPosition = { q: foundUnit.position[0], r: foundUnit.position[1] };
              console.log('✅ [UnitInfoPopup] Position trouvée:', unitPosition);
            } else {
              console.log('❌ [UnitInfoPopup] Unité non trouvée ou sans position:', foundUnit);
            }
          }

          if (unitPosition && heroAuraFunction) {
            console.log('🎯 [UnitInfoPopup] Calcul bonus héros pour:', possibleUnitId, 'à la position:', unitPosition);
            const result = heroAuraFunction(unit, unitPosition);
            console.log('🎯 [UnitInfoPopup] Résultat bonus héros:', result);
            setHeroBonuses(result);
          } else {
            console.log('❌ [UnitInfoPopup] Pas de position ou pas de fonction héros');
            setHeroBonuses({ inAura: false, bonuses: null, hero: null });
          }
        } catch (error) {
          console.error('Erreur calcul bonus héros:', error);
          setHeroBonuses({ inAura: false, bonuses: null, hero: null });
        }
      } else {
        setHeroBonuses(null);
      }
    };

    if (isOpen && unit) {
      calculateHeroBonuses();
    }
  }, [isOpen, unit, heroAuraFunction, serverUnits]);

  // ✅ Charger les stats des héros depuis l'API quand nécessaire
  useEffect(() => {
    const loadHeroStats = async () => {
      if (!isOpen || !unit) {
        setHeroStatsFromAPI(null);
        return;
      }

      const unitAny = unit as any;
      const possibleUnitId = unitAny.unitId || unitAny.id || unitAny.unit_id;
      const unitTypeFromExtract = extractUnitType(possibleUnitId || '');
      
      if (unitTypeFromExtract === 'hero') {
        try {
          // Extraire playerId depuis l'unitId
          let playerId = 'player_1';
          if (possibleUnitId && possibleUnitId.includes('player_')) {
            const playerMatch = possibleUnitId.match(/player_(\d+)/);
            if (playerMatch) {
              playerId = `player_${playerMatch[1]}`;
            }
          }
          
          const response = await fetch(`${getApiUrl()}/api/v2/player_heroes`);
          if (response.ok) {
            const heroesData = await response.json();
            
            if (heroesData[playerId] && heroesData[playerId].heroes) {
              // Extraire l'instance_id depuis l'unitId
              const heroInstanceId = possibleUnitId.match(/hero_hero_(\w+)/)?.[1];
              
              if (heroInstanceId) {
                // Chercher le héros par instance_id dans la structure heroes
                const heroKey = `hero_${heroInstanceId}`;
                const hero = heroesData[playerId].heroes[heroKey];
                
                if (hero) {
                  setHeroStatsFromAPI(hero);
                } else {
                  // Fallback: prendre le premier héros disponible
                  const firstHeroKey = Object.keys(heroesData[playerId].heroes)[0];
                  if (firstHeroKey) {
                    const fallbackHero = heroesData[playerId].heroes[firstHeroKey];
                    setHeroStatsFromAPI(fallbackHero);
                  }
                }
              }
            }
          }
        } catch (error) {
          setHeroStatsFromAPI(null);
        }
      } else {
        setHeroStatsFromAPI(null);
      }
    };

    loadHeroStats();
  }, [isOpen, unit]);

  // ✅ Fonction pour calculer les statistiques totales
  // Calculer les stats totales basées sur le nombre d'unités
  const calculateTotalStats = () => {
    if (!unit || !isOpen) return {
      aliveCount: 0, maxCount: 0, totalHP: 0, maxTotalHP: 0,
      totalAttackMelee: 0, totalDefenseMelee: 0, totalAttackRanged: 0, totalDefenseRanged: 0,
      baseAttackMelee: 0, baseDefenseMelee: 0, finalAttackMelee: 0, finalDefenseMelee: 0,
      forgeEnhancedAttack: 0, forgeEnhancedDefense: 0, forgeEnhancedAttackRanged: 0, forgeEnhancedDefenseRanged: 0,
      hasForgeBonus: false
    };

    const unitAny = unit as any;
    const unitCount = unitAny.unitCount || unitAny.stack || unitAny.count || 0;
    
    // Pour les héros, utiliser max_stack_size = 1 et effectif = 1, pour les autres unités utiliser unit_stats.json
    const maxCount = unitAny.heroData ? 1 : (unitBaseStats?.max_stack_size || unitCount);
    const aliveCount = unitAny.heroData ? 1 : unitCount;
    
    // Détecter si c'est un héros par le type ou par heroData
    const unitAnyForType = unit as any;
    const possibleUnitId = unitAnyForType.unitId || unitAnyForType.id || unitAnyForType.unit_id;
    
    // Utiliser extractUnitType pour détecter correctement les héros
    const unitTypeFromExtract = extractUnitType(possibleUnitId || '');
    const isHero = unitTypeFromExtract === 'hero' || unit.heroData?.calculated_stats;
    

    
    // Si c'est un héros, utiliser les stats depuis player_heroes.json
    if (isHero) {
      if (heroStatsFromAPI) {
        const heroStats = heroStatsFromAPI.calculated_stats || {};
        const currentHP = (unitAnyForType as any).hp || heroStats.hp;
        const maxHP = heroStats.hp;
        
        return {
          aliveCount: 1,
          maxCount: 1,
          totalHP: currentHP,
          maxTotalHP: maxHP,
          totalAttackMelee: heroStats.attack_melee,
          totalDefenseMelee: heroStats.defense_melee,
          totalAttackRanged: 0,
          totalDefenseRanged: heroStats.defense_ranged,
          baseAttackMelee: heroStats.attack_melee,
          baseDefenseMelee: heroStats.defense_melee,
          finalAttackMelee: heroStats.attack_melee,
          finalDefenseMelee: heroStats.defense_melee
        };
      } else {
        // Retourner des valeurs vides si les données ne sont pas encore chargées
        return {
          aliveCount: 1,
          maxCount: 1,
          totalHP: 0,
          maxTotalHP: 0,
          totalAttackMelee: 0,
          totalDefenseMelee: 0,
          totalAttackRanged: 0,
          totalDefenseRanged: 0,
          baseAttackMelee: 0,
          baseDefenseMelee: 0,
          finalAttackMelee: 0,
          finalDefenseMelee: 0
        };
      }
    }
    
    // Pour les unités normales, utiliser unit_stats.json
    if (!unitBaseStats) {
      const baseAttack = unit.attack || 0;
      const baseDefense = unit.defense || 0;
      
      return {
        aliveCount,
        maxCount,
        totalHP: (unit.health || 0),
        totalAttackMelee: baseAttack * aliveCount,
        totalDefenseMelee: baseDefense * aliveCount,
        totalAttackRanged: 0,
        totalDefenseRanged: 0,
        baseAttackMelee: baseAttack,
        baseDefenseMelee: baseDefense,
        finalAttackMelee: baseAttack,
        finalDefenseMelee: baseDefense
      };
    }

    const baseAttack = unitBaseStats.attack_melee || 0;
    const baseDefense = unitBaseStats.defense_melee || 0;
    const baseAttackRanged = unitBaseStats.attack_ranged || 0;
    const baseDefenseRanged = unitBaseStats.defense_ranged || 0;
    
    // ✅ NOUVEAUTÉ : Appliquer d'abord les bonus de forge
    let forgeEnhancedAttack = baseAttack;
    let forgeEnhancedDefense = baseDefense;
    let forgeEnhancedAttackRanged = baseAttackRanged;
    let forgeEnhancedDefenseRanged = baseDefenseRanged;
    
    if (forgeEnhancedStats) {
      forgeEnhancedAttack = forgeEnhancedStats.attack_melee || baseAttack;
      forgeEnhancedDefense = forgeEnhancedStats.defense_melee || baseDefense;
      forgeEnhancedAttackRanged = forgeEnhancedStats.attack_ranged || baseAttackRanged;
      forgeEnhancedDefenseRanged = forgeEnhancedStats.defense_ranged || baseDefenseRanged;
    }
    
    // Appliquer les bonus de forge
    const finalAttack = forgeEnhancedAttack;
    const finalDefense = forgeEnhancedDefense;

    return {
      aliveCount,
      maxCount,
      totalHP: (unitBaseStats.hp || 0) * aliveCount,
      totalAttackMelee: finalAttack * aliveCount,
      totalDefenseMelee: finalDefense * aliveCount,
      totalAttackRanged: forgeEnhancedAttackRanged * aliveCount,
      totalDefenseRanged: forgeEnhancedDefenseRanged * aliveCount,
      baseAttackMelee: baseAttack,
      baseDefenseMelee: baseDefense,
      finalAttackMelee: finalAttack,
      finalDefenseMelee: finalDefense
    };
  };

  // ✅ Calcul des statistiques totales
  const totalStats = calculateTotalStats();

  // ✅ Vérification conditionnelle APRÈS les hooks
  if (!isOpen || !unit) return null;

  const unitAny = unit as any;

  // Extraire les informations de l'unité
  const possibleUnitId = unitAny.unitId || unitAny.id || unitAny.unit_id;
  const unitType = extractUnitType(possibleUnitId || '');

  return (
    <div className="unit-info-overlay" onClick={onClose} onWheel={handleOverlayWheel}>
      <div className="unit-info-popup" onClick={(e) => e.stopPropagation()} onWheel={handleContentWheel}>
        <div className="unit-info-header">
          <h2>{unitBaseStats?.name || unitAny.heroData?.hero_id || unitAny.name || unitType || 'Unité inconnue'}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="unit-info-content">
          {/* Section 1: Stats de base */}
          <div className="info-section">
            <h3>📊 Statistiques de base</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="label">Nom:</span>
                <span className="value">{unitBaseStats?.name || unitAny.heroData?.hero_id || unitType || 'Inconnu'}</span>
              </div>
              <div className="info-item">
                <span className="label">Catégorie:</span>
                <span className="value">{unitBaseStats?.category || unitType}</span>
              </div>
              <div className="info-item">
                <span className="label">Joueur:</span>
                <span className="value team-color" data-player={extractUnitInfo(possibleUnitId).playerId}>
                  {extractUnitInfo(possibleUnitId).playerId || 'Inconnu'}
                </span>
              </div>
              <div className="info-item">
                <span className="label">Équipe:</span>
                <span className="value team-color" data-team={extractUnitInfo(possibleUnitId).team}>
                  {extractUnitInfo(possibleUnitId).team}
                </span>
              </div>
              {unit.heroData && (
                <div className="info-item">
                  <span className="label">Niveau:</span>
                  <span className="value">{unit.heroData.current_level}</span>
                </div>
              )}
              <div className="info-item">
                <span className="label">Nombre:</span>
                <span className="value">{totalStats.aliveCount}/{totalStats.maxCount}</span>
              </div>
              <div className="info-item">
                <span className="label">PV totaux:</span>
                <span className="value">
                  {heroStatsFromAPI ? (
                    formatCalculation(totalStats.totalHP, totalStats.aliveCount, totalStats.totalHP)
                  ) : (
                    formatCalculation(unitBaseStats?.hp || 'N/A', totalStats.aliveCount, totalStats.totalHP)
                  )}
                </span>
              </div>
              <div className="info-item">
                <span className="label">Attaque mêlée:</span>
                <span className="value">
                  {heroStatsFromAPI ? 
                    formatCalculation(totalStats.baseAttackMelee, totalStats.aliveCount, totalStats.totalAttackMelee) :
                    // Affichage avec bonus de forge et aura
                    totalStats.baseAttackMelee !== totalStats.finalAttackMelee ?
                      formatComplexCalculation(`${totalStats.baseAttackMelee} → ${totalStats.finalAttackMelee} × ${totalStats.aliveCount} = ${totalStats.totalAttackMelee} 🎖️`, totalStats.aliveCount) :
                      formatCalculation(totalStats.baseAttackMelee || 'N/A', totalStats.aliveCount, totalStats.totalAttackMelee)
                  }
                </span>
              </div>
              <div className="info-item">
                <span className="label">Défense mêlée:</span>
                <span className="value">
                  {heroStatsFromAPI ? 
                    formatCalculation(totalStats.baseDefenseMelee, totalStats.aliveCount, totalStats.totalDefenseMelee) :
                    // Affichage avec bonus de forge et aura
                    totalStats.baseDefenseMelee !== totalStats.finalDefenseMelee ?
                      formatComplexCalculation(`${totalStats.baseDefenseMelee} → ${totalStats.finalDefenseMelee} × ${totalStats.aliveCount} = ${totalStats.totalDefenseMelee} 🎖️`, totalStats.aliveCount) :
                      formatCalculation(totalStats.baseDefenseMelee || 'N/A', totalStats.aliveCount, totalStats.totalDefenseMelee)
                  }
                </span>
              </div>
              <div className="info-item">
                <span className="label">Attaque à distance:</span>
                <span className="value">
                  {heroStatsFromAPI ? 
                    formatCalculation(0, totalStats.aliveCount, 0) :
                    unit.heroData?.calculated_stats ? 
                      formatCalculation(0, totalStats.aliveCount, 0) :
                      // ✅ NOUVEAUTÉ : Affichage avec bonus de forge pour attaque à distance
                      totalStats.hasForgeBonus && totalStats.forgeEnhancedAttackRanged > (unitBaseStats?.attack_ranged || 0) ?
                        formatComplexCalculation(`${unitBaseStats?.attack_ranged || 0} + bonus forge → ${totalStats.forgeEnhancedAttackRanged} × ${totalStats.aliveCount} = ${totalStats.totalAttackRanged}`, totalStats.aliveCount) :
                        formatCalculation(unitBaseStats?.attack_ranged || 'N/A', totalStats.aliveCount, totalStats.totalAttackRanged)
                  }
                </span>
              </div>
              <div className="info-item">
                <span className="label">Défense à distance:</span>
                <span className="value">
                  {heroStatsFromAPI ? 
                    formatCalculation(heroStatsFromAPI.calculated_stats?.defense_ranged || 0, totalStats.aliveCount, totalStats.totalDefenseRanged) :
                    unit.heroData?.calculated_stats ? 
                      formatCalculation(unit.heroData.calculated_stats.defense_ranged || 0, totalStats.aliveCount, totalStats.totalDefenseRanged) :
                      // ✅ NOUVEAUTÉ : Affichage avec bonus de forge pour défense à distance
                      totalStats.hasForgeBonus && totalStats.forgeEnhancedDefenseRanged > (unitBaseStats?.defense_ranged || 0) ?
                        formatComplexCalculation(`${unitBaseStats?.defense_ranged || 0} + bonus forge → ${totalStats.forgeEnhancedDefenseRanged} × ${totalStats.aliveCount} = ${totalStats.totalDefenseRanged}`, totalStats.aliveCount) :
                        formatCalculation(unitBaseStats?.defense_ranged || 'N/A', totalStats.aliveCount, totalStats.totalDefenseRanged)
                  }
                </span>
              </div>
              <div className="info-item">
                <span className="label">Portée:</span>
                <span className="value">
                  {unit.heroData ? 
                    unit.heroData.calculated_stats?.range || 1 :
                    unitBaseStats?.range || 1
                  }
                </span>
              </div>
              <div className="info-item">
                <span className="label">Mouvement:</span>
                <span className="value">
                  {unit.heroData ? 
                    unit.heroData.calculated_stats?.movement || 0 :
                    unitBaseStats?.movement || unit.movement || 0
                  }
                </span>
              </div>
            </div>

            {/* Capacités spéciales */}
            {unitBaseStats?.special_abilities && unitBaseStats.special_abilities.length > 0 && (
              <div className="special-abilities">
                <h4>⚡ Capacités spéciales:</h4>
                <ul>
                  {unitBaseStats.special_abilities.map((ability: any, index: number) => (
                    <li key={index}>
                      <strong>vs {ability.target_category}:</strong>
                      {ability.attack_melee && ` Attaque ${ability.attack_melee}`}
                      {ability.defense_melee && ` Défense ${ability.defense_melee}`}
                      {ability.attack_ranged && ` Attaque distance ${ability.attack_ranged}`}
                      {ability.defense_ranged && ` Défense distance ${ability.defense_ranged}`}
                      {ability.morale_bonus && ` Moral ${ability.morale_bonus}`}
                      {ability.first_strike && ` Frappe en premier`}
                      {ability.area_damage && ` Dégâts de zone`}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Section 2: Caractéristiques terrain */}
          <div className="info-section">
            <h3>🌍 Effets du terrain</h3>
            {terrainEffects ? (
              <div className="info-grid">
                <div className="info-item">
                  <span className="label">Terrain:</span>
                  <span className="value">{terrainEffects.terrain_name}</span>
                </div>
                <div className="info-item">
                  <span className="label">Bonus attaque:</span>
                  <span className={`value ${terrainEffects.attack_bonus > 0 ? 'positive' : terrainEffects.attack_bonus < 0 ? 'negative' : ''}`}>
                    {terrainEffects.attack_bonus > 0 ? '+' : ''}{terrainEffects.attack_bonus}%
                  </span>
                </div>
                <div className="info-item">
                  <span className="label">Bonus défense:</span>
                  <span className={`value ${terrainEffects.defense_bonus > 0 ? 'positive' : terrainEffects.defense_bonus < 0 ? 'negative' : ''}`}>
                    {terrainEffects.defense_bonus > 0 ? '+' : ''}{terrainEffects.defense_bonus}%
                  </span>
                </div>
                <div className="info-item">
                  <span className="label">Coût mouvement:</span>
                  <span className="value">×{terrainEffects.movement_cost}</span>
                </div>
              </div>
            ) : (
              <p className="no-data">Aucune information de terrain disponible</p>
            )}
          </div>

          {/* Section 3: Bonus Héros */}
          {heroBonuses && (
            <div className="info-section">
              <h3>⚔️ Bonus Héros</h3>
              {heroBonuses.inAura && heroBonuses.bonuses ? (
                <div className="info-grid">
                  <div className="info-item">
                    <span className="label">Héros:</span>
                    <span className="value hero-name">{heroBonuses.hero?.name || 'Héros'}</span>
                  </div>
                  {heroBonuses.bonuses.offensive_bonus && heroBonuses.bonuses.offensive_bonus > 0 && (
                    <div className="info-item">
                      <span className="label">Bonus attaque:</span>
                      <span className="value positive">+{heroBonuses.bonuses.offensive_bonus}%</span>
                    </div>
                  )}
                  {heroBonuses.bonuses.defensive_bonus && heroBonuses.bonuses.defensive_bonus > 0 && (
                    <div className="info-item">
                      <span className="label">Bonus défense:</span>
                      <span className="value positive">+{heroBonuses.bonuses.defensive_bonus}%</span>
                    </div>
                  )}
                  {heroBonuses.bonuses.movement_bonus && heroBonuses.bonuses.movement_bonus > 0 && (
                    <div className="info-item">
                      <span className="label">Bonus mouvement:</span>
                      <span className="value positive">+{heroBonuses.bonuses.movement_bonus}</span>
                    </div>
                  )}
                  {heroBonuses.bonuses.moral_bonus && heroBonuses.bonuses.moral_bonus > 0 && (
                    <div className="info-item">
                      <span className="label">Bonus moral:</span>
                      <span className="value positive">+{heroBonuses.bonuses.moral_bonus}%</span>
                    </div>
                  )}
                  <div className="info-item">
                    <span className="label">Portée aura:</span>
                    <span className="value">{heroBonuses.bonuses.aura_radius} case(s)</span>
                  </div>
                </div>
              ) : (
                <p className="no-data">Aucun héros à proximité</p>
              )}
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default UnitInfoPopup;

