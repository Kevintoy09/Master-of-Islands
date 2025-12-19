"""
Enhanced Unit Stats Service

Service pour récupérer les statistiques d'unités avec les bonus de forge appliqués.
Ce service remplace les appels directs à unit_stats.json pour inclure les améliorations personnalisées.

Usage:
    service = EnhancedUnitStatsService()
    stats = service.get_unit_stats_with_forge_bonus(unit_type, player_id)
"""

import json
import os
from typing import Dict, Any, Optional
from .unit_improvement_service import UnitImprovementService


class EnhancedUnitStatsService:
    """
    Service pour récupérer les stats d'unité avec bonus de forge appliqués
    Utilisé par le système de combat pour avoir les vraies stats des unités des joueurs
    """
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.unit_stats_file = os.path.join(self.base_path, 'data', 'unit_stats.json')
        
        # Service d'améliorations d'unités pour récupérer les bonus de forge
        self.unit_improvement_service = UnitImprovementService()
        
        # Cache des stats de base
        self._unit_stats_cache = None
    
    def _load_unit_stats(self) -> Dict[str, Any]:
        """Charge les statistiques d'unités de base depuis unit_stats.json avec cache"""
        if self._unit_stats_cache is None:
            try:
                if os.path.exists(self.unit_stats_file):
                    with open(self.unit_stats_file, 'r', encoding='utf-8') as f:
                        self._unit_stats_cache = json.load(f)
                else:
                    self._unit_stats_cache = {}
            except Exception as e:
                self._unit_stats_cache = {}
        
        return self._unit_stats_cache
    
    def get_base_unit_stats(self, unit_type: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les statistiques de base d'un type d'unité depuis unit_stats.json
        
        Args:
            unit_type: Type d'unité (ex: 'infantry_light', 'archer')
            
        Returns:
            Dict avec les stats de base ou None si non trouvé
        """
        unit_stats = self._load_unit_stats()
        
        # Chercher dans toutes les ères
        for era_name, era_units in unit_stats.items():
            if unit_type in era_units:
                return era_units[unit_type].copy()  # Copy pour éviter les modifications
        
        return None
    
    def get_unit_stats_with_forge_bonus(self, unit_type: str, player_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les statistiques d'unité avec les bonus de forge appliqués
        
        Args:
            unit_type: Type d'unité (ex: 'infantry_light', 'archer')
            player_id: ID du joueur pour récupérer ses améliorations
            
        Returns:
            Dict avec les stats enhancées ou None si type d'unité invalide
        """
        # Récupérer les stats de base
        base_stats = self.get_base_unit_stats(unit_type)
        if not base_stats:
            return None
        
        # Récupérer les améliorations du joueur pour cette unité
        player_improvements = self.unit_improvement_service.get_player_improvements(player_id)
        unit_improvements = player_improvements.get(unit_type, {})
        
        # Appliquer les bonus aux stats de combat
        enhanced_stats = base_stats.copy()
        
        # ✅ NOUVEAU: Ajouter les informations de bonus pour l'affichage côté client
        forge_bonuses = {}
        
        # Les 4 stats améliorables par la forge
        combat_stats = ['attack_melee', 'defense_melee', 'attack_ranged', 'defense_ranged']
        
        for stat in combat_stats:
            if stat in base_stats:
                base_value = base_stats[stat]
                bonus_percent = unit_improvements.get(stat, 0)
                
                if bonus_percent > 0:
                    # Appliquer le bonus : nouvelle_valeur = base * (1 + bonus/100)
                    enhanced_value = int(base_value * (1 + bonus_percent / 100))
                    enhanced_stats[stat] = enhanced_value
                    
                    # ✅ NOUVEAU: Stocker les infos de bonus pour l'affichage
                    forge_bonuses[stat] = {
                        'base_value': base_value,
                        'bonus_percent': bonus_percent,
                        'enhanced_value': enhanced_value
                    }
                    
        
        # ✅ NOUVEAU: Ajouter les infos de bonus aux stats retournées
        if forge_bonuses:
            enhanced_stats['_forge_bonuses'] = forge_bonuses
        
        return enhanced_stats
    
    def get_multiple_units_stats_with_forge_bonus(self, unit_data: list, player_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Récupère les stats avec bonus pour plusieurs unités
        
        Args:
            unit_data: Liste d'unités avec leur type
            player_id: ID du joueur
            
        Returns:
            Dict {unit_id: enhanced_stats}
        """
        result = {}
        
        for unit in unit_data:
            unit_id = unit.get('id', unit.get('unitId', ''))
            unit_type = self._extract_unit_type(unit_id)
            
            if unit_type:
                enhanced_stats = self.get_unit_stats_with_forge_bonus(unit_type, player_id)
                if enhanced_stats:
                    result[unit_id] = enhanced_stats
        
        return result
    
    def _extract_unit_type(self, unit_id: str) -> str:
        """
        Extrait le type d'unité depuis un ID d'unité
        Format attendu: "attacker_playerX_unit_type_timestamp_index" ou "attacker_playerX_hero_timestamp"
        """
        if not unit_id:
            return ''
        
        # Diviser par underscore
        parts = unit_id.split('_')
        
        if len(parts) < 3:
            return ''
        
        # Format: [attacker/defender]_[playerX]_[unit_type]_[timestamp]_[index]
        team = parts[0]  # attacker ou defender
        player = parts[1]  # playerX
        unit_type_part = parts[2]  # unit_type ou hero
        
        if unit_type_part == 'hero':
            return 'hero'
        
        # Pour les unités normales, peut être sur plusieurs segments
        # Ex: attacker_player3_infantry_light_timestamp_index
        if len(parts) >= 4:
            # Prendre tous les segments entre player et timestamp
            unit_type_segments = []
            for i in range(2, len(parts)):
                # Arrêter si on arrive à un timestamp (nombre long)
                if parts[i].isdigit() and len(parts[i]) > 10:
                    break
                unit_type_segments.append(parts[i])
            
            if unit_type_segments:
                return '_'.join(unit_type_segments)
        
        # Fallback
        return unit_type_part
    
    def get_enhanced_stats_for_battle_units(self, battle_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour les stats d'une bataille complète avec les bonus de forge
        
        Args:
            battle_data: Données de bataille avec unités attackers/defenders
            
        Returns:
            battle_data avec stats enhancées appliquées
        """
        enhanced_battle_data = battle_data.copy()
        
        # Traiter les attaquants
        if 'attackers' in battle_data:
            attacker_player_id = battle_data.get('attacker_player_id', '')
            for unit in enhanced_battle_data.get('attackers', []):
                unit_type = self._extract_unit_type(unit.get('id', ''))
                enhanced_stats = self.get_unit_stats_with_forge_bonus(unit_type, attacker_player_id)
                if enhanced_stats:
                    # Mettre à jour les stats de combat dans l'unité
                    unit.update({
                        'attack_melee': enhanced_stats.get('attack_melee', unit.get('attack_melee', 0)),
                        'defense_melee': enhanced_stats.get('defense_melee', unit.get('defense_melee', 0)),
                        'attack_ranged': enhanced_stats.get('attack_ranged', unit.get('attack_ranged', 0)),
                        'defense_ranged': enhanced_stats.get('defense_ranged', unit.get('defense_ranged', 0))
                    })
        
        # Traiter les défenseurs
        if 'defenders' in battle_data:
            defender_player_id = battle_data.get('defender_player_id', '')
            for unit in enhanced_battle_data.get('defenders', []):
                unit_type = self._extract_unit_type(unit.get('id', ''))
                enhanced_stats = self.get_unit_stats_with_forge_bonus(unit_type, defender_player_id)
                if enhanced_stats:
                    # Mettre à jour les stats de combat dans l'unité
                    unit.update({
                        'attack_melee': enhanced_stats.get('attack_melee', unit.get('attack_melee', 0)),
                        'defense_melee': enhanced_stats.get('defense_melee', unit.get('defense_melee', 0)),
                        'attack_ranged': enhanced_stats.get('attack_ranged', unit.get('attack_ranged', 0)),
                        'defense_ranged': enhanced_stats.get('defense_ranged', unit.get('defense_ranged', 0))
                    })
        
        return enhanced_battle_data
    
    def clear_cache(self):
        """Vide le cache des stats d'unité (utile après modification des fichiers)"""
        self._unit_stats_cache = None
