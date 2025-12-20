"""Middleware pour logger les requêtes lentes"""
import time
from flask import request, g
from functools import wraps

def init_performance_monitoring(app):
    """Initialise le monitoring de performance sur toutes les routes"""
    
    @app.before_request
    def before_request():
        """Démarre le chronomètre avant chaque requête"""
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """Log les requêtes qui prennent plus de 500ms"""
        # Logs désactivés pour production
        # if hasattr(g, 'start_time'):
        #     elapsed = (time.time() - g.start_time) * 1000
        #     if elapsed > 500:
        #         method = request.method
        #         path = request.path
        #         status = response.status_code
        #         color = '🔴' if elapsed > 1000 else '🟠'
        #         print(f"{color} [{elapsed:.0f}ms] {method} {path} → {status}")
        
        return response
