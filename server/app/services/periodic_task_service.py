"""
SERVICE DE TIMERS GLOBAUX
========================
Remplace le GameLoopManager supprimé pour gérer tous les éléments pilotés par des timers :
- Transports (loading, traveling, returning)
- Construction de bâtiments
- Upgrades des sites de ressources
- Transports d'unités
- Batailles (timers de tours, actions automatiques)

SÉPARATION CLAIRE :
- TickService → Logique métier (ressources, population, or)
- TimerService → Éléments temporels (timers, countdowns)
"""
import threading
import time
from typing import Dict, Any
from app.data_manager import DataManager
from app.business.transport_timer_service import TransportTimerService
from app.business.battle_timer_service import BattleTimerService

class TimerService:
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.transport_timer = TransportTimerService(data_manager)
        self.battle_timer = BattleTimerService(data_manager)
        self.running = False
        self.thread = None
        self.update_interval = 1.0  # Mise à jour toutes les secondes
        
    def start(self):
        """Démarre les tâches périodiques en arrière-plan"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_timer_updates, daemon=True)
        self.thread.start()
        print("[TIMER] Service de timers globaux demarre")
        
    def stop(self):
        """Arrête les tâches périodiques"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("🛑 Service de timers globaux arrêté")
        
    def _run_timer_updates(self):
        """Boucle principale de mise à jour des timers"""
        while self.running:
            try:
                # 1. Mettre à jour les transports (loading, traveling, returning)
                transport_results = self.transport_timer.update_all_transports()
                
                # 2. Mettre à jour les timers de batailles (tours, actions automatiques)
                battle_results = self.battle_timer.update_all_battles()
                
                # 3. Mettre à jour les timers de construction de bâtiments
                building_results = self._update_building_timers()
                
                # 4. Mettre à jour les timers des sites de ressources
                resource_site_results = self._update_resource_site_timers()
                
                # Attendre avant la prochaine itération
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"❌ Erreur dans les timers: {e}")
                # Continuer malgré l'erreur pour éviter l'arrêt total
                time.sleep(self.update_interval)
                
    def _update_building_timers(self) -> Dict[str, Any]:
        """Met à jour les timers de construction des bâtiments"""
        try:
            # Charger les données des villes
            savegame_data = self.data_manager.load_savegame()
            if not savegame_data:
                return {"updated": 0, "completed": 0}
            
            cities = savegame_data.get('cities', [])
            updated_count = 0
            completed_count = 0
            
            for city in cities:
                buildings = city.get('buildings', [])
                for building in buildings:
                    # Vérifier si le bâtiment est en construction
                    if isinstance(building, dict) and building.get('status') == 'En construction':
                        remaining_time = building.get('remaining_time', 0)
                        if remaining_time > 0:
                            # Décrémenter le timer
                            building['remaining_time'] = max(0, remaining_time - 1)
                            updated_count += 1
                            
                            # Vérifier si terminé
                            if building['remaining_time'] == 0:
                                building['status'] = 'Terminé'
                                completed_count += 1
                                print(f"🏗️ Bâtiment {building.get('name', 'Inconnu')} terminé dans {city.get('name', 'Ville')}")
            
            # Sauvegarder si des changements ont été effectués
            if updated_count > 0:
                self.data_manager.save_savegame(savegame_data)
            
            return {"updated": updated_count, "completed": completed_count}
            
        except Exception as e:
            print(f"❌ Erreur mise à jour timers bâtiments: {e}")
            return {"updated": 0, "completed": 0}
    
    def _update_resource_site_timers(self) -> Dict[str, Any]:
        """Met à jour les timers des sites de ressources"""
        try:
            # Les sites de ressources sont gérés par leur propre service
            # Pour l'instant, on peut laisser vide ou implémenter plus tard
            return {"updated": 0, "completed": 0}
            
        except Exception as e:
            print(f"❌ Erreur mise à jour timers sites: {e}")
            return {"updated": 0, "completed": 0}
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du service"""
        return {
            "running": self.running,
            "thread_alive": self.thread.is_alive() if self.thread else False,
            "update_interval": self.update_interval
        }