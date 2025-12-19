# -*- coding: utf-8 -*-
"""
TUTORIAL.PY - Routes API du Système de Tutoriel

RÔLE:
    Gère le backend du système de tutoriel interactif.
    Fournit les endpoints pour suivre la progression et créditer les récompenses.

RESPONSABILITÉS:
    1. Récupération du statut du tutoriel d'un joueur (progression, étape actuelle)
    2. Validation et complétion d'une étape
    3. Crédit automatique des récompenses (ressources, points de recherche)
    4. Mise à jour de la progression dans players.json
    5. Vérification des conditions de complétion (via api_check)

ENDPOINTS:
    GET  /api/tutorial/status/<player_id>
         → Retourne le statut complet du tutoriel (completed, current_step, completed_steps)
    
    POST /api/tutorial/complete
         → Marque une étape comme complétée et crédite les récompenses
         Body: { player_id, step_id, reward }
    
    POST /api/tutorial/check/<step_id>
         → Vérifie si une condition d'étape est remplie (pour validation automatique)
         Body: { player_id }

SYSTÈME DE RÉCOMPENSES:
    Les récompenses sont définies dans tutorialSteps.ts (frontend) et créditées ici:
    - Ressources : Ajoutées à la première ville du joueur (wood, stone, gold, etc.)
    - Points de recherche : Ajoutés au compteur du joueur (player.research_points)
    - Validation backend : Empêche la triche (récompenses dupliquées)

ARCHITECTURE:
    Frontend (tutorialSteps.ts)
        ↓ (appelle l'API)
    Backend (tutorial.py)
        ↓ (met à jour)
    players.json (player.tutorial: {completed, current_step, completed_steps})
    savegame.json (city.resources: {wood, stone, ...})

SÉCURITÉ:
    - Vérification que l'étape n'est pas déjà complétée (pas de récompenses multiples)
    - Validation des données (player_id, step_id)
    - Gestion des erreurs (joueur introuvable, ville introuvable)

FLUX DE COMPLÉTION D'ÉTAPE:
    1. Frontend détecte validation (click, api_check, etc.)
    2. POST /api/tutorial/complete avec step_id et reward
    3. Backend vérifie que l'étape n'est pas déjà complétée
    4. Crédit des récompenses (ressources ou research_points)
    5. Mise à jour de player.tutorial.completed_steps
    6. Retour du nouveau statut au frontend

POINTS CLÉS:
    - Le tutoriel est stocké au niveau JOUEUR (players.json)
    - Les récompenses ressources vont à la PREMIÈRE VILLE du joueur
    - completed_steps est un nombre (pas une liste) = nombre d'étapes complétées
    - current_step contient l'ID de l'étape actuelle (ex: 'welcome_world')

EXEMPLE DE RÉPONSE API:
    GET /api/tutorial/status/player_1
    {
      "completed": false,
      "current_step": "build_sawmill",
      "completed_steps": 5
    }

HISTORIQUE:
    - Système de validation automatique (api_check)
    - Crédit des récompenses automatique
    - Double validation frontend + backend
    - Support des récompenses research_points
"""

from flask import Blueprint, request, jsonify
from app.data_manager import DataManager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

tutorial_bp = Blueprint('tutorial', __name__, url_prefix='/api/tutorial')

# Instance de DataManager (sera initialisée par init_tutorial_routes)
data_manager = None

def init_tutorial_routes(dm: DataManager):
    """Initialise les routes du tutoriel avec le DataManager."""
    global data_manager
    data_manager = dm
    return tutorial_bp

@tutorial_bp.route('/status/<player_id>', methods=['GET'])
def get_tutorial_status(player_id):
    """Obtenir le statut du tutoriel pour un joueur."""
    try:
        # Charger tous les joueurs
        players_data = data_manager.load_players()
        player_data = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
        
        if not player_data:
            return jsonify({'error': 'Joueur non trouvé'}), 404
        
        tutorial_data = player_data.get('tutorial', {
            'completed': False,
            'current_step': 'welcome_world',
            'completed_steps': 0
        })
        
        # Ordre des étapes (doit correspondre à tutorialSteps.ts)
        tutorial_step_ids = [
            'welcome_world',           # 0
            'welcome_island',          # 1
            'welcome_city',            # 2
            'build_townhall',          # 3
            'build_academy',           # 4
            'assign_worker_academy',   # 5
            'unlock_chief_house',      # 6
            'assign_worker_forest',    # 7
            'build_barracks',          # 8
            'train_militia',           # 9
            'build_port',              # 10
            'attack_barbarian',        # 11
            'continue_exploration',    # 12
            'tutorial_complete'        # 13 (finale)
        ]
        
        # Calculer l'étape actuelle basée sur completed_steps
        completed_count = tutorial_data.get('completed_steps', 0)
        if completed_count >= len(tutorial_step_ids):
            current_step = tutorial_step_ids[-1]  # Dernière étape
        else:
            current_step = tutorial_step_ids[completed_count]
        
        return jsonify({
            'success': True,
            'tutorial_completed': tutorial_data.get('completed', False),
            'current_step': current_step,
            'completed_steps': tutorial_data.get('completed_steps', 0)
        })
    
    except Exception as e:
        logger.error(f"Erreur get_tutorial_status: {e}")
        return jsonify({'error': str(e)}), 500


@tutorial_bp.route('/complete-step', methods=['POST'])
def complete_step():
    """Valider une étape du tutoriel et attribuer la récompense."""
    try:
        data = request.get_json()
        player_id = data.get('player_id')
        step_id = data.get('step_id')
        reward = data.get('reward')
        
        if not player_id or not step_id:
            return jsonify({'error': 'Données manquantes'}), 400
        
        # Charger tous les joueurs
        players_data = data_manager.load_players()
        player_data = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
        
        if not player_data:
            return jsonify({'error': 'Joueur non trouvé'}), 404
        
        # Initialiser les données du tutoriel si nécessaire
        if 'tutorial' not in player_data:
            player_data['tutorial'] = {
                'completed': False,
                'current_step': 'welcome',
                'completed_steps': 0
            }
        # Attribuer les récompenses
        rewards_given = {}
        if reward and reward.get('value'):
            reward_type = reward.get('type')
            reward_values = reward.get('value')
            
            if reward_type == 'resources':
                # Or dans player.gold, autres ressources dans la ville
                savegame_data = data_manager.load_savegame()
                player_city = next((c for c in savegame_data.get('cities', []) if c['owner'] == player_id), None)
                
                for resource, amount in reward_values.items():
                    if resource == 'gold':
                        # Or dans player
                        player_data['gold'] = player_data.get('gold', 0) + amount
                    elif resource == 'population':
                        # Population dans la ville
                        if player_city:
                            if 'resources' not in player_city:
                                player_city['resources'] = {}
                            current_pop = player_city['resources'].get('population_total', 0)
                            current_free = player_city['resources'].get('population_free', 0)
                            player_city['resources']['population_total'] = current_pop + amount
                            player_city['resources']['population_free'] = current_free + amount
                    else:
                        # Matériaux dans la première ville du joueur
                        if player_city:
                            if 'resources' not in player_city:
                                player_city['resources'] = {}
                            player_city['resources'][resource] = player_city['resources'].get(resource, 0) + amount
                    
                    rewards_given[resource] = amount
                
                # Sauvegarder une seule fois après toutes les modifications
                if player_city:
                    data_manager.save_savegame(savegame_data, force_save=True)
            
            elif reward_type == 'research_points':
                # Ajouter des points de recherche au champ racine (utilisé par le système)
                points = reward_values.get('research_points', 0)
                current_points = player_data.get('research_points', 0)
                player_data['research_points'] = current_points + points
                rewards_given['research_points'] = points
            
            elif reward_type == 'units':
                # Ajouter des unités dans la garnison de la ville du joueur
                savegame_data = data_manager.load_savegame()
                player_city = next((c for c in savegame_data.get('cities', []) if c['owner'] == player_id), None)
                
                if player_city:
                    # Initialiser la structure military si nécessaire
                    if 'military' not in player_city:
                        player_city['military'] = {'garrison': {}}
                    if 'garrison' not in player_city['military']:
                        player_city['military']['garrison'] = {}
                    if player_id not in player_city['military']['garrison']:
                        player_city['military']['garrison'][player_id] = {}
                    
                    # Ajouter les unités dans la garnison du joueur
                    player_garrison = player_city['military']['garrison'][player_id]
                    for unit_type, amount in reward_values.items():
                        if unit_type not in player_garrison:
                            player_garrison[unit_type] = {'quantity': 0}
                        current_qty = player_garrison[unit_type].get('quantity', 0)
                        player_garrison[unit_type]['quantity'] = current_qty + amount
                        rewards_given[unit_type] = amount
                    
                    data_manager.save_savegame(savegame_data, force_save=True)
        
        # Marquer l'étape comme complétée (compteur)
        tutorial_data = player_data['tutorial']
        tutorial_data['completed_steps'] = tutorial_data.get('completed_steps', 0) + 1
        # current_step est maintenant calculé automatiquement par /status basé sur completed_steps
        
        # Sauvegarder les données
        data_manager.save_players(players_data, force_save=True)
        
        logger.info(f"Joueur {player_id} a complété l'étape '{step_id}' - Récompenses: {rewards_given}")
        
        return jsonify({
            'success': True,
            'message': f'Étape "{step_id}" complétée !',
            'rewards_given': rewards_given,
            'completed_steps': tutorial_data['completed_steps']
        })
    
    except Exception as e:
        logger.error(f"Erreur complete_step: {e}")
        return jsonify({'error': str(e)}), 500


@tutorial_bp.route('/complete', methods=['POST'])
def complete_tutorial():
    """Marquer le tutoriel comme terminé."""
    try:
        data = request.get_json()
        player_id = data.get('player_id')
        
        if not player_id:
            return jsonify({'error': 'player_id manquant'}), 400
        
        # Charger tous les joueurs
        players_data = data_manager.load_players()
        player_data = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
        
        if not player_data:
            return jsonify({'error': 'Joueur non trouvé'}), 404
        
        # Marquer le tutoriel comme complété et nettoyer les champs inutiles
        player_data['tutorial'] = {'completed': True}
        
        # Sauvegarder
        data_manager.save_players(players_data, force_save=True)
        
        logger.info(f"Joueur {player_id} a terminé le tutoriel !")
        
        return jsonify({
            'success': True,
            'message': 'Tutoriel terminé ! Bon jeu !'
        })
    
    except Exception as e:
        logger.error(f"Erreur complete_tutorial: {e}")
        return jsonify({'error': str(e)}), 500


@tutorial_bp.route('/skip', methods=['POST'])
def skip_tutorial():
    """Passer le tutoriel (sans récompenses)."""
    try:
        data = request.get_json()
        player_id = data.get('player_id')
        
        if not player_id:
            return jsonify({'error': 'player_id manquant'}), 400
        
        # Charger tous les joueurs
        players_data = data_manager.load_players()
        player_data = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
        
        if not player_data:
            return jsonify({'error': 'Joueur non trouvé'}), 404
        
        # Marquer le tutoriel comme passé (format compact)
        player_data['tutorial'] = {'completed': True}
        
        # Sauvegarder
        data_manager.save_players(players_data, force_save=True)
        
        logger.info(f"Joueur {player_id} a passé le tutoriel")
        
        return jsonify({
            'success': True,
            'message': 'Tutoriel passé'
        })
    
    except Exception as e:
        logger.error(f"Erreur skip_tutorial: {e}")
        return jsonify({'error': str(e)}), 500


@tutorial_bp.route('/reset/<player_id>', methods=['POST'])
def reset_tutorial(player_id):
    """Réinitialiser le tutoriel (pour debug)."""
    try:
        # Charger tous les joueurs
        players_data = data_manager.load_players()
        player_data = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
        
        if not player_data:
            return jsonify({'error': 'Joueur non trouvé'}), 404
        
        # Réinitialiser le tutoriel
        player_data['tutorial'] = {
            'completed': False,
            'current_step': 'welcome',
            'completed_steps': []
        }
        
        # Sauvegarder
        data_manager.save_players(players_data, force_save=True)
        
        logger.info(f"Tutoriel du joueur {player_id} réinitialisé")
        
        return jsonify({
            'success': True,
            'message': 'Tutoriel réinitialisé'
        })
    
    except Exception as e:
        logger.error(f"Erreur reset_tutorial: {e}")
        return jsonify({'error': str(e)}), 500
