"""
Routes API pour les paramètres du joueur
"""
from flask import Blueprint, request, jsonify
from ..data_manager import DataManager
from ..business.profile_service import ProfileService
from ..core.decorators import handle_errors
import os
import json

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

data_manager: DataManager = None
profile_service: ProfileService = None

def init_settings_routes(dm: DataManager):
    """Initialise les routes avec le data manager"""
    global data_manager, profile_service
    data_manager = dm
    profile_service = ProfileService(dm)

@settings_bp.route('/profile', methods=['GET'])
@handle_errors
def get_profile():
    """Récupère le profil d'un joueur"""
    player_id = request.args.get('player_id')
    
    if not player_id:
        return jsonify({'success': False, 'error': 'player_id manquant'}), 400
    
    profile = profile_service.get_profile(player_id)
    
    if not profile:
        return jsonify({'success': False, 'error': 'Profil non trouvé'}), 404
    
    return jsonify({
        'player_id': profile.get('player_id'),
        'username': profile.get('username'),
        'email': profile.get('email'),
        'firstName': profile.get('firstName'),
        'lastName': profile.get('lastName'),
        'country': profile.get('country'),
        'is_email_verified': profile.get('is_email_verified', False)
    })

@settings_bp.route('/update-username', methods=['POST'])
@handle_errors
def update_username():
    """Met à jour le nom d'utilisateur"""
    data = request.get_json()
    player_id = data.get('player_id')
    new_username = data.get('username', '').strip()
    
    if not player_id or not new_username:
        return jsonify({'success': False, 'error': 'Paramètres manquants'}), 400
    
    if len(new_username) < 3 or len(new_username) > 20:
        return jsonify({'success': False, 'error': 'Le nom doit contenir entre 3 et 20 caractères'}), 400
    
    # Mettre à jour dans player_profiles.json
    profile = profile_service.update_profile(player_id, {'username': new_username})
    
    # Mettre à jour dans players.json
    players_data = data_manager.load_players()
    players_list = players_data.get('players', [])
    player = next((p for p in players_list if p.get('id') == player_id), None)
    
    if player:
        player['username'] = new_username
        data_manager.save_players(players_data, force_save=True)
    
    return jsonify({'success': True, 'username': new_username})

@settings_bp.route('/update-email', methods=['POST'])
@handle_errors
def update_email():
    """Met à jour l'adresse email"""
    data = request.get_json()
    player_id = data.get('player_id')
    new_email = data.get('email', '').strip()
    
    if not player_id or not new_email:
        return jsonify({'success': False, 'error': 'Paramètres manquants'}), 400
    
    # Validation et mise à jour via ProfileService
    profile = profile_service.update_profile(player_id, {'email': new_email})
    
    return jsonify({'success': True, 'email': profile['email']})

@settings_bp.route('/update-password', methods=['POST'])
@handle_errors
def update_password():
    """Met à jour le mot de passe"""
    data = request.get_json()
    player_id = data.get('player_id')
    new_password = data.get('password', '').strip()
    
    if not player_id or not new_password:
        return jsonify({'success': False, 'error': 'Paramètres manquants'}), 400
    
    if len(new_password) < 4:
        return jsonify({'success': False, 'error': 'Le mot de passe doit contenir au moins 4 caractères'}), 400
    
    # Mettre à jour dans player_profiles.json
    profile = profile_service.update_profile(player_id, {'password': new_password})
    
    return jsonify({'success': True})

@settings_bp.route('/delete-account', methods=['POST'])
@handle_errors
def delete_account():
    """Supprime complètement le compte du joueur et toutes ses données"""
    data = request.get_json()
    player_id = data.get('player_id')
    
    print(f"\n[SETTINGS] ⚠️ SUPPRESSION COMPTE: {player_id}")
    
    # SÉCURITÉ: Vérifier que player_id est valide et non vide
    if not player_id or not isinstance(player_id, str) or player_id.strip() == '':
        print("[SETTINGS] ❌ ABORT: player_id invalide")
        return jsonify({'success': False, 'error': 'player_id manquant ou invalide'}), 400
    
    # SÉCURITÉ: Vérifier que player_id commence par "player_"
    if not player_id.startswith('player_'):
        print(f"[SETTINGS] ❌ ABORT: player_id invalide '{player_id}'")
        return jsonify({'success': False, 'error': 'player_id invalide'}), 400
    
    # 1. Supprimer de player_profiles.json
    profiles_file = os.path.join(data_manager.gamedata_dir, 'player_profiles.json')
    if os.path.exists(profiles_file):
        with open(profiles_file, 'r', encoding='utf-8') as f:
            profiles_data = json.load(f)
        
        if player_id in profiles_data.get('profiles', {}):
            del profiles_data['profiles'][player_id]
            with open(profiles_file, 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, indent=2, ensure_ascii=False)
    
    # 2. Supprimer de players.json
    players_data = data_manager.load_players()
    players_data['players'] = [p for p in players_data.get('players', []) if p.get('id') != player_id]
    data_manager.save_players(players_data, force_save=True)
    
    # 3. Supprimer ses villes du savegame.json
    savegame_data = data_manager.load_savegame()
    savegame_data['cities'] = [c for c in savegame_data.get('cities', []) if c.get('owner') != player_id]
    data_manager.save_savegame(savegame_data, force_save=True)
    
    # 4. Supprimer de player_quests.json
    quests_file = os.path.join(data_manager.gamedata_dir, 'player_quests.json')
    if os.path.exists(quests_file):
        with open(quests_file, 'r', encoding='utf-8') as f:
            quests_data = json.load(f)
        
        if player_id in quests_data.get('player_quests', {}):
            del quests_data['player_quests'][player_id]
            with open(quests_file, 'w', encoding='utf-8') as f:
                json.dump(quests_data, f, indent=2, ensure_ascii=False)
    
    # 5. Supprimer de player_heroes.json
    heroes_file = os.path.join(data_manager.gamedata_dir, 'player_heroes.json')
    if os.path.exists(heroes_file):
        with open(heroes_file, 'r', encoding='utf-8') as f:
            heroes_data = json.load(f)
        
        if player_id in heroes_data:
            del heroes_data[player_id]
            with open(heroes_file, 'w', encoding='utf-8') as f:
                json.dump(heroes_data, f, indent=2, ensure_ascii=False)
    
    # 6. Supprimer de player_unit_improvements.json
    improvements_file = os.path.join(data_manager.gamedata_dir, 'player_unit_improvements.json')
    if os.path.exists(improvements_file):
        with open(improvements_file, 'r', encoding='utf-8') as f:
            improvements_data = json.load(f)
        
        if player_id in improvements_data:
            del improvements_data[player_id]
            with open(improvements_file, 'w', encoding='utf-8') as f:
                json.dump(improvements_data, f, indent=2, ensure_ascii=False)
    
    # 7. Supprimer ses messages
    messages_file = os.path.join(data_manager.gamedata_dir, 'messages.json')
    if os.path.exists(messages_file):
        with open(messages_file, 'r', encoding='utf-8') as f:
            messages_data = json.load(f)
        
        # Filtrer les messages où le joueur est sender ou recipient
        filtered_messages = [
            msg for msg in messages_data 
            if msg.get('sender_id') != player_id and msg.get('recipient_id') != player_id
        ]
        
        with open(messages_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_messages, f, indent=2, ensure_ascii=False)
    
    # 8. Supprimer ses notifications
    notifications_file = os.path.join(data_manager.gamedata_dir, 'notifications.json')
    if os.path.exists(notifications_file):
        with open(notifications_file, 'r', encoding='utf-8') as f:
            notifications_data = json.load(f)
        
        if player_id in notifications_data:
            del notifications_data[player_id]
            with open(notifications_file, 'w', encoding='utf-8') as f:
                json.dump(notifications_data, f, indent=2, ensure_ascii=False)
    
    # 9. Supprimer ses transports
    transports_file = os.path.join(data_manager.gamedata_dir, 'transports.json')
    if os.path.exists(transports_file):
        with open(transports_file, 'r', encoding='utf-8') as f:
            transports_data = json.load(f)
        
        # Filtrer les transports où le joueur est source ou destination
        filtered_transports = [
            t for t in transports_data.get('transports', [])
            if t.get('source_player_id') != player_id and t.get('destination_player_id') != player_id
        ]
        
        transports_data['transports'] = filtered_transports
        with open(transports_file, 'w', encoding='utf-8') as f:
            json.dump(transports_data, f, indent=2, ensure_ascii=False)
    
    # 10. Supprimer son historique de transports
    transport_history_file = os.path.join(data_manager.gamedata_dir, 'transport_history.json')
    if os.path.exists(transport_history_file):
        try:
            with open(transport_history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            if isinstance(history_data, dict) and player_id in history_data:
                del history_data[player_id]
                with open(transport_history_file, 'w', encoding='utf-8') as f:
                    json.dump(history_data, f, indent=2, ensure_ascii=False)
            elif isinstance(history_data, list):
                with open(transport_history_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f, indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, UnicodeDecodeError):
            with open(transport_history_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=2, ensure_ascii=False)
    
    # 11. Supprimer ses batailles actives
    battles_file = os.path.join(data_manager.gamedata_dir, 'battlesv2.json')
    if os.path.exists(battles_file):
        with open(battles_file, 'r', encoding='utf-8') as f:
            battles_data = json.load(f)
        
        # Filtrer les batailles où le joueur est attaquant ou défenseur
        filtered_battles = [
            b for b in battles_data.get('battles', [])
            if b.get('attacker_id') != player_id and b.get('defender_id') != player_id
        ]
        
        battles_data['battles'] = filtered_battles
        with open(battles_file, 'w', encoding='utf-8') as f:
            json.dump(battles_data, f, indent=2, ensure_ascii=False)
    
    # 12. Supprimer ses rapports de bataille
    battle_reports_file = os.path.join(data_manager.gamedata_dir, 'battle_reports.json')
    if os.path.exists(battle_reports_file):
        with open(battle_reports_file, 'r', encoding='utf-8') as f:
            reports_data = json.load(f)
        
        # Filtrer les rapports du joueur
        if player_id in reports_data:
            del reports_data[player_id]
            with open(battle_reports_file, 'w', encoding='utf-8') as f:
                json.dump(reports_data, f, indent=2, ensure_ascii=False)
    
    # 13. Supprimer ses replays de bataille
    battle_replays_file = os.path.join(data_manager.gamedata_dir, 'battle_replays.json')
    if os.path.exists(battle_replays_file):
        with open(battle_replays_file, 'r', encoding='utf-8') as f:
            replays_data = json.load(f)
        
        # Filtrer les replays impliquant le joueur
        filtered_replays = {
            k: v for k, v in replays_data.items()
            if v.get('attacker_id') != player_id and v.get('defender_id') != player_id
        }
        
        with open(battle_replays_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_replays, f, indent=2, ensure_ascii=False)
    
    # 14. Supprimer ses offres sur le marché
    market_file = os.path.join(data_manager.gamedata_dir, 'market.json')
    if os.path.exists(market_file):
        with open(market_file, 'r', encoding='utf-8') as f:
            market_data = json.load(f)
        
        # Filtrer les offres du joueur
        filtered_offers = [
            offer for offer in market_data.get('offers', [])
            if offer.get('player_id') != player_id
        ]
        
        market_data['offers'] = filtered_offers
        with open(market_file, 'w', encoding='utf-8') as f:
            json.dump(market_data, f, indent=2, ensure_ascii=False)
    
    print(f"[SETTINGS] ✅ Suppression complète de {player_id} terminée avec succès")
    
    return jsonify({
        'success': True, 
        'message': 'Compte supprimé avec succès'
    })
