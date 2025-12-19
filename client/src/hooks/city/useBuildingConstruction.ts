// Hook custom pour gérer la construction de nouveaux bâtiments
import { useState, useCallback } from 'react';
import { Slot } from '../../types';
import { BuildingService } from '../../services/BuildingService';

interface UseBuildingConstructionOptions {
  cityId: string | undefined;
  onCityDataChange: () => Promise<any>;
}

export const useBuildingConstruction = ({ cityId, onCityDataChange }: UseBuildingConstructionOptions) => {
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null);
  const [buildingsList, setBuildingsList] = useState<any[]>([]);
  const [buildingCostsWithBonus, setBuildingCostsWithBonus] = useState<any>({});
  const [loadingBuildings, setLoadingBuildings] = useState(false);
  const [buildingsError, setBuildingsError] = useState("");
  const [buildingActionLoading, setBuildingActionLoading] = useState(false);
  const [buildingActionMsg, setBuildingActionMsg] = useState<string | null>(null);

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
      setBuildingActionMsg('Erreur : ' + (error.message || 'Impossible de construire'));
    } finally {
      setBuildingActionLoading(false);
    }
  }, [cityId, selectedSlot, buildingActionLoading, onCityDataChange]);

  const closeConstructionPopup = useCallback(() => {
    setSelectedSlot(null);
    setBuildingActionMsg(null);
    setBuildingsError("");
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
    handleSlotClick,
    constructBuilding,
    closeConstructionPopup
  };
};
