"""
=================================================================
RESOURCE_SITE_SERVICE.PY - Service pour la gestion des sites de ressources
=================================================================

Service pour gérer les donations, upgrades et timer des sites de ressources.
Inspiré de la logique d'Ikariam.

FONCTIONNALITÉS:
- Donations pour améliorer les sites
- Gestion des timers d'upgrade
- Passage automatique de niveau
- Historique des donations
- Validation des ressources

UTILISATION:
- Appelé par resource_routes.py
- Utilise resource_sites_database.py pour les configurations
=================================================================
"""

from datetime import datetime, timezone
import os

class ResourceSiteService:
    """Service pour gérer les sites de ressources"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        
        # Charger la configuration depuis le JSON
        config_path = os.path.join(data_manager.data_dir, 'resource_sites_config.json')
        config = data_manager._load_json_file(config_path, use_cache=True) or {}
        
        # Convertir les clés de niveau de string à int
        resource_site_levels = config.get('resource_site_levels', {})
        self.RESOURCE_SITE_LEVELS = {}
        for resource, levels in resource_site_levels.items():
            self.RESOURCE_SITE_LEVELS[resource] = {int(k): v for k, v in levels.items()}
        
        self.SITE_TO_RESOURCE = config.get('site_to_resource', {})
    
    def find_island_by_coords(self, island_coords, savegame_data):
        """Trouve une île par ses coordonnées ou ID"""
        # Charger l'univers pour récupérer la structure des îles
        universe_data = self.data_manager.load_universe()
        if not universe_data:
            return None
            
        islands = universe_data.get('islands', [])
        
        # Si island_coords est une liste [x, y], chercher par coordonnées
        if isinstance(island_coords, list) and len(island_coords) == 2:
            for island in islands:
                if island.get('coords') == island_coords:
                    return island
        
        # Si c'est un string ou un ID, chercher par ID
        else:
            island_id = str(island_coords)
            for island in islands:
                if str(island.get('id')) == island_id:
                    return island
        
        return None
    
    def find_resource_site_on_island(self, island, site_type, universe_data=None):
        """
        Trouve un site de ressource sur une île
        Note: savegame_data n'est plus utilisé, les sites sont dans resource_sites.json
        """
        # Chercher dans les éléments de l'île pour vérifier que le site existe
        elements = island.get('elements', [])
        site_exists = any(
            isinstance(element, dict) and element.get('type') == site_type 
            for element in elements
        )
        
        if not site_exists:
            return None
        
        # Si le site existe dans l'univers, récupérer ses données de progression
        return self.get_or_create_site_data(island, site_type)
    
    def get_or_create_site_data(self, island, site_type):
        """
        Récupère ou crée les données d'un site de ressource
        Utilise maintenant resource_sites.json au lieu de savegame.json
        """
        island_id = island.get('id')
        
        # Charger resource_sites.json
        resource_sites_data = self.data_manager.load_resource_sites()
        
        # Clé unique pour ce site : island_id + site_type
        site_key = f"{island_id}_{site_type}"
        
        # Si le site n'existe pas encore, le créer
        if site_key not in resource_sites_data['sites']:
            resource_sites_data['sites'][site_key] = {
                'island_id': island_id,
                'type': site_type,
                'level': 1,
                'donations': {},
                'donations_history': {}
            }
            # Sauvegarder immédiatement
            self.data_manager.save_resource_sites(resource_sites_data)
        
        return resource_sites_data['sites'][site_key]
    
    def check_and_upgrade_site(self, site):
        """Vérifie si un site doit être upgradé et le fait si nécessaire"""
        if not site.get("upgrade_start_time"):
            return False
            
        # Convertir le timestamp si c'est une string
        start_time = site["upgrade_start_time"]
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        
        now = datetime.now(timezone.utc)
        upgrade_time = site.get("upgrade_time", 0)
        elapsed = (now - start_time).total_seconds()
        
        if elapsed >= upgrade_time:
            # Passage de niveau
            site["level"] = site.get("level", 1) + 1
            site.pop("upgrade_start_time", None)
            site.pop("upgrade_time", None)
            site["donations"] = {}  # Remise à zéro des dons pour le nouveau niveau
            # NE PAS toucher à donations_history !
            return True
            
        return False
    
    def calculate_total_donations(self, site, resource_type):
        """Calcule le total des donations pour une ressource"""
        donations = site.get("donations", {})
        return sum(city_dons.get(resource_type, 0) for city_dons in donations.values())
    
    def can_start_upgrade(self, site, site_type):
        """Vérifie si on peut démarrer un upgrade"""
        if site.get("upgrade_start_time"):
            return False  # Upgrade déjà en cours
            
        level = site.get("level", 1)
        resource_type = self.SITE_TO_RESOURCE.get(site_type, site_type)
        site_config = self.RESOURCE_SITE_LEVELS.get(resource_type, {})
        level_config = site_config.get(level, {})
        upgrade_cost = level_config.get("upgrade_cost", {})
        
        if not upgrade_cost:
            return False  # Pas d'upgrade possible pour ce niveau
        
        # Calculer le total des donations
        donations_total = {}
        donations = site.get("donations", {})
        for city_dons in donations.values():
            for res, val in city_dons.items():
                donations_total[res] = donations_total.get(res, 0) + val
        
        # Vérifier si toutes les ressources sont disponibles
        return all(donations_total.get(res, 0) >= cost for res, cost in upgrade_cost.items())
    
    def start_upgrade(self, site, site_type):
        """Démarre un upgrade"""
        level = site.get("level", 1)
        resource_type = self.SITE_TO_RESOURCE.get(site_type, site_type)
        site_config = self.RESOURCE_SITE_LEVELS.get(resource_type, {})
        level_config = site_config.get(level, {})
        
        site["upgrade_start_time"] = datetime.now(timezone.utc).isoformat()
        site["upgrade_time"] = level_config.get("upgrade_time", 0)
        
        return True
    
    def donate_to_site(self, island_coords, site_type, city_id, active_city_id, player_id, resource_type, amount):
        """
        Effectue une donation à un site de ressources
        
        Args:
            island_coords: Coordonnées de l'île [x, y]
            site_type: Type du site (forest, quarry, etc.)
            city_id: ID de la ville qui fournit les ressources
            active_city_id: ID de la ville active dans le headerbar (détermine les permissions)
            player_id: ID du joueur
            resource_type: Type de ressource donné
            amount: Quantité à donner
            
        Returns:
            dict: Résultat de l'opération
        """
        try:
            # Charger les données
            savegame_data = self.data_manager.load_savegame()
            if not savegame_data:
                return {"success": False, "error": "Impossible de charger les données"}
            
            # Trouver l'île
            island = self.find_island_by_coords(island_coords, savegame_data)
            if not island:
                return {"success": False, "error": "Île introuvable"}
            
            # Trouver la ville active (celle dans le headerbar)
            active_city = next((c for c in savegame_data.get('cities', []) if c.get('id') == active_city_id), None)
            if not active_city:
                return {"success": False, "error": "Ville active introuvable"}
            
            # Vérifier que la ville active appartient au joueur
            if active_city.get('owner') != player_id:
                return {"success": False, "error": "La ville active ne vous appartient pas."}
            
            # VALIDATION PRINCIPALE: Vérifier que la ville active est sur la même île que le site
            island_id = island.get('id')
            active_city_island_id = active_city.get('island_id')
            if str(active_city_island_id) != str(island_id):
                return {"success": False, "error": "Seules les villes présentes sur cette île peuvent contribuer à l'amélioration de ce site de production."}
            
            # Trouver la ville qui fournit les ressources
            city = next((c for c in savegame_data.get('cities', []) if c.get('id') == city_id), None)
            if not city:
                return {"success": False, "error": "Ville qui fournit les ressources introuvable"}
            
            # Vérifier que la ville qui fournit les ressources appartient au joueur
            if city.get('owner') != player_id:
                return {"success": False, "error": "Cette ville ne vous appartient pas."}
            
            # Trouver le site de ressource (charge automatiquement resource_sites.json)
            site = self.find_resource_site_on_island(island, site_type)
            if not site:
                return {"success": False, "error": "Site non trouvé sur l'île"}
            
            # Charger resource_sites pour modifications
            resource_sites_data = self.data_manager.load_resource_sites()
            island_id = island.get('id')
            site_key = f"{island_id}_{site_type}"
            site_ref = resource_sites_data['sites'][site_key]  # Référence modifiable
            
            # Vérifier si le site peut être upgradé automatiquement
            upgraded_automatically = self.check_and_upgrade_site(site_ref)
            if upgraded_automatically:
                self.data_manager.save_resource_sites(resource_sites_data)
            
            # Récupérer les infos du niveau courant
            level = site_ref.get("level", 1)
            resource_key = self.SITE_TO_RESOURCE.get(site_type, site_type)
            site_config = self.RESOURCE_SITE_LEVELS.get(resource_key, {})
            level_config = site_config.get(level, {})
            upgrade_cost = level_config.get("upgrade_cost", {})
            
            # Vérifier que la ressource est requise
            if resource_type not in upgrade_cost:
                return {"success": False, "error": f"La ressource {resource_type} n'est pas requise pour l'amélioration."}
            
            # Calculer le maximum possible
            total_donated = self.calculate_total_donations(site_ref, resource_type)
            max_possible = max(0, upgrade_cost[resource_type] - total_donated)
            
            if max_possible <= 0:
                return {"success": False, "error": f"Le site a déjà reçu tout le {resource_type} nécessaire pour ce niveau."}
            
            # Limiter la donation au maximum possible
            amount = min(amount, max_possible)
            
            # Vérifier que la ville a suffisamment de ressources
            current_resource = city.get('resources', {}).get(resource_type, 0)
            if current_resource < amount:
                return {"success": False, "error": f"Pas assez de {resource_type} dans la ville."}
            
            # Déduire les ressources de la ville
            city['resources'][resource_type] = current_resource - amount
            
            # Ajouter la donation pour ce niveau
            if "donations" not in site_ref:
                site_ref["donations"] = {}
            if city_id not in site_ref["donations"]:
                site_ref["donations"][city_id] = {}
            site_ref["donations"][city_id][resource_type] = site_ref["donations"][city_id].get(resource_type, 0) + amount
            
            # Historique cumulé des dons (jamais remis à zéro)
            if "donations_history" not in site_ref:
                site_ref["donations_history"] = {}
            if city_id not in site_ref["donations_history"]:
                site_ref["donations_history"][city_id] = {}
            site_ref["donations_history"][city_id][resource_type] = site_ref["donations_history"][city_id].get(resource_type, 0) + amount
            
            upgraded = False
            
            # Vérifier si on peut démarrer un upgrade
            if self.can_start_upgrade(site_ref, site_type):
                self.start_upgrade(site_ref, site_type)
                upgraded = False  # Upgrade démarré mais pas encore terminé
            
            # Sauvegarder resource_sites.json (forcer la sauvegarde - action critique)
            self.data_manager.save_resource_sites(resource_sites_data, force_save=True)
            
            # Sauvegarder savegame.json pour les ressources de la ville
            self.data_manager.save_savegame(savegame_data, force_save=True)
            
            # Calculer le temps restant pour l'upgrade
            upgrade_remaining_time = 0
            if site_ref.get("upgrade_start_time"):
                start_time = site_ref["upgrade_start_time"]
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                now = datetime.now(timezone.utc)
                elapsed = (now - start_time).total_seconds()
                upgrade_time = site_ref.get("upgrade_time", 0)
                upgrade_remaining_time = max(0, int(upgrade_time - elapsed))
            
            return {
                "success": True,
                "donated_amount": amount,
                "donated_resource": resource_type,
                "remaining_resource": city['resources'][resource_type],
                "upgraded": upgraded,
                "current_level": site_ref.get("level", 1),
                "upgrade_in_progress": bool(site_ref.get("upgrade_start_time")),
                "upgrade_remaining_time": upgrade_remaining_time,
                "message": f'{amount} {resource_type} donné au site {site_type}'
            }
            
        except Exception as e:
            return {"success": False, "error": f"Erreur serveur: {str(e)}"}
    
    def get_site_info(self, island_coords, site_type, player_id):
        """
        Récupère les informations complètes d'un site de ressources
        
        Args:
            island_coords: Coordonnées de l'île [x, y]
            site_type: Type du site (forest, quarry, etc.)
            player_id: ID du joueur
            
        Returns:
            dict: Informations du site
        """
        try:
            # Charger les données
            savegame_data = self.data_manager.load_savegame()
            resource_sites_data = self.data_manager.load_resource_sites()
            
            if not savegame_data or not resource_sites_data:
                return {"success": False, "error": "Impossible de charger les données"}
            
            # Trouver l'île
            island = self.find_island_by_coords(island_coords, savegame_data)
            if not island:
                return {"success": False, "error": "Île introuvable"}
            
            # Trouver le site de ressource
            site = self.find_resource_site_on_island(island, site_type)
            if not site:
                return {"success": False, "error": "Site non trouvé sur l'île"}
            
            # Vérifier et appliquer les upgrades automatiques
            upgraded = self.check_and_upgrade_site(site)
            if upgraded:
                self.data_manager.save_resource_sites(resource_sites_data)
            
            # Récupérer les informations du niveau courant
            level = site.get("level", 1)
            resource_key = self.SITE_TO_RESOURCE.get(site_type, site_type)
            site_config = self.RESOURCE_SITE_LEVELS.get(resource_key, {})
            level_config = site_config.get(level, {})
            
            max_workers_per_city = level_config.get("max_workers_per_city", 0)
            upgrade_time = level_config.get("upgrade_time", 0)
            upgrade_cost = level_config.get("upgrade_cost", {})
            base_yield = level_config.get("base_yield", 1)
            
            # Informations du niveau suivant
            next_level_config = site_config.get(level + 1, {})
            next_level_benefits = {}
            if next_level_config:
                next_level_benefits = {
                    "max_workers_per_city": next_level_config.get("max_workers_per_city", 0)
                }
            
            # Récupérer toutes les villes de l'île
            island_id = island.get('id')
            cities = [c for c in savegame_data.get('cities', []) 
                     if c.get('island_id') == island_id]
            
            all_cities = []
            player_cities = []
            
            for city in cities:
                city_id = city.get('id')
                city_name = city.get('name', '')
                owner = city.get('owner')
                
                # Récupérer les ouvriers affectés au site
                workers = 0
                workers_assigned = city.get('workers_assigned', {})
                if site_type in workers_assigned:
                    workers = workers_assigned[site_type]
                elif resource_key in workers_assigned:
                    workers = workers_assigned[resource_key]
                
                city_info = {
                    "city_id": city_id,
                    "city_name": city_name,
                    "player": owner,
                    "workers": workers
                }
                
                all_cities.append(city_info)
                
                if owner == player_id:
                    # Ajouter des informations supplémentaires pour les villes du joueur
                    free_population = city.get('population_free', 0)
                    city_info.update({
                        "free_population": free_population
                    })
                    player_cities.append(city_info)
            
            # Timer d'upgrade
            upgrade_in_progress = False
            upgrade_remaining_time = 0
            if site.get("upgrade_start_time"):
                start_time = site["upgrade_start_time"]
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                now = datetime.now(timezone.utc)
                current_upgrade_time = site.get("upgrade_time", 0)
                elapsed = (now - start_time).total_seconds()
                if elapsed < current_upgrade_time:
                    upgrade_in_progress = True
                    upgrade_remaining_time = int(current_upgrade_time - elapsed)
            
            return {
                "success": True,
                "level": level,
                "max_workers_per_city": max_workers_per_city,
                "base_yield": base_yield,
                "upgrade_time": upgrade_time,
                "upgrade_cost": upgrade_cost,
                "next_level_benefits": next_level_benefits,
                "player_cities": player_cities,
                "all_cities": all_cities,
                "donations": site.get("donations", {}),
                "donations_history": site.get("donations_history", {}),
                "upgrade_in_progress": upgrade_in_progress,
                "upgrade_remaining_time": upgrade_remaining_time
            }
            
        except Exception as e:
            return {"success": False, "error": f"Erreur serveur: {str(e)}"}
