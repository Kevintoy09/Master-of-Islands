"""
BUILDING_MANAGER.PY - Gestionnaire métier pour la gestion des bâtiments
Simplifié pour utiliser le nouveau modèle Building
"""

from typing import Dict, List, Optional, Any
from ..models.building_simplified import Building
from ..data_manager import DataManager
from ..core.exceptions import GameValidationError, InsufficientResourcesError
from .notification_service import NotificationService
from ..models.notification import NotificationType

class BuildingManager:
    """Gestionnaire simplifié pour la gestion des bâtiments"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.notification_service = NotificationService(data_manager)
    
    def create_building(self, slot_id: str, building_name: str, level: int = 1) -> Building:
        """Crée un nouveau bâtiment"""
        # Charger la configuration des bâtiments
        buildings_data = self.data_manager.load_buildings()
        
        if building_name not in buildings_data:
            raise GameValidationError(f"Bâtiment inconnu: {building_name}")
        
        # Créer l'instance
        building = Building(
            slot_id=slot_id,
            name=building_name,
            level=level
        )
        
        # NOTE: On ne charge PAS les effects ici car:
        # - Les effects ne sont plus sauvegardés dans savegame.json (optimisation)
        # - Ils sont recalculés dynamiquement par tick_service et game_logic
        # building.update_from_config(buildings_data)  # DÉSACTIVÉ
        
        return building
    
    def start_construction(self, building: Building, buildings_data: Dict[str, Any]) -> Building:
        """Démarre la construction d'un bâtiment"""
        if building.name not in buildings_data:
            raise GameValidationError(f"Configuration manquante pour {building.name}")
        
        # Récupérer la durée de construction
        building_config = buildings_data[building.name]
        levels = building_config.get('levels', [])
        
        if 0 < building.level <= len(levels):
            level_data = levels[building.level - 1]
            duration = level_data.get('construction_time', 30)
            building.start_construction(duration)
        
        return building
    
    def check_construction_requirements(self, building_name: str, player_data: Dict[str, Any]) -> bool:
        """Vérifie si le joueur peut construire ce bâtiment (recherche)"""
        buildings_data = self.data_manager.load_buildings()
        
        if building_name not in buildings_data:
            return False
        
        building_config = buildings_data[building_name]
        required_research = building_config.get('required_research')
        
        if not required_research:
            return True
        
        unlocked_research = player_data.get('unlocked_research', [])
        return required_research in unlocked_research
    
    def calculate_construction_cost(self, building_name: str, level: int = 1) -> Dict[str, int]:
        """Calcule le coût de construction d'un bâtiment"""
        buildings_data = self.data_manager.load_buildings()
        
        if building_name not in buildings_data:
            return {}
        
        building_config = buildings_data[building_name]
        levels = building_config.get('levels', [])
        
        if 0 < level <= len(levels):
            level_data = levels[level - 1]
            return level_data.get('cost', {})
        
        return {}
    
    def check_resources(self, city_resources: Dict[str, int], cost: Dict[str, int]) -> Dict[str, int]:
        """Vérifie si les ressources sont suffisantes, retourne les manquantes"""
        missing = {}
        
        for resource, amount in cost.items():
            available = city_resources.get(resource, 0)
            if available < amount:
                missing[resource] = amount - available
        
        return missing
    
    def update_completed_buildings(self, buildings: List[Building], player_id: str, city_name: str) -> List[Building]:
        """Met à jour le statut des bâtiments terminés et crée des notifications"""
        for building in buildings:
            print(f"🏗️ Bâtiment {building.name}: remaining_time={building.remaining_time}, status='{building.status}'")
            # Vérifier si le bâtiment vient de se terminer (remaining_time = 0 mais status pas encore "Terminé")
            if building.remaining_time == 0 and building.status != "Terminé":
                print(f"✅ Bâtiment {building.name} terminé ! Création de notification...")
                # Marquer le bâtiment comme terminé
                building.complete()
                
                # Créer une notification de construction terminée
                self._create_building_notification(player_id, building.name, city_name)
        
        return buildings
    
    def _create_building_notification(self, player_id: str, building_name: str, city_name: str):
        """Crée une notification pour la fin de construction d'un bâtiment"""
        try:
            print(f"🔔 Création notification bâtiment: {building_name} dans {city_name} pour {player_id}")
            self.notification_service.create_building_notification(
                player_id=player_id,
                building_name=building_name,
                city_name=city_name
            )
            print(f"✅ Notification créée avec succès !")
        except Exception as e:
            print(f"❌ Erreur lors de la création de la notification de bâtiment: {e}")
    
    def buildings_to_dict_list(self, buildings: List[Building]) -> List[Dict[str, Any]]:
        """Convertit une liste de bâtiments en liste de dictionnaires"""
        return [building.to_dict() for building in buildings]
    
    def buildings_from_dict_list(self, buildings_data: List[Dict[str, Any]]) -> List[Building]:
        """Convertit une liste de dictionnaires en liste de bâtiments
        
        NOTE: On ne charge PAS les effects depuis buildings.json car:
        - Les effects ne sont plus sauvegardés dans savegame.json (optimisation)
        - Ils sont recalculés dynamiquement par tick_service et game_logic
        """
        buildings = []
        
        for building_dict in buildings_data:
            building = Building.from_dict(building_dict)
            # PAS d'update_from_config() pour éviter de polluer le savegame avec 'effect'
            buildings.append(building)
        
        return buildings
    
    def apply_architect_bonuses_to_cost(self, base_cost: Dict[str, int], city: Dict[str, Any]) -> Dict[str, int]:
        """Applique les bonus de l'Atelier d'Architecte au coût d'un bâtiment"""
        from ..game_logic import GameLogic
        
        game_logic = GameLogic(self.data_manager)
        architect_bonuses = game_logic.calculate_architect_bonuses(city)
        cost_reduction_percent = architect_bonuses.get('cost_reduction', 0) / 100.0
        
        reduced_cost = {}
        for resource, amount in base_cost.items():
            reduced_amount = int(amount * (1 - cost_reduction_percent))
            reduced_cost[resource] = max(1, reduced_amount)  # Minimum 1 ressource
        
        return reduced_cost
    
    def apply_architect_bonuses_to_time(self, base_time: int, city: Dict[str, Any]) -> int:
        """Applique les bonus de l'Atelier d'Architecte au temps de construction"""
        from ..game_logic import GameLogic
        
        game_logic = GameLogic(self.data_manager)
        architect_bonuses = game_logic.calculate_architect_bonuses(city)
        time_reduction_percent = architect_bonuses.get('time_reduction', 0) / 100.0
        
        reduced_time = int(base_time * (1 - time_reduction_percent))
        return max(1, reduced_time)  # Minimum 1 seconde
