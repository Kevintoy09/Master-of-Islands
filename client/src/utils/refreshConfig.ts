/**
 * Configuration centralisée pour les intervalles de rafraîchissement
 * Tous les composants qui rafraîchissent des données doivent utiliser cette config
 */

import { getApiUrl } from './api';

let cachedInterval: number = 5; // Valeur par défaut: 5 secondes
let lastFetchTime: number = 0;
const CACHE_DURATION = 1000; // Cache pendant 1 seconde seulement

/**
 * Récupère l'intervalle de rafraîchissement configuré dans l'admin
 * Utilise un cache pour éviter trop de requêtes
 */
export async function getRefreshInterval(): Promise<number> {
  const now = Date.now();
  
  // Utiliser le cache si disponible et récent
  if (lastFetchTime > 0 && (now - lastFetchTime) < CACHE_DURATION) {
    return cachedInterval * 1000; // Convertir en millisecondes
  }
  
  try {
    const response = await fetch(`${getApiUrl()}/admin/api/refresh-interval/status`);
    const data = await response.json();
    
    if (data.success) {
      const newInterval = data.interval_seconds || 5;
      cachedInterval = newInterval;
      lastFetchTime = now;
      return cachedInterval * 1000; // Convertir en millisecondes
    }
  } catch (error) {
    console.error('Erreur lors de la récupération de l\'intervalle de rafraîchissement:', error);
  }
  
  // Valeur par défaut: 5 secondes
  cachedInterval = 5;
  return 5000;
}


