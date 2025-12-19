"""
Routes API pour les notifications
"""
from flask import Blueprint, request, jsonify
from app.data_manager import DataManager
from app.business.notification_service import NotificationService

# Créer le blueprint
notification_bp = Blueprint('notification', __name__)

# Variable globale pour le manager (sera initialisée dans init_notification_routes)
_notification_service = None

def init_notification_routes(data_manager: DataManager):
    """Initialiser les routes de notification avec le data manager"""
    global _notification_service
    _notification_service = NotificationService(data_manager)
    return notification_bp

@notification_bp.route('/api/notifications/player/<player_id>', methods=['GET'])
def get_player_notifications(player_id: str):
    """Récupérer les notifications d'un joueur"""
    try:
        limit = int(request.args.get('limit', 50))
        only_unread = request.args.get('only_unread', 'false').lower() == 'true'
        
        notifications = _notification_service.get_player_notifications(
            player_id=player_id,
            limit=limit,
            only_unread=only_unread
        )
        
        return jsonify({
            "success": True,
            "notifications": notifications
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la récupération des notifications: {str(e)}"
        }), 500

@notification_bp.route('/api/notifications/player/<player_id>/unread-count', methods=['GET'])
def get_unread_count(player_id: str):
    """Récupérer le nombre de notifications non lues"""
    try:
        count = _notification_service.get_unread_count(player_id)
        
        return jsonify({
            "success": True,
            "unread_count": count
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors du comptage des notifications: {str(e)}"
        }), 500

@notification_bp.route('/api/notifications/player/<player_id>/mark-read', methods=['POST'])
def mark_notifications_read(player_id: str):
    """Marquer toutes les notifications comme lues"""
    try:
        success = _notification_service.mark_all_as_read(player_id)
        
        return jsonify({
            "success": True,
            "marked": success
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors du marquage des notifications: {str(e)}"
        }), 500

@notification_bp.route('/api/notifications/sync-buildings/<player_id>', methods=['POST'])
def sync_building_notifications(player_id: str):
    """Synchroniser les notifications de bâtiments terminés"""
    try:
        created_notifications = _notification_service.create_missing_building_notifications(player_id)
        
        return jsonify({
            "success": True,
            "created_count": len(created_notifications),
            "notification_ids": created_notifications,
            "message": f"{len(created_notifications)} notifications créées pour les bâtiments manquants"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la synchronisation: {str(e)}"
        }), 500
