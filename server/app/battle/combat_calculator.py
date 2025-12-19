"""
Combat Calculator - Calcul de dégâts pour les batailles
EXACTEMENT LA MÊME LOGIQUE QUE CombatPopup.tsx (client)

Ce fichier est la SOURCE DE VÉRITÉ pour tous les calculs de combat :
- Utilisé par l'IA pour calculer les dégâts
- Peut être utilisé pour valider les attaques des joueurs
- Formule identique au client pour cohérence

Porté depuis: client/src/components/CombatPopup.tsx (calculateCombat)
"""

import random
import math
import json
import os
from typing import Dict, List, Tuple, Optional


class CombatCalculator:
    """Calculateur de dégâts de combat - Port exact du client TypeScript"""
    
    def __init__(self):
        self.unit_stats = self._load_unit_stats()
        self.terrain_definitions = self._load_terrain_definitions()
    
    def _load_unit_stats(self) -> Dict:
        """Charge les stats des unités depuis unit_stats.json"""
        try:
            # Chemin absolu basé sur l'emplacement de ce fichier
            # __file__ est dans server/app/battle/, on remonte 2 fois pour arriver à server/
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            stats_path = os.path.join(base_dir, 'data', 'unit_stats.json')
            
            with open(stats_path, 'r', encoding='utf-8') as f:
                all_stats = json.load(f)
            
            # Fusionner toutes les ères comme dans le client
            merged = {}
            for era_key in ['stone_age', 'classical_age', 'medieval_age', 'renaissance_age', 'napoleonic_age', 'enemy_units']:
                if era_key in all_stats:
                    merged.update(all_stats[era_key])
            
            return merged
        except Exception as e:
            print(f"❌ [COMBAT-CALC] Erreur chargement unit_stats.json: {e}")
            return {}
    
    def _load_terrain_definitions(self) -> Dict:
        """Charge les définitions de terrains"""
        try:
            # TODO: Charger depuis le bon fichier si disponible
            # Pour l'instant, valeurs par défaut basiques
            return {
                'plains': {'name': 'plains', 'defenseBonus': 0, 'attackPenalty': 0, 'movementBonus': 0},
                'forest': {'name': 'forest', 'defenseBonus': 10, 'attackPenalty': 5, 'movementBonus': -1},
                'hill': {'name': 'hill', 'defenseBonus': 15, 'attackPenalty': 10, 'movementBonus': -1},
                'mountain': {'name': 'mountain', 'defenseBonus': 25, 'attackPenalty': 15, 'movementBonus': -2},
                'river': {'name': 'river', 'defenseBonus': 5, 'attackPenalty': 10, 'movementBonus': -1},
                'swamp': {'name': 'swamp', 'defenseBonus': 5, 'attackPenalty': 15, 'movementBonus': -2},
            }
        except Exception as e:
            print(f"❌ [COMBAT-CALC] Erreur chargement terrains: {e}")
            return {}
    
    def get_unit_type_from_id(self, unit_id: str) -> str:
        """
        Extrait le type d'unité depuis l'ID
        Même logique que extractUnitType() dans combatUtils.ts
        
        Ex: "auto_attacker_player_1_militia_0" → "militia"
        """
        if not unit_id:
            return 'infantry_light'
        
        # Héros
        if unit_id.startswith('hero_hero_'):
            return 'hero'
        
        if '_hero_hero_' in unit_id:
            return 'hero'
        
        if '_hero_' in unit_id or unit_id.endswith('_hero'):
            return 'hero'
        
        # Format auto-deploy wild_camp
        if unit_id.startswith('auto_') and '_wild_camp_' in unit_id:
            parts = unit_id.split('_')
            # auto_defender_wild_camp_barbarian_archer_0
            # → ['auto', 'defender', 'wild', 'camp', 'barbarian', 'archer', '0']
            if len(parts) >= 6:
                return '_'.join(parts[4:-1])  # barbarian_archer
        
        # Format auto-deploy standard: auto_attacker_player_4_militia_0
        if unit_id.startswith('auto_'):
            parts = unit_id.split('_')
            # ['auto', 'attacker', 'player', '4', 'militia', '0']
            if len(parts) >= 5 and parts[2] == 'player' and parts[3].isdigit():
                return '_'.join(parts[4:-1])  # militia
        
        # Format standard: attacker_player_X_TYPE_timestamp
        parts = unit_id.split('_')
        if parts[0] in ['attacker', 'defender'] and len(parts) >= 4:
            # Retirer attacker/defender, player_X, et timestamp final
            if parts[1] == 'player' and parts[2].isdigit():
                # Format: attacker_player_4_infantry_light_1234567890
                # OU Format simple: attacker_player_1_slinger_2 (le 2 est un index, pas le type)
                unit_parts = []
                for i in range(3, len(parts)):
                    # Arrêter au timestamp (10+ chiffres) OU au dernier élément si c'est un petit nombre
                    if parts[i].isdigit():
                        # Si c'est un grand nombre (timestamp), on s'arrête
                        if len(parts[i]) >= 10:
                            break
                        # Si c'est un petit nombre ET c'est le dernier élément, c'est un index (slinger_2)
                        elif i == len(parts) - 1:
                            break  # Ne pas inclure l'index final
                    unit_parts.append(parts[i])
                if unit_parts:
                    return '_'.join(unit_parts)
        
        print(f"⚠️ [COMBAT-CALC] Type inconnu pour {unit_id}, fallback: infantry_light")
        return 'infantry_light'
    
    def get_unit_stats(self, unit_type: str) -> Dict:
        """Récupère les stats d'une unité"""
        if unit_type in self.unit_stats:
            return self.unit_stats[unit_type]
        
        print(f"⚠️ [COMBAT-CALC] Stats inconnues pour {unit_type}, utilisation defaults")
        return {
            'hp': 100,
            'attack_melee': 10,
            'defense_melee': 5,
            'attack_ranged': 0,
            'defense_ranged': 5,
            'range': 1,
            'category': 'infantry',
            'special_abilities': []
        }
    
    def get_primary_combat_type(self, unit_stats: Dict) -> str:
        """Détermine si l'unité attaque en mêlée ou à distance"""
        attack_ranged = unit_stats.get('attack_ranged', 0)
        attack_melee = unit_stats.get('attack_melee', 0)
        
        return 'ranged' if attack_ranged > attack_melee else 'melee'
    
    def get_contextual_bonus(self, unit_stats: Dict, target_stats: Dict, bonus_type: str, combat_type: str) -> float:
        """
        Calcule les bonus contextuels (ex: piquier vs cavalerie)
        
        Args:
            unit_stats: Stats de l'unité qui reçoit le bonus
            target_stats: Stats de la cible
            bonus_type: 'attack' ou 'defense'
            combat_type: 'melee' ou 'ranged'
        
        Returns:
            Pourcentage de bonus (ex: 50.0 pour +50%)
        """
        special_abilities = unit_stats.get('special_abilities', [])
        target_category = target_stats.get('category', '')
        
        for ability in special_abilities:
            if ability.get('target_category') == target_category:
                # Déterminer le champ approprié selon le type de combat et bonus
                if bonus_type == 'attack':
                    field = f'attack_{combat_type}'
                else:  # defense
                    field = f'defense_{combat_type}'
                
                bonus_str = ability.get(field)
                if bonus_str:
                    # Format: "+50%" → 50.0
                    try:
                        return float(bonus_str.replace('+', '').replace('%', ''))
                    except:
                        pass
        
        return 0.0
    
    def calculate_combat(
        self,
        attacker_unit_id: str,
        attacker_count: int,
        defender_unit_id: str,
        defender_count: int,
        terrain_attacker: str = 'plains',
        terrain_defender: str = 'plains',
        moral_attacker: float = 100.0,
        moral_defender: float = 100.0,
        hero_bonus_attacker: float = 0.0,
        hero_bonus_defender: float = 0.0
    ) -> Dict:
        """
        Calcule le résultat d'un combat
        
        EXACTEMENT LA MÊME LOGIQUE QUE CombatPopup.tsx
        
        Args:
            attacker_unit_id: ID de l'unité attaquante
            attacker_count: Nombre d'unités attaquantes
            defender_unit_id: ID de l'unité défendante
            defender_count: Nombre d'unités défendantes
            terrain_attacker: Terrain de l'attaquant
            terrain_defender: Terrain du défenseur
            moral_attacker: Moral de l'attaquant (0-100)
            moral_defender: Moral du défenseur (0-100)
            hero_bonus_attacker: Bonus de héros offensif (%)
            hero_bonus_defender: Bonus de héros défensif (%)
        
        Returns:
            Dict avec:
                - damage: Dégâts infligés
                - kills: Nombre d'unités tuées
                - remaining_hp: HP restants du défenseur
                - surviving_units: Unités survivantes
                - is_defender_hero: Si le défenseur est un héros
                - log: Liste des étapes de calcul
        """
        log = []
        
        # 1. Récupérer les types et stats
        attacker_type = self.get_unit_type_from_id(attacker_unit_id)
        defender_type = self.get_unit_type_from_id(defender_unit_id)
        
        att_stats = self.get_unit_stats(attacker_type)
        def_stats = self.get_unit_stats(defender_type)
        
        log.append(f"🎯 Attaquant: {attacker_type} x{attacker_count}")
        log.append(f"🛡️ Défenseur: {defender_type} x{defender_count}")
        log.append("")
        
        # 2. CALCUL ATTAQUE
        attacker_combat_type = self.get_primary_combat_type(att_stats)
        is_ranged = attacker_combat_type == 'ranged'
        
        base_attack_stat = att_stats['attack_ranged'] if is_ranged else att_stats['attack_melee']
        base_attack = attacker_count * base_attack_stat
        
        attack_label = '🏹' if is_ranged else '🗡️'
        attack_text = 'distance' if is_ranged else 'mêlée'
        log.append(f"{attack_label} Attaque {attack_text}: {attacker_count} × {base_attack_stat} = {base_attack}")
        
        # Bonus de héros offensif
        attack_with_hero = base_attack
        if hero_bonus_attacker > 0:
            hero_attack_bonus = base_attack * (hero_bonus_attacker / 100)
            attack_with_hero = base_attack + hero_attack_bonus
            log.append(f"🎖️ Bonus héros (+{hero_bonus_attacker}%): +{hero_attack_bonus:.1f} = {attack_with_hero:.1f}")
        
        # Bonus terrain d'attaque
        terrain_def = self.terrain_definitions.get(terrain_attacker, {})
        terrain_bonus_pct = -terrain_def.get('attackPenalty', 0)
        terrain_bonus = attack_with_hero * (terrain_bonus_pct / 100)
        attack_with_terrain = attack_with_hero + terrain_bonus
        
        if terrain_bonus_pct != 0:
            log.append(f"🏞️ Terrain {terrain_attacker}: {terrain_bonus_pct:+.0f}% = {terrain_bonus:+.1f}")
        
        # Bonus contextuel (ex: piquier vs cavalerie)
        contextual_bonus_pct = self.get_contextual_bonus(att_stats, def_stats, 'attack', attacker_combat_type)
        contextual_bonus = attack_with_hero * (contextual_bonus_pct / 100)
        attack_with_contextual = attack_with_terrain + contextual_bonus
        
        if contextual_bonus_pct != 0:
            log.append(f"⚔️ Bonus spécialisé vs {def_stats['category']}: +{contextual_bonus_pct:.0f}% = +{contextual_bonus:.1f}")
        
        # Moral (appliqué à 50% du total)
        moral_multiplier = moral_attacker / 100
        moral_bonus = attack_with_contextual * 0.5 * moral_multiplier
        log.append(f"🛡️ Moral ({moral_multiplier:.2f}): 50% × {moral_multiplier:.2f} = +{moral_bonus:.1f}")
        
        # Chance (appliquée à 50% du total)
        chance_multiplier = random.random() * 0.4 + 0.8  # 0.8 à 1.2
        chance_bonus = attack_with_contextual * 0.5 * chance_multiplier
        log.append(f"🎲 Chance ({chance_multiplier:.2f}): 50% × {chance_multiplier:.2f} = +{chance_bonus:.1f}")
        
        total_attack = attack_with_contextual + moral_bonus + chance_bonus
        log.append(f"**📊 Total Attaque: {total_attack:.1f}**")
        log.append("")
        
        # 3. CALCUL DÉFENSE
        base_defense_stat = def_stats['defense_ranged'] if is_ranged else def_stats['defense_melee']
        base_defense = defender_count * base_defense_stat
        
        defense_text = 'distance' if is_ranged else 'mêlée'
        log.append(f"🛡️ Défense {defense_text}: {defender_count} × {base_defense_stat} = {base_defense}")
        
        # Bonus de héros défensif
        defense_with_hero = base_defense
        if hero_bonus_defender > 0:
            hero_defense_bonus = base_defense * (hero_bonus_defender / 100)
            defense_with_hero = base_defense + hero_defense_bonus
            log.append(f"🎖️ Bonus héros (+{hero_bonus_defender}%): +{hero_defense_bonus:.1f} = {defense_with_hero:.1f}")
        
        # Bonus terrain de défense
        terrain_def_def = self.terrain_definitions.get(terrain_defender, {})
        terrain_defense_bonus_pct = terrain_def_def.get('defenseBonus', 0)
        terrain_defense_bonus = defense_with_hero * (terrain_defense_bonus_pct / 100)
        defense_with_terrain = defense_with_hero + terrain_defense_bonus
        
        if terrain_defense_bonus_pct != 0:
            log.append(f"🏞️ Terrain {terrain_defender}: +{terrain_defense_bonus_pct:.0f}% = +{terrain_defense_bonus:.1f}")
        
        # Bonus contextuel défensif
        defender_combat_type = self.get_primary_combat_type(def_stats)
        contextual_defense_bonus_pct = self.get_contextual_bonus(def_stats, att_stats, 'defense', defender_combat_type)
        contextual_defense_bonus = defense_with_hero * (contextual_defense_bonus_pct / 100)
        defense_with_contextual = defense_with_terrain + contextual_defense_bonus
        
        if contextual_defense_bonus_pct != 0:
            log.append(f"⚔️ Bonus défensif vs {att_stats['category']}: +{contextual_defense_bonus_pct:.0f}% = +{contextual_defense_bonus:.1f}")
        
        # Moral défense
        moral_defense_multiplier = moral_defender / 100
        moral_defense_bonus = defense_with_contextual * 0.5 * moral_defense_multiplier
        log.append(f"🛡️ Moral défense ({moral_defense_multiplier:.2f}): 50% × {moral_defense_multiplier:.2f} = +{moral_defense_bonus:.1f}")
        
        # Chance défense
        chance_defense_multiplier = random.random() * 0.4 + 0.8
        chance_defense_bonus = defense_with_contextual * 0.5 * chance_defense_multiplier
        log.append(f"🎲 Chance défense ({chance_defense_multiplier:.2f}): 50% × {chance_defense_multiplier:.2f} = +{chance_defense_bonus:.1f}")
        
        total_defense = defense_with_contextual + moral_defense_bonus + chance_defense_bonus
        log.append(f"**📊 Total Défense: {total_defense:.1f}**")
        log.append("")
        
        # 4. CALCUL DÉGÂTS ET KILLS
        damage = max(1, total_attack - total_defense)
        total_hp = defender_count * def_stats['hp']
        remaining_hp = max(0, total_hp - damage)
        
        # Différencier héros vs unités classiques
        is_defender_hero = defender_type == 'hero' or def_stats.get('category') == 'hero' or defender_count == 1
        
        if is_defender_hero:
            # Héros: garde ses HP, ne meurt pas tant qu'il a des HP
            surviving_units = 1 if remaining_hp > 0 else 0
            kills = 1 if remaining_hp <= 0 else 0
            
            log.append(f"💥 Dégâts infligés: {total_attack:.1f} - {total_defense:.1f} = {damage:.1f}")
            log.append(f"❤️ HP héros restants: {total_hp} - {damage:.1f} = {remaining_hp:.0f}")
            
            if remaining_hp > 0:
                log.append(f"🦸‍♂️ Héros survivant: {remaining_hp:.0f}/{total_hp} HP")
            else:
                log.append(f"💀 Héros éliminé (0 HP)")
        else:
            # Unités classiques: calcul par unités tuées
            surviving_units = math.floor(remaining_hp / def_stats['hp'])
            kills = defender_count - surviving_units
            
            log.append(f"💥 Dégâts infligés: {total_attack:.1f} - {total_defense:.1f} = {damage:.1f}")
            log.append(f"❤️ HP restants: {total_hp} - {damage:.1f} = {remaining_hp:.1f}")
            log.append(f"**👥 Unités survivantes: {surviving_units}/{defender_count} (kills: {kills})**")
        
        return {
            'damage': damage,
            'kills': kills,
            'remaining_hp': remaining_hp,
            'surviving_units': surviving_units,
            'is_defender_hero': is_defender_hero,
            'total_attack': total_attack,
            'total_defense': total_defense,
            'log': log
        }


# Instance singleton
combat_calculator = CombatCalculator()
