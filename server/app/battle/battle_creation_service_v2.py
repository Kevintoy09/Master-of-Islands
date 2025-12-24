"""
BattleCreationServiceV2.py

Service complet et autonome pour la création de batailles V2
- TOUT EST DANS CE FICHIER : logique, timer, transitions automatiques
- Structure simplifiée et modulaire
- Aucune dépendance vers l'ancien système
- Timer automatique intégré qui fait passer transport → arrivée → bataille
- Déduction automatique des troupes du savegame.json
- Application automatique des bonus de héros
"""

import json
import time
import os
import threading
from typing import Dict, Any, Optional
from datetime import datetime

# Import du gestionnaire de bonus de héros
from app.utils.wall_group_manager import WallGroupManager
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.battle.HeroBonusManager import HeroBonusManager

# Import du gestionnaire de groupes de murs
from app.utils.wall_group_manager import get_wall_group_manager

# Import du sélecteur de battlefield
from app.utils.battlefield_selector import determine_battlefield_template

# Fonction simple de synchronisation avec debug
def sync_to_client(force=False):
    """
    Synchronisation vers client COMPLÈTEMENT DÉSACTIVÉE
    
    SOLUTION TEMPORAIRE: Désactiver tout jusqu'à ce qu'on trouve 
    pourquoi ça recharge encore la page.
    """
    return


# Import circulaire évité - import direct dans la fonction


class BattleCreationServiceV2:
    """
    Service V2 pour la création et gestion complète des batailles
    - Timer automatique de transport (5 secondes)
    - Transitions automatiques des phases
    - Déduction des troupes du savegame.json
    - Structure organisée par statut
    """
    
    def __init__(self):
        # __file__ = .../server/app/battle/battle_creation_service_v2.py
        # Deux répertoires : gamedata/ pour fichiers de jeu, data/ pour configurations statiques
        base_server_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.gamedata_dir = os.path.join(base_server_dir, 'gamedata')
        self.static_data_dir = os.path.join(base_server_dir, 'data')
        self.savegame_path = os.path.join(self.gamedata_dir, 'savegame.json')
        self.battlefields_v2_path = os.path.join(self.gamedata_dir, 'battlefields_v2.json')
        
        # Gestionnaire de bonus de héros
        self.hero_bonus_manager = HeroBonusManager()
        
        # Service de stats de bataille avec bonus de forge
        from .battle_stats_service_v2 import get_battle_stats_service_v2
        self.battle_stats_service = get_battle_stats_service_v2()
        
        # Gestionnaire de groupes de murs (utilise data/ pour buildings.json)
        self.wall_group_manager = get_wall_group_manager(self.static_data_dir)
        
        # Service V2 initialisé
        
        # Initialiser le fichier battlefields_v2.json s'il n'existe pas
        self._initialize_battlefields_v2()
    
    def _initialize_battlefields_v2(self):
        """Initialise le fichier battlefields_v2.json avec la nouvelle structure simplifiée"""
        if not os.path.exists(self.battlefields_v2_path):
            initial_structure = {}
            
            with open(self.battlefields_v2_path, 'w', encoding='utf-8') as f:
                json.dump(initial_structure, f, indent=2, ensure_ascii=False)
            
            # Fichier initialisé
    
    def _compact_wall_positions(self, positions):
        """Convertit les positions de format array [[x,y]] vers format string compact 'x,y;x,y'"""
        if not positions:
            return ""
        if isinstance(positions, str):
            return positions  # Déjà compact
        return ";".join(f"{pos[0]},{pos[1]}" for pos in positions)
    
    def _expand_wall_positions(self, positions):
        """Convertit les positions de format string 'x,y;x,y' vers format array [[x,y]]"""
        if not positions:
            return []
        if isinstance(positions, list):
            return positions  # Déjà expansé
        return [[int(coord) for coord in pos.split(',')] for pos in positions.split(';') if pos.strip()]
    
    def _load_savegame(self) -> Dict[str, Any]:
        """Charge le fichier savegame.json via transition_utils"""
        try:
            from app.transition_utils import load_savegame_transition
            data = load_savegame_transition()
            if not data:
                            return {}
            return data
        except Exception as e:
                    return {}
    
    def _save_savegame(self, data: Dict[str, Any]):
        """Sauvegarde le fichier savegame.json via transition_utils"""
        try:
            from app.transition_utils import save_savegame_transition
            save_savegame_transition(data, force=True)
        except Exception as e:
            print(f"❌ [V2] Erreur lors de la sauvegarde du savegame: {e}")
            
    def _load_battlefields_v2(self) -> Dict[str, Any]:
        """Charge le fichier battlefields_v2.json et décompacte les positions"""
        try:
            with open(self.battlefields_v2_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Décompacter les positions et ajouter les wall_stats calculées
            wall_manager = WallGroupManager(self.static_data_dir)
            
            for bf_id, bf_data in data.items():
                wall_system = bf_data.get('wall_system', {})
                wall_groups = wall_system.get('wall_groups', {})
                
                # Décompacter les positions
                for group_key, group_data in wall_groups.items():
                    if 'positions' in group_data:
                        group_data['positions'] = self._expand_wall_positions(group_data['positions'])
                
                # Ajouter les wall_stats calculées dynamiquement si des groupes existent
                if wall_groups:
                    # Prendre le wall_level du premier groupe pour calculer les stats globales
                    first_group = next(iter(wall_groups.values()))
                    wall_level = first_group.get('wall_level', 1)
                    wall_system['wall_stats'] = wall_manager.get_wall_stats(wall_level)
            
            return data
        except Exception as e:
                    return {}
    
    def _save_battlefields_v2(self, data: Dict[str, Any]):
        """Sauvegarde le fichier battlefields_v2.json avec positions compactées et synchronise automatiquement"""
        try:
            # Créer une copie pour compacter sans modifier l'original
            compact_data = {}
            
            for bf_id, bf_data in data.items():
                compact_bf = bf_data.copy()
                
                # Compacter les positions des murs
                wall_system = compact_bf.get('wall_system', {})
                if wall_system and 'wall_groups' in wall_system:
                    compact_wall_system = wall_system.copy()
                    compact_wall_groups = {}
                    
                    for group_key, group_data in wall_system['wall_groups'].items():
                        compact_group = group_data.copy()
                        if 'positions' in compact_group:
                            compact_group['positions'] = self._compact_wall_positions(compact_group['positions'])
                        compact_wall_groups[group_key] = compact_group
                    
                    compact_wall_system['wall_groups'] = compact_wall_groups
                    compact_bf['wall_system'] = compact_wall_system
                
                compact_data[bf_id] = compact_bf
            
            with open(self.battlefields_v2_path, 'w', encoding='utf-8') as f:
                json.dump(compact_data, f, indent=2, ensure_ascii=False)
                    
            # Synchroniser automatiquement les unit_counts
            self._sync_unit_counts_for_battles(data)
            
            # Synchronisation désactivée (sera forcée seulement pour les renforts)
            sync_to_client(force=False)
            
        except Exception as e:
            pass
            
    def _sync_unit_counts_for_battles(self, data: Dict[str, Any]):
        """Synchronise automatiquement les unit_counts pour toutes les batailles actives"""
        try:
            # Importer la fonction depuis battle_routes_v2
            from app.routes.battle_routes_v2 import generate_unit_counts_structure, save_json_data, BATTLES_V2_FILE
            
            # Charger battles_v2.json
            battles_v2_path = os.path.join(self.gamedata_dir, 'battlesv2.json')
            with open(battles_v2_path, 'r', encoding='utf-8') as f:
                battles_data = json.load(f)
            
            # Synchroniser chaque bataille
            updated = False
            for battle_id in data.keys():
                if battle_id in battles_data:
                    # PRÉSERVER les données de tour avant la mise à jour
                    current_round = battles_data[battle_id].get('current_round')
                    current_player = battles_data[battle_id].get('current_player')
                    timestamp = battles_data[battle_id].get('timestamp')
                    
                    new_unit_counts = generate_unit_counts_structure(battle_id)
                    if new_unit_counts:
                        # Mettre à jour SEULEMENT les unit_counts
                        battles_data[battle_id]['unit_counts'] = new_unit_counts
                        
                        # RESTAURER explicitement les données de tour
                        if current_round is not None:
                            battles_data[battle_id]['current_round'] = current_round
                        if current_player is not None:
                            battles_data[battle_id]['current_player'] = current_player
                        if timestamp is not None:
                            battles_data[battle_id]['timestamp'] = timestamp
                        
                        updated = True
                                
            # Sauvegarder si mis à jour - UTILISER save_json_data avec compact=True
            if updated:
                save_json_data(BATTLES_V2_FILE, battles_data, compact=True)
                            
        except Exception as e:
            pass
            
    def _generate_battle_id(self) -> str:
        """Génère un ID unique pour la bataille"""
        import random
        import string
        current_time = int(time.time())
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"bfv2_{random_suffix}"
    
    def _get_wall_level_for_city(self, city_id: str, savegame_data: Dict[str, Any]) -> int:
        """
        Récupère le niveau de muraille d'une ville
        
        Args:
            city_id: ID de la ville
            savegame_data: Données du savegame
            
        Returns:
            Niveau de la muraille (0 si pas de muraille)
        """
        try:
            cities = savegame_data.get('cities', [])
            
            for city in cities:
                if city.get('id') == city_id:
                    buildings = city.get('buildings', [])
                    
                    for building in buildings:
                        if (building.get('name') == 'Muraille' and 
                            building.get('status') == 'Terminé'):
                            return building.get('level', 0)
                    break
            
            return 0
            
        except Exception as e:
                    return 0
    
    # ✅ Fonctions supprimées - logique simplifiée intégrée directement
    
    def _get_city_troops(self, city_id: str, savegame_data: Dict[str, Any]) -> Dict[str, Any]:
        """Récupère les troupes d'une ville depuis le savegame (agrégées par type d'unité)"""
        for city in savegame_data.get('cities', []):
            if city['id'] == city_id:
                garrison = city.get('military', {}).get('garrison', {})
                # Nouvelle structure: garrison[player_id][unit_type] -> agréger par unit_type
                aggregated_troops = {}
                for player_id, player_units in garrison.items():
                    if isinstance(player_units, dict):
                        for unit_type, unit_data in player_units.items():
                            if isinstance(unit_data, dict) and 'quantity' in unit_data:
                                if unit_type not in aggregated_troops:
                                    aggregated_troops[unit_type] = {'quantity': 0}
                                aggregated_troops[unit_type]['quantity'] += unit_data['quantity']
                return aggregated_troops
        return {}
    
    def _calculate_total_units(self, player_forces: Dict[str, Any]) -> Dict[str, int]:
        """
        Calcule les totaux d'unités depuis les contributions
        Évite de parcourir les contributions côté client
        """
        total_units = {}
        
        for contribution in player_forces.get('contributions', []):
            for unit_type, count in contribution.get('units', {}).items():
                total_units[unit_type] = total_units.get(unit_type, 0) + count
        
        return total_units
    
    def _get_city_owner(self, city_id: str, savegame_data: Dict[str, Any]) -> str:
        """Récupère le propriétaire d'une ville"""
        # Gestion spéciale pour les camps de sauvages
        if city_id.startswith('wild_camp_'):
            return 'wild_camp'  # Identifiant spécial pour les camps de sauvages
        
        # Logique normale pour les villes
        for city in savegame_data.get('cities', []):
            if city['id'] == city_id:
                owner = city.get('owner', 'unknown')
                return owner
        
        return 'unknown'
    
    def _deduct_troops_from_city(self, city_id: str, units_to_deduct: Dict[str, int], savegame_data: Dict[str, Any]) -> bool:
        """Déduit les troupes d'une ville et sauvegarde"""
        try:
            for city in savegame_data.get('cities', []):
                if city['id'] == city_id:
                    garrison = city.get('military', {}).get('garrison', {})
                    
                    # Vérifier si on a assez de troupes (nouvelle structure)
                    for unit_type, quantity in units_to_deduct.items():
                        total_available = 0
                        for player_id, player_units in garrison.items():
                            if isinstance(player_units, dict) and unit_type in player_units:
                                total_available += player_units[unit_type].get('quantity', 0)
                        if total_available < quantity:
                            return False
                    
                    # Déduire les troupes (priorité au propriétaire de la ville)
                    city_owner = city.get('owner')
                    for unit_type, quantity in units_to_deduct.items():
                        remaining = quantity
                        
                        # D'abord déduire du propriétaire
                        if city_owner in garrison and unit_type in garrison[city_owner]:
                            owner_qty = garrison[city_owner][unit_type].get('quantity', 0)
                            deduct_from_owner = min(owner_qty, remaining)
                            garrison[city_owner][unit_type]['quantity'] -= deduct_from_owner
                            if garrison[city_owner][unit_type]['quantity'] <= 0:
                                del garrison[city_owner][unit_type]
                            remaining -= deduct_from_owner
                        
                        # Déduire le reste chez les autres si nécessaire
                        if remaining > 0:
                            for player_id, player_units in garrison.items():
                                if remaining <= 0 or player_id == city_owner:
                                    continue
                                if isinstance(player_units, dict) and unit_type in player_units:
                                    player_qty = player_units[unit_type].get('quantity', 0)
                                    deduct = min(player_qty, remaining)
                                    garrison[player_id][unit_type]['quantity'] -= deduct
                                    if garrison[player_id][unit_type]['quantity'] <= 0:
                                        del garrison[player_id][unit_type]
                                    remaining -= deduct
                    
                    # Sauvegarder le savegame
                    self._save_savegame(savegame_data)
                    return True
            
            return False
            
        except Exception as e:
                    return False
    
    def _get_and_deduct_city_heroes(self, city_id: str, savegame_data: Dict[str, Any], player_id: str) -> list:
        """Récupère les héros d'une ville et les marque comme 'en_bataille'"""
        heroes_list = []
        try:
            for city in savegame_data.get('cities', []):
                if city['id'] == city_id:
                    heroes_section = city.get('military', {}).get('heroes', {})
                    
                    # Gérer le cas où heroes est une liste vide (pas de héros)
                    if isinstance(heroes_section, list):
                                            return []
                    
                    # Gérer le cas normal où heroes est un dictionnaire
                    if isinstance(heroes_section, dict):
                        for hero_id, hero_data in heroes_section.items():
                            if (hero_data.get('owner') == player_id and 
                                hero_data.get('status') == 'garrison'):
                                # Marquer le héros comme en bataille
                                hero_data['status'] = 'en_bataille'
                                heroes_list.append(hero_id)
                                                
                    # Sauvegarder les changements
                    self._save_savegame(savegame_data)
                    break
            
            return heroes_list
            
        except Exception as e:
                    return []
    
    def _deduct_attacker_heroes(self, city_id: str, heroes: list, savegame_data: Dict[str, Any], player_id: str) -> bool:
        """Déduit les héros sélectionnés de la ville attaquante"""
        if not heroes:
            return True
            
        try:
            for city in savegame_data.get('cities', []):
                if city['id'] == city_id:
                    heroes_section = city.get('military', {}).get('heroes', {})
                    
                    # Vérifier que tous les héros sont disponibles
                    for hero_id in heroes:
                        if (hero_id not in heroes_section or 
                            heroes_section[hero_id].get('status') != 'garrison' or
                            heroes_section[hero_id].get('owner') != player_id):
                                                    return False
                    
                    # Marquer les héros comme en bataille
                    for hero_id in heroes:
                        heroes_section[hero_id]['status'] = 'en_bataille'
                                        
                    # Sauvegarder les changements
                    self._save_savegame(savegame_data)
                    return True
            
            return False
            
        except Exception as e:
                    return False

    def _load_players_data(self) -> Dict[str, Any]:
        """Charge le fichier players.json"""
        try:
            players_path = os.path.join(self.gamedata_dir, 'players.json')
            with open(players_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
                    return {}

    def _save_players_data(self, data: Dict[str, Any]):
        """Sauvegarde le fichier players.json"""
        try:
            players_path = os.path.join(self.gamedata_dir, 'players.json')
            with open(players_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde des joueurs: {e}")
        
    def _check_and_deduct_ships(self, player_id: str, ships_needed: int) -> bool:
        """
        Vérifie que le joueur a assez de bateaux et les déduit
        
        Args:
            player_id: ID du joueur
            ships_needed: Nombre de bateaux requis
            
        Returns:
            bool: True si la déduction réussit, False sinon
        """
        try:
            players_data = self._load_players_data()
            
            # Trouver le joueur
            player = None
            for player_entry in players_data.get('players', []):
                if player_entry.get('id') == player_id:
                    player = player_entry
                    break
            
            if not player:
                            return False
            
            # Vérifier les bateaux disponibles
            ships_total = player.get('transport_ships_total', 0)
            if ships_total < ships_needed:
                            return False
            
            # Déduire les bateaux
            player['transport_ships_total'] = ships_total - ships_needed
                    
            # Sauvegarder
            self._save_players_data(players_data)
            return True
            
        except Exception as e:
                    return False

    def _calculate_team_moral_with_heroes(self, team_data: Dict[str, Any]) -> int:
        """
        Calcule le moral d'une équipe en incluant les bonus des héros
        Returns: moral total (base 100 + bonus héros)
        """
        heroes = team_data.get('heroes', [])
        return self.hero_bonus_manager.apply_moral_bonus_to_team(team_data, heroes)

    def _add_hero_bonuses_to_forces(self, forces_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialise le moral avec bonus des héros dès la création
        Logique: moral_initial = 100 + bonus_héros
        """
        updated_forces = forces_data.copy()
        
        # Traiter les attaquants - calculer moral avec bonus héros
        for player_id, team_data in updated_forces.get('attackers', {}).items():
            hero_bonus = self._get_team_hero_moral_bonus(team_data, player_id)
            initial_moral = 100 + hero_bonus
            team_data['moral'] = initial_moral
                
        # Traiter les défenseurs - calculer moral avec bonus héros  
        for player_id, team_data in updated_forces.get('defenders', {}).items():
            hero_bonus = self._get_team_hero_moral_bonus(team_data, player_id)
            initial_moral = 100 + hero_bonus
            team_data['moral'] = initial_moral
                
        return updated_forces

    def _get_team_hero_moral_bonus(self, team_data: Dict[str, Any], player_id: str) -> int:
        """
        Calcule le bonus moral total des héros d'une équipe
        """
        try:
            total_hero_bonus = 0
            
            # Parcourir toutes les contributions pour trouver les héros
            contributions = team_data.get('contributions', [])
            for contribution in contributions:
                heroes = contribution.get('heroes', [])
                for hero_id in heroes:
                    hero_bonus = self._get_hero_moral_bonus_by_id(hero_id, player_id)
                    total_hero_bonus += hero_bonus
                            
            return total_hero_bonus
            
        except Exception as e:
                    return 0

    def _get_hero_moral_bonus_by_id(self, hero_id: str, player_id: str) -> int:
        """
        Récupère le bonus moral d'un héros depuis player_heroes.json
        """
        try:
            player_heroes_path = os.path.join(self.gamedata_dir, 'player_heroes.json')
            with open(player_heroes_path, 'r', encoding='utf-8') as f:
                heroes_data = json.load(f)
            
            player_heroes = heroes_data.get(player_id, {}).get('heroes', {})
            hero_data = player_heroes.get(hero_id, {})
            
            # Récupérer le bonus moral depuis les bonuses calculés
            calculated_bonuses = hero_data.get('calculated_bonuses', {})
            moral_bonus = calculated_bonuses.get('moral_bonus', 0)
            
            return moral_bonus
            
        except Exception as e:
                    return 0

    def _apply_hero_bonuses_to_battle(self, battle_id: str) -> None:
        """
        Applique tous les bonus de héros à une bataille existante
        """
        try:
            updated_battle = self.hero_bonus_manager.update_battle_with_hero_bonuses(battle_id)
        except Exception as e:
            print(f"❌ Erreur lors de l'application des bonus de héros: {e}")
            
    # ✅ Méthode supprimée - plus de temporisation nécessaire
    
    def _transition_to_battle_ready(self, battle_id: str):
        """✅ Méthode obsolète - les battlefields sont créés directement en battle_ready"""
        
    def create_battle(self, attacker_city_id: str, target_city_id: str, units: Dict[str, int], 
                     heroes: list = None, ships: int = 1, battlefield_template_id: str = "default_working",
                     attacker_player_id: str = None, skip_troop_deduction: bool = False, transport_id: str = None) -> Dict[str, Any]:
        """
        Crée une nouvelle bataille V2 avec timer automatique
        
        Args:
            attacker_city_id: ID de la ville attaquante
            target_city_id: ID de la ville cible
            units: Dict des unités sélectionnées {unit_type: quantity}
            heroes: Liste des héros sélectionnés
            ships: Nombre de bateaux de transport
            battlefield_template_id: Template du champ de bataille
            attacker_player_id: ID du joueur attaquant
            skip_troop_deduction: Si True, ne déduit pas les troupes (déjà fait par le transport)
            transport_id: ID du transport d'attaque (pour lier transport et battlefield)
        
        Returns:
            Dict avec success, battle_id, battlefield_id
        """
        try:
            # Charger les données
            savegame_data = self._load_savegame()
            battlefields_data = self._load_battlefields_v2()
            
            # Récupérer le propriétaire de l'attaquant si pas fourni
            if not attacker_player_id:
                attacker_player_id = self._get_city_owner(attacker_city_id, savegame_data)
            
            # ✅ NOUVEAU : Vérifier et déduire les bateaux AVANT de créer la bataille (sauf si skip)
            if not skip_troop_deduction and not self._check_and_deduct_ships(attacker_player_id, ships):
                return {
                    "success": False,
                    "error": f"Pas assez de bateaux disponibles. Requis: {ships}"
                }
            
            # 🔥 NOUVEAU : Vérifier s'il existe déjà une bataille dans cette ville
            existing_battle_id = self._find_existing_battle_in_city(target_city_id, battlefields_data)
            
            if existing_battle_id:
                            return self._add_reinforcements_to_battle(
                    existing_battle_id, attacker_city_id, target_city_id, 
                    units, heroes, ships, attacker_player_id, 
                    savegame_data, battlefields_data, skip_troop_deduction, transport_id
                )
            else:
                            
                # Déterminer le template de battlefield selon le type de cible (ville normale, village barbare, etc.)
                from app.data_manager import DataManager
                # Obtenir le répertoire de base du projet
                current_file = os.path.abspath(__file__)
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
                dm = DataManager(base_dir)
                correct_template = determine_battlefield_template(target_city_id, dm, attacker_player_id)
                            
                return self._create_new_battle(
                    attacker_city_id, target_city_id, units, heroes, ships,
                    correct_template, attacker_player_id,  # ← Utiliser le bon template
                    savegame_data, battlefields_data, skip_troop_deduction, transport_id
                )
        except Exception as e:
                    return {
                "success": False,
                "error": str(e)
            }
    
    def get_battlefield(self, battle_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un battlefield par son ID avec la nouvelle structure
        
        Args:
            battle_id: ID du battlefield à récupérer
            
        Returns:
            Dict du battlefield ou None si non trouvé
        """
        try:
            battlefields_data = self._load_battlefields_v2()
            return battlefields_data.get(battle_id)
        except Exception as e:
            return None
    
    def get_all_battlefields(self) -> Dict[str, Any]:
        """
        Récupère tous les battlefields organisés par statut
        
        Returns:
            Dict complet des battlefields V2
        """
        try:
            return self._load_battlefields_v2()
        except Exception as e:
            return {}
    
    def get_battlefields_by_status(self, status: str) -> Dict[str, Any]:
        """
        Récupère tous les battlefields d'un statut donné avec la nouvelle structure
        
        Args:
            status: 'transport', 'battle_ready', ou 'completed'
            
        Returns:
            Dict des battlefields pour ce statut
        """
        try:
            battlefields_data = self._load_battlefields_v2()
            battles_by_status = {}
            
            # Filtrer par statut dans la nouvelle structure plate
            for battle_id, battlefield in battlefields_data.items():
                if battlefield.get('status') == status:
                    battles_by_status[battle_id] = battlefield
                    
            return battles_by_status
        except Exception as e:
                    return {}
    
    def get_player_active_battles(self, player_id: str) -> Dict[str, Any]:
        """
        Récupère toutes les batailles actives d'un joueur avec la nouvelle structure
        
        Args:
            player_id: ID du joueur
            
        Returns:
            Dict avec les batailles du joueur par statut
        """
        try:
            battlefields_data = self._load_battlefields_v2()
            player_battles = {
                "transport": {},
                "battle_ready": {},
                "completed": {}
            }
            
            # Parcourir toutes les batailles dans la nouvelle structure plate
            for battle_id, battlefield in battlefields_data.items():
                participants = battlefield.get('participants', {})
                if (player_id in participants.get('attackers', []) or 
                    player_id in participants.get('defenders', [])):
                    
                    status = battlefield.get('status', 'unknown')
                    if status in player_battles:
                        player_battles[status][battle_id] = battlefield
            
                    return player_battles
            
        except Exception as e:
                    return {"transport": {}, "battle_ready": {}, "completed": {}}
    
    def cleanup_old_completed_battles(self, max_age_hours: int = 24):
        """
        Nettoie les anciennes batailles complétées
        
        Args:
            max_age_hours: Âge maximum en heures pour garder les batailles complétées
        """
        try:
            battlefields_data = self._load_battlefields_v2()
            current_time = int(time.time())
            max_age_seconds = max_age_hours * 3600
            
            completed_battles = battlefields_data.get('completed', {})
            battles_to_remove = []
            
            for battle_id, battlefield in completed_battles.items():
                if 'completed_at' in battlefield:
                    age = current_time - battlefield['completed_at']
                    if age > max_age_seconds:
                        battles_to_remove.append(battle_id)
            
            # Supprimer les anciennes batailles
            for battle_id in battles_to_remove:
                del battlefields_data['completed'][battle_id]
                        
            if battles_to_remove:
                self._save_battlefields_v2(battlefields_data)
                        
        except Exception as e:
            pass
            
    def get_battlefield_status(self, battle_id: str) -> Dict[str, Any]:
        """
        Récupère le statut détaillé d'un battlefield avec informations de timer
        
        Args:
            battle_id: ID du battlefield
            
        Returns:
            Dict avec success, status, remaining_time, etc.
        """
        try:
            battlefield = self.get_battlefield(battle_id)
            
            if not battlefield:
                return {
                    "success": False,
                    "error": "Battlefield non trouvé"
                }
            
            current_time = int(time.time())
            status = battlefield.get('status')
            
            # Calculer le temps restant selon le statut
            remaining_time = 0
            if status == 'transport' and 'transport_end' in battlefield:
                remaining_time = max(0, battlefield['transport_end'] - current_time)
            
            return {
                "success": True,
                "battle_id": battle_id,
                "status": status,
                "remaining_time": remaining_time,
                "created_at": battlefield.get('created_at'),
                "transport_end": battlefield.get('transport_end'),
                "battle_start_time": battlefield.get('battle_start_time'),
                "participants": battlefield.get('participants', {}),
                "location": battlefield.get('location')
            }
            
        except Exception as e:
                    return {
                "success": False,
                "error": str(e)
            }

    def _find_existing_battle_in_city(self, target_city_id: str, battlefields_data: dict) -> str:
        """
        Vérifie s'il existe déjà une bataille dans la ville cible
        
        Returns:
            battle_id si trouvé, None sinon
        """
        for battle_id, battlefield in battlefields_data.items():
            if battlefield.get('location') == target_city_id:
                status = battlefield.get('status', '')
                if status in ['transport', 'battle_ready']:
                                    return battle_id
        return None
    
    def _add_reinforcements_to_battle(self, existing_battle_id: str, attacker_city_id: str, 
                                    target_city_id: str, units: dict, heroes: list, ships: int,
                                    attacker_player_id: str, savegame_data: dict, 
                                    battlefields_data: dict, skip_troop_deduction: bool = False, transport_id: str = None) -> dict:
        """
        Ajoute des renforts à une bataille existante
        """
        try:
            if not attacker_player_id:
                attacker_player_id = self._get_city_owner(attacker_city_id, savegame_data)
            
            # Déduire les troupes et héros (sauf si déjà fait par le transport)
            if not skip_troop_deduction:
                if not self._deduct_troops_from_city(attacker_city_id, units, savegame_data):
                    return {"success": False, "error": "Pas assez de troupes disponibles"}
                
                if heroes and not self._deduct_attacker_heroes(attacker_city_id, heroes, savegame_data, attacker_player_id):
                    return {"success": False, "error": "Héros non disponibles"}
            
            battlefield = battlefields_data[existing_battle_id]
            
            # Créer la nouvelle contribution
            new_contribution = {
                "from_city": attacker_city_id,
                "units": units,
                "heroes": heroes or [],
                "transport_ships": ships
            }
            
            # 🆕 Ajouter l'ID du transport si fourni
            if transport_id:
                new_contribution["id"] = transport_id
            
            # Vérifier si le joueur existe déjà dans les attackers
            if attacker_player_id in battlefield['forces']['attackers']:
                # 🔧 FIX: Vérifier si cette contribution (transport_id) existe déjà
                existing_contributions = battlefield['forces']['attackers'][attacker_player_id]['contributions']
                contribution_exists = False
                
                if transport_id:
                    for existing_contrib in existing_contributions:
                        if existing_contrib.get('id') == transport_id:
                            contribution_exists = True
                            break
                
                # Ajouter la contribution seulement si elle n'existe pas déjà
                if not contribution_exists:
                    battlefield['forces']['attackers'][attacker_player_id]['contributions'].append(new_contribution)
                
                # Mettre à jour les units_lost pour inclure les nouvelles unités
                for unit_type, count in units.items():
                    if unit_type not in battlefield['forces']['attackers'][attacker_player_id]['units_lost']:
                        battlefield['forces']['attackers'][attacker_player_id]['units_lost'][unit_type] = 0
            else:
                # Créer une nouvelle entrée pour ce joueur
                battlefield['forces']['attackers'][attacker_player_id] = {
                    "units_lost": {unit_type: 0 for unit_type in units.keys()},
                    "units_killed": {},
                    "xp_gained": 0,
                    "moral": 100,
                    "contributions": [new_contribution],
                    "total_units": dict(units)  # ✨ Pré-calcul des totaux
                }
                        
            # 🔧 Mettre à jour total_units après modification
            battlefield['forces']['attackers'][attacker_player_id]['total_units'] = self._calculate_total_units(
                battlefield['forces']['attackers'][attacker_player_id]
            )
            
            # Ajouter le joueur aux participants s'il n'y est pas déjà
            if attacker_player_id not in battlefield['participants']['attackers']:
                battlefield['participants']['attackers'].append(attacker_player_id)
            
            # 🦸 Mettre à jour hero_participants si des héros arrivent en renfort
            if not battlefield.get('hero_participants'):
                battlefield['hero_participants'] = {}
            
            if heroes and len(heroes) > 0:
                battlefield['hero_participants'][attacker_player_id] = heroes[0]  # Premier héros
            
            # Sauvegarder
            self._save_battlefields_v2(battlefields_data)
            self._save_savegame(savegame_data)
            
                    
            return {
                "success": True,
                "battle_id": existing_battle_id,
                "battlefield_id": existing_battle_id,
                "is_reinforcement": True,  # ← NOUVEAU FLAG
                "message": "Renforts ajoutés avec succès"
            }
            
        except Exception as e:
                    return {"success": False, "error": str(e)}
    
    def _create_new_battle(self, attacker_city_id: str, target_city_id: str, units: dict,
                          heroes: list, ships: int, battlefield_template_id: str,
                          attacker_player_id: str, savegame_data: dict, 
                          battlefields_data: dict, skip_troop_deduction: bool = False, transport_id: str = None) -> dict:
        """
        Crée une nouvelle bataille (logique originale)
        """
        try:
            # Récupérer le propriétaire de l'attaquant si pas fourni
            if not attacker_player_id:
                attacker_player_id = self._get_city_owner(attacker_city_id, savegame_data)
            
            # Récupérer le propriétaire du défenseur
            defender_player_id = self._get_city_owner(target_city_id, savegame_data)
            
                    
            # Déduire les troupes de la ville attaquante (sauf si déjà fait par le transport)
            if not skip_troop_deduction:
                if not self._deduct_troops_from_city(attacker_city_id, units, savegame_data):
                    return {"success": False, "error": "Pas assez de troupes disponibles"}
                
                # Déduire les héros attaquants 
                if heroes and not self._deduct_attacker_heroes(attacker_city_id, heroes, savegame_data, attacker_player_id):
                    return {"success": False, "error": "Héros non disponibles ou insuffisants"}
            
            # Créer les données de contribution pour l'attaquant (nouvelle structure)
            attacker_contribution = {
                "from_city": attacker_city_id,
                "units": units,
                "heroes": heroes or [],
                "transport_ships": ships
            }
            
            # 🆕 Ajouter l'ID du transport si fourni
            if transport_id:
                attacker_contribution["id"] = transport_id
            
            # Créer l'entrée joueur attaquant avec la nouvelle structure
            attacker_player_data = {
                "units_lost": {unit_type: 0 for unit_type in units.keys()},
                "units_killed": {},
                "xp_gained": 0,
                "moral": 100,  # Sera calculé plus tard avec les bonus de héros
                "contributions": [attacker_contribution]
            }
            
            # Générer l'ID de bataille
            battle_id = self._generate_battle_id()
            current_time = int(time.time())
            transport_end_time = current_time + 10
            
            # ✅ SIMPLE : DÉDUIRE TOUTES les unités de la garrison pour les défenseurs
            defenders_data = {}
            defender_participants = []
            
            # GESTION SPÉCIALE : Villages barbares
            if target_city_id.startswith('wild_camp_'):
                            
                # Récupérer l'île et le niveau du village barbare
                island_id = target_city_id.replace('wild_camp_', '')
                
                # Récupérer le niveau du village barbare pour l'attaquant
                barbarian_level = 1  # Niveau par défaut
                for city in savegame_data.get('cities', []):
                    if city['id'] == attacker_city_id:
                        barbarian_level = city.get('wild_camp_level', 1)
                        break
                
                # Charger les unités barbares depuis la configuration
                try:
                    import json
                    barbarian_config_path = os.path.join(self.static_data_dir, 'wild_camps_config.json')
                    
                    with open(barbarian_config_path, 'r', encoding='utf-8') as f:
                        barbarian_config = json.load(f)
                    
                    # Récupérer les unités pour le niveau correspondant
                    level_key = f"level_{barbarian_level}"
                    
                    if level_key in barbarian_config:
                        barbarian_units = barbarian_config[level_key].get('units', {})
                        
                        # Créer la contribution défensive barbare
                        barbarian_contribution = {
                            "player_id": "wild_camp",
                            "units": barbarian_units,
                            "from_city": target_city_id,
                            "heroes": [],
                            "transport_ships": 0
                        }
                        
                        # Créer les données des défenseurs barbares
                        defenders_data['wild_camp'] = {
                            "units_lost": {unit_type: 0 for unit_type in barbarian_units.keys()},
                            "units_killed": {},
                            "xp_gained": 0,
                            "moral": 100,
                            "contributions": [barbarian_contribution],
                            "total_units": dict(barbarian_units)  # ✨ Pré-calcul des totaux
                        }
                        defender_participants = ['wild_camp']
                    else:
                        defender_participants = ['wild_camp']
                        defenders_data['wild_camp'] = {
                            "units_lost": {},
                            "units_killed": {},
                            "xp_gained": 0,
                            "moral": 100,
                            "contributions": []
                        }
                    
                except Exception as e:
                    print(f"❌ Erreur chargement wild camp config: {e}")
                    defender_participants = ['wild_camp']
                    defenders_data['wild_camp'] = {
                        "units_lost": {},
                        "units_killed": {},
                        "xp_gained": 0,
                        "moral": 100,
                        "contributions": []
                    }
            
            else:
                # LOGIQUE NORMALE : Trouver la ville et sa garrison
                for city in savegame_data.get('cities', []):
                    if city['id'] == target_city_id:
                        garrison = city.get('military', {}).get('garrison', {})
                                            
                        # Pour chaque joueur dans la garrison
                        for player_id, player_units in garrison.items():
                            if not isinstance(player_units, dict):
                                continue
                                
                            # Extraire ET DÉDUIRE les unités avec quantité > 0
                            units_for_battle = {}
                            for unit_type, unit_data in player_units.items():
                                if isinstance(unit_data, dict):
                                    qty = unit_data.get('quantity', 0)
                                    if qty > 0:
                                        units_for_battle[unit_type] = qty
                                        # ✅ DÉDUCTION : Mettre la quantité à 0 dans la garrison
                                        unit_data['quantity'] = 0
                            
                            # Nettoyer la garrison - supprimer les unités avec quantité 0
                            units_to_remove = []
                            for unit_type, unit_data in player_units.items():
                                if isinstance(unit_data, dict) and unit_data.get('quantity', 0) <= 0:
                                    units_to_remove.append(unit_type)
                            
                            for unit_type in units_to_remove:
                                del player_units[unit_type]
                            
                            # Si ce joueur a des unités, l'ajouter comme défenseur
                            if units_for_battle:
                                # Gérer les héros (seulement pour le propriétaire)
                                player_heroes = []
                                if player_id == defender_player_id:
                                    player_heroes = self._get_and_deduct_city_heroes(target_city_id, savegame_data, player_id)
                                
                                # Créer la contribution défensive
                                defender_contribution = {
                                    "from_city": target_city_id,
                                    "units": units_for_battle,
                                    "heroes": player_heroes,
                                    "transport_ships": 0
                                }
                                
                                defenders_data[player_id] = {
                                    "units_lost": {unit_type: 0 for unit_type in units_for_battle.keys()},
                                    "units_killed": {},
                                    "xp_gained": 0,
                                    "moral": 100,
                                    "contributions": [defender_contribution],
                                    "total_units": dict(units_for_battle)  # ✨ Pré-calcul des totaux
                                }
                                
                                defender_participants.append(player_id)
                                                    
                        # ✅ IMPORTANT : Nettoyer la garrison si des joueurs n'ont plus d'unités
                        players_to_remove = []
                        for player_id, player_units in garrison.items():
                            if isinstance(player_units, dict) and len(player_units) == 0:
                                players_to_remove.append(player_id)
                        
                        for player_id in players_to_remove:
                            del garrison[player_id]
                        
                        break
            
            # Si aucune garrison, défenseur par défaut
            if not defender_participants:
                defender_participants = [defender_player_id]
            
            # ✅ NOUVEAU : Créer directement en statut battle_ready (plus de temporisation)
            battlefield_data = {
                "id": battle_id,
                "location": target_city_id,
                "status": "battle_ready",  # ← Directement prêt
                "created_at": current_time,
                "map": battlefield_template_id,
                "arrival_time": current_time,  # ← Arrivé immédiatement
                "participants": {
                    "attackers": [attacker_player_id],
                    "defenders": defender_participants
                },
                "forces": {
                    "attackers": {
                        attacker_player_id: attacker_player_data
                    },
                    "defenders": defenders_data
                },
                "hero_participants": {}  # 🦸 Mapping player_id -> hero_id pour déploiement auto
            }
            
            # 🦸 Construire le mapping hero_participants depuis les contributions
            # Pour attaquants
            for player_id, player_data in battlefield_data["forces"]["attackers"].items():
                for contribution in player_data.get("contributions", []):
                    hero_list = contribution.get("heroes", [])
                    if hero_list and len(hero_list) > 0:
                        battlefield_data["hero_participants"][player_id] = hero_list[0]  # Premier héros
            
            # Pour défenseurs
            for player_id, player_data in battlefield_data["forces"]["defenders"].items():
                for contribution in player_data.get("contributions", []):
                    hero_list = contribution.get("heroes", [])
                    if hero_list and len(hero_list) > 0:
                        battlefield_data["hero_participants"][player_id] = hero_list[0]  # Premier héros
            
            # Ajouter le niveau original du village barbare si c'est un combat contre un village barbare
            if target_city_id.startswith('wild_camp_') and 'barbarian_level' in locals():
                battlefield_data["original_barbarian_level"] = barbarian_level
            
            # Ajouter à la base de données
            battlefields_data[battle_id] = battlefield_data
            
            # 🔧 NOUVEAUTÉ : Enrichir avec les bonus de forge
            self.battle_stats_service.enrich_battle_with_forge_bonuses(battle_id)
            
            # Copier la hex map du template vers la bataille
            self._copy_template_hex_map(battlefield_data, battlefield_template_id)
            
            # Initialiser les groupes de murs
            wall_level = self._get_wall_level_for_city(target_city_id, savegame_data)
            if wall_level > 0:
                try:
                    wall_data = self.wall_group_manager.initialize_battlefield_walls(battlefield_template_id, wall_level)
                    if wall_data:
                        battlefield_data["wall_system"] = wall_data
                except Exception as e:
                    print(f"❌ Erreur initialisation murs: {e}")
                            
            # ✅ Plus de timer - battlefield directement prêt
            
            # Sauvegarder
            self._save_battlefields_v2(battlefields_data)
            self._save_savegame(savegame_data)
            
            # 🎯 NOUVEAU: Créer l'entrée de base dans battlesv2.json dès la création
            self._create_base_battle_entry(battle_id, current_time, target_city_id)
            
            # 🏴‍☠️ DÉTECTION ATTAQUE WILD CAMP POUR QUÊTES
            if target_city_id.startswith('wild_camp_'):
                try:
                    # Import ici pour éviter les imports circulaires
                    from app.services.quest_service import QuestService
                    quest_service = QuestService()
                    
                    # Récupérer le username à partir de l'ID du joueur
                    players_file = os.path.join(os.path.dirname(self.savegame_path), 'players.json')
                    if os.path.exists(players_file):
                        with open(players_file, 'r', encoding='utf-8') as f:
                            players = json.load(f)
                            username = None
                            for player in players.get('players', []):
                                if player.get('id') == attacker_player_id:
                                    username = player.get('username')
                                    break
                            
                            if username:
                                # Incrémenter la quête quotidienne "mil_attack_barbarians" si elle existe
                                quest_service.update_quest_progress(username, 'mil_attack_barbarians', increment=1)
                except Exception as e:
                    print(f"⚠️ [QUEST] Erreur lors de la mise à jour de la quête d'attaque de sauvages: {e}")
                            
            return {
                "success": True,
                "battle_id": battle_id,
                "battlefield_id": battle_id,
                "arrival_time": current_time,  # Arrivé immédiatement
                "status": "battle_ready",  # ← Nouveau statut
                "is_reinforcement": False
            }
            
        except Exception as e:
                    return {"success": False, "error": str(e)}

    def _generate_reinforcement_key(self, player_id: str, attackers_dict: dict) -> str:
        """
        Génère une clé simple pour les renforts: player_3_1, player_3_2, etc.
        """
        # Compter combien d'entrées existent déjà pour ce joueur
        counter = 1
        while f"{player_id}_{counter}" in attackers_dict:
            counter += 1
        
        return f"{player_id}_{counter}"

    def _generate_unit_counts_from_battlefield(self, battle_id: str) -> dict:
        """
        Génère la structure unit_counts depuis battlefields_v2.json
        avec deployed=0 et total=somme des contributions
        """
        try:
            battlefields_file = os.path.join(self.gamedata_dir, 'battlefields_v2.json')
            with open(battlefields_file, 'r', encoding='utf-8') as f:
                battlefields_data = json.load(f)
            
            if battle_id not in battlefields_data:
                return {}
            
            battlefield = battlefields_data[battle_id]
            unit_counts = {}
            
            # Traiter attaquants et défenseurs
            forces = battlefield.get('forces', {})
            for side in ['attackers', 'defenders']:
                for player_id, player_forces in forces.get(side, {}).items():
                    unit_counts[player_id] = {}
                    
                    # Calculer totaux depuis contributions
                    contributions = player_forces.get('contributions', [])
                    for contribution in contributions:
                        # Traiter unités
                        units = contribution.get('units', {})
                        for unit_type, count in units.items():
                            if unit_type not in unit_counts[player_id]:
                                unit_counts[player_id][unit_type] = {'deployed': 0, 'total': 0}
                            unit_counts[player_id][unit_type]['total'] += count
                        
                        # Traiter héros
                        heroes = contribution.get('heroes', [])
                        if heroes:
                            if 'heroes' not in unit_counts[player_id]:
                                unit_counts[player_id]['heroes'] = {'deployed': 0, 'total': 0}
                            unit_counts[player_id]['heroes']['total'] += len(heroes)
            
            return unit_counts
            
        except Exception as e:
            print(f"❌ Erreur génération unit_counts: {e}")
            return {}

    def _create_base_battle_entry(self, battle_id: str, timestamp: int, location: str):
        """
        Crée l'entrée de base dans battlesv2.json dès la création de la battlefield
        Cette approche évite les problèmes de synchronisation lors du déploiement
        """
        try:
            battles_file = os.path.join(self.gamedata_dir, 'battlesv2.json')
            
            # Charger le battlefield pour obtenir les participants
            battlefields_file = os.path.join(self.gamedata_dir, 'battlefields_v2.json')
            with open(battlefields_file, 'r', encoding='utf-8') as f:
                battlefields_data = json.load(f)
            
            if battle_id not in battlefields_data:
                return
                
            battlefield = battlefields_data[battle_id]
            participants = battlefield.get('participants', {})
            attackers = participants.get('attackers', [])
            defenders = participants.get('defenders', [])
            
            attacker_player_id = attackers[0] if attackers else "attacker"
            defender_player_id = defenders[0] if defenders else "defender"

            # Charger ou créer battlesv2.json
            try:
                with open(battles_file, 'r', encoding='utf-8') as f:
                    battles_data = json.load(f)
                    # ✅ FIX: Convertir [] en {} si nécessaire (problème Railway)
                    if isinstance(battles_data, list):
                        battles_data = {}
            except:
                battles_data = {}
            
            # Générer unit_counts depuis battlefield
            unit_counts = self._generate_unit_counts_from_battlefield(battle_id)
            
            # 🦸 Copier hero_participants depuis battlefield
            hero_participants = battlefield.get('hero_participants', {})
            
            # Créer l'entrée de base avec unit_counts intégrés
            base_entry = {
                "battleId": battle_id,
                "unit_counts": unit_counts,
                "hero_participants": hero_participants,
                "location": location,
                "timestamp": timestamp,
                "current_round": 1,
                "current_player": attacker_player_id,
                "turn_started_at": int(time.time() * 1000),
                "teams": {
                    attacker_player_id: [],
                    defender_player_id: []
                }
            }
            
            battles_data[battle_id] = base_entry
            
            # Sauvegarder avec format compact unifié
            try:
                from app.routes.battle_routes_v2 import save_battles_ultra_compact
                            
                with open(battles_file, 'w', encoding='utf-8') as f:
                    json_str = save_battles_ultra_compact(battles_data)
                    f.write(json_str)
            except ImportError:
                with open(battles_file, 'w', encoding='utf-8') as f:
                    json.dump(battles_data, f, ensure_ascii=False, indent=2)
            
            # Synchronisation désactivée
            sync_to_client(force=False)
            
        except Exception as e:
            print(f"❌ [BATTLE-CREATE] Erreur: {e}")
            import traceback
            traceback.print_exc()
        
        return {
            "current_player": attacker_player_id,
            "turn_started_at": int(time.time() * 1000),
            "teams": {
                attacker_player_id: [],
                defender_player_id: []
            }
        }
    
    def _copy_template_hex_map(self, battlefield_data, battlefield_template_id):
        """NE COPIE PLUS le hexMap - il reste dans le template pour économiser de l'espace"""
        # ✅ Simplification: Le hexMap reste dans le template
        # Les wall_groups sont calculés une fois et stockés directement
        # Plus besoin de dupliquer toute la carte
    

# Instance singleton pour le service
_battle_creation_service_v2 = None

def get_battle_creation_service_v2() -> BattleCreationServiceV2:
    """Retourne l'instance singleton du service V2"""
    global _battle_creation_service_v2
    if _battle_creation_service_v2 is None:
        _battle_creation_service_v2 = BattleCreationServiceV2()
    return _battle_creation_service_v2


