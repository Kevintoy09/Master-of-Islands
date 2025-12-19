/**
 * UnifiedBattleLoaderService.ts
 * 
 * Service unifié pour le chargement des batailles côté client.
 * Remplace l'ancien BattleLoaderService.ts et centralise tous les appels API.
 * Utilise exclusivement les APIs du serveur unifié.
 * 
 * unified_battle_loader_service.py (backend Python) :
Ce fichier gère la logique métier côté serveur : chargement des données, calculs, accès aux fichiers JSON, gestion des routes API, etc. Il fonctionne avec Flask (ou FastAPI) et s'exécute sur le serveur.

UnifiedBattleLoaderService.ts (frontend TypeScript) :
Ce fichier est un service client qui s'occupe d'appeler les endpoints API du backend, de recevoir les réponses, et de les transmettre aux composants React. Il s'exécute dans le navigateur.
 * 
 */

import { getApiUrl } from '../utils/api';

export interface BattleData {
  battleId: string;
  map: string;
  participants: string[];
  forces: any;
  status: string;
  hasPositions: boolean;
  positions?: any;
  currentRound?: number;
  currentPlayer?: string;
}

export interface BattleStats {
  success?: boolean;
  battleId: string;
  attacker: { total_units: number; moral: number };
  defender: { total_units: number; moral: number };
  // Format attendu par le client
  unit_counts?: {
    attacker: number;
    defender: number;
  };
  moral?: {
    attacker: number;
    defender: number;
  };
  map: string;
  status: string;
  currentRound: number;
  current_round?: number;
  currentPlayer: string;
}

export interface BattlePositions {
  battleId: string;
  teams: any;
  current_round: number;
  current_player: string;
}

export class UnifiedBattleLoaderService {
  private static getBaseUrl(): string {
    return getApiUrl();
  }

  /**
   * Charge une bataille depuis une ville donnée
   */
  static async loadBattleFromCity(cityId: string): Promise<BattleData | null> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v2/battle/city/${cityId}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.success && result.battle) {
        return result.battle;
      } else {
        return null;
      }
    } catch (error) {
      console.error(`Erreur lors du chargement de la bataille:`, error);
      return null;
    }
  }

  /**
   * Récupère toutes les batailles actives
   */
  static async getAllActiveBattles(): Promise<BattleData[]> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v2/battlefields/all`);
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.success && result.battlefields) {
        return Object.values(result.battlefields) as BattleData[];
      }
      
      return [];
    } catch (error) {
      console.error(`❌ [UnifiedService] Erreur lors du chargement des batailles:`, error);
      return [];
    }
  }

  /**
   * Vérifie si une ville a une bataille en cours
   */
  static async hasBattle(cityId: string): Promise<boolean> {
    const battle = await this.loadBattleFromCity(cityId);
    return battle !== null;
  }

  /**
   * Récupère les statistiques d'une bataille
   */
  static async getBattleStats(battleId: string): Promise<BattleStats | null> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v2/battle/stats/${battleId}`);
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.success) {
        return result;
      }
      
      return null;
    } catch (error) {
      console.error(`❌ [UnifiedService] Erreur lors du chargement des stats:`, error);
      return null;
    }
  }

  /**
   * Récupère les positions d'une bataille
   */
  static async getBattlePositions(battleId: string): Promise<BattlePositions | null> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v2/battle/get-positions/${battleId}`);
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error(`❌ [UnifiedService] Erreur lors du chargement des positions:`, error);
      return null;
    }
  }

  /**
   * Récupère les bonus de terrain
   */
  static async getBattlefieldBonuses(battleId: string): Promise<any> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/hero/battlefield-bonuses/${battleId}`);
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.success) {
        return result.bonuses;
      }
      
      return {};
    } catch (error) {
      console.error(`❌ [UnifiedService] Erreur lors du chargement des bonus:`, error);
      return {};
    }
  }

  /**
   * Récupère le moral d'une bataille
   */
  static async getBattleMoral(battleId: string): Promise<any> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/battle/${battleId}/moral`);
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.success) {
        return result.moral;
      }
      
      return {};
    } catch (error) {
      console.error(`❌ [UnifiedService] Erreur lors du chargement du moral:`, error);
      return {};
    }
  }

  /**
   * Initialise une nouvelle bataille
   */
  static async initializeBattle(data: any): Promise<any> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/battle/initialize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error(`❌ [UnifiedService] Erreur lors de l'initialisation:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Erreur inconnue',
        attackerUnits: {},
        defenderUnits: {}
      };
    }
  }

  /**
   * Sauvegarde les positions de bataille
   */
  static async savePositions(data: any): Promise<any> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v2/battle/save-positions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`❌ [UnifiedService] Erreur lors de la sauvegarde:`, error);
      return { success: false, error: error instanceof Error ? error.message : 'Erreur inconnue' };
    }
  }

  /**
   * Génère les positions initiales
   */
  static async generateInitialPositions(battleId: string): Promise<any> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v2/battle/generate-positions/${battleId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`❌ [UnifiedService] Erreur lors de la génération:`, error);
      return { success: false, error: error instanceof Error ? error.message : 'Erreur inconnue' };
    }
  }

  /**
   * Déplace une unité
   */
  static async moveUnit(battleId: string, unitId: string, position: [number, number]): Promise<any> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v2/battle/${battleId}/move_unit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          unit_id: unitId,
          position: position
        })
      });
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`❌ [UnifiedService] Erreur lors du déplacement:`, error);
      return { success: false, error: error instanceof Error ? error.message : 'Erreur inconnue' };
    }
  }

  /**
   * Termine une bataille
   */
  static async endBattle(battleId: string): Promise<any> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/v2/battle/end/${battleId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`❌ [UnifiedService] Erreur lors de la fin de bataille:`, error);
      return { success: false, error: error instanceof Error ? error.message : 'Erreur inconnue' };
    }
  }

  /**
   * Initie le voyage de retour pour TOUS les transports d'une bataille
   */
  static async returnAllTransports(battleId: string): Promise<boolean> {
    if (!battleId) {
      alert('❌ Aucun battlefield actif');
      return false;
    }

    try {
      // Charger battlefield pour identifier les transports
      const battlefieldResponse = await fetch(`${this.getBaseUrl()}/api/military/battlefield_v2/${battleId}`);
      if (!battlefieldResponse.ok) {
        throw new Error(`Erreur HTTP: ${battlefieldResponse.status}`);
      }
      const battlefieldData = await battlefieldResponse.json();
      if (!battlefieldData.battlefield) {
        throw new Error('Données de battlefield non trouvées');
      }

      // Extraire les transports
      const attackers = battlefieldData.battlefield.forces?.attackers || {};
      const transportList: any[] = [];

      for (const [playerId, playerData] of Object.entries(attackers)) {
        const contributions = (playerData as any).contributions || [];
        for (const contribution of contributions) {
          if (contribution.id && contribution.id.startsWith('transport_')) {
            transportList.push({
              transportId: contribution.id,
              playerId: playerId,
              cityId: contribution.source_city || 'N/A'
            });
          }
        }
      }

      if (transportList.length === 0) {
        alert('❌ Aucun transport trouvé dans cette bataille');
        return false;
      }

      // Confirmation
      const transportDetails = transportList
        .map(t => `• ${t.transportId} (Joueur ${t.playerId}, Ville ${t.cityId})`)
        .join('\n');

      const confirmed = window.confirm(
        `🚢 Initier le voyage de retour pour TOUS les transports ?\n\n` +
        `📊 ${transportList.length} transport(s) concerné(s):\n${transportDetails}\n\n` +
        `⚠️ Cette action configurera le retour pour tous les transports participants à cette bataille.\n\n` +
        `Confirmer ?`
      );
      
      if (!confirmed) return false;

      // Appeler l'API
      const returnResponse = await fetch('/api/unit-transports/return-all', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          battleId: battleId
        }),
      });

      if (!returnResponse.ok) {
        throw new Error(`Erreur HTTP: ${returnResponse.status}`);
      }

      const result = await returnResponse.json();
      
      if (result.success) {
        const processedCount = result.processed_transports?.length || 0;
        const totalUnits = result.total_units || 0;
        const totalResources = Object.values(result.total_resources || {}).reduce((sum: number, val: any) => sum + (val || 0), 0);
        
        alert(`🚢 Voyage de retour initié pour ${processedCount} transport(s) !
        
📊 Statistiques:
📦 ${totalUnits} unités embarquées
💰 ${totalResources} ressources chargées
⏱️ Durée: ${Math.round(result.journey_duration_minutes || 60)} min
🎯 Destination: Villes d'origine

🚢 Tous les transports sont en route !`);
        
        console.log('✅ [BATTLE_RETURN] Tous les transports configurés:', result);
        return true;
      } else {
        throw new Error(result.error || 'Erreur lors du voyage retour groupé');
      }

    } catch (err: any) {
      alert(`❌ Erreur voyage retour groupé: ${err.message}`);
      return false;
    }
  }
}