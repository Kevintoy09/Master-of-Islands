"""
Battle End V2 Manager
=====================

Gestionnaire dédié à la fin des batailles V2 :
- Complètement séparé de battle_end.py (V1) 
- Gestion du retour des troupes vers cities d'origine
- Mise à jour savegame.json avec crédits d'unités
- Création rapports de bataille
- Suppression des battlefields V2
- 🎯 NOUVEAU: Système de victoire/défaite avec 3 conditions
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple


class BattleEndV2Manager:
    """Gestionnaire complet de fin de bataille V2"""
    
    def __init__(self):
        # Chemin absolu vers le dossier data
        # __file__ = .../server/app/battle/battle_end_v2.py
        # Nous voulons aller jusqu'à .../server/
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = os.path.join(base_dir, 'data')
    
    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Charge un fichier JSON du dossier data"""
        filepath = os.path.join(self.data_dir, filename)
        try:
            # Essayer UTF-8 en premier
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except UnicodeDecodeError:
            # Si UTF-8 échoue, essayer UTF-16 (pour les fichiers Windows)
            try:
                with open(filepath, 'r', encoding='utf-16') as f:
                    return json.load(f)
            except UnicodeDecodeError:
                # En dernier recours, utiliser utf-8-sig (avec BOM)
                with open(filepath, 'r', encoding='utf-8-sig') as f:
                    return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Fichier {filename} non trouvé")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Erreur lecture JSON {filename}: {e}")
            return {}
    
    def _save_json(self, filename: str, data: Dict[str, Any]) -> bool:
        """Sauvegarde un fichier JSON dans le dossier data"""
        filepath = os.path.join(self.data_dir, filename)
        try:
            # Créer le répertoire si nécessaire
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"💾 [V2] {filename} sauvegardé")
            return True
        except Exception as e:
            print(f"❌ [V2] Erreur sauvegarde {filename}: {e}")
            return False
    
    def end_battle(self, battle_id: str) -> Dict[str, Any]:
        """
        Terminer une bataille V2 avec gestion complète
        
        Processus V2:
        1. Récupérer les données de la bataille dans battlefields_v2.json
        2. Collecter toutes les troupes (troops_on_the_way + engaged_forces)
        3. Renvoyer les troupes vers from_city (ville d'origine)
        4. Créditer les unités dans savegame.json
        5. Créer un rapport de bataille
        6. Supprimer la battlefield
        
        Args:
            battle_id: Identifiant de la bataille V2
            
        Returns:
            Dict avec success, message, et détails du retour
        """
        try:
            print(f"🏁 [BATTLE_END_V2] Début fin de bataille: {battle_id}")
            
            # =================================================================
            # 1. CHARGER LES DONNÉES DE LA BATAILLE V2
            # =================================================================
            battlefields_data = self._load_json('battlefields_v2.json')
            
            # Trouver la bataille directement (nouvelle structure sans catégories)
            battlefield = None
            if battlefields_data.get(battle_id):
                battlefield = battlefields_data[battle_id]
                # Vérifier que la bataille peut être terminée
                if battlefield['status'] not in ['battle_ready', 'transport']:
                    return {
                        'success': False,
                        'error': f'Bataille V2 {battle_id} ne peut pas être terminée (statut: {battlefield["status"]})'
                    }
            else:
                return {
                    'success': False,
                    'error': f'Bataille V2 {battle_id} non trouvée'
                }
            
            print(f"✅ [BATTLE_END_V2] Bataille trouvée: {battlefield['location']}")
            
            # =================================================================
            # 2. COLLECTER TOUTES LES TROUPES À RENVOYER (SOUSTRACTION DES PERTES)
            # =================================================================
            troops_to_return = {}  # player_id -> {from_city, units, heroes}
            
            # Collecter les forces des attaquants
            for player_id, player_data in battlefield.get('forces', {}).get('attackers', {}).items():
                # Nouvelle structure: unités dans contributions
                contributions = player_data.get('contributions', [])
                initial_units = contributions[0].get('units', {}) if contributions else {}
                units_lost = player_data.get('units_lost', {})
                
                surviving_units = {}
                for unit_type, initial_count in initial_units.items():
                    lost_count = units_lost.get(unit_type, 0)
                    surviving_count = initial_count - lost_count
                    if surviving_count > 0:
                        surviving_units[unit_type] = surviving_count
                
                # Nouvelle structure: from_city dans contributions
                contributions = player_data.get('contributions', [])
                from_city = contributions[0]['from_city'] if contributions and 'from_city' in contributions[0] else None
                
                troops_to_return[player_id] = {
                    'from_city': from_city,
                    'units': surviving_units,
                    'heroes': contributions[0].get('heroes', []) if contributions else []
                }
                
                print(f"⚔️ [BATTLE_END_V2] Attaquant {player_id}: {initial_units} - {units_lost} = {surviving_units} + {contributions[0].get('heroes', []) if contributions else []}")
            
            # Collecter les forces des défenseurs
            for player_id, player_data in battlefield.get('forces', {}).get('defenders', {}).items():
                # Nouvelle structure: unités dans contributions
                contributions = player_data.get('contributions', [])
                initial_units = contributions[0].get('units', {}) if contributions else {}
                units_lost = player_data.get('units_lost', {})
                
                surviving_units = {}
                for unit_type, initial_count in initial_units.items():
                    lost_count = units_lost.get(unit_type, 0)
                    surviving_count = initial_count - lost_count
                    if surviving_count > 0:
                        surviving_units[unit_type] = surviving_count
                
                # Nouvelle structure: from_city dans contributions
                contributions = player_data.get('contributions', [])
                from_city = contributions[0]['from_city'] if contributions and 'from_city' in contributions[0] else None
                
                troops_to_return[player_id] = {
                    'from_city': from_city,
                    'units': surviving_units,
                    'heroes': contributions[0].get('heroes', []) if contributions else []
                }
                
                print(f"🛡️ [BATTLE_END_V2] Défenseur {player_id}: {initial_units} - {units_lost} = {surviving_units} + {contributions[0].get('heroes', []) if contributions else []}")
            
            print(f"📋 [BATTLE_END_V2] Récapitulatif troupes survivantes à renvoyer: {troops_to_return}")
            
            # =================================================================
            # 3. CRÉDITER LES UNITÉS DANS SAVEGAME.JSON (GARNISON)
            # =================================================================
            savegame_data = self._load_json('savegame.json')
            
            if not savegame_data.get('cities'):
                return {
                    'success': False,
                    'error': 'Aucune donnée de villes trouvée dans savegame.json'
                }
            
            cities_updated = 0
            for player_id, troop_data in troops_to_return.items():
                from_city = troop_data['from_city']
                
                # Trouver la ville dans savegame
                city_found = False
                for city in savegame_data['cities']:
                    if city['id'] == from_city and city['owner'] == player_id:
                        city_found = True
                        
                        # Initialiser military si nécessaire
                        if 'military' not in city:
                            city['military'] = {}
                        if 'garrison' not in city['military']:
                            city['military']['garrison'] = {}
                        
                        # Créditer les unités dans garrison (pas dans units)
                        # Nouvelle structure: garrison[player_id][unit_type]
                        garrison = city['military']['garrison']
                        if player_id not in garrison:
                            garrison[player_id] = {}
                        
                        for unit_type, count in troop_data['units'].items():
                            if unit_type not in garrison[player_id]:
                                garrison[player_id][unit_type] = {"quantity": 0}
                            
                            current_count = garrison[player_id][unit_type].get('quantity', 0)
                            garrison[player_id][unit_type]['quantity'] = current_count + count
                            print(f"💰 [BATTLE_END_V2] {from_city}: +{count} {unit_type} dans garrison[{player_id}] (total: {current_count + count})")
                        
                        # Créditer les héros et remettre leur statut à 'garrison'
                        if 'heroes' not in city['military']:
                            city['military']['heroes'] = {}
                        
                        for hero_id in troop_data['heroes']:
                            if hero_id in city['military']['heroes']:
                                # Le héros existe déjà, remettre son statut à garrison
                                city['military']['heroes'][hero_id]['status'] = 'garrison'
                                print(f"👑 [BATTLE_END_V2] {from_city}: héros {hero_id} remis en garrison")
                            else:
                                print(f"⚠️ [BATTLE_END_V2] {from_city}: héros {hero_id} non trouvé dans la ville")
                        
                        cities_updated += 1
                        break
                
                if not city_found:
                    print(f"⚠️ [BATTLE_END_V2] Ville {from_city} non trouvée pour {player_id}")
            
            # Sauvegarder savegame
            if not self._save_json('savegame.json', savegame_data):
                return {
                    'success': False,
                    'error': 'Erreur lors de la sauvegarde du savegame'
                }
            
            print(f"✅ [BATTLE_END_V2] {cities_updated} villes mises à jour dans savegame")
            
            # =================================================================
            # 4. CRÉER RAPPORT DE BATAILLE
            # =================================================================
            battle_reports = self._load_json('battle_reports.json')
            
            # Initialiser la structure si fichier vide
            if not battle_reports or 'reports' not in battle_reports:
                battle_reports = {'reports': []}
            
            report_id = f"report_v2_{battle_id}_{int(time.time())}"
            
            battle_report = {
                'id': report_id,
                'battle_id': battle_id,
                'version': '2.0',
                'timestamp': int(time.time()),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'location': battlefield['location'],
                'participants': battlefield['participants'],
                'outcome': 'bataille_terminee_v2',
                'troops_returned': {
                    player_id: {
                        'to_city': data['from_city'],
                        'units_returned': data['units'],
                        'heroes_returned': data['heroes']
                    }
                    for player_id, data in troops_to_return.items()
                },
                'summary': f"Bataille V2 a {battlefield['location']} terminee. {len(troops_to_return)} joueurs ont recupere leurs troupes."
            }
            
            battle_reports['reports'].append(battle_report)
            print(f"📋 [BATTLE_END_V2] Création rapport: {report_id}")
            
            if not self._save_json('battle_reports.json', battle_reports):
                print(f"❌ [BATTLE_END_V2] Erreur sauvegarde rapport: {report_id}")
                return {
                    'success': False,
                    'error': 'Erreur lors de la création du rapport'
                }
            
            print(f"✅ [BATTLE_END_V2] Rapport créé et sauvegardé: {report_id}")
            
            # =================================================================
            # 4.1 MISE À JOUR DES STATISTIQUES JOUEURS ET HÉROS
            # =================================================================
            try:
                from app.battle.battle_victory_manager import BattleVictoryManager
                victory_manager = BattleVictoryManager()
                
                # Récupérer le winner_team depuis le battlefield
                battle_result = battlefield.get('battle_result', {})
                winner_team = battle_result.get('winner_team', '')
                
                if not winner_team:
                    # Si pas encore de résultat, vérifier les conditions de victoire
                    has_winner, winner_team, victory_type = victory_manager.check_all_victory_conditions(battle_id)
                    if has_winner:
                        # Sauvegarder le résultat
                        victory_manager.save_battle_result(battle_id, winner_team, victory_type)
                        print(f"✅ [BATTLE_END_V2] Victoire détectée: {winner_team} par {victory_type}")
                
                location = battlefield.get('location', '')
                is_barbarian_village = location.startswith('wild_camp_')
                
                if winner_team:
                    player_stats_result = victory_manager.update_player_stats_from_battle(battlefield, winner_team, is_barbarian_village)
                    hero_stats_result = victory_manager.update_hero_stats_from_battle(battlefield, winner_team)
                    
                    if not player_stats_result:
                        print(f"⚠️ [BATTLE_END_V2] Erreur mise à jour stats joueurs (non bloquant)")
                    else:
                        print(f"✅ [BATTLE_END_V2] Stats joueurs mises à jour")
                        
                    if not hero_stats_result:
                        print(f"⚠️ [BATTLE_END_V2] Erreur mise à jour stats héros (non bloquant)")
                    else:
                        print(f"✅ [BATTLE_END_V2] Stats héros mises à jour")
                else:
                    print(f"⚠️ [BATTLE_END_V2] Aucun vainqueur déterminé, stats non mises à jour")
                    
            except Exception as e:
                print(f"⚠️ [BATTLE_END_V2] Erreur mise à jour stats: {e}")
            
            # =================================================================
            # 5. SUPPRIMER LA BATTLEFIELD (NOUVELLE STRUCTURE V2)
            # =================================================================
            if battle_id in battlefields_data:
                del battlefields_data[battle_id]
                
                if not self._save_json('battlefields_v2.json', battlefields_data):
                    return {
                        'success': False,
                        'error': 'Erreur lors de la suppression de la battlefield'
                    }
                
                print(f"🗑️ [BATTLE_END_V2] Battlefield {battle_id} supprimée avec nouvelle structure")
            
            # =================================================================
            # 5.1 SUPPRIMER AUSSI DE BATTLESV2.JSON (SYNCHRONISATION)
            # =================================================================
            battlesv2_data = self._load_json('battlesv2.json')
            if battle_id in battlesv2_data:
                del battlesv2_data[battle_id]
                
                if not self._save_json('battlesv2.json', battlesv2_data):
                    return {
                        'success': False,
                        'error': 'Erreur lors de la suppression de battlesv2.json'
                    }
                
                print(f"🗑️ [BATTLE_END_V2] Battle {battle_id} supprimée aussi de battlesv2.json")
            else:
                print(f"ℹ️ [BATTLE_END_V2] Battle {battle_id} non trouvée dans battlesv2.json (normal si bataille ancienne)")
            
            # =================================================================
            # 6. RÉPONSE DE SUCCÈS
            # =================================================================
            return {
                'success': True,
                'message': f'Bataille V2 {battle_id} terminée avec succès',
                'battle_id': battle_id,
                'troops_returned': troops_to_return,
                'report_id': report_id,
                'cities_updated': cities_updated
            }
            
        except Exception as e:
            print(f"❌ [BATTLE_END_V2] Erreur inattendue: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Erreur inattendue: {str(e)}'
            }
    
