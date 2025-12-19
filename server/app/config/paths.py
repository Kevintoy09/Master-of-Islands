"""
Configuration centralisée des chemins de fichiers
Évite la confusion entre data/ (configs statiques) et gamedata/ (données dynamiques)
"""

import os

# Répertoire racine du serveur
SERVER_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Données statiques (configurations, templates)
STATIC_DATA_DIR = os.path.join(SERVER_DIR, 'data')

# Données dynamiques du jeu (savegames, batailles)
GAME_DATA_DIR = os.path.join(SERVER_DIR, 'gamedata')

# Fichiers de configuration statiques
UNIT_STATS_FILE = os.path.join(STATIC_DATA_DIR, 'unit_stats.json')
BUILDINGS_FILE = os.path.join(STATIC_DATA_DIR, 'buildings.json')
WILD_CAMPS_CONFIG_FILE = os.path.join(STATIC_DATA_DIR, 'wild_camps_config.json')
BARBARIAN_VILLAGES_CONFIG_FILE = os.path.join(STATIC_DATA_DIR, 'barbarian_villages_config.json')

# Fichiers de données dynamiques
SAVEGAME_FILE = os.path.join(GAME_DATA_DIR, 'savegame.json')
BATTLEFIELDS_V2_FILE = os.path.join(GAME_DATA_DIR, 'battlefields_v2.json')
BATTLES_V2_FILE = os.path.join(GAME_DATA_DIR, 'battlesv2.json')
PLAYERS_FILE = os.path.join(GAME_DATA_DIR, 'players.json')
PLAYER_HEROES_FILE = os.path.join(GAME_DATA_DIR, 'player_heroes.json')
PLAYER_QUESTS_FILE = os.path.join(GAME_DATA_DIR, 'player_quests.json')
