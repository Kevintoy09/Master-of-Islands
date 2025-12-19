/**
 * UnitCounterService - Gestion des compteurs d'unités centralisés
 * Résout le problème de réapparition des unités après déploiement
 */
import { getApiUrl } from '../utils/api';

export interface UnitCounter {
  total: number;      // Unités totales disponibles (depuis battlefields_v2.json)
  deployed: number;   // Unités déjà déployées 
}

export interface PlayerUnitCounts {
  [unitType: string]: UnitCounter;
}

export interface BattleUnitCounts {
  [playerId: string]: PlayerUnitCounts;
}

export interface AvailableUnit {
  unitType: string;
  available: number;    // total - deployed
  total: number;
  deployed: number;
  playerId: string;
}

export class UnitCounterService {

  /**
   * Récupère les compteurs d'unités pour une bataille
   */
  static async getUnitCounts(battleId: string): Promise<BattleUnitCounts | null> {
    try {
      const response = await fetch(`${getApiUrl()}/api/v2/battle/get-unit-counts/${battleId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || 'Erreur lors de la récupération des compteurs');
      }

      return result.unit_counts;
    } catch (error) {
      console.error('❌ Erreur récupération compteurs:', error);
      return null;
    }
  }

  /**
   * Met à jour les compteurs après déploiement
   */
  static async updateUnitCounts(battleId: string, deployedUnits: any[]): Promise<boolean> {
    try {
      const response = await fetch(`${getApiUrl()}/api/v2/battle/update-unit-counts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          battleId,
          deployedUnits
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('❌ Erreur mise à jour compteurs:', error);
      return false;
    }
  }

  /**
   * Calcule les unités disponibles pour un joueur (total - deployed)
   */
  static getAvailableUnitsForPlayer(
    unitCounts: BattleUnitCounts, 
    playerId: string
  ): AvailableUnit[] {
    const playerCounts = unitCounts[playerId];
    if (!playerCounts) {
      return [];
    }

    const availableUnits: AvailableUnit[] = [];

    Object.entries(playerCounts).forEach(([unitType, counter]) => {
      const available = Math.max(0, counter.total - counter.deployed);
      
      if (available > 0) {
        availableUnits.push({
          unitType,
          available,
          total: counter.total,
          deployed: counter.deployed,
          playerId
        });
      }
    });

    return availableUnits;
  }

  /**
   * Charge toutes les unités disponibles pour une bataille (remplace loadRealUnitsFromBattlefield)
   */
  static async loadAvailableUnits(battleId: string, currentPlayerId?: string): Promise<{
    [unitType: string]: {
      count: number;
      name: string;
      category: string;
      playerId: string;
    }
  }> {
    try {
      // Récupérer les compteurs depuis l'API
      const unitCounts = await this.getUnitCounts(battleId);
      if (!unitCounts) {
        console.warn('⚠️ Aucun compteur trouvé pour la bataille', battleId);
        return {};
      }

      // Charger les stats des unités pour les noms et catégories
      const unitStats = await this.loadUnitStats();
      
      const availableUnits: { [unitType: string]: any } = {};

      // Pour chaque joueur, récupérer les unités disponibles
      Object.entries(unitCounts).forEach(([playerId, playerCounts]) => {
        // Si currentPlayerId spécifié, filtrer seulement ce joueur
        if (currentPlayerId && playerId !== currentPlayerId) {
          return;
        }

        const playerAvailable = this.getAvailableUnitsForPlayer(unitCounts, playerId);
        
        playerAvailable.forEach(unit => {
          const unitStat = unitStats[unit.unitType];
          
          availableUnits[unit.unitType] = {
            count: unit.available,
            name: unitStat?.name || unit.unitType,
            category: unitStat?.category || 'infantry',
            playerId: unit.playerId
          };
        });
      });


      return availableUnits;

    } catch (error) {
      console.error('❌ Erreur chargement unités disponibles:', error);
      return {};
    }
  }

  /**
   * Charge les statistiques des unités
   */
  private static async loadUnitStats(): Promise<{ [unitType: string]: any }> {
    try {
      const response = await fetch(`${getApiUrl()}/api/v2/unit_stats`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const allStatsData = await response.json();
      
      // Fusionner toutes les sections y compris enemy_units
      return {
        ...(allStatsData.stone_age || {}),
        ...(allStatsData.classical_age || {}),
        ...(allStatsData.medieval_age || {}),
        ...(allStatsData.renaissance_age || {}),
        ...(allStatsData.napoleonic_age || {}),
        ...(allStatsData.enemy_units || {})
      };
    } catch (error) {
      console.warn('⚠️ Impossible de charger unit_stats.json, utilisation des valeurs par défaut');
      return {};
    }
  }

  /**
   * Vérifie si un joueur peut déployer un type d'unité
   */
  static canDeployUnit(
    unitCounts: BattleUnitCounts, 
    playerId: string, 
    unitType: string, 
    requestedCount: number = 1
  ): boolean {
    const playerCounts = unitCounts[playerId];
    if (!playerCounts || !playerCounts[unitType]) {
      return false;
    }

    const counter = playerCounts[unitType];
    const available = counter.total - counter.deployed;
    
    return available >= requestedCount;
  }

  /**
   * Obtient un résumé des compteurs pour debug
   */
  static getSummary(unitCounts: BattleUnitCounts): string {
    const summary: string[] = [];
    
    Object.entries(unitCounts).forEach(([playerId, playerCounts]) => {
      const playerSummary = Object.entries(playerCounts)
        .map(([unitType, counter]) => 
          `${unitType}: ${counter.total - counter.deployed}/${counter.total}`
        )
        .join(', ');
      
      summary.push(`${playerId}: ${playerSummary}`);
    });

    return summary.join(' | ');
  }
}