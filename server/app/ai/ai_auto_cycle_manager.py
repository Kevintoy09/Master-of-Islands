"""
Gestionnaire des cycles automatiques IA
Gère l'exécution automatique des IA en fonction des ticks
"""
import json
import os
from datetime import datetime
from typing import Dict, Optional, List
from app.ai.ai_controller import AIController


class AIAutoCycleManager:
    """Gère les cycles automatiques d'IA"""
    
    def __init__(self, gamedata_dir: str):
        self.config_file = os.path.join(gamedata_dir, 'ai_auto_cycles.json')
        self.players_file = os.path.join(gamedata_dir, 'players.json')
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Charge la configuration depuis le fichier JSON"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Initialiser avec les presets par défaut
        default_config = {
            "enabled": True,
            "presets": {
                "casual": {"tick_per_cycle": 12, "time_slots": None},
                "easy": {"tick_per_cycle": 6, "time_slots": None},
                "medium": {"tick_per_cycle": 3, "time_slots": None},
                "hard": {"tick_per_cycle": 1, "time_slots": None},
                "extreme": {"tick_per_cycle": 0.5, "time_slots": None},
                "perso": {"tick_per_cycle": 1, "time_slots": []}
            }
        }
        
        # Sauvegarder le fichier par défaut
        self._save_config_data(default_config)
        return default_config
    
    def _save_config(self):
        """Sauvegarde la configuration dans le fichier JSON"""
        self._save_config_data(self.config)
    
    def _save_config_data(self, config_data: dict):
        """Sauvegarde des données de configuration dans le fichier JSON"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def _load_players(self) -> dict:
        """Charge les données des joueurs"""
        if os.path.exists(self.players_file):
            with open(self.players_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"players": []}
    
    def _save_players(self, players_data: dict):
        """Sauvegarde les données des joueurs"""
        with open(self.players_file, 'w', encoding='utf-8') as f:
            json.dump(players_data, f, indent=2, ensure_ascii=False)
    
    def is_enabled(self) -> bool:
        """Vérifie si le système est activé"""
        return self.config.get('enabled', False)
    
    def toggle_system(self, enabled: bool):
        """Active ou désactive le système"""
        self.config['enabled'] = enabled
        self._save_config()
    
    def get_presets(self) -> dict:
        """Retourne tous les presets disponibles"""
        return self.config.get('presets', {})
    
    def get_preset(self, name: str) -> Optional[dict]:
        """Retourne un preset spécifique"""
        return self.config.get('presets', {}).get(name)
    
    def save_preset(self, name: str, tick_per_cycle: float, time_slots: Optional[List[str]] = None):
        """Crée ou met à jour un preset"""
        if 'presets' not in self.config:
            self.config['presets'] = {}
        
        self.config['presets'][name] = {
            'tick_per_cycle': tick_per_cycle,
            'time_slots': time_slots
        }
        self._save_config()
    
    def delete_preset(self, name: str):
        """Supprime un preset"""
        if name in self.config.get('presets', {}):
            del self.config['presets'][name]
            self._save_config()
    
    def get_player_config(self, player_id: str) -> Optional[dict]:
        """Retourne la configuration d'un joueur (lit depuis players.json)"""
        players_data = self._load_players()
        for player in players_data.get('players', []):
            if player.get('id') == player_id or player.get('username') == player_id:
                preset_name = player.get('ai_preset')
                if preset_name:
                    return {'preset': preset_name}
        return None
    
    def set_player_preset(self, player_id: str, preset_name: Optional[str]):
        """Assigne un preset à un joueur dans players.json"""
        # Vérifier que le preset existe si fourni
        if preset_name and preset_name not in self.config.get('presets', {}):
            raise ValueError(f"Preset '{preset_name}' n'existe pas")
        
        # Modifier players.json
        players_data = self._load_players()
        player_found = False
        
        for player in players_data.get('players', []):
            if player.get('id') == player_id or player.get('username') == player_id:
                if preset_name is None:
                    # Retirer le preset
                    if 'ai_preset' in player:
                        del player['ai_preset']
                else:
                    # Assigner le preset
                    player['ai_preset'] = preset_name
                player_found = True
                break
        
        if not player_found:
            raise ValueError(f"Joueur '{player_id}' non trouvé")
        
        self._save_players(players_data)
    
    def is_in_active_time_slot(self, time_slots: Optional[List[str]]) -> bool:
        """Vérifie si l'heure actuelle est dans une des plages horaires"""
        if not time_slots:
            return True  # Pas de restriction horaire
        
        current_time = datetime.now()
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        for slot in time_slots:
            # Format attendu: "8h-12h" ou "18h30-22h45"
            try:
                start_str, end_str = slot.split('-')
                
                # Parser l'heure de début
                if 'h' in start_str:
                    parts = start_str.split('h')
                    start_hour = int(parts[0])
                    start_minute = int(parts[1]) if len(parts) > 1 and parts[1] else 0
                else:
                    start_hour = int(start_str)
                    start_minute = 0
                
                # Parser l'heure de fin
                if 'h' in end_str:
                    parts = end_str.split('h')
                    end_hour = int(parts[0])
                    end_minute = int(parts[1]) if len(parts) > 1 and parts[1] else 0
                else:
                    end_hour = int(end_str)
                    end_minute = 0
                
                # Convertir en minutes depuis minuit
                current_minutes = current_hour * 60 + current_minute
                start_minutes = start_hour * 60 + start_minute
                end_minutes = end_hour * 60 + end_minute
                
                # Vérifier si dans la plage
                if start_minutes <= current_minutes <= end_minutes:
                    return True
                    
            except (ValueError, IndexError):
                # Format invalide, ignorer ce slot
                continue
        
        return False
    
    def get_cycles_to_execute(self, player_id: str, current_tick: int) -> int:
        """
        Calcule le nombre de cycles à exécuter pour un joueur à ce tick
        
        Args:
            player_id: ID du joueur
            current_tick: Numéro du tick actuel
            
        Returns:
            Nombre de cycles à exécuter (0 si aucun)
        """
        if not self.is_enabled():
            return 0
        
        player_config = self.get_player_config(player_id)
        if not player_config:
            return 0
        
        preset_name = player_config.get('preset')
        if not preset_name:
            return 0
        
        preset = self.get_preset(preset_name)
        if not preset:
            return 0
        
        # Vérifier la plage horaire
        time_slots = preset.get('time_slots')
        if not self.is_in_active_time_slot(time_slots):
            return 0
        
        # Calculer le nombre de cycles
        tick_per_cycle = preset.get('tick_per_cycle', 1)
        
        if tick_per_cycle < 1:
            # Plusieurs cycles par tick (ex: 0.5 → 2 cycles/tick)
            return int(1 / tick_per_cycle)
        else:
            # 1 cycle tous les N ticks
            return 1 if current_tick % int(tick_per_cycle) == 0 else 0
    
    def execute_ai_cycles_for_tick(self, current_tick: int, ai_controller: AIController, savegame_data: dict = None) -> dict:
        """
        Exécute les cycles IA pour tous les joueurs configurés à ce tick
        
        Args:
            current_tick: Numéro du tick actuel
            ai_controller: Instance du contrôleur IA
            savegame_data: Données de sauvegarde (optionnel)
            
        Returns:
            Dict avec les statistiques d'exécution
        """
        if not self.is_enabled():
            return {"enabled": False, "executed": 0}
        
        stats = {
            "enabled": True,
            "executed": 0,
            "players": []
        }
        
        # Lire depuis players.json
        players_data = self._load_players()
        for player in players_data.get('players', []):
            if not player.get('is_ai'):
                continue
                
            player_id = player.get('id')
            if not player_id:
                continue
            
            cycles_to_execute = self.get_cycles_to_execute(player_id, current_tick)
            
            if cycles_to_execute > 0:
                for i in range(cycles_to_execute):
                    try:
                        # Utiliser execute_ai au lieu de execute_ai_cycle
                        result = ai_controller.execute_ai(player, savegame_data)
                        if result:
                            stats["executed"] += 1
                            stats["players"].append(player_id)
                    except Exception as e:
                        print(f"[AI AUTO CYCLE] Erreur lors de l'exécution du cycle pour {player_id}: {e}")
        
        return stats
    
    def get_status(self) -> dict:
        """Retourne le statut complet du système"""
        # Recharger la config pour s'assurer qu'elle est à jour
        self.config = self._load_config()
        
        active_now = 0
        player_configs = {}
        
        # Lire depuis players.json
        players_data = self._load_players()
        for player in players_data.get('players', []):
            if player.get('is_ai') and player.get('ai_preset'):
                player_id = player.get('id')
                preset_name = player.get('ai_preset')
                preset = self.get_preset(preset_name)
                
                if preset_name:
                    player_configs[player_id] = {'preset': preset_name}
                    
                    if preset and self.is_in_active_time_slot(preset.get('time_slots')):
                        active_now += 1
        
        return {
            "enabled": self.is_enabled(),
            "presets": self.get_presets(),
            "player_configs": player_configs,
            "active_now": active_now
        }
