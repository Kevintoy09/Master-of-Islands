"""
Battle Victory Manager
======================

Gestionnaire unifié pour les 3 conditions de victoire :
1. Élimination complète des unités adverses 🔪
2. Effondrement du moral (moral = 0) 💔
3. Abandon d'une équipe 🏳️

Chaque type de victoire a des conséquences différentes sur le butin et les troupes.
"""

import json
import math
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from app.services.quest_service import QuestService


class BattleVictoryManager:
    """
    🎯 Gestionnaire unifié des conditions de victoire/défaite
    
    3 types de victoire avec conséquences différentes :
    1. Élimination : 100% des troupes restantes capturées
    2. Moral : 75% des troupes restantes capturées  
    3. Abandon : 50% des troupes restantes capturées + confirmation
    """
    
    def __init__(self):
        # Chemin absolu vers le dossier gamedata
        # __file__ = .../server/app/battle/battle_victory_manager.py
        # Nous voulons aller jusqu'à .../server/gamedata/
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.gamedata_dir = os.path.join(base_dir, 'gamedata')  # Données dynamiques
        self.config_dir = os.path.join(base_dir, 'data')  # Configs statiques
        self.data_dir = self.gamedata_dir  # Alias pour compatibilité
        self.notifications_file = os.path.join(self.gamedata_dir, 'battle_notifications.json')
    
    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Charge un fichier JSON du dossier gamedata (données dynamiques)"""
        filepath = os.path.join(self.gamedata_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _load_config(self, filename: str) -> Dict[str, Any]:
        """Charge un fichier JSON du dossier data (configurations statiques)"""
        filepath = os.path.join(self.config_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_json(self, filename: str, data: Dict[str, Any]) -> bool:
        """Sauvegarde un fichier JSON dans le dossier data"""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            return False
    
    # =========================================================================
    # 🔪 CONDITION 1: ÉLIMINATION COMPLÈTE
    # =========================================================================
    
    def check_elimination_victory(self, battle_id: str) -> Tuple[bool, str, str]:
        """Vérifie si toutes les unités d'une équipe ont été éliminées"""
        try:
            battles_data = self._load_json('battlesv2.json')
            battlefields_data = self._load_json('battlefields_v2.json')
            
            if battle_id not in battles_data or battle_id not in battlefields_data:
                return (False, '', 'elimination')

            battle = battles_data[battle_id]
            teams = battle.get('teams', {})
            battle_status = battle.get('battle_status', 'deployment')
            current_round = battle.get('current_round', 1)
            
            battlefield = battlefields_data[battle_id]
            participants = battlefield.get('participants', {})
            attackers = participants.get('attackers', [])
            defenders = participants.get('defenders', [])
            
            # Villages barbares : pas de check avant Round 2 (déploiement différent)
            if 'wild_camp' in defenders and (battle_status == 'deployment' or current_round < 2):
                return (False, '', 'elimination')

            # 3. Compter les unités vivantes pour chaque équipe selon les participants réels
            attacker_units = 0
            defender_units = 0
            
            for team_name, team_units in teams.items():
                if not isinstance(team_units, list):
                    continue
                    
                unit_count = 0
                for unit in team_units:
                    if isinstance(unit, dict):
                        # Vérifier si l'unité est vivante
                        unit_count_value = unit.get('unitCount', 0)
                        hp = unit.get('hp')
                        
                        # Unité vivante si elle a des soldats OU des HP (pour les héros)
                        if unit_count_value > 0 or (hp is not None and hp > 0):
                            unit_count += 1
                
                # Associer le nombre d'unités à l'équipe selon les participants réels
                # team_name dans battlesv2.json est l'ID du joueur (ex: "player_1")
                if team_name in attackers:
                    attacker_units += unit_count
                elif team_name in defenders:
                    defender_units += unit_count
            
            # Vérifier les conditions d'élimination
            if attacker_units == 0 and defender_units > 0:
                return (True, 'defenders', 'elimination')
            elif defender_units == 0 and attacker_units > 0:
                return (True, 'attackers', 'elimination')
            elif attacker_units == 0 and defender_units == 0:
                return (True, 'draw', 'elimination')
            
            return (False, '', 'elimination')
            
        except Exception as e:
            return (False, '', 'elimination')
    
    def check_moral_victory(self, battle_id: str) -> Tuple[bool, str, str]:
        """Vérifie si le moral d'une équipe est tombé à 0"""
        
        try:
            battlefields_data = self._load_json('battlefields_v2.json')
            
            if battle_id not in battlefields_data:
                return (False, '', 'moral_breakdown')
            
            battlefield = battlefields_data[battle_id]
            forces = battlefield.get('forces', {})
            
            # Vérifier le moral des attaquants
            for player_id, player_data in forces.get('attackers', {}).items():
                if player_data.get('moral', 100) <= 0:
                    return (True, 'defenders', 'moral_breakdown')
            
            # Vérifier le moral des défenseurs
            for player_id, player_data in forces.get('defenders', {}).items():
                if player_data.get('moral', 100) <= 0:
                    return (True, 'attackers', 'moral_breakdown')
            
            return (False, '', 'moral_breakdown')
            
        except Exception as e:
            return (False, '', 'moral_breakdown')
    
    # =========================================================================
    # 🏳️ CONDITION 3: ABANDON D'UNE ÉQUIPE
    # =========================================================================
    
    def surrender_battle(self, battle_id: str, surrendering_player: str) -> Dict[str, Any]:
        """Gère l'abandon d'un joueur et termine la bataille"""
        try:
            battlefields_data = self._load_json('battlefields_v2.json')
            
            if battle_id not in battlefields_data:
                return {'success': False, 'error': f'Bataille {battle_id} non trouvée'}
            
            battlefield = battlefields_data[battle_id]
            participants = battlefield.get('participants', {})
            attackers = participants.get('attackers', [])
            defenders = participants.get('defenders', [])
            
            if surrendering_player in attackers:
                surrendering_team = 'attackers'
                winning_team = 'defenders'
            elif surrendering_player in defenders:
                surrendering_team = 'defenders'
                winning_team = 'attackers'
            else:
                return {'success': False, 'error': f'Joueur {surrendering_player} non trouvé'}
            
            # Calculer et stocker les détails de reddition
            surrender_details = self._calculate_surrender_details(battlefield, surrendering_team, surrendering_player)
            battlefield['surrender_info'] = surrender_details
            battlefield['status'] = 'completed'
            battlefield['completed_at'] = time.time()
            
            # Actions post-victoire
            self._credit_victory_units_to_winner(battlefield, surrendering_team, winning_team)
            self._prepare_proportional_resource_distribution(battlefield, surrendering_team, winning_team)
            
            # Sauvegarder le résultat de bataille (inclut l'incrément de village barbare)
            self.save_battle_result(battle_id, winning_team, 'surrender')
            
            self._mark_battle_as_finished_in_battles(battle_id, winning_team, 'surrender')
            
            # Sauvegarde directe pour préserver le pillage
            import os
            import json
            battlefield_path = os.path.join(self.gamedata_dir, 'battlefields_v2.json')
            
            with open(battlefield_path, 'r', encoding='utf-8') as f:
                fresh_battlefields = json.load(f)
            
            if battle_id in fresh_battlefields:
                fresh_battlefields[battle_id]['surrender_info'] = battlefield['surrender_info']
                fresh_battlefields[battle_id]['status'] = battlefield['status']
                fresh_battlefields[battle_id]['completed_at'] = battlefield['completed_at']
                
                with open(battlefield_path, 'w', encoding='utf-8') as f:
                    json.dump(fresh_battlefields, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'victory_type': 'surrender',
                'winner_team': winning_team,
                'surrendering_player': surrendering_player,
                'message': f'{surrendering_player} s\'est rendu. Bataille terminée !'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _calculate_surrender_details(self, battlefield: dict, surrendering_team: str, surrendering_player: str) -> dict:
        """Calcule les détails de reddition : unités capturées/retournantes et pillage"""
        forces = battlefield.get('forces', {})
        surrendering_forces = forces.get(surrendering_team, {})
        player_data = surrendering_forces.get(surrendering_player, {})
        
        # Calculer unités initiales depuis contributions
        initial_units = {}
        contributions = player_data.get('contributions', [])
        for contrib in contributions:
            units = contrib.get('units', {})
            for unit_type, count in units.items():
                initial_units[unit_type] = initial_units.get(unit_type, 0) + count
        
        # Calculer unités perdues (gérer préfixes comme "3_infantry_heavy")
        lost_units = {}
        units_lost = player_data.get('units_lost', {})
        for unit_type in initial_units.keys():
            lost_count = 0
            for lost_key, lost_value in units_lost.items():
                if lost_key == unit_type or lost_key.endswith(f'_{unit_type}'):
                    lost_count += lost_value
            if lost_count > 0:
                lost_units[unit_type] = lost_count
        
        # Calculer unités survivantes
        surviving_units = {}
        for unit_type, initial_count in initial_units.items():
            lost_count = lost_units.get(unit_type, 0)
            surviving_count = initial_count - lost_count
            if surviving_count > 0:
                surviving_units[unit_type] = surviving_count
        
        # Calculer répartition 50/50
        captured_units = {}
        returning_units = {}
        for unit_type, surviving_count in surviving_units.items():
            captured = math.floor(surviving_count / 2)
            returning = surviving_count - captured
            if captured > 0:
                captured_units[unit_type] = captured
            if returning > 0:
                returning_units[unit_type] = returning
        
        # Répartition par joueur (pour les gagnants)
        participants = battlefield.get('participants', {})
        winning_players = participants.get('attackers' if surrendering_team == 'defenders' else 'defenders', [])
        
        unit_distribution = {}
        for winner_player in winning_players:
            unit_distribution[winner_player] = {}
            for unit_type, captured_count in captured_units.items():
                # Répartition équitable entre tous les gagnants
                per_player = math.floor(captured_count / len(winning_players))
                if per_player > 0:
                    unit_distribution[winner_player][unit_type] = per_player
        
        # 🎯 MESSAGE DÉTAILLÉ DE REDDITION
        message_parts = [
            f"🏳️ {surrendering_player} s'est rendu !",
            "",
            "📊 RÉSUMÉ DES TROUPES :",
        ]
        
        for unit_type, count in surviving_units.items():
            captured = captured_units.get(unit_type, 0)
            returning = returning_units.get(unit_type, 0)
            message_parts.append(f"• {unit_type}: {count} survivants → {captured} capturées, {returning} retournent")
        
        if unit_distribution:
            message_parts.append("")
            message_parts.append("🎁 RÉPARTITION ENTRE VAINQUEURS :")
            for player, units in unit_distribution.items():
                if units:
                    units_text = ", ".join([f"{count} {unit_type}" for unit_type, count in units.items()])
                    message_parts.append(f"• {player}: {units_text}")
        
        # Calcul du pillage par joueur
        pillage_distribution = {}
        

        
        # Récupérer le pillage total depuis les contributions (exclure les récompenses barbares)
        battles_data = self._load_json('battlesv2.json')
        battle_id = battlefield.get('id')
        location = battles_data.get(battle_id, {}).get('location', '') if battle_id else ''
        is_wild_camp = location.startswith('wild_camp_')
        
        total_pillage = {}
        
        if 'attackers' in forces and not is_wild_camp:
            for attacker_id, attacker_data in forces['attackers'].items():
                contributions = attacker_data.get('contributions', [])
                for contrib in contributions:
                    pillage = contrib.get('pillage', {})
                    for resource, amount in pillage.items():
                        total_pillage[resource] = total_pillage.get(resource, 0) + amount
        
        # Répartir le pillage proportionnellement
        if winning_players and any(total_pillage.values()):
            player_contributions = {}
            total_contributions = 0
            
            for winner_player in winning_players:
                winner_data = forces.get('attackers' if surrendering_team == 'defenders' else 'defenders', {}).get(winner_player, {})
                contributions = winner_data.get('contributions', [])
                transport_ships = sum(contrib.get('transport_ships', 0) for contrib in contributions)
                player_contributions[winner_player] = max(1, transport_ships)
                total_contributions += player_contributions[winner_player]
            
            for winner_player in winning_players:
                proportion = player_contributions[winner_player] / total_contributions
                pillage_distribution[winner_player] = {}
                for resource, total_amount in total_pillage.items():
                    if total_amount > 0:
                        pillage_distribution[winner_player][resource] = math.floor(total_amount * proportion)
        
        # Ajouter le pillage au message détaillé
        if pillage_distribution and any(any(resources.values()) for resources in pillage_distribution.values()):
            message_parts.append("")
            message_parts.append("💰 PILLAGE RÉPARTI :")
            for player, resources in pillage_distribution.items():
                if any(resources.values()):
                    resource_texts = []
                    for resource, amount in resources.items():
                        if amount > 0:
                            resource_texts.append(f"{amount} {resource}")
                    if resource_texts:
                        message_parts.append(f"• {player}: {', '.join(resource_texts)}")
        
        detailed_message = "\n".join(message_parts)
        
        return {
            'surrendering_team': surrendering_team,
            'surrendering_player': surrendering_player,
            'initial_units': initial_units,
            'lost_units': lost_units,
            'surviving_units': surviving_units,
            'captured_units': captured_units,
            'returning_units': returning_units,
            'unit_distribution': unit_distribution,
            'winning_players': winning_players,
            'pillage_distribution': pillage_distribution,
            'detailed_message': detailed_message,
            'calculated_at': time.time()
        }
            
    def _credit_victory_units_to_winner(self, battlefield: dict, surrendering_team: str, winning_team: str) -> dict:
        """
        Créditer 50% des unités survivantes du camp perdant au camp gagnant dans le champ de bataille.
        - Ne touche pas aux héros.
        - Modifie le dict battlefield en place et le retourne.
        Args:
            battlefield: dict du champ de bataille (battlefields_v2.json)
            surrendering_team: 'attackers' ou 'defenders' 
            winning_team: 'attackers' ou 'defenders'
        Returns:
            battlefield modifié
        """
        
        # Récupérer les joueurs
        losing_players = battlefield['participants'][surrendering_team]
        winning_players = battlefield['participants'][winning_team] 
        forces = battlefield['forces']
        
        # Pour chaque joueur perdant
        for player_id in losing_players:
            player_forces = forces[surrendering_team][player_id]
            contributions = player_forces.get('contributions', [])
            units_lost = player_forces.get('units_lost', {})
            
            if not contributions:
                continue
                
            # Traiter chaque contribution (normalement il n'y en a qu'une)
            for contribution in contributions:
                units = contribution.get('units', {})
                
                # Consolider les units_lost en tenant compte des préfixes (comme côté client)
                consolidated_lost = self._consolidate_units_lost(units_lost, player_id)
                
                # Calculer les survivants réels (contributions - units_lost consolidées)
                survivors = {}
                for unit_type, total_contrib in units.items():
                    lost = consolidated_lost.get(unit_type, 0)
                    alive = max(0, total_contrib - lost)
                    survivors[unit_type] = alive
                
                # Calculer 50% avec la même logique que le client (arrondi inférieur pour capturer)
                for unit_type, alive_count in survivors.items():
                    if alive_count > 0:
                        gained_by_winner = math.floor(alive_count / 2)  # Même logique que le client
                        remaining_for_loser = alive_count - gained_by_winner
                        
                        
                        # 1. Mettre à jour les contributions du perdant
                        # Nouvelles contributions = contributions_originales - unités_transférées
                        lost = units_lost.get(unit_type, 0)
                        original_contrib = contribution['units'].get(unit_type, 0)
                        new_contrib_loser = original_contrib - gained_by_winner
                        contribution['units'][unit_type] = new_contrib_loser
                        
                        # 2. Répartir proportionnellement selon les bateaux engagés
                        if gained_by_winner > 0:
                            self._distribute_units_proportionally(
                                forces[winning_team], 
                                unit_type, 
                                gained_by_winner
                            )
        
        return battlefield
    
    def _consolidate_units_lost(self, units_lost: dict, player_id: str) -> dict:
        """
        Consolide les units_lost en tenant compte des préfixes (comme côté client)
        
        Args:
            units_lost: Dict des unités perdues avec potentiels préfixes
            player_id: ID du joueur (ex: "player_2" → utilise préfixe "2_")
            
        Returns:
            Dict consolidé des unités perdues par type
        """
        if not units_lost:
            return {}
        
        # Extraire le numéro du player_id (ex: "player_2" → "2")
        player_number = player_id.split('_')[-1] if '_' in player_id else player_id
        prefix = f"{player_number}_"
        
        consolidated_lost = {}
        
        for key, count in units_lost.items():
            if key.startswith(prefix):
                # Retirer le préfixe (ex: "2_archer" → "archer")
                unit_type = key[len(prefix):]
                consolidated_lost[unit_type] = consolidated_lost.get(unit_type, 0) + count
            else:
                # Garder tel quel (unités sans préfixe)
                consolidated_lost[key] = consolidated_lost.get(key, 0) + count
        
        return consolidated_lost

    def check_surrender_flag(self, battle_id: str) -> Tuple[bool, str, str]:
        """
        🏳️ Condition 3: Vérifier si quelqu'un s'est rendu
        
        Logique:
        - Vérifie un flag "surrender" dans battlefields_v2.json
        - Sera déclenché par les boutons "Se rendre" dans l'interface
        
        Returns:
            (has_winner, winner_team, 'surrender')
        """
        
        try:
            battlefields_data = self._load_json('battlefields_v2.json')
            
            if battle_id not in battlefields_data:
                return (False, '', 'surrender')
            
            battlefield = battlefields_data[battle_id]
            
            # Vérifier si la bataille est marquée comme terminée par abandon
            if battlefield.get('victory_type') == 'surrender':
                winner_team = battlefield.get('winner_team', '')
                return (True, winner_team, 'surrender')
            
            return (False, '', 'surrender')
            
        except Exception as e:
            return (False, '', 'surrender')
    
    # =========================================================================
    # 🎯 FONCTION PRINCIPALE DE VÉRIFICATION
    # =========================================================================
    
    def check_all_victory_conditions(self, battle_id: str) -> Tuple[bool, str, str]:
        """
        Vérifie toutes les conditions de victoire
        
        Args:
            battle_id: ID de la bataille
            
        Returns:
            Tuple (has_winner, winner_team, victory_type)
            - has_winner: True si la bataille doit se terminer
            - winner_team: 'attacker' ou 'defender' (ou '' si aucun)
            - victory_type: 'elimination', 'moral_breakdown', 'surrender'
        """
        
        # 1. Vérifier abandon (priorité car décision joueur)
        surrender_result = self.check_surrender_flag(battle_id)
        if surrender_result[0]:
            return surrender_result
            
        # 2. Vérifier effondrement du moral (priorité sur élimination)
        moral_result = self.check_moral_victory(battle_id)
        if moral_result[0]:
            return moral_result
            
        # 3. Vérifier élimination complète (après moral)
        elimination_result = self.check_elimination_victory(battle_id)
        if elimination_result[0]:
            return elimination_result
            
        # Aucune condition de victoire atteinte
        return (False, '', '')
    
    def _distribute_units_proportionally(self, team_forces: dict, unit_type: str, total_units: int):
        """
        Répartit les unités gagnées proportionnellement selon les bateaux engagés
        
        Args:
            team_forces: Forces de l'équipe gagnante (ex: forces['attackers'])
            unit_type: Type d'unité à répartir (ex: 'archer')
            total_units: Nombre total d'unités à répartir
        """
        # 1. Calculer le total de bateaux engagés par tous les joueurs
        total_ships = 0
        player_ship_counts = {}
        
        for player_id, player_forces in team_forces.items():
            contributions = player_forces.get('contributions', [])
            player_ships = 0
            
            for contribution in contributions:
                ships = contribution.get('transport_ships', 0)
                player_ships += ships
            
            player_ship_counts[player_id] = player_ships
            total_ships += player_ships
        
        if total_ships == 0:
            # Si aucun bateau, donner toutes les unités au premier joueur de l'équipe gagnante
            first_player_id = list(team_forces.keys())[0]
            first_player_forces = team_forces[first_player_id]
            contributions = first_player_forces.get('contributions', [])
            if contributions:
                contribution = contributions[0]
                old_contrib = contribution['units'].get(unit_type, 0)
                new_contrib = old_contrib + total_units
                contribution['units'][unit_type] = new_contrib
            return
        
        
        # 2. Répartir proportionnellement
        units_distributed = 0
        
        for player_id, player_ships in player_ship_counts.items():
            if player_ships == 0:
                continue
                
            # Calcul proportionnel avec arrondi
            proportion = player_ships / total_ships
            player_units = round(total_units * proportion)
            
            # Ajuster le dernier joueur pour éviter les erreurs d'arrondi
            is_last_player = player_id == list(player_ship_counts.keys())[-1]
            if is_last_player:
                player_units = total_units - units_distributed
            
            if player_units > 0:
                # Distribuer proportionnellement entre toutes les contributions du joueur
                player_forces = team_forces[player_id]
                contributions = player_forces.get('contributions', [])
                
                if contributions:
                    # Calculer le total des bateaux de ce joueur pour répartir entre ses contributions
                    player_total_ships = sum(c.get('transport_ships', 0) for c in contributions)
                    
                    if player_total_ships > 0:
                        units_distributed_for_player = 0
                        
                        for i, contribution in enumerate(contributions):
                            contrib_ships = contribution.get('transport_ships', 0)
                            if contrib_ships > 0:
                                # Proportion de cette contribution par rapport au total du joueur
                                contrib_proportion = contrib_ships / player_total_ships
                                contrib_units = round(player_units * contrib_proportion)
                                
                                # Ajuster le dernier pour éviter les erreurs d'arrondi
                                is_last_contrib = (i == len(contributions) - 1)
                                if is_last_contrib:
                                    contrib_units = player_units - units_distributed_for_player
                                
                                if contrib_units > 0:
                                    old_contrib = contribution['units'].get(unit_type, 0)
                                    new_contrib = old_contrib + contrib_units
                                    contribution['units'][unit_type] = new_contrib
                                    
                                    from_city = contribution.get('from_city', 'unknown')
                                    contrib_percentage = contrib_proportion * 100
                                    
                                    units_distributed_for_player += contrib_units
                        
                        percentage = (player_ships / total_ships) * 100
                        units_distributed += player_units
                    else:
                        # Fallback à la première contribution si aucun bateau trouvé
                        contribution = contributions[0]
                        old_contrib = contribution['units'].get(unit_type, 0)
                        new_contrib = old_contrib + player_units
                        contribution['units'][unit_type] = new_contrib
                        
                        percentage = (player_ships / total_ships) * 100
                        units_distributed += player_units
        
    
    def _distribute_resources_proportionally(self, team_forces: dict, resource_type: str, total_amount: int):
        """
        Répartit les ressources pillées proportionnellement selon les bateaux engagés
        
        Args:
            team_forces: Forces de l'équipe gagnante
            resource_type: Type de ressource (ex: 'wood', 'iron')
            total_amount: Quantité totale à répartir
        """
        # 1. Calculer le total de bateaux engagés
        total_ships = 0
        player_ship_counts = {}
        
        for player_id, player_forces in team_forces.items():
            contributions = player_forces.get('contributions', [])
            player_ships = 0
            
            for contribution in contributions:
                ships = contribution.get('transport_ships', 0)
                player_ships += ships
            
            player_ship_counts[player_id] = player_ships
            total_ships += player_ships
        
        if total_ships == 0:
            return
        
        
        # 2. Répartir proportionnellement
        resources_distributed = 0
        
        for player_id, player_ships in player_ship_counts.items():
            if player_ships == 0:
                continue
                
            # Calcul proportionnel avec arrondi
            proportion = player_ships / total_ships
            player_amount = round(total_amount * proportion)
            
            # Ajuster le dernier joueur pour éviter les erreurs d'arrondi
            is_last_player = player_id == list(player_ship_counts.keys())[-1]
            if is_last_player:
                player_amount = total_amount - resources_distributed
            
            if player_amount > 0:
                # Attribuer à la première contribution du joueur (celle avec pillage)
                player_forces = team_forces[player_id]
                contributions = player_forces.get('contributions', [])
                
                for contribution in contributions:
                    if 'pillage' in contribution:
                        old_amount = contribution['pillage'].get(resource_type, 0)
                        new_amount = old_amount + player_amount
                        contribution['pillage'][resource_type] = new_amount
                        
                        percentage = (player_ships / total_ships) * 100
                        
                        resources_distributed += player_amount
                        break
        
    
    def _prepare_proportional_resource_distribution(self, battlefield: dict, surrendering_team: str, winning_team: str):
        """
        Prépare le système de distribution proportionnelle des ressources lors d'une reddition.
        Cette méthode marque le battlefield pour que les ressources pillées soient distribuées 
        proportionnellement plutôt qu'au premier attaquant.
        """
        try:
            
            # Marquer le battlefield pour indiquer qu'il faut une distribution proportionnelle
            if 'surrender_info' not in battlefield:
                battlefield['surrender_info'] = {}
            
            battlefield['surrender_info']['proportional_pillage'] = True
            battlefield['surrender_info']['surrendering_team'] = surrendering_team
            battlefield['surrender_info']['winning_team'] = winning_team
            
            # Calculer les contributions des gagnants pour référence future
            forces = battlefield['forces']
            winning_forces = forces.get(winning_team, {})
            
            total_ships = 0
            player_contributions = {}
            
            for player_id, player_forces in winning_forces.items():
                contributions = player_forces.get('contributions', [])
                player_ships = 0
                
                for contribution in contributions:
                    ships = contribution.get('transport_ships', 0)
                    player_ships += ships
                
                if player_ships > 0:
                    player_contributions[player_id] = player_ships
                    total_ships += player_ships
            
            battlefield['surrender_info']['player_contributions'] = player_contributions
            battlefield['surrender_info']['total_ships'] = total_ships
            
            
        except Exception as e:
            pass

    def _handle_wild_camp_victory(self, battle_id: str, winner_team: str):
        """
        Gère l'incrémentation du niveau du village barbare après une victoire contre lui
        """
        try:
            # Vérifier s'il s'agit d'un combat contre un village barbare
            battlefields_data = self._load_json('battlefields_v2.json')
            battlefield = battlefields_data.get(battle_id, {})
            
            participants = battlefield.get('participants', {})
            defenders = participants.get('defenders', [])
            
            # Vérifier si un défenseur est 'wild_camp' et victoire des attaquants
            if 'wild_camp' not in defenders or winner_team != 'attackers':
                return
            
            # Protection anti-double incrémentation
            if battlefield.get('wild_camp_level_incremented'):
                return
            
            attackers = participants.get('attackers', [])
            if attackers:
                self._increment_wild_camp_level(attackers[0])
                battlefield['wild_camp_level_incremented'] = True
                self._save_json('battlefields_v2.json', battlefields_data)
            
        except Exception:
            pass

    def _increment_wild_camp_level(self, player_id: str):
        """
        Incrémente le niveau du village barbare pour le joueur spécifié
        """
        try:
            # Charger la configuration pour obtenir le niveau maximum
            config_data = self._load_config('wild_camps_config.json')
            max_level = config_data.get('max_level', 30)
            
            savegame_data = self._load_json('savegame.json')
            cities = savegame_data.get('cities', [])
            player_cities = [city for city in cities if city.get('owner') == player_id]
            
            if player_cities:
                # Calculer le nouveau niveau (maximum selon config)
                current_level = player_cities[0].get('wild_camp_level', 1)
                new_level = min(current_level + 1, max_level)
                
                # Mettre à jour toutes les villes du joueur
                for city in cities:
                    if city.get('owner') == player_id:
                        city['wild_camp_level'] = new_level
                
                self._save_json('savegame.json', savegame_data)
                
        except Exception:
            pass

    def _execute_automatic_pillage(self, battle_id: str, battlefields_data: dict) -> bool:
        """
        Déclenche automatiquement le pillage après une victoire des attaquants
        
        Args:
            battle_id: ID de la bataille
            battlefields_data: Données complètes de battlefields_v2.json
            
        Returns:
            bool: True si pillage réussi
        """
        try:
            print(f"💰 [PILLAGE-AUTO] Démarrage du pillage automatique pour {battle_id}")
            
            if battle_id not in battlefields_data:
                print(f"❌ [PILLAGE-AUTO] Bataille {battle_id} non trouvée")
                return False
                
            battlefield = battlefields_data[battle_id]
            
            # 1. Récupérer la ville cible (location de la bataille)
            location = battlefield.get('location', '')
            
            # Gérer les villages barbares avec leur système de récompenses
            if location.startswith('wild_camp_'):
                print(f"🏴‍☠️ [PILLAGE-AUTO] Village barbare détecté - système de récompenses")
                return self._execute_barbarian_pillage(battle_id, battlefields_data)
            
            city_id = location
            
            # 2. Calculer le nombre total de bateaux disponibles depuis les contributions
            participants = battlefield.get('participants', {})
            attackers = participants.get('attackers', [])
            forces = battlefield.get('forces', {})
            attacker_forces = forces.get('attackers', {})
            
            total_ships = 0
            pillage_per_player = {}  # Pour répartition proportionnelle
            
            for attacker_id in attackers:
                player_data = attacker_forces.get(attacker_id, {})
                contributions = player_data.get('contributions', [])
                
                player_ships = 0
                for contribution in contributions:
                    ships = contribution.get('transport_ships', 0)
                    player_ships += ships
                
                if player_ships > 0:
                    total_ships += player_ships
                    pillage_per_player[attacker_id] = player_ships
            
            print(f"🚢 [PILLAGE-AUTO] Total bateaux disponibles: {total_ships}")
            
            if total_ships == 0:
                print(f"⚠️ [PILLAGE-AUTO] Aucun bateau disponible - pas de pillage")
                return False
            
            # 3. Importer et utiliser le PillageManager
            from app.routes.pillage_routes import PillageManager
            pillage_manager = PillageManager()
            
            # 4. Calculer les ressources pillables
            pillage_data = pillage_manager.calculate_pillage_resources(city_id, total_ships)
            
            if 'error' in pillage_data:
                print(f"❌ [PILLAGE-AUTO] Erreur calcul: {pillage_data['error']}")
                return False
            
            pillable_resources = pillage_data.get('pillable_resources', {})
            total_pillable = sum(pillable_resources.values())
            
            print(f"📦 [PILLAGE-AUTO] Ressources pillables: {pillable_resources}")
            
            if total_pillable == 0:
                print(f"⏭️ [PILLAGE-AUTO] Aucune ressource à piller")
                return False
            
            # 5. Calculer la distribution proportionnelle
            transport_capacity = total_ships * 500
            
            pillaged_resources = {}
            if total_pillable <= transport_capacity:
                # On peut tout prendre
                pillaged_resources = pillable_resources.copy()
            else:
                # Distribution proportionnelle
                for resource_type, amount in pillable_resources.items():
                    proportion = amount / total_pillable
                    pillaged_amount = int(transport_capacity * proportion)
                    if pillaged_amount > 0:
                        pillaged_resources[resource_type] = pillaged_amount
            
            print(f"💎 [PILLAGE-AUTO] Ressources pillées: {pillaged_resources}")
            
            # 6. Transférer les ressources de la ville vers les attaquants
            savegame_data = self._load_json('savegame.json')
            
            # Retirer des ressources de la ville défendue
            city_updated = False
            for city in savegame_data.get('cities', []):
                if city['id'] == city_id:
                    for resource_type, amount in pillaged_resources.items():
                        if resource_type in city.get('resources', {}):
                            city['resources'][resource_type] -= amount
                            city['resources'][resource_type] = max(0, city['resources'][resource_type])
                    city_updated = True
                    print(f"✅ [PILLAGE-AUTO] Ressources retirées de {city_id}")
                    break
            
            if not city_updated:
                print(f"❌ [PILLAGE-AUTO] Ville {city_id} non trouvée")
                return False
            
            # 7. Distribuer proportionnellement aux attaquants selon leurs bateaux
            for attacker_id, player_ships in pillage_per_player.items():
                proportion = player_ships / total_ships
                
                # Trouver la première ville de l'attaquant
                for city in savegame_data.get('cities', []):
                    if city.get('owner') == attacker_id:
                        if 'resources' not in city:
                            city['resources'] = {}
                        
                        # Créditer la part proportionnelle
                        for resource_type, total_amount in pillaged_resources.items():
                            player_amount = int(total_amount * proportion)
                            if player_amount > 0:
                                if resource_type not in city['resources']:
                                    city['resources'][resource_type] = 0
                                city['resources'][resource_type] += player_amount
                        
                        print(f"✅ [PILLAGE-AUTO] {attacker_id} reçoit {int(proportion * 100)}% du butin")
                        break
            
            # Sauvegarder savegame
            if self._save_json('savegame.json', savegame_data):
                # Enregistrer dans les contributions
                import os
                import json
                battlefield_path = os.path.join(self.gamedata_dir, 'battlefields_v2.json')
                
                # Recharger les données fraîches
                with open(battlefield_path, 'r', encoding='utf-8') as f:
                    fresh_battlefields = json.load(f)
                
                if battle_id in fresh_battlefields:
                    fresh_battlefield = fresh_battlefields[battle_id]
                    fresh_attackers_forces = fresh_battlefield.get('forces', {}).get('attackers', {})
                    
                    for attacker_id in attackers:
                        if attacker_id in pillage_per_player and attacker_id in fresh_attackers_forces:
                            proportion = pillage_per_player[attacker_id] / total_ships
                            contributions = fresh_attackers_forces[attacker_id].get('contributions', [])
                            
                            if contributions:
                                # Ajouter le pillage à la première contribution
                                if 'pillage' not in contributions[0]:
                                    contributions[0]['pillage'] = {}
                                
                                for resource_type, total_amount in pillaged_resources.items():
                                    player_amount = int(total_amount * proportion)
                                    if player_amount > 0:
                                        contributions[0]['pillage'][resource_type] = player_amount
                    
                    # Sauvegarder directement
                    with open(battlefield_path, 'w', encoding='utf-8') as f:
                        json.dump(fresh_battlefields, f, indent=2, ensure_ascii=False)
                
                # Mettre à jour la quête de pillage pour chaque attaquant
                quest_service = QuestService()
                players_file = os.path.join(self.gamedata_dir, 'players.json')
                if os.path.exists(players_file):
                    with open(players_file, 'r', encoding='utf-8') as f:
                        players_data = json.load(f)
                        for attacker_id in attackers:
                            if attacker_id in pillage_per_player:
                                proportion = pillage_per_player[attacker_id] / total_ships
                                total_pillaged = sum(pillaged_resources.values())
                                player_pillaged = int(total_pillaged * proportion)
                                if player_pillaged > 0:
                                    # Convertir player_id → username
                                    username = None
                                    for player in players_data.get('players', []):
                                        if player.get('id') == attacker_id:
                                            username = player.get('username')
                                            break
                                    if username:
                                        quest_service.update_quest_progress(
                                            username,
                                            'mil_pillage_resources',
                                            player_pillaged
                                        )
                
                return True
            return False
                
        except Exception as e:
            print(f"❌ [PILLAGE-AUTO] Exception: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _execute_barbarian_pillage(self, battle_id: str, battlefields_data: dict) -> bool:
        """
        Gère le pillage automatique des villages barbares
        
        Args:
            battle_id: ID de la bataille
            battlefields_data: Données complètes de battlefields_v2.json
            
        Returns:
            bool: True si pillage réussi
        """
        try:
            if battle_id not in battlefields_data:
                print(f"❌ Pillage barbare: bataille {battle_id} non trouvée")
                return False
                
            battlefield = battlefields_data[battle_id]
            
            # 1. Extraire le niveau du village barbare
            original_level = battlefield.get('original_barbarian_level', 1)
            
            # 2. Charger la configuration des villages barbares
            barbarian_config = self._load_config('wild_camps_config.json')
            level_key = f'level_{original_level}'
            
            if level_key not in barbarian_config:
                print(f"❌ Pillage barbare: configuration niveau {original_level} non trouvée")
                return False
            
            rewards = barbarian_config[level_key].get('rewards', {})
            
            if not rewards or sum(rewards.values()) == 0:
                print(f"⚠️ [PILLAGE-BARBARE] Aucune récompense disponible")
                return False
            
            # 3. Distribuer les récompenses aux attaquants
            participants = battlefield.get('participants', {})
            attackers = participants.get('attackers', [])
            forces = battlefield.get('forces', {})
            attacker_forces = forces.get('attackers', {})
            
            savegame_data = self._load_json('savegame.json')
            
            # Pour les villages barbares, donner toutes les récompenses au premier attaquant
            # (les barbares n'ont généralement qu'un seul attaquant)
            if attackers:
                main_attacker = attackers[0]
                
                # Trouver la première ville de l'attaquant
                for city in savegame_data.get('cities', []):
                    if city.get('owner') == main_attacker:
                        if 'resources' not in city:
                            city['resources'] = {}
                        
                        # Ajouter les récompenses
                        for resource_type, amount in rewards.items():
                            if resource_type not in city['resources']:
                                city['resources'][resource_type] = 0
                            city['resources'][resource_type] += amount
                        
                        break
                
                # Enregistrer dans les contributions
                if main_attacker in attacker_forces:
                    contributions = attacker_forces[main_attacker].get('contributions', [])
                    if contributions:
                        contributions[0]['pillage'] = rewards.copy()
                        
                        # Sauvegarde directe pour éviter les écrasements
                        import os
                        import json
                        battlefield_path = os.path.join(self.gamedata_dir, 'battlefields_v2.json')
                        
                        with open(battlefield_path, 'r', encoding='utf-8') as f:
                            fresh_battlefields = json.load(f)
                        
                        if battle_id in fresh_battlefields:
                            fresh_battlefield = fresh_battlefields[battle_id]
                            fresh_forces = fresh_battlefield.get('forces', {}).get('attackers', {})
                            if main_attacker in fresh_forces:
                                fresh_contribs = fresh_forces[main_attacker].get('contributions', [])
                                if fresh_contribs:
                                    fresh_contribs[0]['pillage'] = rewards.copy()
                                    with open(battlefield_path, 'w', encoding='utf-8') as f:
                                        json.dump(fresh_battlefields, f, indent=2, ensure_ascii=False)
            
            # Mettre à jour la quête de pillage pour l'attaquant principal
            if attackers and 'main_attacker' in locals():
                total_pillaged = sum(rewards.values())
                if total_pillaged > 0:
                    # Convertir player_id → username
                    players_file = os.path.join(self.gamedata_dir, 'players.json')
                    if os.path.exists(players_file):
                        with open(players_file, 'r', encoding='utf-8') as f:
                            players_data = json.load(f)
                            username = None
                            for player in players_data.get('players', []):
                                if player.get('id') == main_attacker:
                                    username = player.get('username')
                                    break
                            if username:
                                quest_service = QuestService()
                                quest_service.update_quest_progress(
                                    username,
                                    'mil_pillage_resources',
                                    total_pillaged
                                )
            
            # Sauvegarder savegame
            return self._save_json('savegame.json', savegame_data)
                
        except Exception as e:
            print(f"❌ [PILLAGE-BARBARE] Exception: {e}")
            import traceback
            traceback.print_exc()
            return False

    def save_battle_result(self, battle_id: str, winner_team: str, victory_type: str) -> bool:
        """
        Sauvegarde le bilan final de la bataille dans battlefields_v2.json
        
        Args:
            battle_id: ID de la bataille
            winner_team: Équipe gagnante ('attackers' ou 'defenders')
            victory_type: Type de victoire ('elimination', 'moral_breakdown', 'surrender')
            
        Returns:
            bool: True si sauvegarde réussie
        """
        try:
            
            # Charger les données de battlefield
            battlefields_data = self._load_json('battlefields_v2.json')
            
            if battle_id not in battlefields_data:
                return False
                
            battlefield = battlefields_data[battle_id]
            
            # Protection anti-double : skip si déjà complétée
            if battlefield.get('status') == 'completed':
                return True
            
            # Verrouillage immédiat pour bloquer les appels parallèles
            battlefield['status'] = 'completed'
            self._save_json('battlefields_v2.json', battlefields_data)
            
            # Ajouter le bilan final
            battlefield['battle_result'] = {
                'winner_team': winner_team,
                'victory_type': victory_type,
                'completed_at': time.time(),
                'victory_message': f"Victoire des {winner_team} par {victory_type}"
            }
            
            # Actions post-victoire
            self._handle_wild_camp_victory(battle_id, winner_team)
            
            # Pillage automatique pour victoires des attaquants
            if winner_team == 'attackers':
                self._execute_automatic_pillage(battle_id, battlefields_data)
            
            self._save_pillage_summary(battlefield, winner_team)
            self._create_battle_notification(battle_id, winner_team, victory_type)
            
            # 📊 MISE À JOUR DES STATISTIQUES JOUEURS ET HÉROS (avant suppression)
            location = battlefield.get('location', '')
            is_wild_camp = location.startswith('wild_camp_')
            
            player_stats_result = self.update_player_stats_from_battle(battlefield, winner_team, is_wild_camp)
            hero_stats_result = self.update_hero_stats_from_battle(battlefield, winner_team)
            
            if not player_stats_result:
                print(f"⚠️ Erreur mise à jour stats joueurs pour {battle_id}")
            
            # Sauvegarder les modifications finales (battle_result, etc.)
            self._save_json('battlefields_v2.json', battlefields_data)
            
            # ⚡ RETOUR AUTOMATIQUE DES TROUPES (supprime le battlefield à la fin)
            self.execute_automatic_return(battle_id)
            
            return True
                
        except Exception as e:
            return False

    def _save_pillage_summary(self, battlefield: dict, winner_team: str) -> None:
        """
        Calcule et sauvegarde un résumé des ressources pillées
        Pour les villages barbares, récupère les données depuis le système de pillage
        """
        try:
            total_pillage = {'wood': 0, 'stone': 0, 'iron': 0, 'cereal': 0, 'papyrus': 0}
            pillage_details = {}
            
            # 1. D'abord essayer de récupérer depuis les contributions normales
            winner_forces = battlefield.get('forces', {}).get(winner_team, {})
            
            for player_id, player_forces in winner_forces.items():
                contributions = player_forces.get('contributions', [])
                player_total = {'wood': 0, 'stone': 0, 'iron': 0, 'cereal': 0, 'papyrus': 0}
                
                for contrib in contributions:
                    pillage = contrib.get('pillage', {})
                    for resource, amount in pillage.items():
                        if resource in total_pillage:
                            total_pillage[resource] += amount
                            player_total[resource] += amount
                
                # Sauvegarder les totaux par joueur
                if any(player_total.values()):
                    pillage_details[player_id] = player_total
            
            # 2. Si pas de pillage trouvé ET que c'est un village barbare, utiliser les valeurs par défaut
            location = battlefield.get('location', '')
            if not any(total_pillage.values()) and 'wild_camp' in location:
                # Extraire le niveau du village depuis location
                try:
                    level = int(location.replace('wild_camp_', ''))
                except:
                    level = 1
                
                # Charger les récompenses par défaut depuis wild_camps_config.json
                try:
                    config_path = os.path.join(self.data_dir, 'wild_camps_config.json')
                    if os.path.exists(config_path):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            barbarian_config = json.load(f)
                        
                        # Clé avec préfixe "level_" 
                        level_key = f"level_{level}"
                        if level_key in barbarian_config:
                            default_rewards = barbarian_config[level_key].get('rewards', {})
                            total_pillage.update(default_rewards)
                            
                            # Attribuer tout le pillage au premier joueur gagnant
                            if winner_forces:
                                first_player = list(winner_forces.keys())[0]
                                pillage_details[first_player] = default_rewards.copy()
                                
                                # ✅ AJOUT : Intégrer le pillage directement dans les contributions
                                player_data = winner_forces[first_player]
                                contributions = player_data.get('contributions', [])
                                
                                # Répartir les ressources proportionnellement entre les contributions
                                if contributions:
                                    total_ships = sum(contrib.get('transport_ships', 0) for contrib in contributions)
                                    if total_ships == 0:
                                        total_ships = len(contributions)  # Fallback si pas de ships
                                    
                                    for contrib in contributions:
                                        ships = contrib.get('transport_ships', 0)
                                        if ships == 0 and len(contributions) > 0:
                                            ships = 1  # Fallback si pas de ships
                                        
                                        # Proportionnel au nombre de vaisseaux
                                        contribution_ratio = ships / total_ships
                                        contrib['pillage'] = {}
                                        
                                        for resource, amount in default_rewards.items():
                                            contrib['pillage'][resource] = int(amount * contribution_ratio)
                        else:
                            pass  # Clé non trouvée dans la configuration
                                
                except Exception as config_error:
                    pass
            
            # 3. Ajouter le résumé du pillage au battlefield
            if any(total_pillage.values()):
                battlefield['pillage_summary'] = {
                    'total_resources': total_pillage,
                    'by_player': pillage_details
                }
                
        except Exception as e:
            pass

    def _mark_battle_as_finished_in_battles(self, battle_id: str, winner_team: str, victory_type: str):
        """
        Marque une bataille comme terminée dans battlesv2.json
        """
        try:
            import time
            battles_data = self._load_json('battlesv2.json')
            
            if battle_id in battles_data:
                battles_data[battle_id]['status'] = 'finished'
                battles_data[battle_id]['winner'] = winner_team
                battles_data[battle_id]['victory_type'] = victory_type
                battles_data[battle_id]['finished_at'] = time.time()
                
                # Sauvegarder
                self._save_json('battlesv2.json', battles_data)
                
        except Exception as e:
            pass

    # =========================================================================
    # 📊 MISE À JOUR DES STATISTIQUES APRÈS BATAILLE
    # =========================================================================

    def update_player_stats_from_battle(self, battlefield: dict, winner_team: str, is_wild_camp: bool) -> bool:
        """
        Met à jour les statistiques des joueurs après la bataille
        
        Pour chaque joueur dans players.json :
        - total_units_killed += units_killed 
        - total_units_lost += units_lost
        - total_xp_gained += xp_gained  
        - battles_fought += 1
        - victories/defeats basé sur winner_team
        - victories_barbarians si bataille contre village barbare gagné
        """
        try:
            # Charger les données des joueurs
            players_data = self._load_json('players.json')
            
            if not players_data or 'players' not in players_data:
                return False
            
            # Traiter les statistiques pour chaque équipe
            for team in ['attackers', 'defenders']:
                team_forces = battlefield.get('forces', {}).get(team, {})
                
                for player_id, player_data in team_forces.items():
                    # Skip barbarian village
                    if player_id == 'wild_camp':
                        continue
                    
                    # Calculer les totaux pour ce joueur
                    units_killed_total = sum(player_data.get('units_killed', {}).values())
                    units_lost_total = sum(player_data.get('units_lost', {}).values()) 
                    xp_gained = player_data.get('xp_gained', 0)
                    
                    # Déterminer victoire/défaite
                    won_battle = (winner_team == team)
                    
                    # Trouver le joueur dans players.json
                    player_found = False
                    for player in players_data['players']:
                        if player.get('id') == player_id:
                            # Mettre à jour les stats
                            old_kills = player.get('total_units_killed', 0)
                            old_lost = player.get('total_units_lost', 0)  
                            old_xp = player.get('total_xp_gained', 0)
                            old_battles = player.get('battles_fought', 0)
                            old_victories = player.get('victories', 0)
                            old_defeats = player.get('defeats', 0)
                            old_victories_barbarians = player.get('victories_barbarians', 0)
                            
                            player['total_units_killed'] = old_kills + units_killed_total
                            player['total_units_lost'] = old_lost + units_lost_total  
                            player['total_xp_gained'] = old_xp + xp_gained
                            player['battles_fought'] = old_battles + 1
                            
                            # Victoires/défaites
                            if won_battle:
                                player['victories'] = old_victories + 1
                                # Victoire contre village barbare
                                if is_wild_camp and team == 'attackers':
                                    player['victories_barbarians'] = old_victories_barbarians + 1
                            else:
                                player['defeats'] = old_defeats + 1
                            
                            player_found = True
                            break
                    
                    if not player_found:
                        print(f"⚠️ Joueur {player_id} non trouvé dans players.json")
            
            # Sauvegarder les données mises à jour
            return self._save_json('players.json', players_data)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False

    def update_hero_stats_from_battle(self, battlefield: dict, winner_team: str) -> bool:
        """
        Met à jour les statistiques des héros après la bataille
        
        Pour chaque héros dans player_heroes.json :
        - current_experience += xp_gained (réparti entre héros)
        - battles_fought += 1
        - victories/defeats basé sur winner_team  
        - units_killed += units_killed (réparti entre héros)
        - units_lost += units_lost (réparti entre héros)
        - times_died += 1 (si HP = 0, TODO)
        """
        try:
            # Charger les données des héros
            heroes_data = self._load_json('player_heroes.json')
            
            if not heroes_data:
                return False
            
            # Traiter les statistiques pour chaque équipe
            for team in ['attackers', 'defenders']:
                team_forces = battlefield.get('forces', {}).get(team, {})
                
                for player_id, player_data in team_forces.items():
                    # Skip barbarian village
                    if player_id == 'wild_camp':
                        continue
                    
                    # Calculer les totaux pour ce joueur
                    units_killed_total = sum(player_data.get('units_killed', {}).values())
                    units_lost_total = sum(player_data.get('units_lost', {}).values()) 
                    xp_gained = player_data.get('xp_gained', 0)
                    
                    # Déterminer victoire/défaite
                    won_battle = (winner_team == team)
                    
                    # Extraire les héros depuis les contributions
                    heroes_list = []
                    contributions = player_data.get('contributions', [])
                    for contribution in contributions:
                        contribution_heroes = contribution.get('heroes', [])
                        heroes_list.extend(contribution_heroes)
                    
                    if heroes_list and player_id in heroes_data:
                        nb_heroes = len(heroes_list)
                        
                        # Répartir équitablement entre les héros
                        if nb_heroes > 0:
                            xp_per_hero = xp_gained // nb_heroes
                            kills_per_hero = units_killed_total // nb_heroes
                            losses_per_hero = units_lost_total // nb_heroes
                            
                            for hero_id in heroes_list:
                                if 'heroes' in heroes_data[player_id] and hero_id in heroes_data[player_id]['heroes']:
                                    hero = heroes_data[player_id]['heroes'][hero_id]
                                    
                                    # Valeurs actuelles
                                    old_xp = hero.get('current_experience', 0)
                                    old_battles = hero.get('battles_fought', 0)
                                    old_victories = hero.get('victories', 0)
                                    old_defeats = hero.get('defeats', 0)
                                    old_kills = hero.get('units_killed', 0)
                                    old_losses = hero.get('units_lost', 0)
                                    
                                    # Mettre à jour les stats du héros
                                    hero['current_experience'] = old_xp + xp_per_hero
                                    hero['battles_fought'] = old_battles + 1
                                    hero['units_killed'] = old_kills + kills_per_hero
                                    hero['units_lost'] = old_losses + losses_per_hero
                                    
                                    # Victoires/défaites pour le héros
                                    if won_battle:
                                        hero['victories'] = old_victories + 1
                                    else:
                                        hero['defeats'] = old_defeats + 1
                                    
                                    # TODO: Vérifier si le héros est mort (HP = 0) pour times_died
                                    # Cette info n'est pas encore disponible dans battlefields_v2.json
                                    # hero['times_died'] = hero.get('times_died', 0) + (1 if hero_hp == 0 else 0)
            
            # Sauvegarder les données mises à jour
            return self._save_json('player_heroes.json', heroes_data)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False
    
    def _create_battle_notification(self, battle_id: str, winner_team: str, victory_type: str) -> bool:
        """
        Crée des notifications de résultat de bataille pour tous les participants
        
        Args:
            battle_id: ID de la bataille
            winner_team: Équipe gagnante ('attackers' ou 'defenders')
            victory_type: Type de victoire ('elimination', 'moral_breakdown', 'surrender')
        """
        try:
            battlefields_data = self._load_json('battlefields_v2.json')
            
            if battle_id not in battlefields_data:
                return False
            
            battlefield = battlefields_data[battle_id]
            participants = battlefield.get('participants', {})
            forces = battlefield.get('forces', {})
            
            # Charger les notifications existantes
            notifications = {}
            if os.path.exists(self.notifications_file):
                try:
                    with open(self.notifications_file, 'r', encoding='utf-8') as f:
                        notifications = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    notifications = {}
            
            # Récupérer le nom de la bataille
            battle_name = battlefield.get('battle_name', f'Bataille {battle_id[:8]}')
            
            # Créer une notification pour chaque participant
            for team in ['attackers', 'defenders']:
                players = participants.get(team, [])
                
                for player_id in players:
                    # Déterminer si victoire ou défaite pour ce joueur
                    is_victory = (team == winner_team)
                    notif_type = 'victory' if is_victory else 'defeat'
                    
                    # Récupérer les stats du joueur
                    player_forces = forces.get(team, {}).get(player_id, {})
                    contributions = player_forces.get('contributions', [])
                    
                    # Calculer les pertes totales du joueur
                    total_casualties = 0
                    total_units_sent = 0
                    total_pillage = {}
                    
                    for contribution in contributions:
                        units_sent = contribution.get('units', {})
                        for unit_type, count in units_sent.items():
                            total_units_sent += count
                        
                        casualties = contribution.get('casualties', {})
                        for unit_type, count in casualties.items():
                            total_casualties += count
                        
                        # Récupérer le pillage (uniquement pour les vainqueurs)
                        if is_victory:
                            pillage = contribution.get('pillage', {})
                            for resource, amount in pillage.items():
                                total_pillage[resource] = total_pillage.get(resource, 0) + amount
                    
                    # Créer la notification
                    notification = {
                        'id': f"{battle_id}_{player_id}",
                        'battleId': battle_id,
                        'playerId': player_id,
                        'type': notif_type,
                        'timestamp': int(time.time() * 1000),
                        'battleName': battle_name,
                        'winnerTeam': winner_team,
                        'victoryType': victory_type,
                        'playerTeam': team,
                        'unitsSent': total_units_sent,
                        'casualties': total_casualties,
                        'pillage': total_pillage if total_pillage else None,
                        'read': False
                    }
                    
                    # Ajouter la notification à la liste du joueur
                    if player_id not in notifications:
                        notifications[player_id] = []
                    
                    notifications[player_id].append(notification)
            
            # Sauvegarder les notifications
            os.makedirs(os.path.dirname(self.notifications_file), exist_ok=True)
            with open(self.notifications_file, 'w', encoding='utf-8') as f:
                json.dump(notifications, f, indent=2, ensure_ascii=False)
            
            print(f"[NOTIFICATIONS] Créé notifications pour bataille {battle_id}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Erreur création notifications: {e}")
            import traceback
            traceback.print_exc()
            return False

    # =========================================================================
    # 🚢 RETOUR AUTOMATIQUE DES TROUPES
    # =========================================================================
    
    def execute_automatic_return(self, battle_id: str) -> bool:
        """
        Gère automatiquement le retour des troupes après une victoire
        Copie exacte de la logique de handle_battle_return_journey()
        
        Étapes:
        1. Retour direct des unités locales (transport_ships = 0)
        2. Configuration des transports retour (transport_ships > 0)
        3. Génération du rapport de bataille
        4. Nettoyage (suppression battlefields + battles)
        """
        try:
            battlefields_data = self._load_json('battlefields_v2.json')
            if battle_id not in battlefields_data:
                return False
            
            battlefield = battlefields_data[battle_id]
            battlefield_location = battlefield.get('location', '')
            
            # Étape 1: Retour direct des unités locales
            self._handle_local_units_return(battlefield)
            
            # Étape 2: Configuration des transports retour
            returned_transports = self._configure_return_transports(battlefield, battle_id, battlefield_location)
            
            # Étape 3: Génération du rapport
            self._create_return_battle_report(battlefield, battle_id, returned_transports)
            
            # Étape 4: Nettoyage
            self._cleanup_battle_data(battle_id)
            
            print(f"✅ [RETOUR-AUTO] Retour automatique complété pour {battle_id}")
            return True
            
        except Exception as e:
            print(f"❌ [RETOUR-AUTO] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _handle_local_units_return(self, battlefield: dict):
        """Retour direct des unités locales (sans transport)"""
        savegame_data = self._load_json('savegame.json')
        cities = savegame_data.get('cities', [])
        
        forces = battlefield.get('forces', {})
        for side in ['attackers', 'defenders']:
            side_forces = forces.get(side, {})
            for player_id, player_data in side_forces.items():
                for contrib in player_data.get('contributions', []):
                    if contrib.get('transport_ships', 0) == 0 and contrib.get('from_city'):
                        self._credit_local_units(cities, contrib['from_city'], contrib, player_id)
        
        self._save_json('savegame.json', savegame_data)
    
    def _credit_local_units(self, cities: list, city_id: str, contribution: dict, player_id: str):
        """Crédite les unités et héros à leur ville d'origine"""
        city = next((c for c in cities if c.get('id') == city_id), None)
        if not city:
            return
        
        if 'military' not in city:
            city['military'] = {}
        if 'garrison' not in city['military']:
            city['military']['garrison'] = {}
        
        garrison = city['military']['garrison']
        if player_id not in garrison:
            garrison[player_id] = {}
        
        # Créditer les unités
        surviving_units = contribution.get('units', {})
        for unit_type, count in surviving_units.items():
            if count > 0:
                if unit_type in garrison[player_id]:
                    current_qty = garrison[player_id][unit_type].get('quantity', 0)
                    garrison[player_id][unit_type]['quantity'] = current_qty + count
                else:
                    garrison[player_id][unit_type] = {'quantity': count}
        
        # Restaurer les héros en statut 'garrison'
        surviving_heroes = contribution.get('heroes', [])
        if surviving_heroes:
            if 'heroes' not in city['military']:
                city['military']['heroes'] = {}
            
            heroes_section = city['military']['heroes']
            for hero_id in surviving_heroes:
                if hero_id in heroes_section:
                    heroes_section[hero_id]['status'] = 'garrison'
                else:
                    heroes_section[hero_id] = {'owner': player_id, 'status': 'garrison'}
    
    def _configure_return_transports(self, battlefield: dict, battle_id: str, battlefield_location: str) -> list:
        """Configure les transports pour le voyage retour"""
        transports_data = self._load_json('transports.json') or {"transports": [], "next_id": 1}
        
        # Trouver les transports de cette bataille
        battle_transports = [
            t for t in transports_data.get('transports', [])
            if (t.get('status') == 'battle_waiting' and 
                t.get('destination_city') == battlefield_location and
                t.get('transport_type') == 'attack')
        ]
        
        if not battle_transports:
            return []
        
        returned_transports = []
        for transport in battle_transports:
            transport_id = transport.get('id')
            source_player = transport.get('source_player_id')
            
            # Récupérer survivants et pillage
            surviving_units, pillage_resources = self._get_transport_results(
                battlefield, transport_id, source_player
            )
            
            # Charger ressources dans le transport
            transport_resources = transport.get('resources', {})
            for unit_type, count in surviving_units.items():
                transport_resources[f"unit_{unit_type}"] = count
            for resource, amount in pillage_resources.items():
                transport_resources[resource] = transport_resources.get(resource, 0) + amount
            
            transport['resources'] = transport_resources
            self._setup_return_journey(transport)
            
            returned_transports.append({
                'transport_id': transport_id,
                'player_id': source_player,
                'surviving_units': surviving_units,
                'pillage_resources': pillage_resources
            })
        
        self._save_json('transports.json', transports_data)
        print(f"✅ [RETOUR-AUTO] {len(returned_transports)} transports configurés")
        return returned_transports
    
    def _get_transport_results(self, battlefield: dict, transport_id: str, player_id: str) -> tuple:
        """Récupère unités survivantes et pillage pour un transport"""
        surviving_units = {}
        pillage_resources = {}
        
        attackers = battlefield.get('forces', {}).get('attackers', {})
        player_data = attackers.get(player_id, {})
        
        transport_contribution = next(
            (c for c in player_data.get('contributions', []) if c.get('id') == transport_id), None
        )
        
        if transport_contribution:
            initial_units = transport_contribution.get('units', {})
            player_losses = player_data.get('units_lost', {})
            
            for unit_type, initial_count in initial_units.items():
                if initial_count > 0:
                    # Chercher pertes avec préfixe joueur EN PRIORITÉ
                    prefixed_name = f"{player_id.split('_')[-1]}_{unit_type}"
                    losses = player_losses.get(prefixed_name, player_losses.get(unit_type, 0))
                    
                    survivors = max(0, initial_count - losses)
                    if survivors > 0:
                        surviving_units[unit_type] = survivors
            
            pillage_resources = {r: a for r, a in transport_contribution.get('pillage', {}).items() if a > 0}
        
        return surviving_units, pillage_resources
    
    def _setup_return_journey(self, transport: dict):
        """Configure un transport pour le retour"""
        original_source = transport['source_city']
        original_destination = transport['destination_city']
        original_source_player = transport['source_player_id']
        original_dest_player = transport['destination_player_id']
        
        transport['source_city'] = original_destination
        transport['destination_city'] = original_source
        transport['source_player_id'] = original_dest_player
        transport['destination_player_id'] = original_source_player
        transport['status'] = 'returning'
        
        original_travel_time = transport.get('travel_time', 3600)
        current_time = time.time()
        
        transport['departure_time'] = current_time
        transport['arrival_time'] = current_time + original_travel_time
        
        if 'timeline' not in transport:
            transport['timeline'] = {}
        transport['timeline']['return_start'] = round(current_time, 2)
        transport['timeline']['return_end'] = round(current_time + original_travel_time, 2)
        
        transport['remaining_time'] = int(original_travel_time)
        transport['last_update'] = current_time
    
    def _create_return_battle_report(self, battlefield: dict, battle_id: str, returned_transports: list):
        """Génère le rapport de retour de bataille"""
        battle_reports_path = os.path.join(self.gamedata_dir, 'battle_reports.json')
        
        if os.path.exists(battle_reports_path):
            with open(battle_reports_path, 'r', encoding='utf-8') as f:
                battle_reports = json.load(f)
        else:
            battle_reports = {'reports': []}
        
        battle_reports['reports'].append({
            'id': f"report_v2_return_{battle_id}_{int(time.time())}",
            'battle_id': battle_id,
            'version': '2.0',
            'timestamp': int(time.time()),
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'location': battlefield.get('location', ''),
            'participants': battlefield.get('participants', {}),
            'outcome': 'retour_voyage_v2_auto',
            'returned_transports': returned_transports,
            'summary': f"Retour automatique depuis {battlefield.get('location', '')}. {len(returned_transports)} transports."
        })
        
        with open(battle_reports_path, 'w', encoding='utf-8') as f:
            json.dump(battle_reports, f, indent=2, ensure_ascii=False)
    
    def _cleanup_battle_data(self, battle_id: str):
        """Supprime les données de bataille après le retour"""
        battlefields_data = self._load_json('battlefields_v2.json')
        if battle_id in battlefields_data:
            del battlefields_data[battle_id]
            self._save_json('battlefields_v2.json', battlefields_data)
        
        battles_data = self._load_json('battlesv2.json')
        if battle_id in battles_data:
            del battles_data[battle_id]
            self._save_json('battlesv2.json', battles_data)
