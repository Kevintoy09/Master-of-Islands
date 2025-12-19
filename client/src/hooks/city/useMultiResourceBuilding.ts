import { useState, useEffect, useCallback } from 'react';
import { CityBuilding } from '../../types';

interface MultiResourceData {
  [resourceKey: string]: {
    baseProduction: number;
    bonus: number;
    totalProduction: number;
    hourlyProduction: number;
  };
}

interface ResourceConfig {
  key: string;
  name: string;
  icon: string;
}

interface MultiResourceBuildingConfig {
  cityId: string;
  building: CityBuilding;
  buildingType: 'resource_center';
  resources: ResourceConfig[];
}

export const useMultiResourceBuilding = ({ cityId, building, buildingType, resources }: MultiResourceBuildingConfig) => {
  const [productionData, setProductionData] = useState<MultiResourceData>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Configuration des bonus par niveau selon le type de bâtiment
  const getBonusForLevel = useCallback((level: number): number => {
    const bonusConfigs = {
      resource_center: [10, 20, 30], // Centre de Ressources: +10%, +20%, +30% (corrigé selon buildings.json)
    };
    
    const bonuses = bonusConfigs[buildingType] || [15, 25, 40];
    return bonuses[level - 1] || 0;
  }, [buildingType]);

  const getNextLevelBonus = useCallback((level: number): number => {
    if (level >= 3) return 0;
    return getBonusForLevel(level + 1);
  }, [getBonusForLevel]);

  // Charger les données de production pour toutes les ressources
  const loadProductionData = useCallback(async () => {
    if (!cityId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/city/${cityId}`);
      if (!response.ok) {
        throw new Error('Impossible de charger les données de la ville');
      }
      
      const data = await response.json();
      const buildingBonus = data.resources?.building_bonus || {};
      
      const newProductionData: MultiResourceData = {};
      
      // Charger les données pour chaque ressource
      for (const resource of resources) {
        try {
          const prodResponse = await fetch(`/api/city/${cityId}/production/${resource.key}`);
          if (prodResponse.ok) {
            const prodData = await prodResponse.json();
            
            // Utiliser les vraies données de production de l'API
            const baseProduction = prodData.baseProduction || 0;  // Production de base (ouvriers + sites)
            const buildingBonus = prodData.buildingBonus || 0;   // Bonus du Centre de Ressources
            const totalProduction = prodData.totalProduction || baseProduction; // Production totale
            
            newProductionData[resource.key] = {
              baseProduction,
              bonus: buildingBonus,
              totalProduction,
              hourlyProduction: totalProduction * 3600
            };
          } else {
            console.error(`Erreur API production ${resource.key}:`, prodResponse.status);
            // Fallback : récupérer depuis les données générales de la ville
            const bonus = buildingBonus[resource.key] || 0;
            
            // Pour le fallback, on ne peut pas connaître la vraie production de base
            // On affiche au moins le bonus correctement
            newProductionData[resource.key] = {
              baseProduction: 0, // Indique qu'on n'a pas les vraies données
              bonus,
              totalProduction: 0,
              hourlyProduction: 0
            };
          }
        } catch (prodErr) {
          console.error(`Erreur récupération production ${resource.key}:`, prodErr);
          // Fallback simple pour cette ressource
          const bonus = buildingBonus[resource.key] || 0;
          
          newProductionData[resource.key] = {
            baseProduction: 0, // Indique qu'on n'a pas les vraies données
            bonus,
            totalProduction: 0,
            hourlyProduction: 0
          };
        }
      }
      
      setProductionData(newProductionData);
    } catch (err) {
      console.error('Erreur chargement données production multi-ressources:', err);
      setError(err instanceof Error ? err.message : 'Erreur de chargement');
    } finally {
      setLoading(false);
    }
  }, [cityId, resources]);

  // Améliorer le bâtiment
  const upgradeBuilding = useCallback(async (): Promise<boolean> => {
    if (building.level >= 3) {
      setError('Niveau maximum atteint');
      return false;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/city/${cityId}/upgrade-building`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          slot_id: building.slot_id
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Erreur lors de l\'amélioration');
      }
      
      await loadProductionData();
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur d\'amélioration');
      return false;
    } finally {
      setLoading(false);
    }
  }, [cityId, building.slot_id, building.level, loadProductionData]);

  // Charger les données au montage et lors des changements
  useEffect(() => {
    loadProductionData();
  }, [loadProductionData]);

  // Calculer les informations de niveau
  const currentBonus = getBonusForLevel(building.level);
  const nextLevelBonus = getNextLevelBonus(building.level);
  const canUpgrade = building.level < 3;

  return {
    productionData,
    loading,
    error,
    currentBonus,
    nextLevelBonus,
    canUpgrade,
    getBonusForLevel,
    upgradeBuilding,
    reloadProduction: loadProductionData
  };
};
