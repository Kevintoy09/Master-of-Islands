"""
=================================================================
SESSION_TRACKER.PY - Suivi des sessions et temps de jeu
=================================================================

RESPONSABILITÉS:
- Tracking des sessions de connexion
- Calcul du temps de jeu actif (pause > 30min = pas compté)
- Batch save pour performances (sauvegarde tous les 5 actions)
- Cache en mémoire pour éviter charges répétées

FONCTIONNEMENT:
- start_session(): Appelé au login, incrémente session_count
- update_activity(): Appelé à chaque action, calcule temps actif
- Pause de 30+ minutes = temps non compté (construction AFK)
- Batch save tous les 5 actions pour optimisation

DONNÉES TRACKÉES (dans players.json):
- last_login: Timestamp dernière connexion
- last_activity: Timestamp dernière action
- session_count: Nombre total de sessions
- total_play_time_minutes: Temps de jeu actif cumulé

UTILISATION:
- Au login: session_tracker.start_session(player_id)
- À chaque action: session_tracker.update_activity(player_id)
=================================================================
"""

import time
from typing import Optional

# Seuil de pause pour détecter l'inactivité (30 minutes)
PAUSE_THRESHOLD_MINUTES = 30

# Batch save: sauvegarder tous les 10 appels pour performances (réduit conflits)
BATCH_SAVE_THRESHOLD = 10

class SessionTracker:
    """
    Service de suivi des sessions de jeu et du temps de jeu actif.
    Utilise un système de batch save pour optimiser les performances.
    """
    
    def __init__(self, data_manager):
        """
        Initialise le SessionTracker avec le DataManager.
        
        Args:
            data_manager: Instance du DataManager pour accès aux données
        """
        self.data_manager = data_manager
        self._activity_cache = {}  # Cache des données joueurs pour batch save
        self._save_counter = 0     # Compteur pour batch save
    
    def start_session(self, player_id: str) -> None:
        """
        Démarre une nouvelle session pour un joueur (appelé au login).
        
        - Met à jour last_login et last_activity
        - Incrémente session_count
        - Nettoie le cache pour nouvelle session
        
        Args:
            player_id: ID du joueur qui se connecte
        """
        players_data = self.data_manager.load_players()
        if not players_data:
            return
        
        # Trouver le joueur
        player = None
        for p in players_data.get('players', []):
            if p.get('id') == player_id:
                player = p
                break
        
        if not player:
            return
        
        current_time = int(time.time())
        
        # Initialiser les champs SessionTracker s'ils manquent (pour anciens joueurs)
        if 'creation_date' not in player:
            player['creation_date'] = current_time
        if 'last_login' not in player:
            player['last_login'] = None
        if 'last_activity' not in player:
            player['last_activity'] = None
        if 'session_count' not in player:
            player['session_count'] = 0
        if 'total_play_time_minutes' not in player:
            player['total_play_time_minutes'] = 0
        
        # Mettre à jour les timestamps
        player['last_login'] = current_time
        player['last_activity'] = current_time
        
        # Incrémenter le compteur de sessions
        player['session_count'] = player['session_count'] + 1
        
        # Nettoyer le cache pour ce joueur (nouvelle session)
        if player_id in self._activity_cache:
            del self._activity_cache[player_id]
        
        # Sauvegarder immédiatement (login = action critique)
        self.data_manager.save_players(players_data)
        
        print(f"📊 [SESSION] Nouvelle session pour {player.get('username', player_id)}: session #{player['session_count']}")
    
    def update_activity(self, player_id: str) -> None:
        """
        Met à jour l'activité d'un joueur (appelé à chaque action).
        
        LOGIQUE DE CALCUL:
        - Si delta < 30min: temps actif ajouté
        - Si delta > 30min: pause détectée, temps non ajouté
        
        BATCH SAVE:
        - Cache les données en mémoire
        - Sauvegarde tous les 5 appels seulement
        
        Args:
            player_id: ID du joueur actif
        """
        try:
            # Charger depuis le cache ou depuis le fichier
            if player_id not in self._activity_cache:
                players_data = self.data_manager.load_players()
                if not players_data:
                    return
                
                player = None
                for p in players_data.get('players', []):
                    if p.get('id') == player_id:
                        player = p
                        break
                
                if not player:
                    return
                
                # Mettre en cache
                self._activity_cache[player_id] = player
            else:
                player = self._activity_cache[player_id]
            
            current_time = int(time.time())
            
            # Initialiser les champs manquants si nécessaire (sécurité)
            if 'last_activity' not in player or player['last_activity'] is None:
                player['last_activity'] = current_time
            if 'total_play_time_minutes' not in player or player['total_play_time_minutes'] is None:
                player['total_play_time_minutes'] = 0
            
            last_activity = player['last_activity']
            
            # Calculer le delta en minutes
            delta_seconds = current_time - last_activity
            delta_minutes = delta_seconds / 60.0
            
            # Si delta < seuil de pause, c'est du temps actif
            if delta_minutes < PAUSE_THRESHOLD_MINUTES:
                # Ajouter le temps actif
                player['total_play_time_minutes'] = player.get('total_play_time_minutes', 0) + delta_minutes
            # Sinon, c'est une pause (construction/inactivité) - temps non compté
            
            # Mettre à jour last_activity
            player['last_activity'] = current_time
            
            # Incrémenter le compteur de batch save
            self._save_counter += 1
            
            # Sauvegarder tous les BATCH_SAVE_THRESHOLD appels
            if self._save_counter >= BATCH_SAVE_THRESHOLD:
                self._flush_cache()
                self._save_counter = 0
        
        except Exception as e:
            # Silent fail - ne pas bloquer l'action principale si le tracking échoue
            print(f"⚠️ [SESSION] Erreur update_activity (non-bloquante): {e}")
    
    def _flush_cache(self) -> None:
        """
        Sauvegarde toutes les données en cache (batch save).
        Appelé automatiquement tous les BATCH_SAVE_THRESHOLD appels.
        """
        if not self._activity_cache:
            return
        
        try:
            players_data = self.data_manager.load_players()
            if not players_data:
                return
            
            # Mettre à jour les joueurs depuis le cache
            for player_id, cached_player in self._activity_cache.items():
                for p in players_data.get('players', []):
                    if p.get('id') == player_id:
                        # Mettre à jour les champs trackés
                        p['last_activity'] = cached_player.get('last_activity')
                        p['total_play_time_minutes'] = cached_player.get('total_play_time_minutes', 0)
                        break
            
            # Sauvegarder avec retry en cas d'échec
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if self.data_manager.save_players(players_data):
                        break
                except Exception as e:
                    if attempt == max_retries - 1:
                        print(f"⚠️ [SESSION] Échec sauvegarde après {max_retries} tentatives: {e}")
                    else:
                        import time
                        time.sleep(0.1)  # Attendre 100ms avant retry
            
            # Nettoyer le cache
            self._activity_cache.clear()
            
        except Exception as e:
            print(f"⚠️ [SESSION] Erreur flush_cache (non-bloquante): {e}")
