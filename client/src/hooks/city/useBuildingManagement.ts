// Hook custom pour gérer les bâtiments sélectionnés et leurs actions
import { useState, useCallback, useMemo } from 'react';
import { CityBuilding } from '../../types';
import { BuildingService } from '../../services/BuildingService';
import { usePlayerResearch } from '../usePlayerResearch';

interface UseBuildingManagementOptions {
  cityId: string | undefined;
  onCityDataChange: () => Promise<any>;
}

interface ErrorInfo {
  message: string;
  title?: string;
  icon?: string;
}

export const useBuildingManagement = ({ cityId, onCityDataChange }: UseBuildingManagementOptions) => {
  const [selectedBuilding, setSelectedBuilding] = useState<CityBuilding | null>(null);
  const [buildingActionLoading, setBuildingActionLoading] = useState(false);
  const [buildingActionMsg, setBuildingActionMsg] = useState<string | null>(null);
  const [errorPopup, setErrorPopup] = useState<ErrorInfo | null>(null);
  const { getInstantFinishThreshold } = usePlayerResearch();

  // Actions de bâtiment
  const developBuilding = useCallback(async (building: CityBuilding) => {
    if (!cityId) return;
    
    setErrorPopup(null);
    
    try {
      await BuildingService.buildBuilding(cityId, building.slot_id, building.name);
      await onCityDataChange();
    } catch (error: any) {
      // Parser l'erreur JSON si disponible
      let errorData: any = {};
      try {
        errorData = JSON.parse(error.message);
      } catch {
        errorData = { error: error.message };
      }

      // Gestion spécifique des erreurs
      if (errorData.type === 'max_concurrent_buildings_reached') {
        setErrorPopup({
          title: '🏗️ Construction en cours',
          message: `Vous ne pouvez développer que ${errorData.max} bâtiment(s) à la fois.\n\nActuellement : ${errorData.current}/${errorData.max} construction(s) en cours.\n\nDébloquez la recherche "Planification Urbaine" pour augmenter cette limite !`,
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
      } else {
        setErrorPopup({
          title: '⚠️ Erreur',
          message: errorData.error || error.message || 'Impossible de développer le bâtiment',
          icon: '⚠️'
        });
      }
    }
  }, [cityId, onCityDataChange]);

  const destroyBuilding = useCallback(async (building: CityBuilding) => {
    if (!cityId) return;
    
    const currentLevel = building.level || 1;
    let confirmMessage;
    
    if (currentLevel > 1) {
      confirmMessage = `Voulez-vous vraiment rétrograder ${building.name} du niveau ${currentLevel} au niveau ${currentLevel - 1} ?`;
    } else {
      confirmMessage = `Voulez-vous vraiment détruire définitivement ${building.name} ?`;
    }
    
    const confirmed = window.confirm(confirmMessage);
    if (!confirmed) return;
    
    try {
      const result = await BuildingService.destroyBuilding(cityId, building.slot_id);
      alert(result.message);
      
      // Recharger les données et fermer le popup si nécessaire
      const updatedCityData = await onCityDataChange();
      if (result.action_type === 'downgrade' || result.action_type === 'destroy') {
        // Vérifier si le bâtiment existe encore
        const updatedBuilding = updatedCityData?.buildings?.find(
          (b: CityBuilding) => b.slot_id === building.slot_id
        );
        if (updatedBuilding) {
          setSelectedBuilding(updatedBuilding);
        } else {
          setSelectedBuilding(null);
        }
      }
    } catch (error: any) {
      alert(error.message || 'Impossible de détruire');
    }
  }, [cityId, onCityDataChange]);

  const finishInstantConstruction = useCallback(async (slotId: string) => {
    if (!cityId) return;
    
    try {
      setBuildingActionLoading(true);
      const result = await BuildingService.finishConstruction(cityId, slotId);
      setBuildingActionMsg(result.message);
      // Recharger les données pour mettre à jour le timer
      await onCityDataChange();
    } catch (error: any) {
      setBuildingActionMsg(`Erreur: ${error.message}`);
    } finally {
      setBuildingActionLoading(false);
    }
  }, [cityId, onCityDataChange]);

  // Calculer les capacités d'actions
  const canFinishInstant = useMemo(() => {
    if (!selectedBuilding || !selectedBuilding.construction_end) return false;
    
    const now = Math.floor(Date.now() / 1000);
    const isUnderConstruction = selectedBuilding.construction_end > now;
    const timeRemaining = isUnderConstruction ? selectedBuilding.construction_end - now : 0;
    
    // Récupérer le seuil depuis la recherche sablier
    const threshold = getInstantFinishThreshold();
    const isCloseToFinish = threshold > 0 && timeRemaining <= threshold;
    
    return isUnderConstruction && isCloseToFinish;
  }, [selectedBuilding, getInstantFinishThreshold]);

  // Gérer la mise à jour du bâtiment sélectionné après reload
  const updateSelectedBuildingFromCity = useCallback((cityData: any) => {
    if (selectedBuilding && cityData?.buildings) {
      const updatedBuilding = cityData.buildings.find(
        (b: CityBuilding) => b.slot_id === selectedBuilding.slot_id
      );
      if (updatedBuilding) {
        setSelectedBuilding(updatedBuilding);
      } else {
        setSelectedBuilding(null);
      }
    }
  }, [selectedBuilding]);

  return {
    selectedBuilding,
    setSelectedBuilding,
    buildingActionLoading,
    buildingActionMsg,
    setBuildingActionMsg,
    errorPopup,
    setErrorPopup,
    developBuilding,
    destroyBuilding,
    finishInstantConstruction,
    canFinishInstant,
    updateSelectedBuildingFromCity
  };
};
