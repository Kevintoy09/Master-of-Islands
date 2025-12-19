/**
 * Configuration API pour Master of Islands
 * Gère automatiquement les URLs selon l'environnement
 */

const getApiUrl = (): string => {
  // En production, utiliser une URL relative (même domaine que le frontend)
  if (process.env.NODE_ENV === 'production') {
    // URL relative - Flask et React sont sur le même domaine
    return '';  // Chemin relatif : les appels /api/* iront vers le même serveur
  }
  
  // En développement local
  return 'http://localhost:5000';
};

export const API_CONFIG = {
  BASE_URL: getApiUrl(),
  TIMEOUT: 30000, // 30 secondes
  ENABLE_LOGS: process.env.REACT_APP_ENV !== 'production'
};

// Helper pour construire les URLs d'API
export const buildApiUrl = (endpoint: string): string => {
  // Enlever le slash initial si présent
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `${API_CONFIG.BASE_URL}/${cleanEndpoint}`;
};

// Logger conditionnel (désactivé en production)
export const apiLog = (...args: any[]) => {
  if (API_CONFIG.ENABLE_LOGS) {
    console.log('[API]', ...args);
  }
};

export const apiError = (...args: any[]) => {
  if (API_CONFIG.ENABLE_LOGS) {
    console.error('[API ERROR]', ...args);
  }
};
