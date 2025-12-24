import React, { useState, useEffect } from 'react';
import './CombatPopup.css';
import { getUnitStatsWithForgeBonus } from '../utils/combatUtils';
import usePreventZoom, { handleOverlayWheel, handleContentWheel } from '../hooks/usePreventZoom';

interface TerrainDefinition {
  name: string;
  defenseBonus: number;
  attackPenalty: number;
  movementBonus: number;
}

interface UnitStats {
  type: string;
  name: string;
  count: number;
  hp: number;
  attack_melee: number;
  defense_melee: number;
  attack_ranged: number;
  defense_ranged: number;
  range?: number;
  category: string;
  special_abilities: Array<{
    target_category: string;
    attack_melee?: string;
    defense_melee?: string;
    attack_ranged?: string;
    defense_ranged?: string;
    morale_bonus?: string;
    first_strike?: boolean;
    area_damage?: boolean;
  }>;
  // 🆕 Informations sur les bonus de héros appliqués
  heroBonusesApplied?: {
    offensive_bonus?: number;
    defensive_bonus?: number;
    movement_bonus?: number;
  };
  // 🆕 Stats de base (avant bonus) pour affichage détaillé
  baseStats?: {
    attack_melee: number;
    defense_melee: number;
    attack_ranged?: number;
    defense_ranged?: number;
  };
}

interface HeroAuraResult {
  inAura: boolean;
  hero: { id: any; name: string } | null;
  bonuses: any | null;
  distance?: number;
}

interface CombatCalculation {
  baseAttack: number;
  terrainBonus: number;
  contextualBonus: number;
  moralMultiplier: number;
  chanceMultiplier: number;
  totalAttack: number;
  
  baseDefense: number;
  terrainDefenseBonus: number;
  contextualDefenseBonus: number;
  moralDefenseMultiplier: number;
  chanceDefenseMultiplier: number;
  totalDefense: number;
  
  damage: number;
  remainingHP: number;
  survivingUnits: number;
  isDefenderHero?: boolean; // ✅ NOUVEAU : Indiquer si le défenseur est un héros
  
  log: string[];
}

interface CombatPopupProps {
  isOpen: boolean;
  attacker: UnitStats | null;
  defender: UnitStats | null;
  attackerPosition: { q: number; r: number } | null;
  defenderPosition: { q: number; r: number } | null;
  terrainAttacker: string;
  terrainDefender: string;
  onConfirmCombat: (result: CombatCalculation) => void;
  onCancel: () => void;
  // Nouvelles props pour le serveur
  battlefieldId?: string;
  attackerId?: string;
  defenderId?: string;
  currentRound?: number;
  // ✅ NOUVEAUTÉ : Fonction pour calculer les auras en temps réel
  isInHeroAura?: (unit: any, position: { q: number; r: number }) => HeroAuraResult;
  attackerUnit?: any; // Unité complète de l'attaquant (Unit ou CompactUnit)
  defenderUnit?: any; // Unité complète du défenseur (Unit ou CompactUnit)
  battleParticipants?: { attacker_id: string; defender_id: string }; // ✅ IDs réels des participants
}

const CombatPopup: React.FC<CombatPopupProps> = ({
  isOpen,
  attacker,
  defender,
  attackerPosition,
  defenderPosition,
  terrainAttacker,
  terrainDefender,
  onConfirmCombat,
  onCancel,
  battlefieldId,
  attackerId,
  defenderId,
  currentRound,
  isInHeroAura,
  attackerUnit,
  defenderUnit,
  battleParticipants
}) => {
  const [calculation, setCalculation] = useState<CombatCalculation | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [combatExecuted, setCombatExecuted] = useState(false); // Nouvel état pour empêcher le retour en arrière
  const [battleMoral, setBattleMoral] = useState<{attacker: number, defender: number}>({attacker: 100, defender: 100});
  const [terrainDefinitions, setTerrainDefinitions] = useState<{[key: string]: TerrainDefinition} | null>(null);

  // Verrouiller le scroll du battlefield quand le popup est ouvert
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  // 🔒 Empêcher le scroll du background sur mobile lors du drag du popup
  useEffect(() => {
    if (!isOpen) return;

    const preventScroll = (e: TouchEvent) => {
      // Empêcher le scroll du body/background
      if (e.target === document.body || !(e.target as HTMLElement).closest('.combat-popup')) {
        e.preventDefault();
      }
    };

    // Ajouter l'écouteur avec { passive: false } pour pouvoir preventDefault()
    document.addEventListener('touchmove', preventScroll, { passive: false });

    return () => {
      document.removeEventListener('touchmove', preventScroll);
    };
  }, [isOpen]);

  // Charger les données de bataille (moral + terrainDefinitions)
  useEffect(() => {
    if (isOpen && battlefieldId) {
      const fetchBattlefieldData = async () => {
        try {
          // Essayer d'abord l'API battlefield V2 complète
          const response = await fetch(`/api/military/battlefield_v2/${battlefieldId}`);
          if (response.ok) {
            const data = await response.json();
            
            // Moral de bataille
            if (data.success && data.battlefield?.forces) {
              const forces = data.battlefield.forces;
              const calculateMoral = (players: any) => {
                const morals = Object.values(players || {})
                  .map((player: any) => player.moral)
                  .filter(Boolean) as number[];
                return morals.length > 0 
                  ? Math.round(morals.reduce((a, b) => a + b, 0) / morals.length) 
                  : 100;
              };
              
              setBattleMoral({
                attacker: calculateMoral(forces.attackers),
                defender: calculateMoral(forces.defenders)
              });
            }
            
            // Définitions de terrain
            const terrainDefs = data.battlefield?.map_data?.terrainDefinitions || 
                              data.battlefield?.terrainDefinitions;
            if (terrainDefs) {
              setTerrainDefinitions(terrainDefs);
              return; // Succès complet
            }
          }
          
          // Fallback: API spécialisée terrain si pas dans battlefield V2
          if (!terrainDefinitions) {
            const terrainResponse = await fetch(`/api/battlefield/terrain-definitions/${battlefieldId}`);
            if (terrainResponse.ok) {
              const terrainData = await terrainResponse.json();
              if (terrainData.success && terrainData.terrainDefinitions) {
                setTerrainDefinitions(terrainData.terrainDefinitions);
              }
            }
          }
        } catch (error) {
          console.warn(`⚠️ Erreur chargement données battlefield ${battlefieldId}:`, error);
        }
      };
      
      fetchBattlefieldData();
    }
  }, [isOpen, battlefieldId]);

  // Fonction pour extraire le player ID depuis les données d'unité
  const getActualPlayerId = (unitId: string, isAttacker: boolean): string => {
    // ✅ UTILISER LES VRAIS IDs depuis battleParticipants si disponible
    if (battleParticipants) {
      return isAttacker ? battleParticipants.attacker_id : battleParticipants.defender_id;
    }
    
    // Essayer d'extraire depuis l'unitId d'abord (fallback legacy)
    if (unitId) {
      // Regex pour extraire player_X depuis l'ID
      const playerMatch = unitId.match(/player_(\d+)/);
      if (playerMatch) return `player_${playerMatch[1]}`;
    }
    
    // Dernière solution: fallback basé sur attackerId/defenderId en props
    if (isAttacker && attackerId) return attackerId;
    if (!isAttacker && defenderId) return defenderId;
    
    // Valeur par défaut (ne devrait jamais arriver)
    return isAttacker ? 'unknown_attacker' : 'unknown_defender';
  };

  // Fonction pour enrichir les stats d'une unité avec les bonus de forge
  const getEnhancedUnitStats = async (unit: UnitStats, playerId: string): Promise<UnitStats> => {
    try {
      // Récupérer les stats avec bonus de forge
      const enhancedStats = await getUnitStatsWithForgeBonus(unit.type, playerId);
      
      if (enhancedStats) {
        // Appliquer les bonus de forge aux stats de base
        const result = {
          ...unit,
          // Utiliser les stats améliorées si disponibles
          attack_melee: enhancedStats.attack_melee || unit.attack_melee,
          defense_melee: enhancedStats.defense_melee || unit.defense_melee,
          attack_ranged: enhancedStats.attack_ranged || unit.attack_ranged,
          defense_ranged: enhancedStats.defense_ranged || unit.defense_ranged,
          // Garder les stats originales pour comparaison
          baseStats: {
            attack_melee: unit.attack_melee,
            defense_melee: unit.defense_melee,
            attack_ranged: unit.attack_ranged,
            defense_ranged: unit.defense_ranged,
          }
        };
        
        return result;
      }
    } catch (error) {
      // Erreur silencieuse
    }
    
    // Retourner l'unité originale si erreur ou pas de bonus
    return {
      ...unit,
      baseStats: {
        attack_melee: unit.attack_melee,
        defense_melee: unit.defense_melee,
        attack_ranged: unit.attack_ranged,
        defense_ranged: unit.defense_ranged,
      }
    };
  };

  // Calcul des points de combat
  const calculateCombat = (att: UnitStats, def: UnitStats): CombatCalculation => {
    
    // ✅ PROTECTION CONTRE NaN : Valider toutes les données d'entrée
    const safeAtt = {
      ...att,
      count: att.count || 1,
      attack_melee: att.attack_melee || 0,
      defense_melee: att.defense_melee || 0,
      hp: att.hp || 100
    };
    
    const safeDef = {
      ...def,
      count: def.count || 1,
      attack_melee: def.attack_melee || 0,
      defense_melee: def.defense_melee || 0,
      hp: def.hp || 100
    };
    
    const log: string[] = [];
    
    // === CALCUL ATTAQUE ===
    // 🆕 Déterminer le type de combat de l'attaquant
    const attackerCombatType = getPrimaryCombatType(safeAtt);
    const isRangedAttack = attackerCombatType === 'ranged';
    
    // ✅ NOUVEAUTÉ : Calculer les bonus d'aura en temps réel
    let baseAttackStat = isRangedAttack ? safeAtt.attack_ranged : safeAtt.attack_melee;
    let baseAttackFromBase = isRangedAttack 
      ? (safeAtt.baseStats?.attack_ranged || safeAtt.attack_ranged)
      : (safeAtt.baseStats?.attack_melee || safeAtt.attack_melee);
    let heroOffensiveBonus = 0;
    
    // Utiliser les stats améliorées par la forge pour le calcul de base
    const baseAttack = safeAtt.count * baseAttackStat;
    const attackTypeLabel = isRangedAttack ? '🏹' : '🗡️';
    const attackTypeText = isRangedAttack ? 'à distance' : 'mêlée';
    log.push(`${attackTypeLabel} Attaque ${attackTypeText}: ${safeAtt.count} × ${baseAttackStat} = ${baseAttack}`);
    
    // Afficher les bonus de forge s'ils sont présents
    if (safeAtt.baseStats && baseAttackFromBase !== baseAttackStat) {
      const forgeBonus = baseAttackStat - baseAttackFromBase;
      const forgeBonusPercent = Math.round((forgeBonus / baseAttackFromBase) * 100);
      log.push(`⚒️ Bonus forge attaque ${attackTypeText}: +${forgeBonusPercent}% (+${forgeBonus.toFixed(1)}) = ${baseAttackStat.toFixed(1)}`);
    }
    
    // Calcul en temps réel de l'aura pour l'attaquant
    if (isInHeroAura && attackerUnit && attackerPosition) {
      const attackerAura = isInHeroAura(attackerUnit, attackerPosition);
      if (attackerAura.inAura && attackerAura.bonuses) {
        heroOffensiveBonus = attackerAura.bonuses.offensive_bonus || 0;
        log.push(`🎖️ Aura de ${attackerAura.hero?.name || 'Héros'} détectée (bonus offensif: +${heroOffensiveBonus}%)`);
      }
    } else if (safeAtt.heroBonusesApplied?.offensive_bonus) {
      // Fallback: utiliser les données statiques si pas de calcul temps réel disponible
      heroOffensiveBonus = safeAtt.heroBonusesApplied.offensive_bonus;
    }
    
    // Ajouter bonus de héros si présent
    let attackWithHero = baseAttack;
    if (heroOffensiveBonus > 0) {
      const heroAttackBonus = Math.round(baseAttack * (heroOffensiveBonus / 100));
      attackWithHero = baseAttack + heroAttackBonus;
      log.push(`🎖️ Bonus héros (+${heroOffensiveBonus}%): +${heroAttackBonus} = ${attackWithHero}`);
    }
    

    
    // Bonus terrain d'attaque
    const terrainBonusPercent = getTerrainAttackBonus(terrainAttacker);
    const terrainBonus = attackWithHero * (terrainBonusPercent / 100);
    const attackWithTerrain = attackWithHero + terrainBonus;
    
    const terrainStatus = !terrainDefinitions ? '❌ Définitions manquantes' : 
                         terrainBonusPercent === 0 ? 'neutre' : 
                         `${terrainBonusPercent > 0 ? '+' : ''}${terrainBonusPercent}%`;
    log.push(`🏞️ Terrain ${terrainAttacker}: ${terrainStatus}${terrainBonus !== 0 ? ` = ${terrainBonus > 0 ? '+' : ''}${terrainBonus.toFixed(1)}` : ''}`);
    
    // Bonus contextuel spécialisé (ex: piquier vs cavalerie, archer vs infanterie)
    const contextualBonusPercent = getContextualBonus(safeAtt, safeDef, 'attack', attackerCombatType);
    const contextualBonus = attackWithHero * (contextualBonusPercent / 100);
    const attackWithContextual = attackWithTerrain + contextualBonus;
    if (contextualBonusPercent !== 0) {
      const bonusSign = contextualBonusPercent > 0 ? '+' : '';
      log.push(`⚔️ Bonus spécialisé vs ${safeDef.category}: ${bonusSign}${contextualBonusPercent}% = ${bonusSign}${contextualBonus.toFixed(1)}`);
    }
    
    // Moral (appliqué à 50% du total) - ✅ CORRECTION : Utiliser le moral dynamique
    const moralPercent = battleMoral.attacker;
    const moralMultiplier = moralPercent / 100; // Convertir pourcentage en multiplicateur
    const moralBonus = attackWithContextual * 0.5 * moralMultiplier;
    log.push(`🛡️ Moral (${moralMultiplier.toFixed(2)}): 50% × ${moralMultiplier.toFixed(2)} = +${moralBonus.toFixed(1)}`);
    
    // Chance (appliquée à 50% du total)
    const chanceMultiplier = Math.random() * 0.4 + 0.8; // Entre 0.8 et 1.2
    const chanceBonus = attackWithContextual * 0.5 * chanceMultiplier;
    log.push(`🎲 Chance (${chanceMultiplier.toFixed(2)}): 50% × ${chanceMultiplier.toFixed(2)} = +${chanceBonus.toFixed(1)}`);
    
    const totalAttack = attackWithContextual + moralBonus + chanceBonus;
    log.push(`**📊 Total Attaque: ${totalAttack.toFixed(1)}**`);
    log.push(''); // Saut de ligne
    
    // === CALCUL DÉFENSE ===
    // 🆕 Utiliser la défense correspondant au type d'attaque
    let baseDefenseStat = isRangedAttack ? safeDef.defense_ranged : safeDef.defense_melee;
    let baseDefenseFromBase = isRangedAttack 
      ? (safeDef.baseStats?.defense_ranged || safeDef.defense_ranged)
      : (safeDef.baseStats?.defense_melee || safeDef.defense_melee);
    let heroDefensiveBonus = 0;
    
    // Utiliser les stats améliorées par la forge pour le calcul de base
    const baseDefense = safeDef.count * baseDefenseStat;
    const defenseTypeText = isRangedAttack ? 'à distance' : 'mêlée';
    log.push(`🛡️ Défense ${defenseTypeText}: ${safeDef.count} × ${baseDefenseStat} = ${baseDefense}`);
    
    // Afficher les bonus de forge s'ils sont présents
    if (safeDef.baseStats && baseDefenseFromBase !== baseDefenseStat) {
      const forgeBonus = baseDefenseStat - baseDefenseFromBase;
      const forgeBonusPercent = Math.round((forgeBonus / baseDefenseFromBase) * 100);
      log.push(`⚒️ Bonus forge défense ${defenseTypeText}: +${forgeBonusPercent}% (+${forgeBonus.toFixed(1)}) = ${baseDefenseStat.toFixed(1)}`);
    }
    
    // Calcul en temps réel de l'aura pour le défenseur
    if (isInHeroAura && defenderUnit && defenderPosition) {
      const defenderAura = isInHeroAura(defenderUnit, defenderPosition);
      if (defenderAura.inAura && defenderAura.bonuses) {
        heroDefensiveBonus = defenderAura.bonuses.defensive_bonus || 0;
        log.push(`🎖️ Aura de ${defenderAura.hero?.name || 'Héros'} détectée (bonus défensif: +${heroDefensiveBonus}%)`);
      }
    } else if (safeDef.heroBonusesApplied?.defensive_bonus) {
      // Fallback: utiliser les données statiques si pas de calcul temps réel disponible
      heroDefensiveBonus = safeDef.heroBonusesApplied.defensive_bonus;
    }
    
    // Ajouter bonus de héros si présent
    let defenseWithHero = baseDefense;
    if (heroDefensiveBonus > 0) {
      const heroDefenseBonus = Math.round(baseDefense * (heroDefensiveBonus / 100));
      defenseWithHero = baseDefense + heroDefenseBonus;
      log.push(`🎖️ Bonus héros (+${heroDefensiveBonus}%): +${heroDefenseBonus} = ${defenseWithHero}`);
    }
    
    // Bonus terrain de défense
    const terrainDefenseBonusPercent = getTerrainDefenseBonus(terrainDefender);
    const terrainDefenseBonus = defenseWithHero * (terrainDefenseBonusPercent / 100);
    const defenseWithTerrain = defenseWithHero + terrainDefenseBonus;
    
    const defenseTerrainStatus = !terrainDefinitions ? '❌ Définitions manquantes' :
                                terrainDefenseBonusPercent === 0 ? 'neutre' :
                                `+${terrainDefenseBonusPercent}%`;
    log.push(`🏞️ Terrain ${terrainDefender}: ${defenseTerrainStatus}${terrainDefenseBonus !== 0 ? ` = +${terrainDefenseBonus.toFixed(1)}` : ''}`);
    
    // Bonus contextuel défensif (défenseur peut avoir des bonus vs le type d'attaquant)
    const defenderCombatType = getPrimaryCombatType(safeDef);
    const contextualDefenseBonusPercent = getContextualBonus(safeDef, safeAtt, 'defense', defenderCombatType);
    const contextualDefenseBonus = defenseWithHero * (contextualDefenseBonusPercent / 100);
    const defenseWithContextual = defenseWithTerrain + contextualDefenseBonus;
    if (contextualDefenseBonusPercent !== 0) {
      const bonusSign = contextualDefenseBonusPercent > 0 ? '+' : '';
      log.push(`⚔️ Bonus défensif vs ${safeAtt.category}: ${bonusSign}${contextualDefenseBonusPercent}% = ${bonusSign}${contextualDefenseBonus.toFixed(1)}`);
    }
    
    // Moral défense - ✅ CORRECTION : Utiliser le moral dynamique du défenseur
    const moralDefensePercent = battleMoral.defender;
    const moralDefenseMultiplier = moralDefensePercent / 100; // Convertir pourcentage en multiplicateur
    const moralDefenseBonus = defenseWithContextual * 0.5 * moralDefenseMultiplier;
    log.push(`🛡️ Moral défense (${moralDefenseMultiplier.toFixed(2)}): 50% × ${moralDefenseMultiplier.toFixed(2)} = +${moralDefenseBonus.toFixed(1)}`);
    
    // Chance défense
    const chanceDefenseMultiplier = Math.random() * 0.4 + 0.8;
    const chanceDefenseBonus = defenseWithContextual * 0.5 * chanceDefenseMultiplier;
    log.push(`🎲 Chance défense (${chanceDefenseMultiplier.toFixed(2)}): 50% × ${chanceDefenseMultiplier.toFixed(2)} = +${chanceDefenseBonus.toFixed(1)}`);
    
    const totalDefense = defenseWithContextual + moralDefenseBonus + chanceDefenseBonus;
    log.push(`**📊 Total Défense: ${totalDefense.toFixed(1)}**`);
    log.push(''); // Saut de ligne
    
    // === CALCUL DÉGÂTS ===
    const damage = Math.max(1, totalAttack - totalDefense);
    const totalHP = safeDef.count * safeDef.hp;
    const remainingHP = Math.max(0, totalHP - damage);
    
    // ✅ NOUVELLE LOGIQUE : Différencier héros vs unités classiques
    const isDefenderHero = safeDef.type === 'hero' || safeDef.category === 'hero' || safeDef.count === 1;
    
    let survivingUnits;
    let finalRemainingHP;
    
    if (isDefenderHero) {
      // 🦸‍♂️ LOGIQUE HÉROS : Le héros garde ses HP restants, ne meurt pas instantanément
      survivingUnits = remainingHP > 0 ? 1 : 0;
      finalRemainingHP = Math.round(remainingHP);
      
      log.push(`💥 Dégâts infligés: ${totalAttack.toFixed(1)} - ${totalDefense.toFixed(1)} = ${damage.toFixed(1)}`);
      log.push(`❤️ HP héros restants: ${totalHP} - ${damage.toFixed(1)} = ${finalRemainingHP}`);
      
      if (finalRemainingHP > 0) {
        log.push(`🦸‍♂️ Héros survivant: ${finalRemainingHP}/${totalHP} HP`);
      } else {
        log.push(`💀 Héros éliminé (0 HP)`);
      }
    } else {
      // 👥 LOGIQUE UNITÉS CLASSIQUES : Calcul normal par unités
      survivingUnits = Math.floor(remainingHP / safeDef.hp);
      finalRemainingHP = remainingHP;
      
      log.push(`💥 Dégâts infligés: ${totalAttack.toFixed(1)} - ${totalDefense.toFixed(1)} = ${damage.toFixed(1)}`);
      log.push(`❤️ HP restants: ${totalHP} - ${damage.toFixed(1)} = ${remainingHP.toFixed(1)}`);
      log.push(`**👥 Unités survivantes: ${survivingUnits}/${safeDef.count}**`);
    }
    
    return {
      baseAttack,
      terrainBonus,
      contextualBonus,
      moralMultiplier,
      chanceMultiplier,
      totalAttack,
      baseDefense,
      terrainDefenseBonus,
      contextualDefenseBonus,
      moralDefenseMultiplier,
      chanceDefenseMultiplier,
      totalDefense,
      damage,
      remainingHP: finalRemainingHP, // Utiliser les HP finaux calculés
      survivingUnits,
      isDefenderHero, // ✅ NOUVEAU : Indiquer si c'est un héros
      log
    };
  };

  // Fonction utilitaire pour trouver une définition de terrain
  const findTerrainDefinition = (terrain: string): TerrainDefinition | null => {
    if (!terrainDefinitions) return null;
    
    // Essayer par nom direct puis par clé
    return Object.values(terrainDefinitions).find(def => def.name === terrain) ||
           terrainDefinitions[terrain] ||
           null;
  };

  // Bonus de terrain pour l'attaque
  const getTerrainAttackBonus = (terrain: string): number => {
    const terrainDef = findTerrainDefinition(terrain);
    return terrainDef ? -terrainDef.attackPenalty : 0;
  };

  // Bonus de terrain pour la défense
  const getTerrainDefenseBonus = (terrain: string): number => {
    const terrainDef = findTerrainDefinition(terrain);
    return terrainDef ? terrainDef.defenseBonus : 0;
  };

  // Fonction pour déterminer le type de combat principal d'une unité
  const getPrimaryCombatType = (unit: UnitStats): 'melee' | 'ranged' => {
    // Si l'attaque à distance est significativement supérieure à l'attaque mêlée, c'est une unité à distance
    if (unit.attack_ranged > unit.attack_melee * 1.5) {
      return 'ranged';
    }
    // Si les deux sont similaires mais que l'unité a une portée > 1, privilégier ranged
    if (unit.range && unit.range > 1 && unit.attack_ranged >= unit.attack_melee) {
      return 'ranged';
    }
    // Sinon c'est du corps à corps
    return 'melee';
  };

  // Fonction pour obtenir les bonus contextuels des special_abilities
  const getContextualBonus = (attacker: UnitStats, defender: UnitStats, type: 'attack' | 'defense', combatType?: 'melee' | 'ranged'): number => {
    if (!attacker.special_abilities || !Array.isArray(attacker.special_abilities)) {
      return 0;
    }
    
    // Si le type de combat n'est pas spécifié, le détecter automatiquement
    const actualCombatType = combatType || getPrimaryCombatType(attacker);
    
    for (const ability of attacker.special_abilities) {
      // Vérifier si le bonus s'applique à cette cible
      if (ability.target_category === defender.category || ability.target_category === 'all') {
        // Déterminer la clé du bonus selon le type et le mode de combat
        let bonusKey: string;
        if (type === 'attack') {
          bonusKey = actualCombatType === 'ranged' ? 'attack_ranged' : 'attack_melee';
        } else {
          bonusKey = actualCombatType === 'ranged' ? 'defense_ranged' : 'defense_melee';
        }
        
        const bonusValue = (ability as any)[bonusKey];
        if (bonusValue) {
          // Convertir "+25%" en 25 ou "-15%" en -15
          return parseInt(bonusValue.replace('%', '').replace('+', ''));
        }
      }
    }
    return 0;
  };

  // Fonction pour obtenir les détails des bonus actifs (pour l'affichage)
  const getActiveBonuses = (attacker: UnitStats, defender: UnitStats): Array<{type: string, bonus: number, description: string}> => {
    const bonuses: Array<{type: string, bonus: number, description: string}> = [];
    
    if (!attacker.special_abilities || !Array.isArray(attacker.special_abilities)) {
      return bonuses;
    }
    
    for (const ability of attacker.special_abilities) {
      if (ability.target_category === defender.category || ability.target_category === 'all') {
        // Vérifier tous les types de bonus
        const bonusTypes = ['attack_melee', 'defense_melee', 'attack_ranged', 'defense_ranged'];
        
        for (const bonusType of bonusTypes) {
          const bonusValue = (ability as any)[bonusType];
          if (bonusValue) {
            const numericBonus = parseInt(bonusValue.replace('%', '').replace('+', ''));
            const description = `${attacker.name || attacker.type} vs ${defender.category}`;
            bonuses.push({
              type: bonusType,
              bonus: numericBonus,
              description
            });
          }
        }
      }
    }
    
    return bonuses;
  };

  useEffect(() => {
    if (isOpen && attacker && defender) {
      // Ne réinitialiser que si aucun combat n'a été exécuté dans cette session
      if (!combatExecuted) {
        setCalculation(null); // Réinitialiser le calcul précédent seulement si pas de combat
        setIsCalculating(false);
      }
    }
    
    // Réinitialiser l'état du combat exécuté quand le popup se ferme
    if (!isOpen) {
      setCombatExecuted(false);
    }
  }, [isOpen, attacker, defender, combatExecuted]);

  // Fonction pour lancer le combat au clic du bouton
  const handleLaunchCombat = async () => {
    if (!attacker || !defender || combatExecuted) return; // Empêcher de relancer si déjà exécuté
    

    setIsCalculating(true);
    setCombatExecuted(true); // Marquer le combat comme exécuté
    
    // Extraire les vrais player IDs
    const realAttackerId = getActualPlayerId(attackerId || '', true);
    const realDefenderId = getActualPlayerId(defenderId || '', false);
    
    // Appliquer les bonus de forge aux unités
    const enhancedAttacker = await getEnhancedUnitStats(attacker, realAttackerId);
    const enhancedDefender = await getEnhancedUnitStats(defender, realDefenderId);

    
    // Simuler un délai de calcul pour l'effet visuel
    setTimeout(() => {
      const calc = calculateCombat(enhancedAttacker, enhancedDefender);

      setCalculation(calc);
      setIsCalculating(false);
    }, 800); // Délai un peu plus long pour l'effet
  };

  // Fonction pour confirmer le résultat et fermer le popup
  const handleConfirmResult = async () => {
    if (calculation && attacker && defender) {
  
      
      // ⚠️ IMPORTANT: Ne pas enregistrer ici, laisser applyCombatResult s'en occuper
      // pour éviter les doubles enregistrements
      
      // Confirmer le résultat côté client
      onConfirmCombat(calculation);
    }
  };

  // ✅ AJOUT: Hook pour empêcher le zoom (même fonctionnement que popup déploiement)
  // IMPORTANT: Doit être appelé AVANT tout return conditionnel
  usePreventZoom(isOpen);

  if (!isOpen) return null;

  // Empêcher la propagation des clics pour éviter de fermer le popup
  const handlePopupClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    // Fermer seulement si on clique sur l'overlay (pas sur le popup lui-même)
    if (e.target === e.currentTarget) {
      onCancel();
    }
  };

  return (
    <div className="combat-popup-overlay" onClick={handleOverlayClick} onWheel={handleOverlayWheel}>
      <div className="combat-popup" onClick={handlePopupClick} onWheel={handleContentWheel}>
        <div className="combat-header">
          <h2>🗡️ Combat Tactique</h2>
          <button className="close-btn" onClick={onCancel}>×</button>
        </div>

        {attacker && defender && (
          <div className="combat-content">
            {/* Vue d'ensemble */}
            <div className="combat-overview">
              <div className="combatant attacker">
                <h3>Attaquant</h3>
                <div className="unit-info">
                  <div className="unit-name">{attacker.name}</div>
                  <div className="unit-count">{attacker.count} unités</div>
                  <div className="unit-stats" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {getPrimaryCombatType(attacker) === 'ranged' ? '🏹' : '⚔️'} 
                    {getPrimaryCombatType(attacker) === 'ranged' ? attacker.attack_ranged : attacker.attack_melee} | 
                    🛡️ {getPrimaryCombatType(attacker) === 'ranged' ? attacker.defense_ranged : attacker.defense_melee} | 
                    ❤️ {attacker.hp}
                  </div>
                  {attackerId && (
                    <div className="unit-id" style={{ fontSize: '10px', color: '#888', marginTop: '4px', wordBreak: 'break-all' }}>
                      {attackerId}
                    </div>
                  )}
                  <div className="terrain-info">Terrain: {terrainAttacker}</div>
                </div>
              </div>

              <div className="vs-separator">VS</div>

              <div className="combatant defender">
                <h3>Défenseur</h3>
                <div className="unit-info">
                  <div className="unit-name">{defender.name}</div>
                  <div className="unit-count">{defender.count} unités</div>
                  <div className="unit-stats" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {getPrimaryCombatType(defender) === 'ranged' ? '🏹' : '⚔️'} 
                    {getPrimaryCombatType(defender) === 'ranged' ? defender.attack_ranged : defender.attack_melee} | 
                    🛡️ {getPrimaryCombatType(defender) === 'ranged' ? defender.defense_ranged : defender.defense_melee} | 
                    ❤️ {defender.hp}
                  </div>
                  {defenderId && (
                    <div className="unit-id" style={{ fontSize: '10px', color: '#888', marginTop: '4px', wordBreak: 'break-all' }}>
                      {defenderId}
                    </div>
                  )}
                  <div className="terrain-info">Terrain: {terrainDefender}</div>
                </div>
              </div>
            </div>

            {/* Affichage des bonus spécialisés */}
            {(() => {
              const attackerBonuses = getActiveBonuses(attacker, defender);
              const defenderBonuses = getActiveBonuses(defender, attacker);
              const hasBonuses = attackerBonuses.length > 0 || defenderBonuses.length > 0;
              
              if (!hasBonuses) return null;
              
              return (
                <div className="special-bonuses">
                  <h4>⚔️ Bonus Tactiques Actifs</h4>
                  <div className="bonuses-grid">
                    {attackerBonuses.length > 0 && (
                      <div className="unit-bonuses attacker-bonuses">
                        <div className="bonuses-title">Attaquant</div>
                        {attackerBonuses.map((bonus, index) => (
                          <div key={index} className={`bonus-item ${bonus.bonus > 0 ? 'positive' : 'negative'}`}>
                            <span className="bonus-value">{bonus.bonus > 0 ? '+' : ''}{bonus.bonus}%</span>
                            <span className="bonus-type">{bonus.type.replace('_', ' ')}</span>
                            <span className="bonus-description">{bonus.description}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {defenderBonuses.length > 0 && (
                      <div className="unit-bonuses defender-bonuses">
                        <div className="bonuses-title">Défenseur</div>
                        {defenderBonuses.map((bonus, index) => (
                          <div key={index} className={`bonus-item ${bonus.bonus > 0 ? 'positive' : 'negative'}`}>
                            <span className="bonus-value">{bonus.bonus > 0 ? '+' : ''}{bonus.bonus}%</span>
                            <span className="bonus-type">{bonus.type.replace('_', ' ')}</span>
                            <span className="bonus-description">{bonus.description}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })()}

            {/* Calculs détaillés */}
            {isCalculating ? (
              <div className="calculating">
                <div className="spinner">⚔️</div>
                <p>Calcul du combat en cours...</p>
              </div>
            ) : calculation ? (
              <div className="combat-calculations">
                <div className="calculation-summary">
                  <div className="summary-item">
                    <span className="label">Attaque totale:</span>
                    <span className="value">{calculation.totalAttack.toFixed(1)}</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Défense totale:</span>
                    <span className="value">{calculation.totalDefense.toFixed(1)}</span>
                  </div>
                  <div className="summary-item damage">
                    <span className="label">Dégâts infligés:</span>
                    <span className="value">{calculation.damage.toFixed(1)}</span>
                  </div>
                  <div className="summary-item result">
                    {calculation.isDefenderHero ? (
                      <>
                        <span className="label">HP héros restants:</span>
                        <span className="value">{calculation.remainingHP}/{defender.count * defender.hp}</span>
                      </>
                    ) : (
                      <>
                        <span className="label">Unités survivantes:</span>
                        <span className="value">{calculation.survivingUnits}/{defender.count}</span>
                      </>
                    )}
                  </div>
                </div>

                {/* Log détaillé */}
                <div className="combat-log">
                  <h4>📋 Détail du calcul</h4>
                  <div className="log-content">
                    {calculation.log.map((line, index) => (
                      <div 
                        key={index} 
                        className={`log-line ${line.startsWith('**') ? 'highlight' : ''}`}
                      >
                        {line.replace(/\*\*/g, '')}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="combat-ready">
                <div className="ready-message">
                  <h3>⚔️ Prêt au Combat</h3>
                  <p>Analysez les forces en présence et cliquez sur "Lancer l'attaque" pour débuter le combat.</p>
                  <div className="tactical-preview">
                    <div className="preview-item">
                      <strong>🗡️ Force d'attaque estimée:</strong>
                      <span>{(attacker.attack_melee * attacker.count).toFixed(0)} points</span>
                    </div>
                    <div className="preview-item">
                      <strong>🛡️ Force défensive estimée:</strong>
                      <span>{(defender.defense_melee * defender.count).toFixed(0)} points</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="combat-actions">
              <button className="btn-cancel" onClick={onCancel}>
                Annuler
              </button>
              
              {!calculation ? (
                // Bouton pour lancer le combat (avant calcul)
                <button 
                  className="btn-confirm" 
                  onClick={handleLaunchCombat}
                  disabled={isCalculating || combatExecuted}
                >
                  {isCalculating ? '⚔️ Combat en cours...' : 
                   combatExecuted ? '✅ Combat effectué' : '🚀 Lancer l\'attaque'}
                </button>
              ) : (
                // Bouton pour confirmer le résultat (après calcul)
                <button 
                  className="btn-confirm" 
                  onClick={handleConfirmResult}
                >
                  ✅ Confirmer le résultat
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CombatPopup;
