# -*- coding: utf-8 -*-
"""
Service de gestion des quêtes quotidiennes et principales
Gère la progression, les récompenses et le niveau des joueurs
"""

import json
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import io


class QuestService:
    def __init__(self):
        # quest_service.py est dans server/app/services/
        # On remonte de 2 niveaux pour atteindre server/
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.quests_config_path = os.path.join(self.base_dir, 'data', 'quests_config.json')
        self.player_quests_path = os.path.join(self.base_dir, 'gamedata', 'player_quests.json')
        self.players_path = os.path.join(self.base_dir, 'gamedata', 'players.json')
        self.savegame_path = os.path.join(self.base_dir, 'gamedata', 'savegame.json')
        
        self.quests_config = self._load_quests_config()
    
    def _load_quests_config(self) -> Dict:
        """Charge la configuration des quêtes depuis quests_config.json"""
        try:
            with open(self.quests_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur chargement quests_config.json: {e}")
            return {}
    
    def load_all_player_quests(self) -> Dict:
        """Charge tout le fichier player_quests.json"""
        try:
            with open(self.player_quests_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            print(f"Erreur chargement player_quests.json: {e}")
            return {}
    
    def load_player_quests(self, username: str) -> Dict:
        """Charge les quêtes d'un joueur depuis player_quests.json"""
        try:
            with open(self.player_quests_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ignorer les clés avec underscore (commentaires)
                if username in data and not username.startswith('_'):
                    return data[username]
                else:
                    # Initialiser si le joueur n'existe pas
                    return self._initialize_player_quests(username)
        except FileNotFoundError:
            return self._initialize_player_quests(username)
        except Exception as e:
            print(f"Erreur chargement player_quests pour {username}: {e}")
            return self._initialize_player_quests(username)
    
    def save_player_quests(self, username: str, quest_data: Dict) -> None:
        """Sauvegarde les quêtes d'un joueur dans player_quests.json"""
        try:
            # Charger toutes les données existantes
            try:
                with open(self.player_quests_path, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)
            except FileNotFoundError:
                all_data = {}
            
            # Mettre à jour les données du joueur
            all_data[username] = quest_data
            
            # Sauvegarder avec format compact intelligent
            with open(self.player_quests_path, 'w', encoding='utf-8') as f:
                self._write_compact_json(all_data, f)
        except Exception as e:
            print(f"Erreur sauvegarde player_quests pour {username}: {e}")
    
    def save_all_player_quests(self, all_data: Dict) -> None:
        """Sauvegarde tout le fichier player_quests.json avec format compact"""
        try:
            with open(self.player_quests_path, 'w', encoding='utf-8') as f:
                self._write_compact_json(all_data, f)
        except Exception as e:
            print(f"Erreur sauvegarde player_quests.json: {e}")
    
    def _get_player_data(self, username: str) -> Optional[Dict]:
        """Récupère les données d'un joueur depuis players.json"""
        try:
            with open(self.players_path, 'r', encoding='utf-8') as f:
                players_data = json.load(f)
            # Le fichier a la structure {"players": [...]}
            players = players_data.get('players', [])
            for player in players:
                if player.get('username') == username:
                    return player
            return None
        except Exception as e:
            print(f"Erreur lecture players.json pour {username}: {e}")
            return None
    
    def _write_compact_json(self, data: Dict, file_obj):
        """Écrit le JSON de façon compactée intelligente (objets simples sur une ligne)"""
        def compact_dump(obj, indent=0, parent_key=None):
            lines = []
            indent_str = "  " * indent
            
            if isinstance(obj, dict):
                if not obj:
                    return "{}"
                
                # Déterminer si c'est un objet simple (quête, récompense)
                is_simple = all(not isinstance(v, (dict, list)) or (isinstance(v, list) and len(v) < 10 and all(not isinstance(x, (dict, list)) for x in v)) for v in obj.values())
                
                if is_simple and len(str(obj)) < 200:
                    # Écrire sur une ligne
                    return json.dumps(obj, ensure_ascii=False)
                else:
                    # Écrire sur plusieurs lignes
                    lines.append("{")
                    items = list(obj.items())
                    for i, (key, value) in enumerate(items):
                        comma = "," if i < len(items) - 1 else ""
                        value_str = compact_dump(value, indent + 1, parent_key=key)
                        if "\n" in value_str:
                            lines.append(f'{indent_str}  "{key}": {value_str}{comma}')
                        else:
                            lines.append(f'{indent_str}  "{key}": {value_str}{comma}')
                    lines.append(f"{indent_str}}}")
                    return "\n".join(lines)
            
            elif isinstance(obj, list):
                if not obj:
                    return "[]"
                
                # Cas spécial : unclaimed_rewards - chaque récompense sur une ligne (AVANT les autres vérifications)
                if parent_key == 'unclaimed_rewards':
                    lines.append("[")
                    for i, item in enumerate(obj):
                        comma = "," if i < len(obj) - 1 else ""
                        # Forcer l'affichage sur une seule ligne pour chaque récompense (sans espaces)
                        item_str = json.dumps(item, ensure_ascii=False, separators=(',', ':'))
                        lines.append(f"{indent_str}  {item_str}{comma}")
                    lines.append(f"{indent_str}]")
                    return "\n".join(lines)
                
                # Si tous les éléments sont simples, écrire sur une ligne
                is_simple_list = all(not isinstance(item, (dict, list)) for item in obj)
                if is_simple_list:
                    return json.dumps(obj, ensure_ascii=False)
                
                # Si liste d'objets simples (quêtes, récompenses)
                all_simple_objs = all(isinstance(item, dict) and len(str(item)) < 200 for item in obj)
                if all_simple_objs:
                    lines.append("[")
                    for i, item in enumerate(obj):
                        comma = "," if i < len(obj) - 1 else ""
                        lines.append(f"{indent_str}  {compact_dump(item, indent + 1, parent_key=parent_key)}{comma}")
                    lines.append(f"{indent_str}]")
                    return "\n".join(lines)
                else:
                    return json.dumps(obj, indent=2, ensure_ascii=False)
            
            else:
                return json.dumps(obj, ensure_ascii=False)
        
        file_obj.write(compact_dump(data).rstrip())
        file_obj.write("\n")
    
    def _initialize_player_quests(self, username: str) -> Dict:
        """Initialise la structure de quêtes pour un nouveau joueur"""
        return {
            "daily_quests": {
                "generated_date": None,
                "player_level_snapshot": 1,
                "initial_snapshot": {},  # Snapshot des valeurs au début de la journée
                "quests": []
            },
            "main_quests": {
                "week_start": None,
                "quests": []
            },
            "unclaimed_rewards": []
        }
    
    def calculate_player_level(self, username: str) -> int:
        """
        Calcule le niveau du joueur basé sur les points de quêtes accumulés.
        
        Paliers de niveaux :
        Niveau 1 : 0-9 points (seuil 10)
        Niveau 2 : 10-19 points (seuil 20 = 10+10)
        Niveau 3 : 20-49 points (seuil 50 = 20+30)
        Niveau 4 : 50-89 points (seuil 90 = 50+40)
        Niveau 5 : 90-139 points (seuil 140 = 90+50)
        Niveau 6 : 140-199 points (seuil 200 = 140+60)
        Niveau 7 : 200-269 points (seuil 270 = 200+70)
        Niveau 8 : 270-349 points (seuil 350 = 270+80)
        Niveau 9 : 350-439 points (seuil 440 = 350+90)
        Niveau 10 : 440-539 points (seuil 540 = 440+100)
        Niveau 11 : 540-650 points (seuil 651 = 540+110)
        Niveau 12 : 651-771 points (seuil 772 = 651+120)
        Niveau 13 : 772-902 points (seuil 903 = 772+130)
        Niveau 14 : 903-1043 points (seuil 1044 = 903+140)
        Niveau 15 : 1044-1194 points (seuil 1195 = 1044+150)
        Niveau 16 : 1195-1355 points (seuil 1356 = 1195+160)
        Niveau 17 : 1356-1526 points (seuil 1527 = 1356+170)
        Niveau 18 : 1527-1707 points (seuil 1708 = 1527+180)
        Niveau 19 : 1708-1898 points (seuil 1899 = 1708+190)
        Niveau 20 : 1899+ points
        """
        try:
            # Charger les données du joueur depuis players.json
            with open(self.players_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Trouver le joueur dans la liste
            players_list = data.get('players', [])
            player = next((p for p in players_list if p.get('username') == username), None)
            
            if not player:
                return 1
            
            quest_points = player.get('quest_points', 0)
            
            # Calculer le niveau basé sur les points de quêtes
            # Paliers : 10, 20, 50, 90, 140, 200, 270, 350, 440, 540, 651, 772, 903, 1044, 1195, 1356, 1527, 1708, 1899
            thresholds = [10, 20, 50, 90, 140, 200, 270, 350, 440, 540, 651, 772, 903, 1044, 1195, 1356, 1527, 1708, 1899]
            
            level = 1
            for threshold in thresholds:
                if quest_points >= threshold:
                    level += 1
                else:
                    break
            
            return min(level, 20)  # Maximum niveau 20
        
        except Exception as e:
            print(f"Erreur calcul niveau pour {username}: {e}")
            return 1
    
    def get_quest_targets_and_rewards(self, quest_id: str, player_level: int) -> tuple:
        """
        Retourne les targets et rewards pour une quête selon le niveau du joueur
        Utilise les 3 paliers: 1-5 (facile), 6-15 (moyen), 16+ (difficile)
        """
        quest_progression = self.quests_config.get('quest_progression', {}).get(quest_id, [])
        
        if not quest_progression:
            return ([0, 0, 0], [{}, {}, {}])
        
        # Déterminer le palier
        # Chercher la configuration exacte pour le niveau du joueur
        level_data = None
        for config in quest_progression:
            if config.get('level') == player_level:
                level_data = config
                break
        
        # Si pas de config pour ce niveau exact, prendre la première disponible en fallback
        if not level_data and len(quest_progression) > 0:
            level_data = quest_progression[0]
        
        if not level_data:
            return ([0, 0, 0], [{}, {}, {}])
        
        targets = level_data.get('targets', [0, 0, 0])
        rewards = level_data.get('rewards', [{}, {}, {}])
        
        return (targets, rewards)
    
    def generate_main_quests(self, username: str) -> List[Dict]:
        """
        Génère 3 quêtes principales basées sur la progression chronologique
        Exclut les quêtes complétées
        """
        # Charger les données du joueur
        all_player_data = self.load_all_player_quests()
        username_data = all_player_data.get(username, {})
        
        # Récupérer la liste des quêtes terminées (ancien nom: quest_week_done)
        completed_quest_ids = username_data.get('completed_main_quests', 
                                                username_data.get('quest_week_done', []))
        
        # Récupérer la config de progression
        main_quests_config = self.quests_config.get('main_quests', {})
        main_progression = main_quests_config.get('quests', [])
        if not main_progression:
            return []
        
        # Trier par ordre chronologique
        main_progression_sorted = sorted(main_progression, key=lambda q: q.get('order', 999))
        
        # Sélectionner les 3 premières quêtes non terminées
        selected_quests = []
        for quest_def in main_progression_sorted:
            quest_id = quest_def.get('id')
            
            if quest_id not in completed_quest_ids:
                quest = {
                    "id": quest_id,
                    "progress": 0,
                    "is_completed": False,
                    "rewards_claimed": False
                }
                selected_quests.append(quest)
                
                if len(selected_quests) >= 3:
                    break
        
        return selected_quests
    
    def calculate_main_quest_progress(self, username: str, quest_id: str, quest_type: str, quest_config: Dict) -> int:
        """
        Calcule la progression actuelle d'une quête principale en lisant savegame.json
        
        Types supportés:
        - own_cities: Nombre de villes possédées
        - reach_population: Population maximale dans une ville
        - building_level: Niveau d'un bâtiment spécifique
        - satisfaction: Satisfaction maximale dans une ville
        """
        try:
            # Charger players.json pour créer le mapping dynamique username -> player_id
            with open(self.players_path, 'r', encoding='utf-8') as f:
                players_data = json.load(f)
            
            # Créer le mapping username -> player_id dynamiquement
            player_id_map = {}
            for player in players_data.get('players', []):
                username_key = player.get('username')
                player_id_value = player.get('id')
                if username_key and player_id_value:
                    player_id_map[username_key] = player_id_value
            
            player_id = player_id_map.get(username)
            if not player_id:
                print(f"Joueur {username} non trouvé dans le mapping: {player_id_map}")
                return 0
            
            # Charger savegame.json
            with open(self.savegame_path, 'r', encoding='utf-8') as f:
                savegame = json.load(f)
            
            cities = savegame.get('cities', [])
            player_cities = [c for c in cities if c.get('owner') == player_id]
            
            # Calculer selon le type
            if quest_type == 'own_cities':
                # Nombre de villes possédées
                return len(player_cities)
            
            elif quest_type == 'reach_population':
                # Population maximale dans une ville
                max_pop = 0
                for city in player_cities:
                    pop = city.get('resources', {}).get('population_total', 0)
                    max_pop = max(max_pop, pop)
                return max_pop
            
            elif quest_type == 'building_level':
                # Niveau maximum d'un bâtiment spécifique (uniquement si construction terminée)
                building_name = quest_config.get('building', '')
                max_level = 0
                
                for city in player_cities:
                    buildings = city.get('buildings', [])
                    for building in buildings:
                        if building.get('name', '').lower() == building_name.lower():
                            status = building.get('status', '')
                            # Compter uniquement les bâtiments terminés
                            if status == 'Terminé':
                                level = building.get('level', 0)
                                max_level = max(max_level, level)
                
                return max_level
            
            elif quest_type == 'satisfaction':
                # Satisfaction maximale dans une ville
                max_satisfaction = 0
                for city in player_cities:
                    # La satisfaction est maintenant dans satisfaction_details.total
                    satisfaction_details = city.get('satisfaction_details', {})
                    satisfaction = satisfaction_details.get('total', 0)
                    max_satisfaction = max(max_satisfaction, satisfaction)
                return max_satisfaction
            
            elif quest_type == 'unlock_specific_research':
                # Vérifier si une recherche spécifique est débloquée
                research_id = quest_config.get('research_id', '')
                player_data = self._get_player_data(username)
                if player_data:
                    unlocked_research = player_data.get('unlocked_research', [])
                    return 1 if research_id in unlocked_research else 0
                return 0
            
            return 0
            
        except Exception as e:
            print(f"Erreur calcul progression {quest_id} pour {username}: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def increment_main_quest_progress(self, username: str, quest_id: str, increment: int = 1) -> bool:
        """
        Incrémente manuellement la progression d'une quête principale
        Utilisé pour les quêtes basées sur des événements (ex: attaques de camps de sauvages)
        
        Args:
            username: Nom du joueur
            quest_id: ID de la quête (ex: 'mil_attack_barbarians')
            increment: Valeur à ajouter (par défaut 1)
        
        Returns:
            True si la mise à jour a réussi, False sinon
        """
        try:
            # Charger les données du joueur
            all_player_data = self.load_all_player_quests()
            username_data = all_player_data.get(username)
            
            if not username_data:
                print(f"Aucune donnée de quête pour {username}")
                return False
            
            main_quests_data = username_data.get('main_quests_data', {})
            main_quests = main_quests_data.get('quests', [])
            
            # Trouver la quête
            quest_found = False
            for quest in main_quests:
                if quest.get('id') == quest_id:
                    # Incrémenter la progression
                    old_progress = quest.get('progress', 0)
                    quest['progress'] = old_progress + increment
                    
                    # Récupérer la config de la quête pour vérifier si complétée
                    main_quests_config = self.quests_config.get('main_quests', {})
                    main_progression = main_quests_config.get('quests', [])
                    quest_def = None
                    for q in main_progression:
                        if q.get('id') == quest_id:
                            quest_def = q
                            break
                    
                    if quest_def:
                        target = quest_def.get('target', 100)
                        # Marquer comme complétée si le target est atteint
                        if quest['progress'] >= target and not quest.get('is_completed'):
                            quest['is_completed'] = True
                            quest['rewards_claimed'] = False
                            print(f"🎉 Quête principale '{quest_id}' complétée pour {username}!")
                        else:
                            print(f"📊 Progression de '{quest_id}' pour {username}: {quest['progress']}/{target}")
                    
                    quest_found = True
                    break
            
            if not quest_found:
                print(f"Quête '{quest_id}' non trouvée dans les quêtes principales de {username}")
                return False
            
            # Sauvegarder les données mises à jour
            all_player_data[username] = username_data
            self.save_all_player_quests(all_player_data)
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'incrémentation de la quête '{quest_id}' pour {username}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_and_complete_main_quests(self, username: str) -> List[str]:
        """
        Vérifie les quêtes principales et met à jour leur statut (is_completed + rewards_claimed)
        Retourne la liste des IDs de quêtes nouvellement complétées
        """
        try:
            all_player_data = self.load_all_player_quests()
            username_data = all_player_data.get(username, {})
            main_quests_data = username_data.get('main_quests', {})
            quests = main_quests_data.get('quests', [])
            
            if not quests:
                return []
            
            newly_completed = []
            has_changes = False
            
            for quest in quests:
                quest_id = quest.get('id')
                
                # Si déjà marquée comme complétée et réclamée, skip
                if quest.get('is_completed') and quest.get('rewards_claimed'):
                    continue
                
                # Obtenir la config de la quête
                main_quests_config = self.quests_config.get('main_quests', {})
                main_progression = main_quests_config.get('quests', [])
                quest_def = None
                for q in main_progression:
                    if q.get('id') == quest_id:
                        quest_def = q
                        break
                
                if not quest_def:
                    continue
                
                # Calculer la progression réelle
                quest_type = quest_def.get('type', '')
                target = quest_def.get('target', 100)
                current_progress = self.calculate_main_quest_progress(username, quest_id, quest_type, quest_def)
                
                # Mettre à jour la progression (toujours, même si pas complétée)
                old_progress = quest.get('progress', 0)
                quest['progress'] = current_progress
                
                # Marquer comme modifié si la progression a changé
                if old_progress != current_progress:
                    has_changes = True
                
                # Si la quête est complétée et pas encore marquée
                if current_progress >= target and not quest.get('is_completed'):
                    quest['is_completed'] = True
                    quest['rewards_claimed'] = False  # Initialement non réclamée
                    newly_completed.append(quest_id)
                    has_changes = True
                    
                    # 🔒 SÉCURITÉ : Ajouter immédiatement à completed_main_quests
                    # pour éviter que la quête soit reproposée avant la réclamation de la récompense
                    completed_main_quests = username_data.get('completed_main_quests', [])
                    if quest_id not in completed_main_quests:
                        completed_main_quests.append(quest_id)
                        username_data['completed_main_quests'] = completed_main_quests
                        print(f"✅ Quête {quest_id} ajoutée à completed_main_quests pour {username}")
            
            # Sauvegarder si des changements
            if has_changes:
                all_player_data[username] = username_data
                self.save_all_player_quests(all_player_data)
            
            return newly_completed
            
        except Exception as e:
            print(f"Erreur check_and_complete_main_quests pour {username}: {e}")
            return []
    
    def generate_daily_quests(self, username: str) -> List[Dict]:
        """
        Génère 5 quêtes quotidiennes aléatoires pour un joueur
        Sélectionne parmi les quêtes disponibles dans quests_config.json
        Ne propose que les quêtes qui ont une configuration pour le niveau du joueur
        """
        player_level = self.calculate_player_level(username)
        
        # Récupérer les pools de quêtes
        daily_pool = self.quests_config.get('daily_quests_pool', {})
        quest_progression = self.quests_config.get('quest_progression', {})
        
        # Filtrer les quêtes disponibles selon le niveau du joueur
        def is_quest_available(quest_def: Dict) -> bool:
            """Vérifie si une quête a une configuration pour le niveau du joueur ou inférieur"""
            quest_id = quest_def.get('id')
            quest_configs = quest_progression.get(quest_id, [])
            
            # Chercher la config pour le niveau le plus proche <= player_level
            available_levels = [c.get('level', 1) for c in quest_configs]
            if not available_levels:
                return False
            
            # Si le niveau du joueur >= max niveau disponible, la quête est disponible
            max_level = max(available_levels)
            return player_level >= min(available_levels) and max_level > 0
            
            return False
        
        # Filtrer les pools de quêtes
        economic = [q for q in daily_pool.get('economic', []) if is_quest_available(q)]
        military = [q for q in daily_pool.get('military', []) if is_quest_available(q)]
        research = [q for q in daily_pool.get('research', []) if is_quest_available(q)]
        
        # Sélection aléatoire: 3 économiques, 1 militaire, 1 recherche
        selected_quests = []
        
        if len(economic) >= 3:
            selected_quests.extend(random.sample(economic, 3))
        else:
            selected_quests.extend(economic)
        
        if len(military) >= 1:
            selected_quests.extend(random.sample(military, 1))
        else:
            selected_quests.extend(military)
        
        if len(research) >= 1:
            selected_quests.extend(random.sample(research, 1))
        else:
            selected_quests.extend(research)
        
        # Construire la structure simplifiée des quêtes (sans targets et rewards)
        daily_quests = []
        for quest_def in selected_quests:
            quest = {
                "id": quest_def['id'],
                "progress": 0,
                "stars_earned": [],
                "rewards_claimed": []
            }
            daily_quests.append(quest)
        
        return daily_quests
    
    def regenerate_daily_quests(self, username: str) -> bool:
        """
        Régénère les quêtes quotidiennes pour un joueur
        Utilisé par le scheduler pour la régénération automatique
        
        Returns:
            bool: True si la régénération a réussi
        """
        try:
            # Charger toutes les quêtes des joueurs
            all_player_data = self.load_all_player_quests()
            
            # Obtenir ou créer l'entrée du joueur
            username_data = all_player_data.get(username, {})
            
            # Générer de nouvelles quêtes quotidiennes
            new_daily_quests = self.generate_daily_quests(username)
            
            # 📸 Créer un snapshot pour mesurer les deltas quotidiens
            initial_snapshot = self._create_daily_snapshot(username)
            
            # Mettre à jour la structure
            username_data['daily_quests'] = {
                'generated_date': datetime.now().strftime('%Y-%m-%d'),
                'initial_snapshot': initial_snapshot,  # ← Nouveau snapshot
                'quests': new_daily_quests
            }
            
            # Sauvegarder
            all_player_data[username] = username_data
            self.save_all_player_quests(all_player_data)
            
            print(f"✅ Quêtes quotidiennes régénérées pour {username}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur régénération quêtes pour {username}: {e}")
            return False
    
    def _get_player_stat(self, username: str, stat_name: str) -> int:
        """Récupère une statistique du joueur depuis players.json"""
        try:
            with open(self.players_path, 'r', encoding='utf-8') as f:
                players_data = json.load(f)
            
            for player in players_data.get('players', []):
                if player.get('username') == username:
                    return player.get(stat_name, 0)
            return 0
        except Exception as e:
            print(f"Erreur lecture stat {stat_name} pour {username}: {e}")
            return 0
    
    def _create_daily_snapshot(self, username: str) -> Dict:
        """
        Crée un snapshot des statistiques du joueur pour calculer les deltas quotidiens
        Retourne: {population_max, research_points, victories, units_killed}
        """
        try:
            snapshot = {}
            
            # Charger players.json
            with open(self.players_path, 'r', encoding='utf-8') as f:
                players_data = json.load(f)
            
            players_list = players_data.get('players', [])
            player = next((p for p in players_list if p.get('username') == username), None)
            
            if player:
                # Stats depuis players.json
                snapshot['research_points'] = player.get('research_points', 0)
                snapshot['victories'] = player.get('victories', 0)
                snapshot['units_killed'] = player.get('total_units_killed', 0)
                
                # Population max depuis savegame.json
                player_id = player.get('id')
                try:
                    with open(self.savegame_path, 'r', encoding='utf-8') as f:
                        savegame = json.load(f)
                    
                    max_pop = 0
                    for city in savegame.get('cities', []):
                        if city.get('owner') == player_id:
                            pop = city.get('resources', {}).get('population_total', 0)
                            max_pop = max(max_pop, pop)
                    
                    snapshot['population_max'] = max_pop
                except Exception as e:
                    print(f"Erreur lecture population pour snapshot: {e}")
                    snapshot['population_max'] = 0
            
            return snapshot
        except Exception as e:
            print(f"Erreur création snapshot pour {username}: {e}")
            return {}
    
    def enrich_quest_data(self, quest_progress: Dict, username: str = None) -> Dict:
        """
        Enrichit les données d'une quête avec les infos depuis quests_config.json
        Supporte deux formats:
        - Format simplifié: {id, current_progress, target, is_completed, is_claimed}
        - Format complet: {id, progress, targets, rewards, stars_earned}
        Retourne: {id, title, description, type, target, current_progress, reward_xp, reward_stars, is_completed, is_claimed}
        """
        quest_id = quest_progress['id']
        
        # Trouver la définition de la quête dans quests_config
        quest_def = None
        for pool_name in ['economic', 'military', 'research']:
            pool = self.quests_config.get('daily_quests_pool', {}).get(pool_name, [])
            for q in pool:
                if q['id'] == quest_id:
                    quest_def = q
                    break
            if quest_def:
                break
        
        # 🛡️ ROBUSTESSE: Si la quête n'est pas trouvée, retourner None
        # Elle sera filtrée côté serveur pour éviter l'affichage "🎯 / "
        if not quest_def:
            print(f"⚠️ Définition de quête non trouvée pour {quest_id} - quête ignorée")
            return None
        
        # Déterminer le format (prioriser 'progress' sur 'current_progress')
        if 'progress' in quest_progress:
            # Format complet (prioritaire)
            current_progress = quest_progress.get('progress', 0)
            
            # 🎯 SYNC AUTO: Pour certaines quêtes basées sur des stats cumulatives,
            # calculer le DELTA depuis le snapshot initial
            if username:
                quest_data = self.load_player_quests(username)
                snapshot = quest_data.get('daily_quests', {}).get('initial_snapshot', {})
                
                if quest_id == 'mil_win_battles':
                    total_victories = self._get_player_stat(username, 'victories')
                    initial_victories = snapshot.get('victories', total_victories)
                    current_progress = max(0, total_victories - initial_victories)  # Delta quotidien
                    quest_progress['progress'] = current_progress
                
                elif quest_id == 'mil_kill_units':
                    total_units_killed = self._get_player_stat(username, 'total_units_killed')
                    initial_units_killed = snapshot.get('units_killed', total_units_killed)
                    current_progress = max(0, total_units_killed - initial_units_killed)  # Delta quotidien
                    quest_progress['progress'] = current_progress
            
            targets = quest_progress.get('targets', [0, 0, 0])
            target = targets[0] if targets else 0
            is_completed = current_progress >= target
            is_claimed = target in quest_progress.get('rewards_claimed', [])
        elif 'current_progress' in quest_progress:
            # Format simplifié
            current_progress = quest_progress['current_progress']
            target = quest_progress['target']
            is_completed = quest_progress['is_completed']
            is_claimed = quest_progress['is_claimed']
        else:
            # Valeurs par défaut
            current_progress = 0
            target = 100
            is_completed = False
            is_claimed = False
        
        # Récupérer les targets et rewards depuis la config selon le niveau du joueur
        quest_progression = self.quests_config.get('quest_progression', {}).get(quest_id, [])
        if quest_progression:
            level_data = quest_progression[0]  # Niveau 1 par défaut
            targets_full = level_data.get('targets', [100, 200, 300])
            rewards_full = level_data.get('rewards', [{}, {}, {}])
        else:
            targets_full = [100, 200, 300]
            rewards_full = [{"gold": 100}, {"gold": 120}, {"gold": 150}]
        
        # Construire la quête enrichie pour le frontend
        enriched = {
            "id": quest_id,
            "title": quest_def.get('title', 'Quête'),
            "description": quest_def.get('description', ''),
            "type": quest_def.get('category', 'economic'),
            "icon": quest_def.get('icon', '🎯'),
            "target": target,  # Target actuel (premier palier)
            "targets": targets_full,  # Tous les paliers [100, 200, 300]
            "rewards": rewards_full,  # Toutes les récompenses [{...}, {...}, {...}]
            "current_progress": current_progress,
            "is_completed": is_completed,
            "is_claimed": is_claimed
        }
        
        return enriched
    
    def enrich_main_quest_data(self, quest_progress: Dict, username: str = None) -> Dict:
        """
        Enrichit les données d'une quête principale depuis quests_config.json
        ET calcule la progression en temps réel depuis savegame.json
        Format entrée: {id, progress, is_completed}
        Format sortie: {id, title, description, icon, type, target, current_progress, rewards, is_completed}
        """
        quest_id = quest_progress['id']
        
        # Trouver la définition dans main_quests.quests
        main_quests_config = self.quests_config.get('main_quests', {})
        main_progression = main_quests_config.get('quests', [])
        quest_def = None
        for q in main_progression:
            if q.get('id') == quest_id:
                quest_def = q
                break
        
        if not quest_def:
            return None
        
        # Calculer la progression en temps réel depuis savegame.json
        quest_type = quest_def.get('type', 'weekly')
        real_progress = 0
        if username:
            real_progress = self.calculate_main_quest_progress(username, quest_id, quest_type, quest_def)
        
        # Construire la quête enrichie
        enriched = {
            "id": quest_id,
            "title": quest_def.get('title', 'Quête principale'),
            "description": quest_def.get('description', ''),
            "type": quest_type,
            "icon": quest_def.get('icon', '⭐'),
            "target": quest_def.get('target', 100),
            "current_progress": real_progress,
            "rewards": quest_def.get('rewards', {}),
            "is_completed": quest_progress.get('is_completed', False),
            "order": quest_def.get('order', 0),
            "help_text": quest_def.get('help_text')  # Texte d'aide pour guider le joueur
        }
        
        return enriched
    
    def get_or_generate_daily_quests(self, username: str) -> List[Dict]:
        """
        Récupère les quêtes quotidiennes actuelles ou en génère de nouvelles si nécessaire
        Retourne les quêtes enrichies avec les infos de quests_config.json
        """
        quest_data = self.load_player_quests(username)
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Vérifier si les quêtes sont à jour ET non vides
        if (quest_data['daily_quests']['generated_date'] == today and 
            len(quest_data['daily_quests']['quests']) > 0):
            # Enrichir chaque quête avec les données de config
            enriched_quests = []
            has_changes = False
            for quest_progress in quest_data['daily_quests']['quests']:
                old_progress = quest_progress.get('progress', 0)
                enriched = self.enrich_quest_data(quest_progress, username=username)  # ← Passer username
                # ✅ Filtrer les None (quêtes non trouvées dans la config)
                if enriched is not None:
                    enriched_quests.append(enriched)
                    # Vérifier si la progression a changé (sync auto)
                    if quest_progress.get('progress', 0) != old_progress:
                        has_changes = True
            
            # Sauvegarder si des changements ont été faits par la sync auto
            if has_changes:
                self.save_player_quests(username, quest_data)
            
            return enriched_quests
        
        # Générer de nouvelles quêtes
        player_level = self.calculate_player_level(username)
        new_quests = self.generate_daily_quests(username)
        
        # 📸 Créer un snapshot des statistiques actuelles pour mesurer les deltas
        initial_snapshot = self._create_daily_snapshot(username)
        
        quest_data['daily_quests'] = {
            "generated_date": today,
            "player_level_snapshot": player_level,
            "initial_snapshot": initial_snapshot,  # ← Nouveau snapshot
            "quests": new_quests
        }
        
        self.save_player_quests(username, quest_data)
        
        # Enrichir les quêtes nouvellement générées avant de les retourner
        enriched_quests = []
        for quest in new_quests:
            enriched = self.enrich_quest_data(quest, username=username)
            if enriched is not None:
                enriched_quests.append(enriched)
        
        return enriched_quests
    
    def update_quest_progress(self, username: str, quest_id: str, increment: int = 0, set_value: int = None) -> Dict:
        """
        Met à jour la progression d'une quête pour un joueur
        increment: ajouter à la progression actuelle
        set_value: définir une valeur absolue
        
        Retourne: {"success": bool, "stars_earned": list, "message": str}
        """
        try:
            quest_data = self.load_player_quests(username)
            daily_quests = quest_data['daily_quests']['quests']
            
            # Trouver la quête
            quest = None
            quest_index = None
            for i, q in enumerate(daily_quests):
                if q['id'] == quest_id:
                    quest = q
                    quest_index = i
                    break
            
            if not quest:
                return {"success": False, "stars_earned": [], "message": "Quête non trouvée"}
            
            # Déterminer le format et mettre à jour la progression
            # Initialiser les champs s'ils n'existent pas
            if 'progress' not in quest:
                quest['progress'] = 0
            if 'stars_earned' not in quest:
                quest['stars_earned'] = []
            if 'rewards_claimed' not in quest:
                quest['rewards_claimed'] = []
            
            # Mettre à jour la progression
            if set_value is not None:
                quest['progress'] = set_value
            else:
                quest['progress'] += increment
            
            # Vérifier et attribuer les étoiles
            new_stars = self.check_and_award_stars(username, quest, quest_data)
            
            # Sauvegarder
            daily_quests[quest_index] = quest
            quest_data['daily_quests']['quests'] = daily_quests
            self.save_player_quests(username, quest_data)
            
            # Récupérer le target max pour le message
            quest_progression = self.quests_config.get('quest_progression', {}).get(quest_id, [])
            max_target = 300  # Défaut
            if quest_progression:
                targets = quest_progression[0].get('targets', [100, 200, 300])
                max_target = targets[-1]
            
            return {
                "success": True,
                "quest_id": quest_id,
                "stars_earned": new_stars,
                "new_progress": quest['progress'],
                "progress": quest['progress'],
                "message": f"Progression mise à jour: {quest['progress']}/{max_target}"
            }
        
        except Exception as e:
            print(f"Erreur update_quest_progress pour {username}/{quest_id}: {e}")
            return {"success": False, "stars_earned": [], "message": str(e)}
    
    def check_and_award_stars(self, username: str, quest: Dict, quest_data: Dict) -> List[int]:
        """
        Vérifie si des étoiles doivent être attribuées et ajoute les récompenses aux unclaimed
        Retourne la liste des nouvelles étoiles obtenues
        """
        new_stars = []
        progress = quest['progress']
        quest_id = quest['id']
        stars_earned = quest.get('stars_earned', [])
        
        # Récupérer targets et rewards depuis quests_config
        quest_progression = self.quests_config.get('quest_progression', {}).get(quest_id, [])
        if not quest_progression:
            return new_stars
        
        level_data = quest_progression[0]  # Niveau 1 par défaut
        targets = level_data.get('targets', [100, 200, 300])
        rewards = level_data.get('rewards', [{}, {}, {}])
        
        for i, target in enumerate(targets):
            star_level = i + 1
            if progress >= target and star_level not in stars_earned:
                # Nouvelle étoile obtenue !
                stars_earned.append(star_level)
                new_stars.append(star_level)
                
                # Ajouter la récompense aux unclaimed
                reward = rewards[i]
                
                # Récupérer le title depuis la config si absent
                quest_title = quest.get('title', '')
                if not quest_title:
                    # Chercher dans quests_config
                    quest_id = quest['id']
                    for pool_name in ['economic', 'military', 'research']:
                        pool = self.quests_config.get('daily_quests_pool', {}).get(pool_name, [])
                        for q in pool:
                            if q['id'] == quest_id:
                                quest_title = q.get('title', quest_id)
                                break
                        if quest_title:
                            break
                
                unclaimed = {
                    "quest_id": quest['id'],
                    "quest_title": quest_title,
                    "star_level": star_level,
                    "rewards": reward,
                    "awarded_at": datetime.now().isoformat(),
                    "expires_at": (datetime.now() + timedelta(days=3)).isoformat()
                }
                
                # S'assurer que unclaimed_rewards existe
                if 'unclaimed_rewards' not in quest_data:
                    quest_data['unclaimed_rewards'] = []
                    
                quest_data['unclaimed_rewards'].append(unclaimed)
        
        quest['stars_earned'] = stars_earned
        return new_stars
    
    def claim_rewards(self, username: str, quest_id: str, star_level: int) -> Dict:
        """
        Réclame une récompense d'étoile et l'applique au joueur
        Retourne: {"success": bool, "rewards": dict, "message": str}
        """
        try:
            quest_data = self.load_player_quests(username)
            
            # Trouver la récompense non réclamée
            unclaimed = quest_data['unclaimed_rewards']
            reward_to_claim = None
            reward_index = None
            
            for i, reward in enumerate(unclaimed):
                if reward['quest_id'] == quest_id and reward['star_level'] == star_level:
                    reward_to_claim = reward
                    reward_index = i
                    break
            
            if not reward_to_claim:
                return {"success": False, "rewards": {}, "message": "Récompense introuvable"}
            
            # Vérifier expiration
            expires_at = datetime.fromisoformat(reward_to_claim['expires_at'])
            if datetime.now() > expires_at:
                # Supprimer la récompense expirée
                unclaimed.pop(reward_index)
                quest_data['unclaimed_rewards'] = unclaimed
                self.save_player_quests(username, quest_data)
                return {"success": False, "rewards": {}, "message": "Récompense expirée"}
            
            # Appliquer les récompenses au joueur
            rewards = reward_to_claim['rewards']
            self._apply_rewards_to_player(username, rewards, quest_data)
            
            # Marquer comme réclamée dans la quête (daily ou main)
            quest_found = False
            
            # Chercher dans les quêtes quotidiennes
            for quest in quest_data['daily_quests']['quests']:
                if quest['id'] == quest_id:
                    if 'rewards_claimed' not in quest:
                        quest['rewards_claimed'] = []
                    quest['rewards_claimed'].append(star_level)
                    quest_found = True
                    break
            
            # Chercher dans les quêtes principales si pas trouvée
            if not quest_found:
                main_quests = quest_data.get('main_quests', {}).get('quests', [])
                for quest in main_quests:
                    if quest['id'] == quest_id:
                        quest['rewards_claimed'] = True
                        quest_found = True
                        
                        # 🔒 VÉRIFICATION : S'assurer que la quête est bien dans completed_main_quests
                        # (normalement déjà ajoutée lors de check_and_complete_main_quests)
                        if 'completed_main_quests' not in quest_data:
                            quest_data['completed_main_quests'] = []
                        if quest_id not in quest_data['completed_main_quests']:
                            print(f"⚠️ Quête {quest_id} pas dans completed_main_quests lors du claim, ajout de sécurité")
                            quest_data['completed_main_quests'].append(quest_id)
                        break
            
            # Supprimer de unclaimed
            unclaimed.pop(reward_index)
            quest_data['unclaimed_rewards'] = unclaimed
            
            # Sauvegarder
            self.save_player_quests(username, quest_data)
            
            return {
                "success": True,
                "rewards": rewards,
                "message": f"Récompenses réclamées avec succès !"
            }
        
        except Exception as e:
            print(f"Erreur claim_rewards pour {username}/{quest_id}/{star_level}: {e}")
            return {"success": False, "rewards": {}, "message": str(e)}
    
    def _apply_rewards_to_player(self, username: str, rewards: Dict, quest_data: Dict) -> None:
        """Applique les récompenses au joueur dans players.json"""
        try:
            with open(self.players_path, 'r', encoding='utf-8') as f:
                players_data = json.load(f)
            
            # players.json a la structure {"players": [...]}
            players_list = players_data.get('players', [])
            player = None
            player_index = None
            
            for i, p in enumerate(players_list):
                if p.get('username') == username:
                    player = p
                    player_index = i
                    break
            
            if not player:
                return
            
            # Appliquer chaque récompense
            if 'gold' in rewards:
                player['gold'] = player.get('gold', 0) + rewards['gold']
            
            if 'research_points' in rewards:
                player['research_points'] = player.get('research_points', 0) + rewards['research_points']
            
            if 'diamonds' in rewards:
                player['diamonds'] = player.get('diamonds', 0) + rewards['diamonds']
            
            if 'wood' in rewards:
                player['wood'] = player.get('wood', 0) + rewards['wood']
            
            if 'stone' in rewards:
                player['stone'] = player.get('stone', 0) + rewards['stone']
            
            if 'marble' in rewards:
                player['marble'] = player.get('marble', 0) + rewards['marble']
            
            if 'population' in rewards:
                # Augmenter la population max (à adapter selon le système existant)
                pass
            
            if 'quest_points' in rewards:
                # Incrémenter les quest_points dans le player uniquement
                if 'quest_points' not in player:
                    player['quest_points'] = 0
                player['quest_points'] = player.get('quest_points', 0) + rewards['quest_points']
            
            # Mettre à jour la liste
            players_list[player_index] = player
            players_data['players'] = players_list
            
            # Sauvegarder
            with open(self.players_path, 'w', encoding='utf-8') as f:
                json.dump(players_data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            print(f"Erreur application récompenses pour {username}: {e}")
    
    def update_resource_collection_quests(self, username: str, resources_collected: Dict[str, float]) -> None:
        """
        Met à jour les quêtes de collecte de ressources pour un joueur
        Appelé après chaque tick avec les ressources collectées
        
        Args:
            username: Nom du joueur
            resources_collected: Dict {resource: amount} ex: {'wood': 5.2, 'stone': 3.1, 'research_points': 1.2}
        """
        try:
            quest_data = self.load_player_quests(username)
            daily_quests = quest_data['daily_quests']['quests']
            
            # Mapping des quêtes de collecte vers les ressources
            quest_resource_mapping = {
                'eco_collect_wood': 'wood',
                'eco_collect_stone': 'stone',
                'eco_collect_marble': 'marble',
                'eco_collect_glass': 'glass',
                'eco_collect_iron': 'iron',
                'eco_collect_cereal': 'cereal',
                'eco_collect_horse': 'horse',
                'eco_collect_wine': 'wine',
                'eco_collect_coal': 'coal',
                'eco_collect_gunpowder': 'gunpowder',
                'eco_collect_spices': 'spices',
                'eco_collect_cotton': 'cotton',
                'eco_collect_papyrus': 'papyrus',
                'eco_produce_gold': 'gold',
                'sci_reach_research_level': 'research_points'
            }
            
            updated = False
            for quest in daily_quests:
                quest_id = quest['id']
                
                # Vérifier si c'est une quête de collecte de ressource
                if quest_id in quest_resource_mapping:
                    resource = quest_resource_mapping[quest_id]
                    
                    # Si cette ressource a été collectée ce tick
                    if resource in resources_collected and resources_collected[resource] > 0:
                        amount = resources_collected[resource]  # Garder les décimales
                        
                        # Initialiser progress_decimal si nécessaire (pour accumuler les décimales)
                        if 'progress_decimal' not in quest:
                            quest['progress_decimal'] = 0.0
                        if 'progress' not in quest:
                            quest['progress'] = 0
                        
                        # Accumuler avec décimales
                        quest['progress_decimal'] += amount
                        old_progress = quest['progress']
                        
                        # Convertir en entier pour l'affichage
                        quest['progress'] = int(quest['progress_decimal'])
                        
                        # Marquer comme updated (même si le progress entier n'a pas changé)
                        updated = True
                        
                        # Vérifier et attribuer les étoiles si progression entière
                        if quest['progress'] > old_progress:
                            self.check_and_award_stars(username, quest, quest_data)
            
            # Sauvegarder si des quêtes ont été mises à jour
            if updated:
                self.save_player_quests(username, quest_data)
                
        except Exception as e:
            # Silent fail - ne pas interrompre le tick
            pass
    
    def update_construction_quest(self, username: str, building_name: str = None, is_upgrade: bool = False) -> None:
        """
        Met à jour la progression des quêtes de construction
        - eco_build_buildings : toutes les constructions/upgrades terminés
        - sci_upgrade_academy : uniquement les upgrades d'académie
        
        Args:
            username: Le nom d'utilisateur
            building_name: Le nom du bâtiment (ex: "Academy", "Caserne")
            is_upgrade: True si c'est un upgrade, False si c'est une nouvelle construction
        """
        try:
            quest_data = self.load_player_quests(username)
            daily_quests = quest_data['daily_quests']['quests']
            modified = False
            
            # Chercher et mettre à jour les quêtes concernées
            for quest in daily_quests:
                # Quête générale de construction (toutes constructions/upgrades)
                if quest['id'] == 'eco_build_buildings':
                    quest['progress'] = quest.get('progress', 0) + 1
                    self.check_and_award_stars(username, quest, quest_data)
                    modified = True
                
                # Quête spécifique : amélioration d'académie
                if quest['id'] == 'sci_upgrade_academy' and is_upgrade and building_name == 'Academy':
                    quest['progress'] = quest.get('progress', 0) + 1
                    self.check_and_award_stars(username, quest, quest_data)
                    modified = True
            
            # Sauvegarder si des modifications ont été faites
            if modified:
                self.save_player_quests(username, quest_data)
                    
        except Exception as e:
            # Silent fail - ne pas interrompre la construction
            import traceback
            print(f"⚠️ Failed to update construction quest: {e}")
            traceback.print_exc()

    def update_research_invested_quest(self, username: str) -> None:
        """
        Met à jour la progression de la quête sci_reach_research_level
        en calculant le total des points de recherche investis par le joueur
        
        Args:
            username: Le nom d'utilisateur
        """
        try:
            from app.services.player_progression_service import PlayerProgressionService
            from app.data_manager import DataManager
            
            quest_data = self.load_player_quests(username)
            daily_quests = quest_data.get('daily_quests', {}).get('quests', [])
            
            # Chercher la quête sci_reach_research_level
            for quest in daily_quests:
                if quest.get('id') == 'sci_reach_research_level':
                    # Récupérer le player_id depuis players.json
                    with open(self.players_path, 'r', encoding='utf-8') as f:
                        players_data = json.load(f)
                    
                    player_id = None
                    for player in players_data.get('players', []):
                        if player.get('username') == username:
                            player_id = player.get('id')
                            break
                    
                    if not player_id:
                        return
                    
                    # Créer le data_manager avec le base_dir de quest_service
                    data_manager = DataManager(self.base_dir)
                    progression_service = PlayerProgressionService(data_manager)
                    
                    # Calculer le total des points investis
                    total_invested = progression_service.calculate_research_points_invested(player_id)
                    
                    # Mettre à jour la progression
                    old_progress = quest.get('progress', 0)
                    quest['progress'] = total_invested
                    
                    # Vérifier et attribuer les étoiles si nécessaire
                    if quest['progress'] != old_progress:
                        self.check_and_award_stars(username, quest, quest_data)
                        self.save_player_quests(username, quest_data)
                    
                    break
                    
        except Exception as e:
            # Silent fail - ne pas interrompre le déblocage de recherche
            import traceback
            print(f"⚠️ Failed to update research invested quest: {e}")
            traceback.print_exc()


# Instance globale
quest_service = QuestService()
