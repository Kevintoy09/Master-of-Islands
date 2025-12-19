"""
SaveService - Service centralisé pour la gestion des sauvegardes
Remplace les accès directs multiples à savegame.json par un cache intelligent.
"""

import json
import os
import threading
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import traceback

class SaveService:
    """
    Service de sauvegarde centralisé avec cache intelligent et batch saving.
    
    Fonctionnalités:
    - Cache en mémoire pour éviter les accès disque répétés
    - Sauvegarde par batch avec différents niveaux de priorité
    - Thread-safe avec locks granulaires
    - Fallback automatique en cas d'échec
    - Métriques de performance
    """
    
    def __init__(self, savegame_path: str = "gamedata/savegame.json"):
        self.savegame_path = savegame_path
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: float = 0
        self._cache_lock = threading.RLock()
        self._save_lock = threading.Lock()
        
        # Configuration de performance - TTL très faible pour consommation temps réel
        self.cache_ttl = 1.0  # Cache valide pendant 1 seconde pour consommation temps réel
        self.batch_save_interval = 5.0  # Sauvegarde batch toutes les 5 secondes pour auto-tick
        self.force_save_threshold = 5  # Force la sauvegarde après 5 modifications pour auto-tick
        
        # Tracking des modifications
        self._pending_changes: Dict[str, Any] = {}
        self._change_count = 0
        self._last_save_time = time.time()
        
        # Métriques
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'saves_total': 0,
            'saves_forced': 0,
            'saves_batch': 0,
            'errors': 0
        }
        
        # Thread de sauvegarde en arrière-plan avec intervalle plus long
        self._running = True
        self._batch_thread = threading.Thread(target=self._batch_save_worker, daemon=True)
        self._batch_thread.start()
        print("[OK] Thread de sauvegarde automatique reactive avec intervalle optimise")
    
    def get_savegame(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Récupère les données de sauvegarde, depuis le cache si possible.
        
        Args:
            force_reload: Force le rechargement depuis le disque
            
        Returns:
            Dictionnaire des données de sauvegarde
        """
        with self._cache_lock:
            current_time = time.time()
            
            # Vérifier si le cache est valide
            if not force_reload and self._cache is not None:
                cache_age = current_time - self._cache_timestamp
                if cache_age < self.cache_ttl:
                    self.stats['cache_hits'] += 1
                    return self._cache.copy()
            
            # Charger depuis le disque
            try:
                self.stats['cache_misses'] += 1
                
                if not os.path.exists(self.savegame_path):
                    # Créer un savegame vide si nécessaire
                    default_data = self._create_default_savegame()
                    self._save_to_disk(default_data)
                    self._cache = default_data
                else:
                    with open(self.savegame_path, 'r', encoding='utf-8') as f:
                        self._cache = json.load(f)
                
                self._cache_timestamp = current_time
                return self._cache.copy()
                
            except Exception as e:
                self.stats['errors'] += 1
                print(f"Erreur lors du chargement de {self.savegame_path}: {e}")
                traceback.print_exc()
                
                # Fallback: retourner le cache existant ou un savegame par défaut
                if self._cache is not None:
                    return self._cache.copy()
                else:
                    return self._create_default_savegame()
    
    def save_savegame(self, data: Dict[str, Any], force: bool = False, priority: str = "normal") -> bool:
        """
        Sauvegarde les données, immédiatement ou en batch selon la priorité.
        
        Args:
            data: Données à sauvegarder
            force: Force la sauvegarde immédiate
            priority: Niveau de priorité ("critical", "high", "normal")
            
        Returns:
            True si la sauvegarde a réussi
        """
        with self._cache_lock:
            # Mettre à jour le cache
            self._cache = data.copy()
            self._cache_timestamp = time.time()
            
            # Tracker les modifications pour le batch saving
            self._pending_changes.update(data)
            self._change_count += 1
        
        # Sauvegarder immédiatement si requis
        if force or priority == "critical" or self._should_force_save():
            return self._save_immediately(data, force=force)
        
        # Sinon, programmer pour le batch saving
        return True
    
    def _should_force_save(self) -> bool:
        """Détermine si une sauvegarde forcée est nécessaire."""
        return (
            self._change_count >= self.force_save_threshold or
            (time.time() - self._last_save_time) > 30  # Force après 30 secondes
        )
    
    def _save_immediately(self, data: Dict[str, Any], force: bool = False) -> bool:
        """Sauvegarde immédiate sur disque."""
        try:
            success = self._save_to_disk(data)
            if success:
                self.stats['saves_forced' if force else 'saves_total'] += 1
                self._reset_batch_state()
            return success
            
        except Exception:
            # Erreur silencieuse pour éviter le spam
            self.stats['errors'] += 1
            return False
    
    def _save_to_disk(self, data: Dict[str, Any]) -> bool:
        """Écrit les données sur le disque de manière thread-safe avec formatage optimisé."""
        with self._save_lock:
            temp_path = None
            try:
                # Créer le répertoire si nécessaire
                os.makedirs(os.path.dirname(self.savegame_path), exist_ok=True)
                
                # Essayer d'appliquer le formatage optimisé, fallback vers JSON standard
                try:
                    from app.data_manager import format_savegame_json
                    formatted_json = format_savegame_json(data)
                except Exception:
                    # Fallback vers JSON standard si le formatage échoue
                    import json
                    formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
                
                # Sauvegarde atomique avec fichier temporaire
                temp_path = f"{self.savegame_path}.tmp"
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(formatted_json)
                
                # Remplacer le fichier original
                if os.path.exists(self.savegame_path):
                    os.replace(temp_path, self.savegame_path)
                else:
                    os.rename(temp_path, self.savegame_path)
                
                self._last_save_time = time.time()
                return True
                
            except (PermissionError, OSError, IOError):
                # Erreurs d'accès silencieuses
                return False
            except Exception:
                # Autres erreurs silencieuses
                return False
            finally:
                # Nettoyer le fichier temporaire si nécessaire
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
    
    def _batch_save_worker(self):
        """Worker thread pour les sauvegardes en batch."""
        while self._running:
            try:
                time.sleep(self.batch_save_interval)
                
                if self._pending_changes and self._change_count > 0:
                    with self._cache_lock:
                        if self._cache is not None:
                            # Sauvegarder les changements accumulés
                            success = self._save_to_disk(self._cache)
                            if success:
                                self.stats['saves_batch'] += 1
                                self._reset_batch_state()
                                
            except Exception as e:
                self.stats['errors'] += 1
                print(f"Erreur dans le batch save worker: {e}")
    
    def _reset_batch_state(self):
        """Remet à zéro l'état du batch saving."""
        self._pending_changes.clear()
        self._change_count = 0
        self._last_save_time = time.time()
    
    def _create_default_savegame(self) -> Dict[str, Any]:
        """Crée un savegame par défaut."""
        return {
            "cities": {},
            "players": {},
            "ships": {},
            "transports": {},
            "diplomacy": {},
            "research": {},
            "world": {
                "current_time": time.time(),
                "last_update": time.time()
            },
            "metadata": {
                "created": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
    
    def invalidate_cache(self):
        """Force l'invalidation du cache."""
        with self._cache_lock:
            self._cache = None
            self._cache_timestamp = 0
    
    def flush_pending_saves(self) -> bool:
        """Force la sauvegarde de tous les changements en attente."""
        with self._cache_lock:
            if self._cache is not None and self._change_count > 0:
                return self._save_immediately(self._cache, force=True)
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de performance."""
        cache_hit_rate = 0
        if self.stats['cache_hits'] + self.stats['cache_misses'] > 0:
            cache_hit_rate = self.stats['cache_hits'] / (self.stats['cache_hits'] + self.stats['cache_misses'])
        
        return {
            **self.stats,
            'cache_hit_rate': f"{cache_hit_rate:.2%}",
            'pending_changes': self._change_count,
            'cache_age': time.time() - self._cache_timestamp if self._cache else 0
        }
    
    def shutdown(self):
        """Arrêt propre du service."""
        self._running = False
        self.flush_pending_saves()
        if self._batch_thread.is_alive():
            self._batch_thread.join(timeout=5.0)


# Instance globale du service
_save_service: Optional[SaveService] = None

def get_save_service() -> SaveService:
    """Retourne l'instance globale du SaveService."""
    global _save_service
    if _save_service is None:
        _save_service = SaveService()
    return _save_service

def init_save_service(savegame_path: str = "gamedata/savegame.json") -> SaveService:
    """Initialise le SaveService avec un chemin spécifique."""
    global _save_service
    _save_service = SaveService(savegame_path)
    return _save_service

# Fonctions de compatibilité pour remplacer les accès directs
def load_savegame() -> Dict[str, Any]:
    """Fonction de compatibilité pour load_savegame."""
    return get_save_service().get_savegame()

def save_savegame(data: Dict[str, Any], force: bool = False) -> bool:
    """Fonction de compatibilité pour save_savegame."""
    priority = "critical" if force else "normal"
    return get_save_service().save_savegame(data, force=force, priority=priority)
