"""
HeroBonusManager - Gestionnaire d'application des bonus de héros sur le champ de bataille
Gère l'application des bonus de héros selon leur position et leur état (vivant/mort)
"""
import json
import os
import math
from typing import Dict, List, Any, Optional, Tuple


class HeroBonusManager:
    def __init__(self):
        self.player_heroes_file = os.path.join('gamedata', 'player_heroes.json')
        self.battles_file = os.path.join('gamedata', 'battlesv2.json')
        
    def load_player_heroes(self) -> Dict:
        """Charge les données des héros des joueurs"""
        try:
            with open(self.player_heroes_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Player heroes file not found: {self.player_heroes_file}")
            return {}
        except json.JSONDecodeError:
            print(f"Error decoding player heroes file: {self.player_heroes_file}")
            return {}
    
    def load_battles_data(self) -> Dict:
        """Charge les données des batailles"""
        try:
            with open(self.battles_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Battles file not found: {self.battles_file}")
            return {}
        except json.JSONDecodeError:
            print(f"Error decoding battles file: {self.battles_file}")
            return {}
    
    def get_hero_bonuses(self, hero_id: str) -> Dict:
        """Récupère les bonus calculés d'un héros depuis player_heroes.json"""
        player_heroes = self.load_player_heroes()
        
        # Extraire l'ID original du héros depuis le nouveau format avec préfixe
        original_hero_id = hero_id
        if hero_id.startswith('hero_attacker_') or hero_id.startswith('hero_defender_'):
            # Ancien format: hero_attacker_1757538620_c8127d -> hero_1757538620_c8127d
            parts = hero_id.split('_')
            if len(parts) >= 3:
                original_hero_id = 'hero_' + '_'.join(parts[2:])
        elif '_hero_' in hero_id:
            # Nouveau format: defender_player_4_hero_1758922347_696526 -> hero_1758922347_696526
            # Cas spécial: defender_player_4_hero_hero_1758922347_696526 -> hero_1758922347_696526  
            parts = hero_id.split('_')
            hero_index = parts.index('hero') if 'hero' in parts else -1
            if hero_index != -1 and hero_index < len(parts) - 1:
                # Nettoyer les doubles "hero_hero_" qui peuvent survenir
                remaining_parts = parts[hero_index + 1:]
                if remaining_parts and remaining_parts[0] == 'hero':
                    remaining_parts = remaining_parts[1:]  # Supprimer le "hero" en double
                if remaining_parts:
                    original_hero_id = 'hero_' + '_'.join(remaining_parts)
        
        # Chercher le héros dans tous les joueurs (OBLIGATOIRE)
        for player_id, player_data in player_heroes.items():
            heroes = player_data.get('heroes', {})
            if original_hero_id in heroes:
                hero_data = heroes[original_hero_id]
                calculated_bonuses = hero_data.get('calculated_bonuses', {})
                if calculated_bonuses:
                    return calculated_bonuses
        
        # ERREUR CRITIQUE: Héros déployé non trouvé dans player_heroes.json
        print(f"❌ ERREUR CRITIQUE: Héros {original_hero_id} (de {hero_id}) non trouvé dans player_heroes.json!")
        print(f"❌ Tous les héros déployés DOIVENT être présents dans player_heroes.json")
        return {}  # Retour vide pour éviter les crashes
    
    def apply_moral_bonus_to_team(self, team_data: Dict, hero_ids: List[str]) -> int:
        """
        Applique le bonus de moral des héros à une équipe
        Returns: nouveau moral total (base 100 + bonus des héros)
        """
        base_moral = 100
        total_moral_bonus = 0
        
        for hero_id in hero_ids:
            hero_bonuses = self.get_hero_bonuses(hero_id)
            moral_bonus = hero_bonuses.get('moral_bonus', 0)
            total_moral_bonus += moral_bonus
            print(f"Hero {hero_id} contributes {moral_bonus} moral bonus")
        
        total_moral = base_moral + total_moral_bonus
        print(f"Team moral: {base_moral} (base) + {total_moral_bonus} (heroes) = {total_moral}")
        return total_moral
    
    def calculate_distance(self, pos1: List[int], pos2: List[int]) -> float:
        """Calcule la distance hexagonale entre deux positions"""
        # Conversion coordonnées hexagonales en distance
        q1, r1 = pos1
        q2, r2 = pos2
        
        # Distance hexagonale standard
        distance = (abs(q1 - q2) + abs(q1 + r1 - q2 - r2) + abs(r1 - r2)) / 2
        return distance
    
    def get_units_in_hero_aura(self, battle_data: Dict, hero_position: List[int], 
                               aura_radius: int, team_key: str) -> List[Dict]:
        """
        Trouve toutes les unités d'une équipe dans le rayon d'aura du héros
        Returns: liste des unités dans l'aura avec leurs positions
        """
        units_in_aura = []
        team_units = battle_data.get('teams', {}).get(team_key, [])
        
        for unit in team_units:
            unit_position = unit.get('position', [])
            if len(unit_position) == 2:
                distance = self.calculate_distance(hero_position, unit_position)
                if distance <= aura_radius:
                    units_in_aura.append({
                        'unit': unit,
                        'distance': distance
                    })
        
        return units_in_aura
    
    def apply_battlefield_bonuses(self, battle_id: str) -> Dict:
        """
        Applique tous les bonus des héros vivants sur le champ de bataille
        Returns: dictionnaire des bonus appliqués par équipe
        """
        battles_data = self.load_battles_data()
        battle_data = battles_data.get(battle_id, {})
        
        if not battle_data:
            print(f"Battle {battle_id} not found")
            return {}
        
        applied_bonuses = {}
        teams = battle_data.get('teams', {})
        
        for team_key, team_units in teams.items():
            applied_bonuses[team_key] = {
                'heroes': [],
                'affected_units': []
            }
            
            # Trouver les héros vivants dans cette équipe
            for unit in team_units:
                unit_id = unit.get('unitId', '')
                # Nouveau format: defender_player_X_hero_xxx ou ancien format: hero_xxx
                if unit_id.startswith('hero_') or '_hero_' in unit_id:
                    hero_hp = unit.get('hp', 0)
                    if hero_hp > 0:  # Héros vivant
                        hero_position = unit.get('position', [])
                        hero_bonuses = self.get_hero_bonuses(unit_id)
                        
                        if hero_bonuses:
                            aura_radius = hero_bonuses.get('aura_radius', 0)
                            
                            # Trouver les unités dans l'aura
                            units_in_aura = self.get_units_in_hero_aura(
                                battle_data, hero_position, aura_radius, team_key
                            )
                            
                            hero_info = {
                                'hero_id': unit_id,
                                'position': hero_position,
                                'bonuses': hero_bonuses,
                                'units_affected': len(units_in_aura)
                            }
                            
                            applied_bonuses[team_key]['heroes'].append(hero_info)
                            applied_bonuses[team_key]['affected_units'].extend(units_in_aura)
                            
                            # Hero bonus applied
        
        return applied_bonuses
    
    def get_unit_effective_stats(self, unit_data: Dict, applied_bonuses: Dict, team_key: str) -> Dict:
        """
        Calcule les statistiques effectives d'une unité avec les bonus des héros
        """
        base_stats = {
            'attack': unit_data.get('attack', 0),
            'defense': unit_data.get('defense', 0),
            'movement': unit_data.get('movement', 0)
        }
        
        effective_stats = base_stats.copy()
        bonus_summary = {'sources': []}
        
        # Appliquer les bonus de tous les héros qui affectent cette unité
        team_bonuses = applied_bonuses.get(team_key, {})
        for affected_unit in team_bonuses.get('affected_units', []):
            if affected_unit['unit'].get('unitId') == unit_data.get('unitId'):
                # Cette unité est affectée par un héros
                for hero_info in team_bonuses.get('heroes', []):
                    hero_bonuses = hero_info.get('bonuses', {})
                    
                    # Appliquer les bonus
                    effective_stats['attack'] += hero_bonuses.get('offensive_bonus', 0)
                    effective_stats['defense'] += hero_bonuses.get('defensive_bonus', 0)
                    effective_stats['movement'] += hero_bonuses.get('movement_bonus', 0)
                    
                    bonus_summary['sources'].append({
                        'hero_id': hero_info.get('hero_id'),
                        'offensive_bonus': hero_bonuses.get('offensive_bonus', 0),
                        'defensive_bonus': hero_bonuses.get('defensive_bonus', 0),
                        'movement_bonus': hero_bonuses.get('movement_bonus', 0)
                    })
        
        return {
            'base_stats': base_stats,
            'effective_stats': effective_stats,
            'bonus_summary': bonus_summary
        }
    
    def update_battle_with_hero_bonuses(self, battle_id: str) -> Dict:
        """
        Met à jour une bataille avec tous les bonus des héros appliqués
        Returns: données de bataille mises à jour
        """
        print(f"Applying hero bonuses to battle {battle_id}")
        
        # Appliquer les bonus sur le champ de bataille
        applied_bonuses = self.apply_battlefield_bonuses(battle_id)
        
        # Calculer les stats effectives pour toutes les unités
        battles_data = self.load_battles_data()
        battle_data = battles_data.get(battle_id, {})
        
        updated_battle = battle_data.copy()
        updated_battle['hero_bonuses_applied'] = applied_bonuses
        
        return updated_battle
