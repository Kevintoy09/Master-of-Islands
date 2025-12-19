import { useEffect, useRef, useState } from 'react';
import { getRefreshInterval } from '../utils/refreshConfig';

/**
 * Hook personnalisé qui gère un intervalle de rafraîchissement dynamique
 * L'intervalle se met automatiquement à jour quand l'admin change la configuration
 */
export function useRefreshInterval(callback: () => void | Promise<void>, deps: any[] = []) {
  const [currentInterval, setCurrentInterval] = useState<number>(5000);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const checkIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const callbackRef = useRef(callback);

  // Mettre à jour la référence du callback
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  // Charger l'intervalle initial et vérifier périodiquement les changements
  useEffect(() => {
    const lastKnownIntervalRef = { current: 0 };

    const setup = async () => {
      // Charger l'intervalle initial
      const intervalMs = await getRefreshInterval();
      lastKnownIntervalRef.current = intervalMs;
      setCurrentInterval(intervalMs);

      // Vérifier périodiquement si l'intervalle a changé (toutes les 2 secondes)
      checkIntervalRef.current = setInterval(async () => {
        const latestInterval = await getRefreshInterval();
        if (latestInterval !== lastKnownIntervalRef.current) {
          lastKnownIntervalRef.current = latestInterval;
          setCurrentInterval(latestInterval);
        }
      }, 2000);
    };

    setup();

    return () => {
      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
      }
    };
  }, []);

  // Configurer l'intervalle
  useEffect(() => {
    // Exécuter immédiatement
    callbackRef.current();

    // Configurer l'intervalle
    intervalRef.current = setInterval(() => {
      callbackRef.current();
    }, currentInterval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [currentInterval, ...deps]);

  return currentInterval;
}
