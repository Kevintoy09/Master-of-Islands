// Hook custom pour gérer la construction de nouveaux bâtiments
import { useState, useCallback } from 'react';
import { Slot } from '../../types';
import { BuildingService } from '../../services/BuildingService';

interface UseBuildingConstructionOptions {
  cityId: string | undefined;
  onCityDataChange: () => Promise<any>;
}

interface ErrorInfo {
  message: string;
  title?: string;
  icon?: string;
}

export const useBuildingConstruction = ({ cityId, onCityDataChange }: UseBuildingConstructionOptions) => {
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null);
  const [buildingsList, setBuildingsList] = useState<any[]>([]);
  const [buildingCostsWithBonus, setBuildingCostsWithBonus] = useState<any>({});
  const [loadingBuildings, setLoadingBuildings] = useState(false);
  const [buildingsError, setBuildingsError] = useState("");
  const [buildingActionLoading, setBuildingActionLoading] = useState(false);
  const [buildingActionMsg, setBuildingActionMsg] = useState<string | null>(null);
  const [errorPopup, setErrorPopup] = useState<ErrorInfo | null>(null);

  // Gérer la sélection d'un slot pour construction
  const handleSlotClick = useCallback(async (slot: Slot) => {
    if (!cityId) return;
    
    setSelectedSlot(slot);
    setBuildingsError("");
    setBuildingActionMsg(null);
    setLoadingBuildings(true);
    
    try {
      // ⚡ OPTIMISATION : 1 seul appel API qui retourne les bâtiments ET les coûts avec bonus
      const buildingsData = await BuildingService.getAvailableBuildings(cityId, slot.type);
      
      setBuildingsList(buildingsData.buildings || []);
      setBuildingCostsWithBonus(buildingsData.building_costs || {}); // Coûts inclus dans la réponse
      
    } catch (error: any) {
      setBuildingsError(error.message || "Erreur inconnue");
      setBuildingsList([]);
    } finally {
      setLoadingBuildings(false);
    }
  }, [cityId]);

  // Construire un bâtiment
  const constructBuilding = useCallback(async (buildingName: string) => {
    if (!cityId || !selectedSlot || buildingActionLoading) return;
    
    setBuildingActionLoading(true);
    setBuildingActionMsg(null);
    setErrorPopup(null);
    
    try {
      await BuildingService.buildBuilding(cityId, selectedSlot.id, buildingName);
      setBuildingActionMsg('Bâtiment construit avec succès !');
      
      // Attendre un peu puis fermer et recharger
      setTimeout(async () => {
        setSelectedSlot(null);
        setBuildingActionMsg(null);
        await onCityDataChange();
      }, 900);
      
    } catch (error: any) {
      // Parser l'erreur JSON si disponible
      let errorData: any = {};
      try {
        errorData = JSON.parse(error.message);
      } catch {
        errorData = { error: error.message };
      }

      // Gestion spécifique des erreurs de construction
      if (errorData.type === 'max_concurrent_buildings_reached') {
        setErrorPopup({
          title: '🏗️ Construction en cours',
          message: `Vous ne pouvez construire que ${errorData.max} bâtiment(s) à la fois.\n\nActuellement : ${errorData.current}/${errorData.max} construction(s) en cours.\n\nDébloquez la recherche "Planification Urbaine" pour augmenter cette limite !`,
          icon: '🏗️'
        });
      } else if (errorData.type === 'insufficient_resources') {
        const missingResources = Object.entries(errorData.missing || {})
          .map(([res, amt]) => `${res}: ${amt}`)
          .join(', ');
        setErrorPopup({
          title: '💰 Ressources insuffisantes',
          message: `Il vous manque : ${missingResources}`,
          icon: '💰'
        });
      } else if (errorData.type === 'research_required') {
        setErrorPopup({
          title: '🔬 Recherche requise',
          message: errorData.error || 'Une recherche doit être débloquée avant de construire ce bâtiment.',
          icon: '🔬'
        });
      } else if (errorData.type === 'max_instances_reached') {
        setErrorPopup({
          title: '🏛️ Limite atteinte',
          message: `Vous avez déjà ${errorData.current} ${buildingName} dans cette ville. Maximum autorisé : ${errorData.max}.`,
          icon: '🏛️'
        });
      } else {
        // Erreur générique
        setErrorPopup({
          title: '⚠️ Erreur',
          message: errorData.error || error.message || 'Impossible de construire le bâtiment',
          icon: '⚠️'
        });
      }
    } finally {
      setBuildingActionLoading(false);
    }
  }, [cityId, selectedSlot, buildingActionLoading, onCityDataChange]);

  const closeConstructionPopup = useCallback(() => {
    setSelectedSlot(null);
    setBuildingActionMsg(null);
    setBuildingsError("");
    setErrorPopup(null);
  }, []);

  return {
    selectedSlot,
    setSelectedSlot,
    buildingsList,
    buildingCostsWithBonus,
    loadingBuildings,
    buildingsError,
    buildingActionLoading,
    buildingActionMsg,
    errorPopup,
    setErrorPopup,
    handleSlotClick,
    constructBuilding,
    closeConstructionPopup
  };
};
