"""
Analyseurs pour déterminer les besoins en population et ressources.

Ce fichier contient les outils d'analyse pour les stratégies autonomes
(colonisation, expansion) où l'IA doit prendre des décisions elle-même.

Pour les stratégies prescriptives (BUILD_ORDER), ces analyseurs ne sont pas nécessaires.
"""

from typing import Dict
import json
import os


# ============================================================
# SYSTÈME DE DÉCISION POUR MANQUES DE RESSOURCES
# ============================================================
#
# PRINCIPE: Quand l'IA manque d'une ressource, 2 solutions possibles:
#
# 1. ATTENDRE (production naturelle)
#    - Si le joueur PRODUIT déjà cette ressource localement
#    - Score: ÉLEVÉ car pas de coût
#    - Impact: Aucun coût, temps variable
#
# 2. COLONISATION
#    - Si le joueur NE PRODUIT PAS cette ressource
#    - Score: ÉLEVÉ si ressource avancée + manques récurrents
#    - Impact: Nouvelle ville avec accès à la ressource
#    - Coût: Élevé (ambassade + recherches + or)
#
# FONCTION PRINCIPALE: decide_resource_shortage_solution()
# Retourne la meilleure solution entre attendre ou coloniser.
#
# ============================================================


# ============================================================
# DÉTECTION & TRACKING DES MANQUES DE RESSOURCES
# ============================================================

def decide_resource_shortage_solution(player_id: str, cities: list, resource: str, amount_needed: int) -> Dict:
    """
    Système de décision simplifié pour résoudre un manque de ressource.
    
    Logique:
    - Si le joueur PRODUIT déjà la ressource → ATTENDRE
    - Si ressource de base MAIS joueur n'a aucune île avec cette ressource → COLONISER
    - Si ressource de base ET joueur a l'île mais ne produit pas → ATTENDRE (affecter workers)
    - Si ressource avancée → COLONISER
    
    Args:
        player_id: ID du joueur IA
        cities: Liste des villes du joueur
        resource: Ressource manquante
        amount_needed: Quantité nécessaire
    
    Returns:
        {
            'best_solution': str,  # 'wait' ou 'colonize'
            'score': float,        # Score de la solution choisie (0-100)
            'reason': str,         # Explication de la décision
            'produces_resource': bool,  # Le joueur produit-il déjà cette ressource?
        }
    """
    # Vérifier si le joueur produit déjà cette ressource
    produces_resource = _player_produces_resource(cities, resource)
    
    if produces_resource:
        # Le joueur produit déjà cette ressource → ATTENDRE
        return {
            'best_solution': 'wait',
            'score': 100.0,
            'reason': f"Attente production naturelle: {resource} déjà produite localement",
            'produces_resource': True
        }
    
    # Le joueur NE produit PAS cette ressource
    # Vérifier si c'est une ressource de base ou avancée
    base_resources = ['wood', 'stone', 'cereal', 'papyrus', 'iron']
    is_base = resource in base_resources
    
    if is_base:
        # Ressource de base mais non produite
        # Vérifier si le joueur a accès à une île avec cette ressource
        has_island_with_resource = _player_has_island_with_resource(cities, resource)
        
        if has_island_with_resource:
            # Le joueur a l'île mais ne produit pas → problème de workers
            return {
                'best_solution': 'wait',
                'score': 80.0,
                'reason': f"Attente: {resource} disponible sur vos îles (affecter des workers)",
                'produces_resource': False
            }
        else:
            # Le joueur n'a AUCUNE île avec cette ressource → COLONISER
            colonize_eval = _evaluate_colonization_solution(player_id, cities, resource, amount_needed)
            
            return {
                'best_solution': 'colonize',
                'score': colonize_eval['score'],
                'reason': f"Colonisation requise: aucune île avec {resource}",
                'produces_resource': False,
                'colonize_viable': colonize_eval['is_viable'],
                'requirements': colonize_eval.get('requirements_met', {})
            }
    else:
        # Ressource avancée → Évaluer COLONISATION
        colonize_eval = _evaluate_colonization_solution(player_id, cities, resource, amount_needed)
        
        return {
            'best_solution': 'colonize',
            'score': colonize_eval['score'],
            'reason': colonize_eval['reason'],
            'produces_resource': False,
            'colonize_viable': colonize_eval['is_viable'],
            'requirements': colonize_eval.get('requirements_met', {})
        }


def _player_produces_resource(cities: list, resource: str) -> bool:
    """
    Vérifie si le joueur produit RÉELLEMENT une ressource via ses villes actuelles.
    
    Critères:
    - Vérifier si des workers sont affectés au site correspondant
    
    Args:
        cities: Liste des villes du joueur
        resource: Ressource à vérifier
    
    Returns:
        bool: True si le joueur produit activement cette ressource
    """
    try:
        # Mapper les ressources aux types de workers
        resource_to_worker_type = {
            'wood': 'forest',
            'stone': 'quarry',
            'cereal': ['cereal', 'cereal_field'],  # Accepter les deux noms
            'papyrus': 'papyrus',
            'iron': ['iron_mine', 'iron'],
            'glass': 'advanced',
            'marble': 'advanced',
            'wine': 'advanced',
            'horse': 'advanced',
            'gunpowder': 'advanced',
            'coal': 'advanced',
            'spices': 'advanced',
            'cotton': 'advanced'
        }
        
        worker_types = resource_to_worker_type.get(resource)
        if not worker_types:
            return False
        
        # Convertir en liste si ce n'est pas déjà le cas
        if isinstance(worker_types, str):
            worker_types = [worker_types]
        
        # Vérifier si au moins une ville a des workers affectés
        for city in cities:
            workers_assigned = city.get('workers_assigned', {})
            
            for worker_type in worker_types:
                if workers_assigned.get(worker_type, 0) > 0:
                    return True
        
        return False
        
    except Exception as e:
        print(f"⚠️ Erreur vérification production ressource: {e}")
        return False


def _player_has_island_with_resource(cities: list, resource: str) -> bool:
    """
    Vérifie si le joueur possède au moins une ville sur une île qui a cette ressource.
    
    Args:
        cities: Liste des villes du joueur
        resource: Ressource à vérifier
    
    Returns:
        bool: True si le joueur a accès à cette ressource via ses îles
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        universe_path = os.path.join(base_dir, 'data', 'universe.json')
        
        with open(universe_path, 'r', encoding='utf-8') as f:
            universe = json.load(f)
        
        # Vérifier chaque ville du joueur
        for city in cities:
            island_id = city.get('island_id')
            
            # Trouver l'île correspondante
            island = next((isl for isl in universe.get('islands', []) if str(isl.get('id')) == str(island_id)), None)
            
            if not island:
                continue
            
            base_resource = island.get('base_resource')
            advanced_resource = island.get('advanced_resource')
            
            # Vérifier si cette île a la ressource
            if base_resource == resource or advanced_resource == resource:
                return True
        
        return False
        
    except Exception as e:
        print(f"⚠️ Erreur vérification île avec ressource: {e}")
        return False



def _evaluate_colonization_solution(player_id: str, cities: list, resource: str, amount_needed: int) -> Dict:
    """
    Évalue l'option "coloniser une nouvelle île".
    
    Score élevé si:
    - Ressource avancée OU ressource de base non disponible
    - Manques récurrents (>= 3 en 24h)
    - Joueur n'a pas déjà une ville avec cette ressource
    - Prérequis débloqués (ambassade, recherches)
    
    Returns:
        {'score': float, 'reason': str, 'is_viable': bool, 'requirements_met': dict}
    """
    # Vérifier si c'est une ressource avancée
    advanced_resources = ['glass', 'marble', 'wine', 'horse', 'gunpowder', 'coal', 'spices', 'cotton']
    is_advanced = resource in advanced_resources
    
    # Accepter colonisation pour ressources avancées OU ressources de base non disponibles
    # (Le cas des ressources de base est géré par decide_resource_shortage_solution)
    
    # Vérifier si le joueur a déjà une ville avec cette ressource
    has_resource_island = _player_has_island_with_resource(cities, resource)
    if has_resource_island:
        return {
            'score': 0.0,
            'reason': f"Colonisation inutile: ville avec {resource} déjà possédée",
            'is_viable': False,
            'requirements_met': {}
        }
    
    # Compter les manques récurrents
    shortage_count = _get_shortage_count(player_id, resource)
    
    if shortage_count < 2:
        return {
            'score': 20.0,  # Score bas mais pas 0
            'reason': f"Colonisation envisageable mais manques insuffisants ({shortage_count}/2)",
            'is_viable': False,
            'requirements_met': {'shortage_frequency': False}
        }
    
    # Si tous les critères sont remplis, score élevé
    score = 80.0  # Score très élevé pour colonisation si conditions OK
    
    return {
        'score': score,
        'reason': f"Colonisation recommandée: {shortage_count} manques de {resource}, ressource non disponible",
        'is_viable': True,
        'requirements_met': {
            'is_advanced_resource': True,
            'no_existing_island': True,
            'shortage_frequency': True
        }
    }


def track_resource_shortage(player_id: str, resource: str, amount: int) -> None:
    """
    Enregistre un manque de ressource dans recent_actions (plus besoin de bloc séparé).
    OBSOLÈTE - Gardé pour compatibilité mais ne fait plus rien.
    Les manques sont déjà trackés dans recent_actions par ai_controller.
    
    Args:
        player_id: ID du joueur IA
        resource: Type de ressource manquante (wood, stone, glass, etc.)
        amount: Quantité manquante
    """
    # Ne fait plus rien - les manques sont trackés dans recent_actions
    pass


def _get_shortage_count(player_id: str, resource: str) -> int:
    """
    Compte le nombre de manques récents d'une ressource depuis recent_actions.
    Analyse les actions récentes DANS LES VILLES pour voir combien de fois la ressource a manqué.
    
    Args:
        player_id: ID du joueur
        resource: Type de ressource
    
    Returns:
        Nombre de manques dans les actions récentes
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        state_path = os.path.join(base_dir, 'gamedata', 'ai_strategies_state.json')
        
        if not os.path.exists(state_path):
            return 0
        
        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        if player_id not in state:
            return 0
        
        # Analyser les recent_actions DE TOUTES LES VILLES
        player_state = state[player_id]
        cities_data = player_state.get('cities', {})
        
        # Compter combien de fois cette ressource apparaît dans les erreurs
        shortage_count = 0
        for city_id, city_data in cities_data.items():
            recent_actions = city_data.get('recent_actions', [])
            
            for action in recent_actions:
                reason = action.get('reason', '')
                # Chercher "Manquant: stone:" ou "manque de stone" dans le message
                if f'{resource}:' in reason.lower() or f'manque de {resource}' in reason.lower():
                    shortage_count += 1
        
        return shortage_count
        
    except Exception as e:
        print(f"⚠️ Erreur lecture shortage count: {e}")
        return 0


# ============================================================
# BESOIN POPULATION
# ============================================================



def analyze_population_needs(city: Dict, player_id: str, ai_player: Dict) -> Dict:
    """
    Détermine s'il faut développer l'hôtel de ville.
    
    Règle simple:
    - Si somme_capacités_sites < capacité_hotel_ville × 90% → attendre
    - Sinon → développer hôtel de ville
    
    La réserve de 10% permet de garder de la population libre pour les besoins militaires
    tout en évitant les upgrades trop fréquents.
    
    Returns:
        {
            'needs_upgrade': bool,
            'total_sites_capacity': int,
            'townhall_capacity': int,
            'townhall_reserve_capacity': int,  # 90% de la capacité
            'available_reserve': int,  # Espace restant dans la réserve
        }
    """
    # Capacité de l'hôtel de ville
    townhall_capacity = city.get('resources', {}).get('population_capacity', 0)
    townhall_reserve_capacity = int(townhall_capacity * 0.90)  # Garder 10% de réserve
    
    # Somme des capacités de tous les sites de production
    total_sites_capacity = 0
    total_sites_capacity += _get_academy_capacity(city)
    total_sites_capacity += _get_forest_capacity(city)
    total_sites_capacity += _get_resource_site_capacity(city, 'basic')
    total_sites_capacity += _get_resource_site_capacity(city, 'advanced')
    
    # Décision simple
    needs_upgrade = total_sites_capacity >= townhall_reserve_capacity
    available_reserve = max(0, townhall_reserve_capacity - total_sites_capacity)
    
    return {
        'needs_upgrade': needs_upgrade,
        'total_sites_capacity': total_sites_capacity,
        'townhall_capacity': townhall_capacity,
        'townhall_reserve_capacity': townhall_reserve_capacity,
        'available_reserve': available_reserve,
    }


def _get_academy_capacity(city: Dict) -> int:
    """Retourne la capacité de l'académie depuis buildings.json"""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        buildings_path = os.path.join(base_dir, 'data', 'buildings.json')
        
        with open(buildings_path, 'r', encoding='utf-8') as f:
            buildings_data = json.load(f)
        
        for building in city.get('buildings', []):
            if building.get('name') == 'Académie':
                level = building.get('level', 0)
                academy_levels = buildings_data.get('Academy', {}).get('levels', [])
                for level_data in academy_levels:
                    if level_data.get('level') == level:
                        return level_data.get('effect', {}).get('max_workers', 0)
        return 0
    except Exception:
        return 0


def _get_forest_capacity(city: Dict) -> int:
    """Retourne la capacité de la forêt depuis resource_sites.json"""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        sites_path = os.path.join(base_dir, 'data', 'resource_sites.json')
        
        with open(sites_path, 'r', encoding='utf-8') as f:
            resource_sites = json.load(f)
        
        island_id = city.get('island_id')
        if not island_id:
            return 0
        
        for site in resource_sites.get('sites', []):
            if str(site.get('island_id')) == str(island_id) and site.get('type') == 'forest':
                level = site.get('level', 0)
                return 10 * level  # Capacité = 10 × niveau
        return 0
    except Exception:
        return 0


def _get_resource_site_capacity(city: Dict, site_type: str) -> int:
    """
    Retourne la capacité d'un site de ressource (basic ou advanced).
    
    Args:
        city: Données de la ville
        site_type: 'basic' ou 'advanced'
    
    Returns:
        int: Capacité du site (10 × niveau)
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        sites_path = os.path.join(base_dir, 'data', 'resource_sites.json')
        
        with open(sites_path, 'r', encoding='utf-8') as f:
            resource_sites = json.load(f)
        
        island_id = city.get('island_id')
        if not island_id:
            return 0
        
        for site in resource_sites.get('sites', []):
            if str(site.get('island_id')) == str(island_id) and site.get('type') == site_type:
                level = site.get('level', 0)
                return 10 * level  # Capacité = 10 × niveau
        return 0
    except Exception:
        return 0

# ============================================================
# BESOIN POINTS DE RECHERCHE
# ============================================================

def analyze_research_production_needs(city: Dict, research_points_needed: int, gain_threshold: float = 0.20) -> Dict:
    """
    Détermine s'il faut upgrader l'académie pour accélérer la production de points de recherche.
    
    Logique proportionnelle:
    - Calcule le temps actuel pour générer les points
    - Calcule le temps après upgrade académie
    - Si gain >= seuil (20% par défaut) → upgrader
    - Sinon → attendre
    
    Args:
        city: Données de la ville
        research_points_needed: Nombre de points de recherche nécessaires
        gain_threshold: Seuil de gain minimal en pourcentage (0.20 = 20%)
    
    Returns:
        {
            'needs_upgrade': bool,
            'current_capacity': int,
            'next_capacity': int,
            'current_workers': int,
            'time_before_hours': float,
            'time_after_hours': float,
            'time_gain_percent': float,
            'has_population_available': bool
        }
    """
    # Workers actuellement affectés à l'académie
    current_workers = city.get('workers_assigned', {}).get('research', 0)
    
    # Capacité actuelle de l'académie
    current_capacity = _get_academy_capacity(city)
    
    # Capacité après upgrade (niveau N+1)
    next_capacity = _get_academy_next_level_capacity(city)
    
    # Si académie au niveau max ou pas de capacité supplémentaire
    if next_capacity <= current_capacity:
        return {
            'needs_upgrade': False,
            'current_capacity': current_capacity,
            'next_capacity': next_capacity,
            'current_workers': current_workers,
            'time_before_hours': 0,
            'time_after_hours': 0,
            'time_gain_percent': 0,
            'has_population_available': False,
            'reason': 'academy_max_level'
        }
    
    # Production actuelle (1 pt/h par worker)
    production_per_hour = current_workers * 1.0
    
    # Si pas de production, temps infini
    if production_per_hour == 0:
        time_before_hours = float('inf')
    else:
        time_before_hours = research_points_needed / production_per_hour
    
    # Production future (si on upgrade et qu'on remplit à 100%)
    future_workers = min(next_capacity, city.get('resources', {}).get('population_total', 0))
    production_future_per_hour = future_workers * 1.0
    
    if production_future_per_hour == 0:
        time_after_hours = float('inf')
    else:
        time_after_hours = research_points_needed / production_future_per_hour
    
    # Calcul du gain en pourcentage
    if time_before_hours == float('inf') or time_before_hours == 0:
        time_gain_percent = 0
    else:
        time_gain_percent = (time_before_hours - time_after_hours) / time_before_hours
    
    # Vérifier si on a assez de population disponible
    population_free = city.get('resources', {}).get('population_free', 0)
    additional_workers_needed = next_capacity - current_workers
    has_population_available = population_free >= additional_workers_needed
    
    # Décision
    needs_upgrade = time_gain_percent >= gain_threshold and has_population_available
    
    return {
        'needs_upgrade': needs_upgrade,
        'current_capacity': current_capacity,
        'next_capacity': next_capacity,
        'current_workers': current_workers,
        'time_before_hours': time_before_hours,
        'time_after_hours': time_after_hours,
        'time_gain_percent': time_gain_percent,
        'has_population_available': has_population_available,
        'reason': 'gain_sufficient' if needs_upgrade else 'gain_insufficient'
    }


def _get_academy_next_level_capacity(city: Dict) -> int:
    """Retourne la capacité de l'académie au niveau N+1"""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        buildings_path = os.path.join(base_dir, 'data', 'buildings.json')
        
        with open(buildings_path, 'r', encoding='utf-8') as f:
            buildings_data = json.load(f)
        
        for building in city.get('buildings', []):
            if building.get('name') == 'Académie':
                current_level = building.get('level', 0)
                next_level = current_level + 1
                
                academy_levels = buildings_data.get('Academy', {}).get('levels', [])
                for level_data in academy_levels:
                    if level_data.get('level') == next_level:
                        return level_data.get('effect', {}).get('max_workers', 0)
        return 0
    except Exception:
        return 0
