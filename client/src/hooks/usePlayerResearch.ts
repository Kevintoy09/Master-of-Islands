import { useState, useEffect } from 'react';
import { useResearchDatabase } from './useResearchDatabase';
import { PlayerResearchService, PlayerResearchData, UnlockResearchRequest } from '../services/PlayerResearchService';
import { useUser } from './useUser';

export const usePlayerResearch = () => {
  const [playerResearchData, setPlayerResearchData] = useState<PlayerResearchData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { user } = useUser();
  
  // Base de données des recherches depuis le serveur
  const { 
    data: researchDatabase, 
    loading: dbLoading, 
    error: dbError,
    getResearchById 
  } = useResearchDatabase();

  const loadPlayerResearch = async () => {
    if (!user?.id) return;
    
    try {
      setLoading(true);
      setError(null);
      const data = await PlayerResearchService.getPlayerResearch(user.id);
      setPlayerResearchData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors du chargement des recherches');
      console.error('Erreur chargement recherches:', err);
    } finally {
      setLoading(false);
    }
  };

  const unlockResearch = async (researchId: string, researchData: UnlockResearchRequest) => {
    if (!user?.id) return { success: false, message: 'Utilisateur non connecté' };
    
    try {
      setLoading(true);
      const result = await PlayerResearchService.unlockResearch(user.id, researchId, researchData);
      
      if (result.success) {
        // Recharger les données après déverrouillage
        await loadPlayerResearch();
        return { success: true, message: result.message };
      } else {
        return { success: false, message: result.message };
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erreur lors du déverrouillage';
      console.error('Erreur déverrouillage recherche:', err);
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  };

  const isResearchUnlocked = (researchId: string): boolean => {
    return playerResearchData?.unlocked_research.includes(researchId) ?? false;
  };

  const getResourceBonus = (resource: string): number => {
    return playerResearchData?.research_effects?.resource_bonuses?.[resource] ?? 0;
  };

  const getInstantFinishThreshold = (): number => {
    // Chercher la recherche "sablier" débloquée
    if (!isResearchUnlocked('sablier')) {
      return 0; // Pas de finition instantanée possible
    }
    
    // Récupérer la valeur depuis research.json
    const research = getResearchById('sablier');
    return research?.effect?.instant_finish_threshold ?? 30; // Défaut: 30 secondes
  };

  const canUnlockResearch = (researchId: string): { canUnlock: boolean; reason?: string } => {
    if (!researchDatabase || !playerResearchData) {
      return { canUnlock: false, reason: 'Données non chargées' };
    }

    const research = getResearchById(researchId);
    if (!research) {
      return { canUnlock: false, reason: 'Recherche introuvable' };
    }

    // Vérifier si déjà débloquée
    if (isResearchUnlocked(researchId)) {
      return { canUnlock: false, reason: 'Recherche déjà débloquée' };
    }

    // Vérifier les prérequis
    const missingPrerequisites = research.prerequisites.filter((prereq: string) => !isResearchUnlocked(prereq));
    if (missingPrerequisites.length > 0) {
      return { canUnlock: false, reason: `Prérequis manquants: ${missingPrerequisites.join(', ')}` };
    }

    // Vérifier les ressources
    const researchPoints = playerResearchData.research_points;
    if (researchPoints < research.cost.research_points) {
      return { 
        canUnlock: false, 
        reason: `Points de recherche insuffisants (${research.cost.research_points} requis, ${researchPoints} disponibles)` 
      };
    }

    // TODO: Vérifier l'or si nécessaire
    if (research.cost.gold) {
      // On pourrait ajouter une vérification de l'or ici si on a accès aux données du joueur
    }

    return { canUnlock: true };
  };

  useEffect(() => {
    loadPlayerResearch();
  }, [user?.id]);

  return {
    // Données du joueur
    playerResearchData,
    loading: loading || dbLoading,
    error: error || dbError,
    
    // Actions
    loadPlayerResearch,
    unlockResearch,
    
    // Vérifications
    isResearchUnlocked,
    canUnlockResearch,
    
    // Utilitaires
    getResourceBonus,
    getInstantFinishThreshold,
    
    // Base de données des recherches
    researchDatabase: researchDatabase?.researches || [],
    categories: researchDatabase?.categories || [],
    getResearchById,
    getResearchesByCategory: (category: string) => {
      if (!researchDatabase) return [];
      return researchDatabase.researches.filter(research => research.category === category);
    },
    getAllCategories: () => ['economy', 'science', 'warfare', 'marine'] as const
  };
};