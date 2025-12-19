"""
=================================================================
HEALTH_CHECK - Endpoint de santé pour Railway
=================================================================
"""

from flask import Blueprint, jsonify
import os

health_bp = Blueprint('health', __name__)


@health_bp.route('/api/health', methods=['GET'])
def health_check():
    """
    Endpoint de santé pour Railway et monitoring
    """
    environment = os.getenv('ENVIRONMENT', 'development')
    db_url = os.getenv('DATABASE_URL', None)
    
    return jsonify({
        'status': 'healthy',
        'environment': environment,
        'database': 'postgresql' if db_url else 'json',
        'version': '1.0.0'
    }), 200
