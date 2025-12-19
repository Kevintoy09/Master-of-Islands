/**
 * useUnitsActed.ts
 * 
 * Hook pour récupérer les unités qui ont déjà agi dans le round actuel
 * Permet l'affichage visuel différencié des unités disponibles/indisponibles
 */

import { useState, useEffect } from 'react';
import { getApiUrl } from '../utils/api';

export const useUnitsActed = (battleId: string | null, refreshTrigger?: any) => {
  const [unitsActed, setUnitsActed] = useState<string[]>([]);
  const [currentRound, setCurrentRound] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUnitsActed = async () => {
    if (!battleId) {
      setUnitsActed([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${getApiUrl()}/api/v2/battle/units-acted/${battleId}`);
      const data = await response.json();

      if (data.success) {
        setUnitsActed(data.units_that_acted || []);
        setCurrentRound(data.current_round || 1);
      } else {
        setError(data.error || 'Erreur lors de la récupération des unités');
        setUnitsActed([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur réseau');
      setUnitsActed([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUnitsActed();
  }, [battleId, refreshTrigger]);

  // Fonction pour vérifier si une unité a déjà agi
  const hasUnitActed = (unitId: string): boolean => {
    return unitsActed.includes(unitId);
  };

  return {
    unitsActed,
    currentRound,
    loading,
    error,
    hasUnitActed,
    refreshUnitsActed: fetchUnitsActed
  };
};

export default useUnitsActed;