/**
 * useUnitStats.ts
 * 
 * Hook pour charger les statistiques d'unités depuis le serveur
 */

import { useState, useEffect } from 'react';
import { getApiUrl } from '../utils/api';

export const useUnitStats = () => {
  const [unitStats, setUnitStats] = useState<any>(null);

  useEffect(() => {
    const loadUnitStats = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/v2/unit_stats`);
        const data = await response.json();
        setUnitStats(data);
      } catch (error) {
        // Erreur silencieuse
      }
    };
    
    loadUnitStats();
  }, []);

  return unitStats;
};
