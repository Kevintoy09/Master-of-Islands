/**
 * wallTypes.ts
 * Types partagés pour le système de murs
 */

export interface WallGroup {
  positions: [number, number][];
  hp: number;
  max_hp: number;
  group_index: number;
  wall_level: number;
  total_positions: number;
  destroyed?: boolean;
}

export interface WallStats {
  defense: number;
  wall_hp: number;
  attack_ranged: number;
  range: number;
  nb_element: number;
  battlefield_map: string;
}

export interface WallDefenderStats {
  type: string;
  name: string;
  count: number;
  hp: number;
  max_hp: number;
  attack_melee: number;
  defense_melee: number;
  attack_ranged: number;
  defense_ranged: number;
  range: number;
  category: string;
  special_abilities: any[];
  isWall: true;
  wallGroup: WallGroup;
  wallStats: WallStats;
  total_positions?: number;
}