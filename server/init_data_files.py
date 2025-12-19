"""
Script d'initialisation des fichiers de données au démarrage
Crée les fichiers JSON vides s'ils n'existent pas
"""
import os
import json

# Dossier des sauvegardes (monté sur volume Railway)
GAMEDATA_DIR = os.path.join(os.path.dirname(__file__), 'gamedata')

# Fichiers de sauvegarde à initialiser
SAVE_FILES = [
    'players.json',
    'savegame.json',
    'player_quests.json',
    'player_heroes.json',
    'player_profiles.json',
    'player_unit_improvements.json',
    'messages.json',
    'notifications.json',
    'battlefields_v2.json',
    'battlesv2.json',
    'battle_reports.json',
    'battle_replays.json',
    'transports.json',
    'transport_history.json',
    'market.json'
]

def init_data_files():
    """Initialise les fichiers de données s'ils n'existent pas"""
    # Créer le dossier gamedata s'il n'existe pas
    os.makedirs(GAMEDATA_DIR, exist_ok=True)
    
    # Créer chaque fichier JSON vide s'il n'existe pas
    for filename in SAVE_FILES:
        filepath = os.path.join(GAMEDATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"📝 Création de {filename}...")
            # Initialiser avec structure par défaut selon le type
            if filename == 'players.json':
                default_data = {}
            elif filename == 'savegame.json':
                default_data = {"cities": [], "timestamp": 0}
            elif filename.endswith('_v2.json'):
                default_data = []
            else:
                default_data = [] if filename.endswith('s.json') else {}
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    init_data_files()
