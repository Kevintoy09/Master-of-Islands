"""
=================================================================
USERNAME_ROUTES.PY - API pour vérification nom d'utilisateur
=================================================================

RESPONSABILITÉS:
- Vérification disponibilité nom d'utilisateur en temps réel
- API simple pour le frontend React

ROUTES DISPONIBLES:
- GET /api/check-username/<username> → Vérifier disponibilité

=================================================================
"""

from flask import Blueprint, jsonify
from ..business.player_service import PlayerService
from ..core.decorators import handle_errors
from ..core.exceptions import GameValidationError

# Création du Blueprint
username_bp = Blueprint('username', __name__, url_prefix='/api')

# Le service sera injecté lors de l'enregistrement
player_service: PlayerService = None

def init_username_routes(ps: PlayerService):
    """Initialise les routes avec le service"""
    global player_service
    player_service = ps

@username_bp.route('/check-username/<username>', methods=['GET'])
@handle_errors
def check_username_availability(username: str):
    """
    Vérifie si un nom d'utilisateur est disponible
    
    Returns:
        JSON: {"available": true/false, "message": "..."}
    """
    try:
        username = username.strip()
        
        if not username:
            return jsonify({
                'available': False,
                'message': 'Le nom d\'utilisateur ne peut pas être vide'
            })
        
        if len(username) < 2:
            return jsonify({
                'available': False,
                'message': 'Le nom d\'utilisateur doit contenir au moins 2 caractères'
            })
        
        if len(username) > 20:
            return jsonify({
                'available': False,
                'message': 'Le nom d\'utilisateur ne peut pas dépasser 20 caractères'
            })
        
        # Vérifier si le nom d'utilisateur existe déjà
        existing_player = player_service.get_player_by_username(username)
        
        if existing_player:
            return jsonify({
                'available': False,
                'message': 'Ce nom d\'utilisateur est déjà utilisé'
            })
        
        return jsonify({
            'available': True,
            'message': 'Nom d\'utilisateur disponible'
        })
        
    except Exception as e:
        return jsonify({
            'available': False,
            'message': f'Erreur lors de la vérification: {str(e)}'
        }), 500