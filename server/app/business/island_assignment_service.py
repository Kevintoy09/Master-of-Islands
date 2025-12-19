"""
=================================================================
ISLAND_ASSIGNMENT_SERVICE.PY - Service pour l'affectation des îles
=================================================================

RESPONSABILITÉS:
- Gestion de l'affectation des îles aux nouveaux joueurs
- Application de la règle "maximum 4 joueurs par île"
- Support pour la logique automatique dans city_routes.py

LOGIQUE D'AFFECTATION:
1. Le joueur choisit un type de ressource de base (stone, iron, cereal, papyrus)
2. Le système trouve la première île de ce type avec moins de 4 joueurs
3. Si toutes les îles sont pleines, propose la prochaine île du même type

MÉTHODES PRINCIPALES:
- get_island_player_count()          → Nombre de joueurs sur une île
- get_available_islands_by_resource() → Îles disponibles par ressource
- suggest_city_for_player()          → Suggère une ville libre sur l'île

RÈGLES D'USAGE:
✓ Maximum 4 joueurs par île
✓ Affectation chronologique (ordre des îles dans universe.json)
✓ Respect du choix de ressource du joueur

NOTE: La logique principale d'affectation est intégrée dans /api/city/colonize
=================================================================
"""

from typing import Dict, List, Optional, Tuple
from ..data_manager import DataManager
from ..core.exceptions import GameValidationError

class IslandAssignmentService:
    """Service pour l'affectation des îles aux joueurs"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.max_players_per_island = 4
    
    def get_island_player_count(self, island_id: str) -> int:
        """Compte le nombre de joueurs distincts présents sur une île"""
        savegame_data = self.data_manager.load_savegame()
        if not savegame_data:
            return 0
        
        # Utiliser un set pour compter les joueurs uniques
        unique_players = set()
        for city in savegame_data.get('cities', []):
            if city.get('island_id') == island_id and city.get('owner'):
                unique_players.add(city.get('owner'))
        
        return len(unique_players)
    
    def get_available_islands_by_resource(self, base_resource: str) -> List[Dict]:
        """
        Récupère toutes les îles d'un type de ressource donné,
        triées par ordre de remplissage (moins remplies en premier)
        """
        universe_data = self.data_manager.load_universe()
        if not universe_data or 'islands' not in universe_data:
            return []
        
        # Filtrer les îles par ressource de base
        matching_islands = []
        for island in universe_data['islands']:
            if island.get('base_resource') == base_resource:
                island_id = island.get('id')
                player_count = self.get_island_player_count(island_id)
                
                island_info = {
                    'id': island_id,
                    'name': island.get('name'),
                    'coords': island.get('coords', [0, 0]),
                    'base_resource': island.get('base_resource'),
                    'advanced_resource': island.get('advanced_resource'),
                    'player_count': player_count,
                    'available_slots': self.max_players_per_island - player_count,
                    'is_full': player_count >= self.max_players_per_island
                }
                matching_islands.append(island_info)
        
        # Trier par ID pour respecter l'ordre d'apparition dans universe.json
        # Cela remplit les îles chronologiquement jusqu'à 4 joueurs avant de passer à la suivante
        matching_islands.sort(key=lambda x: x['id'])
        
        return matching_islands
    
    def get_next_available_island(self, base_resource: str) -> Optional[Dict]:
        """
        Trouve la prochaine île disponible pour un type de ressource donné.
        Retourne la première île avec moins de 4 joueurs.
        """
        available_islands = self.get_available_islands_by_resource(base_resource)
        
        for island in available_islands:
            if not island['is_full']:
                return island
        
        # Si toutes les îles sont pleines, retourner None
        return None
    
    def get_available_cities_on_island(self, island_id: str) -> List[Dict]:
        """
        Récupère toutes les villes libres sur une île donnée
        """
        universe_data = self.data_manager.load_universe()
        savegame_data = self.data_manager.load_savegame()
        
        if not universe_data or 'islands' not in universe_data:
            return []
        
        # Trouver l'île dans l'univers
        target_island = None
        for island in universe_data['islands']:
            if island.get('id') == island_id:
                target_island = island
                break
        
        if not target_island:
            return []
        
        # Récupérer les villes de l'île
        available_cities = []
        for element in target_island.get('elements', []):
            if element.get('type') == 'city' and element.get('controlable'):
                city_id = element.get('id')
                
                # Vérifier si la ville est libre
                is_free = True
                if savegame_data:
                    for city in savegame_data.get('cities', []):
                        if city.get('id') == city_id and city.get('owner'):
                            is_free = False
                            break
                
                if is_free:
                    available_cities.append({
                        'id': city_id,
                        'name': element.get('name'),
                        'city_coords': element.get('city_coords'),
                        'island_id': island_id
                    })
        
        return available_cities
    
    def suggest_city_for_player(self, base_resource: str) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Suggère une ville et une île pour un nouveau joueur basé sur sa préférence de ressource.
        
        Returns:
            Tuple[island_info, city_info] : Informations de l'île et de la ville suggérées,
                                           ou (None, None) si aucune ville disponible
        """
        # Trouver la prochaine île disponible
        island = self.get_next_available_island(base_resource)
        if not island:
            return None, None
        
        # Trouver une ville libre sur cette île
        available_cities = self.get_available_cities_on_island(island['id'])
        if not available_cities:
            return island, None
        
        # Retourner la première ville disponible
        suggested_city = available_cities[0]
        
        return island, suggested_city
