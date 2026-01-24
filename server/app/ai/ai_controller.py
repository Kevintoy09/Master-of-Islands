"""
AIController - Système d'IA avec stratégies modulaires
=======================================================================

FONCTIONNALITÉS:
- Système de stratégies modulaires (development, etc.)
- Affectation automatique des ouvriers (ratios optimisés)
- Gestion des urgences (céréales, or)

STRATÉGIES DISPONIBLES:
- development: Développement économique standard
"""

import os
import random
import threading
from typing import Dict, List, Optional
from .ai_strategy_manager import AIStrategyManager
from .ai_military_manager import AIMilitaryManager
from .strategies.development_strategy import BUILD_ORDER, RESEARCH_PRIORITY

# Mode debug pour contrôler la verbosité des logs IA
DEBUG_MODE = False  # Mettre à True pour logs détaillés


class AIController:
    """Contrôleur principal des IAs avec build order intelligent"""
    
    # Domaines de décision (rotation cyclique)
    DOMAINES_IA = [
        'construction',  # Construire/upgrader bâtiments
        'workers',       # Affecter ouvriers
        'research',      # Débloquer recherches
        'military',      # Gérer production militaire (conditionnel)
        'transport',     # Envoyer ressources entre villes
    ]
    
    def __init__(self, data_manager=None):
        """
        Args:
            data_manager: Instance de DataManager (optionnel, chargé auto si non fourni)
        """
        if data_manager is None:
            from app.data_manager import DataManager
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.data_manager = DataManager(base_dir)
        else:
            self.data_manager = data_manager
        
        # Initialiser le gestionnaire de stratégies
        self.strategy_manager = AIStrategyManager(self.data_manager)
        
        # Initialiser le gestionnaire militaire
        self.military_manager = AIMilitaryManager(self.data_manager)
    
    def execute_all_ais(self, force=False, savegame_data=None) -> Dict:
        """
        Exécute un tick pour toutes les IAs actives
        
        Args:
            force: Si True, ignore la vérification ai_auto_enabled (pour exécution manuelle)
            savegame_data: Données du savegame (optionnel, chargées si non fournies)
        
        Returns:
            Résultats de l'exécution avec détails des actions
        """
        results = {
            'executed_count': 0,
            'total_actions': 0,
            'actions': []
        }
        
        # Vérifier si l'IA auto est activée (sauf si force=True)
        if not force and not self.data_manager.is_ai_auto_enabled():
            return results
        
        # Récupérer tous les joueurs IA
        ai_players = self.get_all_ai_players()
        
        if not ai_players:
            return results
        
        for ai_player in ai_players:
            try:
                action_result = self.execute_ai(ai_player, savegame_data=savegame_data)
                results['executed_count'] += 1
                
                if action_result and isinstance(action_result, dict):
                    results['total_actions'] += 1
                    results['actions'].append(action_result)
                    self._write_console_log(action_result)
                    
            except Exception as e:
                player_name = ai_player.get('username', 'Unknown')
                player_id = ai_player.get('id')
                error_msg = f"❌ Erreur: {str(e)}"
                print(f"{error_msg} [{player_name}]")
                
                results['actions'].append({
                    'player_id': player_id,
                    'player_name': player_name,
                    'action': 'error',
                    'message': error_msg,
                    'success': False
                })
        
        return results
    
    def execute_ai(self, ai_player: Dict, savegame_data=None) -> Optional[Dict]:
        """
        Exécute un tick pour une IA spécifique
        
        Args:
            ai_player: Données du joueur IA
            savegame_data: Données du savegame (optionnel, chargées si non fournies)
            
        Returns:
            Dict avec détails de l'action ou None
        """
        player_id = ai_player.get('id')
        player_name = ai_player.get('username', 'Unknown')
        
        # Récupérer les villes de l'IA
        if savegame_data is None:
            savegame_data = self.data_manager.load_savegame()
        ai_cities = [c for c in savegame_data.get('cities', []) if c.get('owner') == player_id]
        
        if not ai_cities:
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'no_city',
                'message': '❌ Aucune ville (IA inactive)',
                'success': False
            }
        
        # NOUVELLE LOGIQUE: Traiter chaque ville indépendamment
        # La ville principale (ai_cities[0]) gère les décisions stratégiques globales
        # Toutes les villes ont leur propre cycle de développement
        
        all_results = []
        
        # 1. Décisions stratégiques GLOBALES (colonisation, etc.) sur ville principale
        main_city = ai_cities[0]
        main_city_id = main_city.get('id')
        city_name = main_city.get('name', 'Unknown')
        
        self._log_debug(f"[{player_name}] {len(ai_cities)} ville(s) - Principale: {city_name}", player_id, player_name)
        
        # Vérifier stratégie globale (colonization, etc.)
        strategy_result = self.strategy_manager.execute_strategy(ai_player, main_city, savegame_data)
        
        if strategy_result:
            strategy_name = strategy_result.get('strategy')
            phase_name = strategy_result.get('phase')
            action_data = strategy_result.get('action', {})
            action_type = action_data.get('action') or action_data.get('type')
            
            # Si stratégie de colonisation, traiter uniquement celle-ci
            if strategy_name == 'colonization':
                self._log_debug(
                    f"[{player_name}] 🏰 Colonisation - Phase: {phase_name}",
                    player_id, player_name
                )
                
                # Si l'action est wait_resource, optimiser la production
                if action_data and action_data.get('action') == 'wait_resource':
                    resource_needed = action_data.get('resource')
                    amount_missing = action_data.get('amount_missing', 0)
                    
                    # Logger le manque dans recent_actions
                    city_cycle = self._get_city_cycle_counter(player_id, main_city.get('id'))
                    self.strategy_manager.add_city_action_to_history(
                        player_id,
                        main_city.get('id'),
                        'wait_resource',
                        'waiting',
                        action_data.get('reason', f'Manquant: {resource_needed}'),
                        cycle=city_cycle
                    )
                    
                    # Optimiser les workers pour produire cette ressource
                    worker_result = self._optimize_workers_for_resource(ai_player, main_city, resource_needed, savegame_data)
                    
                    # Incrémenter compteur et retourner
                    self._increment_cycle_counter(ai_player)
                    return worker_result
                
                # Sinon, exécuter l'action normale
                action_result = self._execute_strategy_action(ai_player, main_city, action_data, savegame_data)
                
                if action_result:
                    result_status = 'success' if action_result.get('success') else 'failed'
                    city_cycle = self._get_city_cycle_counter(player_id, main_city.get('id'))
                    self.strategy_manager.add_city_action_to_history(
                        player_id, 
                        main_city.get('id'),
                        action_type,
                        result_status,
                        action_result.get('message', 'Action effectuée'),
                        cycle=city_cycle
                    )
                    
                    # Incrémenter compteur global et retourner
                    self._increment_cycle_counter(ai_player)
                    return action_result
                
                # Si action_result est None, incrémenter et retourner None
                self._increment_cycle_counter(ai_player)
                return None
        
        # 2. Développement: Chaque ville se développe INDÉPENDAMMENT
        for city_index, city in enumerate(ai_cities, 1):
            city_id = city.get('id')
            city_name = f"City {city_index}"
            
            # Récupérer le cycle propre à cette ville
            city_cycle = self._get_city_cycle_counter(player_id, city_id)
            
            # Migration: Si ville principale (index 0) et city_cycle == 0, utiliser l'ancien cycle_counter
            if city == main_city and city_cycle == 0:
                player_state = self.strategy_manager._get_player_state(player_id)
                old_counter = player_state.get('phase_data', {}).get('cycle_counter', 0)
                if old_counter > 0:
                    print(f"🔄 Migration: Ville principale {city_id} - cycle {old_counter}")
                    # Initialiser avec l'ancien compteur
                    city_cycle = old_counter
                    # Sauvegarder immédiatement
                    phase_data = player_state.get('phase_data', {})
                    if 'city_cycles' not in phase_data:
                        phase_data['city_cycles'] = {}
                    phase_data['city_cycles'][city_id] = city_cycle
                    self.strategy_manager.update_phase_data(player_id, phase_data)
            
            city_domaine = self.DOMAINES_IA[city_cycle % len(self.DOMAINES_IA)]
            
            if DEBUG_MODE:
                print(f"🏙️ [{city_name}] Cycle {city_cycle} - Domaine: {city_domaine}")
            
            # Exécuter l'action selon le domaine
            city_result = None
            if city_domaine == 'construction':
                city_result = self._decide_construction(ai_player, city)
            elif city_domaine == 'workers':
                city_result = self._decide_workers(ai_player, city, savegame_data=savegame_data)
            elif city_domaine == 'research':
                city_result = self._decide_research(ai_player, city)
            elif city_domaine == 'military':
                city_result = self._decide_military(ai_player, city, savegame_data=savegame_data)
            elif city_domaine == 'transport':
                city_result = self._decide_transport(ai_player, city, savegame_data)
            
            # Logger résultat et enregistrer dans l'historique
            if city_result:
                if city_result.get('success'):
                    print(f"  ✅ {city_result.get('message', '')}")
                all_results.append(city_result)
                
                # Enregistrer l'action dans l'historique de la ville
                action_type = city_result.get('action', city_domaine)
                result_status = 'success' if city_result.get('success') else 'failed'
                reason = city_result.get('message', '')
                
                self.strategy_manager.add_city_action_to_history(
                    player_id, 
                    city_id,
                    action_type,
                    result_status,
                    reason,
                    cycle=city_cycle
                )
            
            # Incrémenter le cycle de CETTE ville
            self._increment_city_cycle_counter(player_id, city_id)
        
        # Incrémenter le compteur global du joueur
        self._increment_cycle_counter(ai_player)
        
        # Retourner le résultat de la ville principale
        action_result = all_results[0] if all_results else None
        
        # Recharger ai_player pour avoir le compteur à jour
        players_data = self.data_manager.load_players(use_cache=False)
        for p in players_data.get('players', []):
            if p.get('id') == player_id:
                ai_player['ai_cycle_counter'] = p.get('ai_cycle_counter', 0)
                break
        
        return action_result
    
    def _decide_construction(self, ai_player: Dict, city: Dict) -> Dict:
        """
        Décide quel bâtiment construire/améliorer selon le build order
        
        Returns:
            Dict avec le résultat de l'action
        """
        player_id = ai_player.get('id')
        player_name = ai_player.get('username', 'Unknown')
        buildings = city.get('buildings', [])
        
        # Vérifier si construction/upgrade en cours
        has_construction = any(
            b.get('status') == 'En construction' or b.get('upgrade_in_progress', False)
            for b in buildings
        )
        
        if has_construction:
            # Afficher quel bâtiment est en cours
            building_in_progress = next((b for b in buildings if b.get('status') == 'En construction' or b.get('upgrade_in_progress', False)), None)
            building_name = building_in_progress.get('name', 'Inconnu') if building_in_progress else 'Inconnu'
            is_upgrade = building_in_progress.get('upgrade_in_progress', False) if building_in_progress else False
            action_type = "amélioration" if is_upgrade else "construction"
            
            self._log_debug(f"[{player_name}] {action_type.capitalize()} en cours: {building_name}", player_id, player_name)
            
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'wait',
                'message': f'⏳ En attente ({action_type} de {building_name})',
                'success': False  # False pour ne pas incrémenter le cycle inutilement
            }
        
        # Analyser ce qui existe déjà (inclure même les bâtiments en construction/upgrade)
        existing_buildings = {}
        for b in buildings:
            name = b.get('name')
            level = b.get('level', 1)
            status = b.get('status', 'Terminé')
            is_upgrading = b.get('upgrade_in_progress', False)
            
            # Compter tous les bâtiments, même ceux en construction
            if name not in existing_buildings:
                existing_buildings[name] = level
            else:
                existing_buildings[name] = max(existing_buildings[name], level)
        
        # Log l'état actuel des bâtiments
        buildings_summary = ', '.join([f"{name}:{lvl}" for name, lvl in existing_buildings.items()]) if existing_buildings else "Aucun"
        self._log_debug(f"[{player_name}] Bâtiments existants: {buildings_summary}", player_id, player_name)
        
        # Log les ressources disponibles
        resources = city.get('resources', {})
        wood = int(resources.get('wood', 0))
        stone = int(resources.get('stone', 0))
        iron = int(resources.get('iron', 0))
        cereal = int(resources.get('cereal', 0))
        self._log_debug(f"[{player_name}] Ressources: Bois:{wood}, Pierre:{stone}, Fer:{iron}, Céréales:{cereal}", player_id, player_name)
        
        # Parcourir le build order et trouver la prochaine action
        for building_name, target_level in BUILD_ORDER:
            current_level = existing_buildings.get(building_name, 0)
            
            if current_level < target_level:
                # Ce bâtiment doit être construit ou amélioré
                if current_level == 0:
                    # Construire
                    self._log_debug(f"[{player_name}] Décision: Construire {building_name} (absent)", player_id, player_name)
                    return self._try_build(ai_player, city, building_name)
                else:
                    # Améliorer
                    self._log_debug(f"[{player_name}] Décision: Améliorer {building_name} de {current_level} → {target_level}", player_id, player_name)
                    return self._try_upgrade(ai_player, city, building_name)
            else:
                self._log_debug(f"[{player_name}] ✓ {building_name} niveau {current_level}/{target_level} (OK)", player_id, player_name)
        
        # Build order terminé → basculer vers système intelligent
        self._log_debug(f"[{player_name}] ✅ Build order complet → système intelligent", player_id, player_name)
        return self._decide_construction_intelligent(ai_player, city)
    
    def _decide_construction_intelligent(self, ai_player: Dict, city: Dict) -> Dict:
        """
        Système de décision intelligent de construction (POST-BUILD_ORDER).
        
        Utilise le moteur de décision avec prévisionnel et sauvegarde.
        
        Returns:
            Action dict (build, upgrade, wait)
        """
        from app.ai.strategies.building_decision_engine import decide_construction_with_forecast
        
        player_id = ai_player.get('id')
        player_name = ai_player.get('username', 'Unknown')
        
        # Récupérer le tick actuel depuis ai_player
        current_tick = ai_player.get('ai_cycle_counter', 0)
        
        # Charger les données du joueur depuis players.json
        players_data = self.data_manager.load_players()
        players = players_data.get('players', [])
        player = next((p for p in players if p['id'] == player_id), None)
        
        if not player:
            self._log_debug(f"[{player_name}] ⚠️ Joueur introuvable dans players.json", player_id, player_name)
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'wait',
                'message': 'Erreur données joueur',
                'success': False
            }
        
        # Appeler le moteur de décision
        decision = decide_construction_with_forecast(city, player, ai_player, current_tick)
        
        action_type = decision.get('action')
        building_name = decision.get('building_name')
        reason = decision.get('reason', '')
        
        self._log_debug(f"[{player_name}] 🤖 Décision intelligente: {action_type} - {reason}", player_id, player_name)
        
        # Convertir en action AI
        if building_name:
            # Vérifier si bâtiment existe
            building_exists = any(b.get('name') == building_name for b in city.get('buildings', []))
            
            if building_exists:
                return self._try_upgrade(ai_player, city, building_name)
            else:
                return self._try_build(ai_player, city, building_name)
        else:  # wait
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'wait',
                'message': f'⏳ {reason}',
                'success': True
            }
    
    def _decide_workers(self, ai_player: Dict, city: Dict, savegame_data=None) -> Dict:
        """
        Décide de l'affectation des ouvriers avec algorithme intelligent
        - Balance d'or sur 24h
        - Sites selon recherches
        - Stockages pleins exclus
        - Répartition équitable
        
        Args:
            savegame_data: Données du savegame (OBLIGATOIRE pour éviter les écrasements)
        """
        from app.game_logic import GameLogic
        from app.ai.worker_optimizer import WorkerOptimizer
        
        player_id = ai_player.get('id')
        player_name = ai_player.get('username', 'Unknown')
        city_id = city.get('id')
        
        resources = city.get('resources', {})
        total_population = resources.get('population_total', 0)
        cereal = resources.get('cereal', 0)
        
        self._log_debug(f"[{player_name}] Population: {int(total_population)}, Céréales: {int(cereal)}", player_id, player_name)
        
        # Urgence céréales
        if cereal < 10:
            self._log_debug(f"[{player_name}] ⚠️ URGENCE CÉRÉALES ({int(cereal)} < 10)", player_id, player_name)
        
        # Population insuffisante
        if total_population < 1:
            self._log_debug(f"[{player_name}] Population trop faible ({total_population})", player_id, player_name)
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'wait_population',
                'message': '⏳ Attente croissance',
                'success': False
            }
        
        # === CALCULER AFFECTATION OPTIMALE ===
        optimizer = WorkerOptimizer(self.data_manager)
        optimal_workers = optimizer.calculate_optimal_assignment(city, player_id, ai_player)
        
        if not optimal_workers:
            self._log_debug(f"[{player_name}] Aucun site disponible", player_id, player_name)
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'workers_ok',
                'message': '✓ Stockages pleins',
                'success': True
            }
        
        # Logs
        assignments_str = ', '.join([f'{s}:{w}' for s, w in optimal_workers.items()])
        self._log_debug(f"[{player_name}] Affectation optimale: {assignments_str}", player_id, player_name)
        
        # === APPLIQUER LES AFFECTATIONS ===
        # Charger le savegame si pas fourni
        if savegame_data is None:
            savegame_data = self.data_manager.load_savegame()
        
        # Utiliser le savegame_data passé en paramètre (partagé avec le tick)
        city_data = next((c for c in savegame_data.get('cities', []) if c.get('id') == city_id), None)
        
        if not city_data:
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'workers_failed',
                'message': '❌ Ville introuvable',
                'success': False
            }
        
        if 'workers_assigned' not in city_data:
            city_data['workers_assigned'] = {}
        
        # Appliquer chaque affectation
        game_logic = GameLogic(self.data_manager)
        changes_made = False
        
        for site_type, count in optimal_workers.items():
            valid, error_msg = game_logic.validate_worker_assignment(city_data, site_type, count, player_id)
            
            if valid:
                city_data['workers_assigned'][site_type] = count
                changes_made = True
                # Recalculer population_free immédiatement après chaque affectation
                city_data['resources']['population_free'] = game_logic.calculate_actual_free_population(city_data)
                self._log_debug(f"[{player_name}] ✅ {count} → {site_type} (population_free: {city_data['resources']['population_free']})", player_id, player_name)
            else:
                self._log_debug(f"[{player_name}] ❌ {site_type}: {error_msg}", player_id, player_name)
        
        # Appliquer les modifications
        if changes_made:
            city_data['resources']['population_free'] = game_logic.calculate_actual_free_population(city_data)
            
            # Sauvegarder immédiatement (l'objet savegame_data est partagé, les modifications sont déjà dedans)
            save_result = self.data_manager.save_savegame(savegame_data, force_save=True)
            
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'assign_workers',
                'message': f'👷 {assignments_str}',
                'success': True
            }
        else:
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'workers_failed',
                'message': '❌ Validation échouée',
                'success': False
            }
    
    def _optimize_workers_for_resource(self, ai_player: Dict, city: Dict, resource: str, savegame_data: Dict) -> Dict:
        """
        Optimise l'affectation des workers pour maximiser la production d'une ressource spécifique.
        
        Args:
            ai_player: Données du joueur IA
            city: Ville concernée
            resource: Ressource à optimiser (wood, stone, cereal, etc.)
            savegame_data: Données du jeu
            
        Returns:
            Dict avec le résultat de l'optimisation
        """
        from app.game_logic import GameLogic
        import json
        import os
        
        player_id = ai_player.get('id')
        player_name = ai_player.get('username', 'Unknown')
        city_id = city.get('id')
        
        # Convertir resource en site_type
        resource_to_site_map = {
            'wood': 'forest',
            'stone': 'quarry',
            'cereal': 'cereal',
            'papyrus': 'papyrus',
            'iron': 'iron',
            'marble': 'marble',
            'glass': 'glass',
            'sulfur': 'sulfur',
            'gold': 'academy'
        }
        
        target_site = resource_to_site_map.get(resource)
        
        if not target_site:
            print(f"⚠️ [{player_id}] Ressource inconnue pour optimisation: {resource}")
            return {
                'player_id': player_id,
                'action': 'optimize_workers',
                'message': f'❌ Ressource {resource} non reconnue',
                'success': False
            }
        
        # Récupérer city_data depuis savegame
        city_data = next((c for c in savegame_data.get('cities', []) if c.get('id') == city_id), None)
        
        if not city_data:
            return {
                'player_id': player_id,
                'action': 'optimize_workers',
                'message': '❌ Ville introuvable',
                'success': False
            }
        
        # Charger universe.json pour vérifier les sites disponibles sur l'île
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        universe_path = os.path.join(base_dir, 'data', 'universe.json')
        
        with open(universe_path, 'r', encoding='utf-8') as f:
            universe = json.load(f)
        
        # Trouver l'île de la ville
        island_id = city_data.get('island_id')
        island = next((isl for isl in universe.get('islands', []) if str(isl.get('id')) == str(island_id)), None)
        
        if not island:
            return {
                'player_id': player_id,
                'action': 'optimize_workers',
                'message': '❌ Île introuvable',
                'success': False
            }
        
        # Vérifier si la ville peut produire cette ressource
        resource_sites = island.get('resource_sites', [])
        site_exists = any(site.get('resource') == target_site for site in resource_sites)
        
        if not site_exists:
            print(f"⚠️ [{player_id}] La ville ne peut pas produire {resource} (pas de {target_site} sur l'île {island_id})")
            return {
                'player_id': player_id,
                'action': 'optimize_workers',
                'message': f'❌ Pas de {target_site} disponible sur l\'île',
                'success': False
            }
        
        # Obtenir la capacité du site
        site_capacity = next((site.get('level', 1) * 10 for site in resource_sites if site.get('resource') == target_site), 10)
        
        # Vérifier l'affectation actuelle
        current_workers = city_data.get('workers_assigned', {}).get(target_site, 0)
        
        # Si déjà au maximum, pas besoin d'optimiser
        if current_workers >= site_capacity:
            print(f"✅ [{player_id}] Workers {resource} déjà optimaux ({current_workers}/{site_capacity})")
            return {
                'player_id': player_id,
                'action': 'wait_production',
                'message': f'⏳ Attente production {resource} ({current_workers}/{site_capacity} workers)',
                'success': True
            }
        
        # Calculer la population disponible
        from app.ai.worker_optimizer import WorkerOptimizer
        
        game_logic = GameLogic(self.data_manager)
        optimizer = WorkerOptimizer(self.data_manager)
        
        total_pop = city_data.get('resources', {}).get('population', 0)
        academy_capacity = optimizer._get_academy_capacity(city_data)
        population_available = min(total_pop, academy_capacity)
        
        # Vérifier qu'il y a assez de population
        if population_available < 2:
            print(f"⚠️ [{player_id}] Population insuffisante pour optimiser ({population_available} workers)")
            return {
                'player_id': player_id,
                'action': 'optimize_workers',
                'message': f'⏳ Population insuffisante ({int(population_available)} workers)',
                'success': False
            }
        
        # Maximiser l'affectation sur la ressource cible
        # Garder un minimum pour gold (academy) si c'est pas la cible
        workers_assigned = {}
        
        if target_site == 'academy':
            # Maximiser academy
            workers_assigned['academy'] = population_available
        else:
            # Affecter minimum à academy (25% de la pop), reste sur target_site
            min_academy = max(1, int(population_available * 0.25))
            max_target = max(0, population_available - min_academy)  # Éviter les négatifs
            
            # Si max_target est 0, impossible d'optimiser
            if max_target == 0:
                print(f"⚠️ [{player_id}] Population trop faible pour optimiser {resource}")
                return {
                    'player_id': player_id,
                    'action': 'optimize_workers',
                    'message': f'⏳ Population insuffisante',
                    'success': False
                }
            
            workers_assigned['academy'] = min_academy
            workers_assigned[target_site] = min(max_target, site_capacity)
        
        # Appliquer les affectations
        changes_made = False
        
        for site_type, count in workers_assigned.items():
            valid, error_msg = game_logic.validate_worker_assignment(city_data, site_type, count, player_id)
            
            if valid:
                city_data['workers_assigned'][site_type] = count
                changes_made = True
                city_data['resources']['population_free'] = game_logic.calculate_actual_free_population(city_data)
        
        if changes_made:
            # Sauvegarder
            self.data_manager.save_savegame(savegame_data, force_save=True)
            
            assignments = ', '.join([f"{site}:{count}" for site, count in workers_assigned.items()])
            print(f"🎯 [{player_id}] Workers optimisés pour {resource}: {assignments}")
            
            return {
                'player_id': player_id,
                'action': 'optimize_workers',
                'message': f'🎯 Workers optimisés pour {resource}: {assignments}',
                'success': True
            }
        else:
            return {
                'player_id': player_id,
                'action': 'optimize_workers',
                'message': f'❌ Optimisation {resource} échouée',
                'success': False
            }
    
    def _decide_research(self, ai_player: Dict, city: Dict) -> Dict:
        """
        Décide de débloquer une recherche (cycle research)
        
        Returns:
            Dict avec le résultat de l'action
        """
        player_id = ai_player.get('id')
        player_name = ai_player.get('username', 'Unknown')
        
        # Récupérer les recherches déjà débloquées
        unlocked = ai_player.get('unlocked_research', [])
        research_points = ai_player.get('research_points', 0)
        
        self._log_debug(f"[{player_name}] Points de recherche: {int(research_points)}, Débloquées: {len(unlocked)}", player_id, player_name)
        
        # Trouver la prochaine recherche à débloquer
        for research_name in RESEARCH_PRIORITY:
            if research_name not in unlocked:
                # Vérifier si on a assez de points (coût simplifié : 50 points par recherche)
                cost = 50
                if research_points >= cost:
                    # Débloquer la recherche
                    try:
                        from app.game_logic import GameLogic
                        game_logic = GameLogic(self.data_manager)
                        
                        # Ajouter la recherche aux recherches débloquées
                        players_data = self.data_manager.load_players()
                        for p in players_data.get('players', []):
                            if p.get('id') == player_id:
                                if 'unlocked_research' not in p:
                                    p['unlocked_research'] = []
                                p['unlocked_research'].append(research_name)
                                p['research_points'] = p.get('research_points', 0) - cost
                                break
                        
                        self.data_manager.save_players(players_data)
                        
                        self._log_debug(f"[{player_name}] ✅ Recherche débloquée: {research_name} (-{cost} points)", player_id, player_name)
                        
                        return {
                            'player_id': player_id,
                            'player_name': player_name,
                            'action': 'research_unlock',
                            'message': f'🔬 Recherche débloquée: {research_name}',
                            'success': True
                        }
                    except Exception as e:
                        error_msg = str(e)
                        self._log_debug(f"[{player_name}] ❌ Erreur recherche {research_name}: {error_msg}", player_id, player_name)
                        return {
                            'player_id': player_id,
                            'player_name': player_name,
                            'action': 'research_failed',
                            'message': f'❌ Erreur recherche: {error_msg}',
                            'success': False
                        }
                else:
                    self._log_debug(f"[{player_name}] ⏳ Pas assez de points pour {research_name} ({int(research_points)}/{cost})", player_id, player_name)
                    return {
                        'player_id': player_id,
                        'player_name': player_name,
                        'action': 'research_wait',
                        'message': f'⏳ Attente points recherche ({int(research_points)}/{cost})',
                        'success': False
                    }
        
        # Toutes les recherches prioritaires débloquées
        self._log_debug(f"[{player_name}] ✓ Toutes les recherches prioritaires débloquées", player_id, player_name)
        return {
            'player_id': player_id,
            'player_name': player_name,
            'action': 'research_complete',
            'message': '✓ Recherches prioritaires complètes',
            'success': False
        }
    
    def _decide_military(self, ai_player: Dict, city: Dict, savegame_data=None) -> Dict:
        """
        Décide si production militaire nécessaire (conditionnel avec seuil 80%)
        
        Returns:
            Dict avec résultat de l'action ou skip si seuil non atteint
        """
        player_id = ai_player.get('id')
        player_name = ai_player.get('username', 'Unknown')
        city_id = city.get('id')
        city_name = city.get('name', f'City {city_id}')
        
        # Vérifier si production nécessaire
        if not self.military_manager.needs_military_production(player_id, savegame_data):
            current_power = self.military_manager.calculate_current_power(player_id, savegame_data)
            target_power = self.military_manager.calculate_target_power(player_id, savegame_data)
            
            self._log_debug(
                f"[{player_name}] ⏭️ Armée suffisante ({current_power:.0f}/{target_power:.0f})", 
                player_id, 
                player_name
            )
            
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'military_skip',
                'message': f'⏭️ Armée suffisante ({current_power:.0f}/{target_power:.0f})',
                'success': False
            }
        
        # Calculer plan de production
        production_plan = self.military_manager.calculate_production_plan(player_id, city_id, savegame_data)
        
        if not production_plan or not production_plan.get('units'):
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'military_no_plan',
                'message': '⚠️ Aucune unité disponible',
                'success': False
            }
        
        # Exécuter production
        result = self.military_manager.execute_military_production(
            player_id=player_id,
            city_id=city_id,
            production_plan=production_plan,
            savegame_data=savegame_data
        )
        
        if result.get('success'):
            units_summary = result.get('units_summary', '')
            self._log_debug(
                f"[{player_name}] 🏹 Production: {units_summary}",
                player_id,
                player_name
            )
        
        return result
    
    def _decide_transport(self, ai_player: Dict, city: Dict, savegame_data: Dict) -> Dict:
        """
        Transporte des ressources entre villes si détection de manques dans recent_actions
        
        Règles:
        - Analyse les échecs de construction pour détecter ressources manquantes
        - Transporte 50% du stock de la ville source
        - Seuil minimum: 250 ressources
        - Achète des bateaux si nécessaire (avec buffer or 24h)
        """
        from app.city_constants import TRANSPORT_CONSTANTS
        from app.business.transport_service import TransportService
        from app.ai.worker_optimizer import WorkerOptimizer
        import re
        
        player_id = ai_player.get('id')
        player_name = ai_player.get('username', 'Unknown')
        city_id = city.get('id')
        city_name = city.get('name', f'City {city_id}')
        
        # Vérifier si plusieurs villes
        all_player_cities = [c for c in savegame_data.get('cities', []) if c.get('owner') == player_id]
        
        if len(all_player_cities) <= 1:
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'transport_skip',
                'message': '⏭️ Une seule ville',
                'success': False
            }
        
        # Analyser recent_actions pour détecter besoins réels
        player_state = self.strategy_manager._get_player_state(player_id)
        city_state = player_state.get('cities', {}).get(city_id, {})
        recent_actions = city_state.get('recent_actions', [])
        
        needed_resources = set()
        for action in recent_actions:
            reason = action.get('reason', '')
            matches = re.findall(r'Manquant:\s*(\w+):\s*[\d.]+', reason)
            needed_resources.update(matches)
        
        if not needed_resources:
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'transport_check',
                'message': '✓ Pas de besoin détecté',
                'success': False
            }
        
        print(f"🚢 [{city_name}] Besoins: {', '.join(needed_resources)}")
        
        # Construire catalogue ressources par ville
        city_productions = {}
        for c in all_player_cities:
            c_resources = c.get('resources', {})
            city_productions[c.get('id')] = {
                'name': c.get('name', f'City {c.get("id")}'),
                **{res: c_resources.get(res, 0) for res in needed_resources}
            }
        
        city_resources = city.get('resources', {})
        
        # Chercher source pour chaque ressource manquante
        for resource in needed_resources:
            for source_city_id, source_data in city_productions.items():
                if source_city_id == city_id:
                    continue
                
                source_stock = source_data.get(resource, 0)
                transport_quantity = int(source_stock * 0.5)
                
                if transport_quantity < 250:
                    continue
                
                print(f"🚢 Source: {source_data['name']} → {transport_quantity} {resource}")
                
                # Vérifier/acheter bateaux
                ship_capacity = TRANSPORT_CONSTANTS['SHIP_CAPACITY']
                ships_needed = (transport_quantity + ship_capacity - 1) // ship_capacity
                current_ships = ai_player.get('transport_ships_total', 0)
                
                if current_ships < ships_needed:
                    ships_to_buy = ships_needed - current_ships
                    total_cost = sum(int(100 * (1.5 ** (current_ships + i))) for i in range(ships_to_buy))
                    
                    # Vérifier sécurité 24h
                    worker_optimizer = WorkerOptimizer(self.data_manager)
                    gold_balance_24h = worker_optimizer._calculate_gold_balance_24h(ai_player, city, savegame_data)
                    current_gold = ai_player.get('gold', 0)
                    
                    if current_gold - total_cost < gold_balance_24h:
                        return {
                            'player_id': player_id,
                            'player_name': player_name,
                            'action': 'transport_wait_gold',
                            'message': f'⏳ Attente or bateaux ({ships_to_buy})',
                            'success': False
                        }
                    
                    # Acheter
                    players_data = self.data_manager.load_players()
                    for p in players_data.get('players', []):
                        if p.get('id') == player_id:
                            p['gold'] = p.get('gold', 0) - total_cost
                            p['transport_ships_total'] = p.get('transport_ships_total', 0) + ships_to_buy
                            break
                    self.data_manager.save_players(players_data)
                    
                    # Recharger
                    players_data = self.data_manager.load_players(use_cache=False)
                    for p in players_data.get('players', []):
                        if p.get('id') == player_id:
                            ai_player['transport_ships_total'] = p.get('transport_ships_total', 0)
                            ai_player['gold'] = p.get('gold', 0)
                            break
                    
                    print(f"🚢 ✅ Acheté {ships_to_buy} bateaux ({total_cost} or)")
                
                # Créer transport
                try:
                    # Vérifier que les deux villes ont un port
                    source_city_obj = next((c for c in all_player_cities if c.get('id') == source_city_id), None)
                    dest_city_obj = city
                    
                    source_has_port = any('port' in b.get('name', '').lower() for b in source_city_obj.get('buildings', []))
                    dest_has_port = any('port' in b.get('name', '').lower() for b in dest_city_obj.get('buildings', []))
                    
                    if not source_has_port or not dest_has_port:
                        print(f"⚠️ Transport impossible: port manquant (source:{source_has_port}, dest:{dest_has_port})")
                        return {
                            'player_id': player_id,
                            'player_name': player_name,
                            'action': 'transport_no_port',
                            'message': f'⏳ Port manquant (source:{source_has_port}, dest:{dest_has_port})',
                            'success': False
                        }
                    
                    transport_service = TransportService(self.data_manager)
                    
                    # Calculer temps de chargement
                    loading_speed = 10
                    port = next((b for b in source_city_obj.get('buildings', []) 
                               if 'port' in b.get('name', '').lower()), None)
                    if port:
                        loading_speed = {1: 10, 2: 14, 3: 19}.get(port.get('level', 1), 10)
                    
                    loading_time = transport_quantity / loading_speed
                    
                    # Calculer distance - utiliser les coordonnées des îles
                    try:
                        import json
                        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                        universe_path = os.path.join(base_dir, 'data', 'universe.json')
                        
                        with open(universe_path, 'r', encoding='utf-8') as f:
                            universe = json.load(f)
                        
                        source_island_id = source_city_obj.get('island_id')
                        dest_island_id = dest_city_obj.get('island_id')
                        
                        source_island = next((isl for isl in universe.get('islands', []) if str(isl.get('id')) == str(source_island_id)), None)
                        dest_island = next((isl for isl in universe.get('islands', []) if str(isl.get('id')) == str(dest_island_id)), None)
                        
                        if source_island and dest_island:
                            import math
                            x1, y1 = source_island.get('coords', [0, 0])
                            x2, y2 = dest_island.get('coords', [0, 0])
                            distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                        else:
                            distance = 100
                    except Exception as e:
                        print(f"⚠️ Erreur calcul distance: {e}")
                        distance = 100
                    
                    travel_time = distance / TRANSPORT_CONSTANTS['STANDARD_SPEED']
                    
                    # Créer
                    result = transport_service.create_transport(
                        player_id=player_id,
                        source_city_id=source_city_id,
                        destination_city_id=city_id,
                        resources={resource: transport_quantity},
                        ships_needed=ships_needed,
                        loading_time=loading_time,
                        travel_time=travel_time
                    )
                    
                    if result.get('success'):
                        print(f"🚢 ✅ Transport créé: {transport_quantity} {resource}")
                        return {
                            'player_id': player_id,
                            'player_name': player_name,
                            'action': 'transport_created',
                            'message': f'🚢 Transport {resource}: {transport_quantity}',
                            'success': True
                        }
                    else:
                        return {
                            'player_id': player_id,
                            'player_name': player_name,
                            'action': 'transport_failed',
                            'message': f'❌ {result.get("message", "Erreur")}',
                            'success': False
                        }
                        
                except Exception as e:
                    return {
                        'player_id': player_id,
                        'player_name': player_name,
                        'action': 'transport_error',
                        'message': f'❌ Erreur: {str(e)}',
                        'success': False
                    }
        
        return {
            'player_id': player_id,
            'player_name': player_name,
            'action': 'transport_check',
            'message': '✓ Pas de source disponible',
            'success': False
        }
    
    def _increment_cycle_counter(self, ai_player: Dict):
        """Incrémente le compteur de cycle global du joueur et sauvegarde"""
        player_id = ai_player.get('id')
        player_name = ai_player.get('username', 'Unknown')
        
        try:
            players_data = self.data_manager.load_players()
            for player in players_data.get('players', []):
                if player.get('id') == player_id:
                    current_counter = player.get('ai_cycle_counter', 0)
                    player['ai_cycle_counter'] = current_counter + 1
                    break
            
            self.data_manager.save_players(players_data)
        except Exception as e:
            self._log_debug(f"[{player_name}] ⚠️ Erreur incrémentation cycle: {e}", player_id, player_name)
    
    
    def _get_city_cycle_counter(self, player_id: str, city_id: str) -> int:
        """Récupère le compteur de cycle spécifique à une ville"""
        player_state = self.strategy_manager._get_player_state(player_id)
        phase_data = player_state.get('phase_data', {})
        city_cycles = phase_data.get('city_cycles', {})
        return city_cycles.get(city_id, 0)
    
    
    def _increment_city_cycle_counter(self, player_id: str, city_id: str):
        """Incrémente le compteur de cycle d'une ville spécifique"""
        player_state = self.strategy_manager._get_player_state(player_id)
        phase_data = player_state.get('phase_data', {})
        
        # Initialiser city_cycles si nécessaire
        if 'city_cycles' not in phase_data:
            phase_data['city_cycles'] = {}
        
        # Incrémenter
        current = phase_data['city_cycles'].get(city_id, 0)
        phase_data['city_cycles'][city_id] = current + 1
        
        # Sauvegarder
        self.strategy_manager.update_phase_data(player_id, phase_data)
    
    def _manage_workers(self, ai_player: Dict, city: Dict) -> Optional[Dict]:
        """
        Gère l'affectation automatique des ouvriers selon les ratios
        
        Returns:
            Dict avec le résultat ou None si rien à faire
        """
        from app.game_logic import GameLogic
        
        player_id = ai_player.get('id')
        player_name = ai_player.get('username', 'Unknown')
        city_id = city.get('id')
        
        # Récupérer la population totale et libre
        total_population = city.get('resources', {}).get('population_total', 0)
        free_population = city.get('resources', {}).get('population_free', 0)
        
        if total_population <= 0:
            return None  # Pas de population, rien à faire
        
        # Déterminer le type de ressource de base de l'île
        island_id = city.get('island_id')
        base_resource_type = self._get_island_base_resource(island_id)
        
        # Calculer les ouvriers à assigner selon les ratios
        workers = {
            'academy': int(total_population * self.DEFAULT_WORKER_RATIOS['academy']),
            'forest': int(total_population * self.DEFAULT_WORKER_RATIOS['forest']),
            base_resource_type: int(total_population * self.DEFAULT_WORKER_RATIOS['base_resource']),
        }
        # Le reste va dans 'gold' (population libre)
        
        # Appliquer les assignations via GameLogic (même fonction que le player)
        game_logic = GameLogic(self.data_manager)
        changes_made = False
        
        for site_type, count in workers.items():
            try:
                success, msg, updated_city = game_logic.assign_workers_to_site(
                    city_id, site_type, count, player_id
                )
                if success:
                    changes_made = True
            except Exception as e:
                # Ignorer les erreurs (recherche manquante, etc.)
                pass
        
        if changes_made:
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'manage_workers',
                'message': f'👷 Ouvriers réaffectés (academy:{workers["academy"]}, forest:{workers["forest"]}, {base_resource_type}:{workers[base_resource_type]})',
                'success': True
            }
        
        return None
    
    def _try_build(self, ai_player: Dict, city: Dict, building_name: str) -> Dict:
        """Tente de construire un bâtiment spécifique"""
        from app.business.city_service import CityService
        from app.game_logic import GameLogic
        
        player_id = ai_player.get('id')
        player_name = ai_player.get('username', 'Unknown')
        
        # Trouver un slot libre
        buildings = city.get('buildings', [])
        used_slots = [b.get('slot_id') for b in buildings]
        
        free_slot = None
        for i in range(1, 21):
            slot = f"slot_{i}"
            if slot not in used_slots:
                free_slot = slot
                break
        
        if not free_slot:
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'build_failed',
                'message': '❌ Aucun slot libre',
                'success': False
            }
        
        try:
            game_logic = GameLogic(self.data_manager)
            city_service = CityService(self.data_manager, game_logic)
            result = city_service.build_building(city['id'], free_slot, building_name)
            
            if result and result.get('success'):
                self._log_debug(f"[{player_name}] ✅ Construction réussie: {building_name} sur {free_slot}", player_id, player_name)
                return {
                    'player_id': player_id,
                    'player_name': player_name,
                    'action': 'build',
                    'message': f'🏗️ Construction: {building_name} sur {free_slot}',
                    'success': True
                }
            else:
                error_msg = result.get('error', 'Erreur inconnue') if result else 'Résultat vide'
                self._log_debug(f"[{player_name}] ❌ Échec construction {building_name}: {error_msg}", player_id, player_name)
                return {
                    'player_id': player_id,
                    'player_name': player_name,
                    'action': 'build_failed',
                    'message': f'❌ Échec construction {building_name}: {error_msg}',
                    'success': False
                }
                
        except Exception as e:
            error_msg = str(e)
            self._log_debug(f"[{player_name}] ⚠️ Exception construction {building_name}: {error_msg}", player_id, player_name)
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'build_failed',
                'message': f'❌ Erreur construction {building_name}: {error_msg}',
                'success': False
            }
    
    def _try_upgrade(self, ai_player: Dict, city: Dict, building_name: str) -> Dict:
        """Tente d'améliorer un bâtiment spécifique"""
        from app.business.city_service import CityService
        from app.game_logic import GameLogic
        
        player_id = ai_player.get('id')
        player_name = ai_player.get('username', 'Unknown')
        buildings = city.get('buildings', [])
        
        # Trouver le bâtiment à améliorer
        target_building = None
        for b in buildings:
            if b.get('name') == building_name and b.get('status') == 'Terminé':
                target_building = b
                break
        
        if not target_building:
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'upgrade_failed',
                'message': f'❌ {building_name} introuvable ou non terminé',
                'success': False
            }
        
        try:
            game_logic = GameLogic(self.data_manager)
            city_service = CityService(self.data_manager, game_logic)
            result = city_service.upgrade_building(city['id'], target_building['slot_id'])
            
            if result:
                current_level = target_building.get('level', 1)
                self._log_debug(f"[{player_name}] ✅ Amélioration réussie: {building_name} {current_level} → {current_level + 1}", player_id, player_name)
                return {
                    'player_id': player_id,
                    'player_name': player_name,
                    'action': 'upgrade',
                    'message': f'🔨 Amélioration: {building_name} niv.{current_level} → {current_level + 1}',
                    'success': True
                }
            else:
                self._log_debug(f"[{player_name}] ❌ Échec amélioration {building_name} (raison inconnue)", player_id, player_name)
                return {
                    'player_id': player_id,
                    'player_name': player_name,
                    'action': 'upgrade_failed',
                    'message': f'❌ Amélioration {building_name} échouée',
                    'success': False
                }
                
        except Exception as e:
            error_msg = str(e)
            self._log_debug(f"[{player_name}] ⚠️ Exception upgrade {building_name}: {error_msg}", player_id, player_name)
            
            # Tracker les manques de ressources pour décision de colonisation
            if "Manquant:" in error_msg:
                self._track_resource_shortage_from_error(player_id, error_msg)
            
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'upgrade_failed',
                'message': f'❌ Erreur upgrade {building_name}: {error_msg}',
                'success': False
            }
    
    def _try_build_random(self, ai_player: Dict, city: Dict) -> Dict:
        """Construit un bâtiment aléatoire (quand build order terminé)"""
        from app.business.city_service import CityService
        from app.game_logic import GameLogic
        
        player_id = ai_player.get('id')
        player_name = ai_player.get('username', 'Unknown')
        
        # Trouver un slot libre
        buildings = city.get('buildings', [])
        used_slots = [b.get('slot_id') for b in buildings]
        
        free_slot = None
        for i in range(1, 21):
            slot = f"slot_{i}"
            if slot not in used_slots:
                free_slot = slot
                break
        
        if not free_slot:
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'build_failed',
                'message': '❌ Aucun slot libre',
                'success': False
            }
        
        # Liste de bâtiments à essayer (ordre de priorité)
        building_priorities = [
            'Scierie',
            'Mine',
            'Carrière',
            'Ferme',
            'Centre de Ressources',
            'Entrepôt',
            'Marché',
            'Forge',
            'Wall'
        ]
        
        # Essayer de construire dans l'ordre
        for building_name in building_priorities:
            try:
                game_logic = GameLogic(self.data_manager)
                city_service = CityService(self.data_manager, game_logic)
                result = city_service.build_building(city['id'], free_slot, building_name)
                
                if result and result.get('success'):
                    return {
                        'player_id': player_id,
                        'player_name': player_name,
                        'action': 'build',
                        'message': f'🏗️ Construction: {building_name} sur {free_slot}',
                        'success': True
                    }
                    
            except Exception as e:
                error_msg = str(e)
                # Continuer avec le bâtiment suivant si erreur
                if "Recherche requise" in error_msg or "Ressources insuffisantes" in error_msg or "Limite atteinte" in error_msg:
                    continue
                else:
                    print(f"  ⚠️ [{player_name}] Build échoué ({building_name}): {error_msg}")
        
        return {
            'player_id': player_id,
            'player_name': player_name,
            'action': 'build_failed',
            'message': '❌ Aucun bâtiment constructible (ressources insuffisantes)',
            'success': False
        }
    
    def get_all_ai_players(self) -> List[Dict]:
        """
        Récupère tous les joueurs IA
        
        Returns:
            Liste des joueurs IA
        """
        players_data = self.data_manager.load_players()
        
        ai_players = []
        for p in players_data.get('players', []):
            if p.get('is_ai', False):
                ai_players.append(p)
        
        return ai_players
    
    def _log_debug(self, message: str, player_id: str = None, player_name: str = None):
        """Affiche un log de débogage dans la console IA web"""
        # Envoyer vers la console IA web uniquement (pas de print serveur)
        self._write_console_log({
            'player_id': player_id,
            'player_name': player_name,
            'action': 'debug',
            'message': f"🔍 {message}",
            'success': None  # Neutre pour les logs de debug
        })
    
    def _get_island_base_resource(self, island_id: str) -> str:
        """
        Récupère le type de ressource de base de l'île depuis universe.json
        
        Args:
            island_id: ID de l'île
            
        Returns:
            Type de ressource ('stone', 'iron', 'cereal', 'papyrus') ou 'stone' par défaut
        """
        try:
            import os
            import json
            
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            universe_path = os.path.join(base_dir, 'data', 'universe.json')
            
            if os.path.exists(universe_path):
                with open(universe_path, 'r', encoding='utf-8') as f:
                    universe = json.load(f)
                
                # Chercher l'île par ID
                for island in universe.get('islands', []):
                    if island.get('id') == island_id:
                        return island.get('base_resource', 'stone')
            
            return 'stone'  # Défaut si non trouvé
            
        except Exception as e:
            print(f"⚠️ Erreur lecture universe.json: {e}")
            return 'stone'
    
    def _execute_strategy_action(self, ai_player: Dict, city: Dict, action_data: Dict, savegame_data: Dict) -> Optional[Dict]:
        """
        Exécute une action retournée par une stratégie
        
        Args:
            ai_player: Données du joueur IA
            city: Ville
            action_data: Données de l'action à exécuter
            savegame_data: Données du jeu
        
        Returns:
            Résultat de l'action
        """
        # Colonization retourne 'action', development retourne 'type'
        action_type = action_data.get('action') or action_data.get('type')
        player_id = ai_player.get('id')
        player_name = ai_player.get('username', 'Unknown')
        
        # === ACTION: FOLLOW_BUILD_ORDER ===
        if action_type == 'follow_build_order':
            # Utiliser le système de rotation existant
            cycle_counter = ai_player.get('ai_cycle_counter', 0)
            domaine = self.DOMAINES_IA[cycle_counter % len(self.DOMAINES_IA)]
            
            # Enregistrer le domaine actuel dans phase_data
            self.strategy_manager.update_phase_data(player_id, {
                'current_domain': domaine,
                'cycle_counter': cycle_counter
            })
            
            if domaine == 'construction':
                return self._decide_construction(ai_player, city)
            elif domaine == 'workers':
                return self._decide_workers(ai_player, city, savegame_data=savegame_data)
            elif domaine == 'research':
                return self._decide_research(ai_player, city)
        
        # === ACTION: BUILD ===
        elif action_type == 'build':
            building_name = action_data.get('building_name')
            return self._try_build(ai_player, city, building_name)
        
        # === ACTION: SAVE_GOLD ===
        elif action_type == 'save_gold':
            target = action_data.get('target', 1000)
            current = action_data.get('current', 0)
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'save_gold',
                'message': f'💰 Épargne ({current}/{target} or)',
                'success': True
            }
        
        # === ACTION: SELECT_ISLAND ===
        elif action_type == 'select_island':
            # Choisir une île selon les ressources manquantes
            missing_resources = action_data.get('missing_resources', [])
            
            if missing_resources:
                target_resource = missing_resources[0]  # Prendre la première manquante
            else:
                target_resource = 'iron'  # Par défaut
            
            # Mettre à jour les données de phase
            self.strategy_manager.update_phase_data(player_id, {
                'target_resource': target_resource,
                'target_island': 'island_to_find'  # TODO: Trouver vraiment une île
            })
            
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'select_island',
                'message': f'🗺️ Île cible: {target_resource}',
                'success': True
            }
        
        # === ACTION: UNLOCK_RESEARCH ===
        elif action_type == 'unlock_research':
            research_id = action_data.get('research_id')
            city_id = action_data.get('city_id')
            
            try:
                players_data = self.data_manager.load_players()
                player = next((p for p in players_data.get('players', []) if p.get('id') == player_id), None)
                
                if not player:
                    return {
                        'player_id': player_id,
                        'player_name': player_name,
                        'action': 'unlock_research',
                        'message': f'❌ Joueur introuvable',
                        'success': False
                    }
                
                if research_id in player.get('unlocked_research', []):
                    return {
                        'player_id': player_id,
                        'player_name': player_name,
                        'action': 'unlock_research',
                        'message': f'✅ {research_id} déjà débloquée',
                        'success': True
                    }
                
                if 'unlocked_research' not in player:
                    player['unlocked_research'] = []
                player['unlocked_research'].append(research_id)
                
                self.data_manager.save_players(players_data)
                
                return {
                    'player_id': player_id,
                    'player_name': player_name,
                    'action': 'unlock_research',
                    'message': f'🔬 {research_id}',
                    'success': True
                }
            except Exception as e:
                return {
                    'player_id': player_id,
                    'player_name': player_name,
                    'action': 'unlock_research',
                    'message': f'❌ Erreur: {str(e)}',
                    'success': False
                }
        
        # === ACTION: COLONIZE ===
        elif action_type == 'colonize':
            island_id = action_data.get('island_id')
            city_id = action_data.get('city_id')
            
            try:
                # Utiliser le service de colonisation existant
                from app.business.city_service import CityService
                from app.game_logic import GameLogic
                
                game_logic = GameLogic(self.data_manager)
                city_service = CityService(self.data_manager, game_logic)
                
                # Coloniser la ville
                city = city_service.claim_city(city_id, player_id)
                
                # Retour à la stratégie development
                self.strategy_manager._update_player_state(player_id, {
                    'current_strategy': 'development',
                    'current_phase': 0,
                    'phase_data': {}
                })
                
                return {
                    'player_id': player_id,
                    'player_name': player_name,
                    'action': 'colonize',
                    'message': f'🏝️ Île {island_id} colonisée (ville {city_id})',
                    'success': True
                }
            except Exception as e:
                return {
                    'player_id': player_id,
                    'player_name': player_name,
                    'action': 'colonize',
                    'message': f'❌ Erreur colonisation: {str(e)}',
                    'success': False
                }
        
        # === ACTION: COLONIZE_API ===
        elif action_type == 'colonize_api':
            target_resource = action_data.get('target_resource')
            
            # TODO: Appeler vraiment l'API de colonisation
            # Pour l'instant, juste logger
            
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'colonize',
                'message': f'🏝️ Colonisation île {target_resource} (TODO)',
                'success': False
            }
        
        # === ACTION: DEVELOP_NEW_CITY ===
        elif action_type == 'develop_new_city':
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'develop_colony',
                'message': '🏗️ Développement colonie (TODO)',
                'success': False
            }
        
        # Action inconnue
        return {
            'player_id': player_id,
            'player_name': player_name,
            'action': 'unknown',
            'message': f'❓ Action inconnue: {action_type}',
            'success': False
        }
    
    def _track_resource_shortage_from_error(self, player_id: str, error_msg: str):
        """
        Parse un message d'erreur de ressources et déclenche la vérification de colonisation.
        Les manques sont déjà trackés dans recent_actions, pas besoin de bloc séparé.
        
        Args:
            player_id: ID du joueur IA
            error_msg: Message d'erreur (ex: "Manquant: stone: 67, iron: 120")
        """
        try:
            # Parser le message d'erreur pour extraire les ressources manquantes
            # Format: "... Manquant: stone: 67, iron: 120"
            if "Manquant:" not in error_msg:
                return
            
            # Extraire la partie après "Manquant:"
            shortage_part = error_msg.split("Manquant:")[1].strip()
            
            # Parser les paires resource: amount
            shortage_pairs = shortage_part.split(",")
            
            for pair in shortage_pairs:
                parts = pair.strip().split(":")
                if len(parts) == 2:
                    resource = parts[0].strip()
                    
                    # Vérifier si colonisation doit être déclenchée
                    # (Les manques sont déjà trackés dans recent_actions)
                    self._check_colonization_trigger(player_id, resource)
                    
        except Exception as e:
            print(f"⚠️ Erreur tracking resource shortage: {e}")
    
    def _check_colonization_trigger(self, player_id: str, resource: str):
        """
        Décide de la meilleure solution pour un manque de ressource.
        Logique simple:
        - Si le joueur PRODUIT déjà la ressource → ATTENDRE
        - Sinon → COLONISER
        
        Args:
            player_id: ID du joueur IA
            resource: Ressource manquante
        """
        try:
            from .strategies.resource_analyzers import decide_resource_shortage_solution
            
            # Vérifier si le joueur est déjà en stratégie colonization
            player_state = self.strategy_manager._get_player_state(player_id)
            current_strategy = player_state.get('current_strategy', 'development')
            
            if current_strategy == 'colonization':
                # Déjà en colonization, ne pas re-déclencher
                return
            
            # Récupérer les villes du joueur
            savegame = self.data_manager.load_savegame()
            cities = [c for c in savegame.get('cities', []) if c.get('owner') == player_id]
            
            if not cities:
                return
            
            # Décision : attendre OU coloniser
            decision = decide_resource_shortage_solution(player_id, cities, resource, 0)
            
            best_solution = decision['best_solution']
            reason = decision['reason']
            produces = decision.get('produces_resource', False)
            
            # Logger la décision
            if best_solution == 'wait':
                print(f"⏳ [{player_id}] Manque de {resource}: {reason}")
                
            elif best_solution == 'colonize':
                score = decision.get('score', 0)
                is_viable = decision.get('colonize_viable', False)
                
                print(f"🎯 [{player_id}] Manque de {resource}: COLONISATION")
                print(f"   → Score: {score:.1f}/100 - {reason}")
                
                if is_viable and score >= 70:
                    # Basculer vers stratégie de colonisation
                    print(f"✅ [{player_id}] DÉCLENCHEMENT COLONISATION")
                    self._log_debug(f"🎯 COLONISATION déclenchée: {reason}", player_id)
                    
                    self.strategy_manager.switch_to_colonization(player_id, resource, score)
                else:
                    print(f"⏸️ [{player_id}] Colonisation pas encore viable (score: {score:.1f})")
                
        except Exception as e:
            print(f"⚠️ Erreur vérification colonisation: {e}")
    
    # Verrou pour ai_console_logs.json (partagé entre toutes les instances)
    _console_log_lock = threading.Lock()
    
    def _write_console_log(self, action_result: Dict):
        """Écrit un log dans le fichier JSON pour la console web"""
        # Temporairement désactivé pour éviter les problèmes BOM UTF-8
        return
        
        try:
            import os
            import json
            import threading
            from datetime import datetime
            
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            logs_path = os.path.join(base_dir, 'gamedata', 'ai_console_logs.json')
            
            with AIController._console_log_lock:
                # Lire les logs existants
                if os.path.exists(logs_path):
                    with open(logs_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    data = {'logs': []}
                
                # Ajouter le nouveau log
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'player_id': action_result.get('player_id'),
                    'player_name': action_result.get('player_name'),
                    'message': action_result.get('message'),
                    'action': action_result.get('action'),
                    'success': action_result.get('success')
                }
                data['logs'].append(log_entry)
                
                # Limiter à 100 derniers logs
                if len(data['logs']) > 100:
                    data['logs'] = data['logs'][-100:]
                
                # Sauvegarder
                with open(logs_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ Erreur écriture console log: {e}")
