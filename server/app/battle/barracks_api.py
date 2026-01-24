"""
barracks_api.py

DESCRIPTION : API REST pour la gestion des casernes et unités militaires
- Endpoints pour la production d'unités dans les casernes
- Gestion des files d'attente de production militaire
- API pour les statistiques d'unités et transferts entre villes
- Gestion des garnisons et attaques entre joueurs

UTILISÉ PAR : Interface de caserne et popups militaires côté client
"""
from flask import Blueprint, request, jsonify
from app.data_manager import DataManager
from app.battle.military_units_service import MilitaryUnitsService  # Version simplifiée
import json
import os
from datetime import datetime, timedelta

barracks_bp = Blueprint('barracks', __name__)

def get_base_dir():
    """Obtient le répertoire de base du projet"""
    current_file = os.path.abspath(__file__)
    # __file__ = .../server/app/battle/barracks_api.py
    # Nous voulons aller jusqu'à .../server/
    return os.path.dirname(os.path.dirname(os.path.dirname(current_file)))

@barracks_bp.route('/api/military/unit-stats', methods=['GET'])
def get_unit_stats_flat():
    """Retourne les statistiques de toutes les unités disponibles au format aplati"""
    try:
        # Charger depuis le nouveau chemin dans server/data/
        base_dir = get_base_dir()
        stats_file = os.path.join(base_dir, "data", "unit_stats.json")
        
        with open(stats_file, 'r', encoding='utf-8') as f:
            unit_stats = json.load(f)
        
        # Retourner uniquement classical_age
        return jsonify(unit_stats.get('classical_age', {}))
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors du chargement des stats: {str(e)}'
        }), 500

@barracks_bp.route('/api/military/production/queue/<city_id>', methods=['GET'])
def get_production_queue(city_id):
    """Retourne la file de production et traite les productions terminées"""
    try:
        import time
        data_manager = DataManager(get_base_dir())
        savegame_data = data_manager.load_savegame()
        military_service = MilitaryUnitsService(data_manager)
        
        city = next((c for c in savegame_data.get('cities', []) if c['id'] == city_id), None)
        if not city:
            return jsonify({'success': False, 'message': 'Ville non trouvée'}), 404
        
        if 'military' not in city:
            city['military'] = {}
        if 'production_queue' not in city['military']:
            city['military']['production_queue'] = []
        
        queue = city['military']['production_queue'][:]
        current_time = int(time.time())
        remaining = []
        units_completed = []  # Pour tracking sans déclencher la quête
        
        for item in queue:
            if current_time >= item['completion_time']:
                # Ajouter automatiquement à la garnison (comportement original)
                if item.get('is_batch') and 'units' in item:
                    # Batch : ajouter toutes les unités
                    for unit_data in item['units']:
                        military_service.add_units_to_garrison(
                            city_id, 
                            unit_data['type'], 
                            unit_data['quantity'], 
                            savegame_data
                        )
                        units_completed.append({
                            'type': unit_data['type'],
                            'quantity': unit_data['quantity']
                        })
                else:
                    # Ancienne méthode : une seule unité
                    military_service.add_units_to_garrison(
                        city_id, 
                        item['unit_type'], 
                        item['quantity'], 
                        savegame_data
                    )
                    units_completed.append({
                        'type': item['unit_type'],
                        'quantity': item['quantity']
                    })
            else:
                item['remaining_time'] = item['completion_time'] - current_time
                remaining.append(item)
        
        # Sauvegarder si des unités ont été complétées
        if len(remaining) < len(queue):
            city['military']['production_queue'] = remaining
            data_manager.save_savegame(savegame_data, force_save=True)
            
            # === HOOK QUÊTE: Recrutement d'unités (APRÈS sauvegarde) ===
            if len(units_completed) > 0:
                try:
                    from app.services.quest_service import quest_service
                    owner_id = city.get('owner')
                    players_data = data_manager.load_players()
                    players_list = players_data.get('players', [])
                    player = next((p for p in players_list if p['id'] == owner_id), None)
                    
                    if player:
                        username = player.get('username')
                        if username:
                            total_recruited = sum(u['quantity'] for u in units_completed)
                            quest_service.update_quest_progress(
                                username=username,
                                quest_id='mil_recruit_units',
                                increment=total_recruited
                            )
                except Exception as e:
                    import traceback
                    print(f"⚠️ Failed to update recruit quest: {e}")
                    print(traceback.format_exc())
        
        return jsonify({
            'success': True, 
            'queue': remaining,
            'units_completed': units_completed  # Info pour le frontend
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@barracks_bp.route('/api/military/production/start', methods=['POST'])
def start_production():
    """Démarre la production d'unités"""
    try:
        data = request.get_json()
        city_id = data.get('city_id')
        unit_type = data.get('unit_type')
        quantity = data.get('quantity', 1)
        
        if not city_id or not unit_type:
            return jsonify({
                'success': False,
                'message': 'city_id et unit_type sont requis'
            }), 400
        
        # Charger les données de la ville depuis savegame.json
        data_manager = DataManager(get_base_dir())
        savegame_data = data_manager.load_savegame()
        
        # Trouver la ville dans la liste des villes
        city = None
        cities = savegame_data.get('cities', [])
        for c in cities:
            if c.get('id') == city_id:
                city = c
                break
        
        if not city:
            return jsonify({
                'success': False,
                'message': 'Ville non trouvée'
            }), 404
        
        # Trouver le niveau de la caserne
        barracks_level = 0
        for building in city.get('buildings', []):
            building_name = building.get('name', '')
            if building_name == 'Caserne':
                barracks_level = building.get('level', 0)
                break
        
        if barracks_level == 0:
            return jsonify({
                'success': False,
                'message': 'Caserne non trouvée ou niveau 0'
            }), 400
        
        # Charger les stats de l'unité
        try:
            base_dir = get_base_dir()
            stats_file = os.path.join(base_dir, "data", "unit_stats.json")
            
            with open(stats_file, 'r', encoding='utf-8') as f:
                all_unit_stats = json.load(f)
            
            unit_stats = all_unit_stats.get('classical_age', {}).get(unit_type)
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Erreur chargement stats: {str(e)}'
            }), 500
        
        if not unit_stats:
            return jsonify({
                'success': False,
                'message': 'Type d\'unité non trouvé'
            }), 400
        
        # Vérifier les prérequis
        if unit_stats.get('required_barracks_level', 1) > barracks_level:
            return jsonify({
                'success': False,
                'message': f'Niveau de caserne insuffisant (requis: {unit_stats.get("required_barracks_level")})'
            }), 400
        
        # Vérifier la recherche requise
        required_research = unit_stats.get('required_research')
        if required_research and required_research != 'null':
            # Récupérer les recherches du joueur propriétaire depuis players.json
            owner_id = city.get('owner')
            players_data = data_manager.load_players()
            player = next((p for p in players_data.get('players', []) if p.get('id') == owner_id), None)
            player_researches = player.get('unlocked_research', []) if player else []
            
            if required_research not in player_researches:
                unit_name = unit_stats.get('name', unit_type)
                return jsonify({
                    'success': False,
                    'message': f'Recherche requise manquante pour {unit_name} : {required_research}'
                }), 400
        
        # Calculer les coûts ajustés selon le niveau de la caserne
        cost_reduction = min(0.45, (barracks_level - 1) * 0.05)
        production_cost = unit_stats.get('production_cost', {})
        
        total_cost = {}
        for resource, cost in production_cost.items():
            if cost > 0:
                if resource == 'population':
                    # La population n'a pas de réduction de coût
                    total_cost[resource] = cost * quantity
                else:
                    total_cost[resource] = int(cost * (1 - cost_reduction) * quantity)
        
        # Vérifier les ressources (utiliser une référence directe)
        if 'resources' not in city:
            city['resources'] = {}
        city_resources = city['resources']  # Référence directe, pas de copie
        
        for resource, cost in total_cost.items():
            if resource == 'population':
                # Pour la population, vérifier population_free
                available = city_resources.get('population_free', 0)
                if available < cost:
                    return jsonify({
                        'success': False,
                        'message': f'Population libre insuffisante: {cost} requis, {int(available)} disponible'
                    }), 400
            else:
                if city_resources.get(resource, 0) < cost:
                    return jsonify({
                        'success': False,
                        'message': f'Ressources insuffisantes: {resource} (requis: {cost}, disponible: {city_resources.get(resource, 0)})'
                    }), 400
        
        # Déduire les ressources (maintenant city_resources est une référence directe)
        for resource, cost in total_cost.items():
            if resource == 'population':
                # Déduire de population_total (la population quitte définitivement la ville pour devenir soldat)
                current_total = city_resources.get('population_total', 0)
                if isinstance(current_total, dict):
                    current_total = current_total.get('total', 0)
                
                new_total = current_total - cost
                city_resources['population_total'] = new_total
            else:
                city_resources[resource] = city_resources.get(resource, 0) - cost
        
        # Calculer le temps de production ajusté
        time_reduction = min(0.55, (barracks_level - 1) * 0.05)
        
        # Bonus de faction Fer : -10% sur le temps de production
        owner_id = city.get('owner')
        players_data = data_manager.load_players()
        player = next((p for p in players_data.get('players', []) if p.get('id') == owner_id), None)
        if player and player.get('faction') == 'iron':
            time_reduction += 0.10  # Bonus supplémentaire de 10%
            time_reduction = min(0.75, time_reduction)  # Cap maximum à 75%
        
        base_time = unit_stats.get('production_time', 60)
        adjusted_time = int(base_time * (1 - time_reduction) * quantity)
        
        # Créer la file de production dans military
        import time
        current_time = int(time.time())
        completion_time = current_time + adjusted_time
        
        if 'military' not in city:
            city['military'] = {}
        if 'production_queue' not in city['military']:
            city['military']['production_queue'] = []
        
        production_item = {
            'unit_type': unit_type,
            'quantity': quantity,
            'start_time': current_time,
            'completion_time': completion_time,
            'total_time': adjusted_time
        }
        
        city['military']['production_queue'].append(production_item)
        data_manager.save_savegame(savegame_data)
        
        return jsonify({
            'success': True,
            'message': f'{quantity}x {unit_stats.get("name", unit_type)} en production!',
            'production_time': adjusted_time,
            'completion_time': completion_time,
            'cost': total_cost,
            'new_resources': city_resources,
            'queue_item': production_item
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la production: {str(e)}'
        }), 500

@barracks_bp.route('/api/military/production/start-batch', methods=['POST'])
def start_batch_production():
    """Démarre la production de plusieurs types d'unités en une seule commande"""
    try:
        data = request.get_json()
        city_id = data.get('city_id')
        units = data.get('units', [])  # [{ unit_type, quantity }, ...]
        
        if not city_id or not units:
            return jsonify({
                'success': False,
                'message': 'city_id et units sont requis'
            }), 400
        
        # Charger les données
        data_manager = DataManager(get_base_dir())
        savegame_data = data_manager.load_savegame()
        
        city = next((c for c in savegame_data.get('cities', []) if c.get('id') == city_id), None)
        if not city:
            return jsonify({'success': False, 'message': 'Ville non trouvée'}), 404
        
        # Trouver le niveau de la caserne
        barracks_level = 0
        for building in city.get('buildings', []):
            if building.get('name', '') == 'Caserne':
                barracks_level = building.get('level', 0)
                break
        
        if barracks_level == 0:
            return jsonify({'success': False, 'message': 'Caserne non trouvée'}), 400
        
        # Charger les stats des unités
        base_dir = get_base_dir()
        stats_file = os.path.join(base_dir, "data", "unit_stats.json")
        with open(stats_file, 'r', encoding='utf-8') as f:
            all_unit_stats = json.load(f)
        classical_age_units = all_unit_stats.get('classical_age', {})
        
        # Calculer les coûts totaux et temps cumulé
        cost_reduction = min(0.45, (barracks_level - 1) * 0.05)
        time_reduction = min(0.55, (barracks_level - 1) * 0.05)
        
        # Bonus de faction Fer : -10% sur le temps de production
        owner_id = city.get('owner')
        players_data = data_manager.load_players()
        player = next((p for p in players_data.get('players', []) if p.get('id') == owner_id), None)
        if player and player.get('faction') == 'iron':
            time_reduction += 0.10  # Bonus supplémentaire de 10%
            time_reduction = min(0.75, time_reduction)  # Cap maximum à 75%
        
        total_cost = {'wood': 0, 'stone': 0, 'iron': 0, 'horse': 0, 'population': 0}
        total_time = 0
        unit_details = []
        
        for unit_data in units:
            unit_type = unit_data.get('unit_type')
            quantity = unit_data.get('quantity', 0)
            
            if quantity <= 0:
                continue
            
            unit_stats = classical_age_units.get(unit_type)
            if not unit_stats:
                return jsonify({'success': False, 'message': f'Unité {unit_type} non trouvée'}), 400
            
            # Vérifier prérequis
            if unit_stats.get('required_barracks_level', 1) > barracks_level:
                return jsonify({
                    'success': False,
                    'message': f'Niveau de caserne insuffisant pour {unit_stats.get("name")}'
                }), 400
            
            # Vérifier la recherche requise
            required_research = unit_stats.get('required_research')
            if required_research and required_research != 'null':
                # Récupérer les recherches du joueur propriétaire depuis players.json
                owner_id = city.get('owner')
                players_data = data_manager.load_players()
                player = next((p for p in players_data.get('players', []) if p.get('id') == owner_id), None)
                player_researches = player.get('unlocked_research', []) if player else []
                
                if required_research not in player_researches:
                    unit_name = unit_stats.get('name', unit_type)
                    return jsonify({
                        'success': False,
                        'message': f'Recherche requise manquante pour {unit_name} : {required_research}'
                    }), 400
            
            # Calculer les coûts
            production_cost = unit_stats.get('production_cost', {})
            for resource in ['wood', 'stone', 'iron', 'horse']:
                cost = production_cost.get(resource, 0)
                if cost > 0:
                    total_cost[resource] += int(cost * (1 - cost_reduction) * quantity)
            
            # Population sans réduction
            pop_cost = production_cost.get('population', 0)
            total_cost['population'] += pop_cost * quantity
            
            # Temps cumulé
            base_time = unit_stats.get('production_time', 60)
            adjusted_time = int(base_time * (1 - time_reduction) * quantity)
            total_time += adjusted_time
            
            unit_details.append({
                'type': unit_type,
                'name': unit_stats.get('name', unit_type),
                'quantity': quantity
            })
        
        # Vérifier les ressources
        if 'resources' not in city:
            city['resources'] = {}
        city_resources = city['resources']
        
        for resource, cost in total_cost.items():
            if cost == 0:
                continue
            if resource == 'population':
                available = city_resources.get('population_free', 0)
                if available < cost:
                    return jsonify({
                        'success': False,
                        'message': f'Population libre insuffisante: {cost} requis, {int(available)} disponible'
                    }), 400
            else:
                if city_resources.get(resource, 0) < cost:
                    return jsonify({
                        'success': False,
                        'message': f'{resource} insuffisant: {cost} requis, {city_resources.get(resource, 0)} disponible'
                    }), 400
        
        # Déduire les ressources
        for resource, cost in total_cost.items():
            if cost == 0:
                continue
            if resource == 'population':
                current_total = city_resources.get('population_total', 0)
                if isinstance(current_total, dict):
                    current_total = current_total.get('total', 0)
                city_resources['population_total'] = current_total - cost
            else:
                city_resources[resource] = city_resources.get(resource, 0) - cost
        
        # Créer UN SEUL item dans la queue avec toutes les unités
        import time
        current_time = int(time.time())
        completion_time = current_time + total_time
        
        if 'military' not in city:
            city['military'] = {}
        if 'production_queue' not in city['military']:
            city['military']['production_queue'] = []
        
        # Item de production avec toutes les unités
        production_item = {
            'units': unit_details,  # Liste de toutes les unités
            'start_time': current_time,
            'completion_time': completion_time,
            'total_time': total_time,
            'is_batch': True  # Indicateur pour différencier du système ancien
        }
        
        city['military']['production_queue'].append(production_item)
        data_manager.save_savegame(savegame_data)
        
        unit_names = ', '.join([f"{u['quantity']}x {u['name']}" for u in unit_details])
        
        return jsonify({
            'success': True,
            'message': f'{unit_names} en production !',
            'production_time': total_time,
            'completion_time': completion_time,
            'cost': total_cost,
            'queue_item': production_item
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la production batch: {str(e)}'
        }), 500

@barracks_bp.route('/api/military/production/cancel/<city_id>', methods=['POST'])
def cancel_production(city_id):
    """Annule la production en cours (sans recréditer les ressources)"""  
    try:
        data_manager = DataManager(get_base_dir())
        savegame_data = data_manager.load_savegame()
        
        city = next((c for c in savegame_data.get('cities', []) if c['id'] == city_id), None)
        if not city:
            return jsonify({'success': False, 'message': 'Ville non trouvée'}), 404
        
        if 'military' not in city:
            city['military'] = {}
        if 'production_queue' not in city['military']:
            city['military']['production_queue'] = []
        
        # Vider la queue de production (sans recréditer les ressources)
        city['military']['production_queue'] = []
        data_manager.save_savegame(savegame_data, force_save=True)
        
        return jsonify({
            'success': True,
            'message': 'Production annulée'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de l\'annulation: {str(e)}'
        }), 500

@barracks_bp.route('/api/military/city/units/<city_id>', methods=['GET'])
def get_city_units(city_id):
    """Retourne les unités d'une ville (garnison)"""
    try:
        data_manager = DataManager(get_base_dir())
        military_service = MilitaryUnitsService(data_manager)
        
        # Récupérer la garnison de la ville
        garrison = military_service.get_city_garrison(city_id)
        
        return jsonify({
            'success': True,
            'garrison': garrison,
            'units': garrison  # Compatibilité avec l'ancien système
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors du chargement des unités: {str(e)}'
        }), 500

@barracks_bp.route('/api/military/player/units/<player_id>', methods=['GET'])
def get_player_units(player_id):
    """Retourne toutes les unités d'un joueur organisées par localisation"""
    try:
        data_manager = DataManager(get_base_dir())
        military_service = MilitaryUnitsService(data_manager)
        
        # Récupérer toutes les unités du joueur
        player_units = military_service.get_all_player_units(player_id)
        
        return jsonify({
            'success': True,
            'data': player_units
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors du chargement des unités du joueur: {str(e)}'
        }), 500

@barracks_bp.route('/api/military/garrison/<city_id>', methods=['GET'])
def get_garrison(city_id):
    """Retourne la garnison (unités) d'une ville"""
    try:
        data_manager = DataManager(get_base_dir())
        military_service = MilitaryUnitsService(data_manager)
        
        garrison = military_service.get_city_garrison(city_id)
        
        return jsonify({
            'success': True,
            'garrison': garrison
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors du chargement de la garnison: {str(e)}'
        }), 500

# ❌ ENDPOINT SUPPRIMÉ - Utilisez /api/unit-transports avec type: 'attack' à la place
# L'ancien endpoint /api/military/attack a été supprimé car :
# 1. Il ne gérait pas le transport avec timer ni l'attente de bateaux
# 2. Il avait un système de combat bidon (juste simulation)
# 3. Il dupliquait la fonctionnalité de /api/unit-transports avec type: 'attack'
# 4. Il n'utilisait pas le système BattleCreationServiceV2 ni les battlefields

# ❌ ENDPOINT SUPPRIMÉ - Utilisez /api/unit-transports avec type: 'movement' à la place
# L'ancien endpoint /api/military/units/transfer a été supprimé car :
# 1. Il appelait une méthode move_units_between_cities() qui n'existait pas
# 2. Il dupliquait la fonctionnalité de /api/unit-transports 
# 3. Il n'avait pas de système d'attente de bateaux ni de timer

