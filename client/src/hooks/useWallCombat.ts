/**
 * useWallCombat.ts
 * Hook personnalisé pour gérer les combats contre les murs
 * Simplifie SimpleBattlefieldV2 en déplaçant toute la logique des murs
 */

import { useCallback } from 'react';
import { WallCombatService } from '../services/WallCombatService';
import { CompactUnit } from '../types/index';
import { extractUnitType } from '../utils/combatUtils';


interface UseWallCombatProps {
  selectedCompactUnit: CompactUnit | null;
  battleUnits: any[];
  setCombatData: (data: any) => void;
  setCombatPopupOpen: (open: boolean) => void;
  attackWallGroup: (groupIndex: number, damage: number) => Promise<void>;
  actualBattleId: string;
  unitStats?: any; // Stats d'unités chargées depuis l'API
}

export const useWallCombat = ({
  selectedCompactUnit,
  battleUnits,
  setCombatData,
  setCombatPopupOpen,
  attackWallGroup,
  actualBattleId,
  unitStats
}: UseWallCombatProps) => {



  // Fonction pour récupérer les vraies stats d'une unité
  const getUnitCombatStats = useCallback((unit: CompactUnit) => {
    if (!unitStats || !unit) {
      return null;
    }

    const unitType = extractUnitType(unit.unitId);
    
    // Chercher dans toutes les ères
    for (const era of Object.keys(unitStats)) {
      if (unitStats[era][unitType]) {
        const baseStats = unitStats[era][unitType];
        return {
          type: unitType,
          name: baseStats.name || unitType,
          count: unit.unitCount || 1,
          hp: unit.hp || baseStats.hp || 100,
          attack_melee: baseStats.attack_melee || 0,
          defense_melee: baseStats.defense_melee || 0,
          attack_ranged: baseStats.attack_ranged || 0,
          defense_ranged: baseStats.defense_ranged || 0,
          category: baseStats.category || 'unknown',
          special_abilities: baseStats.special_abilities || []
        };
      }
    }
    
    return null;
  }, [unitStats]);  // Fonction pour ouvrir le combat popup pour attaquer un mur
  const handleWallCombatPopup = useCallback((wallGroup: any, wallStats: any) => {
    // Validation des données
    const validation = WallCombatService.validateCombatData(selectedCompactUnit, wallGroup, wallStats);
    if (!validation.isValid) {
      alert(validation.errorMessage);
      return;
    }

    if (!selectedCompactUnit) {
      alert('Aucune unité sélectionnée.');
      return;
    }
    
    const attackerCombatStats = getUnitCombatStats(selectedCompactUnit);
    if (!attackerCombatStats) {
      alert('Impossible de récupérer les statistiques de l\'unité attaquante.');
      return;
    }

    // Préparer les données du mur défenseur
    const wallDefenderStats = {
      type: 'wall',
      name: `🧱 Groupe de Murs #${wallGroup.group_index + 1}`,
      count: 1,
      hp: wallGroup.hp,
      max_hp: wallGroup.max_hp,
      attack_melee: 0,
      defense_melee: wallStats.defense,
      attack_ranged: wallStats.attack_ranged,
      defense_ranged: wallStats.defense,
      range: wallStats.range || 2,
      category: 'structure',
      special_abilities: [],
      isWall: true,
      wallGroup: wallGroup,
      wallStats: wallStats,
      total_positions: wallGroup.total_positions
    };

    // Configurer le popup de combat
    setCombatData({
      attacker: selectedCompactUnit,
      defender: null,
      attackerStats: attackerCombatStats,
      defenderStats: wallDefenderStats
    });

    setCombatPopupOpen(true);
  }, [selectedCompactUnit, getUnitCombatStats, setCombatData, setCombatPopupOpen]);

  // Fonction pour appliquer les dégâts au mur
  const handleWallDamage = useCallback(async (result: any, defenderStats: any) => {
    if (defenderStats.isWall) {
      const wallGroup = defenderStats.wallGroup;
      const damage = result.damage || 25;
      
      await WallCombatService.applyWallDamage(wallGroup, damage, actualBattleId, attackWallGroup);
      return true; // Indique que c'était un combat de mur
    }
    return false; // Combat normal
  }, [actualBattleId, attackWallGroup]);

  return {
    handleWallCombatPopup,
    handleWallDamage
  };
};