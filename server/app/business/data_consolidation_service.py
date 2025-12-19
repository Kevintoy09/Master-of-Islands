"""
DATA_CONSOLIDATION_SERVICE.PY - Service de consolidation des données
====================================================================

Service responsable de la consolidation et synchronisation des données
entre les différents fichiers JSON pour éliminer les duplications.
"""

from typing import Dict, List, Optional, Any
import json
import os
from ..data_manager import DataManager
from ..core.exceptions import GameValidationError

class DataConsolidationService:
    """Service de consolidation des sources de données multiples"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def get_city_complete_data(self, city_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les données complètes d'une ville en consolidant:
        - universe.json (définition statique)
        - savegame.json (état dynamique)
        """
        # Données statiques depuis universe.json
        universe_data = self.data_manager.load_universe()
        static_city = self._find_city_in_universe(city_id, universe_data)
        
        if not static_city:
            return None
        
        # Données dynamiques depuis savegame.json
        savegame_data = self.data_manager.load_savegame()
        dynamic_city = self._find_city_in_savegame(city_id, savegame_data)
        
        # Consolider les données
        consolidated_city = {
            # Données statiques (universe.json)
            'id': static_city['id'],
            'name': static_city['name'],
            'city_coords': static_city.get('city_coords', [0, 0]),
            'controlable': static_city.get('controlable', True),
            
            # Données dynamiques (savegame.json) 
            'owner': dynamic_city.get('owner') if dynamic_city else None,
            'resources': dynamic_city.get('resources', {}) if dynamic_city else {},
            'buildings': dynamic_city.get('buildings', []) if dynamic_city else [],
            'workers_assigned': dynamic_city.get('workers_assigned', {}) if dynamic_city else {},
            'satisfaction': dynamic_city.get('satisfaction', 100) if dynamic_city else 100,
            
            # Données consolidées depuis l'île parente
            'island_id': self._get_island_id_for_city(city_id, universe_data),
            'city_layout': self._get_city_layout_for_city(city_id, universe_data),
            'base_resource': self._get_base_resource_for_city(city_id, universe_data)
        }
        
        return consolidated_city
    
    def get_player_cities(self, player_id: str) -> List[str]:
        """Récupère toutes les villes possédées par un joueur"""
        savegame_data = self.data_manager.load_savegame()
        
        if not savegame_data or 'cities' not in savegame_data:
            return []
        
        player_cities = []
        for city in savegame_data['cities']:
            if city.get('owner') == player_id:
                player_cities.append(city['id'])
        
        return player_cities
    
    def consolidate_player_data(self, player_id: str) -> Optional[Dict[str, Any]]:
        """
        Consolide les données d'un joueur depuis:
        - players.json (profil, recherche)
        - savegame.json (villes possédées)
        """
        # Données de profil depuis players.json
        players_data = self.data_manager.load_players()
        player_profile = players_data.get(player_id)
        
        if not player_profile:
            return None
        
        # Villes possédées depuis savegame.json
        player_cities = self.get_player_cities(player_id)
        
        # Consolider
        consolidated_player = {
            **player_profile,  # Profil complet
            'cities_owned': player_cities,  # Villes possédées
            'cities_count': len(player_cities)  # Nombre de villes
        }
        
        return consolidated_player
    
    def _find_city_in_universe(self, city_id: str, universe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Trouve une ville dans universe.json"""
        for island in universe_data.get('islands', []):
            for element in island.get('elements', []):
                if element.get('type') == 'city' and element.get('id') == city_id:
                    return element
        return None
    
    def _find_city_in_savegame(self, city_id: str, savegame_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Trouve une ville dans savegame.json"""
        if not savegame_data or 'cities' not in savegame_data:
            return None
        
        for city in savegame_data['cities']:
            if city.get('id') == city_id:
                return city
        return None
    
    def _get_island_id_for_city(self, city_id: str, universe_data: Dict[str, Any]) -> Optional[str]:
        """Récupère l'ID de l'île contenant la ville"""
        for island in universe_data.get('islands', []):
            for element in island.get('elements', []):
                if element.get('type') == 'city' and element.get('id') == city_id:
                    return island['id']
        return None
    
    def _get_city_layout_for_city(self, city_id: str, universe_data: Dict[str, Any]) -> Optional[str]:
        """Récupère le layout de la ville depuis son île"""
        for island in universe_data.get('islands', []):
            for element in island.get('elements', []):
                if element.get('type') == 'city' and element.get('id') == city_id:
                    return island.get('city_layout')
        return None
    
    def _get_base_resource_for_city(self, city_id: str, universe_data: Dict[str, Any]) -> Optional[str]:
        """Récupère la ressource de base de la ville depuis son île"""
        for island in universe_data.get('islands', []):
            for element in island.get('elements', []):
                if element.get('type') == 'city' and element.get('id') == city_id:
                    return island.get('base_resource')
        return None
    
    def validate_data_consistency(self) -> Dict[str, List[str]]:
        """Valide la cohérence entre les différentes sources de données"""
        issues = {
            'missing_cities': [],
            'orphaned_cities': [],
            'invalid_owners': []
        }
        
        universe_data = self.data_manager.load_universe()
        savegame_data = self.data_manager.load_savegame()
        players_data = self.data_manager.load_players()
        
        # Vérifier que toutes les villes de universe existent en savegame
        universe_cities = self._extract_city_ids_from_universe(universe_data)
        savegame_cities = self._extract_city_ids_from_savegame(savegame_data)
        
        for city_id in universe_cities:
            if city_id not in savegame_cities:
                issues['missing_cities'].append(city_id)
        
        # Vérifier qu'il n'y a pas de villes orphelines en savegame
        for city_id in savegame_cities:
            if city_id not in universe_cities:
                issues['orphaned_cities'].append(city_id)
        
        # Vérifier que tous les propriétaires existent
        for city in savegame_data.get('cities', []):
            owner = city.get('owner')
            if owner and owner not in players_data:
                issues['invalid_owners'].append(f"{city.get('id')} -> {owner}")
        
        return issues
    
    def _extract_city_ids_from_universe(self, universe_data: Dict[str, Any]) -> List[str]:
        """Extrait tous les IDs de villes depuis universe.json"""
        city_ids = []
        for island in universe_data.get('islands', []):
            for element in island.get('elements', []):
                if element.get('type') == 'city':
                    city_ids.append(element.get('id'))
        return city_ids
    
    def _extract_city_ids_from_savegame(self, savegame_data: Dict[str, Any]) -> List[str]:
        """Extrait tous les IDs de villes depuis savegame.json"""
        if not savegame_data or 'cities' not in savegame_data:
            return []
        
        return [city.get('id') for city in savegame_data['cities'] if city.get('id')]
