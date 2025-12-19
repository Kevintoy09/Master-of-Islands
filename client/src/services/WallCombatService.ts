/**
 * WallCombatService.ts
 * Service dédié pour gérer les combats contre les murs
 * Sépare la logique complexe de SimpleBattlefieldV2
 */

import { CompactUnit } from '../types/index';
import { WallGroup, WallStats } from '../types/wallTypes';

export class WallCombatService {

  /**
   * Applique les dégâts calculés au mur via l'API
   */
  static async applyWallDamage(
    wallGroup: WallGroup,
    damage: number,
    actualBattleId: string,
    attackWallGroup: (groupIndex: number, damage: number) => Promise<void>
  ): Promise<void> {
    await attackWallGroup(wallGroup.group_index, damage);
  }

  /**
   * Valide les données avant ouverture du popup de combat
   */
  static validateCombatData(
    selectedUnit: CompactUnit | null,
    wallGroup: WallGroup | null,
    wallStats: WallStats | null
  ): { isValid: boolean; errorMessage?: string } {
    if (!selectedUnit) {
      return {
        isValid: false,
        errorMessage: 'Aucune unité sélectionnée pour attaquer.'
      };
    }

    if (!wallGroup) {
      return {
        isValid: false,
        errorMessage: 'Aucun groupe de murs trouvé à cette position.'
      };
    }

    if (!wallStats) {
      return {
        isValid: false,
        errorMessage: 'Statistiques des murs indisponibles.'
      };
    }

    if (wallGroup.hp <= 0) {
      return {
        isValid: false,
        errorMessage: 'Ce groupe de murs est déjà détruit.'
      };
    }

    return { isValid: true };
  }
}