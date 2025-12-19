/**
 * useHeroAura.ts
 * 
 * Hook personnalisé pour la gestion des auras de héros
 * - Calcul des unités dans l'aura des héros
 * - Récupération des bonus d'aura
 * - Cache des données héros
 */

import { useState, useEffect, useCallback } from 'react';
import { getApiUrl } from '../utils/api';

interface CompactBattle {
  battleId: string;
  timestamp: number;
  current_round: number;
  current_player: string;
  teams: {
    [teamKey: string]: any[];
  };
}

export const useHeroAura = (
  battleData: CompactBattle | null, 
  battleId?: string, 
  participants?: { attackers: string[]; defenders: string[] }
) => {
  const [unitsInHeroAura, setUnitsInHeroAura] = useState<Set<string>>(new Set());
  const [heroAuraCache, setHeroAuraCache] = useState<Map<string, any>>(new Map());
  const [heroesDataCache, setHeroesDataCache] = useState<any>(null);

  // Charger les données des héros une fois
  useEffect(() => {
    const loadHeroesData = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/v2/player_heroes`);
        const data = await response.json();
        setHeroesDataCache(data);
      } catch (error) {
        // Erreur silencieuse
      }
    };
    
    loadHeroesData();
  }, []);

  // Calcul fallback côté client avec données héros en cache
  const calculateHeroAuraFallback = useCallback(() => {
    const affectedUnitIds = new Set<string>();
    
    if (battleData && battleData.teams && heroesDataCache) {
      const attackers = participants?.attackers || [];
      const defenders = participants?.defenders || [];
      
      const allUnits: any[] = [];
      
      // Extraire toutes les unités
      for (const [teamKey, units] of Object.entries(battleData.teams)) {
        const isAttacker = attackers.includes(teamKey);
        const team = isAttacker ? 'attacker' : 'defender';
        
        for (const unit of units as any[]) {
          const unitInfo = {
            id: unit.unitId,
            position: unit.position,
            team: team,
            unitCount: unit.unitCount,
            hp: unit.hp
          };
          
          allUnits.push(unitInfo);
        }
      }
      
      const heroesData = heroesDataCache;
      
      // Trouver héros vivants
      const aliveHeroes = allUnits.filter(unit => 
        (unit.id.includes('hero_') || unit.id.includes('_hero_')) && (unit.hp || 0) > 0
      );
      
      for (const hero of aliveHeroes) {
        const heroPos = hero.position || [0, 0];
        
        if (!heroesData) {
          continue;
        }
        
        // Extraire l'instanceId du heroUnitId
        let heroKey = hero.id;
        if (hero.id.includes('_hero_')) {
          const parts = hero.id.split('_');
          const heroIndex = parts.indexOf('hero');
          if (heroIndex !== -1 && heroIndex < parts.length - 1) {
            let instanceParts = parts.slice(heroIndex + 1);
            if (instanceParts[0] === 'hero') {
              instanceParts = instanceParts.slice(1);
            }
            if (instanceParts.length > 0) {
              heroKey = `hero_${instanceParts.join('_')}`;
            }
          }
        }
        
        // Chercher dans player_heroes.json
        let heroData = null;
        for (const playerId in heroesData) {
          const playerData = heroesData[playerId];
          if (playerData.heroes && playerData.heroes[heroKey]) {
            heroData = playerData.heroes[heroKey];
            break;
          }
        }
        
        if (!heroData || !heroData.calculated_bonuses?.aura_radius) {
          continue;
        }
        
        const auraRadius = heroData.calculated_bonuses.aura_radius;
        
        let unitsAffectedByThisHero = 0;
        
        // Unités dans l'aura (distance hexagonale)
        for (const unit of allUnits) {
          if (unit.id === hero.id) continue;
          
          const unitPos = unit.position || [0, 0];
          
          const [q1, r1] = heroPos;
          const [q2, r2] = unitPos;
          const distance = (Math.abs(q1 - q2) + Math.abs(q1 + r1 - q2 - r2) + Math.abs(r1 - r2)) / 2;
          
          if (distance <= auraRadius && unit.team === hero.team) {
            affectedUnitIds.add(unit.id);
            unitsAffectedByThisHero++;
          }
        }
      }
    }
    
    setUnitsInHeroAura(affectedUnitIds);
  }, [battleData, heroesDataCache, participants]);

  // Fonction principale pour calculer les auras
  const calculateUnitsInHeroAura = useCallback(() => {
    try {
      calculateHeroAuraFallback();
    } catch (error) {
      // Erreur silencieuse
    }
  }, [calculateHeroAuraFallback]);

  // Vérifier si une unité est dans l'aura et récupérer les bonus (synchrone)
  const getHeroAuraForUnitSync = useCallback((unit: any, position: { q: number; r: number }) => {
    const unitId = unit?.unitId || unit?.id;
    
    if (!unitId || !battleData?.teams) {
      return { inAura: false, bonuses: null, hero: null };
    }
    
    const isInAuraSet = unitsInHeroAura.has(unitId);
    
    if (!isInAuraSet) {
      return { inAura: false, bonuses: null, hero: null };
    }
    
    if (!heroesDataCache) {
      return { inAura: false, bonuses: null, hero: null };
    }
    
    try {
      const attackers = participants?.attackers || [];
      const defenders = participants?.defenders || [];
      
      const allUnits: any[] = [];
      for (const [teamKey, units] of Object.entries(battleData.teams)) {
        const isAttacker = attackers.includes(teamKey);
        const team = isAttacker ? 'attacker' : 'defender';
        
        for (const u of units as any[]) {
          allUnits.push({
            id: u.unitId,
            position: u.position,
            team: team,
            hp: u.hp
          });
        }
      }
      
      const currentUnit = allUnits.find(u => u.id === unitId);
      if (!currentUnit) {
        return { inAura: false, bonuses: null, hero: null };
      }
      
      const aliveHeroes = allUnits.filter(u => 
        (u.id.includes('hero_') || u.id.includes('_hero_')) && 
        (u.hp || 0) > 0 && 
        u.team === currentUnit.team
      );
      
      for (const hero of aliveHeroes) {
        const heroPos = hero.position || [0, 0];
        const unitPos = currentUnit.position || [0, 0];
        
        const [q1, r1] = heroPos;
        const [q2, r2] = unitPos;
        const distance = (Math.abs(q1 - q2) + Math.abs(q1 + r1 - q2 - r2) + Math.abs(r1 - r2)) / 2;
        
        let heroKey = hero.id;
        
        if (hero.id.includes('_hero_hero_')) {
          const match = hero.id.match(/_hero_(hero_[^_]+_[^_]+)$/);
          if (match) {
            heroKey = match[1];
          }
        } else if (hero.id.includes('_hero_') && !hero.id.includes('_hero_hero_')) {
          const parts = hero.id.split('_');
          const heroIndex = parts.indexOf('hero');
          
          if (heroIndex !== -1 && heroIndex < parts.length - 1) {
            const heroPlayerPart = parts[heroIndex - 1];
            const heroIdPart = parts[heroIndex + 1];
            const heroNumberPart = parts[heroIndex + 2];
            
            if (heroPlayerPart && heroIdPart && heroNumberPart) {
              heroKey = `hero_${heroIdPart}_${heroNumberPart}`;
            }
          }
        }
        
        let heroData = null;
        for (const playerId in heroesDataCache) {
          const playerData = heroesDataCache[playerId];
          if (playerData.heroes && playerData.heroes[heroKey]) {
            heroData = playerData.heroes[heroKey];
            break;
          }
        }
        
        if (heroData && heroData.calculated_bonuses && heroData.calculated_bonuses.aura_radius) {
          const auraRadius = heroData.calculated_bonuses.aura_radius;
          
          if (distance <= auraRadius) {
            const bonuses = {
              offensive_bonus: heroData.calculated_bonuses.offensive_bonus,
              defensive_bonus: heroData.calculated_bonuses.defensive_bonus,
              movement_bonus: heroData.calculated_bonuses.movement_bonus,
              moral_bonus: heroData.calculated_bonuses.moral_bonus,
              aura_radius: auraRadius
            };
            
            return {
              inAura: true,
              bonuses,
              hero: { 
                id: hero.id, 
                name: heroData.hero_id || heroData.name || 'Héros',
                heroKey: heroKey
              }
            };
          }
        }
      }
    } catch (error) {
      return { inAura: false, bonuses: null, hero: null };
    }
    
    return { inAura: false, bonuses: null, hero: null };
  }, [battleData, unitsInHeroAura, heroesDataCache, participants]);

  // Recalculer quand battleData change
  useEffect(() => {
    if (battleData) {
      calculateUnitsInHeroAura();
    }
  }, [battleData, battleId, calculateUnitsInHeroAura]);

  return {
    unitsInHeroAura,
    getHeroAuraForUnitSync,
    calculateUnitsInHeroAura,
    heroesDataCache
  };
};
