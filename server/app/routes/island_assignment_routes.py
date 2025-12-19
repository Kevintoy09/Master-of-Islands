"""
=================================================================
ISLAND_ASSIGNMENT_ROUTES.PY - Routes API pour le monitoring des îles
=================================================================

RESPONSABILITÉS:
- API pour consulter l'état d'occupation des îles
- Suggestions pour debug/test (la logique principale est dans city_routes.py)

ROUTES DISPONIBLES:
- GET  /api/islands/assignment/suggest/<resource>  → Suggestion île + ville (debug)
- GET  /api/islands/assignment/resource/<resource> → Îles par ressource (monitoring)

UTILISE:
- IslandAssignmentService pour logique métier

NOTE: La logique principale d'affectation automatique est maintenant intégrée
      directement dans /api/city/colonize pour une expérience transparente.
=================================================================
"""

from flask import Blueprint, jsonify
from ..business.island_assignment_service import IslandAssignmentService
from ..core.decorators import handle_errors

# Création du Blueprint
island_assignment_bp = Blueprint('island_assignment', __name__, url_prefix='/api/islands/assignment')

# Le service sera injecté lors de l'enregistrement
island_assignment_service: IslandAssignmentService = None

def init_island_assignment_routes(ias: IslandAssignmentService):
    """Initialise les routes avec le service"""
    global island_assignment_service
    island_assignment_service = ias

@island_assignment_bp.route('/suggest/<resource>', methods=['GET'])
@handle_errors
def suggest_city_for_resource(resource: str):
    """
    Suggère une ville disponible pour une ressource donnée (principalement pour debug/test).
    La logique principale d'affectation est maintenant dans /api/city/colonize.
    """
    island, city = island_assignment_service.suggest_city_for_player(resource)
    
    if not island or not city:
        return jsonify({
            'success': False,
            'message': f'Aucune île disponible pour la ressource {resource}'
        }), 404
    
    return jsonify({
        'success': True,
        'suggestion': {
            'island': island,
            'city': city,
            'message': f"Île recommandée: {island['name']} (Ressource: {resource}), Ville: {city['name']}"
        }
    })

@island_assignment_bp.route('/resource/<resource>', methods=['GET'])
@handle_errors
def get_islands_by_resource(resource: str):
    """Récupère toutes les îles d'une ressource donnée avec leur statut d'occupation"""
    islands_info = island_assignment_service.get_available_islands_by_resource(resource)
    
    return jsonify({
        'success': True,
        'resource': resource,
        'total_islands': len(islands_info),
        'available_islands': len([i for i in islands_info if not i['is_full']]),
        'islands': islands_info
    })
