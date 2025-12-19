"""
IA Basique de Combat - Serveur
Logique simple pour faire jouer automatiquement l'IA quand le timer expire
"""

import random
import math
from typing import List, Tuple, Optional, Dict


class BattleAIBasic:
    """IA basique pour les combats - joue automatiquement"""
    
    def __init__(self):
        self.attack_range = 1  # Portée d'attaque standard (hexagones adjacents)
        from app.battle.combat_calculator import combat_calculator
        self.combat_calc = combat_calculator
        
        # Charger la config IA
        import json
        import os
        # __file__ = server/app/ai/battle_ai_basic.py
        # On remonte 3 fois pour arriver à server/, puis data/
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(base_dir, 'data', 'ai_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except:
            # Config par défaut
            self.config = {
                'decision_weights': {
                    'priority_hero': 100,
                    'priority_low_hp': 80,
                    'priority_ranged': 60,
                    'priority_closest': 40,
                    'priority_threat_level': 70
                },
                'behavior': {
                    'prefer_ranged_attacks': True,
                    'avoid_high_defense': True,
                    'focus_wounded': True
                }
            }
    
    def execute_ai_turn(self, battle_id: str, current_player: str) -> bool:
        """
        Exécute un tour d'IA pour le joueur actuel
        
        Args:
            battle_id: ID de la bataille
            current_player: ID du joueur actuel (ex: "player_1")
            
        Returns:
            bool: True si une action a été effectuée
        """
        from app.routes.battle_routes_v2 import load_json_data, save_json_data
        from app.config.paths import BATTLES_V2_FILE
        from app.battle.battle_turn_manager_v2 import BattleTurnManagerV2
        
        print(f"🤖 [IA] Début tour IA pour {current_player} dans {battle_id}")
        
        # Charger les données de bataille
        battles_data = load_json_data(BATTLES_V2_FILE, {})
        
        if battle_id not in battles_data:
            print(f"❌ [IA] Bataille {battle_id} non trouvée")
            return False
        
        battle = battles_data[battle_id]
        current_round = battle.get('current_round', 1)
        
        # 1. Trouver les unités disponibles (qui n'ont pas encore joué)
        available_units = self._get_available_units(battle, current_player, current_round)
        
        if not available_units:
            print(f"✅ [IA] Aucune unité disponible pour {current_player}")
            return False
        
        print(f"🎯 [IA] {len(available_units)} unités disponibles")
        
        # 2. Chercher les ennemis une seule fois (optimisation)
        enemy_units = self._get_enemy_units(battle, current_player)
        
        if not enemy_units:
            print(f"❌ [IA] Aucun ennemi trouvé")
            return False
        
        # 3. Initialiser le gestionnaire de tours
        turn_manager = BattleTurnManagerV2()
        
        # 4. BOUCLE : Faire jouer TOUTES les unités disponibles
        actions_performed = 0
        
        for unit_index, selected_unit in enumerate(available_units):
            print(f"🎯 [IA] Traitement unité {unit_index + 1}/{len(available_units)}: {selected_unit['unitId']}")
            
            # ⏱️ DÉLAI ENTRE CHAQUE UNITÉ (0.5s pour voir les actions séparément)
            if unit_index > 0:  # Pas de délai pour la première unité
                import time
                time.sleep(0.5)  # 500ms entre chaque action
            
            # Recharger les données de bataille pour avoir l'état à jour
            battles_data = load_json_data(BATTLES_V2_FILE, {})
            if battle_id not in battles_data:
                continue
            battle = battles_data[battle_id]
            
            # Recharger la liste des ennemis (certains ont pu mourir)
            enemy_units = self._get_enemy_units(battle, current_player)
            if not enemy_units:
                print(f"✅ [IA] Plus d'ennemis, victoire probable")
                break
            
            # 5. Calculer la distance à chaque ennemi
            targets_with_distance = []
            for enemy in enemy_units:
                distance = self._hex_distance(selected_unit['position'], enemy['position'])
                targets_with_distance.append({
                    'unit': enemy,
                    'distance': distance
                })
            
            # Trier par distance (les plus proches en premier)
            targets_with_distance.sort(key=lambda x: x['distance'])
            
            # 6. Récupérer la portée d'attaque de cette unité
            unit_type = self.combat_calc.get_unit_type_from_id(selected_unit['unitId'])
            unit_stats = self.combat_calc.get_unit_stats(unit_type)
            unit_range = unit_stats.get('range', 1)
            
            # 7. Décider : Attaquer ou Se déplacer
            action_done = False
            
            for target_info in targets_with_distance:
                target = target_info['unit']
                distance = target_info['distance']
                
                # Si à portée d'attaque
                if distance <= unit_range:
                    print(f"⚔️ [IA] {selected_unit['unitId']} attaque {target['unitId']} (portée {unit_range}, distance {distance})")
                    
                    # Récupérer les counts
                    attacker_count = selected_unit.get('unitCount', 1)
                    defender_count = target.get('unitCount', 1)
                    
                    # Récupérer le vrai terrain pour attaquant et défenseur
                    terrain_attacker = self._get_terrain_at_position(selected_unit['position'], battle)
                    terrain_defender = self._get_terrain_at_position(target['position'], battle)
                    
                    # Récupérer le moral des équipes
                    moral_attacker = self._get_team_moral(battle, current_player)
                    moral_defender = self._get_enemy_moral(battle, current_player)
                    
                    # Récupérer les bonus de héros
                    hero_bonus_attacker = self._get_hero_attack_bonus(selected_unit['unitId'], selected_unit['position'], battle)
                    hero_bonus_defender = self._get_hero_defense_bonus(target['unitId'], target['position'], battle)
                    
                    # Calculer le combat
                    combat_result = self.combat_calc.calculate_combat(
                        attacker_unit_id=selected_unit['unitId'],
                        attacker_count=attacker_count,
                        defender_unit_id=target['unitId'],
                        defender_count=defender_count,
                        terrain_attacker=terrain_attacker,
                        terrain_defender=terrain_defender,
                        moral_attacker=moral_attacker,
                        moral_defender=moral_defender,
                        hero_bonus_attacker=hero_bonus_attacker,
                        hero_bonus_defender=hero_bonus_defender
                    )
                    
                    kills = combat_result['kills']
                    
                    if kills == 0:
                        kills = max(1, kills)
                    
                    result = turn_manager.record_attack_action(
                        battle_id,
                        selected_unit['unitId'],
                        target['unitId'],
                        kills
                    )
                    
                    if result.get('success'):
                        print(f"✅ [IA] Attaque réussie ({kills} kills)")
                        actions_performed += 1
                        action_done = True
                        break
                    else:
                        print(f"❌ [IA] Échec attaque: {result.get('error')}")
                        continue
            
            # 8. Si aucune attaque réussie, se déplacer vers l'ennemi le plus proche
            if not action_done and targets_with_distance:
                closest_target = targets_with_distance[0]['unit']
                
                new_position = self._move_towards(
                    selected_unit['position'],
                    closest_target['position'],
                    battle,
                    selected_unit['unitId']
                )
                
                if new_position and new_position != selected_unit['position']:
                    print(f"🚶 [IA] Déplacement de {selected_unit['unitId']} vers {new_position}")
                    
                    result = turn_manager.record_unit_move(
                        battle_id,
                        selected_unit['unitId'],
                        selected_unit['position'],
                        new_position
                    )
                    
                    if result.get('success'):
                        print(f"✅ [IA] Déplacement réussi")
                        actions_performed += 1
                    else:
                        print(f"❌ [IA] Échec déplacement: {result.get('error')}")
        
        # 8. Résultat final
        if actions_performed > 0:
            print(f"✅ [IA] {actions_performed} actions effectuées pour {current_player}")
            
            # 🏆 VÉRIFIER LA VICTOIRE après chaque tour d'IA
            victory_check = turn_manager._check_victory_after_action(battle_id)
            if victory_check.get('victory_detected'):
                print(f"🏆 [IA] VICTOIRE DÉTECTÉE: {victory_check.get('winner_team')} par {victory_check.get('victory_type')}")
            
            return True
        else:
            print(f"⚠️ [IA] Aucune action réussie pour {current_player}")
            return False
    
    def _get_available_units(self, battle: dict, player_id: str, current_round: int) -> List[dict]:
        """Récupère les unités qui n'ont pas encore joué ce round"""
        
        # Récupérer les unités du joueur
        teams = battle.get('teams', {})
        player_units = []
        
        for team_key, units in teams.items():
            if player_id in team_key:
                player_units = units
                break
        
        if not player_units:
            return []
        
        # Vérifier quelles unités ont déjà joué
        units_that_acted = set()
        
        rounds_history = battle.get('rounds_history', {})
        round_key = f"round_{current_round}"
        
        if round_key in rounds_history:
            moves = rounds_history[round_key].get('moves', [])
            for action in moves:
                unit_id = action.get('unitId')
                if unit_id:
                    units_that_acted.add(unit_id)
        
        # Filtrer les unités disponibles
        available = [
            unit for unit in player_units
            if unit.get('unitId') not in units_that_acted
        ]
        
        return available
    
    def _get_enemy_units(self, battle: dict, player_id: str) -> List[dict]:
        """Récupère toutes les unités ennemies"""
        
        teams = battle.get('teams', {})
        enemy_units = []
        
        for team_key, units in teams.items():
            # Si ce n'est pas l'équipe du joueur actuel
            if player_id not in team_key:
                enemy_units.extend(units)
        
        return enemy_units
    
    def _hex_distance(self, pos1: List[int], pos2: List[int]) -> int:
        """Calcule la distance hexagonale entre deux positions"""
        q1, r1 = pos1
        q2, r2 = pos2
        
        return (abs(q1 - q2) + abs(r1 - r2) + abs((q1 + r1) - (q2 + r2))) // 2
    
    def _move_towards(self, from_pos: List[int], to_pos: List[int], battle: dict, unit_id: str = None) -> Optional[List[int]]:
        """
        Trouve la meilleure position pour se rapprocher de la cible en utilisant
        la portée de mouvement complète de l'unité (movement + bonus terrain/héros)
        
        Args:
            from_pos: Position actuelle [q, r]
            to_pos: Position cible [q, r]
            battle: Données de bataille
            unit_id: ID de l'unité pour récupérer ses stats de mouvement
            
        Returns:
            Nouvelle position [q, r] ou None
        """
        from app.battle.combat_calculator import combat_calculator
        
        # Récupérer la portée de mouvement de base de l'unité
        max_movement = 1  # Valeur par défaut
        
        if unit_id:
            unit_type = combat_calculator.get_unit_type_from_id(unit_id)
            unit_stats = combat_calculator.get_unit_stats(unit_type)
            max_movement = unit_stats.get('movement', 1)
            
            # Ajouter les bonus de terrain et de héros
            terrain_bonus = self._get_terrain_movement_bonus(from_pos, battle)
            hero_bonus = self._get_hero_movement_bonus(unit_id, from_pos, battle)
            
            # Le bonus de terrain peut être négatif (terrain difficile)
            # Le movement ne peut pas être < 1
            max_movement = max(1, max_movement + terrain_bonus + hero_bonus)
        
        # Utiliser BFS (parcours en largeur) pour trouver toutes les cases accessibles
        accessible_positions = self._get_accessible_positions(from_pos, max_movement, battle)
        
        if not accessible_positions:
            return None
        
        # Trouver la position accessible la plus proche de la cible
        best_pos = None
        best_distance = float('inf')
        
        for pos in accessible_positions:
            distance = self._hex_distance(pos, to_pos)
            if distance < best_distance:
                best_distance = distance
                best_pos = pos
        
        return best_pos
    
    def _get_terrain_movement_bonus(self, position: List[int], battle: dict) -> int:
        """
        Récupère le bonus/malus de mouvement du terrain à une position donnée
        
        Args:
            position: Position [q, r]
            battle: Données de bataille contenant battlefield_map
            
        Returns:
            int: Bonus de mouvement (peut être négatif)
        """
        from app.battle.combat_calculator import combat_calculator
        
        # Récupérer le terrain à cette position
        battlefield = battle.get('battlefield', {})
        battlefield_map = battlefield.get('battlefield_map', {})
        
        # Convertir la position en string key "q_r"
        pos_key = f"{position[0]}_{position[1]}"
        
        # Récupérer le terrain
        terrain_type = 'plains'  # Défaut
        if pos_key in battlefield_map:
            terrain_type = battlefield_map[pos_key].get('terrain', 'plains')
        
        # Récupérer les stats du terrain depuis terrain_definitions
        terrain_stats = combat_calculator.terrain_definitions.get(terrain_type, {})
        movement_bonus = terrain_stats.get('movementBonus', 0)
        
        return movement_bonus
    
    def _get_hero_movement_bonus(self, unit_id: str, position: List[int], battle: dict) -> int:
        """
        Récupère le bonus de mouvement des héros à proximité
        
        Args:
            unit_id: ID de l'unité
            position: Position de l'unité [q, r]
            battle: Données de bataille
            
        Returns:
            int: Bonus de mouvement des héros (arrondi)
        """
        from app.battle.HeroBonusManager import HeroBonusManager
        
        # Déterminer l'équipe de cette unité
        teams = battle.get('teams', {})
        unit_team = None
        
        for team_key, units in teams.items():
            for unit in units:
                if unit.get('unitId') == unit_id:
                    unit_team = team_key
                    break
            if unit_team:
                break
        
        if not unit_team:
            return 0
        
        # Trouver les héros de cette équipe
        team_units = teams.get(unit_team, [])
        bonus_manager = HeroBonusManager()
        total_movement_bonus = 0
        
        for unit in team_units:
            # Vérifier si c'est un héros
            if 'hero' in unit.get('unitId', '').lower():
                hero_id = unit.get('unitId')
                hero_pos = unit.get('position', [])
                
                # Récupérer les bonus du héros
                hero_bonuses = bonus_manager.get_hero_bonuses(hero_id)
                aura_radius = hero_bonuses.get('aura_radius', 0)
                movement_bonus = hero_bonuses.get('movement_bonus', 0)
                
                # Vérifier si l'unité est dans l'aura
                if aura_radius > 0 and movement_bonus > 0:
                    distance = self._hex_distance(position, hero_pos)
                    if distance <= aura_radius:
                        total_movement_bonus += movement_bonus
                        print(f"✨ [IA] Héros {hero_id} donne +{movement_bonus} mouvement (aura {aura_radius}, distance {distance})")
        
        # Arrondir le bonus (valeur discrète pour le champ de bataille)
        return round(total_movement_bonus)
    
    def _get_accessible_positions(self, start_pos: List[int], max_movement: int, battle: dict) -> List[List[int]]:
        """
        Trouve toutes les positions accessibles depuis start_pos dans un rayon de max_movement
        en utilisant un algorithme BFS (parcours en largeur)
        
        Args:
            start_pos: Position de départ [q, r]
            max_movement: Portée de mouvement maximum
            battle: Données de bataille
            
        Returns:
            Liste de positions accessibles [[q, r], ...]
        """
        from collections import deque
        
        # Directions hexagonales
        hex_directions = [
            [1, 0], [-1, 0],     # Est, Ouest
            [0, 1], [0, -1],     # Sud-Est, Nord-Ouest
            [1, -1], [-1, 1]     # Nord-Est, Sud-Ouest
        ]
        
        # BFS pour explorer toutes les cases accessibles
        visited = set()
        queue = deque([(start_pos, 0)])  # (position, distance)
        visited.add(tuple(start_pos))
        accessible = []
        
        while queue:
            current_pos, distance = queue.popleft()
            
            # Si on a atteint la portée max, ne pas explorer plus loin
            if distance >= max_movement:
                continue
            
            # Explorer les voisins
            for direction in hex_directions:
                neighbor = [current_pos[0] + direction[0], current_pos[1] + direction[1]]
                neighbor_tuple = tuple(neighbor)
                
                # Si déjà visité, ignorer
                if neighbor_tuple in visited:
                    continue
                
                visited.add(neighbor_tuple)
                
                # Si occupé, ignorer (mais continuer à explorer au-delà)
                if self._is_position_occupied(neighbor, battle):
                    continue
                
                # Vérifier que ce n'est pas une rivière (infranchissable)
                neighbor_terrain = self._get_terrain_at_position(neighbor, battle)
                if neighbor_terrain == 'river':
                    continue  # Ne pas ajouter aux positions accessibles
                
                # Cette case est accessible
                accessible.append(neighbor)
                
                # Ajouter à la queue pour exploration
                queue.append((neighbor, distance + 1))
        
        return accessible
    
    def _is_position_occupied(self, position: List[int], battle: dict) -> bool:
        """Vérifie si une position est occupée par une unité"""
        
        teams = battle.get('teams', {})
        
        for team_key, units in teams.items():
            for unit in units:
                unit_pos = unit.get('position', [])
                if unit_pos == position:
                    return True
        
        return False
    
    def _calculate_target_score(
        self,
        attacker: dict,
        target: dict,
        battle: dict,
        battlefield: dict,
        moral: int = 100
    ) -> dict:
        """
        Calcule le score d'une cible pour le panneau de debug
        
        Returns:
            dict avec total_score, breakdown détaillé, etc.
        """
        from app.battle.combat_calculator import combat_calculator
        import json
        import os
        
        # Charger la config IA
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(base_dir, 'data', 'ai_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            # Config par défaut si fichier absent
            config = {
                'decision_weights': {
                    'priority_hero': 100,
                    'priority_low_hp': 80,
                    'priority_ranged': 60,
                    'priority_closest': 40,
                    'priority_threat_level': 70
                }
            }
        
        weights = config.get('decision_weights', {})
        
        # Distance
        distance = self._hex_distance(attacker['position'], target['position'])
        
        # HP de la cible
        target_hp = target.get('current_hp', target.get('max_hp', 100))
        target_max_hp = target.get('max_hp', 100)
        hp_percent = target_hp / target_max_hp if target_max_hp > 0 else 0
        
        # Vérifier si c'est un héros
        target_id = target.get('unitId', '')
        is_hero = 'hero' in target_id.lower()
        
        # Vérifier si c'est une unité à distance
        target_type = combat_calculator.get_unit_type_from_id(target_id)
        is_ranged = target_type in ['Archers', 'Catapultes', 'Onagres']
        
        # CALCUL DES BONUS
        hero_bonus = weights.get('priority_hero', 100) if is_hero else 0
        
        # HP bas = score élevé (inverser le pourcentage)
        hp_bonus = weights.get('priority_low_hp', 80) * (1 - hp_percent)
        
        ranged_bonus = weights.get('priority_ranged', 60) if is_ranged else 0
        
        # Proximité (plus proche = meilleur score)
        distance_penalty = -1 * weights.get('priority_closest', 40) * distance / 10
        
        # Menace (nombre d'unités)
        threat_bonus = weights.get('priority_threat_level', 70) * target.get('unitCount', 1) / 10
        
        # SCORE TOTAL
        total_score = (
            hero_bonus +
            hp_bonus +
            ranged_bonus +
            distance_penalty +
            threat_bonus
        )
        
        return {
            'total_score': total_score,
            'hero_bonus': hero_bonus,
            'hp_bonus': round(hp_bonus, 1),
            'ranged_bonus': ranged_bonus,
            'distance_penalty': round(distance_penalty, 1),
            'threat_bonus': round(threat_bonus, 1),
            'distance': distance,
            'hp': f"{target_hp}/{target_max_hp}",
            'breakdown': f"H:{int(hero_bonus)} HP:{int(hp_bonus)} R:{int(ranged_bonus)} D:{int(distance_penalty)} T:{int(threat_bonus)}"
        }
    
    def _get_all_enemies(self, battle: dict, team_name: str) -> List[dict]:
        """Récupère tous les ennemis pour un team donné"""
        teams = battle.get('teams', {})
        enemies = []
        
        for team_key, units in teams.items():
            # Si ce n'est pas mon équipe
            if team_name not in team_key:
                enemies.extend(units)
        
        return enemies
    
    def _get_terrain_at_position(self, position: List[int], battle: dict) -> str:
        """Récupère le type de terrain à une position"""
        battlefield = battle.get('battlefield', {})
        battlefield_map = battlefield.get('battlefield_map', {})
        pos_key = f"{position[0]}_{position[1]}"
        
        if pos_key in battlefield_map:
            return battlefield_map[pos_key].get('terrain', 'plains')
        
        return 'plains'
    
    def _get_team_moral(self, battle: dict, player_id: str) -> float:
        """Récupère le moral de l'équipe du joueur"""
        teams = battle.get('teams', {})
        
        for team_key in teams.keys():
            if player_id in team_key:
                # Trouver les héros de cette équipe
                return self._calculate_team_moral(battle, team_key)
        
        return 100.0  # Moral par défaut
    
    def _get_enemy_moral(self, battle: dict, player_id: str) -> float:
        """Récupère le moral de l'équipe ennemie"""
        teams = battle.get('teams', {})
        
        for team_key in teams.keys():
            if player_id not in team_key:
                return self._calculate_team_moral(battle, team_key)
        
        return 100.0
    
    def _calculate_team_moral(self, battle: dict, team_key: str) -> float:
        """Calcule le moral d'une équipe (100 + bonus des héros)"""
        from app.battle.HeroBonusManager import HeroBonusManager
        
        base_moral = 100.0
        bonus_manager = HeroBonusManager()
        teams = battle.get('teams', {})
        team_units = teams.get(team_key, [])
        
        for unit in team_units:
            if 'hero' in unit.get('unitId', '').lower():
                hero_bonuses = bonus_manager.get_hero_bonuses(unit.get('unitId'))
                moral_bonus = hero_bonuses.get('moral_bonus', 0)
                base_moral += moral_bonus
        
        return base_moral
    
    def _get_hero_attack_bonus(self, unit_id: str, position: List[int], battle: dict) -> float:
        """Récupère le bonus d'attaque des héros à proximité"""
        from app.battle.HeroBonusManager import HeroBonusManager
        
        teams = battle.get('teams', {})
        unit_team = None
        
        for team_key, units in teams.items():
            for unit in units:
                if unit.get('unitId') == unit_id:
                    unit_team = team_key
                    break
            if unit_team:
                break
        
        if not unit_team:
            return 0.0
        
        team_units = teams.get(unit_team, [])
        bonus_manager = HeroBonusManager()
        total_bonus = 0.0
        
        for unit in team_units:
            if 'hero' in unit.get('unitId', '').lower():
                hero_id = unit.get('unitId')
                hero_pos = unit.get('position', [])
                hero_bonuses = bonus_manager.get_hero_bonuses(hero_id)
                aura_radius = hero_bonuses.get('aura_radius', 0)
                attack_bonus = hero_bonuses.get('attack_bonus', 0)
                
                if aura_radius > 0 and attack_bonus > 0:
                    distance = self._hex_distance(position, hero_pos)
                    if distance <= aura_radius:
                        total_bonus += attack_bonus
        
        return total_bonus
    
    def _get_hero_defense_bonus(self, unit_id: str, position: List[int], battle: dict) -> float:
        """Récupère le bonus de défense des héros à proximité"""
        from app.battle.HeroBonusManager import HeroBonusManager
        
        teams = battle.get('teams', {})
        unit_team = None
        
        for team_key, units in teams.items():
            for unit in units:
                if unit.get('unitId') == unit_id:
                    unit_team = team_key
                    break
            if unit_team:
                break
        
        if not unit_team:
            return 0.0
        
        team_units = teams.get(unit_team, [])
        bonus_manager = HeroBonusManager()
        total_bonus = 0.0
        
        for unit in team_units:
            if 'hero' in unit.get('unitId', '').lower():
                hero_id = unit.get('unitId')
                hero_pos = unit.get('position', [])
                hero_bonuses = bonus_manager.get_hero_bonuses(hero_id)
                aura_radius = hero_bonuses.get('aura_radius', 0)
                defense_bonus = hero_bonuses.get('defense_bonus', 0)
                
                if aura_radius > 0 and defense_bonus > 0:
                    distance = self._hex_distance(position, hero_pos)
                    if distance <= aura_radius:
                        total_bonus += defense_bonus
        
        return total_bonus


# Instance globale
battle_ai = BattleAIBasic()
