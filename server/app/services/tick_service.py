"""
TickService UNIFIÉ V4 - Service de tick complet
Centralise TOUTE la logique de tick : manuel ET automatique
Service unique pour tous les modes de tick
FOCUS: Production (or, recherche, ressources) + Auto-tick précis
"""

import logging
import threading
import time
import json
import os
from typing import Dict, Any

class TickService:
    """Service de tick unifié - Manuel ET Auto"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.logger = logging.getLogger(__name__)
        
        # === INTÉGRATION POPULATION MANAGER ===
        from app.managers.population_manager import PopulationManager
        # PopulationManager attend le répertoire 'data'
        data_dir = os.path.join(data_manager.base_dir, 'data')
        self.population_manager = PopulationManager(data_dir)
        
        # === AUTO-TICK INTÉGRÉ ===
        self.auto_tick_running = False
        self.auto_tick_thread = None
        self.auto_tick_interval = 10.0
        self.auto_tick_enabled = False
        self._load_auto_tick_settings()
        
        # Démarrer auto-tick si activé dans les paramètres
        if self.auto_tick_enabled:
            self.start_auto_tick()
    
    def _load_auto_tick_settings(self):
        """Charge les paramètres d'auto-tick depuis auto_tick_settings.json"""
        try:
            settings_file = os.path.join(self.data_manager.base_dir, 'data', 'auto_tick_settings.json')
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                self.auto_tick_interval = float(settings.get('interval_seconds', 10.0))
                self.auto_tick_enabled = bool(settings.get('enabled', True))
                
                pass  # Settings loaded silently
            else:
                self.auto_tick_interval = 10.0
                self.auto_tick_enabled = True
                
        except Exception as e:
            print(f"❌ [AUTO-TICK] Error loading settings: {e}")
            self.auto_tick_interval = 10.0
            self.auto_tick_enabled = True
    
    def execute_tick(self) -> Dict[str, Any]:
        """
        TICK MANUEL UNIFIÉ - Tout est calculé ici dans une seule méthode
        
        Pour chaque ville:
        1. Calculer production de chaque ressource (workers + bonus)
        2. Calculer consommation céréales population
        3. Appliquer les changements
        
        Pour chaque joueur:
        4. Calculer production d'or (population libre × gold_rate)
        5. Calculer points de recherche (workers académie)
        
        Returns:
            dict: Résumé complet des changements
        """
        results = {
            'cities_updated': 0,
            'players_updated': 0,
            'total_production': {},
            'errors': []
        }
        
        try:
            # === CHARGER LES DONNÉES UNE SEULE FOIS ===
            savegame_data = self.data_manager.load_savegame()
            players_data = self.data_manager.load_players()
            
            if not savegame_data or not players_data:
                results['errors'].append("Données manquantes")
                return results
            
            cities = savegame_data.get('cities', [])
            players = players_data.get('players', [])
            
            # === CRÉER UN MAPPING player_id -> username ===
            player_id_to_username = {}
            for player in players:
                player_id = player.get('id')
                username = player.get('username')
                if player_id and username:
                    player_id_to_username[player_id] = username
            
            # === TRAITEMENT PAR VILLE ===
            # Accumuler la production par joueur pour les quêtes
            player_production_totals = {}  # {username: {resource: amount}}
            
            for city in cities:
                try:
                    city_results = self._process_city_tick(city)
                    results['cities_updated'] += 1
                    
                    # Accumuler les totaux globaux
                    for resource, amount in city_results.items():
                        results['total_production'][resource] = results['total_production'].get(resource, 0) + amount
                    
                    # Accumuler par joueur pour les quêtes (convertir player_id en username)
                    owner_id = city.get('owner')
                    if owner_id and owner_id in player_id_to_username:
                        username = player_id_to_username[owner_id]
                        if username not in player_production_totals:
                            player_production_totals[username] = {}
                        for resource, amount in city_results.items():
                            player_production_totals[username][resource] = player_production_totals[username].get(resource, 0) + amount
                        
                except Exception as e:
                    city_name = city.get('name', city.get('id', 'Inconnue'))
                    results['errors'].append(f"Erreur ville {city_name}: {e}")
            
            # === TRAITEMENT PAR JOUEUR ===
            for player in players:
                try:
                    player_results = self._process_player_tick(player, cities)
                    results['players_updated'] += 1
                    
                    # Accumuler les totaux (or, recherche)
                    for resource, amount in player_results.items():
                        results['total_production'][resource] = results['total_production'].get(resource, 0) + amount
                    
                    # Accumuler l'or pour les quêtes
                    player_id = player.get('id')
                    if player_id in player_id_to_username:
                        username = player_id_to_username[player_id]
                        if username not in player_production_totals:
                            player_production_totals[username] = {}
                        for resource, amount in player_results.items():
                            player_production_totals[username][resource] = player_production_totals[username].get(resource, 0) + amount
                    
                except Exception as e:
                    player_id = player.get('id', 'Inconnu')
                    results['errors'].append(f"Erreur joueur {player_id}: {e}")
            
            # === MISE À JOUR DES QUÊTES DE COLLECTE ===
            try:
                from app.services.quest_service import quest_service
                for username, resources_collected in player_production_totals.items():
                    quest_service.update_resource_collection_quests(username, resources_collected)
            except Exception as e:
                results['errors'].append(f"Erreur mise à jour quêtes: {e}")
            
            # === TRAITEMENT DES CONSTRUCTIONS ===
            # Vérifier et finaliser les constructions terminées
            try:
                from app.game_logic import GameLogic
                game_logic = GameLogic(self.data_manager)
                game_logic.update_construction_statuses_in_memory(savegame_data)
            except Exception as e:
                results['errors'].append(f"Erreur constructions: {e}")
            
            # === TRAITEMENT DES IA ===
            # Exécuter les cycles de décision des IA
            try:
                from app.ai.ai_controller import AIController
                ai_controller = AIController()
                ai_results = ai_controller.execute_all_ais()
                results['ai_executed'] = ai_results.get('executed_count', 0)
                results['ai_actions'] = ai_results.get('total_actions', 0)
            except Exception as e:
                results['errors'].append(f"Erreur IA: {e}")
            
            # === SAUVEGARDER UNE SEULE FOIS ===
            if results['cities_updated'] > 0:
                # Force la sauvegarde immédiate pour les auto-ticks
                force_save = self.auto_tick_running  # Force seulement si c'est un auto-tick
                self.data_manager.save_savegame(savegame_data, force_save=force_save)
            if results['players_updated'] > 0:
                force_save = self.auto_tick_running
                self.data_manager.save_players(players_data, force_save=force_save)
            
            self.logger.info(f"✅ Tick unifié: {results['cities_updated']} villes, {results['players_updated']} joueurs")
            return results
            
        except Exception as e:
            error_msg = f"Erreur tick unifié: {e}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)
            return results
    
    def _process_city_tick(self, city: Dict) -> Dict[str, float]:
        """
        Traite tous les calculs pour UNE ville en un seul endroit
        
        Returns:
            dict: Production par ressource pour cette ville
        """
        city_production = {}
        
        # === 0. MISE À JOUR DES BONUS BÂTIMENTS ===
        self._update_building_bonuses(city)
        
        # === 1. PRODUCTION RESSOURCES (wood, stone, cereal, etc.) ===
        workers_assigned = city.get('workers_assigned', {})
        resources = city.get('resources', {})
        
        # Mapping entre les clés workers et les ressources produites - COMPLET
        worker_to_resource = {
            'forest': 'wood',
            'quarry': 'stone', 
            'iron_mine': 'iron',
            'grain_field': 'cereal',
            'vineyard': 'wine',
            'marble_quarry': 'marble',
            'horse_farm': 'horse',
            'glass_works': 'glass',
            'coal_mine': 'coal',
            'gunpowder_mill': 'gunpowder',
            'spices_farm': 'spices', 
            'cotton_farm': 'cotton',
            'papyrus_field': 'papyrus',
            'academy': 'research',  # Géré séparément dans _process_player_tick
        }
        
        for worker_type, resource in worker_to_resource.items():
            # Workers sur ce type de production
            workers = workers_assigned.get(worker_type, 0)
            
            if workers > 0 and resource != 'research':  # research géré dans _process_player_tick
                # Production de ressources : 1 ouvrier = 1.44 ressources/heure (style Ikariam)
                # Avec 1 tick = 10 sec, il y a 360 ticks/heure
                # Donc : 1.44 / 360 = 0.004 ressources/tick par ouvrier
                RESOURCES_PER_WORKER_PER_HOUR = 1.44
                TICKS_PER_HOUR = 360
                base_production = workers * (RESOURCES_PER_WORKER_PER_HOUR / TICKS_PER_HOUR)
                
                # Bonus bâtiments (si existant)
                building_bonus_multiplier = resources.get('building_bonus', {}).get(resource, 0)
                total_production = base_production + (base_production * building_bonus_multiplier / 100)
                
                # Ajouter aux ressources avec limite de stockage
                current_amount = resources.get(resource, 0)
                storage_limit = self._get_storage_limit(city, resource)
                
                if current_amount < storage_limit:
                    # Appliquer production jusqu'à la limite
                    actual_production = min(total_production, storage_limit - current_amount)
                    # Arrondir à 4 décimales pour éviter l'accumulation d'erreurs de virgule flottante
                    resources[resource] = round(current_amount + actual_production, 4)
                    city_production[resource] = actual_production
                    
                    # Log si production bloquée par limite
                    if actual_production < total_production:
                        self.logger.debug(f"⚠️ Production {resource} limitée: {actual_production}/{total_production} (stockage plein)")
                    elif actual_production > 0:
                        self.logger.debug(f"✅ Production {resource}: +{actual_production} (total: {resources[resource]})")
                else:
                    # Stockage plein
                    city_production[resource] = 0
                    self.logger.debug(f"⚠️ Production {resource} bloquée: stockage plein ({current_amount}/{storage_limit})")
        
        # === 2. GESTION POPULATION (avec PopulationManager) ===
        # Le PopulationManager s'occupe de toute la gestion population:
        # - Consommation céréales selon population non nourrie
        # - Calcul satisfaction et facteurs de croissance  
        # - Application croissance basée sur satisfaction
        # - Mise à jour satisfaction_details
        try:
            # Utiliser le PopulationManager pour une gestion complète de la population
            # IMPORTANT: elapsed_seconds doit correspondre à l'intervalle de tick réel
            self.population_manager.update_city_population(city, elapsed_seconds=self.auto_tick_interval)
        except Exception as e:
            self.logger.error(f"Erreur PopulationManager pour ville {city.get('id', 'unknown')}: {e}")
        
        # === 3. RECALCUL POPULATION LIBRE ===
        total_workers = sum(workers_assigned.values())
        resources['population_free'] = max(0, resources.get('population_total', 0) - total_workers)
        
        return city_production
    
    def _process_player_tick(self, player: Dict, cities: list) -> Dict[str, float]:
        """
        Traite tous les calculs pour UN joueur
        
        Returns:
            dict: Production du joueur
        """
        player_id = player['id']
        player_production = {}
        
        # === 1. PRODUCTION D'OR ===
        total_gold_production = 0
        total_research_production = 0
        
        for city in cities:
            if city.get('owner') == player_id:
                # Or: production d'or = 1 or/habitant/heure (× gold_rate)
                # Avec 1 tick = 10 sec, il y a 360 ticks/heure
                # Donc : 1 / 360 = 0.00278 or/tick par habitant
                population_free = city.get('resources', {}).get('population_free', 0)
                gold_rate = city.get('gold_rate', 1)
                
                GOLD_PER_HABITANT_PER_HOUR = 1.0
                TICKS_PER_HOUR = 360
                gold_per_habitant_per_tick = (GOLD_PER_HABITANT_PER_HOUR / TICKS_PER_HOUR) * gold_rate
                
                city_gold = population_free * gold_per_habitant_per_tick
                total_gold_production += city_gold
                
                # Recherche: workers académie × points_per_worker (en points/h) ÷ 360
                # Les valeurs dans buildings.json sont en points/heure (ex: 1 point/h)
                # Avec 1 tick = 10 secondes, il y a 360 ticks par heure
                workers_academy = city.get('workers_assigned', {}).get('academy', 0)
                if workers_academy > 0:
                    # Trouver l'Academy et son niveau
                    buildings = city.get('buildings', [])
                    academy = next((b for b in buildings if b.get('name') == 'Academy'), None)
                    
                    if academy:
                        # Récupérer points_per_worker depuis buildings.json (en points/heure)
                        effect = academy.get('effect', {})
                        points_per_worker_per_hour = effect.get('research_points_per_worker', 1.0)
                        
                        # Appliquer le bonus de recherche "Écriture" (+10%)
                        research_bonus_multiplier = 1.0
                        unlocked_research = player.get('unlocked_research', [])
                        if 'ecriture' in unlocked_research:
                            # Charger le bonus depuis research.json
                            research_path = os.path.join(self.data_manager.base_dir, 'data', 'research.json')
                            try:
                                with open(research_path, 'r', encoding='utf-8') as f:
                                    research_data = json.load(f)
                                ecriture = next((r for r in research_data.get('researches', []) if r.get('id') == 'ecriture'), None)
                                if ecriture and 'effect' in ecriture:
                                    bonus_percent = ecriture['effect'].get('research_points_bonus', 0)
                                    research_bonus_multiplier = 1 + (bonus_percent / 100.0)
                                    logging.info(f"[RECHERCHE BONUS] Player {player.get('id')} - Écriture: +{bonus_percent}% (multiplicateur={research_bonus_multiplier})")
                            except Exception as e:
                                logging.warning(f"Erreur chargement bonus recherche écriture: {e}")
                        
                        # Conversion: 1 tick = 10 sec, donc 360 ticks/heure
                        TICKS_PER_HOUR = 360
                        points_per_worker_per_tick = points_per_worker_per_hour / TICKS_PER_HOUR
                        
                        # Appliquer le bonus recherche
                        city_research = workers_academy * points_per_worker_per_tick * research_bonus_multiplier
                        logging.debug(f"[RECHERCHE] City {city.get('id')}: {workers_academy} workers × {points_per_worker_per_tick:.4f} × {research_bonus_multiplier} = {city_research:.4f} points/tick")
                        total_research_production += city_research
        
        # Appliquer à ce joueur
        if total_gold_production > 0:
            current_gold = player.get('gold', 0)
            # Arrondir à 4 décimales pour éviter l'accumulation d'erreurs de virgule flottante
            player['gold'] = round(current_gold + total_gold_production, 4)
            player_production['gold'] = total_gold_production
        
        if total_research_production > 0:
            current_research = player.get('research_points', 0)
            # Arrondir à 4 décimales pour éviter l'accumulation d'erreurs de virgule flottante
            player['research_points'] = round(current_research + total_research_production, 4)
            player_production['research_points'] = total_research_production
        
        # === HOOK QUÊTE: Mise à jour de la population (valeur absolue) ===
        try:
            from app.services.quest_service import quest_service
            username = player.get('username')
            if username:
                # Calculer la population maximale parmi toutes les villes du joueur
                max_population = 0
                for city in cities:
                    if city.get('owner') == player_id:
                        pop = city.get('resources', {}).get('population_total', 0)
                        max_population = max(max_population, pop)
                
                # Mettre à jour la quête avec set_value pour refléter la population actuelle
                if max_population > 0:
                    quest_service.update_quest_progress(
                        username=username,
                        quest_id='eco_reach_population',
                        set_value=int(max_population)
                    )
                
                # === HOOK QUÊTE: Points de recherche accumulés (valeur absolue) ===
                research_points = int(player.get('research_points', 0))
                if research_points > 0:
                    # Mettre à jour les deux quêtes possibles (ancien et nouveau nom)
                    for quest_id in ['sci_reach_research_level', 'sci_accumulate_research_points']:
                        result = quest_service.update_quest_progress(
                            username=username,
                            quest_id=quest_id,
                            set_value=research_points
                        )
        except Exception as e:
            # Ne jamais bloquer le tick principal si la mise à jour des quêtes échoue
            self.logger.warning(f"⚠️ Failed to update quests for {player.get('username', 'unknown')}: {e}")
        
        return player_production
    
    def _get_storage_limit(self, city: Dict, resource: str) -> float:
        """Calcule la limite de stockage pour une ressource"""
        # Limites par défaut (peuvent être augmentées par bâtiments)
        base_limits = {
            'wood': 3500, 'stone': 3500, 'iron': 3500, 'cereal': 3500, 'papyrus': 3500,
            'horse': 1000, 'marble': 1000, 'glass': 1000, 'meat': 1000, 'coal': 1000,
            'gunpowder': 1000, 'spices': 1000, 'cotton': 1000
        }
        
        base_limit = base_limits.get(resource, 1000)
        
        return base_limit
    
    # ===================================================================
    # AUTO-TICK INTÉGRÉ - MÉTHODES DE CONTRÔLE
    # ===================================================================
    
    def start_auto_tick(self):
        """Démarre l'auto-tick intégré"""
        if self.auto_tick_running:
            return False
            
        # S'assurer qu'aucun thread précédent n'existe
        if self.auto_tick_thread and self.auto_tick_thread.is_alive():
            self.stop_auto_tick()
            time.sleep(0.5)  # Laisser le temps au thread de s'arrêter
            
        self.auto_tick_running = True
        self.auto_tick_thread = threading.Thread(target=self._auto_tick_loop, daemon=True)
        self.auto_tick_thread.start()
        return True
        
    def stop_auto_tick(self):
        """Arrête l'auto-tick intégré"""
        if not self.auto_tick_running:
            return False
            
        self.auto_tick_running = False
        
        # Attendre que le thread se termine proprement
        if self.auto_tick_thread and self.auto_tick_thread.is_alive():
            try:
                self.auto_tick_thread.join(timeout=2.0)  # Max 2 secondes d'attente
            except:
                pass  # Arrêt silencieux
            
        self.auto_tick_thread = None
        return True
        
    def set_auto_tick_interval(self, seconds: float):
        """Change l'intervalle d'auto-tick"""
        self.auto_tick_interval = float(seconds)
        pass  # Changement silencieux
        return True
        
    def get_auto_tick_status(self) -> Dict[str, Any]:
        """Retourne le statut de l'auto-tick"""
        return {
            'enabled': self.auto_tick_running,
            'running': self.auto_tick_running,
            'thread_alive': self.auto_tick_thread.is_alive() if self.auto_tick_thread else False,
            'interval_seconds': self.auto_tick_interval,
            'run_production': True  # Toujours true dans cette version intégrée
        }
    
    def _auto_tick_loop(self):
        """Boucle d'auto-tick avec timing précis"""
        tick_count = 0
        next_tick_time = time.time() + self.auto_tick_interval
        
        while self.auto_tick_running:
            current_time = time.time()
            tick_count += 1
            
            try:
                # Exécuter le tick
                tick_start = time.time()
                result = self.execute_tick()
                
                execution_time = time.time() - tick_start
                cities_updated = result.get('cities_updated', 0)
                # Log seulement toutes les 10 ticks pour éviter le spam
                if tick_count % 10 == 0:
                    print(f"[AUTO-TICK] Tick #{tick_count} ({execution_time:.3f}s) - {cities_updated} villes")
                    
            except Exception as e:
                print(f"❌ [AUTO-TICK] Erreur: {e}")
            
            # Calculer le temps d'attente pour respecter l'intervalle exact
            next_tick_time += self.auto_tick_interval
            sleep_time = max(0, next_tick_time - time.time())
            
            # Si on est trop en retard, recaler
            if sleep_time <= 0:
                next_tick_time = time.time() + self.auto_tick_interval
                sleep_time = self.auto_tick_interval
            
            time.sleep(sleep_time)
    
    def _update_building_bonuses(self, city: Dict):
        """Met à jour les bonus de production des bâtiments pour une ville"""
        # Charger la config des bâtiments
        buildings_data = self.data_manager.load_buildings()
        if not buildings_data:
            return
        
        # Initialiser les structures de bonus
        if 'resources' not in city:
            city['resources'] = {}
        if 'building_bonus' not in city['resources']:
            city['resources']['building_bonus'] = {}
        
        # Calculer les bonus depuis tous les bâtiments terminés
        building_bonuses = {}
        
        for building in city.get('buildings', []):
            # Vérifier que le bâtiment est terminé
            if building.get('status') != 'Terminé':
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
        
        # Sauvegarder UNIQUEMENT les bonus non-nuls (optimisation pour milliers de villes)
        city['resources']['building_bonus'] = {
            resource: bonus 
            for resource, bonus in building_bonuses.items() 
            if bonus > 0
        }