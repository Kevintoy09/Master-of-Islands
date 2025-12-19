"""
=================================================================
__INIT__.PY - Configuration principale de l'application Flask
=================================================================

RESPONSABILITÉS:
- Configuration Flask et CORS
- Enregistrement des blueprints API modulaires
- Gestionnaires d'erreurs globaux
- Initialisation des services métier

ARCHITECTURE MODULAIRE:
- /api/auth/*       → auth_routes.py    (Authentification)
- /api/city/*       → city_routes.py    (Gestion villes)
- /api/universe/*   → universe_routes.py (Univers/îles)
- /api/resources/*  → resource_routes.py (Sites ressources)
- /api/game/*       → game_routes.py    (Contrôles jeu)

SERVICES MÉTIER:
- PlayerService → Gestion joueurs
- CityService   → Logique villes

⚠️ RÈGLES:
- NE PAS ajouter de routes directement ici
- Utiliser les blueprints appropriés
- Services initialisés une seule fois
=================================================================
"""

from flask import Flask, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os
import sys

# Configuration des paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Imports des gestionnaires centraux - SIMPLIFIÉS
from .data_manager import DataManager
from .game_logic import GameLogic

# Imports des services métier
from .business.player_service import PlayerService
from .business.city_service import CityService
from .business.profile_service import ProfileService

# Import du système militaire (simplifié)
from .battle.barracks_api import barracks_bp
# from .military_api import military_unified_bp  # SUPPRIMÉ - fichier supprimé pour éviter conflits V1/V2
from .business.research_service import ResearchService
from .business.island_assignment_service import IslandAssignmentService

# Import du SaveService
from .services.save_service import init_save_service

# Import du système de bataille V2
from .routes.battle_routes_v2 import battle_v2_bp

# Import du système de héros V2
from .routes.hero_routes_v2 import hero_v2_bp

# Import du gestionnaire de tours V2
from .battle.battle_turn_manager_v2 import battle_turn_bp

# Import des actions de bataille V2
from .battle.battle_actions_v2 import battle_actions_v2_bp

# Import du système de pillage
from .routes.pillage_routes import pillage_bp

# Import des routes de debug IA
from .routes.ai_debug_routes import ai_debug_bp

# Import du service de timers globaux
from .services.periodic_task_service import TimerService

from .routes.auth_routes import auth_bp, legacy_auth_bp, init_auth_routes
from .routes.username_routes import username_bp, init_username_routes
from .routes.city_routes import city_bp, legacy_city_bp, init_city_routes
# from .routes.military_routes import military_bp, init_military_routes  # OBSOLÈTE - remplacé par military_api.py
from .routes.universe_routes import universe_bp, legacy_bp, init_universe_routes
from .routes.resource_routes import resource_bp, init_resource_routes
from .routes.game_routes import game_bp, legacy_game_bp, init_game_routes
from .routes.research_routes import research_bp, init_research_routes
from .routes.notification_routes import notification_bp, init_notification_routes
from .routes.island_assignment_routes import island_assignment_bp, init_island_assignment_routes
from .routes.market_routes import market_bp, init_market_routes
from .routes.transport_routes import transport_bp, init_transport_routes
from .routes.unit_transport_routes import unit_transport_routes, init_unit_transport_routes
from .routes.unit_improvement_routes import unit_improvement_bp
from .routes.city_check_routes import city_check_bp
from .routes.battle_results import battles_bp
from .routes.battle_replay import battle_replay_bp
from .routes.wall_attack import wall_attack_bp
from .routes.barbarian_level_routes import barbarian_level_bp
from .routes.tutorial import tutorial_bp, init_tutorial_routes
from .routes.progression_routes import progression_bp
from .routes.leaderboard_routes import leaderboard_bp
from .routes.quest_routes import quest_bp
from .messages import messages_bp

def create_app():
    """
    Factory pour créer l'application Flask avec configuration complète.
    """
    # Configuration du chemin vers le build React
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # PRIORITÉ 1: static_frontend dans server/ (pour Railway)
    # PRIORITÉ 2: ../client/build (pour développement local)
    static_frontend_dir = os.path.join(BASE_DIR, 'static_frontend')
    client_build_fallback = os.path.abspath(os.path.join(BASE_DIR, '..', 'client', 'build'))
    
    # Déterminer le dossier build à utiliser
    if os.path.exists(os.path.join(static_frontend_dir, 'index.html')):
        client_build_dir = static_frontend_dir
    else:
        client_build_dir = client_build_fallback
    
    static_dir = os.path.join(client_build_dir, 'static')
    
    # Flask app avec static_folder configuré pour servir le build React
    app = Flask(__name__, 
                static_folder=static_dir,
                static_url_path='/static')
    
    # Configuration depuis variables d'environnement
    from dotenv import load_dotenv
    load_dotenv()
    
    app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Configuration session : 24 heures de durée de vie
    from datetime import timedelta
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    
    # === CONFIGURATION ===
    cors_origins = os.getenv('CORS_ORIGINS', '*')
    if cors_origins != '*':
        cors_origins = cors_origins.split(',')
    
    CORS(app, resources={r"/*": {"origins": cors_origins}}, supports_credentials=True)
    
    # === INITIALISATION DATABASE (PostgreSQL en production) ===
    from .config.database import init_db
    db_initialized = init_db()
    app.config['USE_POSTGRESQL'] = db_initialized
    
    # Réduire les logs Werkzeug
    import logging
    werkzeug_log = logging.getLogger('werkzeug')
    werkzeug_log.setLevel(logging.ERROR)
    
    # === MONITORING DE PERFORMANCE ===
    from .middleware.performance_logger import init_performance_monitoring
    init_performance_monitoring(app)
    
    # === INITIALISATION DES SERVICES ===
    
    # SaveService désactivé - utilisation de DataManager uniquement pour éviter les conflits d'accès concurrentiel
    # savegame_path = os.path.join(BASE_DIR, 'gamedata', 'savegame.json')
    # init_save_service(savegame_path)
    
    data_manager = DataManager(BASE_DIR)
    
    # Configurer le fallback pour la transition
    from .transition_utils import set_legacy_data_manager
    set_legacy_data_manager(data_manager)
    
    # Initialiser et démarrer le service de timers globaux
    timer_service = TimerService(data_manager)
    timer_service.start()
    
    game_logic = GameLogic(data_manager)
    # PopulationManager supprimé - logique intégrée dans ManualTickService
    
    # Services métier
    player_service = PlayerService(data_manager)
    profile_service = ProfileService(data_manager)
    # Créer une instance de CityService avec les gestionnaires appropriés - SIMPLIFIÉ
    city_service = CityService(data_manager, game_logic, None)
    research_service = ResearchService(data_manager)
    island_assignment_service = IslandAssignmentService(data_manager)
    
    # Initialiser le SessionTracker pour suivi des sessions de jeu
    from .services.session_tracker import SessionTracker
    session_tracker = SessionTracker(data_manager)
    
    # === INITIALISATION DU SYSTÈME MILITAIRE ===
    # military_service = init_military_service(data_manager)

    
    # === INITIALISATION DU TICK SERVICE UNIFIÉ ===
    # Service unique pour ticks manuels ET auto-tick intégré
    from .services.tick_service import TickService
    tick_service = TickService(data_manager)
    
    # Expose pour les endpoints admin
    app.config['TICK_SERVICE'] = tick_service
    
    # === INITIALISATION DU TIME MANAGER ===
    # === INITIALISATION DES BLUEPRINTS - SIMPLIFIÉ ===
    init_auth_routes(player_service, profile_service, session_tracker)
    init_username_routes(player_service)
    init_city_routes(city_service, data_manager, game_logic, None, session_tracker)
    # init_military_routes(data_manager)  # OBSOLÈTE - remplacé par military_api.py
    init_universe_routes(data_manager)
    init_resource_routes(data_manager, game_logic, None)
    init_game_routes(game_logic, None, data_manager)
    init_research_routes(research_service)
    init_notification_routes(data_manager)
    init_island_assignment_routes(island_assignment_service)
    init_market_routes(data_manager)
    init_transport_routes(data_manager)
    init_unit_transport_routes(data_manager)
    init_tutorial_routes(data_manager)  # Système de tutoriel

    # === ENREGISTREMENT DES BLUEPRINTS ===
    app.register_blueprint(auth_bp)
    app.register_blueprint(legacy_auth_bp)  # Blueprint legacy pour auth sans préfixe
    app.register_blueprint(username_bp)  # API vérification username
    app.register_blueprint(city_bp)
    app.register_blueprint(legacy_city_bp)  # Blueprint legacy pour /api/city-state
    # app.register_blueprint(military_bp)  # OBSOLÈTE - remplacé par military_unified_bp
    app.register_blueprint(universe_bp)
    app.register_blueprint(legacy_bp)  # Blueprint legacy pour les routes sans préfixe
    app.register_blueprint(resource_bp)
    app.register_blueprint(transport_bp)
    app.register_blueprint(unit_transport_routes)  # Routes pour transports d'unités
    app.register_blueprint(game_bp)
    app.register_blueprint(legacy_game_bp)  # Blueprint legacy pour les routes game
    app.register_blueprint(research_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(island_assignment_bp)  # Routes d'affectation des îles
    app.register_blueprint(market_bp)  # Routes du marché
    app.register_blueprint(barracks_bp)  # Production d'unités dans la caserne
    app.register_blueprint(battle_v2_bp)  # 🎯 SYSTÈME DE BATAILLE V2 - PRIORITÉ MAX - TOUTES ROUTES CONSOLIDÉES
    app.register_blueprint(hero_v2_bp)  # 🦸‍♂️ SYSTÈME DE HÉROS V2 - GESTION DES HÉROS PROPRE
    app.register_blueprint(battle_turn_bp)  # 🔄 GESTIONNAIRE DE TOURS V2 - SYSTÈME DE ROUNDS
    app.register_blueprint(battle_actions_v2_bp)  # ⚔️ ACTIONS DE COMBAT V2 - ENREGISTREMENT ATTACKS/MOVES
    app.register_blueprint(unit_improvement_bp)  # 🔨 SYSTÈME D'AMÉLIORATION D'UNITÉS - FORGE
    app.register_blueprint(pillage_bp)  # 🏴‍☠️ SYSTÈME DE PILLAGE - RESSOURCES POST-BATAILLE (avec support barbares)
    app.register_blueprint(ai_debug_bp)  # 🧪 PANNEAU DE DEBUG IA - TESTS DÉCISIONS COMBAT
    app.register_blueprint(wall_attack_bp)  # 🧱 SYSTÈME D'ATTAQUE DES MURS - DESTRUCTION GROUPES
    app.register_blueprint(battles_bp)  # 📊 SYSTÈME DE GESTION DES BATAILLES - PAGE ARMÉE
    app.register_blueprint(barbarian_level_bp)  # 🏺 API NIVEAU VILLAGES BARBARES - DÉTECTION NIVEAU RÉEL
    app.register_blueprint(battle_replay_bp)  # 🎬 SYSTÈME DE REPLAY DES BATAILLES
    app.register_blueprint(city_check_bp)  # ✅ VÉRIFICATION POSSESSION VILLE - endpoint simple
    app.register_blueprint(tutorial_bp)  # 📚 SYSTÈME DE TUTORIEL - PROGRESSION ET RÉCOMPENSES
    app.register_blueprint(progression_bp)  # 📊 SYSTÈME DE PROGRESSION - SCORES CONSTRUCTION/RECHERCHE
    app.register_blueprint(leaderboard_bp)  # 🏆 SYSTÈME DE CLASSEMENT - LEADERBOARD DES JOUEURS
    app.register_blueprint(quest_bp)  # 🎯 SYSTÈME DE QUÊTES - QUOTIDIENNES ET HEBDOMADAIRES
    app.register_blueprint(messages_bp)  # 💬 SYSTÈME DE MESSAGERIE - COMMUNICATION JOUEURS & ADMIN
    # app.register_blueprint(military_unified_bp)  # SUPPRIMÉ - gestion militaire V1 supprimée pour éviter conflits
    
    # Initialiser et enregistrer les routes de paramètres utilisateur
    from .routes.settings_routes import settings_bp, init_settings_routes
    init_settings_routes(data_manager)
    app.register_blueprint(settings_bp)  # ⚙️ PARAMÈTRES UTILISATEUR - MODIFICATION PROFIL & SUPPRESSION COMPTE
    
    # Health check pour Railway
    from .routes.health_routes import health_bp
    app.register_blueprint(health_bp)
    
    # ROUTES V1 DÉSACTIVÉES - Migration vers V2 complète
    # from .battle_routes import battle_bp
    # app.register_blueprint(battle_bp)  # Gestion des enregistrements de batailles V1
    
    # === ROUTES POUR SERVIR LE CLIENT REACT ===
    # /static/* est automatiquement géré par Flask.static_folder
    CLIENT_BUILD_DIR = client_build_dir
    
    @app.route('/')
    def serve_react_app():
        """Sert la page principale du client React"""
        index_path = os.path.join(CLIENT_BUILD_DIR, 'index.html')
        if os.path.exists(index_path):
            return send_file(index_path)
        return jsonify({'status': 'error', 'message': 'React build not found'}), 404
    
    @app.route('/api/health')
    def health_check():
        """Route de test pour vérifier que le serveur fonctionne"""
        return jsonify({'status': 'ok', 'message': 'Server is running'})
    
    @app.route('/data/v2/<filename>')
    def serve_v2_data_files(filename):
        """Sert les fichiers de données V2 depuis server/data/v2/ et server/data/"""
        try:
            # Vérifier d'abord dans data/v2/
            v2_data_dir = os.path.join(BASE_DIR, 'data', 'v2')
            file_path = os.path.join(v2_data_dir, filename)
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return send_file(file_path)
            
            # Si pas trouvé et que c'est battlefields_v2.json, chercher dans data/
            if filename == 'battlefields_v2.json':
                main_data_dir = os.path.join(BASE_DIR, 'data')
                file_path = os.path.join(main_data_dir, filename)
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    return send_file(file_path)
            
            return jsonify({'error': 'File not found', 'path': f'data/v2/{filename}'}), 404
        except Exception as e:
            return jsonify({'error': 'Server error', 'details': str(e)}), 500

    @app.route('/data/battlefields/<filename>')
    def serve_battlefield_files(filename):
        """Sert les fichiers de battlefields depuis server/data/battlefields/"""
        try:
            battlefields_dir = os.path.join(BASE_DIR, 'data', 'battlefields')
            file_path = os.path.join(battlefields_dir, filename)
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return send_file(file_path)
            
            return jsonify({'error': 'Battlefield not found'}), 404
        except Exception as e:
            return jsonify({'error': 'Server error'}), 500

    @app.route('/data/battlefields_v2.json')
    def serve_battlefields_v2():
        """Sert le fichier battlefields_v2.json avec positions décompactées pour le frontend"""
        try:
            from app.battle.battle_creation_service_v2 import BattleCreationServiceV2
            
            battle_service = BattleCreationServiceV2()
            battlefields_data = battle_service.get_all_battlefields()
            
            return jsonify(battlefields_data)
        except Exception as e:
            return jsonify({'error': 'Server error', 'details': str(e)}), 500

    @app.route('/data/buildings.json')
    def serve_buildings():
        """Sert le fichier buildings.json depuis server/data/"""
        try:
            data_dir = os.path.join(BASE_DIR, 'data')
            file_path = os.path.join(data_dir, 'buildings.json')
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return send_file(file_path)
            
            return jsonify({'error': 'buildings.json not found'}), 404
        except Exception as e:
            return jsonify({'error': 'Server error', 'details': str(e)}), 500
    
    @app.route('/<path:path>')
    def serve_static_files(path):
        """Route catch-all pour servir le React SPA.
        Les fichiers /static/* sont automatiquement gérés par Flask.static_folder.
        Cette route gère les assets non-static et le routing React.
        """
        file_path = os.path.join(CLIENT_BUILD_DIR, path)
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_file(file_path)
        
        # Route React non trouvée = servir index.html (SPA routing)
        return send_file(os.path.join(CLIENT_BUILD_DIR, 'index.html'))
    
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({'error': 'Not found', 'details': str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error', 'details': str(error)}), 500
    
    # Initialiser le service V2 pour démarrer le timer automatique
    try:
        from .battle.battle_creation_service_v2 import get_battle_creation_service_v2
        battle_service_v2 = get_battle_creation_service_v2()
    except Exception as e:
        print(f"❌ [V2] Erreur initialisation service V2: {e}")
    
    # Système temporel centralisé supprimé - utilise TickService maintenant
    
    # Enregistrer l'interface d'administration
    try:
        from .routes.admin_routes import admin_bp
        app.register_blueprint(admin_bp)
    except Exception as e:
        print(f"❌ [ADMIN] Erreur enregistrement interface admin: {e}")
    
    # Routes AI supprimées (système IA simplifié)
    
    # Route pour l'interface admin AI (accessible directement)
    @app.route('/admin/ai')
    def ai_admin_interface():
        """Interface d'administration des joueurs IA"""
        from flask import render_template
        return render_template('ai_admin.html')
    
    # API pour toggle IA auto
    @app.route('/api/admin/ai/toggle-auto', methods=['POST'])
    def toggle_ai_auto():
        """Active/désactive l'exécution automatique de l'IA"""
        from flask import request, jsonify
        import json
        import os
        
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
            settings_path = os.path.join(data_dir, 'admin_settings.json')
            
            # Charger les paramètres actuels
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Toggle l'état
            current_state = settings.get('ai_auto_enabled', False)
            settings['ai_auto_enabled'] = not current_state
            
            # Sauvegarder
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            
            return jsonify({
                'success': True,
                'ai_auto_enabled': settings['ai_auto_enabled']
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # API pour récupérer l'état de l'IA auto
    @app.route('/api/admin/ai/auto-status', methods=['GET'])
    def get_ai_auto_status():
        """Récupère l'état actuel de l'IA auto"""
        from flask import jsonify
        import json
        import os
        
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
            settings_path = os.path.join(data_dir, 'admin_settings.json')
            
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            return jsonify({
                'success': True,
                'ai_auto_enabled': settings.get('ai_auto_enabled', False)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # Routes API simplifiées pour l'interface admin IA
    @app.route('/api/ai/stats', methods=['GET'])
    def get_ai_stats():
        """Récupère les statistiques des IA"""
        from flask import jsonify
        from app.ai.ai_controller import AIController
        
        try:
            ai_controller = AIController()
            ai_players = ai_controller.get_all_ai_players()
            
            stats = {
                'total_ais': len(ai_players),
                'active_now': 0,
                'by_personality': {},
                'by_difficulty': {}
            }
            
            for ai in ai_players:
                # Compter par personnalité
                personality = ai.get('ai_personality', 'unknown')
                stats['by_personality'][personality] = stats['by_personality'].get(personality, 0) + 1
                
                # Compter par difficulté
                difficulty = ai.get('ai_difficulty', 'unknown')
                stats['by_difficulty'][difficulty] = stats['by_difficulty'].get(difficulty, 0) + 1
            
            return jsonify({
                'success': True,
                'stats': stats
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/ai/players', methods=['GET'])
    def get_ai_players():
        """Récupère la liste des joueurs IA"""
        from flask import jsonify
        from app.ai.ai_controller import AIController
        
        try:
            ai_controller = AIController()
            ai_players = ai_controller.get_all_ai_players()
            
            # Enrichir avec infos villes
            from app.data_manager import DataManager
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_manager = DataManager(base_dir)
            savegame = data_manager.load_savegame()
            
            for ai in ai_players:
                player_id = ai.get('id')
                cities = [c for c in savegame.get('cities', []) if c.get('owner') == player_id]
                ai['city_count'] = len(cities)
                ai['is_online'] = True  # Simplifié
                ai['personality'] = ai.get('ai_personality', 'balanced')
                ai['difficulty'] = ai.get('ai_difficulty', 'medium')
            
            return jsonify({
                'success': True,
                'ai_players': ai_players
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/ai/execute', methods=['POST'])
    def execute_ai_cycle():
        """Exécute manuellement un cycle IA (force=True pour ignorer ai_auto_enabled)"""
        from flask import jsonify
        from app.ai.ai_controller import AIController
        
        try:
            ai_controller = AIController()
            results = ai_controller.execute_all_ais(force=True)  # Force l'exécution manuelle
            
            return jsonify({
                'success': True,
                'executed_count': results.get('executed_count', 0),
                'total_actions': results.get('total_actions', 0),
                'actions': results.get('actions', [])  # Liste des actions avec détails
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/ai/console-logs', methods=['GET'])
    def get_ai_console_logs():
        """Récupère les logs de la console IA (pour polling)"""
        from flask import jsonify
        import os
        import json
        
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            logs_path = os.path.join(base_dir, 'data', 'ai_console_logs.json')
            
            if os.path.exists(logs_path):
                with open(logs_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return jsonify({
                        'success': True,
                        'logs': data.get('logs', [])
                    })
            else:
                return jsonify({
                    'success': True,
                    'logs': []
                })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/ai/console-logs/<player_id>', methods=['DELETE'])
    def clear_ai_console_logs(player_id):
        """Supprime les logs console d'un joueur IA spécifique"""
        from flask import jsonify
        import os
        import json
        
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            logs_path = os.path.join(base_dir, 'data', 'ai_console_logs.json')
            
            if os.path.exists(logs_path):
                with open(logs_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Filtrer pour supprimer les logs du joueur
                original_count = len(data.get('logs', []))
                data['logs'] = [log for log in data.get('logs', []) if log.get('player_id') != player_id]
                deleted_count = original_count - len(data['logs'])
                
                # Sauvegarder
                with open(logs_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                return jsonify({
                    'success': True,
                    'deleted_count': deleted_count
                })
            else:
                return jsonify({
                    'success': True,
                    'deleted_count': 0
                })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return app

# Instance globale pour compatibilité (temporaire)
app = create_app()
