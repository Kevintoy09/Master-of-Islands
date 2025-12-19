/**
 * 🔧 Adaptateur de lecture Battlefield - Format optimisé V2
 * 
 * Lit les battlefields dans le format optimisé (4KB) avec hexMap compact
 * et les convertit en structure standardisée pour le moteur de jeu
 */

import { getApiUrl } from './api';

interface OptimizedBattlefield {
  template: {
    id: string;
    name: string;
    description?: string;
    size: { width: number; height: number };
    difficulty: string;
    deploymentZones: {
      attacker: {
        infantry: Array<[number, number]>;
        ranged: Array<[number, number]>;
        cavalry: Array<[number, number]>;
        hero?: Array<[number, number]>;
      };
      defender: {
        infantry: Array<[number, number]>;
        ranged: Array<[number, number]>;
        cavalry: Array<[number, number]>;
        hero?: Array<[number, number]>;
      };
    };
  };
  terrainDefinitions: { 
    [code: string]: {
      name: string;
      defenseBonus: number;
      attackPenalty: number;
      movementBonus: number;
    }
  };
  hexMap: string[];
  customBonusZones?: Array<{
    name: string;
    coords: Array<[number, number]>;
    bonuses: {
      defenseBonus: number;
      attackPenalty: number;
      movementBonus: number;
    };
  }>;
}

interface StandardizedHexCell {
  q: number;
  r: number;
  terrain: string;
  zone: string;
  defenseBonus: number;
  attackPenalty: number;
  movementBonus: number;
}

interface StandardizedBattlefield {
  id: string;
  name: string;
  description: string;
  width: number;
  height: number;
  difficulty: string;
  hexCells: StandardizedHexCell[];
  deploymentZones: {
    attacker: {
      infantry: Array<{ q: number; r: number; zoneCode?: string }>;
      ranged: Array<{ q: number; r: number; zoneCode?: string }>;
      cavalry: Array<{ q: number; r: number; zoneCode?: string }>;
      hero?: Array<{ q: number; r: number; zoneCode?: string }>;
    };
    defender: {
      infantry: Array<{ q: number; r: number; zoneCode?: string }>;
      ranged: Array<{ q: number; r: number; zoneCode?: string }>;
      cavalry: Array<{ q: number; r: number; zoneCode?: string }>;
      hero?: Array<{ q: number; r: number; zoneCode?: string }>;
    };
  };
}

class BattlefieldAdapter {
  
  /**
   * Charge un battlefield optimisé V2 et le convertit en format standardisé
   */
  async loadBattlefield(pathOrData: string | any): Promise<StandardizedBattlefield> {
    let battlefieldData: OptimizedBattlefield;
    
    // Si c'est un chemin, charger le fichier
    if (typeof pathOrData === 'string') {
      try {
        const response = await fetch(pathOrData);
        battlefieldData = await response.json();

      } catch (error) {
        throw new Error(`Erreur chargement battlefield: ${error}`);
      }
    } else {
      battlefieldData = pathOrData;
    }
    
    return this.convertOptimizedToStandard(battlefieldData);
  }
  

  
  /**
   * Convertit le nouveau format optimisé vers le format standardisé
   */
  private convertOptimizedToStandard(optimized: OptimizedBattlefield): StandardizedBattlefield {

    
    const hexCells: StandardizedHexCell[] = [];
    const { width, height } = optimized.template.size;
    
    // Reconstituer les hexCells depuis la hexMap
    for (let r = 0; r < height && r < optimized.hexMap.length; r++) {
      const row = optimized.hexMap[r];
      for (let q = 0; q < width && q < row.length; q++) {
        const terrainCode = row[q];
        
        // Ignorer les cases vides (X) - ne pas les ajouter aux hexCells
        if (terrainCode === 'X') {
          continue;
        }
        
        const terrainDef = optimized.terrainDefinitions[terrainCode];
        
        if (terrainDef) {
          let finalDefenseBonus = terrainDef.defenseBonus;
          let finalAttackPenalty = terrainDef.attackPenalty;
          let finalMovementBonus = terrainDef.movementBonus;
          
          // Appliquer les bonus des zones spéciales si elles existent
          if (optimized.customBonusZones) {
            const customZone = optimized.customBonusZones.find(zone => 
              zone.coords.some(([zq, zr]) => zq === q && zr === r)
            );
            if (customZone) {
              finalDefenseBonus = customZone.bonuses.defenseBonus;
              finalAttackPenalty = customZone.bonuses.attackPenalty;
              finalMovementBonus = customZone.bonuses.movementBonus;
            }
          }
          
          hexCells.push({
            q,
            r,
            terrain: terrainDef.name,
            zone: 'battlefield',
            defenseBonus: finalDefenseBonus,
            attackPenalty: finalAttackPenalty,
            movementBonus: finalMovementBonus
          });
        }
      }
    }
    
    // Fonction helper pour convertir les zones avec validation
    const convertZones = (zones: Array<[number, number]> | undefined, prefix: string) => {
      if (!zones || !Array.isArray(zones)) return [];
      return zones
        .filter(coord => Array.isArray(coord) && coord.length === 2 && typeof coord[0] === 'number' && typeof coord[1] === 'number')
        .map(([q, r], index) => ({
          q: Number(q),
          r: Number(r),
          zoneCode: `${prefix}${index + 1}`
        }));
    };

    // Convertir les zones de déploiement avec vérification robuste
    const deploymentZones = {
      attacker: {
        infantry: convertZones(optimized.template.deploymentZones.attacker?.infantry, 'AI'),
        ranged: convertZones(optimized.template.deploymentZones.attacker?.ranged, 'AR'),
        cavalry: convertZones(optimized.template.deploymentZones.attacker?.cavalry, 'AC'),
        hero: convertZones(optimized.template.deploymentZones.attacker?.hero, 'AH')
      },
      defender: {
        infantry: convertZones(optimized.template.deploymentZones.defender?.infantry, 'DI'),
        ranged: convertZones(optimized.template.deploymentZones.defender?.ranged, 'DR'),
        cavalry: convertZones(optimized.template.deploymentZones.defender?.cavalry, 'DC'),
        hero: convertZones(optimized.template.deploymentZones.defender?.hero, 'DH')
      }
    };
    
    return {
      id: optimized.template.id,
      name: optimized.template.name,
      description: optimized.template.description || '',
      width,
      height,
      difficulty: optimized.template.difficulty,
      hexCells,
      deploymentZones
    };
  }
  

  
  /**
   * Charge une liste de battlefields disponibles (format V2 optimisé uniquement)
   */
  async loadAvailableBattlefields(): Promise<string[]> {
    const battlefields = [
      'default_working_v2',
      'grande_carte_v2',
      'Austerlitz',
      'Overload_beach',
      'custom_battlefield_1_v2'
    ];
    
    const available: string[] = [];
    
    for (const battlefield of battlefields) {
      try {
        const response = await fetch(`${getApiUrl()}/data/battlefields/${battlefield}.json`);
        if (response.ok) {
          available.push(battlefield);
        }
      } catch (error) {
        console.log(`⚠️ Battlefield ${battlefield} non disponible`);
      }
    }
    

    return available;
  }
  
  /**
   * Statistiques de performance d'un battlefield
   */
  getPerformanceStats(battlefield: StandardizedBattlefield) {
    const cellCount = battlefield.hexCells.length;
    const uniqueTerrains = new Set(battlefield.hexCells.map(cell => cell.terrain)).size;
    const mapSize = battlefield.width * battlefield.height;
    const coverage = ((cellCount / mapSize) * 100).toFixed(1);
    
    return {
      cellCount,
      uniqueTerrains,
      mapSize,
      coverage: parseFloat(coverage),
      deploymentZones: {
        attacker: Object.keys(battlefield.deploymentZones.attacker).reduce((sum, key) => {
          const zones = battlefield.deploymentZones.attacker[key as keyof typeof battlefield.deploymentZones.attacker];
          return sum + (zones ? zones.length : 0);
        }, 0),
        defender: Object.keys(battlefield.deploymentZones.defender).reduce((sum, key) => {
          const zones = battlefield.deploymentZones.defender[key as keyof typeof battlefield.deploymentZones.defender];
          return sum + (zones ? zones.length : 0);
        }, 0)
      }
    };
  }
}

// Export pour utilisation
export { BattlefieldAdapter, type StandardizedBattlefield, type StandardizedHexCell };