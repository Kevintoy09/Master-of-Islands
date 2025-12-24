"""
Resource Sites Database - Charge automatiquement depuis resource_sites_config.json
Ce fichier maintient la compatibilité avec l'ancien code qui importe SITE_TO_RESOURCE et RESOURCE_SITE_LEVELS
"""
import json
import os

# Charger la configuration depuis le JSON
# Depuis server/app/data/resource_sites_database.py -> server/data/resource_sites_config.json
_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'resource_sites_config.json')

try:
    with open(_config_path, 'r', encoding='utf-8') as f:
        _config_data = json.load(f)
        
    # Mapper les données JSON vers les constantes attendues
    SITE_TO_RESOURCE = _config_data.get('site_to_resource', {})
    
    # Convertir les niveaux en int pour rester compatible avec l'ancien code
    RESOURCE_SITE_LEVELS = {}
    for resource, levels_dict in _config_data.get('resource_site_levels', {}).items():
        RESOURCE_SITE_LEVELS[resource] = {}
        for level_str, level_data in levels_dict.items():
            RESOURCE_SITE_LEVELS[resource][int(level_str)] = level_data
            
except FileNotFoundError:
    print(f"⚠️ Fichier de configuration non trouvé: {_config_path}")
    # Fallback minimal
    SITE_TO_RESOURCE = {}
    RESOURCE_SITE_LEVELS = {}
except Exception as e:
    print(f"⚠️ Erreur lors du chargement de la configuration des sites de ressources: {e}")
    SITE_TO_RESOURCE = {}
    RESOURCE_SITE_LEVELS = {}

