import { useState, useEffect, useCallback } from 'react';
import { CityBuilding } from '../../types';

interface ProductionData {
  baseProduction: number;
  bonus: number;
  totalProduction: number;
  hourlyProduction: number;
}

interface ProductionBuildingConfig {
  cityId: string;
  building: CityBuilding;
  resourceType: 'wood' | 'stone' | 'iron' | 'grain' | 'cereal' | 'papyrus';
  buildingType: 'sawmill' | 'resource_center' | 'farm';
}

export const useProductionBuilding = ({ cityId, building, resourceType, buildingType }: ProductionBuildingConfig) => {
  const [production, setProduction] = useState<ProductionData>({
    baseProduction: 0,
    bonus: 0,
    totalProduction: 0,
    hourlyProduction: 0
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Configuration des bonus par niveau selon le type de bâtiment
  const getBonusForLevel = useCallback((level: number): number => {
    const bonusConfigs = {
      sawmill: [10, 20, 30], // Scierie: +10%, +20%, +30%
      resource_center: [10, 20, 30],    // Centre de Ressources: +10%, +20%, +30% (corrigé selon buildings.json)
      farm: [8, 16, 25]      // Ferme: +8%, +16%, +25%
    };
    
    const bonuses = bonusConfigs[buildingType] || [10, 20, 30];
    return bonuses[level - 1] || 0;
  }, [buildingType]);

  const getNextLevelBonus = useCallback((level: number): number => {
    if (level >= 3) return 0;
    return getBonusForLevel(level + 1);
  }, [getBonusForLevel]);

  // Charger les données de production
  const loadProductionData = useCallback(async () => {
    if (!cityId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const prodResponse = await fetch(`/api/city/${cityId}/production/${resourceType}`);
      if (prodResponse.ok) {
        const prodData = await prodResponse.json();
        
        // Utiliser les vraies données de production de l'API
        const baseProduction = prodData.baseProduction || 0;
        const buildingBonus = prodData.buildingBonus || 0;
        const totalProduction = prodData.totalProduction || baseProduction;
        
        setProduction({
          baseProduction,
          bonus: buildingBonus,
          totalProduction,
          hourlyProduction: totalProduction * 3600
        });
      } else {
        throw new Error('Impossible de charger les données de production');
      }
    } catch (err) {
      console.error('Erreur chargement données production:', err);
      setError(err instanceof Error ? err.message : 'Erreur de chargement');
    } finally {
      setLoading(false);
    }
  }, [cityId, resourceType]);

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
    production,
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
