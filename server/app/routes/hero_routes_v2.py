"""
Hero Routes V2 - Gestion des héros pour le système V2
====================================================

Routes Flask pour la gestion des héros dans le système V2 :
- GET /api/military/city/heroes/<city_id> : Récupérer les héros d'une ville

Complètement séparé des anciens systèmes V1
"""

from flask import Blueprint, request, jsonify
import json
import os
import time
import uuid
import datetime

# Blueprint dédié aux héros V2
hero_v2_bp = Blueprint('hero_v2', __name__)


@hero_v2_bp.route('/api/military/city/heroes/<city_id>', methods=['GET'])
def get_city_heroes_v2(city_id):
    """Récupère les héros disponibles dans une ville pour les attaques V2"""
    try:
        # Construire le chemin vers les fichiers de données
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(os.path.dirname(current_dir))
        savegame_file = os.path.join(base_dir, "gamedata", "savegame.json")
        
        with open(savegame_file, 'r', encoding='utf-8') as f:
            savegame_data = json.load(f)
        
        # Trouver la ville
        target_city = None
        for city in savegame_data.get('cities', []):
            if city.get('id') == city_id:
                target_city = city
                break
        
        if not target_city:
            return jsonify({
                'success': False,
                'message': f'Ville {city_id} introuvable'
            }), 404
        
        # Récupérer les héros de la garnison
        military_data = target_city.get('military', {})
        heroes_garrison = military_data.get('heroes', {})
        
        if not heroes_garrison:
            return jsonify({
                'success': True,
                'heroes': {}
            })
        
        # Charger les définitions des héros depuis heroes.json
        heroes_file = os.path.join(base_dir, "data", "heroes.json")
        heroes_definitions = {}
        try:
            with open(heroes_file, 'r', encoding='utf-8') as f:
                heroes_definitions = json.load(f)  # Les héros sont directement à la racine
        except FileNotFoundError:
            pass  # Pas de fichier de héros
        
        # Charger les données des héros joueurs depuis player_heroes.json
        player_heroes_file = os.path.join(base_dir, "gamedata", "player_heroes.json")
        player_heroes_data = {}
        try:
            with open(player_heroes_file, 'r', encoding='utf-8') as f:
                player_heroes_data = json.load(f)
        except FileNotFoundError:
            pass  # Pas de fichier de héros joueurs
        
        # Enrichir les données des héros
        enriched_heroes = {}
        
        for hero_instance_id, hero_garrison_data in heroes_garrison.items():
            hero_id = hero_garrison_data.get('hero_id')
            owner_id = hero_garrison_data.get('owner')
            status = hero_garrison_data.get('status', 'garrison')
            
            # Seulement les héros en garnison sont disponibles pour l'attaque
            if status != 'garrison':
                continue
                
            # OBLIGATOIRE : Trouver les vraies stats du héros dans player_heroes.json
            hero_stats = None
            if owner_id in player_heroes_data:
                hero_stats = player_heroes_data[owner_id]['heroes'].get(hero_instance_id)
            
            # Si le héros n'existe pas dans player_heroes.json, on l'ignore
            if not hero_stats:
                print(f"⚠️ [HERO_V2] Héros {hero_instance_id} non trouvé dans player_heroes.json, ignoré")
                continue
            
            # Récupérer les informations de base du héros depuis heroes.json
            hero_base_data = heroes_definitions.get(hero_stats['hero_id'], {})
            
            # Utiliser EXCLUSIVEMENT les vraies données de player_heroes.json + données de base
            enriched_heroes[hero_instance_id] = {
                'instance_id': hero_stats['instance_id'],
                'hero_id': hero_stats['hero_id'],
                'name': hero_base_data.get('name', 'Héros Inconnu'),
                'specialty': hero_base_data.get('specialty', 'unknown'),
                'rarity': hero_base_data.get('rarity', 'common'),
                'description': hero_base_data.get('description', ''),
                'current_level': hero_stats['current_level'],
                'current_experience': hero_stats['current_experience'],
                'battles_fought': hero_stats['battles_fought'],
                'victories': hero_stats['victories'],
                'defeats': hero_stats['defeats'],
                'units_killed': hero_stats.get('units_killed', 0),
                'units_lost': hero_stats.get('units_lost', 0),
                'status': hero_stats['status'],  # Utiliser le status de player_heroes.json
                'owner': owner_id,
                'calculated_stats': hero_stats['calculated_stats'],
                'calculated_bonuses': hero_stats['calculated_bonuses'],
                'experience_table': hero_base_data.get('experience_table', []),
                'progression': hero_base_data.get('progression', {})
            }
        
        return jsonify({
            'success': True,
            'heroes': enriched_heroes
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors du chargement des héros: {str(e)}'
        }), 500


@hero_v2_bp.route('/api/heroes/available', methods=['GET'])
def get_available_heroes():
    """Récupère tous les héros disponibles pour la sélection lors du déblocage de 'premiers_heros'"""
    try:
        # Construire le chemin vers les fichiers de données
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(os.path.dirname(current_dir))
        heroes_file = os.path.join(base_dir, "data", "heroes.json")
        
        # Charger le fichier heroes.json
        with open(heroes_file, 'r', encoding='utf-8') as f:
            heroes_data = json.load(f)
        
        # Retourner tous les héros disponibles
        return jsonify({
            'success': True,
            'heroes': heroes_data
        })
        
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'message': 'Fichier heroes.json introuvable'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors du chargement des héros: {str(e)}'
        }), 500


@hero_v2_bp.route('/api/heroes/select/<player_id>/<hero_id>', methods=['POST'])
def select_hero(player_id, hero_id):
    """Permet à un joueur de sélectionner son premier héros après avoir débloqué 'premiers_heros'"""
    try:
        # Construire le chemin vers les fichiers de données
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(os.path.dirname(current_dir))
        
        # Vérifier que le héros existe dans heroes.json
        heroes_file = os.path.join(base_dir, "data", "heroes.json")
        
        if not os.path.exists(heroes_file):
            print(f"❌ [HERO_SELECT] Fichier heroes.json introuvable: {heroes_file}")
            return jsonify({
                'success': False,
                'message': 'Fichier de configuration des héros introuvable'
            }), 500
        
        with open(heroes_file, 'r', encoding='utf-8') as f:
            heroes_data = json.load(f)
        
        if hero_id not in heroes_data:
            print(f"❌ [HERO_SELECT] Héros {hero_id} introuvable dans {list(heroes_data.keys())}")
            return jsonify({
                'success': False,
                'message': f'Héros {hero_id} introuvable'
            }), 400
        
        # Charger les données du joueur depuis players.json
        players_file = os.path.join(base_dir, "gamedata", "players.json")
        with open(players_file, 'r', encoding='utf-8') as f:
            players_data = json.load(f)
        
        # Trouver le joueur
        target_player = None
        for player in players_data.get('players', []):
            if player.get('id') == player_id:
                target_player = player
                break
        
        if not target_player:
            return jsonify({
                'success': False,
                'message': f'Joueur {player_id} introuvable'
            }), 404
        
        # Vérifier que le joueur a débloqué 'premiers_heros'
        if 'premiers_heros' not in target_player.get('unlocked_research', []):
            return jsonify({
                'success': False,
                'message': 'Vous devez débloquer la recherche "Premiers Héros" avant de pouvoir sélectionner un héros'
            }), 403
        
        # Charger ou créer le fichier player_heroes.json
        player_heroes_file = os.path.join(base_dir, "gamedata", "player_heroes.json")
        try:
            with open(player_heroes_file, 'r', encoding='utf-8') as f:
                player_heroes_data = json.load(f)
        except FileNotFoundError:
            player_heroes_data = {}
        
        # Vérifier que le joueur n'a pas déjà un héros
        if player_id in player_heroes_data and player_heroes_data[player_id].get('heroes'):
            return jsonify({
                'success': False,
                'message': 'Vous avez déjà sélectionné votre premier héros'
            }), 400
        
        # Trouver la ville active du joueur dans savegame.json
        savegame_file = os.path.join(base_dir, "gamedata", "savegame.json")
        with open(savegame_file, 'r', encoding='utf-8') as f:
            savegame_data = json.load(f)
        
        # Chercher une ville appartenant au joueur
        player_city = None
        for city in savegame_data.get('cities', []):
            if city.get('owner') == player_id:
                player_city = city
                break
        
        if not player_city:
            return jsonify({
                'success': False,
                'message': f'Aucune ville trouvée pour le joueur {player_id}'
            }), 404
        
        city_id = player_city.get('id')
        
        # Créer l'instance du héros avec des stats de niveau 1
        hero_definition = heroes_data[hero_id]
        hero_instance_id = f"hero_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        
        # Calculer les stats et bonus actuels (niveau 1)
        base_stats = hero_definition.get('base_stats', {})
        base_bonuses = hero_definition.get('base_bonuses', {})
        
        hero_instance = {
            'hero_id': hero_id,
            'instance_id': hero_instance_id,
            'current_level': 1,
            'current_experience': 0,
            'battles_fought': 0,
            'victories': 0,
            'defeats': 0,
            'units_killed': 0,
            'units_lost': 0,
            'times_died': 0,
            'acquired_date': datetime.datetime.now().isoformat(),
            'current_location': {
                'type': 'city',
                'city_id': city_id
            },
            'status': 'available',
            'calculated_stats': base_stats.copy(),
            'calculated_bonuses': base_bonuses.copy()
        }
        
        # Initialiser les données du joueur s'il n'existe pas
        if player_id not in player_heroes_data:
            player_heroes_data[player_id] = {
                'heroes': {},
                'active_hero': None
            }
        
        # Ajouter le héros au joueur
        player_heroes_data[player_id]['heroes'][hero_instance_id] = hero_instance
        player_heroes_data[player_id]['active_hero'] = hero_instance_id
        
        # Sauvegarder le fichier player_heroes.json
        with open(player_heroes_file, 'w', encoding='utf-8') as f:
            json.dump(player_heroes_data, f, indent=2, ensure_ascii=False)
        
        # Ajouter le héros à la garnison de la ville dans savegame.json
        if 'military' not in player_city:
            player_city['military'] = {}
        if 'heroes' not in player_city['military']:
            player_city['military']['heroes'] = {}
            
        # Ajouter le héros à la garnison de la ville
        player_city['military']['heroes'][hero_instance_id] = {
            'hero_id': hero_id,
            'instance_id': hero_instance_id,
            'owner': player_id,
            'status': 'garrison'
        }
        
        # Sauvegarder le fichier savegame.json
        with open(savegame_file, 'w', encoding='utf-8') as f:
            json.dump(savegame_data, f, indent=2, ensure_ascii=False)
        
        hero_name = hero_definition.get('name', hero_id)
        
        return jsonify({
            'success': True,
            'message': f'Félicitations ! Vous avez sélectionné {hero_name} comme votre premier héros !',
            'hero': {
                'instance_id': hero_instance_id,
                'hero_id': hero_id,
                'name': hero_name,
                'level': 1
            }
        })
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ [HERO_SELECT] Erreur: {str(e)}")
        print(error_trace)
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la sélection du héros: {str(e)}'
        }), 500


@hero_v2_bp.route('/api/heroes/level-up', methods=['POST'])
def level_up_hero():
    """Fait monter un héros de niveau si il a assez d'XP"""
    try:
        data = request.get_json()
        instance_id = data.get('instance_id')
        city_id = data.get('city_id')
        
        if not instance_id:
            return jsonify({
                'success': False,
                'message': 'ID d\'instance du héros manquant'
            }), 400
        
        # Construire le chemin vers les fichiers de données
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(os.path.dirname(current_dir))
        player_heroes_file = os.path.join(base_dir, "gamedata", "player_heroes.json")
        heroes_file = os.path.join(base_dir, "data", "heroes.json")
        
        # Charger les données des héros joueurs
        with open(player_heroes_file, 'r', encoding='utf-8') as f:
            player_heroes_data = json.load(f)
        
        # Charger les définitions des héros
        with open(heroes_file, 'r', encoding='utf-8') as f:
            heroes_definitions = json.load(f)
        
        # Trouver le héros
        hero_data = None
        owner_id = None
        for player_id, player_data in player_heroes_data.items():
            if instance_id in player_data.get('heroes', {}):
                hero_data = player_data['heroes'][instance_id]
                owner_id = player_id
                break
        
        if not hero_data:
            return jsonify({
                'success': False,
                'message': 'Héros introuvable'
            }), 404
        
        # Récupérer la définition du héros
        hero_definition = heroes_definitions.get(hero_data['hero_id'])
        if not hero_definition:
            return jsonify({
                'success': False,
                'message': 'Définition du héros introuvable'
            }), 404
        
        # Vérifier si le héros peut monter de niveau
        current_level = hero_data['current_level']
        current_xp = hero_data['current_experience']
        experience_table = hero_definition.get('experience_table', [])
        
        # Trouver l'XP requis pour le prochain niveau
        next_level = current_level + 1
        next_level_data = next((exp for exp in experience_table if exp['level'] == next_level), None)
        
        if not next_level_data:
            return jsonify({
                'success': False,
                'message': 'Niveau maximum atteint'
            }), 400
        
        if current_xp < next_level_data['xp_required']:
            return jsonify({
                'success': False,
                'message': f'XP insuffisant. {next_level_data["xp_required"] - current_xp} XP manquant'
            }), 400
        
        # Calculer les nouvelles stats
        progression = hero_definition.get('progression', {})
        base_stats = hero_definition.get('base_stats', {})
        base_bonuses = hero_definition.get('base_bonuses', {})
        
        # Calculer les stats avec progression
        new_calculated_stats = {}
        for stat_name, base_value in base_stats.items():
            progression_key = f"{stat_name}_per_level"
            if stat_name == "attack_melee":
                progression_key = "attack_per_level"
            elif stat_name == "defense_melee":
                progression_key = "defense_melee_per_level"
            elif stat_name == "defense_ranged":
                progression_key = "defense_ranged_per_level"
            
            progression_value = progression.get(progression_key, 0)
            calculated_value = base_value + (progression_value * (next_level - 1))
            
            # Arrondir les valeurs discrètes (champ de bataille)
            if stat_name in ['movement', 'range']:
                calculated_value = int(round(calculated_value))
            
            new_calculated_stats[stat_name] = calculated_value
        
        # Calculer les bonus avec progression
        new_calculated_bonuses = {}
        for bonus_name, base_value in base_bonuses.items():
            progression_key = f"{bonus_name}_per_level"
            progression_value = progression.get(progression_key, 0)
            calculated_value = base_value + (progression_value * (next_level - 1))
            
            # Arrondir movement_bonus (valeur discrète pour le champ de bataille)
            if bonus_name == 'movement_bonus':
                calculated_value = int(round(calculated_value))
            
            new_calculated_bonuses[bonus_name] = calculated_value
        
        # Mettre à jour le héros
        hero_data['current_level'] = next_level
        hero_data['calculated_stats'] = new_calculated_stats
        hero_data['calculated_bonuses'] = new_calculated_bonuses
        
        # Sauvegarder
        with open(player_heroes_file, 'w', encoding='utf-8') as f:
            json.dump(player_heroes_data, f, indent=2, ensure_ascii=False)
        
        # Préparer la réponse avec toutes les données nécessaires pour l'affichage
        hero_response = {
            'instance_id': hero_data['instance_id'],
            'hero_id': hero_data['hero_id'],
            'name': hero_definition.get('name', 'Héros Inconnu'),
            'specialty': hero_definition.get('specialty', 'unknown'),
            'rarity': hero_definition.get('rarity', 'common'),
            'description': hero_definition.get('description', ''),
            'current_level': hero_data['current_level'],
            'current_experience': hero_data['current_experience'],
            'battles_fought': hero_data['battles_fought'],
            'victories': hero_data['victories'],
            'defeats': hero_data['defeats'],
            'units_killed': hero_data.get('units_killed', 0),
            'units_lost': hero_data.get('units_lost', 0),
            'status': hero_data['status'],
            'calculated_stats': hero_data['calculated_stats'],
            'calculated_bonuses': hero_data['calculated_bonuses'],
            'experience_table': hero_definition.get('experience_table', []),
            'progression': hero_definition.get('progression', {})
        }
        
        return jsonify({
            'success': True,
            'message': f'Félicitations ! Votre héros est maintenant niveau {next_level}',
            'hero': hero_response
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors du level up: {str(e)}'
        }), 500
        
    except FileNotFoundError as e:
        return jsonify({
            'success': False,
            'message': f'Fichier de données introuvable: {str(e)}'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la sélection du héros: {str(e)}'
        }), 500


@hero_v2_bp.route('/api/player-heroes', methods=['GET'])
def get_all_player_heroes():
    """Récupère tous les héros de tous les joueurs depuis player_heroes.json"""
    try:
        # Construire le chemin vers player_heroes.json
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(os.path.dirname(current_dir))
        player_heroes_file = os.path.join(base_dir, "gamedata", "player_heroes.json")
        
        # Charger les données des héros
        with open(player_heroes_file, 'r', encoding='utf-8') as f:
            heroes_data = json.load(f)
        
        return jsonify(heroes_data)
        
    except FileNotFoundError:
        return jsonify({
            'error': 'Fichier player_heroes.json introuvable'
        }), 404
    except Exception as e:
        return jsonify({
            'error': f'Erreur lors du chargement des héros: {str(e)}'
        }), 500