"""
Battle Loader Service - Service pour charger les batailles depuis les fichiers JSON
=================================================================================

Ce service charge les données de bataille depuis battlesv2.json et les retourne
au format attendu par le frontend.
"""

import json
import os
from app.config.paths import BATTLEFIELDS_V2_FILE, BATTLES_V2_FILE


class BattleLoaderService:
    """Service pour charger les batailles V2"""
    
    @staticmethod
    def load_battle_from_city(city_id):
        """Charger une bataille active pour une ville donnée"""
        try:
            print(f"🔍 [BattleLoader] Chargement bataille pour ville: {city_id}")
            
            print(f"🔍 [BattleLoader] Chemin battlefields: {BATTLEFIELDS_V2_FILE}")
            print(f"🔍 [BattleLoader] Chemin battles: {BATTLES_V2_FILE}")
            
            # D'abord chercher dans battlefields_v2.json
            if os.path.exists(BATTLEFIELDS_V2_FILE):
                with open(BATTLEFIELDS_V2_FILE, 'r', encoding='utf-8') as f:
                    battlefields_data = json.load(f)
                
                print(f"🔍 [BattleLoader] Battlefields trouvés: {list(battlefields_data.keys())}")
                
                # Chercher un battlefield dans cette ville
                for battlefield_id, battlefield in battlefields_data.items():
                    if battlefield.get('location') == city_id:
                        print(f"✅ [BattleLoader] Battlefield trouvé dans {city_id}: {battlefield_id}")
                        
                        # Créer les données de bataille à partir du battlefield
                        battle_data = {
                            'battleId': battlefield_id,
                            'id': battlefield_id,
                            'map': battlefield.get('map', 'default_working'),
                            'status': 'active',
                            'current_round': 1,
                            'current_player': 'attacker',
                            'location': city_id,
                            'created_at': battlefield.get('created_at'),
                            'participants': battlefield.get('participants', {}),
                            'forces': battlefield.get('forces', {})
                        }
                        
                        return battle_data
            
            # Si pas trouvé dans battlefields, chercher dans battles (ancien système)
            if os.path.exists(BATTLES_V2_FILE):
                with open(BATTLES_V2_FILE, 'r', encoding='utf-8') as f:
                    battles_data = json.load(f)
                
                print(f"🔍 [BattleLoader] Batailles trouvées: {list(battles_data.keys())}")
                
                # Chercher une bataille active
                for battle_id, battle in battles_data.items():
                    print(f"🔍 [BattleLoader] Vérification {battle_id} - current_round: {battle.get('current_round')}")
                    
                    # Une bataille est considérée active si elle a des rounds et des équipes
                    has_teams = battle.get('teams') and len(battle.get('teams', {})) > 0
                    has_rounds = battle.get('current_round', 0) >= 1
                    
                    if has_teams and has_rounds:
                        print(f"✅ [BattleLoader] Bataille active trouvée: {battle_id}")
                        
                        # Ajouter les IDs nécessaires
                        battle_with_id = battle.copy()
                        battle_with_id['battleId'] = battle_id
                        battle_with_id['id'] = battle_id
                        battle_with_id['map'] = battle_with_id.get('map', 'grande_carte')  # Valeur par défaut
                        
                        return battle_with_id
            
            print(f"❌ [BattleLoader] Aucune bataille active pour ville: {city_id}")
            return None
            
        except Exception as e:
            print(f"❌ [BattleLoader] Erreur: {str(e)}")
            return None
    
    @staticmethod
    def get_battlefield_bonuses(battle_id):
        """Récupérer les bonus de terrain (placeholder)"""
        print(f"🔍 [BattleLoader] Bonus demandés pour bataille: {battle_id}")
        # Pour l'instant, retourner des bonus par défaut
        return {
            "terrain_bonuses": {},
            "defensive_bonuses": {},
            "message": "Bonus de base appliqués"
        }

    @staticmethod
    def get_battle_moral(battle_id):
        """Récupérer le moral d'une bataille (placeholder)"""
        print(f"🔍 [BattleLoader] Moral demandé pour bataille: {battle_id}")
        # Pour l'instant, retourner un moral par défaut
        return {
            "battle_id": battle_id,
            "attacker_moral": 100,
            "defender_moral": 100,
            "message": "Moral de base"
        }

    @staticmethod
    def initialize_battle(data):
        """Initialiser une bataille (placeholder)"""
        print(f"🔍 [BattleLoader] Initialisation bataille avec données: {data}")
        return {
            "status": "initialized",
            "message": "Bataille initialisée avec succès",
            "attackerUnits": {},
            "defenderUnits": {}
        }