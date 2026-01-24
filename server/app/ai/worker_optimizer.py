"""
Optimiseur d'affectation des ouvriers pour l'IA
Algorithme intelligent basé sur:
- Balance d'or sur 24h
- Recherches débloquées
- Stockages pleins
- Répartition équitable
"""

from typing import Dict, List, Tuple


class WorkerOptimizer:
    """Calcule l'affectation optimale des ouvriers"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
    
    def calculate_optimal_assignment(self, city: Dict, player_id: str, ai_player: Dict) -> Dict[str, int]:
        """
        Calcule l'affectation optimale des ouvriers
        
        Returns:
            Dict {site_type: nb_workers}
        """
        # 1. Règle d'OR
        pop_available = self._calculate_available_population(city, player_id, ai_player)
        
        # 2. Sites disponibles selon recherches
        available_sites = self._get_available_sites(city, ai_player)
        
        # 3. Éliminer sites avec stockage plein
        sites_to_assign = self._filter_full_storage(city, available_sites)
        
        # 4. Répartir équitablement
        assignments = self._distribute_workers(pop_available, sites_to_assign)
        
        return assignments
    
    def _calculate_available_population(self, city: Dict, player_id: str, ai_player: Dict) -> int:
        """
        Calcule la population disponible pour affectation après réserve d'or
        
        Returns:
            int: Population disponible
        """
        total_pop = city.get('resources', {}).get('population_total', 0)
        
        # Balance d'or sur 24h
        balance_24h = self._calculate_gold_balance_24h(city, player_id, ai_player)
        
        if balance_24h < 0:
            # Réserver de la pop libre pour équilibrer
            pop_needed = int(abs(balance_24h) / 24) + 1  # 1 or/h par habitant
            return max(0, total_pop - pop_needed)
        
        return total_pop
    
    def _calculate_gold_balance_24h(self, city: Dict, player_id: str, ai_player: Dict) -> float:
        """
        Stock + (Production - Consommation) × 24h
        """
        try:
            from app.services.tick_service import TickService
            
            current_gold = ai_player.get('gold', 0)
            
            # Production: pop_libre × 1 or/h
            pop_free = city.get('resources', {}).get('population_free', 0)
            gold_rate = city.get('gold_rate', 1.0)
            gold_prod_per_hour = pop_free * 1.0 * gold_rate
            
            # Consommation militaire
            tick_service = TickService(self.data_manager)
            savegame = self.data_manager.load_savegame()
            player_cities = [c for c in savegame.get('cities', []) if c.get('owner') == player_id]
            
            military_cost_per_tick = tick_service._calculate_military_cost(player_id, player_cities)
            military_cost_per_hour = military_cost_per_tick * 360  # 360 ticks/heure
            
            return current_gold + (gold_prod_per_hour - military_cost_per_hour) * 24
            
        except Exception:
            return 0  # Erreur → suppose équilibre
    
    def _get_available_sites(self, city: Dict, ai_player: Dict) -> Dict[str, int]:
        """
        Retourne {site_type: capacité_max} selon recherches débloquées
        Lit les niveaux réels depuis resource_sites.json
        """
        unlocked = ai_player.get('unlocked_research', [])
        sites = {}
        
        # Academy: toujours disponible
        academy_cap = self._get_academy_capacity(city)
        if academy_cap > 0:
            sites['academy'] = academy_cap
        
        # Charger les sites de ressources depuis resource_sites.json
        island_id = city.get('island_id')
        if not island_id:
            return sites
        
        resource_sites_data = self.data_manager.load_resource_sites()
        
        # Forest: toujours accessible
        forest_cap = self._get_site_capacity(island_id, 'forest', resource_sites_data)
        if forest_cap > 0:
            sites['forest'] = forest_cap
        
        # Ressource de base
        if 'acces_ressources' in unlocked:
            base_type = self._get_base_resource_type(city)
            if base_type:
                # Conversion ressource → site (ex: papyrus → papyrus_field)
                site_type = self._resource_to_site(base_type)
                cap = self._get_site_capacity(island_id, site_type, resource_sites_data)
                if cap > 0:
                    sites[base_type] = cap
        
        # Ressources avancées
        if 'ressources_avancees' in unlocked:
            # TODO: Déterminer ressource avancée de l'île
            pass
        
        return sites
    
    def _filter_full_storage(self, city: Dict, sites: Dict[str, int]) -> Dict[str, int]:
        """
        Retire les sites dont le stockage est plein (100%)
        """
        filtered = {}
        resources = city.get('resources', {})
        storage = self._get_storage_capacity(city)
        
        for site_type, capacity in sites.items():
            if site_type == 'academy':
                # Pas de limite pour points de recherche
                filtered[site_type] = capacity
            else:
                resource_key = self._site_to_resource(site_type)
                current = resources.get(resource_key, 0)
                max_storage = storage.get(resource_key, 10000)
                
                if current < max_storage:
                    filtered[site_type] = capacity
        
        return filtered
    
    def _distribute_workers(self, population: int, sites: Dict[str, int]) -> Dict[str, int]:
        """
        Répartit la population équitablement entre les sites (division par nombre de sites)
        """
        if not sites:
            return {}
        
        total_capacity = sum(sites.values())
        
        if population >= total_capacity:
            # Remplir tous les sites au max
            return sites.copy()
        
        # Répartition équitable
        num_sites = len(sites)
        workers_per_site = population // num_sites
        remainder = population % num_sites
        
        assignments = {}
        for i, (site_type, max_cap) in enumerate(sites.items()):
            workers = workers_per_site + (1 if i < remainder else 0)
            assignments[site_type] = min(workers, max_cap)
        
        return assignments
    
    def _get_academy_capacity(self, city: Dict) -> int:
        """Capacité académie selon son niveau réel"""
        buildings = city.get('buildings', [])
        academy = next((b for b in buildings if b.get('name') == 'Academy'), None)
        if not academy:
            return 0
        
        # Lire la capacité réelle depuis buildings.json
        try:
            buildings_data = self.data_manager.load_buildings()
            academy_config = buildings_data.get('Academy', {})
            levels = academy_config.get('levels', [])
            
            academy_level = academy.get('level', 1)
            level_data = next((l for l in levels if l.get('level') == academy_level), None)
            
            if level_data:
                # Le champ s'appelle 'max_workers' dans buildings.json
                capacity = level_data.get('effect', {}).get('max_workers', 10)
                return capacity
            
            return 10  # Fallback
        except Exception as e:
            print(f"⚠️ [ACADEMY] Erreur: {e}")
            return 10  # Fallback si erreur
    
    def _get_base_resource_type(self, city: Dict) -> str:
        """
        Détermine la ressource de base de l'île
        Retourne la CLÉ RESSOURCE ('papyrus', 'stone', etc) PAS le site
        """
        # La ressource de base est stockée DIRECTEMENT dans la ville !
        # Pas besoin de chercher dans les îles
        base_resource = city.get('base_resource')
        return base_resource  # Retourne 'papyrus', 'stone', 'iron', 'cereal'
    
    def _get_storage_capacity(self, city: Dict) -> Dict[str, int]:
        """
        Calcule la capacité de stockage réelle depuis les bâtiments
        Utilise GameLogic.get_city_storage_limits()
        """
        from app.game_logic import GameLogic
        
        game_logic = GameLogic(self.data_manager)
        return game_logic.get_city_storage_limits(city)
    
    def _site_to_resource(self, site_type: str) -> str:
        """
        Convertit site → clé ressource
        Utilise SITE_TO_RESOURCE du jeu
        """
        try:
            from app.data.resource_sites_database import SITE_TO_RESOURCE
            return SITE_TO_RESOURCE.get(site_type, site_type)
        except ImportError:
            # Fallback si import échoue
            mapping = {
                'forest': 'wood',
                'quarry': 'stone',
                'iron_mine': 'iron',
                'cereal_field': 'cereal',
                'grain_field': 'cereal',
                'papyrus_field': 'papyrus',
                'papyrus_pond': 'papyrus',
                'marble_quarry': 'marble',
                'marble_mine': 'marble',
                'vineyard': 'wine',
                'glassworks': 'glass',
                'glass_workshop': 'glass',
                'horse_ranch': 'horse',
                'coal_mine': 'coal',
                'gunpowder_lab': 'gunpowder',
                'spice_garden': 'spices',
                'cotton_field': 'cotton'
            }
            return mapping.get(site_type, site_type)
    
    def _resource_to_site(self, resource_type: str) -> str:
        """
        Convertit ressource → type de site
        Ex: papyrus → papyrus_field
        """
        mapping = {
            'wood': 'forest',
            'stone': 'quarry',
            'iron': 'iron_mine',
            'cereal': 'cereal_field',
            'papyrus': 'papyrus_field',
            'marble': 'marble_quarry',
            'wine': 'vineyard',
            'glass': 'glassworks',
            'horse': 'horse_ranch',
            'coal': 'coal_mine',
            'gunpowder': 'gunpowder_lab',
            'spices': 'spice_garden',
            'cotton': 'cotton_field'
        }
        return mapping.get(resource_type, resource_type)
    
    def _get_site_capacity(self, island_id: str, site_type: str, resource_sites_data: Dict) -> int:
        """
        Lit la capacité réelle d'un site depuis resource_sites.json
        """
        try:
            from app.data.resource_sites_database import RESOURCE_SITE_LEVELS, SITE_TO_RESOURCE
            
            site_key = f"{island_id}_{site_type}"
            site_info = resource_sites_data.get('sites', {}).get(site_key, {})
            
            level = site_info.get('level', 1)
            resource_type = SITE_TO_RESOURCE.get(site_type, site_type)
            
            site_levels = RESOURCE_SITE_LEVELS.get(resource_type, {})
            level_data = site_levels.get(str(level), {})
            
            return level_data.get('max_workers_per_city', 10)
        except Exception:
            return 10  # Fallback
