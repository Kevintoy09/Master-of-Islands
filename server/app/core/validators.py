"""
=================================================================
VALIDATORS.PY - Validateurs de données du jeu
=================================================================

RESPONSABILITÉS:
- Validation de toutes les données d'entrée du jeu
- Vérification des règles métier avant traitement
- Levée d'exceptions GameValidationError en cas d'erreur
- Réutilisable dans toutes les couches (API, Services, etc.)

AVANT D'AJOUTER UNE VALIDATION:
- Vérifier si elle n'existe pas déjà dans ce fichier
- Une validation = une fonction pure (pas d'effets de bord)
- Toujours lever GameValidationError en cas d'échec
- Documenter les paramètres et le comportement

FONCTIONS DISPONIBLES:
- validate_city_data()          # Données de ville complètes
- validate_worker_assignment()  # Assignation d'ouvriers
- validate_resource_amount()    # Montants de ressources
- validate_player_data()        # Données de joueur
- validate_ids()                # Validation d'IDs
- validate_coordinates()        # Coordonnées de position
=================================================================
"""

from typing import Dict, Any, List, Optional
from .exceptions import GameValidationError

def validate_city_data(city_data: Dict[str, Any]) -> None:
    """Valide les données d'une ville"""
    required_fields = ['id', 'name', 'resources']
    
    for field in required_fields:
        if field not in city_data:
            raise GameValidationError(f"Champ requis manquant: {field}", field)
    
    # Vérifier que les ressources sont un dictionnaire
    if not isinstance(city_data.get('resources'), dict):
        raise GameValidationError("Les ressources doivent être un dictionnaire", 'resources')

def validate_worker_assignment(workers: int, max_workers: int, available_population: int) -> None:
    """Valide une assignation d'ouvriers"""
    if workers < 0:
        raise GameValidationError("Le nombre d'ouvriers ne peut pas être négatif")
    
    if workers > max_workers:
        raise GameValidationError(f"Capacité maximale dépassée. Maximum: {max_workers}")
    
    if workers > available_population:
        raise GameValidationError(f"Population insuffisante. Disponible: {available_population}")

def validate_resource_amount(amount: int, resource_type: str) -> None:
    """Valide un montant de ressource"""
    if amount <= 0:
        raise GameValidationError(f"Le montant de {resource_type} doit être positif")

def validate_player_data(player_data: Dict[str, Any]) -> None:
    """Valide les données d'un joueur"""
    required_fields = ['id', 'username']
    
    for field in required_fields:
        if field not in player_data:
            raise GameValidationError(f"Champ requis manquant: {field}", field)
    
    username = player_data.get('username', '').strip()
    if not username:
        raise GameValidationError("Le nom d'utilisateur ne peut pas être vide", 'username')
    
    if len(username) < 3:
        raise GameValidationError("Le nom d'utilisateur doit faire au moins 3 caractères", 'username')

def validate_ids(*ids: str) -> None:
    """Valide que tous les IDs fournis sont valides"""
    for i, id_value in enumerate(ids):
        if not id_value or not isinstance(id_value, str) or not id_value.strip():
            raise GameValidationError(f"ID invalide à la position {i}")

def validate_coordinates(coords: List[int]) -> None:
    """Valide des coordonnées"""
    if not isinstance(coords, list) or len(coords) != 2:
        raise GameValidationError("Les coordonnées doivent être une liste de 2 entiers")
    
    if not all(isinstance(coord, int) and coord >= 0 for coord in coords):
        raise GameValidationError("Les coordonnées doivent être des entiers positifs")
