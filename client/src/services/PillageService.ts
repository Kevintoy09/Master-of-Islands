/**
 * Service de gestion du pillage de ressources et des victoires de bataille
 * Gère la détection de victoire, les calculs de pillage et l'exécution
 */

import { getApiUrl } from '../utils/api';

export interface VictoryData {
  winner_team: string;
  victory_type: string;
  victory_message: string;
  battle_id: string;
  attacker_id: string;
  defender_city_id: string;
  attacker_ships: number;
}

export interface VictoryDetectionResult {
  hasVictory: boolean;
  victoryData?: VictoryData;
}

export interface PillageableResources {
  [resource: string]: {
    current: number;
    secure: number;
    pillable: number;
    maxCapacity: number;
  };
}

export interface PillageResult {
  totalPillable: number;
  transportCapacity: number;
  resourcesPillaged: { [resource: string]: number };
  distributionRatio: number;
  shipsUsed: number;
}

export interface PillageRequest {
  battleId: string;
  cityId: string;
  shipsCount: number;
  attackerId: string;
}

export class PillageService {
  private static readonly SHIP_CAPACITY = 500; // Capacité par bateau

  // ========== DÉTECTION DE VICTOIRE ==========

  /**
   * Détecte si une réponse d'API contient des informations de victoire
   * et prépare les données nécessaires pour le pillage
   */
  static async detectVictoryFromResponse(
    responseData: any, 
    battleId: string
  ): Promise<VictoryDetectionResult> {
    
    // Vérifier si une victoire a été détectée
    if (!responseData.victory_detected || responseData.winner_team !== 'attackers') {
      return { hasVictory: false };
    }

    try {
      // Récupérer les informations de bataille pour extraire les données nécessaires
      const battleResponse = await fetch(`${getApiUrl()}/api/military/battlefield_v2/${battleId}`);
      if (!battleResponse.ok) {
        console.error('Impossible de récupérer les données de bataille');
        return { hasVictory: false };
      }

      const battleInfo = await battleResponse.json();
      const attackerId = battleInfo.battlefield?.participants?.attackers?.[0];
      
      // Trouver la ville défendue
      let defenderCityId = null;
      if (battleInfo.battlefield?.location) {
        defenderCityId = battleInfo.battlefield.location;
      }

      // Calculer le nombre total de bateaux de tous les attaquants
      let attackerShips = 0;
      const attackers = battleInfo.battlefield?.forces?.attackers || {};
      
      // Parcourir tous les attaquants et leurs contributions
      for (const [_, playerData] of Object.entries(attackers)) {
        const contributions = (playerData as any)?.contributions || [];
        for (const contribution of contributions) {
          attackerShips += contribution.transport_ships || 0;
        }
      }
      
      // Si aucun bateau trouvé via les contributions, essayer surrender_info
      if (attackerShips === 0 && battleInfo.battlefield?.surrender_info?.total_ships) {
        attackerShips = battleInfo.battlefield.surrender_info.total_ships;
      }

      if (!attackerId || !defenderCityId) {
        console.error('Données de bataille incomplètes pour le pillage');
        return { hasVictory: false };
      }

      const victoryData: VictoryData = {
        winner_team: responseData.winner_team,
        victory_type: responseData.victory_type,
        victory_message: responseData.victory_message,
        battle_id: battleId,
        attacker_id: attackerId,
        defender_city_id: defenderCityId,
        attacker_ships: attackerShips
      };

      return { hasVictory: true, victoryData };

    } catch (error) {
      console.error('Erreur lors de l\'analyse de victoire:', error);
      return { hasVictory: false };
    }
  }

  /**
   * Détecte la victoire lors d'une reddition et prépare les données de pillage
   */
  static async detectVictoryFromSurrender(
    surrenderResult: any, 
    battleId: string
  ): Promise<VictoryDetectionResult> {
    
    if (!surrenderResult.success) {
      return { hasVictory: false };
    }

    // Le popup de pillage ne s'ouvre que si les attaquants gagnent (défenseur se rend)
    if (surrenderResult.winner_team !== 'attackers') {
      console.log('⚠️ [PILLAGE] Victoire des défenseurs, pas de pillage');
      return { hasVictory: false };
    }

    // Réutiliser la même logique que pour les combats
    return this.detectVictoryFromResponse({
      victory_detected: true,
      winner_team: surrenderResult.winner_team,
      victory_type: surrenderResult.victory_type,
      victory_message: surrenderResult.message
    }, battleId);
  }

  // ========== CALCULS DE PILLAGE ==========

  /**
   * Calcule les ressources pillables d'une ville à partir des données d'entrepôt
   */
  static calculatePillableResources(storageData: any): PillageableResources {
    const pillableResources: PillageableResources = {};

    if (!storageData) {
      return pillableResources;
    }

    const { current_resources, secure_storage, total_storage } = storageData;

    // Pour chaque ressource, calculer ce qui peut être pillé
    Object.keys(current_resources || {}).forEach(resource => {
      const current = current_resources[resource] || 0;
      const secure = secure_storage[resource] || 0;
      const maxCapacity = total_storage[resource] || 0;
      const pillable = Math.max(0, current - secure);

      if (current > 0) {
        pillableResources[resource] = {
          current,
          secure,
          pillable,
          maxCapacity
        };
      }
    });

    return pillableResources;
  }

  /**
   * Calcule le pillage avec distribution proportionnelle
   */
  static calculatePillageDistribution(
    pillableResources: PillageableResources,
    shipsCount: number
  ): PillageResult {
    const transportCapacity = shipsCount * this.SHIP_CAPACITY;
    
    // Calculer le total pillable
    const totalPillable = Object.values(pillableResources).reduce(
      (sum, resource) => sum + resource.pillable,
      0
    );

    // Si pas de ressources pillables
    if (totalPillable === 0) {
      return {
        totalPillable: 0,
        transportCapacity,
        resourcesPillaged: {},
        distributionRatio: 0,
        shipsUsed: 0
      };
    }

    // Si la capacité de transport couvre tout
    if (transportCapacity >= totalPillable) {
      const resourcesPillaged: { [resource: string]: number } = {};
      
      Object.entries(pillableResources).forEach(([resource, data]) => {
        resourcesPillaged[resource] = data.pillable;
      });

      return {
        totalPillable,
        transportCapacity,
        resourcesPillaged,
        distributionRatio: 1.0,
        shipsUsed: Math.ceil(totalPillable / this.SHIP_CAPACITY)
      };
    }

    // Distribution proportionnelle (arrondir à l'entier)
    const distributionRatio = transportCapacity / totalPillable;
    const resourcesPillaged: { [resource: string]: number } = {};

    Object.entries(pillableResources).forEach(([resource, data]) => {
      if (data.pillable > 0) {
        resourcesPillaged[resource] = Math.floor(data.pillable * distributionRatio);
      }
    });

    return {
      totalPillable,
      transportCapacity,
      resourcesPillaged,
      distributionRatio,
      shipsUsed: shipsCount
    };
  }

  /**
   * Récupère les données de pillage pour une ville ou un village barbare
   */
  static async getPillageData(cityId: string, attackerPlayerId?: string): Promise<PillageableResources> {
    try {
      // Détecter si c'est un village barbare
      if (cityId.includes('wild_camp')) {
        // Pour les villages barbares, récupérer le vrai niveau depuis les données de la ville
        let level = 1;
        
        try {
          // Utiliser la nouvelle API dédiée pour récupérer le niveau réel
          const apiUrl = attackerPlayerId 
            ? `${getApiUrl()}/api/barbarian-village-level-v2/${cityId}/${attackerPlayerId}`
            : `${getApiUrl()}/api/barbarian-village-level-v2/${cityId}/player_6`; // Fallback
          const levelResponse = await fetch(apiUrl);
          if (levelResponse.ok) {
            const levelData = await levelResponse.json();
            
            if (levelData.success && levelData.level) {
              // L'API retourne maintenant directement le niveau
              level = levelData.level;
            } else {
              // Fallback local: extraire depuis le nom
              const simpleMatch = cityId.match(/wild_camp_(\d+)/);
              if (simpleMatch) {
                level = parseInt(simpleMatch[1]);
              }
            }
          } else {
            console.warn(`⚠️ [PILLAGE] API niveau village échoué: ${levelResponse.status}`);
            // Fallback local: extraire depuis le nom
            const simpleMatch = cityId.match(/wild_camp_(\d+)/);
            if (simpleMatch) {
              level = parseInt(simpleMatch[1]);
            }
          }
        } catch (error) {
          console.error('❌ [PILLAGE] Erreur récupération niveau village:', error);
          // Fallback: extraire depuis le nom
          const simpleMatch = cityId.match(/wild_camp_(\d+)/);
          if (simpleMatch) {
            level = parseInt(simpleMatch[1]);
          }
        }
        
        // Utiliser l'endpoint spécialisé pour les villages barbares
        const barbarianResponse = await fetch(`${getApiUrl()}/api/pillage/barbarian-preview/${level}`);
        
        if (barbarianResponse.ok) {
          const result = await barbarianResponse.json();
          if (result.success) {
            // Adapter le format des données barbares
            const pillableResources: PillageableResources = {};
            Object.entries(result.data.pillable_resources || {}).forEach(([resource, amount]) => {
              pillableResources[resource] = {
                current: amount as number,
                secure: 0,
                pillable: amount as number,
                maxCapacity: amount as number // Les villages barbares donnent tout
              };
            });
            return pillableResources;
          }
        }
      }

      // Pour les villes normales, utiliser la route standard
      const pillageResponse = await fetch(`${getApiUrl()}/api/pillage/preview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ city_id: cityId, ships: 1 })
      });

      if (pillageResponse.ok) {
        const result = await pillageResponse.json();
        if (result.success) {
          // Adapter le format des données
          const pillableResources: PillageableResources = {};
          Object.entries(result.data.pillable_resources || {}).forEach(([resource, amount]) => {
            pillableResources[resource] = {
              current: amount as number,
              secure: 0,
              pillable: amount as number,
              maxCapacity: result.data.max_transport_capacity || 1500
            };
          });
          return pillableResources;
        }
      }

      // Fallback vers l'ancienne méthode
      const response = await fetch(`${getApiUrl()}/api/city/${cityId}/storage`);
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      const storageData = await response.json();
      return this.calculatePillableResources(storageData);
    } catch (error) {
      console.error('Erreur lors de la récupération des données de pillage:', error);
      throw error;
    }
  }

  /**
   * Exécute un pillage via l'API
   */
  static async executePillage(request: PillageRequest): Promise<PillageResult> {
    try {
      // Détecter si c'est un village barbare pour utiliser l'endpoint spécialisé
      if (request.cityId.includes('wild_camp')) {
        const response = await fetch(`${getApiUrl()}/api/pillage/barbarian-execute`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            battle_id: request.battleId,
            city_id: request.cityId,
            ships: request.shipsCount,
            attacker_id: request.attackerId || 'player_2'
          }),
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || 'Erreur lors du pillage du camp des sauvages');
        }

        const result = await response.json();
        
        // Adapter le format de réponse pour les villages barbares
        return {
          totalPillable: result.data.total_pillaged || 0,
          transportCapacity: result.data.capacity_total || (request.shipsCount * this.SHIP_CAPACITY),
          resourcesPillaged: result.data.pillaged_resources || {},
          distributionRatio: 1.0,
          shipsUsed: result.data.ships_used || request.shipsCount
        };
      }

      // Pour les villes normales, utiliser l'endpoint standard
      const response = await fetch(`${getApiUrl()}/api/pillage/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          battle_id: request.battleId,
          city_id: request.cityId,
          ships: request.shipsCount,
          attacker_id: request.attackerId || 'player_2' // Utiliser l'ID fourni
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Erreur lors du pillage');
      }

      const result = await response.json();
      
      // Adapter le format de réponse
      return {
        totalPillable: result.total_pillaged || 0,
        transportCapacity: (result.ships_used || 1) * this.SHIP_CAPACITY,
        resourcesPillaged: result.pillaged_resources || {},
        distributionRatio: 1.0,
        shipsUsed: result.ships_used || 1
      };
    } catch (error) {
      console.error('Erreur lors de l\'exécution du pillage:', error);
      throw error;
    }
  }

  /**
   * Formate les ressources pillées pour l'affichage
   */
  static formatPillageDisplay(result: PillageResult): string {
    const resources = Object.entries(result.resourcesPillaged)
      .filter(([, amount]) => amount > 0)
      .map(([resource, amount]) => `${this.getResourceEmoji(resource)} ${amount}`)
      .join(', ');

    return resources || 'Aucune ressource pillée';
  }

  /**
   * Récupère l'emoji d'une ressource
   */
  static getResourceEmoji(resource: string): string {
    const emojis: { [key: string]: string } = {
      wood: '🪵',
      stone: '🪨',
      iron: '⚙️',
      cereal: '🌾',
      papyrus: '📜',
      wine: '�',
      marble: '🏛️',
      horse: '🐎',
      glass: '🪟',
      gunpowder: '💥',
      coal: '⚫',
      cotton: '🌸',
      spices: '🌶️'
    };
    return emojis[resource] || '📦';
  }
}
