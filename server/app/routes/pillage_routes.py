"""
Pillage Routes
==============

Routes Flask pour le système de pillage automatique et villages barbares.
Le pillage classique est maintenant automatique via battle_victory_manager.py
"""

from flask import Blueprint, request, jsonify
import json
import math
import os
import re
from datetime import datetime
from typing import Dict, Any, Tuple

pillage_bp = Blueprint('pillage', __name__)

class PillageManager:
    """Gestionnaire du système de pillage"""
    
    def __init__(self, data_manager=None):
        if data_manager is None:
            from app.data_manager import DataManager
            import os
            # Corriger le chemin : pointer vers le dossier server, pas server/data
            server_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.data_manager = DataManager(server_dir)
        else:
            self.data_manager = data_manager

    def calculate_pillage_resources(self, city_id: str, max_ships: int) -> Dict[str, Any]:
        """
        Calcule les ressources pillables d'une ville
        
        Args:
            city_id: ID de la ville à piller
            max_ships: Nombre maximum de bateaux disponibles
            
        Returns:
            Dict avec les ressources pillables et la capacité de transport
        """
        try:
            # Charger les données de la ville
            savegame = self.data_manager.load_savegame()
            city_data = None
            
            for city in savegame.get('cities', []):
                if city['id'] == city_id:
                    city_data = city
                    break
            
            if not city_data:
                return {'error': f'Ville {city_id} non trouvée'}
            
            # Calculer les capacités de stockage (réutiliser la logique existante)
            from app.routes.city_routes import calculate_storage_capacities
            storage_info = calculate_storage_capacities(city_data)
            
            # Ressources actuelles de la ville
            city_resources = city_data.get('resources', {})
            
            # Calculer les ressources pillables (différence entre actuel et sécurisé)
            pillable_resources = {}
            total_pillable_value = 0
            
            for resource_type, current_amount in city_resources.items():
                if resource_type in storage_info['secure']:
                    secure_amount = storage_info['secure'][resource_type]
                    pillable_amount = max(0, current_amount - secure_amount)
                    
                    if pillable_amount > 0:
                        pillable_resources[resource_type] = pillable_amount
                        total_pillable_value += pillable_amount
            
            # Capacité de transport (500 par bateau)
            ship_capacity = 500
            max_transport_capacity = max_ships * ship_capacity
            
            return {
                'pillable_resources': pillable_resources,
                'total_pillable': total_pillable_value,
                'max_ships': max_ships,
                'ship_capacity': ship_capacity,
                'max_transport_capacity': max_transport_capacity,
                'storage_info': storage_info
            }
            
        except Exception as e:
            return {'error': str(e)}


# Instance globale du gestionnaire
pillage_manager = PillageManager()

# Fonction utilitaire pour les villages barbares
def _load_barbarian_config():
    """Charge la configuration des villages barbares"""
    barbarian_config_path = os.path.join(pillage_manager.data_manager.base_dir, 'data', 'wild_camps_config.json')
    with open(barbarian_config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _extract_barbarian_level(city_id, battle_id=None):
    """Extrait le niveau d'un village barbare depuis battlefields_v2.json ou son ID"""
    # Priorité 1: Charger depuis battlefields_v2.json si battle_id fourni
    if battle_id:
        try:
            import os
            import json
            battlefields_path = os.path.join(pillage_manager.data_manager.gamedata_dir, 'battlefields_v2.json')
            with open(battlefields_path, 'r', encoding='utf-8') as f:
                battlefields = json.load(f)
            
            if battle_id in battlefields:
                battlefield = battlefields[battle_id]
                original_level = battlefield.get('original_barbarian_level')
                if original_level:
                    return original_level
        except Exception as e:
            print(f"⚠️ Erreur récupération niveau barbare depuis battlefield: {e}")
    
    # Fallback: extraire depuis le nom (DANGEREUX - donne des niveaux erronés)
    simple_match = re.search(r'wild_camp_(\d+)', city_id)
    if simple_match:
        return int(simple_match.group(1))
    
    level_match = re.search(r'level_(\d+)', city_id)
    if level_match:
        return int(level_match.group(1))
    
    return 1  # Niveau par défaut


# =========================================================================
# ROUTES API - Villages barbares uniquement
# =========================================================================
# Les routes de pillage classique ont été supprimées car le système
# est maintenant automatique via battle_victory_manager.py


@pillage_bp.route('/api/pillage/barbarian-preview/<int:level>', methods=['GET'])
def get_barbarian_pillage_preview(level):
    """
    Récupère les récompenses disponibles pour un village barbare selon son niveau
    """
    try:
        config = _load_barbarian_config()
        level_key = f'level_{level}'
        
        if level_key not in config:
            return jsonify({
                'success': False, 
                'error': f'Niveau {level} non trouvé'
            }), 404
        
        level_config = config[level_key]
        rewards = level_config.get('rewards', {})
        units = level_config.get('units', {})
        
        return jsonify({
            'success': True,
            'data': {
                'pillable_resources': rewards,
                'total_pillable': sum(rewards.values()),
                'units': units,
                'description': level_config.get('description', f'Village barbare niveau {level}'),
                'difficulty': level_config.get('difficulty', 'Inconnu'),
                'level': level,
                'is_wild_camp': True
            }
        }), 200
        
    except FileNotFoundError:
        return jsonify({
            'success': False, 
            'error': 'Configuration des villages barbares non trouvée'
        }), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@pillage_bp.route('/api/pillage/barbarian-execute', methods=['POST'])
def execute_barbarian_pillage():
    """
    Exécute le pillage d'un village barbare après victoire
    """
    try:
        data = request.get_json()
        battle_id = data.get('battle_id')
        city_id = data.get('city_id')  # wild_camp_X
        ships = data.get('ships', 1)
        attacker_id = data.get('attacker_id')
        
        if not all([battle_id, city_id, attacker_id]):
            return jsonify({
                'success': False, 
                'error': 'Données manquantes (battle_id, city_id, attacker_id)'
            }), 400
        
        # Extraire le niveau et charger la config
        level = _extract_barbarian_level(city_id, battle_id)
        config = _load_barbarian_config()
        
        level_key = f'level_{level}'
        if level_key not in config:
            return jsonify({
                'success': False, 
                'error': f'Niveau {level} non trouvé'
            }), 404
        
        
        level_config = config[level_key]
        rewards = level_config.get('rewards', {})
        
        # Calculer le pillage selon la capacité de transport
        ship_capacity = 500
        total_capacity = ships * ship_capacity
        total_rewards = sum(rewards.values())
        
        if total_capacity >= total_rewards:
            # Capacité suffisante : prendre tout
            pillaged_resources = rewards.copy()
            ships_used = max(1, math.ceil(total_rewards / ship_capacity))
        else:
            # Répartition proportionnelle
            ratio = total_capacity / total_rewards
            pillaged_resources = {resource: math.floor(amount * ratio) for resource, amount in rewards.items()}
            ships_used = ships
        
        total_pillaged = sum(pillaged_resources.values())
        
        # Ajouter les ressources aux contributions du battlefield pour le transport de retour
        import os
        import json
        
        # Charger directement le fichier JSON depuis gamedata/
        battlefield_path = os.path.join(pillage_manager.data_manager.gamedata_dir, 'battlefields_v2.json')
        with open(battlefield_path, 'r', encoding='utf-8') as f:
            battlefields = json.load(f)
        
        if battle_id in battlefields:
            battlefield = battlefields[battle_id]
            attackers_forces = battlefield.get('forces', {}).get('attackers', {})
            
            if attacker_id in attackers_forces:
                contributions = attackers_forces[attacker_id].get('contributions', [])
                if contributions:
                    # Ajouter les ressources pillées aux contributions
                    contributions[0]['pillage'] = pillaged_resources
                    
                    # Sauvegarder directement le fichier JSON
                    with open(battlefield_path, 'w', encoding='utf-8') as f:
                        json.dump(battlefields, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'data': {
                'pillaged_resources': pillaged_resources,
                'total_pillaged': total_pillaged,
                'ships_used': ships_used,
                'capacity_used': total_pillaged,
                'capacity_total': total_capacity
            }
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
