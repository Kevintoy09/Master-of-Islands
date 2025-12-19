"""
Module API - Routes organisées par domaine fonctionnel
"""

from flask import Blueprint

def register_routes(app):
    """Enregistre toutes les routes API"""
    from .auth_routes import auth_bp
    from .city_routes import city_bp
    from .universe_routes import universe_bp, legacy_bp
    from .resource_routes import resource_bp
    from .transport_routes import transport_bp
    from .game_routes import game_bp, legacy_game_bp
    # ai_routes supprimé (système IA simplifié)
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(city_bp)
    app.register_blueprint(universe_bp)
    app.register_blueprint(legacy_bp)  # Routes legacy sans préfixe
    app.register_blueprint(resource_bp)
    app.register_blueprint(transport_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(legacy_game_bp)
    # ai_bp supprimé
