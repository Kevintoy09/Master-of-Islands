/**
 * unitIcons.ts
 * 
 * Mapping des icônes par type d'unité selon unit_stats.json
 */

export const UNIT_ICONS = {
  // Infanterie
  'infantry_light': '🗡️',
  'infantry_heavy': '⚔️',
  'hoplite': '🛡️',
  'swordsman': '⚔️',
  'spearman': '🔱',
  'militia': '🗡️',
  'pikeman': '🔱',
  
  // Unités à distance
  'archer': '🏹',
  'slinger': '🪃',
  'javelin_thrower': '🗂️',
  'crossbow': '🏹',
  
  // Cavalerie
  'cavalry_light': '🐎',
  'cavalry_heavy': '🏇',
  'horse_archer': '🏹🐎',
  'chariot': '🏛️',
  'hussar': '🐎',
  'cuirassier': '🏇',
  
  // Siège et artillerie
  'catapult': '🏗️',
  'ballista': '🎯',
  'battering_ram': '🔨',
  'siege_tower': '🏰',
  'field_cannon': '💣',
  'howitzer': '💣',
  
  // Support
  'military_engineer': '⚒️',
  
  // Napoleonic
  'line_infantry': '🎖️',
  'grenadier': '💥',
  'rifle_regiment': '🎯',
  
  // Ennemis
  'barbarian_warrior': '⚔️',
  'barbarian_archer': '🏹',
  'barbarian_raider': '🐎',
  'tribal_shaman': '🔮',
  'bandit_leader': '👑',
  'pirate_crew': '☠️',
  'pirate_captain': '👑',
  'mercenary_veteran': '⚔️',
  'rogue_mage': '🔮',
  'ancient_guardian': '🗿',
  
  // Héros
  'hero': '👑',
  
  // Fallback
  'default': '⚔️'
};

export const getUnitIcon = (unitType: string): string => {
  return UNIT_ICONS[unitType as keyof typeof UNIT_ICONS] || UNIT_ICONS.default;
};
