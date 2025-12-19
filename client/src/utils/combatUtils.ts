/**
 * combatUtils.ts
 * 
 * DESCRIPTION : Utilitaires pour le système de combat V2
 * - Calcul de distance hexagonale 
 * - Récupération de la portée d'attaque depuis unit_stats.json
 * - Vérification de portée d'attaque entre unités
 * - Logique identique à la V1 (UnitController.ts)
 */

import { getApiUrl } from './api';

import { CompactUnit } from '../types/index';

// Interface pour les stats d'unités depuis unit_stats.json
interface UnitStatEntry {
  name: string;
  category: string;
  hp: number;
  attack_melee: number;
  defense_melee: number;
  attack_ranged: number;
  defense_ranged: number;
  range: number;
  movement: number;
  weight: number;
  max_stack_size: number;
  production_cost: { [resource: string]: number };
  production_time: number;
  required_barracks_level: number;
  required_research?: string;
  xp_value: number;
  era: string;
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
}

interface UnitStats {
  [era: string]: {
    [unitType: string]: UnitStatEntry;
  };
}

// Cache pour les stats d'unités
let unitStatsCache: UnitStats | null = null;

/**
 * Charge les stats d'unités depuis unit_stats.json
 */
export const loadUnitStats = async (): Promise<UnitStats> => {
  if (unitStatsCache) {
    return unitStatsCache;
  }

  try {
    const response = await fetch(`${getApiUrl()}/api/v2/unit_stats`);
    if (!response.ok) {
      throw new Error('Failed to load unit stats');
    }
    
    const allStatsData = await response.json();
    
    // Fusionner toutes les sections y compris enemy_units
    unitStatsCache = {
      ...(allStatsData.stone_age || {}),
      ...(allStatsData.classical_age || {}),
      ...(allStatsData.medieval_age || {}),
      ...(allStatsData.renaissance_age || {}),
      ...(allStatsData.napoleonic_age || {}),
      ...(allStatsData.enemy_units || {})
    };
    
    return unitStatsCache!;
  } catch (error) {
    console.error('❌ Erreur chargement unit_stats.json:', error);
    return {};
  }
};

/**
 * Extrait le type d'unité depuis l'ID
 */
export const extractUnitType = (unitId: string): string => {
  if (!unitId) return 'infantry_light';
  
  // Cas spécial direct : hero_hero_1760731775_d086a0
  if (unitId.startsWith('hero_hero_')) {
    return 'hero';
  }
  
  // Cas spécial : defender_player_4_hero_hero_1758922347_696526
  const heroSpecialMatch = unitId.match(/^(attacker|defender)_player_\d+_hero_hero_/);
  if (heroSpecialMatch) {
    return 'hero';
  }
  
  // Cas spécial hero : attacker_player_1_hero_player_1_hero_1 (pas de timestamp long)
  if (unitId.includes('_hero_') || unitId.includes('_hero')) {
    return 'hero';
  }
  
  // ✅ Format auto-deploy wild_camp : auto_defender_wild_camp_barbarian_archer_0
  const wildCampMatch = unitId.match(/^auto_(attacker|defender)_wild_camp_([^_]+_[^_]+)_\d+$/);
  if (wildCampMatch) {
    return wildCampMatch[2]; // ex: barbarian_archer
  }
  
  // ✅ Format wild_camp sans auto : defender_wild_camp_barbarian_warrior_1
  const wildCampStandardMatch = unitId.match(/^(attacker|defender)_wild_camp_([^_]+(?:_[^_]+)*)_\d+$/);
  if (wildCampStandardMatch) {
    return wildCampStandardMatch[2]; // ex: barbarian_warrior, tribal_shaman
  }
  
  // ✅ Format auto-deploy : auto_attacker_player_4_militia_0 OU auto_attacker_player_4_infantry_light_0
  const autoFormatMatch = unitId.match(/^auto_(attacker|defender)_player_\d+_([^_]+(?:_[^_]+)*)_\d+$/);
  if (autoFormatMatch) {
    return autoFormatMatch[2]; // ex: militia OU infantry_light
  }
  
  // ✅ Format sans auto : attacker_player_1_militia_1 OU defender_player_4_barbarian_warrior_2
  const standardMatch = unitId.match(/^(attacker|defender)_player_\d+_([^_]+(?:_[^_]+)*)_\d+$/);
  if (standardMatch) {
    return standardMatch[2]; // ex: militia OU barbarian_warrior
  }
  
  // Format standard : attacker_player_X_TYPE_timestamp_id (timestamp = 10+ caractères)
  const newFormatMatch = unitId.match(/^(attacker|defender)_player_\d+_([^_]+(?:_[^_]+)*?)_\d{10,}/);
  if (newFormatMatch) {
    return newFormatMatch[2];
  }
  
  // Ancien format : infantry_light_attacker_123_0
  const oldFormatMatch = unitId.match(/^([^_]+(?:_[^_]+)*?)_(attacker|defender)_/);
  if (oldFormatMatch) {
    return oldFormatMatch[1];
  }
  
  // Héros ancien format : hero_xxx
  if (unitId.startsWith('hero_')) {
    return 'hero';
  }
  
  console.warn('⚠️ [extractUnitType] Aucun pattern trouvé, fallback: infantry_light');
  return 'infantry_light';
};

/**
 * Récupère les stats d'unité avec bonus de forge depuis l'API
 */
export const getUnitStatsWithForgeBonus = async (unitType: string, playerId: string): Promise<UnitStatEntry | null> => {
  try {
    // Les murs n'ont pas de bonus de forge, retourner les stats de base directement
    if (unitType === 'wall') {
      return await getBaseUnitStats(unitType);
    }
    
    const response = await fetch(`/api/unit-improvements/enhanced-stats/${playerId}/${unitType}`);
    if (!response.ok) {
      throw new Error('Failed to load enhanced unit stats');
    }
    
    const result = await response.json();
    
    if (result.success) {
      return result.stats;
    } else {
      console.warn(`⚠️ Pas de stats améliorées pour ${unitType} / ${playerId}, utilisation stats de base`);
      return await getBaseUnitStats(unitType);
    }
  } catch (error) {
    console.error('❌ Erreur chargement stats avec bonus forge:', error);
    return await getBaseUnitStats(unitType);
  }
};

/**
 * Récupère les stats de base d'une unité (sans bonus de forge)
 */
export const getBaseUnitStats = async (unitType: string): Promise<UnitStatEntry | null> => {
  // Cas spécial pour les murs - les stats viennent des wall_stats du battlefield
  if (unitType === 'wall') {
    return {
      name: "Mur",
      category: "structure",
      hp: 120, // Valeur par défaut, sera remplacée par les données du battlefield
      attack_melee: 0,
      defense_melee: 100, // Valeur par défaut, sera remplacée par les données du battlefield
      attack_ranged: 55, // Valeur par défaut, sera remplacée par les données du battlefield
      defense_ranged: 100,
      range: 2, // Valeur par défaut, sera remplacée par les données du battlefield
      movement: 0,
      weight: 0,
      max_stack_size: 1,
      production_cost: {"wood": 0, "stone": 0, "population": 0},
      production_time: 0,
      required_barracks_level: 0,
      required_research: undefined,
      xp_value: 0,
      era: "classical",
      special_abilities: []
    };
  }

  const unitStats = await loadUnitStats();
  
  // Chercher dans toutes les ères
  for (const era of Object.keys(unitStats)) {
    const eraUnits = unitStats[era];
    if (eraUnits[unitType]) {
      return eraUnits[unitType];
    }
  }
  
  console.warn(`⚠️ Type d'unité inconnu: ${unitType}`);
  return null;
};
export const getUnitRange = async (unit: CompactUnit): Promise<number> => {
  const unitStats = await loadUnitStats();
  const unitType = extractUnitType(unit.unitId);
  
  // Chercher dans toutes les ères
  for (const era of Object.keys(unitStats)) {
    const eraUnits = unitStats[era];
    if (eraUnits[unitType]) {
      const range = eraUnits[unitType].range;
      return range;
    }
  }
  
  // Fallback basé sur le type d'unité si non trouvé
  return getFallbackRange(unitType);
};

/**
 * Portée par défaut selon le type d'unité (identique à UnitController V1)
 */
const getFallbackRange = (unitType: string): number => {
  if (unitType.includes('archer') || unitType.includes('slinger')) {
    return 3;
  } else if (unitType.includes('catapult')) {
    return 4;
  } else if (unitType.includes('mounted_archer')) {
    return 2;
  } else if (unitType === 'hero') {
    return 1; // Les héros ont une portée de mêlée par défaut
  }
  
  return 1; // Mêlée par défaut
};

/**
 * Calcule la distance hexagonale entre deux positions (identique à UnitController V1)
 */
export const hexDistance = (q1: number, r1: number, q2: number, r2: number): number => {
  return (Math.abs(q1 - q2) + Math.abs(q1 + r1 - q2 - r2) + Math.abs(r1 - r2)) / 2;
};

/**
 * Vérifie si une unité peut attaquer une cible selon sa portée
 */
export const canAttackTarget = async (
  attacker: CompactUnit, 
  attackerPos: [number, number], 
  targetPos: [number, number]
): Promise<{ canAttack: boolean; range: number; distance: number }> => {
  
  const range = await getUnitRange(attacker);
  const distance = hexDistance(attackerPos[0], attackerPos[1], targetPos[0], targetPos[1]);
  
  const canAttack = distance <= range;
  
  return { canAttack, range, distance };
};

/**
 * Détermine l'équipe d'une unité depuis son ID
 */
export const getUnitTeam = (unitId: string): 'attacker' | 'defender' => {
  return unitId.includes('attacker') ? 'attacker' : 'defender';
};

/**
 * Vérifie si deux unités sont dans des équipes opposées
 */
export const areEnemies = (unit1: CompactUnit, unit2: CompactUnit): boolean => {
  const team1 = getUnitTeam(unit1.unitId);
  const team2 = getUnitTeam(unit2.unitId);
  return team1 !== team2;
};