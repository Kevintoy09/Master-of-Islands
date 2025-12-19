"""
BattleStatsServiceV2.py

Service dédié à la gestion des statistiques de bataille en temps réel
- Calcul des stats (unités, moral) depuis battlefields_v2.json
- Mise à jour des statistiques pendant la bataille
- Séparé de la création de bataille pour une meilleure organisation
"""

import json
import os
import time
from typing import Dict, Any, Optional

# Import du service de stats amélioré pour inclure les bonus de forge
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.battle.enhanced_unit_stats_service import EnhancedUnitStatsService
from app.config.paths import STATIC_DATA_DIR, GAME_DATA_DIR, BATTLEFIELDS_V2_FILE, UNIT_STATS_FILE
from app.services.unit_stats_service import get_unit_stats_service


class BattleStatsServiceV2:
    """
    Service V2 pour la gestion des statistiques de bataille
    - Calcul en temps réel des unités et moral
    - Mise à jour des statistiques pendant le combat
    - Gestion propre et séparée de la création de bataille
    """
    
    def __init__(self):
        # Utiliser les constantes de chemins
        self.battlefields_v2_path = BATTLEFIELDS_V2_FILE
        self.gamedata_dir = GAME_DATA_DIR
        self.data_dir = STATIC_DATA_DIR
        
        # Service pour stats d'unités avec bonus de forge
        self.enhanced_stats_service = EnhancedUnitStatsService()
        
        # Service centralisé pour les stats d'unités
        self.unit_stats_service = get_unit_stats_service()
        
        # Cache pour battlefields
        self._battlefields_cache: Optional[Dict[str, Any]] = None
        self._battlefields_cache_time = 0
        self._battlefields_cache_duration = 0.5  # 500ms
    
    def _load_battlefields_v2(self, use_cache: bool = True) -> Dict[str, Any]:
        """Charge le fichier battlefields_v2.json avec cache optionnel"""
        current_time = time.time()
        
        # Utiliser le cache si valide
        if use_cache and self._battlefields_cache is not None:
            if current_time - self._battlefields_cache_time < self._battlefields_cache_duration:
                return self._battlefields_cache
        
        # Charger depuis le disque
        try:
            with open(self.battlefields_v2_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Mettre en cache
                if use_cache:
                    self._battlefields_cache = data
                    self._battlefields_cache_time = current_time
                
                return data
        except Exception as e:
            return {}
    
    def _save_battlefields_v2(self, data: Dict[str, Any]):
        """Sauvegarde le fichier battlefields_v2.json et invalide le cache"""
        try:
            with open(self.battlefields_v2_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Invalider le cache après sauvegarde
            self._battlefields_cache = None
        except Exception as e:
            pass
    
    def get_battle_stats(self, battle_id: str) -> Dict[str, Any]:
        """
        Calcule et retourne les statistiques en temps réel d'une bataille
        
        Args:
            battle_id: ID du battlefield
            
        Returns:
            Dict avec les stats attaquant/défenseur (unités, moral)
        """
        try:
            battlefields_data = self._load_battlefields_v2()
            
            if battle_id not in battlefields_data:
                return {
                    "success": False,
                    "error": f"Battlefield {battle_id} non trouvé"
                }
            
            battlefield = battlefields_data[battle_id]
            forces = battlefield.get('forces', {})
            attackers = forces.get('attackers', {})
            defenders = forces.get('defenders', {})
            
            # Calculer les stats attaquant
            attacker_units_total = 0
            attacker_moral = 100  # Valeur par défaut
            attacker_hero_bonus = 0  # Bonus moral des héros
            
            for player_id, player_data in attackers.items():
                # Calculer les unités initiales depuis contributions
                initial_units_total = 0
                contributions = player_data.get('contributions', [])
                for contribution in contributions:
                    units = contribution.get('units', {})
                    for unit_count in units.values():
                        if isinstance(unit_count, (int, float)):
                            initial_units_total += int(unit_count)
                    
                    # Calculer le bonus moral des héros dans cette contribution
                    heroes = contribution.get('heroes', [])
                    for hero_id in heroes:
                        hero_bonus = self._get_hero_moral_bonus(hero_id, player_id)
                        attacker_hero_bonus += hero_bonus
                
                # Calculer les unités perdues
                units_lost = player_data.get('units_lost', {})
                lost_units_total = 0
                for unit_type, lost_count in units_lost.items():
                    if isinstance(lost_count, (int, float)):
                        lost_units_total += int(lost_count)
                
                # Unités survivantes = initiales - perdues
                surviving_units = max(0, initial_units_total - lost_units_total)
                attacker_units_total += surviving_units
                
                # Récupérer le moral directement (plus de calcul complexe)
                attacker_moral = player_data.get('moral', 100)
            
            # SIMPLE: Utiliser le moral stocké tel quel
            final_attacker_moral = attacker_moral
            
            # Calculer les stats défenseur
            defender_units_total = 0
            defender_moral = 100  # Valeur par défaut
            defender_hero_bonus = 0  # Bonus moral des héros (pour le log)
            
            for player_id, player_data in defenders.items():
                # Calculer les unités initiales depuis contributions
                initial_units_total = 0
                contributions = player_data.get('contributions', [])
                for contribution in contributions:
                    units = contribution.get('units', {})
                    for unit_count in units.values():
                        if isinstance(unit_count, (int, float)):
                            initial_units_total += int(unit_count)
                    
                    # Calculer le bonus moral des héros dans cette contribution
                    heroes = contribution.get('heroes', [])
                    for hero_id in heroes:
                        hero_bonus = self._get_hero_moral_bonus(hero_id, player_id)
                        defender_hero_bonus += hero_bonus
                
                # Calculer les unités perdues
                units_lost = player_data.get('units_lost', {})
                lost_units_total = 0
                for unit_type, lost_count in units_lost.items():
                    if isinstance(lost_count, (int, float)):
                        lost_units_total += int(lost_count)
                
                # Unités survivantes = initiales - perdues
                surviving_units = max(0, initial_units_total - lost_units_total)
                defender_units_total += surviving_units
                
                # Récupérer le moral directement (plus de calcul complexe)
                defender_moral = player_data.get('moral', 100)
            
            # SIMPLE: Utiliser le moral stocké tel quel
            final_defender_moral = defender_moral
            
            # Supprimer le log verbeux répétitif
            # print(f"📊 [StatsV2] Stats calculées pour {battle_id} - Att: {attacker_units_total}u/{attacker_moral}m, Def: {defender_units_total}u/{defender_moral}m")
            
            return {
                "success": True,
                "attacker": {
                    "units": attacker_units_total,
                    "moral": final_attacker_moral
                },
                "defender": {
                    "units": defender_units_total,
                    "moral": final_defender_moral
                },
                # Format attendu par le client pour BattlePopup.tsx
                "unit_counts": {
                    "attacker": attacker_units_total,
                    "defender": defender_units_total
                },
                "moral": {
                    "attacker": final_attacker_moral,
                    "defender": final_defender_moral
                },
                "current_round": battlefield.get('current_round', 1),
                "last_updated": int(time.time())
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_battle_stats(self, battle_id: str, attacker_stats: Dict = None, defender_stats: Dict = None) -> bool:
        """
        Met à jour les statistiques d'une bataille (unités et moral)
        
        Args:
            battle_id: ID du battlefield
            attacker_stats: Dict avec 'units' et/ou 'moral' pour l'attaquant
            defender_stats: Dict avec 'units' et/ou 'moral' pour le défenseur
            
        Returns:
            bool: True si la mise à jour a réussi
        """
        try:
            battlefields_data = self._load_battlefields_v2()
            
            if battle_id not in battlefields_data:
                return False
            
            battlefield = battlefields_data[battle_id]
            forces = battlefield.setdefault('forces', {})
            attackers = forces.setdefault('attackers', {})
            defenders = forces.setdefault('defenders', {})
            
            # Mettre à jour les stats attaquant
            if attacker_stats:
                for player_id, player_data in attackers.items():
                    if 'moral' in attacker_stats:
                        player_data['moral'] = attacker_stats['moral']
                    # Note: les unités sont plus complexes à mettre à jour car elles sont réparties par type
                    # Pour l'instant, on met à jour seulement le moral
            
            # Mettre à jour les stats défenseur
            if defender_stats:
                for player_id, player_data in defenders.items():
                    if 'moral' in defender_stats:
                        player_data['moral'] = defender_stats['moral']
            
            # Sauvegarder les changements
            self._save_battlefields_v2(battlefields_data)
            return True
            
        except Exception as e:
            return False
    
    def get_battlefield(self, battle_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un battlefield par son ID (méthode helper)
        
        Args:
            battle_id: ID du battlefield
            
        Returns:
            Dict avec les données du battlefield ou None si non trouvé
        """
        try:
            battlefields_data = self._load_battlefields_v2()
            return battlefields_data.get(battle_id)
        except Exception as e:
            return None

    # ============================================================================
    # NOUVELLES FONCTIONS XP/KILLS/LOSSES
    # ============================================================================
    
    def get_unit_xp_value(self, unit_type: str) -> int:
        """Récupère la valeur XP d'un type d'unité (utilise UnitStatsService)"""
        return self.unit_stats_service.get_xp_value(unit_type)
    
    def extract_unit_type(self, unit_id: str) -> str:
        """
        Extrait le type d'unité depuis l'ID
        Formats supportés:
        - auto_attacker_playerX_unit_type_index
        - attacker_playerX_unit_type_timestamp_index
        - wild_camp_unit_type_index
        - barbarian_village_unit_type_index
        """
        if not unit_id:
            return 'unknown'
        
        # Diviser par underscore
        parts = unit_id.split('_')
        
        if len(parts) < 3:
            return 'unknown'
        
        # 🆕 Supprimer le préfixe "auto" si présent
        if parts[0] == 'auto':
            parts = parts[1:]  # Retirer "auto_"
        
        # 🆕 Gérer les formats wild_camp et barbarian_village
        try:
            wild_index = parts.index('wild')
            if wild_index + 1 < len(parts) and parts[wild_index + 1] == 'camp':
                # Format: wild_camp_barbarian_warrior_2 → barbarian_warrior
                start_index = wild_index + 2
                unit_type_parts = parts[start_index:-1] if parts[-1].isdigit() else parts[start_index:]
                return '_'.join(unit_type_parts)
        except ValueError:
            pass  # 'wild' pas trouvé, continuer
        
        try:
            barbarian_index = parts.index('barbarian')
            if barbarian_index > 0 and parts[barbarian_index - 1] == 'village':
                start_index = barbarian_index + 1
                unit_type_parts = parts[start_index:-1] if parts[-1].isdigit() else parts[start_index:]
                return '_'.join(unit_type_parts)
        except ValueError:
            pass
        
        # Format standard: [attacker/defender]_[playerX]_[unit_type]_[timestamp?]_[index]
        if len(parts) < 3:
            return 'unknown'
        
        # Trouver où commence "player" pour savoir où se termine le préfixe
        player_index = -1
        for i, part in enumerate(parts):
            if part == 'player' or (part.startswith('player') and part[6:].isdigit()):
                player_index = i
                break
        
        if player_index == -1:
            return 'unknown'
        
        # Après player_X, récupérer les segments jusqu'au dernier index
        # Format: [team]_[player]_[X]_[unit_type_parts...]_[index]
        start_unit_type = player_index + 2  # Sauter "player" et le numéro
        
        if start_unit_type >= len(parts):
            return 'unknown'
        
        # Prendre tout sauf le dernier segment (qui est l'index numérique)
        unit_type_parts = parts[start_unit_type:-1] if parts[-1].isdigit() and len(parts[-1]) < 5 else parts[start_unit_type:]
        
        if not unit_type_parts:
            return 'unknown'
        
        # Si le premier segment est "hero", retourner juste "hero"
        if unit_type_parts[0] == 'hero':
            return 'hero'
        
        return '_'.join(unit_type_parts)
        return unit_type_part
    
    def update_battle_stats_on_combat(self, battle_id: str, attacker_id: str, defender_id: str, 
                                    kills: int, damage: float = 0) -> bool:
        """
        Met à jour les statistiques de bataille lors d'un combat
        
        Args:
            battle_id: ID de la bataille
            attacker_id: ID de l'unité attaquante
            defender_id: ID de l'unité défendante
            kills: Nombre d'unités tuées
            damage: Dégâts infligés (héros)
            
        Returns:
            bool: True si succès
        """
        try:
            battlefields_data = self._load_battlefields_v2()
            
            if battle_id not in battlefields_data:
                return False
            
            battlefield = battlefields_data[battle_id]
            forces = battlefield.get('forces', {})
            
            # Déterminer les équipes
            attacker_team = 'attackers' if 'attacker' in attacker_id else 'defenders'
            defender_team = 'defenders' if 'defender' in defender_id else 'attackers'
            
            # Trouver les joueurs
            attacker_player = None
            defender_player = None
            
            for team_name in ['attackers', 'defenders']:
                for player_id in forces.get(team_name, {}):
                    if attacker_team == team_name and not attacker_player:
                        attacker_player = player_id
                    elif defender_team == team_name and not defender_player:
                        defender_player = player_id
            
            if not attacker_player or not defender_player:
                return False
            
            # Type d'unité défendante
            defender_type = self.extract_unit_type(defender_id)
            
            # Mettre à jour units_lost (défenseur)
            if kills > 0:
                defender_forces = forces[defender_team][defender_player]
                
                if 'units_lost' not in defender_forces:
                    defender_forces['units_lost'] = {}
                
                current_lost = defender_forces['units_lost'].get(defender_type, 0)
                defender_forces['units_lost'][defender_type] = current_lost + kills
                
            
            # Mettre à jour units_killed et XP (attaquant)
            if kills > 0:
                attacker_forces = forces[attacker_team][attacker_player]
                
                if 'units_killed' not in attacker_forces:
                    attacker_forces['units_killed'] = {}
                
                current_killed = attacker_forces['units_killed'].get(defender_type, 0)
                attacker_forces['units_killed'][defender_type] = current_killed + kills
                
                # Calculer XP
                xp_per_unit = self.get_unit_xp_value(defender_type)
                xp_gained = kills * xp_per_unit
                
                current_xp = attacker_forces.get('xp_gained', 0)
                attacker_forces['xp_gained'] = current_xp + xp_gained
                
            
            # Sauvegarder
            self._save_battlefields_v2(battlefields_data)
            return True
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False
    
    def enrich_battle_with_forge_bonuses(self, battle_id: str) -> bool:
        """
        Enrichit les données d'une bataille avec les bonus de forge des joueurs
        Applique les améliorations aux stats des unités selon leurs types
        
        Args:
            battle_id: ID du battlefield à enrichir
            
        Returns:
            bool: True si enrichissement réussi
        """
        try:
            battlefields_data = self._load_battlefields_v2()
            
            if battle_id not in battlefields_data:
                return False
            
            battlefield = battlefields_data[battle_id]
            forces = battlefield.get('forces', {})
            
            
            # Enrichir les attackers
            for player_id, player_data in forces.get('attackers', {}).items():
                units = player_data.get('units', {})
                for unit_type, unit_count in units.items():
                    if isinstance(unit_count, (int, float)) and unit_count > 0:
                        # Les stats avec bonus de forge sont récupérées à la demande
                        # via enhanced_stats_service.get_unit_stats_with_forge_bonus()
                        # Plus besoin de les stocker dans battlefields_v2.json
                        pass
            
            # Enrichir les defenders
            for player_id, player_data in forces.get('defenders', {}).items():
                units = player_data.get('units', {})
                for unit_type, unit_count in units.items():
                    if isinstance(unit_count, (int, float)) and unit_count > 0:
                        # Les stats avec bonus de forge sont récupérées à la demande
                        # via enhanced_stats_service.get_unit_stats_with_forge_bonus()
                        # Plus besoin de les stocker dans battlefields_v2.json
                        pass
            
            # Sauvegarder les données enrichies
            self._save_battlefields_v2(battlefields_data)
            return True
            
        except Exception as e:
            return False

    def _get_hero_moral_bonus(self, hero_id: str, player_id: str) -> int:
        """
        Récupère le bonus moral d'un héros depuis player_heroes.json
        
        Args:
            hero_id: ID de l'instance du héros (ex: "hero_1760985204_35f1db")
            player_id: ID du joueur possédant le héros
            
        Returns:
            int: Bonus moral du héros (0 si non trouvé)
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
            
            return True
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False


# Instance singleton pour le service
_battle_stats_service_v2 = None

def get_battle_stats_service_v2() -> BattleStatsServiceV2:
    """Retourne l'instance singleton du service de stats V2"""
    global _battle_stats_service_v2
    if _battle_stats_service_v2 is None:
        _battle_stats_service_v2 = BattleStatsServiceV2()
    return _battle_stats_service_v2
