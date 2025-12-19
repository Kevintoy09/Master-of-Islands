// Types communs utilisés dans tout le projet

export interface Slot {
  id: string;
  x: number;
  y: number;
  type: string;
  locked: boolean;
}

export interface CityLayout {
  background: string;
  slots: Slot[];
}

export interface CityBuilding {
  slot_id: string;
  name: string;
  level: number;
  construction_end?: number;
  status?: string;
  started_at?: number;
  duration?: number;
}

export interface City {
  id: string;
  name: string;
  owner: string | null;
  city_coords?: [number, number];
  controlable: boolean;
  layout?: string;
  city_layout?: string;
  buildings?: CityBuilding[];
  resources?: Record<string, number>;
  workers_assigned?: Record<string, number>;
  satisfaction?: number;
  base_resource?: string;
}

export interface BuildingData {
  name?: string;
  description?: string;
  image?: string;
  category?: string;
  required_research?: string | null;
  levels?: BuildingLevel[];
}

export interface BuildingLevel {
  level: number;
  cost: Record<string, number>;
  construction_time: number;
  effect: Record<string, any>;
}

export interface PopupProps {
  building: CityBuilding;
  city: City;
  onClose: () => void;
  onCityDataChange?: () => void;
  onDevelop?: () => void;
  onDestroy?: () => void;
}

// ===== TYPES DE BATAILLE UNIFIÉS =====
// Remplace toutes les définitions dispersées de Unit, HexPosition, etc.

export type UnitCategory = 'infantry' | 'ranged' | 'cavalry' | 'siege' | 'hero' | 'artillery' | 'general';

// Types pour les données compactes de battlesv2.json
export interface CompactUnit {
  unitId: string;
  position: [number, number]; // Format [q, r]
  unitCount?: number;
  hp?: number; // Pour les héros
}

export interface HexPosition {
  q: number;
  r: number;
}

export interface Unit {
  // Identité
  id: string;
  name: string;
  type: UnitCategory | string; // ✅ Toutes les catégories du jeu + compatibilité
  detailedType?: string; // archer, spearman, etc.
  
  // Combat
  health: number;
  maxHealth: number;
  attack: number;
  defense: number;
  movement: number;
  morale: number;
  
  // Bataille - UNIFIE count/stack/effectif
  count: number;  // Propriété principale 
  stack?: number; // ✅ COMPATIBILITÉ: Alias pour count (BattlePopup l'utilise)
  team: 'attacker' | 'defender';
  
  // Position (BattlePopup l'utilise)
  position?: HexPosition;
  
  // Combat avancé (BattlePopup l'utilise)  
  range?: number;
  
  // État - UNIFIE hasMovedThisTurn/hasActed
  hasMovedThisTurn?: boolean; 
  hasActed?: boolean; // ✅ COMPATIBILITÉ: Alias pour hasMovedThisTurn
  
  // Visuel
  icon?: string;
  
  // 🆕 Propriétés héros (ajout minimal)
  heroData?: any; // Données du héros depuis UnitDeploymentPopup
  
  // 🆕 Bonus de héros appliqués aux unités
  heroBonusesApplied?: {
    offensive_bonus?: number;
    defensive_bonus?: number;
    movement_bonus?: number;
  };
  
  // 🆕 Statut de combat pour les héros (HP actuels vs HP max)
  combatStatus?: {
    current_hp?: number;
    max_hp?: number;
    last_damage?: number;
    status?: 'healthy' | 'wounded' | 'eliminated';
    last_updated?: string;
  };
}

export interface HexCell {
  q: number;
  r: number;
  terrain: 'plains' | 'forest' | 'hill' | 'river' | 'marsh' | 'road' | 'village' | 'base-attack' | 'base-defense' | 'wall';
  zone: 'attacker-base' | 'defender-base' | 'battlefield';
  unit?: Unit;
  defenseBonus: number;
  attackPenalty: number;
  movementBonus: number;
}

export interface UnitAction {
  action: 'select' | 'move' | 'attack' | 'invalid' | 'deselect' | 'pending';
  unit?: Unit | null;
  movementRange?: HexPosition[];
  result?: {
    isValid: boolean;
    source: HexPosition;
    target: HexPosition;
    message?: string;
  };
  // Combat
  attacker?: Unit;
  defender?: Unit;
  attackerHex?: HexPosition;
  defenderHex?: HexPosition;
}

// ===== TYPES ÉTENDUS POUR DÉPLOIEMENT =====
export interface UnitGroup extends Unit {
  maxStack: number; // Spécifique au déploiement
  status: 'arrived' | 'en_route'; // Statut des renforts
  heroData?: any; // Données spécifiques aux héros
}

export interface PlayerDeploymentData {
  player_id: string;
  player_name: string;
  garrison: { [unitType: string]: number };
  arrived_reinforcements: { [unitType: string]: number };
  en_route_reinforcements: { [unitType: string]: number };
  total_available: { [unitType: string]: number };
  heroes: { [heroInstanceId: string]: any }; // Héros disponibles pour le déploiement
}
