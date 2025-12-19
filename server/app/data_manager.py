"""
=================================================================
DATA_MANAGER.PY - Gestionnaire centralisé des données
=================================================================

RESPONSABILITÉS:
- Accès centralisé à tous les fichiers JSON du jeu
- Gestion robuste des erreurs de lecture/écriture
            old_data = self.load_savegame()
            if not old_data or not isinstance(old_data, dict):
                return
            
            # Comparer les bâtiments pour chaque ville
            for new_city in new_data.get('cities', []):
                if not new_city or not isinstance(new_city, dict):
                    continue
                    
                city_id = new_city.get('id')
                if not city_id:
                    continue
                
                # Trouver l'ancienne version de cette ville
                old_city = next((c for c in old_data.get('cities', []) if c.get('id') == city_id), None)
                if not old_city or not isinstance(old_city, dict):
                    continues de lecture/écriture
- Cache intelligent pour optimiser les performances
- Sauvegarde atomique avec backup automatique

AVANT D'AJOUTER UNE MÉTHODE:
- Vérifier si le fichier JSON a déjà des méthodes load/save
- Respecter le pattern load_xxx() / save_xxx()
- Gérer le cache approprié (use_cache=False pour savegame)
- Documenter le format de données attendu

FICHIERS GÉRÉS:
- universe.json    → load_universe() (avec cache)
- savegame.json    → load_savegame() / save_savegame() (pas de cache)
- players.json     → load_players() / save_players()
- buildings.json   → load_buildings() (avec cache)

FONCTIONNALITÉS:
- Cache automatique avec expiration (5s par défaut)
- Retry automatique en cas d'erreur temporaire
- Backup automatique avant sauvegarde
- Validation JSON automatique
- Nettoyage des fichiers temporaires

NE PAS MODIFIER sans comprendre les mécanismes de cache et backup !
=================================================================
"""

import os
import json
import time
import random
import threading
import re
from typing import Optional, Dict, Any

def format_savegame_json(data: Dict) -> str:
    """
    Formate le savegame.json avec les sections critiques sur une ligne
    """
    # Générer le JSON avec indentation normale
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    # 1. Compacter production_bonus, building_bonus sur une ligne
    bonus_patterns = [
        r'"production_bonus":\s*\{[^}]*\}',
        r'"building_bonus":\s*\{[^}]*\}'
    ]
    
    for pattern in bonus_patterns:
        matches = re.findall(pattern, json_str, re.DOTALL)
        for match in matches:
            # Compacter sur une ligne
            compact_match = re.sub(r'\s+', ' ', match).strip()
            json_str = json_str.replace(match, compact_match)
    
    # 2. Compacter les 13 ressources de base sur une ligne (approche simple et efficace)
    # Chercher et remplacer le pattern spécifique des 13 ressources consécutives
    resources_pattern = r'(\s*"wood":\s*[0-9.]+,\s*\n\s*"stone":\s*[0-9.]+,\s*\n\s*"iron":\s*[0-9.]+,\s*\n\s*"cereal":\s*[0-9.]+,\s*\n\s*"papyrus":\s*[0-9.]+,\s*\n\s*"horse":\s*[0-9.]+,\s*\n\s*"marble":\s*[0-9.]+,\s*\n\s*"glass":\s*[0-9.]+,\s*\n\s*"meat":\s*[0-9.]+,\s*\n\s*"coal":\s*[0-9.]+,\s*\n\s*"gunpowder":\s*[0-9.]+,\s*\n\s*"spices":\s*[0-9.]+,\s*\n\s*"cotton":\s*[0-9.]+,\s*)'
    resources_matches = re.findall(resources_pattern, json_str, re.DOTALL)
    for resources_match in resources_matches:
        # Compacter sur une ligne avec espacement propre
        compact_resources = re.sub(r',\s*\n\s*', ', ', resources_match.strip())
        # Ajouter l'indentation appropriée et garder la structure
        compact_resources_formatted = '\n        ' + compact_resources
        json_str = json_str.replace(resources_match, compact_resources_formatted)
    
    # 3. satisfaction_factors supprimé - maintenant dans satisfaction_details uniquement
    
    # 4. Compacter satisfaction_details (plus complexe, avec objets imbriqués)
    satisfaction_details_pattern = r'"satisfaction_details":\s*\{[^}]*?"cereal_consumption":\s*\{[^}]*?\}\s*\}'
    matches = re.findall(satisfaction_details_pattern, json_str, re.DOTALL)
    for match in matches:
        # Pour satisfaction_details, on garde une structure semi-compacte
        compact_match = re.sub(r'\n\s+', ' ', match)
        compact_match = re.sub(r'\s+', ' ', compact_match)
        compact_match = re.sub(r'\{\s*"', '{ "', compact_match)
        compact_match = re.sub(r'",\s*"', '", "', compact_match)
        compact_match = re.sub(r'"\s*\}', '" }', compact_match)
        json_str = json_str.replace(match, compact_match)
    
    # 5. Compacter chaque building individuellement sur une ligne
    # Trouver tous les objets building individuels et les compacter
    building_objects = re.findall(r'\{\s*"slot_id":[^}]*\}', json_str, re.DOTALL)
    for building_obj in building_objects:
        # Compacter ce building sur une ligne
        compact_building = re.sub(r'\s+', ' ', building_obj).strip()
        compact_building = re.sub(r'\{\s*"', '{ "', compact_building)
        compact_building = re.sub(r'",\s*"', '", "', compact_building)
        compact_building = re.sub(r'"\s*\}', '" }', compact_building)
        json_str = json_str.replace(building_obj, compact_building)
    
    # 6. Compacter chaque unité militaire sur une ligne (ex: "infantry_light": { "quantity": 4 })
    # Pattern plus spécifique pour les objets contenant "quantity"
    unit_pattern = r'(\{\s*"quantity":\s*\d+\s*\})'
    unit_matches = re.findall(unit_pattern, json_str, re.DOTALL)
    for unit_match in unit_matches:
        # Compacter cette unité sur une ligne
        compact_unit = re.sub(r'\s+', ' ', unit_match).strip()
        compact_unit = re.sub(r'\{\s*"', '{ "', compact_unit)
        compact_unit = re.sub(r'"\s*\}', '" }', compact_unit)
        json_str = json_str.replace(unit_match, compact_unit)
    
    # 7. Compacter production_queue items sur une ligne
    production_queue_pattern = r'\{\s*"unit_type":\s*"[^"]*",\s*"quantity":\s*\d+,\s*"start_time":\s*\d+,\s*"completion_time":\s*\d+,\s*"total_time":\s*\d+\s*\}'
    production_queue_matches = re.findall(production_queue_pattern, json_str, re.DOTALL)
    for pq_match in production_queue_matches:
        compact_pq = re.sub(r'\s+', ' ', pq_match).strip()
        compact_pq = re.sub(r'\{\s*"', '{ "', compact_pq)
        compact_pq = re.sub(r'",\s*"', '", "', compact_pq)
        compact_pq = re.sub(r'":\s*', '": ', compact_pq)
        compact_pq = re.sub(r',\s*"', ', "', compact_pq)
        compact_pq = re.sub(r'\s*\}', ' }', compact_pq)
        json_str = json_str.replace(pq_match, compact_pq)
    
    # 8. Compacter workers_assigned sur une ligne
    workers_pattern = r'"workers_assigned":\s*\{[^}]*?\}'
    workers_matches = re.findall(workers_pattern, json_str, re.DOTALL)
    for workers_match in workers_matches:
        compact_workers = re.sub(r'\s+', ' ', workers_match).strip()
        compact_workers = re.sub(r'\{\s*"', '{ "', compact_workers)
        compact_workers = re.sub(r'",\s*"', '", "', compact_workers)
        compact_workers = re.sub(r'"\s*\}', '" }', compact_workers)
        json_str = json_str.replace(workers_match, compact_workers)
    
    # 8. Compacter population_food_status sur une ligne
    pop_food_status_pattern = r'"population_food_status":\s*\{[^}]*?\}'
    pop_food_status_matches = re.findall(pop_food_status_pattern, json_str, re.DOTALL)
    for pop_food_status_match in pop_food_status_matches:
        compact_pop_food_status = re.sub(r'\s+', ' ', pop_food_status_match).strip()
        compact_pop_food_status = re.sub(r'\{\s*"', '{ "', compact_pop_food_status)
        compact_pop_food_status = re.sub(r'",\s*"', '", "', compact_pop_food_status)
        compact_pop_food_status = re.sub(r'"\s*\}', '" }', compact_pop_food_status)
        json_str = json_str.replace(pop_food_status_match, compact_pop_food_status)
    
    # 9. Compacter cereal_consumption sur une ligne
    cereal_consumption_pattern = r'"cereal_consumption":\s*\{[^}]*?\}'
    cereal_consumption_matches = re.findall(cereal_consumption_pattern, json_str, re.DOTALL)
    for cereal_consumption_match in cereal_consumption_matches:
        compact_cereal_consumption = re.sub(r'\s+', ' ', cereal_consumption_match).strip()
        compact_cereal_consumption = re.sub(r'\{\s*"', '{ "', compact_cereal_consumption)
        compact_cereal_consumption = re.sub(r'",\s*"', '", "', compact_cereal_consumption)
        compact_cereal_consumption = re.sub(r'"\s*\}', '" }', compact_cereal_consumption)
        json_str = json_str.replace(cereal_consumption_match, compact_cereal_consumption)
    
    # 10. Compacter satisfaction_details partiellement (base, bonus, malus, total sur moins de lignes)
    satisfaction_details_compact_pattern = r'"satisfaction_details":\s*\{\s*"base":\s*\d+,\s*"bonus":\s*\{[^}]*\},\s*"malus":\s*\{[^}]*\},\s*"total":\s*\d+,'
    satisfaction_details_matches = re.findall(satisfaction_details_compact_pattern, json_str, re.DOTALL)
    for satisfaction_details_match in satisfaction_details_matches:
        # Compacter les premières lignes de satisfaction_details
        compact_satisfaction_details = re.sub(r'\s+', ' ', satisfaction_details_match).strip()
        compact_satisfaction_details = re.sub(r'\{\s*"', '{ "', compact_satisfaction_details)
        compact_satisfaction_details = re.sub(r'",\s*"', '", "', compact_satisfaction_details)
        compact_satisfaction_details = re.sub(r'"\s*\}', '" }', compact_satisfaction_details)
        json_str = json_str.replace(satisfaction_details_match, compact_satisfaction_details)
    
    # 11. Compacter les champs simples de resources sur une seule ligne
    # Pattern pour les champs de compatibilité frontend (cereal_needed, population_unfed, etc.)
    simple_fields_pattern = r'(\s*"growth_blocked_no_cereal":\s*(?:true|false)),\s*\n(\s*"cereal_needed":\s*[0-9.-]+),\s*\n(\s*"population_unfed":\s*[0-9.-]+),\s*\n(\s*"pop_nourished_by_townhall":\s*[0-9.-]+),\s*\n(\s*"pop_nourished_by_windmill":\s*[0-9.-]+),\s*\n(\s*"total_food_supply":\s*[0-9.-]+)'
    
    def compact_simple_fields_replacement(match):
        # Récupérer l'indentation du premier champ
        indentation = re.match(r'(\s*)', match.group(1)).group(1) if match.group(1) else '        '
        return f'{match.group(1)}, {match.group(2).strip()}, {match.group(3).strip()}, {match.group(4).strip()}, {match.group(5).strip()}, {match.group(6).strip()}'
    
    json_str = re.sub(simple_fields_pattern, compact_simple_fields_replacement, json_str, flags=re.DOTALL)
    
    # 12. Compacter food_capacities sur une ligne
    food_capacities_pattern = r'"food_capacities":\s*\{\s*"townhall":\s*\d+,\s*\n\s*"windmill":\s*\d+,\s*\n\s*"total":\s*\d+\s*\}'
    food_capacities_matches = re.findall(food_capacities_pattern, json_str, re.DOTALL)
    for food_capacities_match in food_capacities_matches:
        compact_food_capacities = re.sub(r'\s+', ' ', food_capacities_match).strip()
        compact_food_capacities = re.sub(r'\{\s*"', '{ "', compact_food_capacities)
        compact_food_capacities = re.sub(r'",\s*"', '", "', compact_food_capacities)
        compact_food_capacities = re.sub(r'"\s*\}', '" }', compact_food_capacities)
        json_str = json_str.replace(food_capacities_match, compact_food_capacities)
    
    # 13. Séparer population_total des ressources et le regrouper avec population_free sur une ligne
    # Pattern pour capturer population_total mélangé avec les ressources
    population_mixed_pattern = r'(cotton": \d+,)"population_total":\s*([0-9.-]+),\s*\n\s*"population_free":\s*([0-9.-]+),'
    population_mixed_matches = re.findall(population_mixed_pattern, json_str)
    for match in population_mixed_matches:
        old_text = f'{match[0]}"population_total": {match[1]},\n        "population_free": {match[2]},'
        new_text = f'{match[0]}\n        "population_total": {match[1]}, "population_free": {match[2]},'
        json_str = json_str.replace(old_text, new_text)
    
    # 14. Compacter les objets heroes individuels sur une ligne
    # Pattern pour capturer chaque hero avec ses propriétés
    hero_pattern = r'("hero_[^"]+"):\s*\{\s*\n\s*"hero_id":\s*"([^"]+)",\s*\n\s*"instance_id":\s*"([^"]+)",\s*\n\s*"owner":\s*"([^"]+)",\s*\n\s*"status":\s*"([^"]+)"\s*\n\s*\}'
    hero_matches = re.findall(hero_pattern, json_str, re.DOTALL)
    for match in hero_matches:
        hero_key, hero_id, instance_id, owner, status = match
        # Reconstituer l'objet hero original pour le remplacer
        old_hero = f'{hero_key}: {{\n            "hero_id": "{hero_id}",\n            "instance_id": "{instance_id}",\n            "owner": "{owner}",\n            "status": "{status}"\n          }}'
        new_hero = f'{hero_key}: {{ "hero_id": "{hero_id}", "instance_id": "{instance_id}", "owner": "{owner}", "status": "{status}" }}'
        json_str = json_str.replace(old_hero, new_hero)
    
    return json_str

class DataManager:
    """Gestionnaire centralisé des données du jeu"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.data_dir = os.path.join(base_dir, 'data')  # Configurations (git)
        self.gamedata_dir = os.path.join(base_dir, 'gamedata')  # Sauvegardes (volume Railway)
        
        # Créer gamedata/ s'il n'existe pas
        os.makedirs(self.gamedata_dir, exist_ok=True)
        
        # Fichiers de sauvegarde (stockés dans gamedata/)
        self._save_files = {
            'players.json', 'savegame.json', 'player_quests.json',
            'battlefields_v2.json', 'battlesv2.json', 'battle_reports.json',
            'battle_replays.json', 'transports.json', 'transport_history.json',
            'market.json', 'messages.json', 'notifications.json',
            'player_heroes.json', 'player_profiles.json', 'player_unit_improvements.json'
        }
        
        # Cache pour éviter les rechargements
        self._cache = {}
        self._cache_timestamps = {}
        self._cache_duration = 5  # 5 secondes
        
        # Verrou pour les sauvegardes du savegame
        self._savegame_lock = threading.Lock()
        
        # Throttling global pour éviter les sauvegardes trop fréquentes
        self._last_save_times = {}
        self._save_throttle = {
            'savegame.json': 5,      # 5 secondes minimum entre sauvegardes
            'transports.json': 2,    # 2 secondes pour transports
            'players.json': 3,       # 3 secondes pour players
            'default': 1             # 1 seconde par défaut
        }
        
    def _get_file_path(self, filename: str) -> str:
        """Retourne le chemin complet vers un fichier de données
        
        Les fichiers de sauvegarde vont dans gamedata/ (volume Railway)
        Les fichiers de configuration vont dans data/ (git)
        """
        if filename in self._save_files:
            return os.path.join(self.gamedata_dir, filename)
        return os.path.join(self.data_dir, filename)
    
    def _is_cache_valid(self, key: str) -> bool:
        """Vérifie si le cache est encore valide"""
        if key not in self._cache:
            return False
        
        cache_time = self._cache_timestamps.get(key, 0)
        return (time.time() - cache_time) < self._cache_duration
    
    def _set_cache(self, key: str, data: Any) -> None:
        """Met en cache des données"""
        self._cache[key] = data
        self._cache_timestamps[key] = time.time()
    
    def _load_json_file(self, filepath: str, use_cache: bool = True) -> Optional[Dict]:
        """
        Charge un fichier JSON avec gestion d'erreurs robuste
        """
        cache_key = f"file_{filepath}"
        
        # Vérifier le cache
        if use_cache and self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        if not os.path.exists(filepath):
            return None
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        return None
                    
                    data = json.loads(content)
                    
                    # Mettre en cache
                    if use_cache:
                        self._set_cache(cache_key, data)
                    
                    return data
                    
            except (PermissionError, OSError) as e:
                if attempt < max_retries - 1:
                    time.sleep(0.1 * (2 ** attempt))
                    continue
                else:
                    print(f"Impossible de lire {filepath}: {e}")
                    return None
            except (ValueError, TypeError) as e:
                print(f"Fichier JSON invalide {filepath}: {e}")
                return None
        
        return None
    
    def _save_json_file(self, filepath: str, data: Dict, create_backup: bool = True, force_save: bool = False) -> bool:
        """
        Sauvegarde un fichier JSON avec gestion d'erreurs robuste et throttling
        
        Args:
            create_backup: Paramètre conservé pour compatibilité (fonctionnalité temporairement désactivée)
        """
        # Paramètre create_backup conservé pour compatibilité future  # noqa: vulture
        _ = create_backup  # Éviter le warning vulture
        
        # Vérifier le throttling (sauf si force_save)
        filename = os.path.basename(filepath)
        current_time = time.time()
        
        if not force_save:
            # Déterminer l'intervalle minimum
            min_interval = self._save_throttle.get(filename, self._save_throttle['default'])
            
            # Vérifier si on peut sauvegarder
            last_save = self._last_save_times.get(filename, 0)
            if current_time - last_save < min_interval:
                # Trop tôt pour sauvegarder
                return True  # Retourner True pour ne pas casser la logique
            
        max_retries = 5  # Augmenté de 3 à 5 pour les conflits d'accès
        backup_path = filepath + ".backup"
        
        for attempt in range(max_retries):
            tmp_path = None
            try:
                # Créer un fichier temporaire unique
                timestamp = int(time.time() * 1000)
                random_suffix = random.randint(1000, 9999)
                tmp_path = filepath + f".tmp.{timestamp}.{random_suffix}"
                
                # Écrire dans le fichier temporaire
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    # Formatage spécial pour savegame.json
                    if filename == 'savegame.json':
                        f.write(format_savegame_json(data))
                    else:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                
                # Vérifier l'intégrité du fichier temporaire
                try:
                    with open(tmp_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    print(f"❌ Erreur d'intégrité JSON détectée dans {tmp_path}: {e}")
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                    return False
                
                # Créer un backup si demandé - DÉSACTIVÉ TEMPORAIREMENT pour éviter WinError 32
                # if create_backup and os.path.exists(filepath):
                #     try:
                #         if os.path.exists(backup_path):
                #             os.remove(backup_path)
                #         os.replace(filepath, backup_path)
                #         # Logs désactivés pour réduire le spam
                #         # if 'savegame.json' in filepath:
                #         #     print(f"✅ Backup créé")
                #     except OSError as e:
                #         print(f"⚠️ Impossible de créer le backup: {e}")
                
                # Remplacer le fichier principal
                os.replace(tmp_path, filepath)
                
                # Mettre à jour le timestamp de dernière sauvegarde
                self._last_save_times[filename] = current_time
                
                # Logs désactivés pour réduire le spam
                # if 'savegame.json' in filepath:
                #     print(f"✅ Savegame sauvé")
                
                # Nettoyer le backup si succès - DÉSACTIVÉ car backups désactivés
                # if create_backup and os.path.exists(backup_path):
                #     try:
                #         os.remove(backup_path)
                #     except OSError:
                #         pass
                
                # Invalider le cache
                cache_key = f"file_{filepath}"
                if cache_key in self._cache:
                    del self._cache[cache_key]
                    del self._cache_timestamps[cache_key]
                
                return True
                
            except (PermissionError, OSError, ValueError) as e:
                if attempt < max_retries - 1:
                    wait_time = 0.1 * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                else:
                    return False
            finally:
                # Nettoyer le fichier temporaire
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass
        
        return False
    
    # === Méthodes publiques pour chaque fichier ===
    
    def load_universe(self) -> Dict:
        """Charge universe.json"""
        data = self._load_json_file(self._get_file_path('universe.json'))
        return data or {}
    
    def load_savegame(self) -> Dict:
        """Charge savegame.json avec récupération automatique et création si absent"""
        filepath = self._get_file_path('savegame.json')
        
        # Essayer le fichier principal
        data = self._load_json_file(filepath, use_cache=False)  # Pas de cache pour savegame
        if data:
            return data
        
        # Essayer le backup seulement s'il existe
        backup_path = filepath + ".backup"
        if os.path.exists(backup_path):
            data = self._load_json_file(backup_path, use_cache=False)
            if data:
                # Restaurer le fichier principal
                if self._save_json_file(filepath, data, create_backup=False):
                    return data
        
        # Si aucun fichier trouvé, créer un savegame vierge
        print("Aucun savegame trouvé, création d'un nouveau fichier vierge...")
        empty_savegame = {
            "cities": [],
            "players": {}
        }
        
        # Sauvegarder le nouveau savegame
        if self._save_json_file(filepath, empty_savegame, create_backup=False):
            print(f"Nouveau savegame créé: {filepath}")
            return empty_savegame
        else:
            print("Erreur lors de la création du nouveau savegame")
            return empty_savegame  # Retourner quand même la structure vierge
    
    def save_savegame(self, data: Dict, force_save: bool = False) -> bool:
        """Sauvegarde savegame.json avec protection contre les écritures simultanées"""
        # Logs réduits en dev
        with self._savegame_lock:
            # Nettoyer les données avant sauvegarde
            cleaned_data = self._clean_savegame_data(data)
            
            # Détecter les nouveaux bâtiments avant la sauvegarde
            self._detect_new_buildings(cleaned_data)
            
            filepath = self._get_file_path('savegame.json')
            result = self._save_json_file(filepath, cleaned_data, create_backup=True, force_save=force_save)
            
            return result
    
    def _clean_savegame_data(self, data: Dict) -> Dict:
        """Nettoie les données du savegame avant sauvegarde (supprime gold, players, etc.)"""
        import copy
        cleaned_data = copy.deepcopy(data)
        
        # Supprimer "gold" de chaque ville
        for city in cleaned_data.get("cities", []):
            resources = city.get("resources", {})
            if "gold" in resources:
                del resources["gold"]
        
        # Supprimer la section "players" qui fait doublon avec players.json
        # (Fait silencieusement pour ne pas polluer les logs)
        if "players" in cleaned_data:
            del cleaned_data["players"]
        
        return cleaned_data
    
    def _detect_new_buildings(self, new_data: Dict):
        """Détecte les nouveaux bâtiments et crée des notifications"""
        try:
            # Validation des données d'entrée
            if not new_data or not isinstance(new_data, dict):
                return
            
            # Charger l'ancien savegame pour comparaison
            old_data = self.load_savegame()
            if not old_data or not isinstance(old_data, dict):
                return
            
            # Comparer les bâtiments pour chaque ville
            for new_city in new_data.get('cities', []):
                if not new_city or not isinstance(new_city, dict):
                    continue
                    
                city_id = new_city.get('id')
                if not city_id:
                    continue
                
                # Trouver l'ancienne version de cette ville
                old_city = next((c for c in old_data.get('cities', []) 
                               if c and isinstance(c, dict) and c.get('id') == city_id), None)
                if not old_city:
                    continue
                    continue
                
                # Comparer les bâtiments
                old_buildings = {b.get('slot_id'): b for b in old_city.get('buildings', [])}
                new_buildings = {b.get('slot_id'): b for b in new_city.get('buildings', [])}
                
                # Détecter les nouveaux slots ou les bâtiments modifiés
                for slot_id, new_building in new_buildings.items():
                    old_building = old_buildings.get(slot_id)
                    
                    # Nouveau bâtiment ou bâtiment modifié (nouveau niveau)
                    if (not old_building or 
                        old_building.get('level', 1) < new_building.get('level', 1) or
                        old_building.get('name') != new_building.get('name')):
                        
                        # Notification désactivée ici car gérée par game_logic lors de finalisation
                        # Évite les doublons lors des upgrades
                        pass
                        
        except Exception as e:
            # Log silencieux pour éviter le spam
            pass
    
    def _create_building_notification(self, city: Dict, building: Dict):
        """Crée une notification pour un nouveau bâtiment"""
        try:
            from .business.notification_service import NotificationService
            from .models.notification import NotificationType
            
            notification_service = NotificationService(self)
            
            building_name = building.get('name', 'Bâtiment')
            city_name = city.get('name', 'Ville')
            player_id = city.get('owner', 'player_1')
            level = building.get('level', 1)
            
            notification_service.create_building_notification(
                player_id=player_id,
                building_name=f"{building_name} niveau {level}" if level > 1 else building_name,
                city_name=city_name
            )
            
            print(f"🔔 Notification créée: {building_name} niveau {level} dans {city_name}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la création de notification: {e}")
    
    def load_players(self, use_cache: bool = True) -> Dict:
        """Charge players.json"""
        data = self._load_json_file(self._get_file_path('players.json'), use_cache=use_cache)
        return data or {"players": []}
    

    
    def load_buildings(self) -> Dict:
        """Charge buildings.json"""
        data = self._load_json_file(self._get_file_path('buildings.json'))
        return data or {}
    
    def load_resource_sites_config(self) -> Dict:
        """Charge resource_sites_config.json"""
        data = self._load_json_file(self._get_file_path('resource_sites_config.json'))
        return data or {}
    
    def load_research(self) -> Dict:
        """Charge research.json"""
        data = self._load_json_file(self._get_file_path('research.json'))
        return data or {"researches": [], "categories": []}
    
    def load_universe(self) -> Dict:
        """Charge universe.json"""
        data = self._load_json_file(self._get_file_path('universe.json'))
        return data or {"islands": []}
    
    def save_universe(self, data: Dict) -> bool:
        """Sauvegarde universe.json"""
        filepath = self._get_file_path('universe.json')
        return self._save_json_file(filepath, data, create_backup=False)
    
    def load_notifications(self) -> Dict:
        """Charge notifications.json"""
        data = self._load_json_file(self._get_file_path('notifications.json'))
        return data or {"notifications": []}
    
    def save_notifications(self, data: Dict) -> bool:
        """Sauvegarde notifications.json"""
        filepath = self._get_file_path('notifications.json')
        return self._save_json_file(filepath, data, create_backup=False)
    
    def load_market(self, use_cache: bool = False) -> Dict:
        """Charge market.json"""
        filepath = self._get_file_path('market.json')
        
        if use_cache:
            data = self._get_from_cache('market')
            if data is not None:
                return data
        
        data = self._load_json_file(filepath)
        if not data:
            # Structure par défaut si le fichier n'existe pas
            data = {
                "offers": [],
                "metadata": {
                    "created": "2025-08-30T17:37:14.315823",
                    "version": "1.0",
                    "last_cleanup": None
                },
                "statistics": {
                    "total_offers_created": 0,
                    "total_transactions": 0,
                    "total_volume": 0
                }
            }
            # Créer le fichier avec la structure par défaut
            self.save_market(data)
        
        if use_cache:
            self._set_cache('market', data)
        
        return data
    
    def save_market(self, data: Dict, force_save: bool = False) -> bool:
        """Sauvegarde market.json"""
        filepath = self._get_file_path('market.json')
        
        # Mettre à jour les métadonnées
        if 'metadata' not in data:
            data['metadata'] = {}
        data['metadata']['last_update'] = time.time()
        
        # Invalider le cache
        self._cache.pop('market', None)
        self._cache_timestamps.pop('market', None)
        
        return self._save_json_file(filepath, data, create_backup=False)
    
    def load_transports(self, use_cache: bool = False) -> Dict:
        """Charge transports.json"""
        filepath = self._get_file_path('transports.json')
        return self._load_json_file(filepath, use_cache) or {"transports": [], "next_id": 1}
    
    def save_transports(self, data: Dict, force_save: bool = False) -> bool:
        """Sauvegarde transports.json"""
        filepath = self._get_file_path('transports.json')
        
        # Invalider le cache
        self._cache.pop('transports', None)
        self._cache_timestamps.pop('transports', None)
        
        return self._save_json_file(filepath, data, create_backup=False, force_save=force_save)
    
    def load_transport_history(self, use_cache: bool = False) -> Dict:
        """Charge transport_history.json"""
        filepath = self._get_file_path('transport_history.json')
        return self._load_json_file(filepath, use_cache) or {"transport_history": []}
    
    def save_transport_history(self, data: Dict, force_save: bool = False) -> bool:
        """Sauvegarde transport_history.json"""
        filepath = self._get_file_path('transport_history.json')
        
        # Invalider le cache
        self._cache.pop('transport_history', None)
        self._cache_timestamps.pop('transport_history', None)
        
        return self._save_json_file(filepath, data, create_backup=False, force_save=force_save)

    def load_unit_transports(self, use_cache: bool = False) -> Dict:
        """Charge unit_transports.json"""
        filepath = self._get_file_path('unit_transports.json')
        return self._load_json_file(filepath, use_cache) or {"transports": [], "next_id": 1}

    def save_unit_transports(self, data: Dict, force_save: bool = False) -> bool:
        """Sauvegarde unit_transports.json"""
        filepath = self._get_file_path('unit_transports.json')
        
        # Invalider le cache
        self._cache.pop('unit_transports', None)
        self._cache_timestamps.pop('unit_transports', None)
        
        return self._save_json_file(filepath, data, create_backup=False, force_save=force_save)

    def load_unit_transport_history(self, use_cache: bool = False) -> Dict:
        """Charge unit_transport_history.json"""
        filepath = self._get_file_path('unit_transport_history.json')
        return self._load_json_file(filepath, use_cache) or {"transport_history": []}

    def load_players(self, use_cache: bool = False) -> Dict:
        """Charge players.json"""
        filepath = self._get_file_path('players.json')
        return self._load_json_file(filepath, use_cache) or {"players": []}
    
    def save_players(self, data: Dict, force_save: bool = False) -> bool:
        """Sauvegarde players.json et synchronise avec savegame.json"""
        filepath = self._get_file_path('players.json')
        
        # Invalider le cache
        self._cache.pop('players', None)
        self._cache_timestamps.pop('players', None)
        
        # Sauvegarder players.json
        result = self._save_json_file(filepath, data, create_backup=False, force_save=force_save)
        
        # Synchroniser avec savegame.json
        if result:
            self._sync_transport_ships_to_savegame(data)
        
        return result

    def _sync_transport_ships_to_savegame(self, players_data: Dict) -> None:
        """Synchronise les données de transport de players.json vers savegame.json"""
        try:
            # Charger savegame.json
            savegame = self.load_savegame()
            if not savegame or 'players' not in savegame:
                return
            
            changes_made = False
            
            # Synchroniser chaque joueur
            for player in players_data.get('players', []):
                player_id = player.get('id')
                if not player_id or player_id not in savegame['players']:
                    continue
                
                # Données de transport à synchroniser
                transport_ships_total = player.get('transport_ships_total')
                transport_ships_busy = player.get('transport_ships_busy')
                
                sg_player = savegame['players'][player_id]
                
                # Mettre à jour si nécessaire
                if transport_ships_total is not None and sg_player.get('transport_ships_total') != transport_ships_total:
                    sg_player['transport_ships_total'] = transport_ships_total
                    changes_made = True
                
                if transport_ships_busy is not None and sg_player.get('transport_ships_busy') != transport_ships_busy:
                    sg_player['transport_ships_busy'] = transport_ships_busy
                    changes_made = True
            
            # Sauvegarder si des changements ont été faits
            if changes_made:
                self.save_savegame(savegame, force_save=True)
                
        except Exception as e:
            print(f"❌ Erreur synchronisation transport ships: {e}")

    def clear_cache(self) -> None:
        """Vide le cache"""
        self._cache.clear()
        self._cache_timestamps.clear()
    
    def load_battlefields_v2(self, use_cache: bool = False) -> Dict:
        """Charge battlefields_v2.json"""
        filepath = self._get_file_path('battlefields_v2.json')
        return self._load_json_file(filepath, use_cache) or {}
    
    def save_battlefields_v2(self, data: Dict, force_save: bool = False) -> bool:
        """Sauvegarde battlefields_v2.json"""
        filepath = self._get_file_path('battlefields_v2.json')
        
        # Invalider le cache
        self._cache.pop('battlefields_v2', None)
        self._cache_timestamps.pop('battlefields_v2', None)
        
        return self._save_json_file(filepath, data, create_backup=False, force_save=force_save)
