# -*- coding: utf-8 -*-
"""
Routes API pour le système de quêtes
"""

from flask import Blueprint, jsonify, request
from app.services.quest_service import quest_service
from functools import wraps
import os

quest_bp = Blueprint('quest', __name__, url_prefix='/api')


def get_base_dir():
    """Obtient le répertoire de base du projet"""
    current_file = os.path.abspath(__file__)
    return os.path.dirname(os.path.dirname(os.path.dirname(current_file)))


def get_username_from_request():
    """Récupère le username depuis la session/token (à adapter selon ton système d'auth)"""
    # Pour l'instant, récupération depuis le body ou query param
    try:
        # Essayer de récupérer depuis le JSON (pour POST)
        if request.is_json and request.json:
            return request.json.get('username')
    except:
        pass
    
    # Sinon, récupérer depuis les query params (pour GET)
    return request.args.get('username')


def require_auth(f):
    """Décorateur pour vérifier l'authentification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = get_username_from_request()
        if not username:
            return jsonify({"error": "Username requis"}), 400
        return f(username, *args, **kwargs)
    return decorated_function


@quest_bp.route('/quests/player-level', methods=['GET'])
@require_auth
def get_player_level(username):
    """Retourne le niveau actuel du joueur"""
    try:
        level = quest_service.calculate_player_level(username)
        return jsonify({
            "username": username,
            "level": level,
            "formula": "(construction_points * 0.5) + (quest_points * 0.5)"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@quest_bp.route('/quests/player-stats', methods=['GET'])
@require_auth
def get_player_stats(username):
    """Retourne les statistiques de progression du joueur (points de quêtes, niveau, barre de progression)"""
    try:
        import json
        from pathlib import Path
        
        # Charger les données du joueur
        players_path = Path(__file__).parent.parent.parent / 'gamedata' / 'players.json'
        with open(players_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Trouver le joueur dans la liste
        players_list = data.get('players', [])
        player = next((p for p in players_list if p.get('username') == username), None)
        
        if not player:
            return jsonify({"error": "Joueur introuvable"}), 404
        
        quest_points = player.get('quest_points', 0)
        level = quest_service.calculate_player_level(username)
        
        # Calculer les paliers de niveau
        thresholds = [0, 10, 20, 50, 90, 140, 200, 270, 350, 440, 540, 651, 772, 903, 1044, 1195, 1356, 1527, 1708, 1899]
        
        # Trouver le palier actuel et le prochain
        current_threshold = thresholds[level - 1] if level <= 20 else thresholds[-1]
        next_threshold = thresholds[level] if level < 20 else thresholds[-1]
        
        # Calculer la progression vers le niveau suivant
        if level >= 20:
            # Niveau max atteint
            points_in_current_level = quest_points - current_threshold
            points_needed = 0
            progress_percentage = 100
        else:
            points_in_current_level = quest_points - current_threshold
            points_needed = next_threshold - current_threshold
            progress_percentage = min(100, (points_in_current_level / points_needed * 100)) if points_needed > 0 else 0
        
        return jsonify({
            "username": username,
            "quest_points": quest_points,
            "level": level,
            "current_threshold": current_threshold,
            "next_threshold": next_threshold if level < 20 else None,
            "points_in_current_level": points_in_current_level,
            "points_needed_for_next_level": points_needed if level < 20 else 0,
            "progress_percentage": round(progress_percentage, 1),
            "is_max_level": level >= 20
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@quest_bp.route('/quests/daily', methods=['GET'])
@require_auth
def get_daily_quests(username):
    """Retourne les 5 quêtes quotidiennes du joueur"""
    try:
        quests = quest_service.get_or_generate_daily_quests(username)
        player_level = quest_service.calculate_player_level(username)
        
        return jsonify({
            "username": username,
            "player_level": player_level,
            "quests": quests,
            "count": len(quests)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@quest_bp.route('/quests/weekly', methods=['GET'])
@require_auth
def get_weekly_quests(username):
    """Retourne les quêtes hebdomadaires du joueur avec progression chronologique"""
    try:
        all_player_data = quest_service.load_all_player_quests()
        username_data = all_player_data.get(username, {})
        weekly_quests_data = username_data.get('weekly_quests', {})
        
        # Si pas de quêtes générées, les générer maintenant
        if not weekly_quests_data.get('quests'):
            generated = quest_service.generate_weekly_quests(username)
            weekly_quests_data = {
                'generated_date': datetime.now().strftime('%Y-%m-%d'),
                'quests': generated
            }
            username_data['weekly_quests'] = weekly_quests_data
            all_player_data[username] = username_data
            quest_service.save_all_player_quests(all_player_data)
        
        # Vérifier et compléter automatiquement les quêtes (met à jour progression + is_completed)
        quest_service.check_and_complete_weekly_quests(username)
        
        # Recharger après complétion pour avoir les données à jour (avec progression sauvegardée)
        all_player_data = quest_service.load_all_player_quests()
        username_data = all_player_data.get(username, {})
        weekly_quests_data = username_data.get('weekly_quests', {})
        
        # Vérifier combien de quêtes sont disponibles (actives = pas encore complétées OU complétées mais récompenses non réclamées)
        all_quests = weekly_quests_data.get('quests', [])
        # Une quête est "active" si elle n'est pas complétée, OU si elle est complétée mais pas encore réclamée
        active_quests = [q for q in all_quests if not (q.get('is_completed') and q.get('rewards_claimed'))]
        
        # Si moins de 3 quêtes actives, régénérer pour en avoir 3
        if len(active_quests) < 3:
            # Régénérer toutes les quêtes (garde celles actives + ajoute les suivantes)
            new_quests = quest_service.generate_weekly_quests(username)
            if new_quests:
                # Recharger pour être sûr d'avoir les dernières données
                all_player_data = quest_service.load_all_player_quests()
                username_data = all_player_data.get(username, {})
                weekly_quests_data['quests'] = new_quests
                username_data['weekly_quests'] = weekly_quests_data
                all_player_data[username] = username_data
                quest_service.save_all_player_quests(all_player_data)
        
        # Enrichir les quêtes avec les données de config ET progression en temps réel
        enriched_quests = []
        for quest in weekly_quests_data.get('quests', []):
            enriched = quest_service.enrich_weekly_quest_data(quest, username)
            if enriched:
                enriched_quests.append(enriched)
        
        return jsonify({
            "username": username,
            "quests": enriched_quests,
            "generated_date": weekly_quests_data.get('generated_date')
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@quest_bp.route('/quests/progress', methods=['GET'])
@require_auth
def get_quest_progress(username):
    """Retourne l'état de progression de toutes les quêtes"""
    try:
        quest_data = quest_service.load_player_quests(username)
        return jsonify(quest_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@quest_bp.route('/quests/unclaimed', methods=['GET'])
@require_auth
def get_unclaimed_rewards(username):
    """Retourne la liste des récompenses non réclamées (daily + weekly)"""
    try:
        quest_data = quest_service.load_player_quests(username)
        unclaimed_daily = quest_data.get('unclaimed_rewards', [])
        
        # Ajouter les récompenses hebdomadaires non réclamées
        weekly_quests_data = quest_data.get('weekly_quests', {})
        weekly_quests = weekly_quests_data.get('quests', [])
        
        unclaimed_weekly = []
        weekly_config = quest_service.quests_config.get('weekly_quests', {})
        weekly_progression = weekly_config.get('quests', [])
        
        for quest in weekly_quests:
            if quest.get('is_completed') and not quest.get('rewards_claimed'):
                # Trouver la config pour récupérer les rewards
                quest_def = next((q for q in weekly_progression if q.get('id') == quest.get('id')), None)
                if quest_def:
                    unclaimed_weekly.append({
                        "quest_id": quest.get('id'),
                        "quest_type": "weekly",
                        "rewards": quest_def.get('rewards', {})
                    })
        
        # Combiner les deux listes
        all_unclaimed = unclaimed_daily + unclaimed_weekly
        
        return jsonify({
            "username": username,
            "unclaimed_rewards": all_unclaimed,
            "count": len(all_unclaimed)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@quest_bp.route('/quests/claim-reward', methods=['POST'])
@require_auth
def claim_reward(username):
    """Réclame une récompense d'étoile"""
    try:
        data = request.json
        quest_id = data.get('quest_id')
        star_level = data.get('star_level')
        
        if not quest_id or not star_level:
            return jsonify({"error": "quest_id et star_level requis"}), 400
        
        result = quest_service.claim_rewards(username, quest_id, star_level)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@quest_bp.route('/quests/update-progress', methods=['POST'])
@require_auth
def update_progress(username):
    """
    Met à jour la progression d'une quête (endpoint de test/debug)
    Body: {"quest_id": "eco_collect_wood", "increment": 10}
    ou   {"quest_id": "eco_build_buildings", "set_value": 5}
    """
    try:
        data = request.json
        quest_id = data.get('quest_id')
        increment = data.get('increment', 0)
        set_value = data.get('set_value')
        
        if not quest_id:
            return jsonify({"error": "quest_id requis"}), 400
        
        result = quest_service.update_quest_progress(
            username, 
            quest_id, 
            increment=increment,
            set_value=set_value
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@quest_bp.route('/quests/claim-weekly-reward', methods=['POST'])
def claim_weekly_reward():
    """Réclamer une récompense de quête hebdomadaire"""
    try:
        data = request.get_json()
        username = data.get('username')
        quest_id = data.get('quest_id')
        
        if not username or not quest_id:
            return jsonify({"error": "username et quest_id requis"}), 400
        
        # Charger les données
        all_player_data = quest_service.load_all_player_quests()
        username_data = all_player_data.get(username, {})
        weekly_quests_data = username_data.get('weekly_quests', {})
        quests = weekly_quests_data.get('quests', [])
        
        # Trouver la quête
        quest_to_claim = None
        for quest in quests:
            if quest.get('id') == quest_id and quest.get('is_completed') and not quest.get('rewards_claimed'):
                quest_to_claim = quest
                break
        
        if not quest_to_claim:
            return jsonify({"error": "Récompense non trouvée ou déjà réclamée"}), 404
        
        # Récupérer les rewards depuis la config
        weekly_config = quest_service.quests_config.get('weekly_quests', {})
        weekly_progression = weekly_config.get('quests', [])
        quest_def = next((q for q in weekly_progression if q.get('id') == quest_id), None)
        
        if not quest_def:
            return jsonify({"error": "Configuration de quête non trouvée"}), 404
        
        rewards = quest_def.get('rewards', {})
        
        # Appliquer les récompenses au joueur
        from app.data_manager import DataManager
        dm = DataManager(get_base_dir())
        players_data = dm.load_players()
        players_list = players_data.get('players', [])
        player = next((p for p in players_list if p.get('username') == username), None)
        
        if player:
            if rewards.get('gold'):
                player['gold'] = player.get('gold', 0) + rewards['gold']
            if rewards.get('diamonds'):
                player['diamonds'] = player.get('diamonds', 0) + rewards['diamonds']
            if rewards.get('research_points'):
                player['research_points'] = player.get('research_points', 0) + rewards['research_points']
            if rewards.get('quest_points'):
                player['quest_points'] = player.get('quest_points', 0) + rewards['quest_points']
            
            dm.save_players(players_data)
        
        # Marquer comme réclamée
        quest_to_claim['rewards_claimed'] = True
        
        # Ajouter à la liste quest_week_done maintenant que la récompense est réclamée
        quest_week_done = username_data.get('quest_week_done', [])
        if quest_id not in quest_week_done:
            quest_week_done.append(quest_id)
            username_data['quest_week_done'] = quest_week_done
        
        all_player_data[username] = username_data
        quest_service.save_all_player_quests(all_player_data)
        
        return jsonify({
            "success": True,
            "rewards": rewards,
            "message": "Récompense récupérée avec succès"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@quest_bp.route('/quests/reset-daily', methods=['POST'])
@require_auth
def reset_daily(username):
    """Reset les quêtes quotidiennes (endpoint admin/debug)"""
    try:
        quest_data = quest_service.load_player_quests(username)
        quest_data['daily_quests'] = {
            "generated_date": None,
            "player_level_snapshot": 1,
            "quests": []
        }
        quest_service.save_player_quests(username, quest_data)
        
        return jsonify({
            "message": "Quêtes quotidiennes réinitialisées",
            "username": username
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
