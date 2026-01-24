"""
=================================================================
AI_STRATEGY_MANAGER.PY - Gestionnaire simplifié des stratégies IA
=================================================================

RÔLE:
- Exécuter la stratégie 'development' (seule stratégie pour l'instant)
- Sauvegarder l'état avec historique dans ai_strategies_state.json
- Fournir update_phase_data() pour communication avec ai_controller

FORMAT JSON COMPLET:
{
  "player_8": {
    "current_strategy": "development",
    "strategy_started_cycle": 0,
    "current_phase": 0,
    "phase_data": {
      "current_domain": "construction",
      "cycle_counter": 33
    },
    "recent_actions": [
      {"cycle": 27, "action": "follow_build_order", "result": "failed", "reason": "..."},
      {"cycle": 28, "action": "follow_build_order", "result": "success", "reason": "..."}
    ]
  }
}

HISTORIQUE:
- Garde les 10 dernières actions
- Permet de détecter échecs répétés (future feature)

=================================================================
"""

import json
import os
import threading
from typing import Dict, Optional
from .strategy_registry import get_strategy_config

# Mode debug pour contrôler la verbosité des logs IA
DEBUG_MODE = False  # Mettre à True pour logs détaillés


class AIStrategyManager:
    """Gestionnaire simplifié des stratégies IA"""
    
    # Verrou partagé pour toutes les instances
    _state_lock = threading.Lock()
    
    def __init__(self, data_manager):
        """
        Args:
            data_manager: Instance de DataManager
        """
        self.data_manager = data_manager
        self.state_file = os.path.join(data_manager.base_dir, 'gamedata', 'ai_strategies_state.json')
    
    
    # ============================================================
    # CHARGEMENT / SAUVEGARDE DE L'ÉTAT
    # ============================================================
    
    def _load_state(self) -> Dict:
        """Charge l'état depuis le fichier JSON"""
        if not os.path.exists(self.state_file):
            return {}
        
        try:
            with self._state_lock:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[STRATEGY] Erreur chargement état: {e}")
            return {}
    
    
    def _save_state(self, state: Dict):
        """Sauvegarde l'état dans le fichier JSON avec formatage compact pour actions"""
        try:
            # Générer le JSON avec indentation
            json_str = json.dumps(state, indent=2, ensure_ascii=False)
            
            # Compacter les objets d'action ligne par ligne
            lines = json_str.split('\n')
            result = []
            i = 0
            
            while i < len(lines):
                line = lines[i]
                
                # Détecter un objet action: ligne avec juste { et ligne suivante avec "cycle"
                if line.strip() == '{' and i + 1 < len(lines) and '"cycle":' in lines[i + 1]:
                    indent = ' ' * (len(line) - len(line.lstrip()))
                    
                    # Collecter les propriétés
                    props = {}
                    j = i + 1
                    while j < len(lines) and lines[j].strip() not in ['}', '},']:
                        prop = lines[j].strip().rstrip(',')
                        if ':' in prop:
                            k, v = prop.split(':', 1)
                            k = k.strip().strip('"')
                            v = v.strip()
                            props[k] = int(v) if v.isdigit() else v.strip('"')
                        j += 1
                    
                    # Construire la ligne compacte
                    parts = [f'"cycle": {props["cycle"]}', f'"action": "{props["action"]}"', f'"result": "{props["result"]}"']
                    if 'reason' in props:
                        parts.append(f'"reason": "{props["reason"]}"')
                    
                    comma = ',' if lines[j].strip() == '},' else ''
                    result.append(indent + '{' + ', '.join(parts) + '}' + comma)
                    i = j + 1
                else:
                    result.append(line)
                    i += 1
            
            with self._state_lock:
                with open(self.state_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(result))
        except Exception as e:
            print(f"[STRATEGY] Erreur sauvegarde: {e}")
            import traceback
            traceback.print_exc()
    
    
    def _get_player_state(self, player_id: str) -> Dict:
        """
        Récupère l'état d'un joueur
        
        Structure des données:
        {
          "player_X": {
            "current_strategy": "development" ou "colonization",
            "current_phase": "unlock_research", "build_embassy", etc.
            "phase_data": {
              "city_cycles": { "city_id_123": 10 }  # Compteur de cycle par ville
            },
            "cities": {  # Toutes les actions sont ici (stratégie + développement)
              "city_id_123": {
                "cycle": 10,
                "recent_actions": [
                  {"cycle": 10, "action": "upgrade_failed", "result": "failed"},
                  {"cycle": 11, "action": "unlock_research", "result": "success"}
                ]
              }
            }
          }
        }
        
        Returns:
            Dict avec current_strategy, phase_data, cities
        """
        state = self._load_state()
        
        if player_id not in state:
            # Initialiser l'état complet
            state[player_id] = {
                'current_strategy': 'development',
                'strategy_started_cycle': 0,
                'current_phase': 0,
                'phase_data': {},
                'cities': {}  # Données par ville uniquement
            }
            self._save_state(state)
        
        return state[player_id]
    
    
    def _update_player_state(self, player_id: str, updates: Dict):
        """Met à jour l'état d'un joueur"""
        state = self._load_state()
        
        if player_id not in state:
            state[player_id] = {
                'current_strategy': 'development',
                'strategy_started_cycle': 0,
                'current_phase': 0,
                'phase_data': {},
                'recent_actions': [],  # Actions stratégiques globales
                'cities': {}  # Données par ville
            }
        
        # Appliquer les mises à jour
        state[player_id].update(updates)
        
        self._save_state(state)
    
    
    # ============================================================
    # EXÉCUTION DE LA STRATÉGIE
    # ============================================================
    
    def execute_strategy(self, ai_player: Dict, city: Dict, savegame_data: Dict) -> Optional[Dict]:
        """
        Exécute la stratégie du joueur IA
        
        Stratégies disponibles:
        - 'development': Construction et amélioration de bâtiments
        - 'colonization': Colonisation d'une nouvelle île
        
        Args:
            ai_player: Données du joueur IA
            city: Ville principale
            savegame_data: Données du jeu
        
        Returns:
            Dict avec l'action à exécuter ou None
        """
        player_id = ai_player.get('id')
        player_name = ai_player.get('username', 'Unknown')
        
        # 1. Charger l'état du joueur
        player_state = self._get_player_state(player_id)
        current_strategy_name = player_state.get('current_strategy', 'development')
        current_phase_name = player_state.get('current_phase', 'unlock_research')
        phase_data = player_state.get('phase_data', {})
        
        print(f"🔍 [{player_id}] Strategy: {current_strategy_name}, Phase: {current_phase_name}")
        
        # 2. Stratégie COLONIZATION
        if current_strategy_name == 'colonization':
            return self._execute_colonization_strategy(player_id, player_name, city, savegame_data, current_phase_name, phase_data)
        
        # 3. Stratégie DEVELOPMENT (par défaut)
        return self._execute_development_strategy(ai_player, player_id, player_name, city, savegame_data, phase_data)
    
    
    def _execute_colonization_strategy(self, player_id: str, player_name: str, city: Dict, 
                                       savegame_data: Dict, current_phase: str, phase_data: Dict) -> Optional[Dict]:
        """Exécute la stratégie de colonisation."""
        print(f"🏰 [{player_id}] Exécution colonization phase: {current_phase}")
        
        from .strategies.colonization_strategy import (
            execute_phase_unlock_research,
            execute_phase_build_embassy,
            execute_phase_select_island
        )
        
        # Mapper phase → fonction
        phase_executors = {
            'unlock_research': execute_phase_unlock_research,
            'build_embassy': execute_phase_build_embassy,
            'select_island': execute_phase_select_island
        }
        
        executor = phase_executors.get(current_phase)
        if not executor:
            print(f"⚠️ [{player_id}] Phase colonization inconnue: {current_phase}")
            return None
        
        print(f"▶️ [{player_id}] Appel executor pour phase: {current_phase}")
        
        # Exécuter la phase
        action_result = executor(player_id, city, savegame_data, phase_data)
        
        print(f"◀️ [{player_id}] Résultat executor: {action_result}")
        
        if not action_result:
            return None
        
        # Gérer les actions spéciales
        action_type = action_result.get('action')
        
        # Changement de phase
        if action_type == 'change_phase':
            next_phase = action_result.get('next_phase')
            print(f"📋 [{player_id}] Changement de phase: {current_phase} → {next_phase}")
            
            self._update_player_state(player_id, {
                'current_phase': next_phase
            })
            return None
        
        # Mise à jour phase_data
        if action_type == 'update_phase_data':
            updates = action_result.get('updates', {})
            self.update_phase_data(player_id, updates)
            return None
        
        # Abandon stratégie
        if action_type == 'abort_strategy':
            reason = action_result.get('reason', 'Unknown')
            print(f"❌ [{player_id}] Abandon colonization: {reason}")
            
            self._update_player_state(player_id, {
                'current_strategy': 'development',
                'current_phase': 0,
                'phase_data': {}
            })
            return None
        
        # Action normale
        if DEBUG_MODE:
            print(f"[STRATEGY] {player_name} 🏰 Colonization - {current_phase}")
        return {
            'strategy': 'colonization',
            'phase': current_phase,
            'action': action_result,
            'player_id': player_id,
            'player_name': player_name
        }
    
    
    def _execute_development_strategy(self, ai_player: Dict, player_id: str, player_name: str, 
                                      city: Dict, savegame_data: Dict, phase_data: Dict) -> Optional[Dict]:
        """Exécute la stratégie de développement (existante)."""
        # Charger la stratégie 'development'
        strategy_config = get_strategy_config('development')
        if not strategy_config:
            if DEBUG_MODE:
                print(f"[STRATEGY] Stratégie 'development' introuvable !")
            return None
        
        # Récupérer la phase (development n'a qu'1 phase)
        phases = strategy_config.get('phases', [])
        if not phases:
            return None
        
        current_phase = phases[0]  # Toujours phase 0
        
        # Exécuter la phase
        execute_func = current_phase.get('execute')
        if not execute_func:
            return None
        
        action_data = execute_func(ai_player, city, phase_data, savegame_data)
        
        # Logger (seulement en mode debug)
        if DEBUG_MODE:
            print(f"[STRATEGY] {player_name} 🏛️ Development - {current_phase['name']}")
        
        # Retourner l'action
        return {
            'strategy': 'development',
            'phase': current_phase['name'],
            'phase_index': 0,
            'total_phases': 1,
            'action': action_data,
            'player_id': player_id,
            'player_name': player_name
        }
    
    
    def switch_to_colonization(self, player_id: str, missing_resource: str, decision_score: float):
        """
        Bascule un joueur vers la stratégie de colonisation.
        
        Args:
            player_id: ID du joueur
            missing_resource: Ressource manquante qui déclenche la colonisation
            decision_score: Score de la décision (0-100)
        """
        print(f"🎯 [{player_id}] Basculement vers stratégie COLONIZATION")
        print(f"   Ressource: {missing_resource}, Score: {decision_score:.1f}")
        
        # Récupérer les city_cycles actuels pour les conserver
        player_state = self._get_player_state(player_id)
        existing_city_cycles = player_state.get('phase_data', {}).get('city_cycles', {})
        
        self._update_player_state(player_id, {
            'current_strategy': 'colonization',
            'current_phase': 'unlock_research',
            'phase_data': {
                'missing_resource': missing_resource,
                'decision_score': decision_score,
                'target_island_id': None,
                'target_city_id': None,
                'target_resource': None,
                'city_cycles': existing_city_cycles  # Conserver les compteurs
            }
        })
    
    
    # ============================================================
    # DONNÉES DE PHASE (utilisé par ai_controller)
    # ============================================================
    
    def update_phase_data(self, player_id: str, data_updates: Dict):
        """
        Met à jour les données de phase (partagées entre ticks)
        
        Utilisé par ai_controller pour stocker des infos (ex: domaine actuel)
        
        Args:
            player_id: ID du joueur
            data_updates: Données à mettre à jour
        """
        player_state = self._get_player_state(player_id)
        phase_data = player_state.get('phase_data', {})
        phase_data.update(data_updates)
        
        self._update_player_state(player_id, {
            'phase_data': phase_data
        })
    
    
    # ============================================================
    # HISTORIQUE PAR VILLE
    # ============================================================
    
    def add_city_action_to_history(self, player_id: str, city_id: str, action: str, result: str, reason: str = None, cycle: int = None):
        """
        Ajoute une action à l'historique d'une ville spécifique
        
        Args:
            player_id: ID du joueur
            city_id: ID de la ville
            action: Type d'action
            result: Résultat ('success' ou 'failed')
            reason: Raison (optionnel)
            cycle: Numéro de cycle de la ville (optionnel)
        """
        player_state = self._get_player_state(player_id)
        cities = player_state.get('cities', {})
        
        if city_id not in cities:
            cities[city_id] = {
                'cycle': 0,
                'current_domain': None,
                'recent_actions': []
            }
        
        city_data = cities[city_id]
        recent_actions = city_data.get('recent_actions', [])
        
        # Ajouter la nouvelle action
        new_action = {
            'cycle': cycle if cycle is not None else city_data.get('cycle', 0),
            'action': action,
            'result': result
        }
        
        if reason:
            new_action['reason'] = reason
        
        recent_actions.append(new_action)
        
        # Garder seulement les 8 dernières actions par ville
        if len(recent_actions) > 8:
            recent_actions = recent_actions[-8:]
        
        city_data['recent_actions'] = recent_actions
        cities[city_id] = city_data
        
        self._update_player_state(player_id, {
            'cities': cities
        })
