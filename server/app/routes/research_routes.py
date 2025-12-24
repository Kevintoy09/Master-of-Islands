"""
Routes API simplifiées pour la gestion des recherches (sans JWT)
"""
from flask import Blueprint, request, jsonify
from ..business.research_service import ResearchService

research_bp = Blueprint('research', __name__)

# Variables globales pour l'injection de dépendances
research_service: ResearchService = None

def init_research_routes(rs: ResearchService):
    """Initialise les routes avec les services injectés"""
    global research_service
    research_service = rs

@research_bp.route('/api/research/player/<player_id>', methods=['GET'])
def get_player_research(player_id):
    """Récupère les recherches d'un joueur"""
    try:
        research_data = research_service.get_player_research(player_id)
        return jsonify({
            "success": True,
            "data": research_data
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erreur lors de la récupération des recherches: {str(e)}"
        }), 500

@research_bp.route('/api/research/check/<player_id>/<research_id>', methods=['POST'])
def check_research_requirements(player_id, research_id):
    """Vérifie si un joueur peut débloquer une recherche"""
    try:
        # Récupérer les données de recherche depuis le client
        research_data = request.get_json()
        if not research_data:
            return jsonify({
                "success": False,
                "message": "Données de recherche manquantes"
            }), 400
            
        result = research_service.can_unlock_research(player_id, research_id, research_data)
        return jsonify({
            "success": True,
            "data": result
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erreur lors de la vérification: {str(e)}"
        }), 500

@research_bp.route('/api/research/<player_id>/<research_id>/unlock', methods=['POST'])
@research_bp.route('/api/research/unlock/<player_id>/<research_id>', methods=['POST'])
def unlock_research(player_id, research_id):
    """Débloque une recherche pour un joueur"""
    try:
        # Charger les données de recherche depuis research.json (source de vérité)
        research_data = research_service.get_research_by_id(research_id)
        if not research_data:
            return jsonify({
                "success": False,
                "message": f"Recherche '{research_id}' introuvable"
            }), 404
            
        result = research_service.unlock_research(player_id, research_id, research_data)
        
        # Log en cas d'échec pour déboguer
        if not result["success"]:
            print(f"❌ [RESEARCH] Échec déverrouillage {research_id} pour {player_id}: {result.get('message')}")
        
        # Si c'est la Maison du Chef et que le déblocage réussit, générer les quêtes
        if result["success"] and research_id == "maison_chef":
            try:
                from app.services.quest_service import quest_service
                from app.data_manager import DataManager
                from datetime import datetime
                import os
                
                # Récupérer le username depuis player_id
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                data_manager = DataManager(base_dir)
                players_data = data_manager.load_players()
                player = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
                
                if player:
                    username = player.get('username')
                    
                    # Générer les quêtes quotidiennes (déjà sauvegardées par get_or_generate)
                    quest_service.get_or_generate_daily_quests(username)
                    
                    # Générer les quêtes principales et les sauvegarder
                    weekly_quests = quest_service.generate_main_quests(username)
                    all_player_data = quest_service.load_all_player_quests()
                    username_data = all_player_data.get(username, {})
                    username_data['weekly_quests'] = {
                        'generated_date': datetime.now().strftime('%Y-%m-%d'),
                        'quests': weekly_quests
                    }
                    all_player_data[username] = username_data
                    quest_service.save_all_player_quests(all_player_data)
                    
                    print(f"✅ [QUESTS] Quêtes générées automatiquement pour {username} (déblocage Maison du Chef)")
                    print(f"   - Daily quests: {len(quest_service.get_or_generate_daily_quests(username))}")
                    print(f"   - Weekly quests: {len(weekly_quests)}")
            except Exception as quest_error:
                print(f"⚠️ [QUESTS] Erreur génération quêtes (non-bloquante): {quest_error}")
                import traceback
                traceback.print_exc()
        
        return jsonify(result), 200 if result["success"] else 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erreur lors du déverrouillage: {str(e)}"
        }), 500

@research_bp.route('/api/research/is-resource-unlocked/<player_id>/<resource>', methods=['GET'])
def is_resource_unlocked(player_id, resource):
    """Vérifie si une ressource est débloquée pour un joueur"""
    try:
        is_unlocked = research_service.is_resource_unlocked(player_id, resource)
        return jsonify({
            "success": True,
            "is_unlocked": is_unlocked
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erreur lors de la vérification: {str(e)}"
        }), 500

@research_bp.route('/api/research/unlocked-resources/<player_id>', methods=['GET'])
def get_unlocked_resources(player_id):
    """Récupère toutes les ressources débloquées pour un joueur"""
    try:
        # Liste des ressources à vérifier
        advanced_resources = ["marble", "wine", "horse", "glass"]
        industrial_resources = ["coal", "gunpowder", "spices", "cotton"]
        all_resources = advanced_resources + industrial_resources
        
        unlocked_resources = {}
        for resource in all_resources:
            unlocked_resources[resource] = research_service.is_resource_unlocked(player_id, resource)
        
        return jsonify({
            "success": True,
            "unlocked_resources": unlocked_resources
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erreur lors de la récupération: {str(e)}"
        }), 500

@research_bp.route('/api/player/<player_id>/research-points', methods=['GET'])
def get_player_research_points(player_id):
    """Récupère les points de recherche d'un joueur"""
    try:
        research_points = research_service.get_player_research_points(player_id)
        return jsonify({
            'research_points': research_points,
            'player_id': player_id
        })
    except Exception as e:
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500

@research_bp.route('/api/research/database', methods=['GET'])
def get_research_database():
    """Récupère la base de données complète des recherches"""
    try:
        from ..data_manager import DataManager
        import os
        
        # Initialiser DataManager avec base_dir
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_manager = DataManager(base_dir)
        
        # Charger research.json
        research_data = data_manager.load_research()
        if not research_data:
            return jsonify({"error": "Impossible de charger la base de données des recherches"}), 500
            
        return jsonify(research_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@research_bp.route('/api/research/database/<category>', methods=['GET'])
def get_research_by_category(category):
    """Récupère les recherches d'une catégorie spécifique"""
    try:
        from ..data_manager import DataManager
        import os
        
        # Initialiser DataManager avec base_dir
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_manager = DataManager(base_dir)
        
        # Charger research.json
        research_data = data_manager.load_research()
        if not research_data:
            return jsonify({"error": "Impossible de charger la base de données des recherches"}), 500
        
        # Filtrer par catégorie
        filtered_researches = [r for r in research_data.get('researches', []) if r.get('category') == category]
        
        return jsonify({
            "researches": filtered_researches,
            "category": category,
            "count": len(filtered_researches)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


