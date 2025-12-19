import { useState, useEffect, useCallback } from 'react';
import { getApiUrl } from '../utils/api';
import { useRefreshInterval } from './useRefreshInterval';

interface PopulationData {
  population: number;
  population_free: number;
  info: {
    current_population: number;
    max_capacity: number;
    base_growth_per_hour: number;
    growth_per_hour: number;
    growth_per_second: number;
    real_growth_per_hour: number;
    time_multiplier: number;
    time_info: string;
    satisfaction: number;
  };
  last_update: number;
}

interface UseAutoUpdatePopulationOptions {
  cityId: string | undefined;
  enabled?: boolean; // pour pouvoir désactiver les mises à jour
}

export const useAutoUpdatePopulation = ({
  cityId,
  enabled = true
}: UseAutoUpdatePopulationOptions) => {
  const [populationData, setPopulationData] = useState<PopulationData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPopulation = useCallback(async () => {
    if (!cityId || !enabled) return;
    
    try {
      setError(null);
      const response = await fetch(`${getApiUrl()}/api/city/${cityId}/population`);
      
      if (!response.ok) {
        // Si la ville n'existe pas (404), arrêter les requêtes
        if (response.status === 404) {
          console.warn(`Ville ${cityId} introuvable`);
          setError(`Ville ${cityId} introuvable`);
          return;
        }
        throw new Error(`Erreur HTTP: ${response.status}`);
      }
      
      const data = await response.json();
      setPopulationData(data);
    } catch (err) {
      console.error('Erreur lors de la récupération de la population:', err);
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    }
  }, [cityId, enabled]);

  // Premier chargement
  useEffect(() => {
    if (cityId && enabled) {
      setLoading(true);
      fetchPopulation().finally(() => setLoading(false));
    }
  }, [cityId, enabled, fetchPopulation]);

  // Utiliser le hook de rafraîchissement centralisé
  useRefreshInterval(fetchPopulation, [cityId, enabled]);

  // Fonction pour forcer une mise à jour manuelle
  const forceUpdate = async () => {
    setLoading(true);
    await fetchPopulation();
    setLoading(false);
  };

  return {
    populationData,
    loading,
    error,
    forceUpdate
  };
}
