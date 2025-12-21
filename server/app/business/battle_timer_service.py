"""
BATTLE_TIMER_SERVICE.PY - Service de gestion automatique des timers de bataille
================================================================================

RESPONSABILITÉS:
- Mise à jour automatique des timers de bataille toutes les secondes
- Détection des timers expirés (> TURN_DURATION secondes)
- Déclenchement des actions automatiques si le joueur n'a pas agi
- Passage automatique au tour suivant

LOGIQUE DES ACTIONS AUTOMATIQUES:
1. Timer expiré → Vérifier si le joueur a fait au moins 1 action (rounds_history)
2. Si OUI → Passer au tour suivant (end_turn)
3. Si NON → Action automatique selon battle_status :
   - battle_status = 'deployment' : Déployer automatiquement les unités
   - battle_status = 'battle' : Faire jouer l'IA (battle_ai_basic.py)

INTÉGRATION:
- Appelé par TimerService (periodic_task_service.py) toutes les secondes
- Thread-safe avec les autres services
================================================================================
"""

import time
import json
from typing import Dict, List, Any
from app.data_manager import DataManager
from app.config.paths import BATTLES_V2_FILE, BATTLEFIELDS_V2_FILE

class BattleTimerService:
    
    # Constantes
    TURN_DURATION = 60  # Secondes par tour (joueurs normaux)
    TURN_DURATION_WILD = 20  # Secondes par tour (wild villages)
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        
    def update_all_battles(self) -> Dict[str, Any]:
        """
        Met à jour tous les timers de bataille actifs.
        Appelé toutes les secondes par TimerService.
        
        Returns: {"checked": int, "expired": int, "auto_actions": int}
        """
        try:
            # Charger les données des batailles
            battles_data = self._load_battles()
            if not battles_data:
                return {"checked": 0, "expired": 0, "auto_actions": 0}
            
            current_time = int(time.time() * 1000)  # Timestamp en millisecondes
            checked_count = 0
            expired_count = 0
            auto_actions_count = 0
            
            # Parcourir toutes les batailles actives
            for battle_id, battle_info in battles_data.items():
                # Vérifier si la bataille est terminée
                if self._is_battle_completed(battle_id, battle_info):
                    continue
                
                checked_count += 1
                
                # Vérifier si le timer est expiré
                if self._is_timer_expired(battle_id, battle_info, current_time):
                    expired_count += 1
                    
                    # Déclencher l'action automatique si nécessaire
                    action_triggered = self._handle_expired_timer(battle_id, battle_info, battles_data)
                    if action_triggered:
                        auto_actions_count += 1
            
            # NE PAS sauvegarder ici : _auto_deploy_units() et _call_end_turn() le font déjà
            # Sauvegarder ici écraserait leurs modifications car battles_data est une copie ancienne
            
            return {
                "checked": checked_count,
                "expired": expired_count,
                "auto_actions": auto_actions_count
            }
            
        except Exception as e:
            print(f"❌ [BATTLE-TIMER] Erreur update_all_battles: {e}")
            return {"checked": 0, "expired": 0, "auto_actions": 0, "error": str(e)}
    
    def _is_timer_expired(self, battle_id: str, battle_info: Dict[str, Any], current_time: int) -> bool:
        """Vérifie si le timer du tour actuel a expiré"""
        # Vérifier si le timer est en pause
        if battle_info.get('timer', {}).get('paused', False):
            return False
        
        turn_started_at = battle_info.get('turn_started_at', 0)
        if turn_started_at == 0:
            return False
        
        elapsed_ms = current_time - turn_started_at
        elapsed_seconds = elapsed_ms / 1000.0
        
        # Vérifier qui joue actuellement
        current_player = battle_info.get('current_player', '')
        
        # Timer de 20s si le joueur actuel est un wild_village, sinon 60s
        is_wild_player = current_player.startswith('wild_camp') or current_player.startswith('barbarian_village')
        
        # Utiliser le bon timer
        duration = self.TURN_DURATION_WILD if is_wild_player else self.TURN_DURATION
        
        return elapsed_seconds >= duration
    
    def _is_battle_completed(self, battle_id: str, battle_info: Dict[str, Any]) -> bool:
        """Vérifie si la bataille est terminée"""
        # Vérifier dans battle_info
        if battle_info.get('battle_status') == 'completed':
            return True
        
        # Vérifier dans battlefield
        try:
            battlefields_data = self._load_battlefields()
            if battle_id in battlefields_data:
                battlefield = battlefields_data[battle_id]
                if ('surrender_info' in battlefield or 
                    'completed_at' in battlefield or 
                    battlefield.get('status') == 'completed'):
                    return True
        except:
            pass
        
        return False
    
    def _handle_expired_timer(self, battle_id: str, battle_info: Dict[str, Any], battles_data: Dict[str, Any]) -> bool:
        """
        Gère le timer expiré : vérifie si le joueur a agi, sinon déclenche action auto
        
        Returns: True si une action auto a été déclenchée
        """
        try:
            current_player = battle_info.get('current_player', '')
            current_round = battle_info.get('current_round', 1)
            battle_status = battle_info.get('battle_status', 'deployment')
            
            print(f"⏰ [BATTLE-TIMER] Timer expiré pour {current_player} (Round {current_round}, Status: {battle_status})")
            
            if not current_player:
                return False
            
            # 1. Vérifier si le joueur a fait au moins une action ce tour
            player_has_acted = self._player_has_acted(battle_info, current_player, current_round)
            print(f"🔍 [BATTLE-TIMER] Joueur {current_player} a agi ce round ? {player_has_acted}")
            
            if player_has_acted:
                # Le joueur a agi → Juste passer au tour suivant
                print(f"✅ [BATTLE-TIMER] Joueur a agi, passage au tour suivant")
                self._call_end_turn(battle_id)
                return False  # Pas d'action auto
            
            # 2. Le joueur n'a pas agi → Vérifier si l'auto-IA est activée
            print(f"⚠️ [BATTLE-TIMER] Joueur {current_player} n'a PAS agi → Vérification auto-IA")
            
            # Vérifier le paramètre ai_auto_enabled dans admin_settings.json
            ai_auto_enabled = self._is_ai_auto_enabled()
            print(f"🎛️ [BATTLE-TIMER] Auto-IA activée : {ai_auto_enabled}")
            
            if not ai_auto_enabled:
                # Auto-IA désactivée → Passer le tour sans action
                print(f"⏭️ [BATTLE-TIMER] Auto-IA désactivée, passage au tour suivant sans action")
                self._call_end_turn(battle_id)
                return False
            
            # Auto-IA activée → Exécuter l'action automatique
            if battle_status == 'deployment':
                # Phase déploiement : déployer automatiquement
                deployment_result = self._auto_deploy_units(battle_id, current_player)
                if deployment_result:
                    print(f"🤖 [BATTLE-TIMER] Auto-déploiement pour {current_player} dans {battle_id}")
                # TOUJOURS appeler end_turn après le déploiement pour incrémenter le round
                self._call_end_turn(battle_id)
                return True
            else:
                # Phase bataille : faire jouer l'IA
                try:
                    from app.ai.battle_ai_basic import battle_ai
                    
                    print(f"🤖 [BATTLE-TIMER] Déclenchement IA pour {current_player} dans {battle_id}")
                    
                    # ⏸️ PAUSE DU TIMER : Réinitialiser turn_started_at pour donner du temps à l'IA
                    import time
                    current_time_ms = int(time.time() * 1000)
                    battle_info['turn_started_at'] = current_time_ms
                    print(f"⏸️ [BATTLE-TIMER] Timer réinitialisé pour laisser l'IA jouer")
                    
                    # Sauvegarder l'état mis à jour
                    from app.routes.battle_routes_v2 import save_json_data
                    from app.config.paths import BATTLES_V2_FILE
                    save_json_data(BATTLES_V2_FILE, battles_data, compact=True)
                    
                    # Exécuter l'IA
                    ai_acted = battle_ai.execute_ai_turn(battle_id, current_player)
                    
                    if ai_acted:
                        print(f"✅ [BATTLE-TIMER] IA a effectué une action pour {current_player}")
                    else:
                        print(f"⚠️ [BATTLE-TIMER] IA n'a pas pu agir pour {current_player}")
                        
                except Exception as e:
                    print(f"❌ [BATTLE-TIMER] Erreur IA: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 3. Passer au tour suivant
            self._call_end_turn(battle_id)
            
            return True  # Action auto déclenchée
            
        except Exception as e:
            print(f"❌ [BATTLE-TIMER] Erreur handle_expired_timer pour {battle_id}: {e}")
            return False
    
    def _player_has_acted(self, battle_info: Dict[str, Any], player_id: str, current_round: int) -> bool:
        """
        Vérifie si le joueur a fait au moins une action pendant ce tour
        en regardant rounds_history
        """
        rounds_history = battle_info.get('rounds_history', {})
        
        # Vérifier la clé du round actuel (format: "round_1", "round_2", etc.)
        round_key = f"round_{current_round}"
        
        if round_key not in rounds_history:
            return False
        
        # Récupérer les moves de ce round
        moves = rounds_history[round_key].get('moves', [])
        
        # Chercher si le joueur a au moins une action dans ce round
        # Les moves ont la structure: {"unitId": "defender_player_4_...", "move": {...}}
        # Il faut extraire player_id depuis unitId
        for move in moves:
            unit_id = move.get('unitId', '')
            # Vérifier si player_id est dans unitId (ex: "defender_player_4_barbarian_warrior_1" contient "player_4")
            if player_id in unit_id:
                print(f"   ✅ [BATTLE-TIMER] Action trouvée: {unit_id}")
                return True
        
        return False
    
    def _is_ai_auto_enabled(self) -> bool:
        """
        Vérifie si l'auto-IA est activée dans admin_settings.json
        
        Returns: True si ai_auto_enabled est activé
        """
        try:
            import os
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
            settings_path = os.path.join(data_dir, 'admin_settings.json')
            
            if not os.path.exists(settings_path):
                # Fichier absent → Considérer comme activé par défaut pour rétrocompatibilité
                print(f"⚠️ [BATTLE-TIMER] admin_settings.json absent, auto-IA activée par défaut")
                return True
            
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Par défaut True si la clé n'existe pas (rétrocompatibilité)
            return settings.get('ai_auto_enabled', True)
            
        except Exception as e:
            print(f"❌ [BATTLE-TIMER] Erreur lecture ai_auto_enabled: {e}")
            return True  # En cas d'erreur, activer par défaut
    
    def _auto_deploy_units(self, battle_id: str, player_id: str) -> bool:
        """
        Déploie automatiquement toutes les unités disponibles du joueur
        dans les zones prédéfinies
        
        Returns: True si le déploiement a réussi
        """
        try:
            # 1. Charger les données
            battles_data = self._load_battles()
            battlefields_data = self._load_battlefields()
            
            if battle_id not in battles_data or battle_id not in battlefields_data:
                print(f"❌ [AUTO-DEPLOY] Bataille {battle_id} non trouvée")
                return False
            
            battle_info = battles_data[battle_id]
            battlefield_info = battlefields_data[battle_id]
            unit_counts = battle_info.get('unit_counts', {})
            player_units = unit_counts.get(player_id, {})
            
            # 2. Récupérer les héros disponibles
            hero_participants = battle_info.get('hero_participants', {})
            player_hero_id = hero_participants.get(player_id)
            
            # 2. Récupérer les unités disponibles
            units_to_deploy = []
            for unit_type, counts in player_units.items():
                if isinstance(counts, dict):
                    total = counts.get('total', 0)
                    deployed = counts.get('deployed', 0)
                    available = max(0, total - deployed)
                    
                    if available > 0 and unit_type != 'heroes':
                        units_to_deploy.append({
                            'unit_type': unit_type,
                            'count': available
                        })
            
            if not units_to_deploy and not player_hero_id:
                print(f"⚠️ [AUTO-DEPLOY] Aucune unité à déployer pour {player_id}")
                return False
            
            # 3. Déterminer l'équipe (attacker/defender)
            participants = battlefield_info.get('participants', {})
            attackers = participants.get('attackers', [])
            team = 'attacker' if player_id in attackers else 'defender'
            
            # 4. Charger les zones de déploiement
            deployment_zones = self._get_deployment_zones(battlefield_info, team)
            if not deployment_zones:
                print(f"❌ [AUTO-DEPLOY] Zones de déploiement introuvables")
                return False
            
            # 5. Déployer d'abord le héros (si présent ET pas encore déployé)
            deployed_positions = []
            occupied_positions = self._get_occupied_positions(battle_info)
            
            if player_hero_id:
                # Vérifier si le héros n'est pas déjà déployé
                hero_already_deployed = False
                teams = battle_info.get('teams', {})
                for team_id, team_units in teams.items():
                    for unit in team_units:
                        if player_hero_id in unit.get('unitId', ''):
                            hero_already_deployed = True
                            break
                    if hero_already_deployed:
                        break
                
                if not hero_already_deployed:
                    hero_zones = deployment_zones.get('hero', [])
                    if not hero_zones:
                        hero_zones = deployment_zones.get('infantry', [])  # Fallback
                    
                    hero_position = self._find_free_position(hero_zones, occupied_positions)
                    if hero_position:
                        # 🦸 Récupérer les HP réels depuis player_heroes.json
                        hero_hp = self._get_hero_hp(player_id, player_hero_id)
                        
                        hero_unit_id = f"{team}_{player_id}_{player_hero_id}"
                        deployed_positions.append({
                            'unitId': hero_unit_id,
                            'position': hero_position,
                            'hp': hero_hp  # 🦸 HP réels du héros depuis player_heroes.json
                        })
                        occupied_positions.add(f"{hero_position[0]},{hero_position[1]}")
                        print(f"🦸 [AUTO-DEPLOY] Héros {player_hero_id} @ {hero_position} avec {hero_hp} HP")
                        
                        # Appliquer le bonus de moral du héros (copie exacte du code manuel)
                        try:
                            from app.battle.HeroBonusManager import HeroBonusManager
                            hero_manager = HeroBonusManager()
                            hero_bonuses = hero_manager.get_hero_bonuses(player_hero_id)
                            moral_bonus = hero_bonuses.get('moral_bonus', 0)
                            
                            if moral_bonus > 0:
                                if battle_id in battlefields_data:
                                    forces = battlefields_data[battle_id].get('forces', {})
                                    team_key = 'attackers' if team == 'attacker' else 'defenders'
                                    
                                    if team_key in forces and player_id in forces[team_key]:
                                        old_moral = forces[team_key][player_id].get('moral', 100)
                                        new_moral = old_moral + moral_bonus
                                        forces[team_key][player_id]['moral'] = new_moral
                        except Exception as e:
                            pass
            
            # 6. Déployer ensuite les unités dans les zones (en respectant max_stack_size)
            for unit_data in units_to_deploy:
                unit_type = unit_data['unit_type']
                total_count = unit_data['count']
                
                # Récupérer le max_stack_size pour ce type d'unité
                max_stack_size = self._get_max_stack_size(unit_type)
                
                # Calculer le nombre de stacks nécessaires
                num_stacks = (total_count + max_stack_size - 1) // max_stack_size  # Arrondi supérieur
                
                print(f"📦 [AUTO-DEPLOY] {unit_type}: {total_count} unités → {num_stacks} stacks (max {max_stack_size}/stack)")
                
                # Trouver la zone appropriée (infantry par défaut)
                zone_positions = deployment_zones.get('infantry', [])
                
                # Déployer chaque stack séparément
                remaining = total_count
                stack_counter = 1
                
                while remaining > 0:
                    # Taille de ce stack (min entre remaining et max_stack_size)
                    stack_size = min(remaining, max_stack_size)
                    
                    # Trouver une position libre
                    position = self._find_free_position(zone_positions, occupied_positions)
                    if position:
                        unit_id = f"{team}_{player_id}_{unit_type}_{stack_counter}"
                        deployed_positions.append({
                            'unitId': unit_id,
                            'position': position,
                            'unitCount': stack_size
                        })
                        occupied_positions.add(f"{position[0]},{position[1]}")
                        print(f"   ✅ Stack {stack_counter}: {stack_size} unités @ {position}")
                        stack_counter += 1
                        remaining -= stack_size
                    else:
                        print(f"   ⚠️ Plus de positions libres, {remaining} unités non déployées")
                        break
            
            if not deployed_positions:
                print(f"⚠️ [AUTO-DEPLOY] Aucune position libre trouvée")
                return False
            
            # 6. Sauvegarder les positions
            teams = battle_info.get('teams', {})
            if player_id not in teams:
                teams[player_id] = []
            
            teams[player_id].extend(deployed_positions)
            battle_info['teams'] = teams
            
            # 7. Mettre à jour unit_counts.deployed
            self._update_deployed_counts(battle_info)
            
            # 8. Sauvegarder les modifications (battles + battlefields)
            self._save_battles(battles_data)
            self._save_battlefields(battlefields_data)
            print(f"✅ [AUTO-DEPLOY] {player_id}: {len(deployed_positions)} stacks déployés")
            return True
            
        except Exception as e:
            print(f"❌ [AUTO-DEPLOY] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_deployment_zones(self, battlefield_info: Dict[str, Any], team: str) -> Dict[str, list]:
        """Récupère les zones de déploiement depuis le template du battlefield"""
        try:
            # Récupérer le nom du template (clé "map" dans battlefieldsv2.json)
            template_id = battlefield_info.get('map', '')
            if not template_id:
                print(f"❌ [AUTO-DEPLOY] Aucun template_id trouvé")
                return {}
            
            # Charger le template depuis data/battlefields/
            import os
            # __file__ est dans server/app/business/, on remonte 3 fois pour arriver à server/
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            template_path = os.path.join(base_dir, 'data', 'battlefields', f'{template_id}.json')
            
            if not os.path.exists(template_path):
                print(f"❌ [AUTO-DEPLOY] Template {template_id} non trouvé")
                return {}
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            zones = template_data.get('template', {}).get('deploymentZones', {}).get(team, {})
            return zones
            
        except Exception as e:
            print(f"❌ [AUTO-DEPLOY] Erreur chargement zones: {e}")
            return {}
    
    def _get_occupied_positions(self, battle_info: Dict[str, Any]) -> set:
        """Retourne toutes les positions déjà occupées"""
        occupied = set()
        teams = battle_info.get('teams', {})
        
        for team_id, team_units in teams.items():
            for unit in team_units:
                pos = unit.get('position', [])
                if len(pos) == 2:
                    occupied.add(f"{pos[0]},{pos[1]}")
        
        return occupied
    
    def _get_hero_hp(self, player_id: str, hero_id: str) -> float:
        """Récupère les HP du héros depuis player_heroes.json"""
        try:
            import json
            import os
            
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            heroes_file = os.path.join(base_dir, 'gamedata', 'player_heroes.json')
            
            with open(heroes_file, 'r', encoding='utf-8') as f:
                heroes_data = json.load(f)
            
            if player_id in heroes_data:
                player_heroes = heroes_data[player_id].get('heroes', {})
                if hero_id in player_heroes:
                    hero_stats = player_heroes[hero_id].get('calculated_stats', {})
                    return hero_stats.get('hp', 100)  # Défaut 100 si pas trouvé
            
            return 100  # Défaut
        except Exception as e:
            print(f"❌ [AUTO-DEPLOY] Erreur chargement HP héros {hero_id}: {e}")
            return 100
    
    def _get_max_stack_size(self, unit_type: str) -> int:
        """
        Récupère le max_stack_size pour un type d'unité depuis unit_stats.json
        
        Args:
            unit_type: Type d'unité (ex: "barbarian_warrior", "infantry_light")
            
        Returns:
            max_stack_size ou 10 par défaut
        """
        try:
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            unit_stats_file = os.path.join(base_dir, 'data', 'unit_stats.json')
            
            with open(unit_stats_file, 'r', encoding='utf-8') as f:
                unit_stats = json.load(f)
            
            # Chercher dans toutes les catégories (units, enemy_units, etc.)
            for category_name, category_units in unit_stats.items():
                if isinstance(category_units, dict) and unit_type in category_units:
                    max_stack = category_units[unit_type].get('max_stack_size', 10)
                    return max_stack
            
            # Si non trouvé, retourner 10 par défaut
            print(f"⚠️ [AUTO-DEPLOY] max_stack_size non trouvé pour {unit_type}, utilisation défaut: 10")
            return 10
            
        except Exception as e:
            print(f"❌ [AUTO-DEPLOY] Erreur lecture max_stack_size pour {unit_type}: {e}")
            return 10  # Défaut sécurisé
    
    def _find_free_position(self, zone_positions: list, occupied: set) -> list:
        """Trouve la première position libre dans une zone"""
        for pos in zone_positions:
            pos_key = f"{pos[0]},{pos[1]}"
            if pos_key not in occupied:
                return pos
        return None
    
    def _update_deployed_counts(self, battle_info: Dict[str, Any]):
        """Met à jour unit_counts.deployed en comptant depuis teams"""
        try:
            unit_counts = battle_info.get('unit_counts', {})
            teams = battle_info.get('teams', {})
            
            # Remettre tous les deployed à 0
            for player_id in unit_counts:
                for unit_type in unit_counts[player_id]:
                    if isinstance(unit_counts[player_id][unit_type], dict):
                        unit_counts[player_id][unit_type]['deployed'] = 0
            
            # Compter depuis teams
            for team_id, team_units in teams.items():
                for unit in team_units:
                    unit_id = unit.get('unitId', '')
                    unit_count = unit.get('unitCount', 0)
                    is_hero = unit.get('hp') is not None and 'unitCount' not in unit
                    
                    # Parser: "attacker_player_1_barbarian_warrior_1" ou "defender_player_4_hero_xxx"
                    parts = unit_id.split('_')
                    if len(parts) >= 4 and parts[1].startswith('player'):
                        player_id = f"{parts[1]}_{parts[2]}"  # ex: "player_1"
                        
                        if is_hero:
                            # 🦸 Compter les héros
                            if player_id in unit_counts and 'heroes' in unit_counts[player_id]:
                                unit_counts[player_id]['heroes']['deployed'] += 1
                        else:
                            # Compter les unités normales (unit_type entre player_id et le dernier nombre)
                            unit_type = '_'.join(parts[3:-1])  # ex: "barbarian_warrior"
                            if player_id in unit_counts and unit_type in unit_counts[player_id]:
                                unit_counts[player_id][unit_type]['deployed'] += unit_count
                            
        except Exception as e:
            print(f"❌ [AUTO-DEPLOY] Erreur update counts: {e}")
    
    def _call_end_turn(self, battle_id: str):
        """Appelle la fonction end_turn pour passer au joueur suivant"""
        try:
            from app.battle.battle_turn_manager_v2 import BattleTurnManagerV2
            
            turn_manager = BattleTurnManagerV2()
            result = turn_manager.end_turn(battle_id)
            
            if result.get('success'):
                new_player = result.get('current_player', 'inconnu')
                new_round = result.get('new_round', 1)
                print(f"⏭️ [BATTLE-TIMER] Tour passé à {new_player} (Round {new_round}) pour {battle_id}")
            else:
                print(f"❌ [BATTLE-TIMER] Erreur end_turn pour {battle_id}: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ [BATTLE-TIMER] Erreur call_end_turn pour {battle_id}: {e}")
    
    # ===== MÉTHODES UTILITAIRES =====
    
    def _load_battles(self) -> Dict[str, Any]:
        """Charge les données des batailles depuis battlesv2.json"""
        try:
            with open(BATTLES_V2_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            print(f"❌ [BATTLE-TIMER] Erreur chargement battles: {e}")
            return {}
    
    def _load_battlefields(self) -> Dict[str, Any]:
        """Charge les données des battlefields depuis battlefieldsv2.json"""
        try:
            with open(BATTLEFIELDS_V2_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            print(f"❌ [BATTLE-TIMER] Erreur chargement battlefields: {e}")
            return {}
    
    def _save_battles(self, battles_data: Dict[str, Any]):
        """Sauvegarde les données des batailles dans battlesv2.json"""
        try:
            with open(BATTLES_V2_FILE, 'w', encoding='utf-8') as f:
                json.dump(battles_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ [BATTLE-TIMER] Erreur sauvegarde battles: {e}")
    
    def _save_battlefields(self, battlefields_data: Dict[str, Any]):
        """Sauvegarde les données des battlefields dans battlefieldsv2.json"""
        try:
            with open(BATTLEFIELDS_V2_FILE, 'w', encoding='utf-8') as f:
                json.dump(battlefields_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ [BATTLE-TIMER] Erreur sauvegarde battlefields: {e}")
