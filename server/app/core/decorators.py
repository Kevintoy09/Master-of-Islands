"""
=================================================================
DECORATORS.PY - Décorateurs pour les routes API
=================================================================

RESPONSABILITÉS:
- Décorateurs réutilisables pour les routes Flask
- Gestion automatique des erreurs et validations
- Fonctionnalités transversales (auth, cache, logs)
- Réduction de code dupliqué dans les routes

AVANT D'AJOUTER UN DÉCORATEUR:
- Vérifier s'il n'existe pas déjà
- S'assurer qu'il est réutilisable (pas spécifique à une route)
- Documenter les paramètres et l'usage
- Tester avec différentes routes

DÉCORATEURS DISPONIBLES:
- @handle_errors               # Gestion automatique des exceptions
- @validate_json('field1')     # Validation des champs JSON requis
- @require_city_owner          # Vérification propriétaire ville (à implémenter)
- @log_api_call                # Log des appels API (optionnel)
- @cache_response(60)          # Cache des réponses (à développer)

USAGE:
@app.route('/api/city/<city_id>')
@handle_errors
@validate_json('player_id', 'action')
def my_route(city_id):
    # Le JSON est validé automatiquement
    # Les erreurs sont gérées automatiquement
=================================================================
"""

from functools import wraps
from flask import jsonify, request
from typing import Callable, Any
from .exceptions import GameError, GameValidationError, CityNotFoundError

def handle_errors(f: Callable) -> Callable:
    """Décorateur pour gérer automatiquement les erreurs"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except GameError as e:
            return jsonify({'error': e.message}), e.code
        except Exception as e:
            import traceback
            print(f"Erreur inattendue dans {f.__name__}: {e}")
            print("Stack trace complète:")
            print(traceback.format_exc())
            return jsonify({'error': 'Erreur serveur interne'}), 500
    return decorated_function

def validate_json(*required_fields: str) -> Callable:
    """Décorateur pour valider la présence de champs JSON requis"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json(force=True)
                if not data:
                    return jsonify({'error': 'Données JSON requises'}), 400
                
                missing_fields = []
                for field in required_fields:
                    if field not in data or data[field] is None:
                        missing_fields.append(field)
                
                if missing_fields:
                    return jsonify({
                        'error': f"Champs requis manquants: {', '.join(missing_fields)}"
                    }), 400
                
                return f(*args, **kwargs)
            except Exception as e:
                # DEBUG: Afficher la vraie erreur au lieu de masquer
                print(f"❌ ERREUR dans validate_json: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': f'Erreur de validation: {str(e)}'}), 400
        return decorated_function
    return decorator

def require_city_owner(f: Callable) -> Callable:
    """Décorateur pour vérifier que le joueur possède la ville (auth à implémenter)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Implémenter la vérification d'authentification
        # Pour l'instant, on laisse passer toutes les requêtes
        return f(*args, **kwargs)
    return decorated_function

def log_api_call(f: Callable) -> Callable:
    """Décorateur pour logger les appels API (optionnel)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Pour les routes fréquentes, on peut désactiver le log
        route_name = f.__name__
        if route_name not in ['get_city_state', 'get_city_population']:
            print(f"[API] {request.method} {request.path} - {route_name}")
        return f(*args, **kwargs)
    return decorated_function

def cache_response(duration: int = 60) -> Callable:
    """Décorateur pour mettre en cache les réponses (simple implémentation)"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Implémenter un vrai système de cache si nécessaire
            # Pour l'instant, on exécute directement
            return f(*args, **kwargs)
        return decorated_function
    return decorator
