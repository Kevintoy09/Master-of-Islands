"""
Script de synchronisation pour maintenir data/savegame.json à jour
Doit être appelé par DataManager après chaque sauvegarde
"""
import shutil
import os

def sync_savegames():
    """Copie gamedata/savegame.json vers data/savegame.json pour compatibilité SaveService"""
    source = os.path.join(os.path.dirname(__file__), 'gamedata', 'savegame.json')
    dest = os.path.join(os.path.dirname(__file__), 'data', 'savegame.json')
    
    if os.path.exists(source):
        shutil.copy2(source, dest)
        # print(f"🔄 Sync: gamedata/savegame.json → data/savegame.json")
    else:
        print(f"⚠️ Source manquante: {source}")

if __name__ == '__main__':
    sync_savegames()
    print("✅ Synchronisation manuelle terminée")
