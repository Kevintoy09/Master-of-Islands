import json
import os
from ..transition_utils import load_savegame_transition, save_savegame_transition

class UnitImprovementService:
    def __init__(self, base_path=''):
        if base_path:
            self.base_path = base_path
        else:
            # Corriger le chemin : app/services -> vers la racine server
            self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Chemins des fichiers de données
        self.improvements_file = os.path.join(self.base_path, 'data', 'player_unit_improvements.json')
        self.players_file = os.path.join(self.base_path, 'gamedata', 'players.json')
        self.savegame_file = os.path.join(self.base_path, 'gamedata', 'savegame.json')
        self.unit_stats_file = os.path.join(self.base_path, 'data', 'unit_stats.json')
        
        # Configuration des améliorations
        self.available_improvements = {
            'infantry_light': ['attack_melee', 'defense_melee'],
            'infantry_heavy': ['attack_melee', 'defense_melee'],
            'archer': ['attack_ranged', 'defense_ranged'],
            'slinger': ['attack_ranged', 'defense_ranged'],
            'cavalry_light': ['attack_melee', 'defense_melee'],
            'cavalry_heavy': ['attack_melee', 'defense_melee'],
            'military_engineer': ['attack_melee', 'defense_melee'],
            'ballista': ['attack_ranged', 'defense_ranged'],
            'battering_ram': ['attack_melee', 'defense_melee'],
            'catapult': ['attack_ranged', 'defense_ranged']
        }
        
                # Chemins des fichiers suppl\u00e9mentaires
        self.buildings_file = os.path.join(self.base_path, 'data', 'buildings.json')
        self.config_file = os.path.join(self.base_path, 'data', 'unit_improvements_config.json')
        
        # Coûts par niveau (niveau 1-5)
        self.upgrade_costs = {
            1: {'gold': 100, 'wood': 50, 'stone': 25, 'iron': 20},
            2: {'gold': 150, 'wood': 75, 'stone': 40, 'iron': 30},
            3: {'gold': 200, 'wood': 100, 'stone': 50, 'iron': 40},
            4: {'gold': 300, 'wood': 150, 'stone': 75, 'iron': 60},
            5: {'gold': 500, 'wood': 250, 'stone': 125, 'iron': 100}
        }

    def get_forge_data(self, player_id):
        """Récupère toutes les données nécessaires pour la forge"""
        try:
            # Récupérer le niveau de la forge du joueur
            forge_level, max_improvement_level = self.get_player_forge_level(player_id)
            
            # Récupérer les unités disponibles selon le niveau de forge
            available_units = self.get_available_units_by_forge_level(forge_level)
            
            # Récupérer les statistiques de base des unités (seulement pour les unités disponibles)
            all_base_stats = self.get_unit_base_stats()
            base_stats = {unit: stats for unit, stats in all_base_stats.items() if unit in available_units}
            
            # Récupérer les ressources du joueur
            resources = self.get_player_resources(player_id)
            
            # Récupérer les améliorations actuelles
            current_improvements = self.get_player_improvements(player_id)
            
            # Calculer les statistiques avec améliorations
            enhanced_stats = self.calculate_enhanced_stats(base_stats, current_improvements)
            
            # Filtrer les améliorations disponibles pour les unités débloquées seulement
            available_improvements = {unit: self.available_improvements[unit] 
                                    for unit in available_units if unit in self.available_improvements}
            
            # Récupérer la configuration des améliorations
            improvement_config = self.get_improvement_config()
            
            return {
                'success': True,
                'forge_level': forge_level,
                'max_improvement_level': max_improvement_level,
                'available_units': available_units,
                'base_stats': base_stats,
                'enhanced_stats': enhanced_stats,
                'current_improvements': current_improvements,
                'resources': resources,
                'available_improvements': available_improvements,
                'upgrade_costs': self.upgrade_costs,
                'improvement_config': improvement_config
            }
            
        except Exception as e:
            print(f"Erreur get_forge_data: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_unit_base_stats(self):
        """Charge les statistiques de base des unités depuis unit_stats.json"""
        try:
            if not os.path.exists(self.unit_stats_file):
                return {}
            
            with open(self.unit_stats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extraire les stats des unités classiques
            base_stats = {}
            classical_units = data.get('classical_age', {})
            
            for unit_type, unit_data in classical_units.items():
                base_stats[unit_type] = {
                    'attack_melee': unit_data.get('attack_melee', 0),
                    'defense_melee': unit_data.get('defense_melee', 0),
                    'attack_ranged': unit_data.get('attack_ranged', 0),
                    'defense_ranged': unit_data.get('defense_ranged', 0),
                    'movement': unit_data.get('movement', 0),
                    'health': unit_data.get('health', 100)
                }
            
            return base_stats
            
        except Exception as e:
            print(f"Erreur chargement stats de base: {e}")
            return {}
    
    def get_player_resources(self, player_id):
        """Récupère les ressources du joueur : OR dans players.json, autres ressources combinées de toutes les villes dans savegame.json"""
        resources = {'gold': 0, 'wood': 0, 'stone': 0, 'iron': 0}
        
        try:
            # 1. Récupérer l'OR dans players.json
            if os.path.exists(self.players_file):
                with open(self.players_file, 'r', encoding='utf-8') as f:
                    players_data = json.load(f)
                
                players = players_data.get('players', [])
                for player in players:
                    if player.get('id') == player_id:
                        resources['gold'] = player.get('gold', 0)
                        break
            
            # 2. Récupérer toutes les ressources de toutes les villes du joueur dans savegame.json
            savegame_data = load_savegame_transition()
            if savegame_data:
                cities = savegame_data.get('cities', [])
                # Combiner les ressources de toutes les villes du joueur
                total_wood = 0
                total_stone = 0
                total_iron = 0
                
                for city in cities:
                    if city.get('owner') == player_id:
                        city_resources = city.get('resources', {})
                        total_wood += city_resources.get('wood', 0)
                        total_stone += city_resources.get('stone', 0) 
                        total_iron += city_resources.get('iron', 0)
                
                resources['wood'] = total_wood
                resources['stone'] = total_stone
                resources['iron'] = total_iron
                    
        except Exception as e:
            print(f"Erreur récupération ressources: {e}")
        
        return resources
    
    def get_player_improvements(self, player_id):
        """Récupère les améliorations actuelles du joueur"""
        try:
            if not os.path.exists(self.improvements_file):
                return {}
            
            with open(self.improvements_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data.get(player_id, {})
            
        except Exception as e:
            print(f"Erreur récupération améliorations: {e}")
            return {}
    
    def calculate_enhanced_stats(self, base_stats, improvements):
        """Calcule les statistiques avec les améliorations appliquées"""
        enhanced_stats = {}
        
        for unit_type, stats in base_stats.items():
            enhanced_stats[unit_type] = {}
            unit_improvements = improvements.get(unit_type, {})
            
            for stat_name, base_value in stats.items():
                improvement_bonus = unit_improvements.get(stat_name, 0)
                enhanced_value = int(base_value * (1 + improvement_bonus / 100))
                enhanced_stats[unit_type][stat_name] = {
                    'base': base_value,
                    'enhanced': enhanced_value,
                    'bonus_percent': improvement_bonus
                }
        
        return enhanced_stats
    
    def _bonus_to_points(self, bonus):
        """Convertit un pourcentage de bonus cumulatif en points d'amélioration"""
        config = self.get_improvement_config()
        bonus_progression = config.get('bonus_progression', [10, 8, 6, 4, 3])
        
        # Calcul inverse : trouver combien de points donnent ce bonus
        cumulative_bonus = 0
        for points in range(1, min(6, len(bonus_progression) + 1)):
            cumulative_bonus += bonus_progression[points - 1]
            if cumulative_bonus == bonus:
                return points
        return 0
    
    def _points_to_bonus(self, points):
        """Convertit des points d'amélioration en pourcentage de bonus cumulatif"""
        if points <= 0:
            return 0
        
        config = self.get_improvement_config()
        bonus_progression = config.get('bonus_progression', [10, 8, 6, 4, 3])
        
        # Calcul cumulatif : 1pt=10%, 2pts=10%+8%=18%, 3pts=10%+8%+6%=24%
        cumulative_bonus = 0
        for i in range(min(points, len(bonus_progression))):
            cumulative_bonus += bonus_progression[i]
        
        return cumulative_bonus
    
    def can_afford_upgrade(self, resources, level):
        """Vérifie si le joueur a les ressources nécessaires"""
        if level not in self.upgrade_costs:
            return False
        
        costs = self.upgrade_costs[level]
        for resource, amount in costs.items():
            if resources.get(resource, 0) < amount:
                return False
        return True
    
    def upgrade_unit(self, player_id, unit_type, improvement_type):
        """Améliore une statistique d'unité"""
        try:
            # Charger les améliorations actuelles
            improvements = {}
            if os.path.exists(self.improvements_file):
                with open(self.improvements_file, 'r', encoding='utf-8') as f:
                    improvements = json.load(f)
            
            # Initialiser la structure si nécessaire
            if player_id not in improvements:
                improvements[player_id] = {}
            if unit_type not in improvements[player_id]:
                improvements[player_id][unit_type] = {}
            
            # Vérifier le niveau actuel
            current_bonus = improvements[player_id][unit_type].get(improvement_type, 0)
            current_points = self._bonus_to_points(current_bonus)
            
            if current_points >= 5:
                return {"success": False, "message": "Niveau maximum atteint"}
            
            # Calculer le nouveau niveau et coût
            new_points = current_points + 1
            cost_level = new_points  # niveau 1-5 correspond aux coûts
            
            # Vérifier les ressources
            resources = self.get_player_resources(player_id)
            if not self.can_afford_upgrade(resources, cost_level):
                return {"success": False, "message": "Ressources insuffisantes"}
            
            # Déduire les ressources
            if not self.deduct_resources(player_id, cost_level):
                return {"success": False, "message": "Erreur lors de la déduction des ressources"}
            
            # Appliquer l'amélioration
            new_bonus = self._points_to_bonus(new_points)
            improvements[player_id][unit_type][improvement_type] = new_bonus
            
            # Sauvegarder
            with open(self.improvements_file, 'w', encoding='utf-8') as f:
                json.dump(improvements, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True, 
                "new_level": new_points,
                "new_bonus": new_bonus,
                "message": f"Amélioration appliquée (niveau {new_points})"
            }
            
        except Exception as e:
            print(f"Erreur upgrade_unit: {e}")
            return {"success": False, "message": f"Erreur: {str(e)}"}
    
    def get_config(self):
        """Retourne la configuration du système"""
        return {
            'available_improvements': self.available_improvements,
            'upgrade_costs': self.upgrade_costs,
            'bonus_levels': {1: 3, 2: 4, 3: 6, 4: 8, 5: 10}
        }
    
    def deduct_resources(self, player_id, level):
        """Déduit les ressources : OR dans players.json, BOIS/PIERRE dans savegame.json"""
        try:
            if level not in self.upgrade_costs:
                return False
            
            costs = self.upgrade_costs[level]
            
            # 1. Déduire l'OR dans players.json
            if 'gold' in costs:
                if not os.path.exists(self.players_file):
                    return False
                    
                with open(self.players_file, 'r', encoding='utf-8') as f:
                    players_data = json.load(f)
                
                player_found = False
                for i, player in enumerate(players_data.get('players', [])):
                    if player.get('id') == player_id:
                        current_gold = player.get('gold', 0)
                        if current_gold < costs['gold']:
                            return False
                        
                        players_data['players'][i]['gold'] = current_gold - costs['gold']
                        player_found = True
                        break
                
                if not player_found:
                    return False
                
                with open(self.players_file, 'w', encoding='utf-8') as f:
                    json.dump(players_data, f, ensure_ascii=False, indent=2)
            
            # 2. Déduire BOIS/PIERRE/FER dans savegame.json via SaveService
            wood_cost = costs.get('wood', 0)
            stone_cost = costs.get('stone', 0)
            iron_cost = costs.get('iron', 0)
            
            if wood_cost > 0 or stone_cost > 0 or iron_cost > 0:
                # Utiliser le SaveService au lieu de la lecture directe
                savegame_data = load_savegame_transition()
                if not savegame_data:
                    return False
                
                # D'abord vérifier que le joueur a assez de ressources (total de toutes les villes)
                player_resources = self.get_player_resources(player_id)
                if (player_resources.get('wood', 0) < wood_cost or 
                    player_resources.get('stone', 0) < stone_cost or
                    player_resources.get('iron', 0) < iron_cost):
                    return False
                
                # Déduire les ressources de la première ville trouvée (ville principale)
                city_found = False
                for i, city in enumerate(savegame_data.get('cities', [])):
                    if city.get('owner') == player_id:
                        city_resources = city.get('resources', {})
                        current_wood = city_resources.get('wood', 0)
                        current_stone = city_resources.get('stone', 0)
                        current_iron = city_resources.get('iron', 0)
                        
                        # Déduire des ressources de cette ville (même si elle n'a pas tout)
                        wood_deduction = min(wood_cost, current_wood)
                        stone_deduction = min(stone_cost, current_stone)
                        iron_deduction = min(iron_cost, current_iron)
                        
                        city_resources['wood'] = current_wood - wood_deduction
                        city_resources['stone'] = current_stone - stone_deduction
                        city_resources['iron'] = current_iron - iron_deduction
                        
                        savegame_data['cities'][i]['resources'] = city_resources
                        city_found = True
                        
                        # Mettre à jour les coûts restants
                        wood_cost -= wood_deduction
                        stone_cost -= stone_deduction
                        iron_cost -= iron_deduction
                        
                        # Si tout est déduit, sortir
                        if wood_cost <= 0 and stone_cost <= 0 and iron_cost <= 0:
                            break
                
                if not city_found:
                    return False
                
                # Si il reste des ressources à déduire, les déduire des autres villes
                if wood_cost > 0 or stone_cost > 0 or iron_cost > 0:
                    for i, city in enumerate(savegame_data.get('cities', [])):
                        if city.get('owner') == player_id:
                            city_resources = city.get('resources', {})
                            
                            wood_deduction = min(wood_cost, city_resources.get('wood', 0))
                            stone_deduction = min(stone_cost, city_resources.get('stone', 0))
                            iron_deduction = min(iron_cost, city_resources.get('iron', 0))
                            
                            city_resources['wood'] = city_resources.get('wood', 0) - wood_deduction
                            city_resources['stone'] = city_resources.get('stone', 0) - stone_deduction
                            city_resources['iron'] = city_resources.get('iron', 0) - iron_deduction
                            
                            savegame_data['cities'][i]['resources'] = city_resources
                            
                            wood_cost -= wood_deduction
                            stone_cost -= stone_deduction
                            iron_cost -= iron_deduction
                            
                            if wood_cost <= 0 and stone_cost <= 0 and iron_cost <= 0:
                                break
                
                # Sauvegarder via SaveService
                if not save_savegame_transition(savegame_data, force=True):
                    return False
            
            return True
            
        except Exception as e:
            print(f"Erreur déduction ressources: {e}")
            return False
    
    def downgrade_unit(self, player_id, unit_type, improvement_type):
        """Rétrograde une statistique d'unité et rembourse des ressources"""
        try:
            # Charger les améliorations actuelles
            improvements = {}
            if os.path.exists(self.improvements_file):
                with open(self.improvements_file, 'r', encoding='utf-8') as f:
                    improvements = json.load(f)
            
            # Vérifier que l'amélioration existe
            if (player_id not in improvements or 
                unit_type not in improvements[player_id] or 
                improvement_type not in improvements[player_id][unit_type]):
                return {"success": False, "message": "Aucune amélioration à rétrograder"}
            
            current_bonus = improvements[player_id][unit_type][improvement_type]
            current_points = self._bonus_to_points(current_bonus)
            
            if current_points <= 0:
                return {"success": False, "message": "Aucune amélioration à rétrograder"}
            
            # Plus de remboursement lors des downgrades
            
            # Rétrograder
            new_points = current_points - 1
            if new_points > 0:
                new_bonus = self._points_to_bonus(new_points)
                improvements[player_id][unit_type][improvement_type] = new_bonus
            else:
                # Supprimer complètement l'amélioration
                del improvements[player_id][unit_type][improvement_type]
                if not improvements[player_id][unit_type]:
                    del improvements[player_id][unit_type]
                if not improvements[player_id]:
                    del improvements[player_id]
            
            # Sauvegarder
            with open(self.improvements_file, 'w', encoding='utf-8') as f:
                json.dump(improvements, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True, 
                "new_level": new_points,
                "new_bonus": self._points_to_bonus(new_points) if new_points > 0 else 0,
                "message": f"Rétrogradation effectuée (niveau {new_points})"
            }
            
        except Exception as e:
            print(f"Erreur downgrade_unit: {e}")
            return {"success": False, "message": f"Erreur: {str(e)}"}
    
    def get_player_forge_level(self, player_id):
        """Récupère le niveau de la forge du joueur depuis savegame.json"""
        try:
            if not os.path.exists(self.savegame_file):
                return 0, 0
                
            with open(self.savegame_file, 'r', encoding='utf-8') as f:
                savegame_data = json.load(f)
            
            # Trouver les villes du joueur
            cities = savegame_data.get('cities', [])
            for city in cities:
                if city.get('owner') == player_id:
                    buildings = city.get('buildings', [])
                    for building in buildings:
                        if building.get('name') == 'Forge d\'Armement':
                            forge_level = building.get('level', 0)
                            # Récupérer le max_improvement_level depuis buildings.json
                            max_improvement_level = self.get_max_improvement_level_for_forge(forge_level)
                            return forge_level, max_improvement_level
            
            return 0, 0  # Pas de forge trouvée
            
        except Exception as e:
            print(f"Erreur récupération niveau forge: {e}")
            return 0, 0
    
    def get_max_improvement_level_for_forge(self, forge_level):
        """Récupère le niveau max d'amélioration selon le niveau de forge depuis buildings.json"""
        try:
            if not os.path.exists(self.buildings_file):
                return 1
                
            with open(self.buildings_file, 'r', encoding='utf-8') as f:
                buildings_data = json.load(f)
            
            forge_config = buildings_data.get('Forge d\'Armement', {})
            levels = forge_config.get('levels', [])
            
            if 1 <= forge_level <= len(levels):
                level_data = levels[forge_level - 1]
                return level_data.get('effect', {}).get('max_improvement_level', 1)
            
            return 1
            
        except Exception as e:
            print(f"Erreur récupération max_improvement_level: {e}")
            return 1
    
    def get_available_units_by_forge_level(self, forge_level):
        """Récupère la liste des unités disponibles selon le niveau de forge"""
        try:
            if not os.path.exists(self.buildings_file):
                return []
                
            with open(self.buildings_file, 'r', encoding='utf-8') as f:
                buildings_data = json.load(f)
            
            forge_config = buildings_data.get('Forge d\'Armement', {})
            levels = forge_config.get('levels', [])
            
            available_units = []
            
            # Récupérer toutes les unités débloquées jusqu'au niveau de forge actuel
            for level_index in range(min(forge_level, len(levels))):
                level_data = levels[level_index]
                unlocked_units = level_data.get('effect', {}).get('unlocks_improvements', [])
                available_units.extend(unlocked_units)
            
            # Supprimer les doublons en conservant l'ordre
            unique_units = []
            for unit in available_units:
                if unit not in unique_units:
                    unique_units.append(unit)
            
            return unique_units
            
        except Exception as e:
            print(f"Erreur récupération unités disponibles: {e}")
            return []
    
    def get_improvement_config(self):
        """Récupère la configuration des améliorations depuis unit_improvements_config.json"""
        try:
            if not os.path.exists(self.config_file):
                # Retourner une configuration par défaut
                return {
                    'max_improvement_points_per_unit': 5,
                    'bonus_progression': [10, 8, 6, 4, 3]
                }
                
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            config = config_data.get('config', {})
            return {
                'max_improvement_points_per_unit': config.get('max_improvement_points_per_unit', 5),
                'bonus_progression': config.get('bonus_progression', [10, 8, 6, 4, 3])
            }
            
        except Exception as e:
            print(f"Erreur récupération config améliorations: {e}")
            # Retourner une configuration par défaut
            return {
                'max_improvement_points_per_unit': 5,
                'bonus_progression': [10, 8, 6, 4, 3]
            }

