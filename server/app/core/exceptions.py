"""
=================================================================
EXCEPTIONS.PY - Exceptions personnalisées du jeu
=================================================================

RESPONSABILITÉS:
- Exceptions spécifiques au métier du jeu
- Hiérarchie avec codes HTTP appropriés
- Messages d'erreur clairs et localisés
- Gestion centralisée des erreurs

HIÉRARCHIE:
- GameError (400)              → Base pour erreurs métier
  ├─ GameValidationError (400) → Validation données
  ├─ InsufficientResourcesError (400) → Ressources manquantes
  └─ WorkerAssignmentError (400) → Problème ouvriers

- NotFoundError (404)          → Base pour ressources introuvables
  ├─ CityNotFoundError (404)   → Ville non trouvée
  └─ PlayerNotFoundError (404) → Joueur non trouvé

- DataAccessError (500)        → Erreurs accès données/fichiers

USAGE:
```python
raise CityNotFoundError("city_123")
raise GameValidationError("Population insuffisante")
raise InsufficientResourcesError({'wood': 50, 'stone': 30})
```
=================================================================
"""

class GameError(Exception):
    """Exception de base pour le jeu"""
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code
        super().__init__(message)

class GameValidationError(GameError):
    """Erreur de validation des données"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, 400)

class CityNotFoundError(GameError):
    """Ville introuvable"""
    def __init__(self, city_id: str):
        super().__init__(f"Ville '{city_id}' introuvable", 404)

class PlayerNotFoundError(GameError):
    """Joueur introuvable"""
    def __init__(self, player_id: str):
        super().__init__(f"Joueur '{player_id}' introuvable", 404)

class InsufficientResourcesError(GameError):
    """Ressources insuffisantes"""
    def __init__(self, missing_resources: dict):
        self.missing_resources = missing_resources
        message = f"Ressources insuffisantes: {missing_resources}"
        super().__init__(message, 400)
