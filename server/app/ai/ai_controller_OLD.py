"""
AIController - Contrôleur principal du système d'IA
Gère tous les joueurs IA et leur exécution
"""

import json
import os
import random
from typing import Dict, List, Optional
from datetime import datetime

from .decision_engine import DecisionEngine
from .personality import Personality
from .utils.activity_simulator import get_activity_simulator
from .utils.data_loader import get_data_loader


class AIController:
    """Contrôleur principal des IAs"""
    
    def __init__(self, data_manager, config_path: str = None):
        """
        Args:
            data_manager: Instance de DataManager
            config_path: Chemin vers ai_config.json (optionnel)
        """
        self.data_manager = data_manager
        
        # Charger la configuration
        if config_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, 'ai', 'config', 'ai_config.json')
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Cache des instances d'IA
        self._ai_instances: Dict[str, DecisionEngine] = {}
    
    def execute_all_ais(self):
        """Exécute un tick pour toutes les IAs actives"""
        if not self.config['global']['enabled']:
            print("⚠️ Système IA désactivé (global.enabled = false)")
            return
        
        # Récupérer tous les joueurs IA
        ai_players = self.get_all_ai_players()
        
        if not ai_players:
            return  # Pas de log, exécuté à chaque tick
        
        print(f"\n🤖 Exécution cycle IA pour {len(ai_players)} joueur(s)")
        
        for ai_player in ai_players:
            try:
                self.execute_ai(ai_player)
            except Exception as e:
                player_name = ai_player.get('username', 'Unknown')
                print(f"❌ Erreur AI {player_name}: {e}")
                import traceback
                traceback.print_exc()
    
    def execute_ai(self, ai_player: Dict):
        """
        Exécute un tick pour une IA spécifique
        
        Args:
            ai_player: Données du joueur IA
        """
        player_id = ai_player.get('id')
        player_name = ai_player.get('username', 'Unknown')
        
        # Vérifier si l'IA est "en ligne" (désactivé pour tests)
        # activity_simulator = get_activity_simulator(
        #     player_id, 
        #     self.config['activity_simulation']
        # )
        # 
        # if not activity_simulator.is_online():
        #     return  # Pas de log pour ne pas polluer la console
        
        # Vérifier si Academy existe mais n'a pas de workers → forcer allocation
        self._ensure_academy_workers(ai_player)
        
        # Récupérer ou créer l'instance DecisionEngine
        if player_id not in self._ai_instances:
            self._ai_instances[player_id] = self._create_decision_engine(ai_player)
        
        decision_engine = self._ai_instances[player_id]
        
        # Exécuter un tick
        action = decision_engine.tick()
        
        if action:
            action_type = action.get('type')
            priority = action.get('priority', 0)
            print(f"  🎯 [{player_name}] {action_type} (priorité: {priority:.0f})")
            self._execute_action(ai_player, action)
            
            # Auto-affectation des ouvriers SEULEMENT si l'action le demande explicitement
            # (ex: reallocate_workers, nouveau bâtiment terminé, upgrade Academy, etc.)
            if action_type in ['reallocate_workers'] or action.get('trigger_worker_reallocation', False):
                self._auto_assign_workers(ai_player)
    
    def _create_decision_engine(self, ai_player: Dict) -> DecisionEngine:
        """
        Crée une instance de DecisionEngine pour une IA
        
        Args:
            ai_player: Données du joueur IA
        
        Returns:
            Instance de DecisionEngine
        """
        personality_type = ai_player.get('personality', 'balanced')
        difficulty = ai_player.get('difficulty', 'medium')
        
        personality = Personality(personality_type)
        
        # Charger les modules actifs
        modules = self._load_modules(ai_player, personality_type)
        
        return DecisionEngine(
            ai_player=ai_player,
            personality=personality,
            difficulty=difficulty,
            modules=modules,
            data_manager=self.data_manager
        )
    
    def _load_modules(self, ai_player: Dict, personality_type: str) -> List:
        """
        Charge les modules actifs pour une IA
        
        Args:
            ai_player: Données du joueur IA
            personality_type: Type de personnalité
        
        Returns:
            Liste des instances de modules
        """
        modules = []
        
        personality_config = self.config['personalities'].get(personality_type, {})
        enabled_modules = personality_config.get('modules', {})
        
        # CityBuilderModule
        if enabled_modules.get('city_builder', False):
            from .modules.city_builder import CityBuilderModule
            module_config = self.config['modules_config']['city_builder']
            modules.append(CityBuilderModule(ai_player, module_config, self.data_manager))
        
        # ResourceManagerModule
        if enabled_modules.get('resource_manager', False):
            from .modules.resource_manager import ResourceManagerModule
            module_config = self.config['modules_config']['resource_manager']
            modules.append(ResourceManagerModule(ai_player, module_config, self.data_manager))
        
        # ColonizerModule
        if enabled_modules.get('colonizer', False):
            from .modules.colonizer import ColonizerModule
            module_config = self.config['modules_config']['colonizer']
            modules.append(ColonizerModule(ai_player, module_config, self.data_manager))
        
        # TODO: Ajouter les autres modules au fur et à mesure
        
        return modules
    
    def _execute_action(self, ai_player: Dict, action: Dict):
        """
        Exécute une action décidée par l'IA
        
        Args:
            ai_player: Données du joueur IA
            action: Action à exécuter
        """
        action_type = action.get('type')
        player_name = ai_player.get('username', 'Unknown')
        
        try:
            if action_type == 'build':
                self._execute_build_action(ai_player, action)
            
            elif action_type == 'upgrade':
                self._execute_upgrade_action(ai_player, action)
            
            elif action_type == 'research':
                self._execute_research_action(ai_player, action)
            
            elif action_type == 'colonize':
                self._execute_colonize_action(ai_player, action)
            
            elif action_type == 'reallocate_workers':
                self._execute_reallocate_action(ai_player, action)
            
            elif action_type == 'cure_plague':
                self._execute_cure_plague_action(ai_player, action)
            
            elif action_type == 'develop_production':
                self._execute_develop_production_action(ai_player, action)
            
            elif action_type == 'raid':
                self._execute_raid_action(ai_player, action)
            
            elif action_type == 'buy_market':
                self._execute_buy_market_action(ai_player, action)
            
            elif action_type == 'complete_quest':
                self._execute_complete_quest_action(ai_player, action)
            
            else:
                print(f"⚠️ [{player_name}] Type d'action inconnu: {action_type}")
        
        except Exception as e:
            print(f"❌ [{player_name}] Erreur lors de l'exécution de {action_type}: {e}")
    
    def _execute_build_action(self, ai_player: Dict, action: Dict):
        """Exécute une action de construction"""
        from app.business.city_service import CityService
        from app.game_logic import GameLogic
        
        data = action.get('data', {})
        city_id = data.get('city_id')
        building_name = data.get('building_name')
        
        if not city_id or not building_name:
            print(f"    ⚠️ Données manquantes: city_id={city_id}, building={building_name}")
            return
        
        try:
            # Trouver un slot libre
            savegame = self.data_manager.load_savegame()
            city = next((c for c in savegame.get('cities', []) if c.get('id') == city_id), None)
            
            if not city:
                print(f"    ❌ Ville {city_id} introuvable")
                return
            
            # Trouver le premier slot libre (slot_1 à slot_20)
            buildings = city.get('buildings', [])
            used_slots = [b.get('slot_id') for b in buildings]
            free_slot = None
            
            for i in range(1, 21):
                slot = f"slot_{i}"
                if slot not in used_slots:
                    free_slot = slot
                    break
            
            if not free_slot:
                print(f"    ⚠️ Aucun slot libre dans {data.get('city_name', city_id)}")
                return
            
            # Créer les services nécessaires
            game_logic = GameLogic(self.data_manager)
            city_service = CityService(self.data_manager, game_logic)
            result = city_service.build_building(city_id, free_slot, building_name)
            
            if result and result.get('success'):
                print(f"    ✅ Construction lancée: {building_name} (slot {free_slot})")
            else:
                print(f"    ❌ Construction échouée: {result}")
        
        except Exception as e:
            error_msg = str(e)
            # Ne pas logger les erreurs attendues en détail
            if "Recherche requise" in error_msg or "Ressources insuffisantes" in error_msg:
                print(f"    ⚠️ {error_msg}")
            else:
                print(f"    ❌ Erreur: {error_msg}")
    
    def _execute_upgrade_action(self, ai_player: Dict, action: Dict):
        """Exécute une amélioration de bâtiment avec validation des règles de progression"""
        from app.business.city_service import CityService
        from app.game_logic import GameLogic
        from app.ai.utils.building_progression_rules import can_upgrade_building, get_progression_status
        
        data = action.get('data', {})
        city_id = data.get('city_id')
        building_name = data.get('building_name')
        
        if not city_id or not building_name:
            print(f"    ⚠️ Données manquantes: city_id={city_id}, building={building_name}")
            return
        
        try:
            # Trouver le bâtiment à améliorer
            savegame = self.data_manager.load_savegame()
            city = next((c for c in savegame.get('cities', []) if c.get('id') == city_id), None)
            
            if not city:
                print(f"    ❌ Ville {city_id} introuvable")
                return
            
            # Chercher le bâtiment du type demandé avec le niveau le plus bas
            buildings = city.get('buildings', [])
            matching_buildings = [b for b in buildings if b.get('name') == building_name and b.get('status') == 'Terminé']
            
            if not matching_buildings:
                print(f"    ⚠️ Aucun {building_name} terminé à améliorer")
                return
            
            # Prendre le bâtiment avec le niveau le plus bas
            building_to_upgrade = min(matching_buildings, key=lambda b: b.get('level', 1))
            slot_id = building_to_upgrade.get('slot_id')
            current_level = building_to_upgrade.get('level', 1)
            
            # 🎯 VÉRIFICATION DES RÈGLES DE PROGRESSION ÉQUILIBRÉE
            can_upgrade, progression_reason = can_upgrade_building(city, building_name, current_level)
            
            if not can_upgrade:
                print(f"    🚫 Upgrade bloqué par règles de progression: {progression_reason}")
                progression = get_progression_status(city)
                print(f"    📊 Distribution niveaux: {progression['level_distribution']}")
                return
            
            # Créer les services nécessaires
            game_logic = GameLogic(self.data_manager)
            city_service = CityService(self.data_manager, game_logic)
            result = city_service.upgrade_building(city_id, slot_id)
            
            if result:
                target_level = building_to_upgrade.get('level', 1) + 1
                print(f"    ✅ Amélioration lancée: {building_name} niveau {building_to_upgrade.get('level', 1)} → {target_level} (slot {slot_id})")
            else:
                print(f"    ❌ Amélioration échouée")
        
        except Exception as e:
            error_msg = str(e)
            if "Ressources insuffisantes" in error_msg:
                print(f"    ⚠️ {error_msg}")
            else:
                print(f"    ❌ Erreur: {error_msg}")
    
    def _execute_research_action(self, ai_player: Dict, action: Dict):
        """Exécute une action de recherche"""
        from ..business.research_service import ResearchService
        
        data = action.get('data', {})
        research_id = data.get('target')
        player_name = ai_player.get('username', 'Unknown')
        player_id = ai_player.get('id')
        
        if not research_id:
            print(f"    ⚠️ [{player_name}] Recherche: target manquant")
            return
        
        # Charger les données de recherche
        research_file = self.data_manager.load_research()
        research_list = research_file.get('researches', [])
        research_data = next((r for r in research_list if r.get('id') == research_id), None)
        
        if not research_data:
            print(f"    ⚠️ [{player_name}] Recherche introuvable: {research_id}")
            return
        
        research_name = research_data.get('name', research_id)
        cost = research_data.get('cost', {})
        
        # Afficher l'intention
        cost_str = ", ".join([f"{v} {k}" for k, v in cost.items()])
        print(f"🔬 [{player_name}] Recherche: {research_name} (coût: {cost_str})")
        
        # Exécuter la recherche via le service
        try:
            research_service = ResearchService(self.data_manager)
            result = research_service.unlock_research(player_id, research_id, research_data)
            
            if result.get('success'):
                print(f"    ✅ {research_name} débloquée!")
                if 'new_research_points' in result:
                    print(f"       Points de recherche restants: {result['new_research_points']}")
            else:
                reason = result.get('message', 'Erreur inconnue')
                if "insuffisant" in reason.lower():
                    print(f"    ⚠️ {reason}")
                else:
                    print(f"    ❌ {reason}")
        except Exception as e:
            error_msg = str(e)
            if "insuffisant" in error_msg.lower():
                print(f"    ⚠️ {error_msg}")
            else:
                print(f"    ❌ Erreur: {error_msg}")
    
    def _execute_colonize_action(self, ai_player: Dict, action: Dict):
        """Exécute une action de colonisation"""
        # TODO: Implémenter l'appel à l'API de colonisation
        data = action.get('data', {})
        player_name = ai_player.get('username', 'Unknown')
        
        print(f"🏝️ [{player_name}] Colonisation: île {data.get('island_name')} ({data.get('resource_type')})")
    
    def _execute_reallocate_action(self, ai_player: Dict, action: Dict):
        """Exécute une réaffectation de travailleurs"""
        data = action.get('data', {})
        city_id = data.get('city_id')
        
        # Supporter deux formats:
        # 1. Ancien: target_needs = ['cereal', 'wood']
        # 2. Nouveau: target = {resource_type: 'cereal', allocation_percent: 80}
        target_needs = data.get('target_needs', [])
        target = data.get('target', {})
        
        if not city_id:
            print(f"    ⚠️ city_id manquant pour réaffectation")
            return
        
        # Convertir nouveau format vers ancien format
        if target and not target_needs:
            resource_type = target.get('resource_type')
            if resource_type:
                target_needs = [resource_type]
        
        if not target_needs:
            print(f"    ⚠️ Aucune ressource cible pour réaffectation")
            return
        
        try:
            # Charger la ville et l'île
            savegame = self.data_manager.load_savegame()
            city = next((c for c in savegame.get('cities', []) if c.get('id') == city_id), None)
            
            if not city:
                print(f"    ❌ Ville {city_id} introuvable")
                return
            
            # Charger l'île pour connaître les sites disponibles
            universe = self.data_manager.load_universe()
            island_id = city.get('island_id')
            island = next((i for i in universe.get('islands', []) if i.get('id') == island_id), None)
            
            if not island:
                print(f"    ❌ Île {island_id} introuvable")
                return
            
            # Sites de ressources disponibles sur l'île
            resource_sites_dict = island.get('resource_sites', {})
            available_sites = set(resource_sites_dict.keys())
            
            # Charger la database pour connaître les capacités
            from data.resource_sites_database import RESOURCE_SITE_LEVELS, SITE_TO_RESOURCE
            
            # Charger les recherches du joueur
            players = self.data_manager.load_players()
            player = None
            if isinstance(players, list):
                player = next((p for p in players if p.get('id') == ai_player.get('id')), None)
            unlocked_research = player.get('unlocked_research', []) if player and isinstance(player, dict) else []
            
            # Vérifier population libre
            pop_free = city.get('resources', {}).get('population_free', 0)
            if pop_free <= 0:
                print(f"    ⚠️ Pas de population libre")
                return
            
            # Mapping ressource -> site de travail
            resource_to_site = {
                'wood': 'forest',
                'stone': 'quarry',
                'iron': 'iron_mine',
                'cereal': 'grain_field',
                'papyrus': 'papyrus_field',
                'marble': 'marble_quarry',
                'glass': 'glassworks',
                'meat': 'brewery',
                'horse': 'stable',
                'coal': 'coal_mine',
                'cotton': 'cotton_plantation',
                'spices': 'spice_farm'
            }
            
            # Ressources nécessitant des recherches spécifiques
            advanced_resources_tier1 = {'marble', 'meat', 'horse', 'glass'}  # ressources_avancees
            advanced_resources_tier2 = {'coal', 'gunpowder', 'spices', 'cotton'}  # ressources_industrielles
            
            # Affecter des workers aux ressources manquantes
            workers_assigned = city.get('workers_assigned', {})
            total_assigned = 0
            
            for resource_type in target_needs:
                if pop_free <= 0:
                    break
                
                site = resource_to_site.get(resource_type)
                if not site:
                    continue
                
                # Vérifier que le site existe sur l'île
                if site not in available_sites:
                    print(f"      ⚠️ Site {site} ({resource_type}) non disponible sur l'île")
                    continue
                
                # Vérifier les recherches pour les ressources avancées
                if resource_type in advanced_resources_tier1:
                    if 'ressources_avancees' not in unlocked_research:
                        print(f"      ⚠️ Ressource {resource_type} nécessite la recherche 'ressources_avancees'")
                        continue
                
                if resource_type in advanced_resources_tier2:
                    if 'ressources_industrielles' not in unlocked_research:
                        print(f"      ⚠️ Ressource {resource_type} nécessite la recherche 'ressources_industrielles'")
                        continue
                
                # Récupérer la capacité max du site selon son niveau
                site_info = resource_sites_dict.get(site, {})
                site_level = site_info.get('level', 1)
                site_data = RESOURCE_SITE_LEVELS.get(resource_type, {}).get(site_level, {})
                max_capacity = site_data.get('max_workers_per_city', 8)
                
                current_workers = workers_assigned.get(site, 0)
                
                # Ne pas dépasser la capacité max
                if current_workers >= max_capacity:
                    print(f"      ℹ️ {site} déjà plein ({current_workers}/{max_capacity})")
                    continue
                
                # Affecter jusqu'à la capacité max
                workers_to_add = min(pop_free, max_capacity - current_workers)
                workers_assigned[site] = current_workers + workers_to_add
                
                pop_free -= workers_to_add
                total_assigned += workers_to_add
                
                print(f"      → {workers_to_add} worker(s) à {site} (total: {workers_assigned[site]}/{max_capacity})")
            
            if total_assigned > 0:
                # Mettre à jour population libre
                city['resources']['population_free'] = pop_free
                
                # Sauvegarder
                self.data_manager.save_savegame(savegame)
                
                print(f"    ✅ {total_assigned} worker(s) réaffecté(s)")
            else:
                print(f"    ⚠️ Aucune réaffectation possible (sites non disponibles ou population insuffisante)")
        
        except Exception as e:
            print(f"    ❌ Erreur réaffectation: {e}")
    
    def _auto_assign_workers(self, ai_player: Dict):
        """
        Affecte automatiquement les ouvriers selon la stratégie de worker_allocation_strategy
        du build_order_config.json
        """
        try:
            savegame = self.data_manager.load_savegame()
            universe = self.data_manager.load_universe()
            player_name = ai_player.get('username', 'Unknown')
            
            # Charger la stratégie depuis le config
            config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'config',
                'build_order_config.json'
            )
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            strategy = config.get('worker_allocation_strategy', {})
            priority_order = strategy.get('priority_order', [])
            
            # Pour chaque ville de l'IA (filtrer par ID du joueur, pas username)
            player_id = ai_player.get('id', ai_player.get('username'))
            ai_cities = [c for c in savegame['cities'] if c['owner'] == player_id]
            
            if not ai_cities:
                print(f"    ⚠️ [{player_name}] Aucune ville trouvée (owner={player_id})")
                return
            
            for city in ai_cities:
                pop_free = city['resources'].get('population_free', 0)
                workers_assigned = city.get('workers_assigned', {})
                island_id = city.get('island_id')
                island = next((i for i in universe['islands'] if i['id'] == island_id), None)
                
                if not island:
                    continue
                
                # resource_sites est un dict {site_name: {level, donations}}
                resource_sites_dict = island.get('resource_sites', {})
                resource_sites = list(resource_sites_dict.keys())  # Convertir en liste de noms
                unlocked_research = ai_player.get('unlocked_research', [])
                
                # Charger la database des sites pour connaître les capacités
                from data.resource_sites_database import RESOURCE_SITE_LEVELS, SITE_TO_RESOURCE
                
                # 🔧 CORRECTION: Libérer les workers excédentaires (dépassement de capacité)
                workers_freed = 0
                sites_to_remove = []
                
                for site, assigned_workers in list(workers_assigned.items()):
                    if assigned_workers <= 0:
                        sites_to_remove.append(site)
                        continue
                    
                    # Vérifier la capacité du site
                    site_info = resource_sites_dict.get(site, {})
                    site_level = site_info.get('level', 1)
                    resource_type = SITE_TO_RESOURCE.get(site, 'unknown')
                    
                    if resource_type == 'unknown':
                        # Peut-être un bâtiment (academy, etc.)
                        continue
                    
                    site_data = RESOURCE_SITE_LEVELS.get(resource_type, {}).get(site_level, {})
                    max_capacity = site_data.get('max_workers_per_city', 8)
                    
                    if assigned_workers > max_capacity:
                        excess = assigned_workers - max_capacity
                        workers_assigned[site] = max_capacity
                        pop_free += excess
                        workers_freed += excess
                        print(f"    ⚠️ Libération de {excess} worker(s) excédentaires de {site} ({assigned_workers}/{max_capacity})")
                
                # Nettoyer les sites vides
                for site in sites_to_remove:
                    del workers_assigned[site]
                
                print(f"    📊 [{player_name}] {city['name']}: {pop_free} population libre")
                
                # Si aucune population libre, skip
                if pop_free == 0:
                    continue
                
                # Ressources avancées
                advanced_resources_tier1 = ['marble', 'horse', 'meat']
                advanced_resources_tier2 = ['glass', 'crystal', 'jewelry']
                
                initial_free = pop_free
                
                # Appliquer la stratégie selon priority_order
                for priority in priority_order:
                    if pop_free == 0:
                        break
                    
                    rank = priority.get('rank')
                    target = priority.get('target')
                    allocation_rule = priority.get('allocation_rule')
                    conditions = priority.get('conditions', {})
                    
                    # Rank 1: wood_production
                    if target == 'wood_production':
                        forest_sites = [s for s in resource_sites if s.startswith('forest')]
                        for site in forest_sites:
                            if pop_free == 0:
                                break
                            
                            # Récupérer la capacité réelle selon le niveau du site
                            site_info = resource_sites_dict.get(site, {})
                            site_level = site_info.get('level', 1)
                            resource_type = SITE_TO_RESOURCE.get(site, 'wood')
                            
                            # Capacité max selon niveau du site
                            site_data = RESOURCE_SITE_LEVELS.get(resource_type, {}).get(site_level, {})
                            max_capacity = site_data.get('max_workers_per_city', 8)
                            
                            current_workers = workers_assigned.get(site, 0)
                            
                            if current_workers < max_capacity:
                                to_add = min(pop_free, max_capacity - current_workers)
                                workers_assigned[site] = current_workers + to_add
                                pop_free -= to_add
                                if to_add > 0:
                                    print(f"      🌲 +{to_add} worker(s) à {site} (total: {workers_assigned[site]}/{max_capacity})")
                    
                    # Rank 2: island_base_resource (stone, iron, cereal, papyrus)
                    elif target == 'island_base_resource':
                        base_resources = ['stone', 'iron', 'grain', 'papyrus']
                        for res in base_resources:
                            if pop_free == 0:
                                break
                            
                            matching_sites = [s for s in resource_sites if s.startswith(f'{res}_') or s == f'{res}_field' or s == 'grain_field']
                            for site in matching_sites:
                                if pop_free == 0:
                                    break
                                
                                # Récupérer la capacité réelle selon le niveau du site
                                site_info = resource_sites_dict.get(site, {})
                                site_level = site_info.get('level', 1)
                                resource_type = SITE_TO_RESOURCE.get(site, res)
                                
                                # Capacité max selon niveau du site
                                site_data = RESOURCE_SITE_LEVELS.get(resource_type, {}).get(site_level, {})
                                max_capacity = site_data.get('max_workers_per_city', 8)
                                
                                current_workers = workers_assigned.get(site, 0)
                                
                                if current_workers < max_capacity:
                                    to_add = min(pop_free, max_capacity - current_workers)
                                    workers_assigned[site] = current_workers + to_add
                                    pop_free -= to_add
                                    if to_add > 0:
                                        print(f"      🌾 +{to_add} worker(s) à {site} (total: {workers_assigned[site]}/{max_capacity})")
                    
                    # Rank 3: advanced_resources
                    elif target == 'advanced_resources':
                        # Vérifier condition "unlocked"
                        if conditions.get('unlocked', True):
                            # Tier 1: ressources_avancees
                            if 'ressources_avancees' in unlocked_research:
                                for res in advanced_resources_tier1:
                                    if pop_free == 0:
                                        break
                                    
                                    matching_sites = [s for s in resource_sites if s.startswith(f'{res}_')]
                                    for site in matching_sites:
                                        if pop_free == 0:
                                            break
                                        
                                        # Récupérer la capacité réelle selon le niveau du site
                                        site_info = resource_sites_dict.get(site, {})
                                        site_level = site_info.get('level', 1)
                                        resource_type = SITE_TO_RESOURCE.get(site, res)
                                        
                                        site_data = RESOURCE_SITE_LEVELS.get(resource_type, {}).get(site_level, {})
                                        max_capacity = site_data.get('max_workers_per_city', 6)
                                        
                                        current_workers = workers_assigned.get(site, 0)
                                        
                                        if current_workers < max_capacity:
                                            to_add = min(pop_free, max_capacity - current_workers)
                                            workers_assigned[site] = current_workers + to_add
                                            pop_free -= to_add
                                            if to_add > 0:
                                                print(f"      💎 +{to_add} worker(s) à {site} (total: {workers_assigned[site]}/{max_capacity})")
                            
                            # Tier 2: ressources_industrielles
                            if 'ressources_industrielles' in unlocked_research:
                                for res in advanced_resources_tier2:
                                    if pop_free == 0:
                                        break
                                    
                                    matching_sites = [s for s in resource_sites if s.startswith(f'{res}_')]
                                    for site in matching_sites:
                                        if pop_free == 0:
                                            break
                                        
                                        site_info = resource_sites_dict.get(site, {})
                                        site_level = site_info.get('level', 1)
                                        resource_type = SITE_TO_RESOURCE.get(site, res)
                                        
                                        site_data = RESOURCE_SITE_LEVELS.get(resource_type, {}).get(site_level, {})
                                        max_capacity = site_data.get('max_workers_per_city', 4)
                                        
                                        current_workers = workers_assigned.get(site, 0)
                                        
                                        if current_workers < max_capacity:
                                            to_add = min(pop_free, max_capacity - current_workers)
                                            workers_assigned[site] = current_workers + to_add
                                            pop_free -= to_add
                                            if to_add > 0:
                                                print(f"      ⚙️ +{to_add} worker(s) à {site} (total: {workers_assigned[site]}/{max_capacity})")
                    
                    # Rank 4: Academy (toujours affecter si elle existe)
                    elif target == 'Academy':
                        # Vérifier conditions
                        academy_building = next((b for b in city.get('buildings', []) if b['name'] == 'Academy'), None)
                        
                        if academy_building:
                            # Charger la config des bâtiments pour connaître la capacité de l'Academy
                            buildings_data = self.data_manager.load_buildings()
                            academy_config = buildings_data.get('Academy', {})
                            academy_level = academy_building.get('level', 1)
                            levels = academy_config.get('levels', [])
                            
                            # Capacité selon niveau (par défaut 20 si pas trouvé)
                            if academy_level <= len(levels):
                                level_data = levels[academy_level - 1]
                                # Chercher "research_capacity" dans effect
                                max_capacity = level_data.get('effect', {}).get('research_capacity', 20)
                            else:
                                max_capacity = 20
                            
                            # Utiliser "academy" comme clé (convention du jeu)
                            academy_key = "academy"
                            current_workers = workers_assigned.get(academy_key, 0)
                            min_workers = 5  # Minimum pour lancer les recherches
                            
                            # Affecter au moins 5 workers si on a assez de population
                            if current_workers < min_workers and pop_free >= (min_workers - current_workers):
                                to_add = min_workers - current_workers
                                workers_assigned[academy_key] = current_workers + to_add
                                pop_free -= to_add
                                print(f"      🎓 +{to_add} worker(s) à Academy (total: {workers_assigned[academy_key]}/{max_capacity})")
                            elif current_workers < max_capacity and pop_free > 0:
                                # Ajouter plus si on a de la population libre
                                to_add = min(pop_free, max_capacity - current_workers)
                                workers_assigned[academy_key] = current_workers + to_add
                                pop_free -= to_add
                                if to_add > 0:
                                    print(f"      🎓 +{to_add} worker(s) à Academy (total: {workers_assigned[academy_key]}/{max_capacity})")
                    
                    # Rank 5: idle_for_gold
                    # Population libre génère de l'or automatiquement, pas d'action nécessaire
                
                # Mettre à jour si des workers ont été affectés
                if pop_free < initial_free:
                    city['resources']['population_free'] = pop_free
                    assigned_count = initial_free - pop_free
                    # Log seulement si des workers ont été réaffectés
                    if assigned_count > 0:
                        print(f"    🔧 [{player_name}] {city['name']}: {assigned_count} worker(s) réaffectés")
            
            # Sauvegarder
            self.data_manager.save_savegame(savegame)
        
        except Exception as e:
            print(f"    ⚠️ Erreur auto-affectation workers: {e}")
    
    def _execute_cure_plague_action(self, ai_player: Dict, action: Dict):
        """Exécute une cure de peste"""
        data = action.get('data', {})
        player_name = ai_player.get('username', 'Unknown')
        
        print(f"💊 [{player_name}] Cure de peste dans {data.get('city_name')}")
    
    def _execute_develop_production_action(self, ai_player: Dict, action: Dict):
        """Exécute développement production (construction bâtiment de ressource)"""
        data = action.get('data', {})
        
        # Déléguer à l'action de construction
        self._execute_build_action(ai_player, action)
    
    def _execute_raid_action(self, ai_player: Dict, action: Dict):
        """Exécute une attaque de pillage"""
        data = action.get('data', {})
        player_name = ai_player.get('username', 'Unknown')
        
        print(f"⚔️ [{player_name}] Raid: {data.get('target_type')} ({data.get('target_id')})")
    
    def _execute_buy_market_action(self, ai_player: Dict, action: Dict):
        """Exécute achat au marché"""
        data = action.get('data', {})
        player_name = ai_player.get('username', 'Unknown')
        
        print(f"🛒 [{player_name}] Achat marché: {data.get('quantity')} {data.get('resource')}")
    
    def _execute_complete_quest_action(self, ai_player: Dict, action: Dict):
        """Exécute complétion de quête"""
        data = action.get('data', {})
        player_name = ai_player.get('username', 'Unknown')
        
        print(f"📜 [{player_name}] Quête: {data.get('quest_name')}")
    
    def get_all_ai_players(self) -> List[Dict]:
        """
        Récupère tous les joueurs IA avec infos enrichies
        
        Returns:
            Liste des joueurs IA avec personnalité, difficulté, villes, statut
        """
        players_data = self.data_manager.load_players()
        savegame = self.data_manager.load_savegame()
        cities = savegame.get('cities', [])
        
        ai_players = []
        for p in players_data.get('players', []):
            if p.get('is_ai', False):
                # Compter les villes
                player_cities = [c for c in cities if c.get('player_id') == p.get('id')]
                
                # Vérifier statut en ligne
                activity_sim = get_activity_simulator(p.get('id'), self.config['activity_simulation'])
                is_online = activity_sim.is_online()
                
                # Enrichir les données
                ai_player = p.copy()
                ai_player['city_count'] = len(player_cities)
                ai_player['is_online'] = is_online
                ai_player['personality'] = p.get('ai_personality', 'unknown')
                ai_player['difficulty'] = p.get('ai_difficulty', 'unknown')
                
                ai_players.append(ai_player)
        
        return ai_players
    
    def create_ai_player(self, personality: str = None, difficulty: str = None, 
                        starting_island_type: str = None, island_id: str = None) -> Dict:
        """
        Crée un nouveau joueur IA
        
        RÈGLE : Maximum 1 IA par île avec joueur(s) humain(s) (ville de départ)
        
        Args:
            personality: Type de personnalité ("economic", "military", "balanced")
            difficulty: Niveau de difficulté ("easy", "medium", "hard")
            starting_island_type: Type d'île de départ (optionnel)
            island_id: ID de l'île cible (optionnel, pour validation manuelle)
        
        Returns:
            Données du joueur IA créé
            
        Raises:
            ValueError: Si la création manuelle viole les règles (aucun humain OU déjà 1 IA)
        """
        # VALIDATION : Vérifier les règles de spawn si island_id fourni (création manuelle)
        if island_id:
            starting_islands = self._get_human_starting_islands()
            
            if island_id not in starting_islands:
                raise ValueError(f"❌ Impossible de créer IA sur île '{island_id}': Aucun joueur humain avec ville de départ sur cette île")
            
            # Charger l'île et compter les IA
            universe = self.data_manager.load_universe()
            island = next((i for i in universe.get('islands', []) if i.get('id') == island_id), None)
            if island:
                ai_count = self._count_ai_on_island(island)
                if ai_count >= 1:
                    raise ValueError(f"❌ Impossible de créer IA sur île '{island_id}': {ai_count} IA(s) déjà présente(s) (maximum 1 IA par île)")
        
        # Valeurs par défaut
        if personality is None:
            personality = random.choice(['economic', 'military', 'balanced'])
        
        if difficulty is None:
            difficulty = random.choice(['easy', 'medium', 'hard'])
        
        # Générer un nom
        username = self._generate_ai_name()
        
        # Créer le joueur
        players_data = self.data_manager.load_players()
        
        # Trouver le prochain ID
        existing_ids = [p.get('id', '') for p in players_data.get('players', [])]
        ai_numbers = [int(pid.replace('ai_', '')) for pid in existing_ids if pid.startswith('ai_')]
        next_number = max(ai_numbers) + 1 if ai_numbers else 1
        
        player_id = f"ai_{str(next_number).zfill(3)}"
        
        new_ai = {
            'id': player_id,
            'username': username,
            'is_ai': True,
            'ai_personality': personality,  # Champ spécifique IA
            'ai_difficulty': difficulty,     # Champ spécifique IA
            # Champs identiques aux joueurs normaux
            'research_points': 0,
            'unlocked_research': [],
            'research_effects': {
                'unlocked_buildings': [],
                'resource_bonuses': {}
            },
            'gold': 10000,
            'diamonds': 10,
            'transport_ships_total': 1,
            'transport_ships_busy': 0,
            'total_units_killed': 0,
            'total_units_lost': 0,
            'total_xp_gained': 0,
            'battles_fought': 0,
            'victories': 0,
            'defeats': 0,
            'victories_barbarians': 0,
            'created_at': datetime.now().isoformat()
        }
        
        players_data['players'].append(new_ai)
        self.data_manager.save_players(players_data)
        
        return new_ai
    
    def _generate_ai_name(self) -> str:
        """
        Génère un nom aléatoire pour une IA
        
        Returns:
            Nom de l'IA
        """
        prefixes = self.config['ai_names']['prefixes']
        suffixes = self.config['ai_names']['suffixes']
        
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        number = random.randint(1, 999)
        
        return f"{prefix}_{suffix}_{number}"
    
    def delete_ai_player(self, player_id: str) -> bool:
        """
        Supprime un joueur IA et TOUTES ses données associées
        
        Nettoie :
        - Joueur dans players.json
        - Villes dans savegame.json
        - Héros dans player_heroes.json
        - Transports dans transports.json et transport_history.json
        - Offres marché dans market.json
        - Notifications dans notifications.json
        - Rapports de bataille dans battle_reports.json
        - Batailles actives dans battlesv2.json
        
        Args:
            player_id: ID du joueur à supprimer
        
        Returns:
            True si supprimé avec succès
        """
        print(f"🗑️ Suppression de l'IA '{player_id}' et de toutes ses données...")
        
        players_data = self.data_manager.load_players()
        
        # 1. Trouver et supprimer le joueur
        players = players_data.get('players', [])
        initial_count = len(players)
        
        players_data['players'] = [p for p in players if p.get('id') != player_id]
        
        if len(players_data['players']) >= initial_count:
            print(f"⚠️ Joueur '{player_id}' introuvable")
            return False
        
        # 2. Supprimer les villes dans savegame.json
        savegame = self.data_manager.load_savegame()
        cities_before = len(savegame.get('cities', []))
        savegame['cities'] = [c for c in savegame.get('cities', []) 
                              if c.get('owner') != player_id and c.get('player_id') != player_id]
        cities_deleted = cities_before - len(savegame.get('cities', []))
        print(f"  ✓ {cities_deleted} ville(s) supprimée(s)")
        
        # 3. Supprimer les héros dans player_heroes.json
        try:
            import os
            filepath = os.path.join(self.data_manager.gamedata_dir, 'player_heroes.json')
            player_heroes = self.data_manager._load_json_file(filepath)
            if player_heroes:
                heroes_before = len(player_heroes.get('player_heroes', []))
                player_heroes['player_heroes'] = [h for h in player_heroes.get('player_heroes', [])
                                                  if h.get('player_id') != player_id]
                heroes_deleted = heroes_before - len(player_heroes.get('player_heroes', []))
                self.data_manager._save_json_file(filepath, player_heroes, create_backup=False, force_save=True)
                print(f"  ✓ {heroes_deleted} héro(s) supprimé(s)")
        except Exception as e:
            print(f"  ⚠️ Erreur suppression héros: {e}")
        
        # 4. Supprimer les transports dans transports.json
        try:
            transports = self.data_manager.load_transports()
            transports_before = len(transports.get('transports', []))
            transports['transports'] = [t for t in transports.get('transports', [])
                                        if t.get('player_id') != player_id]
            transports_deleted = transports_before - len(transports.get('transports', []))
            self.data_manager.save_transports(transports, force_save=True)
            print(f"  ✓ {transports_deleted} transport(s) supprimé(s)")
        except Exception as e:
            print(f"  ⚠️ Erreur suppression transports: {e}")
        
        # 5. Supprimer l'historique des transports dans transport_history.json
        try:
            transport_history = self.data_manager.load_transport_history()
            history_before = len(transport_history.get('transport_history', []))
            transport_history['transport_history'] = [h for h in transport_history.get('transport_history', [])
                                                      if h.get('player_id') != player_id]
            history_deleted = history_before - len(transport_history.get('transport_history', []))
            self.data_manager.save_transport_history(transport_history, force_save=True)
            print(f"  ✓ {history_deleted} historique(s) transport supprimé(s)")
        except Exception as e:
            print(f"  ⚠️ Erreur suppression historique transports: {e}")
        
        # 6. Supprimer les offres marché dans market.json
        try:
            market = self.data_manager.load_market()
            offers_before = len(market.get('market_offers', []))
            market['market_offers'] = [o for o in market.get('market_offers', [])
                                       if o.get('player_id') != player_id]
            offers_deleted = offers_before - len(market.get('market_offers', []))
            self.data_manager.save_market(market, force_save=True)
            print(f"  ✓ {offers_deleted} offre(s) marché supprimée(s)")
        except Exception as e:
            print(f"  ⚠️ Erreur suppression offres marché: {e}")
        
        # 7. Supprimer les notifications dans notifications.json
        try:
            notifications = self.data_manager.load_notifications()
            notifs_before = len(notifications.get('notifications', []))
            notifications['notifications'] = [n for n in notifications.get('notifications', [])
                                              if n.get('player_id') != player_id]
            notifs_deleted = notifs_before - len(notifications.get('notifications', []))
            self.data_manager.save_notifications(notifications)
            print(f"  ✓ {notifs_deleted} notification(s) supprimée(s)")
        except Exception as e:
            print(f"  ⚠️ Erreur suppression notifications: {e}")
        
        # 8. Supprimer les rapports de bataille dans battle_reports.json
        try:
            import os
            filepath = os.path.join(self.data_manager.gamedata_dir, 'battle_reports.json')
            battle_reports = self.data_manager._load_json_file(filepath)
            if battle_reports:
                reports_before = len(battle_reports.get('battle_reports', []))
                battle_reports['battle_reports'] = [r for r in battle_reports.get('battle_reports', [])
                                                    if r.get('attacker_player_id') != player_id 
                                                    and r.get('defender_player_id') != player_id]
                reports_deleted = reports_before - len(battle_reports.get('battle_reports', []))
                self.data_manager._save_json_file(filepath, battle_reports, create_backup=False, force_save=True)
                print(f"  ✓ {reports_deleted} rapport(s) bataille supprimé(s)")
        except Exception as e:
            print(f"  ⚠️ Erreur suppression rapports bataille: {e}")
        
        # 9. Supprimer les batailles actives dans battlesv2.json
        try:
            import os
            filepath = os.path.join(self.data_manager.gamedata_dir, 'battlesv2.json')
            battles = self.data_manager._load_json_file(filepath)
            if battles:
                battles_before = len(battles.get('battles', []))
                battles['battles'] = [b for b in battles.get('battles', [])
                                      if b.get('attacker_player_id') != player_id 
                                      and b.get('defender_player_id') != player_id]
                battles_deleted = battles_before - len(battles.get('battles', []))
                self.data_manager._save_json_file(filepath, battles, create_backup=False, force_save=True)
                print(f"  ✓ {battles_deleted} bataille(s) active(s) supprimée(s)")
        except Exception as e:
            print(f"  ⚠️ Erreur suppression batailles: {e}")
        
        # Sauvegarder les modifications
        self.data_manager.save_players(players_data)
        self.data_manager.save_savegame(savegame)
        
        # Supprimer de la cache
        if player_id in self._ai_instances:
            del self._ai_instances[player_id]
            
            print(f"✅ Joueur IA {player_id} supprimé")
            return True
        
        return False
    
    def get_ai_stats(self) -> Dict:
        """
        Récupère les statistiques globales des IAs
        
        Returns:
            Dictionnaire avec les stats
        """
        ai_players = self.get_all_ai_players()
        
        return {
            'total_ais': len(ai_players),
            'by_personality': self._count_by_field(ai_players, 'ai_personality'),
            'by_difficulty': self._count_by_field(ai_players, 'ai_difficulty'),
            'active_now': sum(1 for ai in ai_players if ai.get('is_online', False))
        }
    
    def _count_by_field(self, players: List[Dict], field: str) -> Dict[str, int]:
        """Compte les joueurs par champ"""
        counts = {}
        for player in players:
            value = player.get(field, 'unknown')
            counts[value] = counts.get(value, 0) + 1
        return counts
    
    def _is_ai_online(self, ai_player: Dict) -> bool:
        """Vérifie si une IA est en ligne"""
        player_id = ai_player.get('id')
        activity_simulator = get_activity_simulator(
            player_id, 
            self.config['activity_simulation']
        )
        return activity_simulator.is_online()
    
    def spawn_missing_ais(self) -> List[Dict]:
        """
        Crée 1 IA par île où un joueur HUMAIN a sa ville de DÉPART (maximum 1 IA par île).
        
        Règles :
        - Dès qu'un joueur a sa ville de départ sur une île → créer 1 IA
        - Si 2ème joueur arrive sur même île → ne PAS créer 2ème IA (max 1)
        - Si joueur colonise autre île → 0 IA sur colonie (seulement ville départ)
        
        Exemples :
        - T1: Player1 sur île A → spawn 1 IA sur île A
        - T2: Player2 sur île A → 0 nouvelle IA (déjà 1 IA)
        - T3: Player1 colonise île B → 0 IA sur île B (colonie)
        
        Returns:
            Liste des joueurs IA créés
        """
        spawned_players = []
        
        try:
            # Trouver les îles où les joueurs HUMAINS ont leur PREMIÈRE ville (ville de départ)
            starting_islands = self._get_human_starting_islands()
            
            if not starting_islands:
                print("ℹ️ Aucun joueur humain trouvé → Pas de spawn IA")
                return spawned_players
            
            print(f"🔍 Vérification spawn IA sur {len(starting_islands)} île(s) avec joueur(s) humain(s)")
            
            # Charger l'univers une seule fois
            universe = self.data_manager.load_universe()
            islands = universe.get('islands', [])
            
            # Pour chaque île avec ville de départ
            for island_id, human_count in starting_islands.items():
                island = next((i for i in islands if i.get('id') == island_id), None)
                
                if not island:
                    continue
                
                island_name = island.get('name', 'Unknown')
                ai_count = self._count_ai_on_island(island)
                
                # Règle : 1 IA maximum par île avec joueur(s) humain(s)
                if ai_count == 0:
                    print(f"📍 Île '{island_name}': {human_count} humain(s), 0 IA → Création IA...")
                    
                    if self._has_free_city_slot(island):
                        ai_player = self._spawn_ai_on_island(island)
                        if ai_player:
                            spawned_players.append(ai_player)
                            print(f"✅ IA '{ai_player['username']}' créée sur '{island_name}'")
                    else:
                        print(f"⚠️ Aucune ville libre sur '{island_name}'")
                else:
                    print(f"✓ Île '{island_name}': {human_count} humain(s), {ai_count} IA → OK")
        
        except Exception as e:
            print(f"❌ Erreur spawn IA: {e}")
        
        if spawned_players:
            print(f"🎯 {len(spawned_players)} IA(s) créée(s)")
        
        return spawned_players
    
    def _get_human_starting_islands(self) -> Dict[str, int]:
        """
        Trouve les îles où les joueurs HUMAINS ont leur PREMIÈRE ville (ville de départ).
        
        Returns:
            Dict {island_id: nombre_joueurs_humains_avec_ville_depart}
        """
        savegame = self.data_manager.load_savegame()
        players_data = self.data_manager.load_players()
        cities = savegame.get('cities', [])
        players = players_data.get('players', [])
        
        # Filtrer les joueurs HUMAINS uniquement
        human_players = [p for p in players if not p.get('is_ai', False)]
        
        starting_islands = {}
        
        for player in human_players:
            player_id = player.get('id')
            
            # Trouver TOUTES les villes du joueur
            player_cities = [c for c in cities if c.get('owner') == player_id]
            
            if len(player_cities) == 0:
                continue
            
            # La ville de DÉPART = celle avec le nom contenant "Capital" OU la première ville (ordre création)
            starting_city = None
            for city in player_cities:
                if 'Capital' in city.get('name', '') or 'capital' in city.get('name', ''):
                    starting_city = city
                    break
            
            # Si pas de "Capital" trouvé, prendre la première ville
            if not starting_city and player_cities:
                starting_city = player_cities[0]
            
            if starting_city:
                island_id = starting_city.get('island_id')
                if island_id:
                    starting_islands[island_id] = starting_islands.get(island_id, 0) + 1
        
        return starting_islands
    
    def _count_ai_on_island(self, island: Dict) -> int:
        """
        Compte le nombre d'IA sur une île
        
        Returns:
            Nombre d'IA
        """
        count = 0
        elements = island.get('elements', [])
        
        # Charger les données
        savegame = self.data_manager.load_savegame()
        players_data = self.data_manager.load_players()
        cities = savegame.get('cities', [])
        players = players_data.get('players', [])
        
        for element in elements:
            if element.get('type') == 'city':
                city_id = element.get('id')
                
                # Trouver la ville
                city = next((c for c in cities if c.get('id') == city_id), None)
                
                if city:
                    player_id = city.get('owner') or city.get('player_id')  # Support ancien format
                    # Trouver le joueur
                    player = next((p for p in players if p.get('id') == player_id), None)
                    
                    if player and player.get('is_ai', False):
                        count += 1
        
        return count
    
    def _has_free_city_slot(self, island: Dict) -> bool:
        """
        Vérifie s'il reste des villes LIBRES (non occupées) sur l'île
        
        Returns:
            True si au moins une ville libre disponible
        """
        # Charger les villes occupées
        savegame = self.data_manager.load_savegame()
        occupied_cities = savegame.get('cities', [])
        occupied_city_ids = [c.get('id') for c in occupied_cities]
        
        # Trouver les villes de l'île
        elements = island.get('elements', [])
        island_cities = [e for e in elements if e.get('type') == 'city' and e.get('controlable', True)]
        
        # Compter les villes libres
        free_cities = [c for c in island_cities if c.get('id') not in occupied_city_ids]
        
        return len(free_cities) > 0
    
    def _spawn_ai_on_island(self, island: Dict) -> Optional[Dict]:
        """
        Crée une IA sur une île spécifique
        
        Returns:
            Joueur IA créé ou None
        """
        try:
            # Choisir personnalité aléatoire
            personalities = ['economic', 'military', 'balanced']
            personality = random.choice(personalities)
            
            # Créer le joueur (sans validation car spawn automatique)
            ai_player = self.create_ai_player(personality=personality, difficulty='medium')
            
            # Créer sa première ville sur cette île
            self._create_starting_city(ai_player, island)
            
            return ai_player
            
        except Exception as e:
            print(f"❌ Erreur création IA sur île {island.get('name')}: {e}")
            return None
    
    def _create_starting_city(self, ai_player: Dict, island: Dict):
        """
        Assigne une ville LIBRE existante à l'IA
        (Ne crée pas de nouvelle ville, prend une ville vide de universe.json)
        
        Args:
            ai_player: Joueur IA
            island: Île cible
        """
        # Charger les villes occupées
        savegame = self.data_manager.load_savegame()
        occupied_cities = savegame.get('cities', [])
        occupied_city_ids = [c.get('id') for c in occupied_cities]
        
        # Trouver les villes libres de l'île
        elements = island.get('elements', [])
        island_cities = [e for e in elements if e.get('type') == 'city' and e.get('controlable', True)]
        free_cities = [c for c in island_cities if c.get('id') not in occupied_city_ids]
        
        if not free_cities:
            print(f"⚠️ Aucune ville libre sur l'île {island.get('name')}")
            return
        
        # Prendre la première ville libre
        city_element = free_cities[0]
        city_id = city_element.get('id')
        
        # Créer les données de la ville pour le savegame (STRUCTURE IDENTIQUE aux villes joueur)
        city = {
            'id': city_id,
            'owner': ai_player['id'],  # Champ standard des villes joueur
            'name': f"{ai_player['username']}'s Capital",
            'island_id': island.get('id'),  # ID de l'île
            'city_layout': city_element.get('layout', 'city_type_1'),  # Layout depuis universe.json
            'base_resource': island.get('base_resource', 'stone'),  # Ressource de l'île
            'resources': {
                'wood': 1500, 'stone': 3000, 'iron': 1000, 'cereal': 2000, 'papyrus': 1000,
                'horse': 10, 'marble': 20, 'glass': 30, 'meat': 40, 'coal': 50,
                'gunpowder': 60, 'spices': 70, 'cotton': 80,
                'population_total': 40,
                'population_free': 40,
                'production_bonus': {},
                'building_bonus': {},
                'population_fractional': 0.0,
                'cereal_needed': 0.0,
                'population_unfed': 0,
                'pop_nourished_by_townhall': 0,
                'pop_nourished_by_windmill': 0,
                'total_food_supply': 0
            },
            'storage_capacity': {},
            'buildings': [
                {
                    'slot_id': 'slot_5',
                    'name': 'Hôtel de Ville',
                    'level': 1,
                    'status': 'Terminé',
                    'effect': {
                        'population_capacity': 40,
                        'food_capacity': 40
                    }
                }
            ],
            'workers_assigned': {},  # Nom standard (pas 'workers')
            'satisfaction': 50,  # Satisfaction de base standard
            'unlocked_buildings': [],
            'controlable': True,
            'gold_rate': 1,
            'windmill_cereal_multiplier': 1,
            'has_plague': False,
            'hygiene_percent': 100,
            'satisfaction_details': {
                'base': 50,
                'bonus': {'thermes': 0, 'impot': 0, 'hygiene': 0},
                'malus': {'population': 0, 'plague': 0},
                'total': 50,
                'growth_rate': 0.0,
                'food_capacities': {'townhall': 0, 'windmill': 0, 'total': 0},
                'population_food_status': {'total': 40, 'fed_by_townhall': 0, 'fed_by_windmill': 0, 'starving': 40},
                'cereal_consumption': {'multiplier': 1, 'max_multiplier': 1, 'total_needed': 0.0, 'base_rate': 0.1}
            }
        }
        
        # Ajouter ville au savegame (pas besoin de modifier universe, la ville existe déjà)
        if 'cities' not in savegame:
            savegame['cities'] = []
        savegame['cities'].append(city)
        
        self.data_manager.save_savegame(savegame)
        
        print(f"✅ Created starting city {city_id} for {ai_player['username']} on island {island.get('name')}")
    
    def _ensure_academy_workers(self, ai_player: Dict):
        """
        Vérifie que l'Academy a des workers si elle existe.
        Si aucun worker n'est affecté aux ressources, force une allocation complète.
        """
        savegame = self.data_manager.load_savegame()
        player_id = ai_player.get('id')
        
        # Trouver les villes de l'AI
        ai_cities = [c for c in savegame.get('cities', []) if c.get('owner') == player_id]
        
        for city in ai_cities:
            buildings = city.get('buildings', [])
            workers_assigned = city.get('workers_assigned', {})
            pop_free = city.get('resources', {}).get('population_free', 0)
            
            # Chercher l'Academy
            has_academy = any(b.get('name') == 'Academy' and b.get('status') == 'Terminé' for b in buildings)
            
            # Vérifier si workers affectés aux ressources (forest, grain_field, etc.)
            resource_workers = sum(v for k, v in workers_assigned.items() if k != 'academy')
            
            # Si Academy existe ET (aucun worker ressource OU population libre > 50) → allocation complète
            if has_academy and (resource_workers == 0 or pop_free > 50):
                if pop_free >= 10:  # Au moins 10 pop libre pour allouer
                    print(f"      🔄 Réaffectation workers pour {city.get('name')} (pop libre: {pop_free})")
                    # Forcer une allocation complète via _auto_assign_workers
                    self._auto_assign_workers(ai_player)
                    return  # Une seule fois suffit
