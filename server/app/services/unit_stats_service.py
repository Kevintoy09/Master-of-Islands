"""
UnitStatsService - Service centralisé pour les statistiques d'unités
=====================================================================

Service unique pour gérer toutes les statistiques d'unités, évitant la duplication
de logique entre battle_stats_service_v2.py et enhanced_unit_stats_service.py
"""

import json
import os
from typing import Dict, Any, Optional
from app.config.paths import UNIT_STATS_FILE


class UnitStatsService:
    """Service centralisé pour la gestion des statistiques d'unités"""
    
    def __init__(self):
        self._unit_stats_cache: Optional[Dict[str, Any]] = None
    
    def _load_unit_stats(self) -> Dict[str, Any]:
        """Charge les statistiques d'unités depuis unit_stats.json avec cache"""
        if self._unit_stats_cache is None:
            try:
                if os.path.exists(UNIT_STATS_FILE):
                    with open(UNIT_STATS_FILE, 'r', encoding='utf-8') as f:
                        self._unit_stats_cache = json.load(f)
                else:
                    self._unit_stats_cache = {}
            except Exception as e:
                print(f"❌ Erreur chargement unit_stats.json: {e}")
                self._unit_stats_cache = {}
        
        return self._unit_stats_cache
    
    def get_xp_value(self, unit_type: str) -> int:
        """
        Récupère la valeur XP d'un type d'unité
        
        Args:
            unit_type: Type d'unité (ex: "barbarian_warrior", "infantry_light")
        
        Returns:
            Valeur XP de l'unité (0 si non trouvé)
        """
        unit_stats = self._load_unit_stats()
        
        # Nettoyer le type d'unité
        clean_unit_type = self._clean_unit_type(unit_type)
        
        # D'abord chercher dans enemy_units (unités barbares)
        if 'enemy_units' in unit_stats and clean_unit_type in unit_stats['enemy_units']:
            return unit_stats['enemy_units'][clean_unit_type].get('xp_value', 0)
        
        # Chercher dans toutes les ères
        for era_name, era_units in unit_stats.items():
            if era_name == 'enemy_units':
                continue
            if isinstance(era_units, dict) and clean_unit_type in era_units:
                return era_units[clean_unit_type].get('xp_value', 0)
        
        return 0
    
    def get_stats(self, unit_type: str) -> Optional[Dict[str, Any]]:
        """
        Récupère toutes les statistiques d'un type d'unité
        
        Args:
            unit_type: Type d'unité
        
        Returns:
            Dictionnaire complet des stats ou None si non trouvé
        """
        unit_stats = self._load_unit_stats()
        clean_unit_type = self._clean_unit_type(unit_type)
        
        # Chercher dans enemy_units d'abord
        if 'enemy_units' in unit_stats and clean_unit_type in unit_stats['enemy_units']:
            return unit_stats['enemy_units'][clean_unit_type]
        
        # Chercher dans toutes les ères
        for era_name, era_units in unit_stats.items():
            if era_name == 'enemy_units':
                continue
            if isinstance(era_units, dict) and clean_unit_type in era_units:
                return era_units[clean_unit_type]
        
        return None
    
    def is_enemy_unit(self, unit_type: str) -> bool:
        """
        Détermine si une unité est une unité ennemie (barbare, pirate, etc.)
        
        Args:
            unit_type: Type d'unité
        
        Returns:
            True si c'est une unité ennemie
        """
        unit_stats = self._load_unit_stats()
        clean_unit_type = self._clean_unit_type(unit_type)
        
        return 'enemy_units' in unit_stats and clean_unit_type in unit_stats['enemy_units']
    
    def _clean_unit_type(self, unit_type: str) -> str:
        """
        Nettoie le type d'unité en retirant les préfixes communs
        
        Args:
            unit_type: Type brut (ex: "1_infantry_light", "village_barbarian_warrior")
        
        Returns:
            Type nettoyé (ex: "infantry_light", "barbarian_warrior")
        """
        if not unit_type:
            return ''
        
        # Retirer le préfixe player si présent (ex: "1_infantry_light" → "infantry_light")
        if '_' in unit_type and unit_type.split('_')[0].isdigit():
            unit_type = '_'.join(unit_type.split('_')[1:])
        
        # Retirer le préfixe village_ si présent (ex: "village_barbarian_warrior" → "barbarian_warrior")
        if unit_type.startswith('village_'):
            unit_type = unit_type[8:]
        
        return unit_type
    
    def reload_cache(self):
        """Force le rechargement du cache des statistiques d'unités"""
        self._unit_stats_cache = None
        self._load_unit_stats()


# Instance globale singleton
_unit_stats_service_instance = None

def get_unit_stats_service() -> UnitStatsService:
    """Récupère l'instance singleton du service"""
    global _unit_stats_service_instance
    if _unit_stats_service_instance is None:
        _unit_stats_service_instance = UnitStatsService()
    return _unit_stats_service_instance
