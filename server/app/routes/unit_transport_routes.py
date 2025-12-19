"""
UNIT_TRANSPORT_ROUTES.PY - Routes API pour les transports d'unités
==================================================================
Fournit l'endpoint REST pour :
- Créer des transports d'unités (attaque, déplacement, renfort)

Utilise le TransportService existant avec des unités comme "ressources spéciales" préfixées par "unit_".
==================================================================
"""

from flask import Blueprint, request, jsonify
from app.data_manager import DataManager
from app.utils.battlefield_selector import determine_battlefield_template
import logging
import math
import json
import os
from datetime import datetime, timezone

# Initialiser le blueprint
unit_transport_routes = Blueprint('unit_transport_routes', __name__)

# Logger pour le debug
logger = logging.getLogger(__name__)

# Variable globale pour le data_manager
data_manager = None

def init_unit_transport_routes(dm: DataManager):
    """Initialise le data_manager pour les routes de transport d'unités"""
    global data_manager
    data_manager = dm



@unit_transport_routes.route('/api/unit-transports', methods=['POST'])
def create_unit_transport():
    """
    Crée un nouveau transport d'unités
    
    Body JSON attendu:
    {
        "player_id": "player_1",
        "source_city": "city_id_1",
        "destination_city": "city_id_2",
        "units": {"archer": 5, "infantry_heavy": 3},
        "heroes": ["hero_1", "hero_2"],  // Optionnel
        "type": "attack|movement|reinforcement",
        "battle_id": "battle_123"  // Optionnel, pour les renforts
    }
    
    Returns:
        JSON: {"success": true, "transport_id": "12", "message": "..."}
    """
    try:
        data = request.get_json()
        
        # Validation des paramètres requis
        required_fields = ['player_id', 'source_city', 'destination_city', 'units', 'type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Champ requis manquant: {field}"
                }), 400
        
        # Extraire les paramètres
        player_id = data['player_id']
        source_city = data['source_city']
        destination_city = data['destination_city']
        units = data['units']
        heroes = data.get('heroes', [])
        transport_type = data['type']
        battle_id = data.get('battle_id')
        ships_requested = data.get('ships', 1)  # Nombre de bateaux choisis par le joueur
        
        # Déterminer automatiquement le battlefield approprié pour les attaques
        if transport_type == 'attack':
            battlefield_template_id = determine_battlefield_template(destination_city, data_manager, player_id)
        else:
            battlefield_template_id = data.get('battlefield_template_id', 'default_working_v2')
        
        # Validation du type
        valid_types = ['attack', 'movement', 'reinforcement']
        if transport_type not in valid_types:
            return jsonify({
                "success": False,
                "error": f"Type de transport invalide. Valeurs acceptées: {valid_types}"
            }), 400
        
        # Utiliser le TransportService existant avec gestion des héros
        from app.business.transport_service import TransportService
        
        # Créer une instance du service de transport
        transport_service = TransportService(data_manager)
        
        # 1. VALIDATION DES HÉROS (si présents)
        if heroes:

            if not _validate_heroes_availability(player_id, source_city, heroes):
                return jsonify({
                    "success": False,
                    "error": "Un ou plusieurs héros ne sont pas disponibles"
                }), 400
        
        # 2. TRANSFORMER LES UNITÉS EN FORMAT "RESSOURCES" POUR LE TRANSPORT SERVICE
        unit_resources = {}
        for unit_type, quantity in units.items():
            if quantity > 0:
                unit_resources[f"unit_{unit_type}"] = quantity
        
        # 3. CALCULER LE NOMBRE DE BATEAUX NÉCESSAIRES
        total_entities = sum(units.values()) + len(heroes)
        minimum_ships = math.ceil(total_entities / 50)  # Minimum requis (50 entités par bateau)
        
        # Vérifier si le joueur a demandé assez de navires
        if ships_requested < minimum_ships:
            return {
                'success': False,
                'error': f'Nombre de navires insuffisant. Minimum requis: {minimum_ships}, demandé: {ships_requested}'
            }
        
        ships_needed = ships_requested  # Utiliser exactement ce que le joueur a demandé
        
        # 4. CALCULER LES TEMPS DE CHARGEMENT ET VOYAGE
        total_entities = sum(units.values()) + len(heroes)
        loading_time = total_entities / 10.0  # 10 unités par seconde (comme client)
        travel_time = _calculate_unit_travel_time(source_city, destination_city)
        
        # 5. CRÉER LE TRANSPORT AVEC LE SERVICE EXISTANT
        result = transport_service.create_transport(
            player_id=player_id,
            source_city_id=source_city,
            destination_city_id=destination_city,
            resources=unit_resources,  # Unités au format "unit_"
            ships_needed=ships_needed,
            loading_time=loading_time,
            travel_time=travel_time,
            transport_type=transport_type,
            battlefield_template_id=battlefield_template_id if transport_type == 'attack' else None
        )
        
        # 6. AJOUTER LES HÉROS AU TRANSPORT SI CRÉATION RÉUSSIE
        if result['success'] and heroes:
            transport_id = result['transport_id']
            if not _add_heroes_to_transport(transport_id, heroes, player_id, source_city):
                # Rollback si échec d'ajout des héros

                return jsonify({
                    "success": False,
                    "error": "Erreur lors de l'ajout des héros au transport"
                }), 400
        
        # 7. INFOS SPÉCIFIQUES AJOUTÉES DIRECTEMENT LORS DE LA CRÉATION
        
        if result['success']:
            return jsonify({
                'success': True,
                'transport_id': result['transport_id'],
                'message': f'Transport d\'unités créé avec succès (ID: {result["transport_id"]})'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        logger.error(f"Erreur création transport unités: {e}")
        return jsonify({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }), 500


@unit_transport_routes.route('/api/unit-transports/return-all', methods=['POST'])
def handle_battle_return_journey():
    """
    Route pour le voyage de retour de TOUS les transports d'une bataille:
    1. Trouve tous les transports en battle_waiting pour cette bataille
    2. Alimente leurs ressources avec les données du battlefield (distribution proportionnelle)
    3. Change leur status vers 'returning'
    """
    try:
        data = request.get_json()
        
        battle_id = data.get('battleId')
        
        if not battle_id:
            return jsonify({
                'success': False,
                'error': 'Paramètre requis: battleId'
            }), 400
        

        
        # Charger les transports
        transports_data = data_manager.load_transports()
        if not transports_data:
            return jsonify({'success': False, 'error': 'Impossible de charger les transports'}), 500
        
        # Charger le battlefield pour connaître la destination spécifique
        battlefields_data = data_manager.load_battlefields_v2()
        battlefield = battlefields_data.get(battle_id) if battlefields_data else None
        
        if not battlefield:
            return jsonify({
                'success': False,
                'error': f'Battlefield {battle_id} non trouvé'
            }), 404
        
        battlefield_location = battlefield.get('location')
        if not battlefield_location:
            return jsonify({
                'success': False,
                'error': f'Location du battlefield {battle_id} non trouvée'
            }), 404
        
        # Trouver SEULEMENT les transports de cette bataille spécifique
        battle_transports = []
        
        for transport in transports_data.get('transports', []):
            transport_destination = transport.get('destination_city')
            transport_status = transport.get('status')
            transport_type = transport.get('transport_type')
            
            if (transport_status == 'battle_waiting' and 
                transport_destination == battlefield_location and
                transport_type == 'attack'):
                
                # Ce transport participe à cette bataille spécifique
                battle_transports.append(transport)
        
        if not battle_transports:
            return jsonify({
                'success': False, 
                'error': f'Aucun transport en battle_waiting trouvé pour la bataille {battle_id} à la destination {battlefield_location}'
            }), 404
        
        # =====================================================================
        # NOUVELLE LOGIQUE: Séparer les unités selon leur origine
        # 1. Unités venues en transport (transport_ships > 0) → repartent en bateau
        # 2. Unités déjà sur place (transport_ships = 0) → retour direct
        # =====================================================================
        
        # Traiter d'abord les unités LOCALES (retour direct)
        _handle_local_units_return(battlefield, battle_id)
        
        # Puis traiter les transports pour le voyage retour
        returned_transports = []
        
        for transport in battle_transports:
            transport_id = transport.get('id')
            source_player = transport.get('source_player_id')
            
            # Récupérer les unités survivantes et pillage pour ce transport spécifique
            surviving_units, pillage_resources = _get_transport_battle_results(
                battlefield, transport_id, source_player
            )
            
            # Alimenter le transport avec les ressources pillées et unités
            transport_resources = transport.get('resources', {})
            
            # Ajouter les unités survivantes (format unit_)
            for unit_type, count in surviving_units.items():
                transport_resources[f"unit_{unit_type}"] = count
            
            # Ajouter les ressources pillées
            for resource, amount in pillage_resources.items():
                transport_resources[resource] = transport_resources.get(resource, 0) + amount
            
            transport['resources'] = transport_resources
            
            # Configurer le voyage retour
            _configure_return_journey(transport)
            
            returned_transports.append({
                'transport_id': transport_id,
                'player_id': source_player,
                'surviving_units': surviving_units,
                'pillage_resources': pillage_resources
            })
        
        # Sauvegarder les transports
        data_manager.save_transports(transports_data)
        

        
        # =================================================================
        # GÉNÉRATION DU RAPPORT : Calculer les données pour le rapport seulement
        # Les unités seront créditées quand les transports arrivent (transport_timer_service)
        # =================================================================
        troops_returned_to_cities = {}
        
        try:
            # Construire le rapport à partir des transports qui partent en retour
            for transport in returned_transports:
                player_id = transport['player_id']
                transport_data = next((t for t in battle_transports if t.get('id') == transport['transport_id']), None)
                from_city = transport_data.get('source_city') if transport_data else 'unknown'
                
                if player_id not in troops_returned_to_cities:
                    troops_returned_to_cities[player_id] = {
                        'to_city': from_city,
                        'units_returned': transport['surviving_units'],
                        'heroes_returned': []  # Traités par transport_timer_service
                    }
                


                
        except Exception as e:
            import traceback
            traceback.print_exc()
        
        # =================================================================
        # FONCTION 2 : CRÉER RAPPORT DE BATAILLE (copié de battle_end_v2.py)
        # =================================================================
        report_id = None
        try:
            
            battle_reports_filepath = data_manager._get_file_path('battle_reports.json')
            battle_reports = data_manager._load_json_file(battle_reports_filepath) or {}
            
            # Initialiser la structure si fichier vide
            if not battle_reports or 'reports' not in battle_reports:
                battle_reports = {'reports': []}
            
            import time
            from datetime import datetime
            report_id = f"report_v2_return_{battle_id}_{int(time.time())}"
            
            battle_report = {
                'id': report_id,
                'battle_id': battle_id,
                'version': '2.0',
                'timestamp': int(time.time()),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'location': battlefield['location'],
                'participants': battlefield['participants'],
                'outcome': 'retour_voyage_v2',
                'troops_returned': troops_returned_to_cities,
                'returned_transports': returned_transports,
                'summary': f"Retour voyage depuis bataille V2 a {battlefield['location']}. {len(troops_returned_to_cities)} joueurs ont recupere leurs troupes + {len(returned_transports)} transports en retour."
            }
            
            battle_reports['reports'].append(battle_report)
            
            data_manager._save_json_file(battle_reports_filepath, battle_reports, create_backup=False, force_save=True)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
        
        # =================================================================
        # FONCTION 3 : MISE À JOUR DES STATISTIQUES JOUEURS ET HÉROS
        # =================================================================
        try:
            from app.battle.battle_victory_manager import BattleVictoryManager
            victory_manager = BattleVictoryManager()
            
            # Déterminer qui a gagné en regardant la bataille
            # 1. Vérifier battle_result dans battlefield  
            winner_team = ''
            battle_result = battlefield.get('battle_result', {})
            if battle_result:
                winner_team = battle_result.get('winner_team', '')
            
            # 2. Si pas trouvé, vérifier winner_team direct
            if not winner_team:
                winner_team = battlefield.get('winner_team', '')
            
            # 3. Si encore pas trouvé, vérifier surrender_info
            if not winner_team:
                surrender_info = battlefield.get('surrender_info', {})
                if surrender_info and 'winning_players' in surrender_info:
                    # Si il y a des joueurs gagnants, déterminer l'équipe
                    winning_players = surrender_info['winning_players']
                    participants = battlefield.get('participants', {})
                    if winning_players:
                        # Vérifier dans quelle équipe est le premier gagnant
                        first_winner = winning_players[0]
                        if first_winner in participants.get('attackers', []):
                            winner_team = 'attackers'
                        elif first_winner in participants.get('defenders', []):
                            winner_team = 'defenders'
            
            # Déterminer si c'est un village barbare (DÉPLACÉ AVANT UTILISATION)
            location = battlefield.get('location', '')
            is_barbarian_village = location.startswith('barbarian_village_')
            
            # 4. NOUVELLE LOGIQUE: Pour les villages barbares, déduire la victoire du succès du transport
            if not winner_team and is_barbarian_village:
                # Si c'est un village barbare ET qu'il y a des transports qui reviennent avec du pillage
                # alors les attaquants ont gagné
                if returned_transports:
                    for transport_info in returned_transports:
                        pillage = transport_info.get('pillage_resources', {})
                        if pillage and any(amount > 0 for amount in pillage.values()):
                            winner_team = 'attackers'
                            print(f"🏆 [BARBARIAN_VICTORY] Victoire automatique détectée pour les attaquants contre {location}")
                            break
            
            # Mettre à jour les statistiques des joueurs
            victory_manager.update_player_stats_from_battle(battlefield, winner_team, is_barbarian_village)
            
            # Mettre à jour les statistiques des héros
            victory_manager.update_hero_stats_from_battle(battlefield, winner_team)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
        
        # =================================================================
        # FONCTION 4 : SUPPRIMER LES DONNÉES (copié de battle_end_v2.py)
        # =================================================================
        try:
            
            # Supprimer de battlefields_v2.json
            if battle_id in battlefields_data:
                del battlefields_data[battle_id]
                
                data_manager.save_battlefields_v2(battlefields_data, force_save=True)
            
            # Supprimer aussi de battlesv2.json (synchronisation)
            try:
                battlesv2_filepath = data_manager._get_file_path('battlesv2.json')
                battlesv2_data = data_manager._load_json_file(battlesv2_filepath) or {}
                if battle_id in battlesv2_data:
                    del battlesv2_data[battle_id]
                    
                    data_manager._save_json_file(battlesv2_filepath, battlesv2_data, create_backup=False, force_save=True)
            except Exception as battlesv2_error:
                # Non bloquant, continue même si battlesv2.json pose problème
                pass
                
        except Exception as e:
            import traceback
            traceback.print_exc()
        
        return jsonify({
            'success': True,
            'message': f'{len(returned_transports)} transports en voyage retour + unités survivantes renvoyées + bataille terminée',
            'returned_transports': returned_transports,
            'troops_returned_to_cities': troops_returned_to_cities,
            'report_id': report_id,
            'battle_id': battle_id
        })
        
    except Exception as e:
        logger.error(f"Erreur voyage retour bataille: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500




def _handle_local_units_return(battlefield: dict, battle_id: str):
    """
    Gère le retour direct des unités LOCALES (celles avec transport_ships = 0)
    Ces unités n'ont jamais pris de bateau et doivent retourner directement au savegame.json
    """
    try:
        # Charger les données de sauvegarde
        savegame = data_manager.load_savegame()
        cities = savegame.get('cities', [])
        
        # Parcourir toutes les forces du battlefield
        forces = battlefield.get('forces', {})
        
        for side in ['attackers', 'defenders']:
            side_forces = forces.get(side, {})
            
            for player_id, player_data in side_forces.items():
                contributions = player_data.get('contributions', [])
                
                for contrib in contributions:
                    # Identifier les contributions LOCALES (sans transport)
                    transport_ships = contrib.get('transport_ships', 0)
                    from_city = contrib.get('from_city', '')
                    
                    if transport_ships == 0 and from_city:
                        # Ces unités sont locales - retour direct
                        _credit_local_units_directly(cities, from_city, contrib, player_id)
        
        # Sauvegarder les changements
        data_manager.save_savegame(savegame, force_save=True)
        
    except Exception as e:
        print(f"❌ Erreur retour unités locales: {e}")


def _credit_local_units_directly(cities: list, city_id: str, contribution: dict, player_id: str):
    """
    Crédite directement les unités survivantes à leur ville d'origine et restaure les héros en garnison
    """
    # Trouver la ville
    city = next((c for c in cities if c.get('id') == city_id), None)
    if not city:
        print(f"❌ Ville {city_id} non trouvée pour crédit direct")
        return
    
    # Assurer la structure militaire
    if 'military' not in city:
        city['military'] = {}
    if 'garrison' not in city['military']:
        city['military']['garrison'] = {}
    
    garrison = city['military']['garrison']
    if player_id not in garrison:
        garrison[player_id] = {}
    
    # Créditer les unités survivantes
    surviving_units = contribution.get('units', {})
    for unit_type, count in surviving_units.items():
        if count > 0:
            if unit_type in garrison[player_id]:
                current_qty = garrison[player_id][unit_type].get('quantity', 0)
                garrison[player_id][unit_type]['quantity'] = current_qty + count
            else:
                garrison[player_id][unit_type] = {'quantity': count}
    
    # 🔧 CORRECTION: Restaurer les héros en statut 'garrison'
    surviving_heroes = contribution.get('heroes', [])
    if surviving_heroes:
        # Assurer la structure héros
        if 'heroes' not in city['military']:
            city['military']['heroes'] = {}
        
        heroes_section = city['military']['heroes']
        
        # Restaurer chaque héros en statut 'garrison'
        for hero_id in surviving_heroes:
            if hero_id in heroes_section:
                heroes_section[hero_id]['status'] = 'garrison'
                print(f"👑 Héros {hero_id} restauré en garnison dans {city_id}")
            else:
                # Le héros n'existe pas, créer une entrée de base
                heroes_section[hero_id] = {
                    'owner': player_id,
                    'status': 'garrison'
                }
                print(f"👑 Héros {hero_id} restauré (créé) en garnison dans {city_id}")
    
    print(f"🏠 Unités locales créditées à {city_id}: {surviving_units} + {len(surviving_heroes)} héros")


def _get_transport_battle_results(battlefield: dict, transport_id: str, player_id: str) -> tuple:
    """
    Récupère les unités survivantes et pillage pour un transport spécifique
    depuis les données du battlefield
    """
    surviving_units = {}
    pillage_resources = {}
    
    try:
        # Récupérer les forces du joueur attaquant
        attackers = battlefield.get('forces', {}).get('attackers', {})
        player_data = attackers.get(player_id, {})
        contributions = player_data.get('contributions', [])
        
        # Trouver la contribution correspondant à ce transport
        transport_contribution = None
        for contrib in contributions:
            if contrib.get('id') == transport_id:
                transport_contribution = contrib
                break
        
        if transport_contribution:
            # Calculer les unités survivantes = Contributions - Pertes
            initial_units = transport_contribution.get('units', {})
            player_losses = player_data.get('units_lost', {})
            
            for unit_type, initial_count in initial_units.items():
                if initial_count > 0:
                    # Chercher les pertes pour cette unité (PRIORITÉ au préfixe joueur)
                    losses = 0
                    prefixed_name = f"{player_id.split('_')[-1]}_{unit_type}"
                    
                    # Vérifier d'abord les pertes avec le préfixe joueur (ex: "6_archer")
                    if prefixed_name in player_losses:
                        losses = player_losses[prefixed_name]
                    # Sinon vérifier les pertes avec le nom standard
                    elif unit_type in player_losses:
                        losses = player_losses[unit_type]
                    
                    # Calculer les survivants
                    survivors = max(0, initial_count - losses)
                    if survivors > 0:
                        surviving_units[unit_type] = survivors
            
            # Récupérer le pillage de cette contribution
            pillage = transport_contribution.get('pillage', {})
            for resource, amount in pillage.items():
                if amount > 0:
                    pillage_resources[resource] = amount
        

        
    except Exception as e:
        print(f"❌ Erreur récupération résultats bataille: {e}")
    
    return surviving_units, pillage_resources


def _configure_return_journey(transport: dict):
    """
    Configure un transport pour le voyage retour
    """
    try:
        # Inverser source et destination pour le retour
        original_source = transport['source_city']
        original_destination = transport['destination_city']
        original_source_player = transport['source_player_id']
        original_dest_player = transport['destination_player_id']
        
        # Inverser pour le voyage retour
        transport['source_city'] = original_destination
        transport['destination_city'] = original_source  
        transport['source_player_id'] = original_dest_player
        transport['destination_player_id'] = original_source_player
        
        # Changer le status vers returning
        transport['status'] = 'returning'
        
        # Calculer temps de retour (même durée que l'aller)
        import time
        original_travel_time = transport.get('travel_time', 3600)  # Fallback 1h
        current_time = time.time()
        
        transport['departure_time'] = current_time
        transport['arrival_time'] = current_time + original_travel_time
        
        # Mettre à jour la timeline avec le voyage retour
        if 'timeline' not in transport:
            transport['timeline'] = {}
        
        transport['timeline']['return_start'] = round(current_time, 2)
        transport['timeline']['return_end'] = round(current_time + original_travel_time, 2)
        
        # Définir remaining_time pour que le TransportTimerService fonctionne correctement
        transport['remaining_time'] = int(original_travel_time)
        transport['last_update'] = current_time
        

        
    except Exception as e:
        print(f"❌ Erreur configuration retour: {e}")
        raise

def _create_protection_transport(player_id: str, source_city: str, target_city: str, 
                              units: dict, heroes: list = None, ships: int = 1) -> dict:
    """Crée un transport de protection simplifié"""
    try:
        import time
        import uuid
        

        
        # 1. Validation des unités disponibles dans la ville source
        savegame = data_manager.load_savegame()
        cities = savegame.get('cities', [])
        source_city_data = next((c for c in cities if c.get('id') == source_city), None)
        
        if not source_city_data:
            return {"success": False, "error": f"Ville source {source_city} non trouvée"}
        
        garrison = source_city_data.get('military', {}).get('garrison', {})
        player_garrison = garrison.get(player_id, {})
        
        # Vérifier disponibilité
        for unit_type, quantity in units.items():
            available = player_garrison.get(unit_type, {}).get('quantity', 0)
            if available < quantity:
                return {
                    "success": False,
                    "error": f"Pas assez de {unit_type}: {available} disponible(s), {quantity} demandé(s)"
                }
        
        # 2. Déduire les unités de la ville source
        for unit_type, quantity in units.items():
            current_qty = player_garrison[unit_type]['quantity']
            new_qty = current_qty - quantity
            
            if new_qty > 0:
                player_garrison[unit_type]['quantity'] = new_qty
            else:
                del player_garrison[unit_type]
        
        # Sauvegarder immédiatement
        data_manager.save_savegame(savegame, force_save=True)

        
        # 3. Calculer temps de voyage
        travel_time = _calculate_protection_travel_time(source_city, target_city)
        arrival_time = time.time() + travel_time
        
        # 4. Créer transport simplifié pour le timer
        transport_id = f"protect_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        current_time = time.time()
        
        # Format simple compatible avec le timer existant
        protection_transport = {
            "id": transport_id,
            "source_player_id": player_id,
            "source_city": source_city,
            "destination_city": target_city,
            "destination_player_id": _get_city_owner(target_city),
            "resources": {},  # Pas de ressources
            "units": units,   # Nos unités
            "heroes": heroes or [],
            "ships_needed": ships,
            "status": "traveling",
            "transport_type": "protection",
            "created_at": current_time,
            "loading_time": 0,
            "travel_time": travel_time,
            "remaining_time": travel_time,
            "last_update": current_time,
            "is_cross_player": True,
            "timeline": {
                "created": current_time,
                "loading_start": current_time,
                "loading_end": current_time,
                "travel_start": current_time,
                "travel_end": current_time + travel_time
            }
        }
        
        # 5. Sauvegarder transport
        transports_data = data_manager.load_transports()
        transports_data["transports"].append(protection_transport)
        save_success = data_manager.save_transports(transports_data, force_save=True)
        
        if save_success:

            return {
                "success": True,
                "transport_id": transport_id,
                "message": f"Protection lancée vers {target_city}",
                "arrival_time": arrival_time
            }
        else:
            return {"success": False, "error": "Erreur sauvegarde transport"}
            
    except Exception as e:

        return {
            "success": False,
            "error": f"Erreur création transport protection: {str(e)}"
        }

def _calculate_protection_travel_time(source_city: str, target_city: str) -> float:
    """Calcule le temps de voyage pour protection"""
    try:
        # Version simplifiée - utiliser la même logique que les autres transports
        islands_data = data_manager.load_universe()
        
        source_coords = None
        dest_coords = None
        
        for island in islands_data.get('islands', []):
            for element in island.get('elements', []):
                if element.get('type') == 'city':
                    if element['id'] == source_city:
                        source_coords = island['coords']
                    elif element['id'] == target_city:
                        dest_coords = island['coords']
        
        if not source_coords or not dest_coords:
            print(f"⚠️ Coordonnées non trouvées, utilisation durée par défaut")
            return 20.0
        
        # Calcul distance avec coefficient d'échelle
        import math
        from app.city_constants import TRANSPORT_CONSTANTS
        dx = abs(source_coords[0] - dest_coords[0])
        dy = abs(source_coords[1] - dest_coords[1])
        raw_distance = math.sqrt(dx*dx + dy*dy)
        distance = raw_distance * TRANSPORT_CONSTANTS['DISTANCE_SCALE_FACTOR']
        
        # Vitesse standard
        transport_speed = TRANSPORT_CONSTANTS['STANDARD_SPEED'] / 10
        travel_time = distance / transport_speed
        
        return max(travel_time, 15.0)  # Minimum 15 secondes
        
    except Exception as e:
        print(f"❌ Erreur calcul temps: {e}")
        return 30.0

def _get_city_owner(city_id: str) -> str:
    """Récupère le propriétaire d'une ville"""
    try:
        savegame = data_manager.load_savegame()
        cities = savegame.get('cities', [])
        city = next((c for c in cities if c.get('id') == city_id), None)
        return city.get('owner', 'unknown') if city else 'unknown'
    except:
        return 'unknown'

@unit_transport_routes.route('/api/unit-transports/protect', methods=['POST'])
def protect_city():
    """Protéger une ville en envoyant des unités défensives - utilise la logique d'attaque"""
    try:
        data = request.get_json()
        
        # Validation des données requises
        required_fields = ['attacker_city_id', 'target_city_id', 'player_id', 'units']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False, 
                    "error": f"Champ manquant: {field}"
                }), 400
        
        source_city = data['attacker_city_id']
        destination_city = data['target_city_id']
        player_id = data['player_id']
        units = data['units']
        heroes = data.get('heroes', [])
        ships = data.get('ships', 1)
        

        
        # Convertir unités au format "unit_" requis par le système de transport
        unit_resources = {f"unit_{unit_type}": quantity for unit_type, quantity in units.items()}
        
        # Calculer le temps de voyage
        travel_time = _calculate_unit_travel_time(source_city, destination_city)
        
        # Utiliser le TransportService existant
        from app.business.transport_service import TransportService
        transport_service = TransportService(data_manager)
        
        # Créer le transport de protection avec temps calculé
        result = transport_service.create_transport(
            player_id=player_id,
            source_city_id=source_city,
            destination_city_id=destination_city,
            resources=unit_resources,
            ships_needed=ships,
            loading_time=0,  # Pas de chargement pour protection
            travel_time=travel_time,  # Temps calculé
            transport_type="protection"
        )
        
        if result.get('success'):

            return jsonify({
                "success": True,
                "message": f"Protection lancée vers {destination_city}",
                "transport_id": result.get('transport_id')
            })
        else:

            return jsonify({
                "success": False,
                "error": result.get('error', 'Erreur inconnue')
            }), 400
            
    except Exception as e:

        return jsonify({
            "success": False,
            "error": f"Erreur serveur: {str(e)}"
        }), 500


@unit_transport_routes.route('/api/unit-transports/recall-protection', methods=['POST'])
def recall_protection():
    """Rappeler les transports de protection d'une ville"""
    try:
        data = request.get_json()
        player_id = data.get('player_id')
        city_id = data.get('city_id')  # Ville où sont les unités de protection
        
        if not player_id or not city_id:
            return jsonify({
                'success': False, 
                'error': 'player_id et city_id requis'
            }), 400
        

        
        # Charger les transports
        transports_data = data_manager.load_transports()
        if not transports_data:
            return jsonify({'success': False, 'error': 'Impossible de charger les transports'}), 500
        
        # Trouver les transports de protection en attente pour ce joueur et cette ville
        protection_transports = []
        for transport in transports_data.get('transports', []):
            if (transport.get('status') == 'protection_waiting' and
                transport.get('source_player_id') == player_id and
                transport.get('destination_city') == city_id):
                protection_transports.append(transport)
        
        if not protection_transports:
            return jsonify({
                'success': False, 
                'error': f'Aucun transport de protection en attente trouvé pour {player_id} à {city_id}'
            }), 404
        

        
        # Traiter chaque transport pour le voyage retour
        recalled_transports = []
        
        for transport in protection_transports:
            transport_id = transport.get('id')
            source_city = transport.get('source_city')
            

            
            # Retirer les unités de la garrison de la ville protégée
            _remove_protection_units_from_garrison(transport, city_id)  
            
            # Configurer le voyage de retour
            _configure_protection_return_journey(transport)
            
            recalled_transports.append({
                'transport_id': transport_id,
                'source_city': source_city,
                'destination_city': city_id,
                'return_time': transport.get('travel_time', 30)
            })
        
        # Sauvegarder les transports modifiés
        data_manager.save_transports(transports_data)
        

        
        return jsonify({
            'success': True,
            'message': f'{len(recalled_transports)} transports de protection rappelés',
            'recalled_transports': recalled_transports,
            'total_recalled': len(recalled_transports)
        })
        
    except Exception as e:
        logger.error(f"Erreur rappel protection: {e}")
        return jsonify({
            'success': False, 
            'error': f'Erreur serveur: {str(e)}'
        }), 500


def _remove_protection_units_from_garrison(transport, city_id):
    """Retirer les unités de protection de la garrison avant le retour"""
    try:
        player_id = transport['source_player_id']
        
        # Convertir les ressources en unités
        units_to_remove = {
            key.replace('unit_', ''): value 
            for key, value in transport.get('resources', {}).items() 
            if key.startswith('unit_')
        }
        
        if not units_to_remove:
            return
        
        # Utiliser le service militaire pour retirer les unités
        from app.battle.military_units_service import MilitaryUnitsService
        military_service = MilitaryUnitsService()
        
        for unit_type, quantity in units_to_remove.items():
            military_service.remove_units_from_garrison(city_id, player_id, unit_type, quantity)

        
    except Exception as e:
        logger.error(f"Erreur retrait unités protection: {e}")


def _configure_protection_return_journey(transport):
    """Configurer le voyage de retour pour un transport de protection"""
    current_time = datetime.now(timezone.utc).timestamp()
    
    # Échanger source et destination pour le retour
    original_source = transport['source_city']
    original_destination = transport['destination_city']
    
    transport['source_city'] = original_destination  # Maintenant c'est la source
    transport['destination_city'] = original_source  # Maintenant c'est la destination
    
    # Changer le statut vers RETURNING
    transport['status'] = 'returning'
    transport['remaining_time'] = transport.get('travel_time', 30)
    transport['last_update'] = current_time
    
    # Mettre à jour la timeline
    transport['timeline']['return_start'] = current_time
    transport['timeline']['return_end'] = current_time + transport.get('travel_time', 30)
    



def _calculate_unit_travel_time(source_city: str, destination_city: str) -> float:
    """Calculer le temps de voyage pour les transports d'unités"""
    try:
        # Charger les données d'îles
        universe_data = data_manager.load_universe()
        islands = universe_data.get('islands', [])
        
        source_coords = None
        dest_coords = None
        source_island_id = None
        dest_island_id = None
        
        # Fonction utilitaire simplifiée pour villages barbares
        def get_coords_for_city(city_id, islands):
            """Récupère les coordonnées d'une ville (normale ou barbare)"""
            # Si c'est un village barbare, extraire l'ID de l'île
            if city_id.startswith('barbarian_village_'):
                island_id = city_id.replace('barbarian_village_', '')
                for island in islands:
                    if island['id'] == island_id:
                        return island['coords'], island_id
            
            # Pour les villes normales
            for island in islands:
                for element in island.get('elements', []):
                    if element.get('type') == 'city' and element['id'] == city_id:
                        return island['coords'], island['id']
            
            return None, None
        
        # Récupérer les coordonnées des deux villes
        source_coords, source_island_id = get_coords_for_city(source_city, islands)
        dest_coords, dest_island_id = get_coords_for_city(destination_city, islands)
        
        if not source_coords or not dest_coords:

            return 30.0  # Valeur par défaut: 30 secondes
        
        # Vérifier si les deux villes sont sur la même île (transport intra-île)
        if source_island_id and dest_island_id and source_island_id == dest_island_id:

            return 10.0  # Temps fixe pour transport intra-île
        
        # Calculer la distance euclidienne pour transport inter-îles
        dx = abs(source_coords[0] - dest_coords[0])
        dy = abs(source_coords[1] - dest_coords[1])
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Calculer le temps de transport (aligné avec le client)
        transport_speed = 1.5  # unités par seconde (comme client)
        travel_time = distance / transport_speed
        

        return max(travel_time, 10.0)  # Minimum 10 secondes
        
    except Exception as e:

        return 30.0  # Valeur par défaut en cas d'erreur


# ========================================
# FONCTIONS DE GESTION DES HÉROS
# ========================================

def _validate_heroes_availability(player_id: str, city_id: str, heroes: list) -> bool:
    """Valide que les héros sont disponibles dans la ville source."""
    try:
        savegame = data_manager.load_savegame()
        cities = savegame.get('cities', [])
        city = next((c for c in cities if c.get('id') == city_id), None)
        
        if not city:
            print(f"❌ Ville {city_id} non trouvée pour validation héros")
            return False
        
        heroes_section = city.get('military', {}).get('heroes', {})
        
        # Vérifier chaque héros
        for hero_id in heroes:
            if hero_id not in heroes_section:
                print(f"❌ Héros {hero_id} non trouvé dans {city_id}")
                return False
            
            hero_data = heroes_section[hero_id]
            if hero_data.get('owner') != player_id:
                print(f"❌ Vous ne possédez pas le héros {hero_id}")
                return False
            
            if hero_data.get('status') != 'garrison':
                status = hero_data.get('status', 'unknown')
                print(f"❌ Héros {hero_id} non disponible (statut: {status})")
                return False
        
        print(f"✅ Validation héros réussie: {len(heroes)} héros disponibles")
        return True
        
    except Exception as e:
        print(f"❌ Erreur validation héros: {e}")
        return False


def _add_heroes_to_transport(transport_id: str, heroes: list, player_id: str, source_city: str) -> bool:
    """Ajoute les héros au transport et les déduit de la ville source."""
    try:
        # 1. Déduire les héros de la ville source
        if not _deduct_heroes_from_city(source_city, heroes, player_id):
            return False
        
        # 2. Ajouter les héros au transport
        transports_data = data_manager.load_transports()
        transports_list = transports_data.get('transports', [])
        
        # Trouver le transport dans la liste
        transport_found = False
        for transport in transports_list:
            if transport.get('id') == transport_id:
                transport['heroes'] = heroes
                transport_found = True
                print(f"👑 Héros ajoutés au transport {transport_id}: {heroes}")
                break
        
        if not transport_found:
            print(f"❌ Transport {transport_id} non trouvé dans la liste")
            return False
        
        # Sauvegarder
        if data_manager.save_transports(transports_data, force_save=True):
            print(f"👑 Héros ajoutés au transport {transport_id}: {heroes}")
            return True
        else:
            print(f"❌ Erreur sauvegarde transport avec héros")
            return False
            
    except Exception as e:
        print(f"❌ Erreur ajout héros au transport: {e}")
        return False


def _deduct_heroes_from_city(city_id: str, heroes: list, player_id: str) -> bool:
    """Déduit des héros d'une ville en les marquant comme 'en_transport'."""
    try:
        savegame = data_manager.load_savegame()
        cities = savegame.get('cities', [])
        city = next((c for c in cities if c.get('id') == city_id), None)
        
        if not city:
            print(f"❌ Ville {city_id} non trouvée pour déduction héros")
            return False
        
        heroes_section = city.get('military', {}).get('heroes', {})
        
        # Marquer tous les héros comme en transport
        for hero_id in heroes:
            if hero_id in heroes_section:
                heroes_section[hero_id]['status'] = 'en_transport'
                print(f"👑 Héros {hero_id} marqué comme en transport depuis {city_id}")
        
        # Sauvegarder
        return data_manager.save_savegame(savegame, force_save=True)
        
    except Exception as e:
        print(f"❌ Erreur déduction héros ville {city_id}: {e}")
        return False


# Fonction _add_attack_specific_data supprimée - battlefield_template_id ajouté directement lors de la création





