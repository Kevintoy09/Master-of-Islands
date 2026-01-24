"""
=================================================================
PLAYER_SERVICE.PY - Service métier pour la gestion des joueurs
=================================================================

RESPONSABILITÉS:
- Logique métier des joueurs (création, authentification)
- Gestion des comptes et sessions
- Relations joueur ↔ villes
- Interface avec players.json et savegame.json

MÉTHODES PRINCIPALES:
- get_player_by_id()           → Joueur par ID
- get_player_by_username()     → Joueur par nom d'utilisateur
- create_player()              → Création nouveau compte
- authenticate_player()        → Authentification/connexion
- get_player_cities()          → Villes possédées
- player_has_city()            → Vérification possession
- get_player_info()            → Informations complètes

RÈGLES D'USAGE:
✓ Utiliser pour toute logique métier des joueurs
✓ Validators pour validation données
✓ Exceptions appropriées pour erreurs
✓ Pas de logique d'affichage ici

DÉPENDANCES:
- DataManager → Accès fichiers données
- Validators → Validation données joueur
- Exceptions → Gestion erreurs métier
=================================================================
"""

from typing import Dict, List, Optional
from ..data_manager import DataManager
from ..core.exceptions import PlayerNotFoundError, GameValidationError
from ..core.validators import validate_player_data

class PlayerService:
    """Service pour la gestion des joueurs"""
    
    def __init__(self, data_manager: DataManager, transport_manager=None):
        self.data_manager = data_manager
        self.transport_manager = transport_manager
    
    def get_player_by_id(self, player_id: str) -> Optional[Dict]:
        """Récupère un joueur par son ID"""
        players_data = self.data_manager.load_players()
        return next(
            (p for p in players_data.get('players', []) if p['id'] == player_id), 
            None
        )
    
    def get_player_by_username(self, username: str) -> Optional[Dict]:
        """Récupère un joueur par son nom d'utilisateur"""
        players_data = self.data_manager.load_players()
        return next(
            (p for p in players_data.get('players', []) if p['username'] == username), 
            None
        )
    
    def create_player(self, username: str) -> Dict:
        """Crée un nouveau joueur avec tous les attributs requis"""
        import time
        
        players_data = self.data_manager.load_players()
        
        # Vérifier l'unicité du nom d'utilisateur
        if self.get_player_by_username(username):
            raise GameValidationError("Ce nom d'utilisateur existe déjà")
        
        # Générer un nouvel ID unique
        existing_ids = [p['id'] for p in players_data['players']]
        player_num = 1
        while f"player_{player_num}" in existing_ids:
            player_num += 1
        new_id = f"player_{player_num}"
        
        current_time = time.time()
        new_player = {
            'id': new_id,
            'username': username,
            'research_points': 50,
            'unlocked_research': [],
            'research_effects': {
                'resource_bonuses': {}
            },
            'gold': 500,
            'diamonds': 10,
            'transport_ships_total': 1,
            'transport_ships_busy': 0,

            # Champs statistiques militaires
            'total_units_killed': 0,
            'total_units_lost': 0,
            'total_xp_gained': 0,
            'battles_fought': 0,
            'victories': 0,
            'defeats': 0,
            'victories_barbarians': 0,
            
            # Champs SessionTracker (tracking sessions et temps de jeu)
            'creation_date': int(current_time),
            'last_login': None,
            'last_activity': None,
            'session_count': 0,
            'total_play_time_minutes': 0
        }
        
        # Valider les données
        validate_player_data(new_player)
        
        # Ajouter et sauvegarder (forcer la sauvegarde pour la création de compte)
        players_data['players'].append(new_player)
        
        if not self.data_manager.save_players(players_data, force_save=True):
            raise GameValidationError("Impossible de sauvegarder le joueur")
        
        return new_player
    
    def authenticate_player(self, username: str, password: str) -> Dict:
        """Authentifie un joueur avec mot de passe depuis player_profiles.json"""
        player = self.get_player_by_username(username)
        if not player:
            raise PlayerNotFoundError(username)
        
        # Vérifier le password dans player_profiles.json
        try:
            import os
            import json
            profiles_file = os.path.join(self.data_manager.gamedata_dir, 'player_profiles.json')
            if os.path.exists(profiles_file):
                with open(profiles_file, 'r', encoding='utf-8') as f:
                    profiles_data = json.load(f)
                
                # Chercher le profil par player_id
                profile = profiles_data.get("profiles", {}).get(player['id'])
                if profile and 'password' in profile:
                    if profile['password'] != password:
                        raise GameValidationError("Nom d'utilisateur ou mot de passe incorrect")
                    return player
        except Exception:
            pass
        
        # Mode legacy : vérifier dans players.json (compatibilité anciens comptes)
        if 'password' in player:
            if player['password'] != password:
                raise GameValidationError("Nom d'utilisateur ou mot de passe incorrect")
        
        return player
    
    def get_player_cities(self, player_id: str) -> List[Dict]:
        """Récupère les villes d'un joueur avec les coordonnées des îles"""
        savegame_data = self.data_manager.load_savegame()
        if not savegame_data:
            return []
        
        # Charger les données de l'univers pour récupérer les coordonnées des îles
        universe_data = self.data_manager.load_universe()
        islands_by_id = {}
        
        if universe_data and 'islands' in universe_data:
            for island in universe_data['islands']:
                island_id = island.get('id')
                if island_id:
                    islands_by_id[island_id] = island
        
        # Récupérer les villes du joueur et ajouter les coordonnées des îles
        player_cities = []
        for city in savegame_data.get('cities', []):
            if city.get('owner') == player_id:
                # Créer une copie de la ville pour ne pas modifier l'original
                city_with_coords = city.copy()
                
                # Ajouter les coordonnées de l'île si disponibles
                island_id = city.get('island_id')
                if island_id and island_id in islands_by_id:
                    island = islands_by_id[island_id]
                    city_with_coords['island_coords'] = island.get('coords', [0, 0])
                else:
                    city_with_coords['island_coords'] = [0, 0]
                
                player_cities.append(city_with_coords)
        
        return player_cities
    
    def player_has_city(self, player_id: str) -> bool:
        """Vérifie si un joueur possède au moins une ville"""
        cities = self.get_player_cities(player_id)
        return len(cities) > 0
    
    def get_player_info(self, player_id: str) -> Dict:
        """Récupère les informations complètes d'un joueur"""
        player = self.get_player_by_id(player_id)
        if not player:
            raise PlayerNotFoundError(player_id)
        
        cities = self.get_player_cities(player_id)
        
        # Calculer les bateaux disponibles
        transport_ships_total = player.get('transport_ships_total', player.get('transport_ships', 0))
        transport_ships_busy = player.get('transport_ships_busy', 0)
        transport_ships_available = max(0, transport_ships_total - transport_ships_busy)
        
        return {
            'id': player['id'],
            'username': player['username'],
            'has_city': len(cities) > 0,
            'city_ids': [c['id'] for c in cities],
            'city_count': len(cities),
            'research_points': player.get('research_points', 0),
            'unlocked_research': player.get('unlocked_research', []),
            'gold': player.get('gold', 0),
            'diamonds': player.get('diamonds', 0),
            'transport_ships_total': transport_ships_total,
            'transport_ships_available': transport_ships_available,
            'faction': player.get('faction')
        }
