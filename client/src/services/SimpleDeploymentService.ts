/**
 * SimpleDeploymentService - Système de déploiement basé sur les zones prédéfinies
 * Utilise directement les zones du battlefield JSON pour un déploiement rapide et cohérent
 */

// Import API helper pour support mobile/desktop
const { getApiUrl } = require('../utils/api');

export interface DeploymentZone {
  q: number;
  r: number;
  zoneCode: string;
}

export interface BattlefieldDeploymentZones {
  attacker: {
    infantry: [number, number][];
    ranged: [number, number][];
    cavalry: [number, number][];
    artillery?: [number, number][];
    support?: [number, number][];
    hero?: [number, number][];
  };
  defender: {
    infantry: [number, number][];
    ranged: [number, number][];
    cavalry: [number, number][];
    artillery?: [number, number][];
    support?: [number, number][];
    hero?: [number, number][];
  };
}

export interface UnitGroup {
  id: string;
  type: string;
  detailedType: string;
  name: string;
  count: number;
  maxStack: number;
  team: 'attacker' | 'defender';
  category?: string;
  deployedPosition?: { q: number; r: number };
  [key: string]: any;
}

export class SimpleDeploymentService {
  private deploymentZones: BattlefieldDeploymentZones | null = null;

  /**
   * Charge les zones de déploiement depuis le battlefield template
   */
  async loadBattlefieldTemplate(battlefieldId: string): Promise<void> {
    try {
      const baseURL = getApiUrl();
      const response = await fetch(`${baseURL}/data/battlefields/${battlefieldId}.json`);
      const battlefieldData = await response.json();
      
      if (!battlefieldData?.template?.deploymentZones) {
        throw new Error('Zones de déploiement manquantes dans le template');
      }

      this.deploymentZones = battlefieldData.template.deploymentZones;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Obtient les zones de déploiement triées pour une équipe et catégorie d'unité
   */
  getDeploymentZones(team: 'attacker' | 'defender', unitCategory: string): DeploymentZone[] {
    if (!this.deploymentZones) {
      throw new Error('Zones de déploiement non chargées');
    }

    const teamZones = this.deploymentZones[team];
    const categoryKey = this.mapUnitCategoryToZoneKey(unitCategory);
    const zones = teamZones[categoryKey as keyof typeof teamZones];

    // Fallback vers infantry si aucune zone spécifique
    if (!zones?.length) {
      const infantryZones = teamZones.infantry || [];
      return infantryZones.map((zone, index) => ({
        q: zone[0],
        r: zone[1],
        zoneCode: `${team.charAt(0).toUpperCase()}I${index + 1}`
      }));
    }

    // Convertir le format [q, r] vers le format avec zoneCode
    return zones.map((zone, index) => ({
      q: zone[0],
      r: zone[1],
      zoneCode: `${team.charAt(0).toUpperCase()}${categoryKey.charAt(0).toUpperCase()}${index + 1}`
    }));
  }

  /**
   * Mappe les catégories d'unités aux zones correspondantes
   */
  private mapUnitCategoryToZoneKey(category: string): string {
    const categoryMap: { [key: string]: string } = {
      'infantry': 'infantry',
      'melee': 'infantry',
      'ranged': 'ranged',
      'archer': 'ranged',
      'cavalry': 'cavalry',
      'mounted': 'cavalry',
      'artillery': 'artillery',
      'siege': 'artillery',
      'support': 'support',
      'hero': 'hero'
    };
    
    return categoryMap[category.toLowerCase()] || 'infantry';
  }

  /**
   * Crée les groupes d'unités basés sur max_stack_size
   */
  createUnitGroups(
    unitType: string, 
    totalCount: number, 
    unitStats: any, 
    team: 'attacker' | 'defender',
    playerId?: string
  ): UnitGroup[] {
    const unitStat = unitStats[unitType];
    if (!unitStat) return [];

    const maxStackSize = unitStat.max_stack_size || 10;
    const unitGroups: UnitGroup[] = [];
    const playerSuffix = playerId ? `_${playerId}` : '';
    let remainingCount = totalCount;
    let groupIndex = 0;

    while (remainingCount > 0) {
      const stackCount = Math.min(remainingCount, maxStackSize);
      
      // Format correct pour l'extraction du playerId dans le système de couleurs
      const standardizedPlayerId = playerId || (team === 'attacker' ? 'player_1' : 'wild_camp');
      const unitId = `${team}_${standardizedPlayerId}_${unitType}_${Date.now()}_${groupIndex}`;
      
      unitGroups.push({
        id: unitId,
        type: unitType,
        detailedType: unitType,
        name: `${unitStat.name || unitType} (${stackCount})`,
        count: stackCount,
        maxStack: maxStackSize,
        team,
        category: unitStat.category || 'infantry',
        health: unitStat.health || 100,
        maxHealth: unitStat.health || 100,
        attack: unitStat.attack || 10,
        defense: unitStat.defense || 8,
        movement: unitStat.movement || 3,
        morale: 100,
        status: 'arrived'
      });

      remainingCount -= stackCount;
      groupIndex++;
    }

    return unitGroups;
  }

  /**
   * Déploie automatiquement les unités dans les zones prédéfinies
   */
  async deployUnitsAutomatically(
    unitGroups: UnitGroup[],
    team: 'attacker' | 'defender',
    unitStats: any,
    onDeployUnit: (unitGroup: UnitGroup, position: { q: number; r: number }) => void,
    battleId?: string
  ): Promise<{ deployed: UnitGroup[]; notDeployed: UnitGroup[] }> {
    
    if (!this.deploymentZones) {
      throw new Error('Zones de déploiement non chargées');
    }

    const deployed: UnitGroup[] = [];
    const notDeployed: UnitGroup[] = [];
    const occupiedPositions = new Set<string>();

    // Charger les positions déjà occupées si battleId fourni
    if (battleId) {
      try {
        const baseURL = getApiUrl();
        const response = await fetch(`${baseURL}/api/v2/battle/get-positions/${battleId}`);
        
        if (response.ok) {
          const battleData = await response.json();
          
          if (battleData && (battleData.teams || (battleData.battle && battleData.battle.teams))) {
            // Gérer les deux formats possibles
            const teams = battleData.teams || battleData.battle.teams;
            
            // Ajouter toutes les positions déjà occupées
            Object.values(teams).forEach((units: any) => {
              if (Array.isArray(units)) {
                units.forEach((unit: any) => {
                  if (unit.position && Array.isArray(unit.position)) {
                    const posKey = `${unit.position[0]},${unit.position[1]}`;
                    occupiedPositions.add(posKey);
                  }
                });
              }
            });
          }
        }
      } catch (error) {
        // Erreur silencieuse - les positions existantes sont optionnelles
      }
    }

    // Grouper par catégorie pour déploiement organisé
    const unitsByCategory = this.groupUnitsByCategory(unitGroups);

    // Déployer chaque catégorie
    for (const [category, categoryUnits] of Object.entries(unitsByCategory)) {
      const zones = this.getDeploymentZones(team, category);
      const deploymentResult = this.deployCategoryUnits(
        categoryUnits, 
        zones, 
        occupiedPositions, 
        onDeployUnit
      );

      deployed.push(...deploymentResult.deployed);
      notDeployed.push(...deploymentResult.notDeployed);
    }

    return { deployed, notDeployed };
  }

  /**
   * Groupe les unités par catégorie
   */
  private groupUnitsByCategory(unitGroups: UnitGroup[]): { [category: string]: UnitGroup[] } {
    return unitGroups.reduce((acc, unit) => {
      const category = unit.category || 'infantry';
      if (!acc[category]) acc[category] = [];
      acc[category].push(unit);
      return acc;
    }, {} as { [category: string]: UnitGroup[] });
  }

  /**
   * Déploie les unités d'une catégorie dans leurs zones
   */
  private deployCategoryUnits(
    units: UnitGroup[],
    zones: DeploymentZone[],
    occupiedPositions: Set<string>,
    onDeployUnit: (unitGroup: UnitGroup, position: { q: number; r: number }) => void
  ): { deployed: UnitGroup[]; notDeployed: UnitGroup[] } {
    const deployed: UnitGroup[] = [];
    const notDeployed: UnitGroup[] = [];

    for (const unit of units) {
      let deployed_successfully = false;
      
      // Chercher la première zone libre pour cette unité
      for (let zoneIndex = 0; zoneIndex < zones.length; zoneIndex++) {
        const zone = zones[zoneIndex];
        const positionKey = `${zone.q},${zone.r}`;

        if (!occupiedPositions.has(positionKey)) {
          // Zone libre trouvée, déployer l'unité
          const position = { q: zone.q, r: zone.r };
          onDeployUnit(unit, position);
          occupiedPositions.add(positionKey);
          deployed.push({ ...unit, deployedPosition: position });
          deployed_successfully = true;
          break;
        }
      }
      
      // Si aucune zone libre trouvée
      if (!deployed_successfully) {
        notDeployed.push(unit);
      }
    }

    return { deployed, notDeployed };
  }

  /**
   * Résumé des zones disponibles pour une équipe
   */
  getAvailableZonesInfo(team: 'attacker' | 'defender'): string {
    if (!this.deploymentZones) return 'Zones non chargées';

    const teamZones = this.deploymentZones[team];
    const info = Object.entries(teamZones)
      .filter(([_, zones]) => zones?.length > 0)
      .map(([category, zones]) => {
        const convertedZones = zones.map((zone, index) => 
          `${team.charAt(0).toUpperCase()}${category.charAt(0).toUpperCase()}${index + 1}`
        );
        return `${category}: ${zones.length} (${convertedZones.join(', ')})`;
      });

    return info.join(' | ') || 'Aucune zone disponible';
  }

  /**
   * Sauvegarde les positions déployées via l'API serveur
   */
  async saveDeployedPositions(
    battleId: string, 
    deployedUnits: UnitGroup[], 
    team: 'attacker' | 'defender',
    currentRound: number = 1
  ): Promise<void> {
    if (!battleId || !deployedUnits?.length) {
      return;
    }

    const positionsData = {
      battleId,
      current_round: currentRound,
      timestamp: Date.now(),
      positions: deployedUnits.map(unit => ({
        unitId: unit.id,
        unitType: unit.type,
        team: unit.team,
        position: unit.deployedPosition || { q: 0, r: 0 },
        unitCount: unit.count,
        ...(unit.isHero && { isHero: true, heroData: unit.heroData || {} })
      }))
    };

    try {
      const baseURL = getApiUrl();
      const response = await fetch(`${baseURL}/api/v2/battle/save-positions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(positionsData)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      await response.json();
    } catch (error) {
      throw error;
    }
  }

  /**
   * Met à jour les compteurs d'unités après déploiement
   */
  async updateUnitCounters(
    battleId: string, 
    deployedUnits: UnitGroup[]
  ): Promise<boolean> {
    try {
      const { UnitCounterService } = await import('./UnitCounterService');
      return await UnitCounterService.updateUnitCounts(battleId, deployedUnits);
    } catch (error) {
      return false;
    }
  }
}
