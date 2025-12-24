"""
LOGIQUE MÉTIER CENTRALISÉE DU JEU

RÔLE:
    Classe centrale contenant toute la logique de gameplay.
    Sépare complètement la logique métier des routes API pour une meilleure maintenabilité.

RESPONSABILITÉS:
    1. Calcul de la production de ressources (avec bonus bâtiments + recherche)
    2. Gestion de la population (croissance, consommation de céréales)
    3. Calcul des capacités de stockage
    4. Gestion des bonus d'architecte (construction)
    5. Attribution des ouvriers sur les sites de ressources
    6. Gestion du moral et de la satisfaction
    7. Calcul des coûts de construction

ARCHITECTURE DES BONUS:
    Production = Base × (1 + Bonus_Bâtiment% + Bonus_Recherche% + Bonus_Spécial%)
    
    - Bonus bâtiment : Lus depuis city.buildings (ex: Scierie +10% bois)
    - Bonus recherche : Lus depuis player.research_effects.resource_bonuses
    - Les bonus recherche s'appliquent à TOUTES les villes du joueur

POINTS CLÉS:
    - Pas de logique dans les routes, tout passe par GameLogic
    - Les bonus de recherche sont chargés depuis le JOUEUR, pas la ville
    - Utilise DataManager pour accéder aux données
    - Système de transition pour la compatibilité savegame/players.json

DÉPENDANCES:
    - DataManager : Accès aux données (savegame, players, buildings, etc.)
    - transition_utils : Système de compatibilité entre ancienne/nouvelle architecture

HISTORIQUE:
    - Refonte majeure : Bonus de recherche au niveau joueur (pas ville)
    - calculate_total_production_rate() : Lit player.research_effects.resource_bonuses
"""

from typing import Dict, List, Optional, Tuple
from .data_manager import DataManager
from .transition_utils import load_savegame_transition, save_savegame_transition

def get_active_resources_by_era(era: str = "all") -> List[str]:
    """
    Retourne les ressources actives selon l'ère du jeu.
    Args:
        era: "early", "mid", "late", ou "all"
    """
    early_game_resources = ['wood', 'stone', 'iron', 'cereal', 'papyrus']
    mid_game_resources = ['marble', 'wine', 'horse', 'glass']
    late_game_resources = ['coal', 'gunpowder', 'spices', 'cotton']
    
    if era == "early":
        return early_game_resources
    elif era == "mid": 
        return early_game_resources + mid_game_resources
    elif era == "late":
        return early_game_resources + mid_game_resources + late_game_resources
    else:  # "all" par défaut
        return early_game_resources + mid_game_resources + late_game_resources

class GameLogic:
    """Gestionnaire de la logique métier du jeu"""
    
    def __init__(self, data_manager: DataManager):
        self.data = data_manager
    
    def get_city_storage_limits(self, city: Dict) -> Dict[str, int]:
        """
        Calcule les limites de stockage d'une ville basées sur ses entrepôts
        """
        import json
        import os
        
        # Charger les données des bâtiments
        buildings_path = os.path.join(self.data.data_dir, 'buildings.json')
        with open(buildings_path, 'r', encoding='utf-8') as f:
            buildings_data = json.load(f)
        
        warehouse_data = buildings_data.get('Entrepôt', {})
        levels = warehouse_data.get('levels', [])
        
        # Récupérer les entrepôts de la ville
        city_buildings = city.get('buildings', [])
        warehouses = [b for b in city_buildings if b.get('name') == 'Entrepôt']
        
        # Capacité de base de 3500 pour toutes les ressources (pour les joueurs débutants sans entrepôt)
        base_storage = {
            'wood': 3500, 'stone': 3500, 'iron': 3500, 'cereal': 3500, 'papyrus': 3500,
            'wine': 3500, 'marble': 3500, 'horse': 3500, 'glass': 3500,
            'gunpowder': 3500, 'coal': 3500, 'cotton': 3500, 'spices': 3500
        }
        
        # Calculer les capacités supplémentaires des entrepôts
        for warehouse in warehouses:
            level = warehouse.get('level', 1)
            if 1 <= level <= len(levels):
                level_data = levels[level - 1]  # Index 0-based
                effect = level_data.get('effect', {})
                storage_effect = effect.get('storage', {})
                
                for resource, capacity in storage_effect.items():
                    if resource in base_storage:
                        base_storage[resource] += capacity
        
        return base_storage
    
    def add_resource_with_limit(self, city: Dict, resource: str, amount: int) -> Dict:
        """
        Ajoute une ressource en respectant les limites de stockage
        Retourne: {'added': int, 'overflow': int, 'total': int}
        """
        if amount <= 0:
            return {'added': 0, 'overflow': 0, 'total': city.get('resources', {}).get(resource, 0)}
        
        # Obtenir les limites de stockage
        storage_limits = self.get_city_storage_limits(city)
        limit = storage_limits.get(resource, 1000)  # Défaut si ressource inconnue
        
        # Quantité actuelle
        current = city.get('resources', {}).get(resource, 0)
        
        # Calculer ce qui peut être ajouté
        available_space = max(0, limit - current)
        can_add = min(amount, available_space)
        overflow = amount - can_add
        
        # Ajouter la ressource
        if 'resources' not in city:
            city['resources'] = {}
        
        city['resources'][resource] = current + can_add
        
        return {
            'added': can_add,
            'overflow': overflow,
            'total': current + can_add
        }
    
    def calculate_actual_free_population(self, city: Dict) -> int:
        """Calcule la vraie population libre en soustrayant tous les ouvriers assignés"""
        population_total = city.get('resources', {}).get('population_total', 0)
        workers_assigned = city.get('workers_assigned', {})
        
        # Fix: si population_total est un dictionnaire, extraire la valeur 'total'
        if isinstance(population_total, dict):
            population_total = population_total.get('total', 0)
        
        # Somme de tous les ouvriers assignés à tous les sites
        total_assigned_workers = sum(workers_assigned.values())
        
        # Si population <= 1, tous les ouvriers doivent être à 0
        if population_total <= 1:
            if total_assigned_workers > 0:
                for resource in workers_assigned:
                    workers_assigned[resource] = 0
                total_assigned_workers = 0
        
        # Population libre = population totale - ouvriers assignés
        free_population = population_total - total_assigned_workers
        
        # Si population libre négative, retirer l'excès d'ouvriers
        if free_population < 0:
            excedent = abs(free_population)
            
            # Utiliser les vrais noms des ressources depuis workers_assigned
            available_resources = list(workers_assigned.keys())
            
            # Ordre de priorité pour retirer les ouvriers
            priority_order = []
            
            # 1. Academy en premier
            if 'academy' in available_resources:
                priority_order.append('academy')
            
            # 2. Forêt
            forest_resources = [res for res in available_resources if 'forest' in res and res not in priority_order]
            priority_order.extend(forest_resources)
            
            # 3. Champs et fermes
            field_resources = [res for res in available_resources if ('field' in res or 'farm' in res) and res not in priority_order]
            priority_order.extend(field_resources)
            
            # 4. Mines et carrières
            mine_resources = [res for res in available_resources if ('mine' in res or 'quarry' in res) and res not in priority_order]
            priority_order.extend(mine_resources)
            
            # 5. Ranchs
            ranch_resources = [res for res in available_resources if 'ranch' in res and res not in priority_order]
            priority_order.extend(ranch_resources)
            
            # 6. Autres ressources
            other_resources = [res for res in available_resources if res not in priority_order]
            priority_order.extend(other_resources)
            
            for resource in priority_order:
                if excedent <= 0:
                    break
                if resource in workers_assigned and workers_assigned[resource] > 0:
                    retire = min(workers_assigned[resource], excedent)
                    workers_assigned[resource] -= retire
                    excedent -= retire
            
            # Recalculer
            total_assigned_workers = sum(workers_assigned.values())
            free_population = population_total - total_assigned_workers
        
        return max(0, free_population)  # Ne peut pas être négative
    
    def find_city_by_id(self, city_id: str, savegame_data: Dict = None) -> Optional[Dict]:
        """Trouve une ville par son ID"""
        if not savegame_data:
            savegame_data = self.data.load_savegame()
        
        if not savegame_data:
            return None
        
        return next((c for c in savegame_data.get('cities', []) if c['id'] == city_id), None)
    
    def find_player_by_id(self, player_id: str) -> Optional[Dict]:
        """Trouve un joueur par son ID"""
        players_data = self.data.load_players()
        return next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
    
    def get_player_cities(self, player_id: str) -> List[Dict]:
        """Retourne toutes les villes d'un joueur"""
        savegame_data = self.data.load_savegame()
        if not savegame_data:
            return []
        
        return [city for city in savegame_data.get('cities', []) if city.get('owner') == player_id]
    
    def update_research_points_production(self) -> None:
        """Met à jour la production de points de recherche pour tous les joueurs"""
        # TimeManager supprimé - production gérée par ManualTickService
        
        current_tick = 0  # Valeur par défaut pour compatibilité
        
        try:
            # Charger les données
            savegame_data = self.data.load_savegame()
            players_data = self.data.load_players()
            buildings_data = self.data.load_buildings()
            
            if not all([savegame_data, players_data, buildings_data]):
                pass  # Données manquantes pour la recherche
                return
            
            # Parcourir tous les joueurs
            for player in players_data.get('players', []):
                try:
                    player_id = player['id']
                    
                    # Calculer la production totale de recherche pour ce joueur
                    total_research_production = 0
                    player_cities = [city for city in savegame_data.get('cities', []) if city.get('owner') == player_id]
                    
                    for city in player_cities:
                        try:
                            # Vérifier si la ville a une académie avec des ouvriers
                            buildings = city.get('buildings', [])
                            academy = next((b for b in buildings if b.get('name') in ['academy', 'Academy']), None)
                            
                            if academy:
                                workers = city.get('workers_assigned', {}).get('academy', 0)
                                if workers > 0:
                                    # Récupérer la config de l'académie selon son niveau
                                    academy_level = academy.get('level', 1)
                                    academy_config = buildings_data.get('Academy', {})  # Majuscule
                                    levels = academy_config.get('levels', [])
                                    
                                    if academy_level <= len(levels):
                                        level_config = levels[academy_level - 1]
                                        effect = level_config.get('effect', {})
                                        points_per_worker = effect.get('research_points_per_worker', 0.5)
                                        
                                        # Production = ouvriers × points par ouvrier
                                        city_production = workers * points_per_worker
                                        total_research_production += city_production
                        except Exception as e:
                            pass  # Erreur calcul production ville
                            continue
                    
                    # Utiliser le système de production centralisé
                    if total_research_production > 0:
                        current_points = player.get('research_points', 0.0)
                        last_tick = player.get('last_research_tick', current_tick)
                        
                        # Production désactivée - gérée par ManualTickService
                        points_to_add = 0  # Valeur par défaut pour compatibilité
                        
                        if points_to_add > 0:
                            new_points = current_points + points_to_add
                            player['research_points'] = round(new_points, 0)  # Arrondir à l'entier
                    
                    player['last_research_tick'] = current_tick
                    
                except Exception as e:
                    pass  # Erreur mise à jour joueur
                    continue
            
            # Sauvegarder les changements avec notre méthode sécurisée
            success = self._save_players_safely(players_data)
            if not success:
                print("❌ [ERROR] Échec de la sauvegarde des points de recherche")
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ [ERROR CRITIQUE] Erreur dans update_research_points_production: {e}")
            print(f"📋 [TRACEBACK] {error_details}")
    
    def validate_worker_assignment(self, city: Dict, site_type: str, workers: int, player_id: str = None) -> Tuple[bool, str]:
        """
        Valide l'assignation d'ouvriers à un site
        Retourne (succès, message_erreur)
        """
        if workers < 0:
            return False, "Nombre d'ouvriers invalide"
        
        # Vérifier si le joueur peut assigner des ouvriers (recherche "acces_ressources", sauf pour la forêt)
        if player_id and site_type != 'forest':
            from .business.research_service import ResearchService
            research_service = ResearchService(self.data)
            
            if not research_service.can_assign_workers_to_resource_sites(player_id):
                return False, "🔒 Recherche 'Accès Ressources de Base' requise pour assigner des ouvriers aux sites de ressources"
        
        # Vérifier la population disponible
        current_workers = city.get('workers_assigned', {}).get(site_type, 0)
        population_free = city.get('resources', {}).get('population_free', 0)
        available_population = population_free + current_workers
        
        if workers > available_population:
            return False, f"Population insuffisante. Disponible: {available_population}"
        
        # Vérifier la capacité du site
        try:
            from app.app.data.resource_sites_database import RESOURCE_SITE_LEVELS, SITE_TO_RESOURCE
            resource_type = SITE_TO_RESOURCE.get(site_type, site_type)
            site_data = RESOURCE_SITE_LEVELS.get(resource_type, {})
            
            if not site_data:
                return False, f"Type de site inconnu: {site_type}"
            
            max_workers = site_data.get('1', {}).get('max_workers_per_city', 10)
            if workers > max_workers:
                return False, f"Capacité maximale dépassée. Maximum: {max_workers}"
        
        except ImportError:
            return False, "Configuration des sites non disponible"
        
        return True, ""
    
    def assign_workers_to_site(self, city_id: str, site_type: str, workers: int, player_id: str = None) -> Tuple[bool, str, Dict]:
        """
        Assigne des ouvriers à un site de ressource
        Retourne (succès, message, données_ville_mise_à_jour)
        """
        savegame_data = self.data.load_savegame()
        if not savegame_data:
            return False, "Impossible de charger les données", {}
        
        city = self.find_city_by_id(city_id, savegame_data)
        if not city:
            return False, "Ville non trouvée", {}
        
        # Si player_id n'est pas fourni, le récupérer depuis la ville
        if not player_id:
            player_id = city.get('owner')
        
        # Valider l'assignation
        valid, error_msg = self.validate_worker_assignment(city, site_type, workers, player_id)
        if not valid:
            return False, error_msg, {}
        
        # Mettre à jour l'assignation
        if 'workers_assigned' not in city:
            city['workers_assigned'] = {}
        city['workers_assigned'][site_type] = workers
        
        # Recalculer la population libre
        city['resources']['population_free'] = self.calculate_actual_free_population(city)
        
        # Sauvegarder
        if not self.data.save_savegame(savegame_data):
            return False, "Erreur de sauvegarde", {}
        
        return True, f"{workers} ouvriers assignés au site {site_type}", city
    
    def update_resource_production(self) -> bool:
        """Met à jour la production de ressources pour toutes les villes"""
        try:
            savegame_data = self.data.load_savegame()
            if not savegame_data:
                return False
            
            from app.data.resource_sites_database import RESOURCE_SITE_LEVELS, SITE_TO_RESOURCE
            # TimeManager supprimé - utilise système de tick manuel maintenant
            
            for city in savegame_data.get('cities', []):
                # Production désactivée - gérée par ManualTickService
                production_interval = 1.0  # Valeur par défaut pour compatibilité
                
                # === CALCUL ET MISE À JOUR DES BONUS BÂTIMENTS ===
                # Calculer les bonus de tous les bâtiments de cette ville
                building_bonuses = self.calculate_building_bonuses(city)
                
                # Mettre à jour les champs building_bonus dans les ressources de la ville
                if 'resources' not in city:
                    city['resources'] = {}
                if 'building_bonus' not in city['resources']:
                    city['resources']['building_bonus'] = {}
                
                # Mettre à jour tous les bonus (même à 0) - or exclu car géré au niveau joueur
                base_resources = ['wood', 'stone', 'iron', 'cereal', 'papyrus', 'horse', 'marble', 'glass', 'wine', 'coal', 'gunpowder', 'spices', 'cotton']
                for resource in base_resources:
                    city['resources']['building_bonus'][resource] = building_bonuses.get(resource, 0)
                
                # === PRODUCTION DE BASE (avec bonus bâtiments et ouvriers) ===
                # Calculer la production pour toutes les ressources de base
                active_resources = get_active_resources_by_era('all')  # TODO: ajuster selon la progression
                
                for resource in active_resources:
                    # Calculer le taux de production total (ouvriers + bonus bâtiments)
                    total_rate = self.calculate_total_production_rate(city, resource)
                    production = total_rate * production_interval
                    
                    # Ajouter aux ressources de la ville avec limites
                    if 'resources' not in city:
                        city['resources'] = {}
                    
                    # Utiliser la nouvelle fonction avec limites
                    result = self.add_resource_with_limit(city, resource, production)
                    
                    # Log si il y a eu débordement (désactivé pour éviter le spam console)
                    # if result['overflow'] > 0:
                    #     print(f"🚫 Débordement dans {city.get('name', city.get('id'))}: {result['overflow']:.1f} {resource} perdu (stockage plein)")
            
                # Plus besoin de timestamp - le système centralisé gère tout
            
            # Sauvegarder les changements
            return self.data.save_savegame(savegame_data)
            
        except Exception as e:
            print(f"Erreur update_resource_production: {e}")
            return False

    def calculate_building_bonuses(self, city: Dict) -> Dict[str, float]:
        """Calcule les bonus de production des bâtiments construits dans une ville"""
        buildings_data = self.data.load_buildings()
        if not buildings_data:
            return {}
        
        building_bonuses = {}
        
        # Parcourir tous les bâtiments construits dans la ville
        for building in city.get('buildings', []):
            # Appliquer les effets si le bâtiment est terminé ou en upgrade
            is_upgrade = building.get('upgrade_in_progress', False)
            status = building.get('status', '')
            
            if status != 'Terminé' and not is_upgrade:
                continue
            
            # Récupérer les infos du bâtiment depuis la config
            building_name = building.get('name')
            building_level = building.get('level', 1)
            
            if building_name not in buildings_data:
                continue
            
            # Récupérer l'effet du niveau actuel
            levels = buildings_data[building_name].get('levels', [])
            if 0 < building_level <= len(levels):
                effect = levels[building_level - 1].get('effect', {})
                resource_bonuses = effect.get('resource_production_multiplier', {})
                
                for resource, bonus in resource_bonuses.items():
                    building_bonuses[resource] = building_bonuses.get(resource, 0) + bonus
        
        return building_bonuses

    def calculate_total_production_rate(self, city: Dict, resource: str) -> float:
        """Calcule le taux de production total pour une ressource donnée"""
        # Calculer la production passive de base à partir des sites de ressources avec ouvriers
        from app.data.resource_sites_database import RESOURCE_SITE_LEVELS, SITE_TO_RESOURCE
        workers_assigned = city.get('workers_assigned', {})
        base_production = 0.0  # Production de base calculée à partir des ouvriers
        
        for site_type, workers in workers_assigned.items():
            if workers > 0 and site_type in SITE_TO_RESOURCE:
                if SITE_TO_RESOURCE[site_type] == resource:
                    site_data = RESOURCE_SITE_LEVELS.get(resource, {}).get('1', {})
                    base_production_per_worker = site_data.get('base_yield', 1.0)
                    base_production += workers * base_production_per_worker
        
        # 1. Bonus des bâtiments (en pourcentage)
        building_bonuses = self.calculate_building_bonuses(city)
        building_bonus = building_bonuses.get(resource, 0)
        
        # 2. Bonus des recherches (en pourcentage) - AU NIVEAU JOUEUR
        research_bonus_percent = 0.0
        player_id = city.get('owner')
        if player_id:
            players_data = self.data.load_players()
            player = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
            if player:
                research_effects = player.get('research_effects', {})
                resource_bonuses = research_effects.get('resource_bonuses', {})
                research_bonus_percent = resource_bonuses.get(resource, 0) / 100.0
        
        # 3. Bonus spéciaux (pour l'instant 0)
        special_bonus_percent = 0
        
        # Formule : Production = Base_Production_Sites × (1 + Bonus_batiment% + Bonus_recherche% + Bonus_special%)
        # Convertir le bonus bâtiment en pourcentage (10 -> 0.10 = 10%)
        building_bonus_percent = building_bonus / 100.0
        
        total_production = base_production * (1 + building_bonus_percent + research_bonus_percent + special_bonus_percent)
        
        return total_production

    def calculate_architect_bonuses(self, city: Dict) -> Dict[str, int]:
        """Calcule les bonus de construction (Atelier d'Architecte + recherches du joueur)"""
        # TimeManager supprimé - utilise système simplifié
        
        buildings_data = self.data.load_buildings()
        current_tick = 0  # Valeur par défaut pour compatibilité
        
        construction_cost_reduction = 0
        construction_time_reduction = 0
        
        # 1. Bonus du bâtiment Atelier d'Architecte
        for building in city.get('buildings', []):
            building_name = building.get('name', '')
            building_level = building.get('level', 1)
            building_status = building.get('status', '')
            construction_end = building.get('construction_end', 0)
            
            # Vérifier si c'est un Atelier d'Architecte
            if building_name == "Atelier d'Architecte":
                # Vérifier si le bâtiment est terminé (statut "Terminé" OU construction_end dépassé)
                is_completed = (building_status == "Terminé" or 
                              (isinstance(construction_end, (int, float)) and construction_end <= current_tick))
                
                if is_completed:
                    # Récupérer la configuration du bâtiment
                    building_config = buildings_data.get(building_name, {})
                    levels = building_config.get('levels', [])
                    
                    if building_level <= len(levels):
                        level_config = levels[building_level - 1]
                        effect = level_config.get('effect', {})
                        
                        # Appliquer les bonus de construction
                        construction_cost_reduction = max(construction_cost_reduction, effect.get('construction_cost_reduction', 0))
                        construction_time_reduction = max(construction_time_reduction, effect.get('construction_time_reduction', 0))
        
        # 2. Bonus des recherches du joueur (Nombre d'Or, Mathématiques, etc.)
        owner_id = city.get('owner')
        if owner_id:
            players_data = self.data.load_players()
            player = next((p for p in players_data.get('players', []) if p.get('id') == owner_id), None)
            if player:
                research_data = self.data.load_research()
                unlocked_research = player.get('unlocked_research', [])
                
                for research_id in unlocked_research:
                    research = next((r for r in research_data.get('researches', []) if r.get('id') == research_id), None)
                    if research and 'effect' in research:
                        effect = research['effect']
                        # Cumuler les bonus de réduction de coût de construction
                        if 'construction_cost_reduction' in effect:
                            construction_cost_reduction += effect['construction_cost_reduction']
        
        return {
            'cost_reduction': construction_cost_reduction,
            'time_reduction': construction_time_reduction
        }

    def apply_architect_bonuses_to_building_cost(self, base_cost: Dict[str, int], city: Dict) -> Dict[str, int]:
        """Applique les bonus de l'Atelier d'Architecte au coût d'un bâtiment"""
        architect_bonuses = self.calculate_architect_bonuses(city)
        cost_reduction_percent = architect_bonuses.get('cost_reduction', 0) / 100.0
        
        reduced_cost = {}
        for resource, amount in base_cost.items():
            reduced_amount = int(amount * (1 - cost_reduction_percent))
            reduced_cost[resource] = max(1, reduced_amount)  # Minimum 1 ressource
        
        return reduced_cost

    def apply_architect_bonuses_to_building_time(self, base_time: int, city: Dict) -> int:
        """Applique les bonus de l'Atelier d'Architecte au temps de construction"""
        # Charger le multiplicateur global de temps de construction depuis admin_settings.json
        time_multiplier = self._load_construction_time_multiplier()
        
        # Appliquer d'abord le multiplicateur global
        adjusted_time = base_time * time_multiplier
        
        # Puis appliquer les bonus de l'Atelier d'Architecte
        architect_bonuses = self.calculate_architect_bonuses(city)
        time_reduction_percent = architect_bonuses.get('time_reduction', 0) / 100.0
        
        reduced_time = int(adjusted_time * (1 - time_reduction_percent))
        return max(1, reduced_time)  # Minimum 1 seconde
    
    def _load_construction_time_multiplier(self) -> float:
        """Charge le multiplicateur de temps de construction depuis admin_settings.json"""
        try:
            import os
            import json
            settings_file = os.path.join(self.data.data_dir, 'admin_settings.json')
            
            if not os.path.exists(settings_file):
                return 1.0  # Valeur par défaut si le fichier n'existe pas
            
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            return settings.get('construction_time_multiplier', 1.0)
        except Exception as e:
            print(f"Warning: Could not load construction_time_multiplier: {e}")
            return 1.0  # Valeur par défaut en cas d'erreur

    def update_construction_statuses(self):
        """
        Met à jour automatiquement le statut des constructions terminées.
        Cette fonction est appelée automatiquement lors de l'actualisation de l'état des villes.
        """
        import time
        import threading
        
        # Protection contre les exécutions simultanées (évite les doublons)
        if not hasattr(self, '_construction_lock_2'):
            self._construction_lock_2 = threading.Lock()
        
        # Protection contre les constructions déjà traitées
        if not hasattr(self, '_processed_constructions_2'):
            self._processed_constructions_2 = set()
        
        # Tentative d'acquisition non-bloquante
        if not self._construction_lock_2.acquire(blocking=False):
            # Une autre thread traite déjà les constructions
            return
        
        try:
            # TimeManager supprimé - constructions gérées par système manuel
            current_tick = 0  # Valeur par défaut pour compatibilité
            save_data = load_savegame_transition()
            has_changes = False
            
            for city in save_data.get('cities', []):
                for building in city.get('buildings', []):
                    construction_end = building.get('construction_end')
                    if (construction_end and 
                        isinstance(construction_end, (int, float)) and
                        construction_end <= current_tick and 
                        building.get('status') == 'En construction'):
                        
                        # Créer un ID unique pour ce bâtiment en construction
                        building_id = f"{city.get('id', 'unknown')}_{building.get('slot_id', 'unknown')}_{construction_end}"
                        
                        # Vérifier si cette construction a déjà été traitée
                        if building_id in self._processed_constructions_2:
                            continue
                        
                        # Marquer comme traité immédiatement
                        self._processed_constructions_2.add(building_id)
                        
                        # Construction terminée
                        building['status'] = 'Construit'
                        
                        # ✅ CRÉER NOTIFICATION IMMÉDIATEMENT
                        try:
                            from app.business.notification_service import NotificationService
                            from app.models.notification import NotificationType
                            notification_service = NotificationService(self.data)
                            
                            building_name = building.get('name', 'Bâtiment')
                            city_name = city.get('name', 'Ville')
                            player_id = city.get('owner', 'player_1')
                            level = building.get('level', 1)
                            
                            if level > 1:
                                title = "Développement terminé"
                                message = f"{building_name} niveau {level} terminé dans {city_name}"
                            else:
                                title = "Construction terminée"
                                message = f"{building_name} terminé dans {city_name}"
                            
                            notification_service.create_building_notification(
                                player_id=player_id,
                                building_name=building_name,
                                city_name=city_name
                            )
                            pass  # Notification créée
                        except Exception as e:
                            pass  # Erreur création notification
                        
                        # Nettoyer les champs de construction
                        building.pop('construction_end', None)
                        building.pop('started_at', None)
                        building.pop('duration', None)
                        building.pop('previous_level', None)  # Nettoyer le niveau précédent pour développements
                        
                        has_changes = True
            
            # Nettoyer les anciennes entrées (plus de 5 minutes)
            if hasattr(self, '_last_cleanup_2') and (current_tick - self._last_cleanup_2) > 300:
                self._processed_constructions_2.clear()
                self._last_cleanup_2 = current_tick
            elif not hasattr(self, '_last_cleanup_2'):
                self._last_cleanup_2 = current_tick
            
            # Sauvegarder si des changements ont eu lieu (SaveService avec force pour actions critiques)
            if has_changes:
                save_savegame_transition(save_data, force=True)
                
        finally:
            # Libérer le lock dans tous les cas
            self._construction_lock_2.release()

    def update_resource_production_in_memory(self, savegame_data):
        """Met à jour la production de ressources pour toutes les villes sans recharger les données"""
        try:
            if not savegame_data:
                return False
            
            from app.data.resource_sites_database import RESOURCE_SITE_LEVELS, SITE_TO_RESOURCE
            # TimeManager supprimé - utilise système de tick manuel maintenant
            
            current_tick = 0  # Valeur par défaut pour compatibilité
            
            for city in savegame_data.get('cities', []):
                # Production désactivée - gérée par ManualTickService
                production_interval = 1.0  # Valeur par défaut pour compatibilité
                
                # === CALCUL ET MISE À JOUR DES BONUS BÂTIMENTS ===
                # Calculer les bonus de tous les bâtiments de cette ville
                building_bonuses = self.calculate_building_bonuses(city)
                
                # Mettre à jour les champs building_bonus dans les ressources de la ville
                if 'resources' not in city:
                    city['resources'] = {}
                if 'building_bonus' not in city['resources']:
                    city['resources']['building_bonus'] = {}
                
                # Mettre à jour tous les bonus (même à 0) - or exclu car géré au niveau joueur
                base_resources = ['wood', 'stone', 'iron', 'cereal', 'papyrus', 'horse', 'marble', 'glass', 'wine', 'coal', 'gunpowder', 'spices', 'cotton']
                for resource in base_resources:
                    city['resources']['building_bonus'][resource] = building_bonuses.get(resource, 0)
                
                # === PRODUCTION DE BASE (avec bonus bâtiments et ouvriers) ===
                # Calculer la production pour toutes les ressources de base
                active_resources = get_active_resources_by_era('all')  # TODO: ajuster selon la progression
                
                for resource in active_resources:
                    # Calculer le taux de production total (ouvriers + bonus bâtiments)
                    total_rate = self.calculate_total_production_rate(city, resource)
                    production = total_rate * production_interval
                    
                    # Ajouter aux ressources de la ville avec limites
                    if 'resources' not in city:
                        city['resources'] = {}
                    
                    # Utiliser la nouvelle fonction avec limites
                    result = self.add_resource_with_limit(city, resource, production)
                    
                    # Log si il y a eu débordement (désactivé pour éviter le spam console)
                    # if result['overflow'] > 0:
                    #     print(f"🚫 Débordement dans {city.get('name', city.get('id'))}: {result['overflow']:.1f} {resource} perdu (stockage plein)")
            
                # Plus besoin de timestamp - le système centralisé gère tout
            
            return True
            
        except Exception as e:
            print(f"Erreur update_resource_production_in_memory: {e}")
            return False

    def update_construction_statuses_in_memory(self, savegame_data):
        """Met à jour automatiquement le statut des constructions terminées sans recharger les données"""
        import time
        import threading
        
        # Protection contre les exécutions simultanées (évite les doublons)
        if not hasattr(self, '_construction_lock'):
            self._construction_lock = threading.Lock()
        
        # Protection contre les constructions déjà traitées
        if not hasattr(self, '_processed_constructions'):
            self._processed_constructions = set()
        
        # Tentative d'acquisition non-bloquante
        if not self._construction_lock.acquire(blocking=False):
            # Une autre thread traite déjà les constructions
            return False
        
        try:
            # Utiliser le timestamp Unix actuel pour vérifier les constructions terminées
            current_time = int(time.time())
            has_changes = False
            
            for city in savegame_data.get('cities', []):
                for building in city.get('buildings', []):
                    # Vérifier les constructions terminées
                    construction_end = building.get('construction_end')
                    if (construction_end and 
                        isinstance(construction_end, (int, float)) and
                        construction_end <= current_time and 
                        building.get('status') == 'En construction'):
                        
                        # Créer un ID unique pour ce bâtiment en construction
                        building_id = f"{city.get('id', 'unknown')}_{building.get('slot_id', 'unknown')}_{construction_end}"
                        
                        # Vérifier si cette construction a déjà été traitée
                        if building_id in self._processed_constructions:
                            continue
                        
                        # Marquer comme traité immédiatement
                        self._processed_constructions.add(building_id)
                        
                        # Construction terminée
                        building['status'] = 'Terminé'
                        
                        # Vérifier si c'est un upgrade (a previous_level) ou une nouvelle construction
                        is_upgrade = 'previous_level' in building
                        
                        # Nettoyer les champs de construction
                        building.pop('construction_end', None)
                        building.pop('started_at', None)
                        building.pop('duration', None)
                        building.pop('previous_level', None)  # Nettoyer le niveau précédent pour développements
                        
                        # Mettre à jour les quêtes de construction
                        try:
                            from app.services.quest_service import quest_service
                            owner_id = city.get('owner')
                            if owner_id:
                                # Trouver le username depuis l'ID dans players.json
                                players_data = self.data.load_players()
                                players = players_data.get('players', [])
                                player = next((p for p in players if p.get('id') == owner_id), None)
                                if player and player.get('username'):
                                    building_name = building.get('name')
                                    quest_service.update_construction_quest(
                                        player['username'],
                                        building_name=building_name,
                                        is_upgrade=is_upgrade
                                    )
                        except Exception:
                                pass  # Silent fail
                        
                        has_changes = True
                    
                    # Vérifier les upgrades terminés
                    upgrade_end_time = building.get('upgrade_end_time')
                    if (upgrade_end_time and 
                        isinstance(upgrade_end_time, (int, float)) and
                        upgrade_end_time <= current_time and 
                        building.get('upgrade_in_progress', False)):
                        
                        # Créer un ID unique pour cet upgrade
                        upgrade_id = f"{city.get('id', 'unknown')}_{building.get('slot_id', 'unknown')}_upgrade_{upgrade_end_time}"
                        
                        # Vérifier si cet upgrade a déjà été traité
                        if upgrade_id in self._processed_constructions:
                            continue
                        
                        # Marquer comme traité immédiatement
                        self._processed_constructions.add(upgrade_id)
                        
                        # Upgrade terminé : passer au niveau supérieur
                        current_level = building.get('level', 1)
                        building['level'] = current_level + 1
                        building.pop('upgrade_in_progress', None)
                        building.pop('upgrade_end_time', None)
                        
                        # Les effets du bâtiment sont calculés dynamiquement par tick_service/game_logic
                        # depuis buildings.json - pas besoin de les stocker dans le savegame
                        
                        # Mettre à jour la quête de construction
                        try:
                            from app.services.quest_service import quest_service
                            owner_id = city.get('owner')
                            if owner_id:
                                # Trouver le username depuis l'ID dans players.json
                                players_data = self.data.load_players()
                                players = players_data.get('players', [])
                                player = next((p for p in players if p.get('id') == owner_id), None)
                                if player and player.get('username'):
                                    quest_service.update_construction_quest(player['username'])
                        except Exception:
                            pass  # Silent fail
                        
                        has_changes = True
            
            # Nettoyer les anciennes entrées (plus de 5 minutes)
            if hasattr(self, '_last_cleanup') and (current_time - self._last_cleanup) > 300:
                self._processed_constructions.clear()
                self._last_cleanup = current_time
            elif not hasattr(self, '_last_cleanup'):
                self._last_cleanup = current_time
            
            return has_changes
            
        finally:
            # Libérer le lock dans tous les cas
            self._construction_lock.release()

    def _save_players_safely(self, players_data: dict) -> bool:
        """
        Sauvegarde sécurisée des données joueurs avec préservation des champs transport.
        Utilise la même logique que PlayerResourcesService pour éviter les conflits.
        """
        import json
        import os
        import threading
        import time
        
        # Utiliser un verrou pour éviter la concurrence d'écriture
        if not hasattr(self, '_save_lock'):
            self._save_lock = threading.Lock()
        
        filepath = os.path.join(self.data.gamedata_dir, 'players.json')
        
        with self._save_lock:
            try:
                # Charger les données actuelles depuis le fichier avec retry
                current_data = {}
                if os.path.exists(filepath):
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read().strip()
                                if not content:
                                    if attempt < max_retries - 1:
                                        time.sleep(0.1)
                                        continue
                                    else:
                                        current_data = players_data
                                        break
                                current_data = json.loads(content)
                                break
                        except (json.JSONDecodeError, IOError) as e:
                            if attempt < max_retries - 1:
                                time.sleep(0.1)
                                continue
                            else:
                                current_data = players_data
                                break
                
                # Préserver les champs de transport pour chaque joueur
                if 'players' in current_data and 'players' in players_data:
                    for current_player in current_data['players']:
                        player_id = current_player.get('id')
                        if player_id:
                            # Trouver le joueur correspondant dans les nouvelles données
                            for new_player in players_data['players']:
                                if new_player.get('id') == player_id:
                                    # Préserver les champs de transport
                                    transport_fields = [
                                        'transport_ships_busy',
                                        'transport_ships_total'
                                    ]
                                    for field in transport_fields:
                                        if field in current_player:
                                            new_player[field] = current_player[field]
                                    break
                
                # Sauvegarder avec retry pour les erreurs de permissions
                # CORRECTIF: Utiliser players_data (nouvelles données) et non current_data (anciennes données)
                data_to_save = players_data
                max_save_retries = 3
                for save_attempt in range(max_save_retries):
                    try:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                        return True  # Succès
                    except (IOError, OSError) as save_error:
                        if save_attempt < max_save_retries - 1:
                            time.sleep(0.05)
                            continue
                        else:
                            print(f"❌ Impossible de sauvegarder après {max_save_retries} tentatives: {save_error}")
                            return False
                
            except Exception as e:
                print(f"❌ Erreur lors de la sauvegarde sécurisée: {e}")
                return False
