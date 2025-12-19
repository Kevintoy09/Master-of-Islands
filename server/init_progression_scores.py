"""
Script d'initialisation des scores de progression pour tous les joueurs.

Lance ce script pour calculer les scores initiaux de tous les joueurs :
    python init_progression_scores.py
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data_manager import DataManager
from app.services.player_progression_service import PlayerProgressionService

def main():
    """Initialise les scores de tous les joueurs"""
    print("🔄 Initialisation des scores de progression...")
    print()
    
    # Créer les services
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_manager = DataManager(base_dir)
    progression_service = PlayerProgressionService(data_manager)
    
    # Charger les joueurs
    players_data = data_manager.load_players()
    players = players_data.get('players', [])
    
    print(f"📊 {len(players)} joueur(s) trouvé(s)")
    print()
    
    # Mettre à jour chaque joueur
    for player in players:
        player_id = player.get('id')
        username = player.get('username', 'N/A')
        
        print(f"⏳ Calcul des scores pour {username} ({player_id})...")
        
        # Calculer les scores
        construction_points = progression_service.calculate_construction_points(player_id)
        research_points_invested = progression_service.calculate_research_points_invested(player_id)
        
        print(f"   🏗️  Points de construction: {construction_points}")
        print(f"   🔬 Points de recherche investis: {research_points_invested}")
        
        # Mettre à jour
        result = progression_service.update_player_scores(player_id)
        
        if result.get('success'):
            print(f"   ✅ Scores mis à jour !")
        else:
            print(f"   ❌ Erreur: {result.get('message')}")
        
        print()
    
    print("✨ Initialisation terminée !")
    print()
    print("📖 Les scores sont maintenant disponibles dans players.json")
    print("   - construction_points: Points basés sur les niveaux de bâtiments")
    print("   - research_points_invested: Total des points de recherche dépensés + actuels")

if __name__ == '__main__':
    main()
