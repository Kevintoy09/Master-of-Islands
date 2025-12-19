import { useState, useEffect } from 'react';
import { getApiUrl } from '../utils/api';

interface UnlockedResourcesState {
  [resource: string]: boolean;
}

export const useUnlockedResources = (playerId: string | null) => {
  const [unlockedResources, setUnlockedResources] = useState<UnlockedResourcesState>({});
  const [loading, setLoading] = useState(false);
  const [lastLoadedPlayerId, setLastLoadedPlayerId] = useState<string | null>(null);

  // Ressources à vérifier (celles qui peuvent être verrouillées)
  const resourcesToCheck = [
    'marble', 'wine', 'horse', 'glass',           // Ressources avancées
    'coal', 'gunpowder', 'spices', 'cotton'      // Ressources industrielles
  ];

  useEffect(() => {
    // Ne recharger que si le playerId a vraiment changé (pas juste un re-render)
    if (!playerId || playerId === lastLoadedPlayerId) return;

    const checkUnlockedResources = async () => {
      setLoading(true);
      try {
        // Utiliser la nouvelle API optimisée qui récupère tout d'un coup
        const response = await fetch(
          `${getApiUrl()}/api/research/unlocked-resources/${playerId}`
        );
        
        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            setUnlockedResources(data.unlocked_resources);
            setLastLoadedPlayerId(playerId); // Marquer ce joueur comme chargé
          } else {
            console.warn('Erreur API unlocked-resources:', data.message);
            // Fallback : considérer toutes les ressources comme débloquées
            const fallbackStates: UnlockedResourcesState = {};
            resourcesToCheck.forEach(resource => {
              fallbackStates[resource] = true;
            });
            setUnlockedResources(fallbackStates);
            setLastLoadedPlayerId(playerId);
          }
        } else {
          console.warn(`Erreur HTTP ${response.status} lors de la récupération des ressources`);
          // Fallback : considérer toutes les ressources comme débloquées
          const fallbackStates: UnlockedResourcesState = {};
          resourcesToCheck.forEach(resource => {
            fallbackStates[resource] = true;
          });
          setUnlockedResources(fallbackStates);
          setLastLoadedPlayerId(playerId);
        }
      } catch (error) {
        console.error('Erreur lors de la vérification des ressources débloquées:', error);
      } finally {
        setLoading(false);
      }
    };

    checkUnlockedResources();
  }, [playerId, lastLoadedPlayerId]);

  const isResourceUnlocked = (resource: string): boolean => {
    // Ressources de base toujours débloquées
    const basicResources = ['wood', 'stone', 'iron', 'cereal', 'papyrus', 'gold', 'population_total', 'population_free'];
    if (basicResources.includes(resource)) {
      return true;
    }

    // Vérifier dans l'état
    return unlockedResources[resource] ?? true; // Par défaut débloqué si pas d'info
  };

  const forceRefresh = () => {
    // Force le rechargement en réinitialisant le cache
    setLastLoadedPlayerId(null);
  };

  return { 
    isResourceUnlocked, 
    loading, 
    unlockedResources,
    forceRefresh 
  };
};