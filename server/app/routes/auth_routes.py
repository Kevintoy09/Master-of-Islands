"""
=================================================================
AUTH_ROUTES.PY - Routes API pour l'authentification
=================================================================

RESPONSABILITÉS:
- Gestion des comptes joueurs
- Authentification et connexion
- Validation des données d'auth

ROUTES DISPONIBLES:
- POST /api/auth/create-account → Création compte
- POST /api/auth/login          → Connexion joueur

UTILISE:
- PlayerService pour logique métier
- Décorateurs pour validation/erreurs

⚠️ NOTE: Routes legacy /create-account et /login
restent dans legacy_routes.py pour compatibilité frontend
=================================================================
"""

from flask import Blueprint, request, jsonify
from ..business.player_service import PlayerService
from ..business.profile_service import ProfileService
from ..core.decorators import handle_errors, validate_json
from ..core.exceptions import GameValidationError

# Création du Blueprint principal
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Création d'un Blueprint pour les routes legacy sans préfixe
legacy_auth_bp = Blueprint('legacy_auth', __name__)

# Les services seront injectés lors de l'enregistrement
player_service: PlayerService = None
profile_service: ProfileService = None
session_tracker = None

def init_auth_routes(ps: PlayerService, prs: ProfileService = None, st = None):
    """Initialise les routes avec les services"""
    global player_service, profile_service, session_tracker
    player_service = ps
    profile_service = prs
    session_tracker = st

@auth_bp.route('/create-account', methods=['POST'])
@handle_errors
@validate_json('username')
def create_account():
    """Crée un nouveau compte joueur"""
    data = request.get_json()
    username = data.get('username').strip()
    
    if not username:
        raise GameValidationError("Le nom d'utilisateur ne peut pas être vide")
    
    new_player = player_service.create_player(username)
    
    return jsonify({
        'success': True, 
        'player': new_player
    })

@auth_bp.route('/login', methods=['POST'])
@handle_errors
@validate_json('username')
def login():
    """Authentifie un joueur"""
    data = request.get_json()
    username = data.get('username').strip()
    password = data.get('password', '').strip()
    if not username:
        raise GameValidationError("Le nom d'utilisateur est requis")
    if not password:
        raise GameValidationError("Le mot de passe est requis")
    player = player_service.authenticate_player(username, password)
    
    # Démarrer le suivi de session
    if session_tracker:
        session_tracker.start_session(player['id'])
    
    player_info = player_service.get_player_info(player['id'])
    return jsonify(player_info)

@auth_bp.route('/player/<player_id>', methods=['GET'])
@handle_errors
def get_player_info(player_id: str):
    """Récupère les informations d'un joueur"""
    player_info = player_service.get_player_info(player_id)
    return jsonify(player_info)

@auth_bp.route('/player/<player_id>/cities', methods=['GET'])
@handle_errors
def get_player_cities(player_id: str):
    """Récupère les villes d'un joueur"""
    cities = player_service.get_player_cities(player_id)
    return jsonify({'cities': cities})

# ===============================================
# ROUTE COMPLÈTE pour création de compte avec profil
# ===============================================

@legacy_auth_bp.route('/create-account-complete', methods=['POST'])
@handle_errors
def create_account_complete():
    """Crée un compte joueur complet avec profil personnel"""
    try:
        data = request.get_json(force=True)
        
        # Validation des données de base
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email = data.get('email', '').strip()
        
        if not username:
            raise GameValidationError("Le nom d'utilisateur est requis")
        if not password:
            raise GameValidationError("Le mot de passe est requis")
        if not email:
            raise GameValidationError("L'adresse email est requise")
        
        # Création du compte joueur (sans password, maintenant géré par ProfileService)
        print(f"🚀 Création du joueur complet: {username}")
        new_player = player_service.create_player(username)
        
        # Création du profil si ProfileService disponible
        if profile_service and 'profile' in data:
            profile_data = data['profile']
            profile_data['email'] = email  # Assurer cohérence email
            profile_data['username'] = username  # Ajouter le username
            profile_data['password'] = password  # Ajouter le password
            
            try:
                profile = profile_service.create_profile(new_player['id'], profile_data)
                print(f"✅ Profil créé pour: {username}")
            except Exception as e:
                print(f"⚠️ Erreur création profil: {e}")
                # On continue même si le profil échoue
        
        print(f"✅ Compte complet créé: {new_player['id']} - {new_player['username']}")
        
        return jsonify({
            'success': True,
            'message': f'Compte créé avec succès pour {username}',
            'player': {
                'id': new_player['id'],
                'username': new_player['username'],
                'email': email,
                'gold': new_player.get('gold', 0),
                'diamonds': new_player.get('diamonds', 0)
            }
        })
        
    except GameValidationError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        print(f"❌ Erreur création compte complet: {e}")
        return jsonify({
            'success': False, 
            'error': f'Erreur lors de la création du compte: {str(e)}'
        }), 500

# ===============================================
# ROUTES LEGACY pour compatibilité (sans préfixe /api/auth)
# ===============================================

@legacy_auth_bp.route('/create-account', methods=['POST'])
def legacy_create_account():
    """Route legacy: crée un nouveau compte joueur"""
    try:
        data = request.get_json(force=True)
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({'success': False, 'error': 'Le nom d\'utilisateur est requis'}), 400
        
        print(f"🚀 Création du joueur: {username}")
        new_player = player_service.create_player(username)
        print(f"✅ Joueur créé: {new_player['id']} - {new_player['username']}")
        
        return jsonify({
            'success': True,
            'message': f'Compte créé avec succès pour {username}',
            'player': {
                'id': new_player['id'],
                'username': new_player['username'],
                'gold': new_player.get('gold', 0),
                'diamonds': new_player.get('diamonds', 0)
            }
        })
        
    except Exception as e:
        print(f"❌ Erreur création compte: {e}")
        return jsonify({
            'success': False, 
            'error': f'Erreur lors de la création du compte: {str(e)}'
        }), 500

@legacy_auth_bp.route('/login', methods=['POST'])
@handle_errors
def legacy_login():
    """Route legacy: authentifie un joueur"""
    data = request.get_json(force=True)
    username = data.get('username')
    password = data.get('password', username)  # Si pas de password, utilise username
    
    if not username:
        return jsonify({'error': 'username is required'}), 400
    
    try:
        player = player_service.authenticate_player(username.strip(), password.strip())
        
        # Démarrer le suivi de session
        if session_tracker:
            session_tracker.start_session(player['id'])
        
        player_info = player_service.get_player_info(player['id'])
        return jsonify(player_info)
    except GameValidationError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'Authentication failed', 'details': str(e)}), 500

@legacy_auth_bp.route('/player/<player_id>/cities', methods=['GET'])
@handle_errors
def legacy_get_player_cities(player_id: str):
    """Route legacy: récupère les villes d'un joueur"""
    try:
        cities = player_service.get_player_cities(player_id)
        return jsonify(cities)  # Format legacy sans wrapper
    except Exception as e:
        return jsonify({'error': str(e)}), 500
