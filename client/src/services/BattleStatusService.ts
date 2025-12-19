/**
 * BattleStatusService.ts
 * 
 * Service pour vérifier le statut des batailles en cours dans les villes
 */

interface BattlefieldV2 {
  id: string;
  location: string;
  status: string;
  created_at: number;
  arrival_time: number;
  participants: {
    attackers: string[];
    defenders: string[];
  };
  forces: any;
}

interface BattlefieldsV2Data {
  [battleId: string]: BattlefieldV2;
}

class BattleStatusService {
  private battlefieldsData: BattlefieldsV2Data | null = null;
  private lastFetchTime = 0;
  private cacheDuration = 5000; // Cache pendant 5 secondes

  /**
   * Récupère les données de battlefields_v2.json depuis le serveur
   */
  private async fetchBattlefieldsData(): Promise<BattlefieldsV2Data> {
    const now = Date.now();
    
    // Utiliser le cache si les données sont récentes (réduit à 2 secondes)
    if (this.battlefieldsData && (now - this.lastFetchTime) < 2000) {
  // console.log('🔄 [BattleStatusService] Utilisation du cache (âge:', now - this.lastFetchTime, 'ms)');
      return this.battlefieldsData;
    }

    try {
      // Utiliser l'API du serveur au lieu du fichier statique + timestamp pour éviter le cache navigateur
      const timestamp = Date.now();
  // console.log('🌐 [BattleStatusService] Requête vers API:', `/api/v2/battlefields/all?t=${timestamp}`);
      
      const response = await fetch(`/api/v2/battlefields/all?t=${timestamp}`);
      if (response.ok) {
        const result = await response.json();
  // console.log('📥 [BattleStatusService] Réponse API reçue:', result);
        
        if (result.success && result.battlefields) {
          this.battlefieldsData = result.battlefields;
          this.lastFetchTime = now;
          // console.log('✅ [BattleStatusService] Données mises en cache:', Object.keys(this.battlefieldsData || {}).length, 'batailles');
          return this.battlefieldsData || {};
        } else {
          console.warn('⚠️ [BattleStatusService] Réponse API sans succès:', result);
        }
      } else {
        console.warn('⚠️ [BattleStatusService] Réponse HTTP non-OK:', response.status, response.statusText);
      }
    } catch (error) {
      console.warn('⚔️ [BattleStatusService] Erreur lors du chargement des battlefields_v2:', error);
    }

    return {};
  }

  /**
   * Vérifie s'il y a une bataille en cours dans une ville donnée
   */
  async hasBattleInCity(cityId: string): Promise<boolean> {
    const battlefields = await this.fetchBattlefieldsData();

    for (const battlefield of Object.values(battlefields)) {
      if (battlefield.location === cityId && 
          (battlefield.status === 'battle_ready' || battlefield.status === 'in_progress')) {
        return true;
      }
    }

    return false;
  }

  /**
   * Récupère les informations de bataille pour une ville
   */
  async getBattleInfoForCity(cityId: string): Promise<BattlefieldV2 | null> {
    const battlefields = await this.fetchBattlefieldsData();

    for (const battlefield of Object.values(battlefields)) {
      if (battlefield.location === cityId && 
          (battlefield.status === 'battle_ready' || battlefield.status === 'in_progress')) {
        return battlefield;
      }
    }

    return null;
  }

  /**
   * Récupère toutes les villes ayant des batailles en cours
   */
  async getCitiesWithBattles(): Promise<string[]> {
    // Toujours invalider le cache pour obtenir les données les plus récentes
    this.invalidateCache();
    
    const battlefields = await this.fetchBattlefieldsData();
    const citiesWithBattles = new Set<string>();

  // console.log('🔍 [BattleStatusService] Battlefields récupérés:', battlefields);

    for (const battlefield of Object.values(battlefields)) {
  // console.log(`🔍 [BattleStatusService] Vérification bataille ${battlefield.id} - location: ${battlefield.location}, status: ${battlefield.status}`);
      
      if (battlefield.status === 'battle_ready' || battlefield.status === 'in_progress') {
        citiesWithBattles.add(battlefield.location);
  // console.log(`✅ [BattleStatusService] Ville ${battlefield.location} ajoutée (status: ${battlefield.status})`);
      } else {
  // console.log(`❌ [BattleStatusService] Ville ${battlefield.location} ignorée (status: ${battlefield.status})`);
      }
    }

  // console.log('🔍 [BattleStatusService] Villes finales avec batailles:', Array.from(citiesWithBattles));
    return Array.from(citiesWithBattles);
  }

  /**
   * Invalide le cache pour forcer un rechargement
   */
  invalidateCache(): void {
    this.battlefieldsData = null;
    this.lastFetchTime = 0;
  }
}

// Instance singleton
export const battleStatusService = new BattleStatusService();
export default battleStatusService;