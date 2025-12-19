"""
AIController - Contrôleur simplifié du système d'IA
Gère l'exécution basique des joueurs IA (construction et amélioration)
"""

import random
from typing import Dict, List


class AIController:
    """Contrôleur principal des IAs"""
    
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
    
    def execute_all_ais(self, force=False) -> Dict:
        """
        Exécute un tick pour toutes les IAs actives
        
        Args:
            force: Si True, ignore la vérification ai_auto_enabled (pour exécution manuelle)
        
        Returns:
            Résultats de l'exécution avec détails des actions
        """
        results = {
            'executed_count': 0,
            'total_actions': 0,
            'actions': []  # Liste des actions pour l'interface
        }
        
        # Vérifier si l'IA auto est activée (sauf si force=True)
        if not force and not self._is_ai_auto_enabled():
            return results
        
        # Récupérer tous les joueurs IA
        ai_players = self.get_all_ai_players()
        
        if not ai_players:
            return results
        
        for ai_player in ai_players:
            try:
                action_result = self.execute_ai(ai_player)
                results['executed_count'] += 1
                
                if action_result and isinstance(action_result, dict):
                    results['total_actions'] += 1
                    results['actions'].append(action_result)
                    # Écrire dans le fichier de logs pour la console web
                    self._write_console_log(action_result)
                elif action_result:
                    results['total_actions'] += 1
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
    
    def _is_ai_auto_enabled(self) -> bool:
        """Vérifie si l'IA auto est activée dans admin_settings.json"""
        try:
            import os
            import json
            
            # Trouver le chemin du fichier admin_settings.json
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            settings_path = os.path.join(base_dir, 'data', 'admin_settings.json')
            
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    return settings.get('ai_auto_enabled', False)
            
            return False
        except Exception as e:
            print(f"⚠️ Erreur lecture admin_settings.json: {e}")
            return False
    
    def execute_ai(self, ai_player: Dict):
        """
        Exécute un tick pour une IA spécifique
        
        Args:
            ai_player: Données du joueur IA
            
        Returns:
            Dict avec détails de l'action ou None
        """
        player_id = ai_player.get('id')
        player_name = ai_player.get('username', 'Unknown')
        
        # Récupérer les villes de l'IA
        savegame = self.data_manager.load_savegame()
        ai_cities = [c for c in savegame.get('cities', []) if c.get('owner') == player_id]
        
        if not ai_cities:
            return None
        
        # Choisir une ville au hasard
        city = random.choice(ai_cities)
        
        # Vérifier si construction/upgrade en cours
        buildings = city.get('buildings', [])
        has_construction = any(
            b.get('status') == 'En construction' or b.get('upgrade_in_progress', False)
            for b in buildings
        )
        
        if has_construction:
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'wait',
                'message': '⏳ En attente (construction en cours)',
                'success': False
            }
        
        # Décider : améliorer (70%) ou construire (30%)
        action_choice = random.random()
        
        if action_choice < 0.7:
            # Tenter une amélioration
            return self._try_upgrade(ai_player, city)
        else:
            # Tenter une construction
            return self._try_build(ai_player, city)
    
    def _try_upgrade(self, ai_player: Dict, city: Dict):
        """Tente d'améliorer un bâtiment"""
        from app.business.city_service import CityService
        from app.game_logic import GameLogic
        
        player_id = ai_player.get('id')
        player_name = ai_player.get('username', 'Unknown')
        buildings = city.get('buildings', [])
        
        # Filtrer les bâtiments terminés
        upgradable = [b for b in buildings if b.get('status') == 'Terminé']
        
        if not upgradable:
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'upgrade_failed',
                'message': '❌ Aucun bâtiment améliorable',
                'success': False
            }
        
        # Choisir le bâtiment avec le niveau le plus bas
        building = min(upgradable, key=lambda b: b.get('level', 1))
        
        try:
            game_logic = GameLogic(self.data_manager)
            city_service = CityService(self.data_manager, game_logic)
            result = city_service.upgrade_building(city['id'], building['slot_id'])
            
            if result:
                building_name = building.get('name')
                current_level = building.get('level', 1)
                print(f"  ✅ [{player_name}] Amélioration: {building_name} niveau {current_level} → {current_level + 1}")
                return {
                    'player_id': player_id,
                    'player_name': player_name,
                    'action': 'upgrade',
                    'message': f'🔨 Amélioration: {building_name} niv.{current_level} → {current_level + 1}',
                    'success': True
                }
            else:
                return {
                    'player_id': player_id,
                    'player_name': player_name,
                    'action': 'upgrade_failed',
                    'message': '❌ Amélioration échouée (raison inconnue)',
                    'success': False
                }
                
        except Exception as e:
            error_msg = str(e)
            if "Ressources insuffisantes" not in error_msg:
                print(f"  ⚠️ [{player_name}] Upgrade échoué: {error_msg}")
            return {
                'player_id': player_id,
                'player_name': player_name,
                'action': 'upgrade_failed',
                'message': f'❌ Erreur: {error_msg[:50]}',
                'success': False
            }
    
    def _try_build(self, ai_player: Dict, city: Dict):
        """Tente de construire un nouveau bâtiment"""
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
        
        # Liste de bâtiments à construire (ordre de priorité)
        building_priorities = [
            'Scierie',
            'Carrière',
            'Ferme',
            'Centre de Ressources',
            'Entrepôt',
            'Marché'
        ]
        
        # Essayer de construire dans l'ordre
        for building_name in building_priorities:
            try:
                game_logic = GameLogic(self.data_manager)
                city_service = CityService(self.data_manager, game_logic)
                result = city_service.build_building(city['id'], free_slot, building_name)
                
                if result and result.get('success'):
                    print(f"  ✅ [{player_name}] Construction: {building_name} sur {free_slot}")
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
    
    def _write_console_log(self, action_result: Dict):
        """Écrit un log dans le fichier JSON pour la console web"""
        try:
            import os
            import json
            from datetime import datetime
            
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            logs_path = os.path.join(base_dir, 'data', 'ai_console_logs.json')
            
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
