"""
Battlefield Selection Utilities
===============================

Système de sélection automatique de cartes de bataille selon le contexte :
- Villages barbares → Carte selon niveau (wild_camps_config.json)  
- Villes avec murailles → Carte fortifiée (city_lvl_1, city_lvl_2, etc.)
- Villes sans murailles → Carte ouverte (city_lvl_0)
"""

import json
import os


def determine_battlefield_template(target_city_id: str, data_manager, attacker_player_id: str = None) -> str:
    """
    Détermine le template de battlefield approprié selon le contexte d'attaque
    
    Args:
        target_city_id: ID de la ville cible
        attacker_player_id: ID du joueur attaquant (optionnel)
        data_manager: Instance du data manager
    
    Returns:
        str: ID du template de battlefield à utiliser
    """
    try:
        # Cas 1: Village barbare
        if target_city_id.startswith('wild_camp_'):
            try:
                # D'abord, essayer de trouver le vrai niveau dans le savegame
                village_level = None
                
                # Extraire l'island_id depuis target_city_id: wild_camp_7 -> island_id = "7"
                island_id = None
                village_parts = target_city_id.split('_')
                if len(village_parts) >= 3:
                    island_id = village_parts[2]
                
                # Charger les données du savegame pour trouver la vraie ville sur cette île
                savegame = data_manager.load_savegame()
                if savegame and 'cities' in savegame and island_id:
                    # Si on a l'attacker_player_id, chercher SA ville sur cette île
                    if attacker_player_id:
                        for city in savegame['cities']:
                            if (city.get('island_id') == island_id and 
                                city.get('owner') == attacker_player_id and
                                'wild_camp_level' in city):
                                village_level = city['wild_camp_level']
                                real_city_id = city.get('id', 'unknown')
                                print(f"🎯 [BATTLEFIELD] Village {target_city_id} -> ville de {attacker_player_id}: {real_city_id} sur île {island_id} -> niveau: {village_level}")
                                break
                    
                    # Sinon, prendre la première ville avec wild_camp_level sur cette île
                    if village_level is None:
                        for city in savegame['cities']:
                            if (city.get('island_id') == island_id and 
                                'wild_camp_level' in city):
                                village_level = city['wild_camp_level']
                                real_city_id = city.get('id', 'unknown')
                                print(f"🎯 [BATTLEFIELD] Village {target_city_id} -> ville générale {real_city_id} sur île {island_id} -> niveau: {village_level}")
                                break
                
                # Fallback: utiliser niveau 1 par défaut
                if village_level is None:
                    village_level = 1  # Par défaut niveau 1 si non trouvé
                    print(f"⚠️ [BATTLEFIELD] Village {target_city_id} -> niveau par défaut: {village_level}")
                
                if village_level is not None:
                    # Charger la configuration des villages barbares
                    barbarian_config_path = os.path.join(data_manager.base_dir, 'data', 'wild_camps_config.json')
                    with open(barbarian_config_path, 'r', encoding='utf-8') as f:
                        barbarian_config = json.load(f)
                    
                    # Récupérer le battlefield pour ce niveau
                    level_key = f"level_{village_level}"
                    if level_key in barbarian_config:
                        battlefield_file = barbarian_config[level_key].get('battlefield', 'default_working_v2.json')
                        print(f"🗺️ [BATTLEFIELD] Niveau {village_level} -> carte: {battlefield_file}")
                        return battlefield_file.replace('.json', '')
                    
            except (ValueError, KeyError, Exception) as e:
                print(f"❌ [BATTLEFIELD] Erreur traitement village barbare: {e}")
            
            # Fallback pour villages barbares
            return 'default_working_v2'
        
        # Cas 2: Ville de joueur - vérifier le niveau de muraille
        else:
            # Charger les données de sauvegarde
            savegame_path = os.path.join(data_manager.base_dir, 'gamedata', 'savegame.json')
            with open(savegame_path, 'r', encoding='utf-8') as f:
                savegame = json.load(f)
            
            # Trouver la ville cible
            target_city = None
            for city in savegame.get('cities', []):
                if city.get('id') == target_city_id:
                    target_city = city
                    break
            
            if target_city:
                # Chercher le bâtiment Muraille
                buildings = target_city.get('buildings', [])
                wall_level = 0
                
                for building in buildings:
                    if building.get('name') == 'Muraille' and building.get('status') == 'Terminé':
                        wall_level = building.get('level', 0)
                        break
                
                # 🗺️ Lire la carte depuis buildings.json
                try:
                    buildings_config_path = os.path.join(data_manager.base_dir, 'data', 'buildings.json')
                    with open(buildings_config_path, 'r', encoding='utf-8') as f:
                        buildings_config = json.load(f)
                    
                    # Trouver le battlefield_map pour ce niveau de muraille
                    wall_config = buildings_config.get('Muraille', {})
                    wall_levels = wall_config.get('levels', [])
                    
                    # Chercher le niveau correspondant
                    for level_data in wall_levels:
                        if level_data.get('level') == wall_level:
                            battlefield_map = level_data.get('effect', {}).get('battlefield_map')
                            if battlefield_map:
                                print(f"🗺️ [BATTLEFIELD] Ville {target_city_id} - Mur niveau {wall_level} -> carte: {battlefield_map}")
                                return battlefield_map
                            break
                except Exception as e:
                    print(f"⚠️ [BATTLEFIELD] Erreur lecture buildings.json: {e}")
                
                # Fallback si pas trouvé dans buildings.json
                if wall_level >= 1:
                    return f'city_lvl_{wall_level}'
                else:
                    return 'city_lvl_0'
            
            # Fallback si ville non trouvée
            return 'city_lvl_0'
    
    except Exception as e:
        print(f"[BATTLEFIELD] Erreur lors de la détermination du battlefield pour {target_city_id}: {e}")
        return 'default_working_v2'

