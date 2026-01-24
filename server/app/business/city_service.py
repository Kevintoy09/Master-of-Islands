
"""
=================================================================
CITY_SERVICE.PY - Service métier pour la gestion des villes
=================================================================
import time
import time

RESPONSABILITÉS:
- Logique métier des villes (création, réclamation, état)
- Gestion des bâtiments et constructions
- Interface avec univers.json et savegame.json
- Calculs de ressources et population

MÉTHODES PRINCIPALES:
- get_city_by_id()             → Ville par ID depuis savegame
- get_city_from_universe()     → Ville par ID depuis univers
- create_city_from_universe()  → Création nouvelle ville
- claim_city()                 → Réclamation par joueur
- build_building()             → Construction bâtiment
- get_city_state()             → État complet avec MAJ

RÈGLES D'USAGE:
✓ Utiliser pour toute logique métier des villes
✓ GameLogic pour calculs complexes  
✓ Validators pour validation données
✓ Exceptions appropriées pour erreurs

DÉPENDANCES:
- DataManager → Accès fichiers données
- GameLogic → Calculs population/production
- Validators/Exceptions → Validation/gestion erreurs
=================================================================
"""


from typing import Dict, List, Optional, Any
from ..data_manager import DataManager
from ..game_logic import GameLogic
from ..core.exceptions import CityNotFoundError, GameValidationError, InsufficientResourcesError
from ..core.validators import validate_city_data
from ..city_constants import DEFAULT_CITY_RESOURCES
from .building_manager import BuildingManager
from .data_consolidation_service import DataConsolidationService
from ..models.building_simplified import Building
import time

class CityService:
    def upgrade_building(self, city_id: str, slot_id: str) -> Dict:
        """Lance l'amélioration d'un bâtiment (upgrade) en conservant les effets du niveau actuel jusqu'à la fin du timer."""
        # Charger le savegame UNE SEULE FOIS au début
        savegame_data = self.data_manager.load_savegame()
        
        # Trouver la ville dans le savegame
        city = next((c for c in savegame_data.get('cities', []) if c['id'] == city_id), None)
        if not city:
            raise CityNotFoundError(city_id)
            
        building = next((b for b in city['buildings'] if b.get('slot_id') == slot_id), None)
        if not building:
            raise GameValidationError("Aucun bâtiment à cet emplacement")
        
        # Vérifier si un upgrade est déjà en cours
        if building.get('upgrade_in_progress'):
            raise GameValidationError("Un upgrade est déjà en cours pour ce bâtiment")
        
        current_level = building.get('level', 1)
        buildings_data = self.data_manager.load_buildings()
        building_config = buildings_data.get(building['name'])
        levels = building_config.get('levels', [])
        if current_level >= len(levels):
            raise GameValidationError("Niveau max atteint")
        
        # Calculer le coût de l'upgrade (niveau suivant)
        next_level = current_level + 1
        upgrade_cost = levels[next_level - 1].get('cost', {})
        
        # Appliquer les bonus de l'Atelier d'Architecte
        actual_cost = self.building_manager.apply_architect_bonuses_to_cost(upgrade_cost, city)
        
        # Vérifier les ressources disponibles
        city_resources = city.get('resources', {})
        missing = self.building_manager.check_resources(city_resources, actual_cost)
        
        if missing:
            missing_str = ', '.join([f"{res}: {amt}" for res, amt in missing.items()])
            raise InsufficientResourcesError(f"Ressources insuffisantes pour l'upgrade - Manquant: {missing_str}")
        
        # Déduire les ressources
        for resource, amount in actual_cost.items():
            city_resources[resource] = city_resources.get(resource, 0) - amount
        
        # Calculer le temps d'upgrade avec bonus architecte + multiplicateur global
        upgrade_time = levels[next_level - 1].get('construction_time', 30)
        actual_time = self.game_logic.apply_architect_bonuses_to_building_time(upgrade_time, city)
        
        # Lancer le timer d'amélioration
        building['upgrade_in_progress'] = True
        building['upgrade_end_time'] = int(time.time()) + actual_time
        
        # Les effets restent ceux du niveau actuel pendant l'upgrade
        
        # Sauvegarder IMMÉDIATEMENT (force_save=True) pour éviter la boucle IA
        self.data_manager.save_savegame(savegame_data, force_save=True)
        return building

    def complete_upgrade(self, city_id: str, slot_id: str) -> Dict:
        """Termine l'amélioration d'un bâtiment : passage au niveau supérieur et application des nouveaux effets."""
        city = self.get_city_by_id(city_id)
        if not city:
            raise CityNotFoundError(city_id)
        building = next((b for b in city['buildings'] if b.get('slot_id') == slot_id), None)
        if not building or not building.get('upgrade_in_progress'):
            raise GameValidationError("Aucune amélioration en cours")
        current_level = building.get('level', 1)
        buildings_data = self.data_manager.load_buildings()
        building_config = buildings_data.get(building['name'])
        levels = building_config.get('levels', [])
        if current_level >= len(levels):
            raise GameValidationError("Niveau max atteint")
        # Passage au niveau supérieur
        building['level'] = current_level + 1
        building.pop('upgrade_in_progress', None)
        building.pop('upgrade_end_time', None)
        
        # Les effets seront recalculés dynamiquement par tick_service et game_logic
        # Pas besoin de les sauvegarder dans le JSON
        
        # Sauvegarder l'état modifié IMMÉDIATEMENT
        savegame_data = self.data_manager.load_savegame()
        for c in savegame_data.get('cities', []):
            if c['id'] == city_id:
                c['buildings'] = city['buildings']
        self.data_manager.save_savegame(savegame_data, force_save=True)
        return building
    """Service pour la gestion des villes"""
    
    def __init__(self, data_manager: DataManager, game_logic: GameLogic, population_manager=None):
        self.data_manager = data_manager
        self.game_logic = game_logic
        self.population_manager = population_manager
        self.building_manager = BuildingManager(data_manager)
        self.data_consolidation = DataConsolidationService(data_manager)
    
    def _ensure_savegame_structure(self, savegame_data: Dict) -> Dict:
        """S'assure que la structure de la sauvegarde est correcte"""
        if not savegame_data:
            savegame_data = {"cities": [], "players": {}}
        
        # S'assurer que cities est une liste
        if 'cities' not in savegame_data or not isinstance(savegame_data['cities'], list):
            savegame_data['cities'] = []
        
        # S'assurer que players est un dictionnaire
        if 'players' not in savegame_data or not isinstance(savegame_data['players'], dict):
            savegame_data['players'] = {}
        
        return savegame_data
    
    def _ensure_player_cities_structure(self, player_data: Dict) -> None:
        """S'assure que la structure des villes du joueur est correcte"""
        if 'cities' not in player_data:
            player_data['cities'] = []
        
        # S'assurer que cities est une liste et non un dictionnaire
        cities = player_data['cities']
        if not isinstance(cities, list):
            if isinstance(cities, dict):
                player_data['cities'] = list(cities.keys())
            else:
                player_data['cities'] = []
    
    def get_city_by_id(self, city_id: str) -> Optional[Dict]:
        """Récupère une ville par son ID"""
        savegame_data = self.data_manager.load_savegame()
        if not savegame_data:
            return None
        
        return next(
            (c for c in savegame_data.get('cities', []) if c['id'] == city_id), 
            None
        )
    
    def get_city_from_universe(self, city_id: str) -> Optional[Dict]:
        """Récupère une ville depuis l'univers"""
        universe = self.data_manager.load_universe()
        
        for island in universe.get('islands', []):
            for element in island.get('elements', []):
                if element.get('type') == 'city' and element.get('id') == city_id:
                    return element
        return None
    
    def create_city_from_universe(self, city_id: str, player_id: str) -> Dict:
        """Crée une ville à partir des données de l'univers"""
        # Récupérer les données de l'univers
        city_data = self.get_city_from_universe(city_id)
        if not city_data:
            raise CityNotFoundError(city_id)
        
        # Trouver l'île parent
        universe = self.data_manager.load_universe()
        island = None
        for isl in universe.get('islands', []):
            if any(el.get('id') == city_id for el in isl.get('elements', [])):
                island = isl
                break
        
        if not island:
            raise GameValidationError("Île parent introuvable")
        
        # Créer la ville avec les données par défaut
        new_city = {
            'id': city_data['id'],
            'owner': player_id,
            'name': city_data.get('name', ''),
            'island_id': island['id'],
            'city_layout': island.get('city_layout'),
            'base_resource': island.get('base_resource'),
            'resources': DEFAULT_CITY_RESOURCES.copy(),
            'storage_capacity': {},
            'buildings': [],
            'workers_assigned': {},
            'controlable': city_data.get('controlable', True),
            'gold_rate': 1,
            'windmill_cereal_bonus': 0,
            'has_plague': False
        }
        
        # Valider et sauvegarder
        validate_city_data(new_city)
        
        # Charger directement via DataManager
        savegame_data = self.data_manager.load_savegame()
        savegame_data = self._ensure_savegame_structure(savegame_data)

        # ⚠️ PROTECTION ANTI-DOUBLON : Vérifier que la ville n'existe pas déjà
        existing_city = next((c for c in savegame_data['cities'] if c.get('id') == city_id), None)
        if existing_city:
            # Assigner le propriétaire si pas déjà fait
            if not existing_city.get('owner') or existing_city.get('owner') == "":
                existing_city['owner'] = player_id
                self.data_manager.save_savegame(savegame_data, force_save=True)
            return existing_city
        
        savegame_data['cities'].append(new_city)
        
        # Note: La gestion des joueurs se fait dans players.json, pas dans savegame.json
        # Le DataManager nettoie automatiquement la section 'players' du savegame
        
        # Utiliser directement data_manager au lieu de save_savegame_transition
        success = self.data_manager.save_savegame(savegame_data, force_save=True)
        if not success:
            raise GameValidationError("Impossible de sauvegarder la ville")
        
        return new_city
    
    def claim_city(self, city_id: str, player_id: str) -> Dict:
        """Récupère une ville pour un joueur"""
        # Charger directement via DataManager
        savegame_data = self.data_manager.load_savegame()
        savegame_data = self._ensure_savegame_structure(savegame_data)
        
        # Vérifier si la ville existe déjà
        city = self.get_city_by_id(city_id)
        
        if city:
            # Vérifier qu'elle n'est pas déjà prise
            if city.get('owner') and city.get('owner') != "":
                raise GameValidationError("Cette ville est déjà réclamée")
            
            # Assigner au joueur
            city['owner'] = player_id
            
            # Note: La gestion des joueurs se fait dans players.json via PlayerService
            # Le savegame contient uniquement les villes avec leur 'owner'
            
            # Sauvegarder directement via DataManager
            success = self.data_manager.save_savegame(savegame_data, force_save=True)
            if not success:
                raise GameValidationError("Impossible de sauvegarder")
            
            return city
        else:
            # Créer la ville depuis l'univers
            return self.create_city_from_universe(city_id, player_id)
    
    def build_building(self, city_id: str, slot_id: str, building_name: str) -> Dict:
        """Construit un bâtiment dans une ville"""
        # Charger le savegame une seule fois et garder la référence
        savegame_data = self.data_manager.load_savegame()
        city = next((c for c in savegame_data.get('cities', []) if c['id'] == city_id), None)
        if not city:
            raise CityNotFoundError(city_id)
        
        # Récupérer le joueur propriétaire
        player_id = city.get('owner')
        if not player_id:
            raise GameValidationError("Impossible de déterminer le propriétaire de la ville")
        
        players_data = self.data_manager.load_players()
        players_list = players_data.get('players', [])
        player = next((p for p in players_list if p.get('id') == str(player_id)), None)
        if not player:
            raise GameValidationError("Joueur introuvable")
        
        # Vérifier les prérequis de recherche
        if not self.building_manager.check_construction_requirements(building_name, player):
            raise GameValidationError(f"Recherche requise non débloquée pour {building_name}")
        
        # Vérifier que le slot est libre
        if 'buildings' not in city:
            city['buildings'] = []
        
        # S'assurer que buildings est une liste
        if not isinstance(city['buildings'], list):
            city['buildings'] = []
        
        if any(b.get('slot_id') == slot_id for b in city['buildings']):
            raise GameValidationError("Ce slot contient déjà un bâtiment")
        
        # Vérifier le nombre maximum d'instances
        buildings_data = self.data_manager.load_buildings()
        building_config = buildings_data.get(building_name, {})
        max_instances = building_config.get('max_instances', 999)
        current_instances = len([b for b in city['buildings'] 
                                if b.get('name') == building_name 
                                and b.get('status') != 'En démolition'])
        
        if current_instances >= max_instances:
            raise GameValidationError(f"Limite atteinte ! Maximum {max_instances} {building_name}(s) par ville")
        
        # Calculer le coût de base et appliquer les bonus architecte
        base_cost = self.building_manager.calculate_construction_cost(building_name, level=1)
        actual_cost = self.building_manager.apply_architect_bonuses_to_cost(base_cost, city)
        
        city_resources = city.get('resources', {})
        missing = self.building_manager.check_resources(city_resources, actual_cost)
        
        if missing:
            raise InsufficientResourcesError(missing)
        
        # Déduire les ressources (coût réduit par les bonus)
        for resource, amount in actual_cost.items():
            city_resources[resource] = city_resources.get(resource, 0) - amount
        
        # Créer le bâtiment et calculer le temps de construction avec bonus
        building = self.building_manager.create_building(slot_id, building_name, level=1)
        buildings_data = self.data_manager.load_buildings()
        
        # Récupérer le temps de base et appliquer les bonus architecte + multiplicateur global
        building_config = buildings_data[building_name]
        levels = building_config.get('levels', [])
        base_time = levels[0].get('construction_time', 30) if levels else 30
        
        # Utiliser GameLogic pour appliquer TOUS les bonus (multiplicateur global + architecte + faction)
        actual_time = self.game_logic.apply_architect_bonuses_to_building_time(base_time, city)
        
        # Démarrer la construction avec le temps réduit
        building.start_construction(actual_time)
        
        # Ajouter le bâtiment à la ville
        city['buildings'].append(building.to_dict())
        
        # Sauvegarder IMMÉDIATEMENT (force_save=True) pour éviter la boucle IA
        save_success = self.data_manager.save_savegame(savegame_data, force_save=True)
        
        if not save_success:
            raise GameValidationError("Impossible de sauvegarder")
        
        return {
            'success': True,
            'message': f'{building_name} en construction sur le slot {slot_id}',
            'construction_end': building.construction_end
        }
    
    def get_city_state(self, city_id: str) -> Dict:
        """Récupère l'état complet d'une ville avec mise à jour"""
        print(f"🏙️ get_city_state appelé pour ville {city_id}")
        
        # FORCE: Mettre à jour TOUS les bâtiments de TOUTES les villes
        print("🔄 FORCE: Mise à jour de tous les bâtiments de toutes les villes")
        self.update_all_buildings_status()
        
        # Mettre à jour la production - DÉSACTIVÉ: utilise ManualTickService maintenant
        # self.game_logic.update_resource_production()
        
        # Récupérer la ville
        city = self.get_city_by_id(city_id)
        if not city:
            raise CityNotFoundError(city_id)
        
        # Mettre à jour les bâtiments terminés
        if 'buildings' in city and city['buildings']:
            buildings = self.building_manager.buildings_from_dict_list(city['buildings'])
            buildings = self.building_manager.update_completed_buildings(buildings, city.get('player_id', 'player_1'), city.get('name', 'Ville'))
            city['buildings'] = self.building_manager.buildings_to_dict_list(buildings)
        
        # Mettre à jour la population libre
        city['resources']['population_free'] = self.game_logic.calculate_actual_free_population(city)
        
        # Sauvegarder les changements
        savegame_data = self.data_manager.load_savegame()
        self.data_manager.save_savegame(savegame_data)
        
        return city
    
    def update_all_constructions(self) -> bool:
        """Met à jour toutes les constructions terminées dans toutes les villes"""
        savegame_data = self.data_manager.load_savegame()
        if not savegame_data or 'cities' not in savegame_data:
            return False
        
        has_changes = False
        
        for city in savegame_data['cities']:
            if 'buildings' in city and city['buildings']:
                # Convertir les bâtiments et vérifier les constructions terminées
                buildings = self.building_manager.buildings_from_dict_list(city['buildings'])
                updated_buildings = self.building_manager.update_completed_buildings(buildings, city.get('player_id', 'player_1'), city.get('name', 'Ville'))
                
                # Reconvertir en dictionnaires
                new_buildings_data = self.building_manager.buildings_to_dict_list(updated_buildings)
                
                # Vérifier s'il y a eu des changements
                if new_buildings_data != city['buildings']:
                    city['buildings'] = new_buildings_data
                    has_changes = True
        
        # Sauvegarder si des changements ont été effectués
        if has_changes:
            return self.data_manager.save_savegame(savegame_data)
        
        return True
    
    def get_city_consolidated(self, city_id: str) -> Dict:
        """
        Récupère l'état consolidé d'une ville depuis toutes les sources
        NOUVEAU: Utilise DataConsolidationService pour éliminer les duplications
        """
        city = self.data_consolidation.get_city_complete_data(city_id)
        if not city:
            raise CityNotFoundError(city_id)
        
        # Mettre à jour la production - DÉSACTIVÉ: utilise ManualTickService maintenant
        # self.game_logic.update_resource_production()
        
        # Mettre à jour les bâtiments terminés si la ville a des bâtiments
        if city.get('buildings'):
            buildings = self.building_manager.buildings_from_dict_list(city['buildings'])
            buildings = self.building_manager.update_completed_buildings(buildings, city.get('player_id', 'player_1'), city.get('name', 'Ville'))
            city['buildings'] = self.building_manager.buildings_to_dict_list(buildings)
        
        # Mettre à jour la population libre
        city['resources']['population_free'] = self.game_logic.calculate_actual_free_population(city)
        
        return city
    
    def validate_data_consistency(self) -> Dict[str, List[str]]:
        """Valide la cohérence des données entre les fichiers"""
        return self.data_consolidation.validate_data_consistency()
    
    def get_player_cities_consolidated(self, player_id: str) -> List[Dict[str, Any]]:
        """Récupère toutes les villes d'un joueur avec données consolidées"""
        city_ids = self.data_consolidation.get_player_cities(player_id)
        cities = []
        
        for city_id in city_ids:
            try:
                city = self.get_city_consolidated(city_id)
                cities.append(city)
            except CityNotFoundError:
                # Log l'erreur mais continue avec les autres villes
                continue
        
        return cities

    def update_all_buildings_status(self) -> Dict[str, int]:
        """Met à jour le statut de tous les bâtiments dans toutes les villes"""
        updated_count = 0
        cities_processed = 0
        
        try:
            savegame_data = self.data_manager.load_savegame()
            cities = savegame_data.get('cities', [])
            
            for city in cities:
                if 'buildings' in city and city['buildings']:
                    cities_processed += 1
                    buildings = self.building_manager.buildings_from_dict_list(city['buildings'])
                    
                    # Mettre à jour les bâtiments
                    updated_buildings = self.building_manager.update_completed_buildings(
                        buildings, 
                        city.get('player_id', 'player_1'), 
                        city.get('name', 'Ville')
                    )
                    
                    # Compter les bâtiments nouvellement terminés
                    new_completed = len([b for b in updated_buildings if b.status == "Terminé"]) - len([b for b in buildings if b.status == "Terminé"])
                    updated_count += new_completed
                    
                    # Sauvegarder si des changements ont eu lieu
                    if new_completed > 0:
                        city['buildings'] = self.building_manager.buildings_to_dict_list(updated_buildings)
                        
            # Sauvegarder les changements
            if updated_count > 0:
                self.data_manager.save_savegame(savegame_data)
                
            return {
                'cities_processed': cities_processed,
                'buildings_completed': updated_count
            }
            
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour des bâtiments: {e}")
            return {'cities_processed': 0, 'buildings_completed': 0}
