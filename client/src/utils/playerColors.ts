/**
 * Système de couleurs dynamique pour différencier les joueurs sur le battlefield
 * - 1er attaquant = rouge, 1er défenseur = bleu
 * - Autres joueurs = couleurs prédéfinies dans l'    //Attribution des couleurs selon l'ordre définieparition
 */

export interface PlayerColor {
  primary: string;    // Couleur principale de l'unité
  secondary: string;  // Couleur de bordure/accent
  name: string;       // Nom lisible de la couleur
}

// Palette de couleurs pour les joueurs additionnels (après le 1er attaquant et 1er défenseur)
const ADDITIONAL_COLORS: PlayerColor[] = [
  { primary: '#ffa600ff', secondary: '#FFD700', name: 'Orange' },      // 3ème joueur
  { primary: '#32CD32', secondary: '#FFD700', name: 'Vert' },        // 4ème joueur  
  { primary: '#9370DB', secondary: '#FFD700', name: 'Violet' },      // 5ème joueur
  { primary: '#ff14ccff', secondary: '#FFD700', name: 'Rose' },        // 6ème joueur
  { primary: '#00CED1', secondary: '#FFD700', name: 'Cyan' },        // 7ème joueur
  { primary: '#FFD700', secondary: '#2F4F4F', name: 'Or' },          // 8ème joueur
  { primary: '#521a0fff', secondary: '#FFD700', name: 'Tomate' },      // 9ème joueur
  { primary: '#40E0D0', secondary: '#FFD700', name: 'Turquoise' },   // 10ème joueur
];

// Cache pour stocker l'attribution dynamique des couleurs
const playerColorCache = new Map<string, PlayerColor>();

// Variables globales pour l'ordre des joueurs dans la bataille actuelle
let battleAttackers: string[] = [];
let battleDefenders: string[] = [];

/**
 * Obtient dynamiquement la couleur d'un joueur basée sur son équipe et l'ordre d'apparition
 * @param playerId - ID du joueur (ex: "player_3", "player_42")
 * @param team - Équipe ("attacker" ou "defender")
 * @param allPlayers - Liste de tous les joueurs pour déterminer l'ordre (optionnel)
 * @returns Couleurs du joueur
 */
export function getPlayerColor(
  playerId: string | null, 
  team: string | null = null,
  allPlayers: string[] = []
): PlayerColor {
  if (!playerId) {
    // Fallback basé sur l'équipe
    if (team === 'attacker') {
      return { primary: '#DC143C', secondary: '#FFD700', name: 'Attaquant' };
    }
    return { primary: '#4169E1', secondary: '#FFD700', name: 'Défenseur' };
  }

  // Vérifier le cache
  if (playerColorCache.has(playerId)) {
    return playerColorCache.get(playerId)!;
  }

  let color: PlayerColor;

  // Si on a la liste de tous les joueurs, déterminer l'ordre
  if (allPlayers.length > 0) {
    const attackers = allPlayers.filter(p => team === 'attacker' || p.includes('attacker'));
    const defenders = allPlayers.filter(p => team === 'defender' || p.includes('defender'));
    
    // Premier attaquant = rouge
    if (team === 'attacker' && attackers.indexOf(playerId) === 0) {
      color = { primary: '#DC143C', secondary: '#FFD700', name: 'Rouge' };
    }
    // Premier défenseur = bleu  
    else if (team === 'defender' && defenders.indexOf(playerId) === 0) {
      color = { primary: '#4169E1', secondary: '#FFD700', name: 'Bleu' };
    }
    // Autres joueurs = couleurs additionnelles
    else {
      const allSorted = [...attackers, ...defenders];
      const playerIndex = allSorted.indexOf(playerId);
      const colorIndex = Math.max(0, playerIndex - 2); // -2 car les 2 premiers ont déjà des couleurs fixes
      color = ADDITIONAL_COLORS[colorIndex % ADDITIONAL_COLORS.length];
    }
  } else {
    // Fallback simple basé sur l'équipe si pas de liste complète
    if (team === 'attacker') {
      color = { primary: '#DC143C', secondary: '#FFD700', name: 'Attaquant' };
    } else if (team === 'defender') {
      color = { primary: '#4169E1', secondary: '#FFD700', name: 'Défenseur' };
    } else {
      // Attribution pseudo-aléatoire basée sur l'ID du joueur
      const hash = playerId.split('').reduce((a, b) => {
        a = ((a << 5) - a) + b.charCodeAt(0);
        return a & a;
      }, 0);
      const colorIndex = Math.abs(hash) % ADDITIONAL_COLORS.length;
      color = ADDITIONAL_COLORS[colorIndex];
    }
  }

  // Mettre en cache
  playerColorCache.set(playerId, color);
  return color;
}

/**
 * Génère une classe CSS dynamique pour un joueur
 * @param playerId - ID du joueur
 * @param team - Équipe
 * @returns Nom de classe CSS
 */
export function getPlayerColorClass(playerId: string | null, team: string | null = null): string {
  if (!playerId) {
    return team === 'attacker' ? 'team-attacker' : 'team-defender';
  }
  
  let colorIndex = 0;
  
  // Si les listes ne sont pas encore initialisées, utiliser un fallback intelligent
  if (battleAttackers.length === 0 && battleDefenders.length === 0) {
    // Fallback temporaire basé sur l'équipe et l'ID du joueur
    if (team === 'attacker') {
      // Extraire le numéro du joueur pour un ordre cohérent
      const playerNum = parseInt(playerId.replace('player_', '')) || 0;
      colorIndex = playerNum === 3 ? 0 : 2; // player_3 = rouge, autres = vert
    } else if (team === 'defender' || playerId === 'wild_camp') {
      colorIndex = 1; // Défenseur = bleu (incluant wild_camp)
    } else {
      // Fallback générique avec hash
      const hash = playerId.split('').reduce((a, b) => {
        a = ((a << 5) - a) + b.charCodeAt(0);
        return a & a;
      }, 0);
      colorIndex = Math.abs(hash) % 8;
    }
  } else {
    // Chercher dans les attaquants
    const attackerIndex = battleAttackers.indexOf(playerId);
    if (attackerIndex >= 0) {
      if (attackerIndex === 0) {
        colorIndex = 0; // Premier attaquant = rouge (player-color-0)
      } else {
        colorIndex = 2 + (attackerIndex - 1); // Autres attaquants: 2, 3, 4...
      }
    } else {
      // Chercher dans les défenseurs
      const defenderIndex = battleDefenders.indexOf(playerId);
      if (defenderIndex >= 0) {
        if (defenderIndex === 0 || playerId === 'wild_camp') {
          colorIndex = 1; // Premier défenseur = bleu (player-color-1) - incluant wild_camp
        } else {
          // Autres défenseurs après tous les attaquants supplémentaires
          colorIndex = 2 + Math.max(0, battleAttackers.length - 1) + defenderIndex;
        }
      } else {
        // Fallback si joueur pas trouvé dans les listes
        const hash = playerId.split('').reduce((a, b) => {
          a = ((a << 5) - a) + b.charCodeAt(0);
          return a & a;
        }, 0);
        colorIndex = Math.abs(hash) % 8;
      }
    }
  }
  
  colorIndex = Math.min(colorIndex, 7); // Maximum 7
  return `player-color-${colorIndex}`;
}

/**
 * Initialise les couleurs pour une bataille avec tous les joueurs
 * @param battleData - Données de la bataille contenant tous les joueurs
 */
export function initializeBattleColors(battleData: any): void {
  playerColorCache.clear();
  battleAttackers = [];
  battleDefenders = [];
  
  // Utiliser directement les participants pour l'ordre officiel
  if (battleData?.participants) {
    // Récupérer l'ordre des attaquants depuis participants
    if (battleData.participants.attackers && Array.isArray(battleData.participants.attackers)) {
      battleAttackers = [...battleData.participants.attackers];
    }
    
    // Récupérer l'ordre des défenseurs depuis participants  
    if (battleData.participants.defenders && Array.isArray(battleData.participants.defenders)) {
      battleDefenders = [...battleData.participants.defenders];
    }
    

    
    // Attribution des couleurs selon l'ordre
    battleAttackers.forEach((playerId, index) => {

    });
    
    battleDefenders.forEach((playerId, index) => {
      // Les défenseurs sont attribués après les attaquants
    });
    
  } else {
    // Fallback sur l'ancienne méthode si pas de participants
    if (!battleData?.teams) {
      return;
    }
    
    // Extraire tous les joueurs uniques des teams
    Object.keys(battleData.teams).forEach(teamKey => {
      const units = battleData.teams[teamKey];
      if (Array.isArray(units)) {
        units.forEach(unit => {
          if (unit.unitId) {
            const parts = unit.unitId.split('_');
            if (parts.length >= 3) {
              const team = parts[0];
              const playerId = `${parts[1]}_${parts[2]}`;
              
              if (team === 'attacker' && !battleAttackers.includes(playerId)) {
                battleAttackers.push(playerId);
              } else if (team === 'defender' && !battleDefenders.includes(playerId)) {
                battleDefenders.push(playerId);
              }
            }
          }
        });
      }
    });
    
    battleAttackers.sort();
    battleDefenders.sort();
  }

}
