/**
 * Cache intelligent pour /api/universe
 * Évite de recharger 3.4 MB à chaque changement de page
 */

interface UniverseData {
  islands: any[];
  cities: any[];
  players: any[];
  [key: string]: any;
}

class UniverseCache {
  private cache: UniverseData | null = null;
  private cacheTime: number = 0;
  private cacheDuration: number = 60000; // 60 secondes
  private fetchPromise: Promise<UniverseData> | null = null;

  /**
   * Récupère l'univers avec cache intelligent
   */
  async getUniverse(apiUrl: string, forceRefresh: boolean = false): Promise<UniverseData> {
    const now = Date.now();
    
    // Si cache valide et pas de forceRefresh, retourner le cache
    if (!forceRefresh && this.cache && (now - this.cacheTime) < this.cacheDuration) {
      return this.cache;
    }

    // Si un fetch est déjà en cours, attendre sa réponse (évite les doublons)
    if (this.fetchPromise) {
      return this.fetchPromise;
    }

    // Nouveau fetch
    this.fetchPromise = fetch(`${apiUrl}/api/universe`)
      .then(res => res.json())
      .then(data => {
        this.cache = data;
        this.cacheTime = now;
        this.fetchPromise = null;
        return data;
      })
      .catch(err => {
        this.fetchPromise = null;
        throw err;
      });

    return this.fetchPromise;
  }

  /**
   * Invalide le cache (à appeler après une colonisation, etc.)
   */
  invalidate(): void {
    console.log('🔄 [CACHE] Cache universe invalidé');
    this.cache = null;
    this.cacheTime = 0;
  }

  /**
   * Récupère une île spécifique depuis le cache
   */
  async getIsland(apiUrl: string, islandId: string): Promise<any | null> {
    const universe = await this.getUniverse(apiUrl);
    return universe.islands?.find((i: any) => i.id === islandId) || null;
  }

  /**
   * Récupère les villes depuis le cache
   */
  async getCities(apiUrl: string): Promise<any[]> {
    const universe = await this.getUniverse(apiUrl);
    return universe.cities || [];
  }
}

// Instance singleton
export const universeCache = new UniverseCache();
