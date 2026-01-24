"""
ai_military_manager.py

GESTIONNAIRE DE L'ARMÉE IA

RESPONSABILITÉS:
- Calculer la puissance militaire cible selon le niveau de l'hôtel de ville
- Déterminer si l'IA doit recruter des unités
- Sélectionner les meilleures unités disponibles par catégorie
- Répartir le budget de puissance entre les catégories
- Mettre en file d'attente la production d'unités

FORMULE:
    puissance_cible = niveau_hdv × niveau_hdv
    
SEUIL DE RECRUTEMENT:
    80% de la puissance cible (évite les micro-ajustements)

ARCHITECTURE:
    Appelé conditionnellement dans le cycle IA si needs_military_production() = True
"""

import json
import os
from typing import Dict, List, Optional, Tuple


class AIMilitaryManager:
    """Gestionnaire de la stratégie militaire IA - Charge dynamiquement les unités depuis unit_stats.json"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.base_dir = data_manager.base_dir
        self.unit_stats = self._load_unit_stats()
    
    def _load_unit_stats(self) -> Dict:
        """Charge les statistiques des unités depuis unit_stats.json"""
        try:
            unit_stats_path = os.path.join(self.base_dir, 'data', 'unit_stats.json')
            with open(unit_stats_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erreur chargement unit_stats.json: {e}")
            return {"classical_age": {}}
    
    def _get_units_by_category(self, category: str) -> List[Dict[str, any]]:
        """
        Récupère toutes les unités d'une catégorie, triées par xp_value (meilleure en premier).
        
        Args:
            category: Catégorie d'unité (infantry, ranged, cavalry, artillery, siege)
        
        Returns:
            Liste d'unités triées par xp_value décroissant
        """
        units = []
        
        for unit_id, unit_data in self.unit_stats.get('classical_age', {}).items():
            if isinstance(unit_data, dict) and unit_data.get('category') == category:
                units.append({
                    'id': unit_id,
                    'xp_value': unit_data.get('xp_value', 0),
                    'required_barracks_level': unit_data.get('required_barracks_level', 1),
                    'required_research': unit_data.get('required_research'),
                    'data': unit_data
                })
        
        # Trier par xp_value décroissant (meilleure unité en premier)
        units.sort(key=lambda x: x['xp_value'], reverse=True)
        
        return units
    
    def calculate_target_power(self, player_id: str, savegame_data: Dict = None, strategy_multiplier: float = 1.0) -> int:
        """
        Calcule la puissance militaire cible pour un joueur (basé sur sa ville principale).
        
        Formule: niveau_hdv × niveau_hdv × multiplicateur_stratégie
        
        Args:
            player_id: ID du joueur
            savegame_data: Données du savegame (optionnel)
            strategy_multiplier: Multiplicateur (1.0 = normal, 2.0 = préparation offensive)
        
        Returns:
            Puissance cible en points
        """
        if savegame_data is None:
            savegame_data = self.data_manager.load_savegame()
        
        # Trouver la ville principale du joueur
        cities = [c for c in savegame_data.get('cities', []) if c.get('owner') == player_id]
        if not cities:
            return 0
        
        city = cities[0]  # Ville principale
        
        # Trouver le niveau de l'hôtel de ville
        townhall_level = 1
        for building in city.get('buildings', []):
            if building.get('name') == "Hôtel de Ville":
                townhall_level = building.get('level', 1)
                break
        
        # Formule : niveau²
        base_power = townhall_level * townhall_level
        
        # Appliquer le multiplicateur stratégique
        target_power = int(base_power * strategy_multiplier)
        
        return target_power
    
    def calculate_current_power(self, player_id: str, savegame_data: Dict = None) -> int:
        """
        Calcule la puissance militaire actuelle d'un joueur.
        Formule: sum(quantity × xp_value) / 100
        
        Args:
            player_id: ID du joueur
            savegame_data: Données du savegame (optionnel)
        
        Returns:
            Puissance actuelle en points
        """
        if savegame_data is None:
            savegame_data = self.data_manager.load_savegame()
        
        try:
            cities = savegame_data.get('cities', [])
            
            total_power_raw = 0
            
            for city in cities:
                military = city.get('military', {})
                garrison = military.get('garrison', {})
                player_garrison = garrison.get(player_id, {})
                
                for unit_type, unit_data in player_garrison.items():
                    quantity = unit_data.get('quantity', 0)
                    
                    # Chercher xp_value dans unit_stats
                    xp_value = 0
                    for category in self.unit_stats.get('classical_age', {}).values():
                        if isinstance(category, dict) and 'xp_value' in category:
                            # C'est une unité directe
                            if unit_type in self.unit_stats.get('classical_age', {}):
                                xp_value = self.unit_stats['classical_age'][unit_type].get('xp_value', 0)
                                break
                    
                    total_power_raw += quantity * xp_value
            
            # Diviser par 100 selon la formule
            return int(total_power_raw / 100)
            
        except Exception as e:
            print(f"❌ Erreur calcul puissance militaire: {e}")
            return 0
    
    def needs_military_production(self, player_id: str, savegame_data: Dict = None, strategy_multiplier: float = 1.0) -> bool:
        """
        Détermine si l'IA doit recruter des unités.
        
        Seuil: 80% de la puissance cible
        
        Args:
            player_id: ID du joueur
            savegame_data: Données du savegame (optionnel)
            strategy_multiplier: Multiplicateur stratégique
        
        Returns:
            True si recrutement nécessaire, False sinon
        """
        if savegame_data is None:
            savegame_data = self.data_manager.load_savegame()
        
        current_power = self.calculate_current_power(player_id, savegame_data)
        target_power = self.calculate_target_power(player_id, savegame_data, strategy_multiplier)
        
        # Seuil de 80%
        threshold = target_power * 0.8
        
        return current_power < threshold
    
    def get_best_unit_available(self, category: str, barracks_level: int, researches: List[str]) -> Optional[str]:
        """
        Trouve la meilleure unité disponible pour une catégorie.
        
        Args:
            category: Catégorie d'unité (infantry, ranged, cavalry, artillery, siege)
            barracks_level: Niveau des casernes
            researches: Recherches débloquées du joueur
        
        Returns:
            ID de l'unité ou None si aucune disponible
        """
        # Récupérer toutes les unités de la catégorie, triées par xp_value
        units = self._get_units_by_category(category)
        
        # Parcourir par ordre de priorité (xp_value décroissant)
        for unit in units:
            # Vérifier le niveau de caserne requis
            if barracks_level < unit['required_barracks_level']:
                continue
            
            # Vérifier la recherche requise
            required_research = unit['required_research']
            if required_research and required_research not in researches:
                continue
            
            # Unité disponible !
            return unit['id']
        
        return None
    
    def determine_army_composition(self, player_id: str, city_id: str, savegame_data: Dict = None) -> Dict[str, Optional[str]]:
        """
        Détermine les meilleures unités disponibles pour chaque catégorie.
        
        Args:
            player_id: ID du joueur
            city_id: ID de la ville
            savegame_data: Données du savegame (optionnel)
        
        Returns:
            Dict avec les types d'unités par catégorie
        """
        if savegame_data is None:
            savegame_data = self.data_manager.load_savegame()
        
        # Trouver la ville
        city = next((c for c in savegame_data.get('cities', []) if c.get('id') == city_id), None)
        if not city:
            return {}
        
        # Récupérer le niveau de la caserne
        barracks_level = 0
        for building in city.get('buildings', []):
            if 'caserne' in building.get('name', '').lower():
                barracks_level = building.get('level', 0)
                break
        
        # Récupérer les recherches du joueur
        players_data = self.data_manager.load_players()
        player = next((p for p in players_data.get('players', []) if p.get('id') == player_id), None)
        researches = player.get('researches', []) if player else []
        
        composition = {
            'infantry': self.get_best_unit_available('infantry', barracks_level, researches),
            'ranged': self.get_best_unit_available('ranged', barracks_level, researches),
            'cavalry': self.get_best_unit_available('cavalry', barracks_level, researches),
            'artillery': self.get_best_unit_available('artillery', barracks_level, researches),
            'siege': self.get_best_unit_available('siege', barracks_level, researches)
        }
        
        return composition
    
    def calculate_budget_distribution(self, player_id: str, city_id: str, savegame_data: Dict = None) -> Dict[str, float]:
        """
        Calcule la répartition du budget selon les unités disponibles.
        
        Args:
            player_id: ID du joueur
            city_id: ID de la ville
            savegame_data: Données du savegame (optionnel)
        
        Returns:
            Pourcentages de répartition par catégorie
        """
        composition = self.determine_army_composition(player_id, city_id, savegame_data)
        
        # Compter les catégories disponibles
        has_infantry = composition.get('infantry') is not None
        has_ranged = composition.get('ranged') is not None
        has_cavalry = composition.get('cavalry') is not None
        has_artillery = composition.get('artillery') is not None
        has_siege = composition.get('siege') is not None
        
        budget = {}
        
        if has_cavalry and (has_artillery or has_siege):
            # Tout disponible (fin de partie)
            budget = {
                'infantry': 0.45,
                'ranged': 0.25,
                'cavalry': 0.15,
                'artillery': 0.10 if has_artillery else 0.0,
                'siege': 0.05 if has_siege else 0.0
            }
        elif has_cavalry:
            # Cavalerie débloquée mais pas artillerie
            budget = {
                'infantry': 0.50,
                'ranged': 0.30,
                'cavalry': 0.20,
                'artillery': 0.0,
                'siege': 0.0
            }
        else:
            # Début de partie (que infanterie et archers)
            budget = {
                'infantry': 0.60 if has_infantry else 0.0,
                'ranged': 0.40 if has_ranged else 0.0,
                'cavalry': 0.0,
                'artillery': 0.0,
                'siege': 0.0
            }
            
            # Si pas d'archers, tout en infanterie
            if not has_ranged and has_infantry:
                budget['infantry'] = 1.0
        
        return budget
    
    def calculate_production_plan(self, player_id: str, city_id: str, savegame_data: Dict = None) -> Dict:
        """
        Calcule le plan de production d'unités pour atteindre la puissance cible.
        
        Args:
            player_id: ID du joueur
            city_id: ID de la ville
            savegame_data: Données du savegame (optionnel)
        
        Returns:
            Dict avec le plan de production et les unités suggérées
        """
        if savegame_data is None:
            savegame_data = self.data_manager.load_savegame()
        
        # Trouver la ville
        city = next((c for c in savegame_data.get('cities', []) if c.get('id') == city_id), None)
        if not city:
            return {'units': [], 'summary': 'Ville introuvable'}
        
        # 1. Vérifier si production nécessaire
        if not self.needs_military_production(player_id, savegame_data):
            return {'units': [], 'summary': 'Armée suffisante'}
        
        # 2. Calculer l'écart à combler
        current_power = self.calculate_current_power(player_id, savegame_data)
        target_power = self.calculate_target_power(player_id, savegame_data)
        power_gap = target_power - current_power
        
        if power_gap <= 0:
            return {'units': [], 'summary': 'Puissance atteinte'}
        
        # 3. Déterminer la composition optimale
        composition = self.determine_army_composition(player_id, city_id, savegame_data)
        budget = self.calculate_budget_distribution(player_id, city_id, savegame_data)
        
        # 4. Convertir en quantités d'unités
        units = []
        summary_parts = []
        
        for category, percentage in budget.items():
            if percentage == 0:
                continue
            
            unit_type = composition.get(category)
            if not unit_type:
                continue
            
            # Calculer la puissance allouée à cette catégorie
            power_for_category = power_gap * percentage
            
            # Récupérer xp_value
            unit_data = self.unit_stats.get('classical_age', {}).get(unit_type, {})
            xp_value = unit_data.get('xp_value', 1)
            
            # Calculer la quantité nécessaire
            # power = (quantity × xp_value) / 100
            # donc quantity = (power × 100) / xp_value
            quantity = max(1, int((power_for_category * 100) / xp_value))
            
            units.append({
                'unit_type': unit_type,
                'quantity': quantity,
                'category': category
            })
            
            summary_parts.append(f"{quantity}x {unit_type}")
        
        return {
            'units': units,
            'summary': ', '.join(summary_parts) if summary_parts else 'Aucune unité',
            'current_power': current_power,
            'target_power': target_power,
            'power_gap': power_gap
        }
    
    def execute_military_production(self, player_id: str, city_id: str, production_plan: Dict, savegame_data: Dict = None) -> Dict:
        """
        Exécute la production militaire IA pour une ville en utilisant le même système que le joueur.
        
        Args:
            player_id: ID du joueur
            city_id: ID de la ville
            production_plan: Plan de production généré
            savegame_data: Données du savegame (optionnel)
        
        Returns:
            Résultat de l'opération
        """
        try:
            units = production_plan.get('units', [])
            
            if not units:
                return {
                    'player_id': player_id,
                    'player_name': self._get_player_name(player_id),
                    'action': 'military_skip',
                    'message': '✓ Armée suffisante',
                    'success': False
                }
            
            if savegame_data is None:
                savegame_data = self.data_manager.load_savegame()
            
            # Trouver la ville
            city = next((c for c in savegame_data.get('cities', []) if c.get('id') == city_id), None)
            if not city:
                return {
                    'player_id': player_id,
                    'player_name': self._get_player_name(player_id),
                    'action': 'military_error',
                    'message': '❌ Ville introuvable',
                    'success': False
                }
            
            # 1. VÉRIFIER LE NIVEAU DE CASERNE
            barracks_level = 0
            for building in city.get('buildings', []):
                if building.get('name') == 'Caserne':
                    barracks_level = building.get('level', 0)
                    break
            
            if barracks_level == 0:
                return {
                    'player_id': player_id,
                    'player_name': self._get_player_name(player_id),
                    'action': 'military_no_barracks',
                    'message': '❌ Caserne non construite',
                    'success': False
                }
            
            # 2. VÉRIFIER LES PRÉREQUIS POUR CHAQUE UNITÉ
            players_data = self.data_manager.load_players()
            player = next((p for p in players_data.get('players', []) if p.get('id') == player_id), None)
            player_researches = player.get('unlocked_research', []) if player else []
            
            producible_units = []
            blocked_units = []
            
            for unit_plan in units:
                unit_type = unit_plan['unit_type']
                quantity = unit_plan['quantity']
                
                # Récupérer les stats de l'unité
                unit_data = self.unit_stats.get('classical_age', {}).get(unit_type, {})
                if not unit_data:
                    blocked_units.append(f"{unit_type} (stats manquantes)")
                    continue
                
                # Vérifier niveau caserne requis
                required_barracks = unit_data.get('required_barracks_level', 1)
                if barracks_level < required_barracks:
                    blocked_units.append(f"{unit_type} (Caserne niv.{required_barracks} requis)")
                    continue
                
                # Vérifier recherche requise
                required_research = unit_data.get('required_research')
                if required_research and required_research not in player_researches:
                    blocked_units.append(f"{unit_type} (recherche {required_research} manquante)")
                    continue
                
                producible_units.append(unit_plan)
            
            if not producible_units:
                reason = ', '.join(blocked_units[:2])  # Montrer max 2 raisons
                return {
                    'player_id': player_id,
                    'player_name': self._get_player_name(player_id),
                    'action': 'military_blocked',
                    'message': f'⚠️ Bloqué: {reason}',
                    'success': False
                }
            
            # 3. CALCULER LES COÛTS TOTAUX (avec réduction selon niveau caserne)
            cost_reduction = min(0.45, (barracks_level - 1) * 0.05)
            total_cost = {}
            
            for unit_plan in producible_units:
                unit_type = unit_plan['unit_type']
                quantity = unit_plan['quantity']
                unit_data = self.unit_stats.get('classical_age', {}).get(unit_type, {})
                production_cost = unit_data.get('production_cost', {})
                
                for resource, cost in production_cost.items():
                    if cost > 0:
                        if resource == 'population':
                            # Population sans réduction
                            total_cost[resource] = total_cost.get(resource, 0) + (cost * quantity)
                        else:
                            # Autres ressources avec réduction
                            total_cost[resource] = total_cost.get(resource, 0) + int(cost * (1 - cost_reduction) * quantity)
            
            # 4. AJUSTER LES QUANTITÉS SELON LES RESSOURCES DISPONIBLES
            city_resources = city.get('resources', {})
            
            # Calculer le ratio de ressources disponibles
            min_ratio = 1.0
            for resource, cost in total_cost.items():
                if cost > 0:
                    if resource == 'population':
                        available = city_resources.get('population_free', 0)
                    else:
                        available = city_resources.get(resource, 0)
                    
                    resource_ratio = available / cost if cost > 0 else 1.0
                    min_ratio = min(min_ratio, resource_ratio)
            
            # Si on n'a pas assez de ressources, ajuster les quantités proportionnellement
            if min_ratio < 1.0:
                if min_ratio < 0.2:  # Moins de 20% des ressources → abandonner
                    missing_str = ', '.join([f"{res}: {int(total_cost[res] - city_resources.get(res, 0))}" 
                                            for res in list(total_cost.keys())[:2]])
                    return {
                        'player_id': player_id,
                        'player_name': self._get_player_name(player_id),
                        'action': 'military_no_resources',
                        'message': f'⚠️ Manque: {missing_str}',
                        'success': False
                    }
                
                # Ajuster les quantités (produire ce qu'on peut)
                adjusted_units = []
                for unit_plan in producible_units:
                    adjusted_qty = max(1, int(unit_plan['quantity'] * min_ratio))
                    adjusted_units.append({
                        'unit_type': unit_plan['unit_type'],
                        'quantity': adjusted_qty,
                        'category': unit_plan['category']
                    })
                producible_units = adjusted_units
                
                # Recalculer les coûts avec les quantités ajustées
                total_cost = {}
                for unit_plan in producible_units:
                    unit_type = unit_plan['unit_type']
                    quantity = unit_plan['quantity']
                    unit_data = self.unit_stats.get('classical_age', {}).get(unit_type, {})
                    production_cost = unit_data.get('production_cost', {})
                    
                    for resource, cost in production_cost.items():
                        if cost > 0:
                            if resource == 'population':
                                total_cost[resource] = total_cost.get(resource, 0) + (cost * quantity)
                            else:
                                total_cost[resource] = total_cost.get(resource, 0) + int(cost * (1 - cost_reduction) * quantity)
            
            # 5. DÉDUIRE LES RESSOURCES ET AJOUTER À LA QUEUE
            for resource, cost in total_cost.items():
                if resource == 'population':
                    current_total = city_resources.get('population_total', 0)
                    if isinstance(current_total, dict):
                        current_total = current_total.get('total', 0)
                    city_resources['population_total'] = current_total - cost
                else:
                    city_resources[resource] = city_resources.get(resource, 0) - cost
            
            # Calculer le temps de production
            time_reduction = min(0.55, (barracks_level - 1) * 0.05)
            
            # Bonus faction Fer : -10% temps
            if player and player.get('faction') == 'iron':
                time_reduction += 0.10
                time_reduction = min(0.75, time_reduction)
            
            import time
            current_time = int(time.time())
            
            # Calculer le temps total (somme de toutes les productions)
            total_time = 0
            for unit_plan in producible_units:
                unit_type = unit_plan['unit_type']
                quantity = unit_plan['quantity']
                unit_data = self.unit_stats.get('classical_age', {}).get(unit_type, {})
                base_time = unit_data.get('production_time', 60)
                total_time += int(base_time * (1 - time_reduction) * quantity)
            
            completion_time = current_time + total_time
            
            # Créer l'item de production (batch)
            if 'military' not in city:
                city['military'] = {}
            if 'production_queue' not in city['military']:
                city['military']['production_queue'] = []
            
            production_item = {
                'is_batch': True,
                'units': [{'type': u['unit_type'], 'quantity': u['quantity']} for u in producible_units],
                'start_time': current_time,
                'completion_time': completion_time,
                'total_time': total_time
            }
            
            city['military']['production_queue'].append(production_item)
            
            # Sauvegarder
            self.data_manager.save_savegame(savegame_data, force_save=True)
            
            units_summary = production_plan.get('summary', 'Unités diverses')
            
            return {
                'player_id': player_id,
                'player_name': self._get_player_name(player_id),
                'action': 'military_production',
                'message': f'🏹 Production: {units_summary} ({total_time}s)',
                'success': True,
                'units_summary': units_summary,
                'production_time': total_time
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'player_id': player_id,
                'player_name': self._get_player_name(player_id),
                'action': 'military_error',
                'message': f'❌ Erreur: {str(e)}',
                'success': False
            }
    
    def _get_player_name(self, player_id: str) -> str:
        """Récupère le nom d'un joueur"""
        try:
            players_data = self.data_manager.load_players()
            player = next((p for p in players_data.get('players', []) if p.get('id') == player_id), None)
            return player.get('username', 'Unknown') if player else 'Unknown'
        except:
            return 'Unknown'
