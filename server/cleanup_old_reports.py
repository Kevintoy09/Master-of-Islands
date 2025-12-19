"""
Script de nettoyage des fichiers historiques trop volumineux
Garde seulement les N dernières entrées pour battle_reports et transport_history
"""
import json
import os
from datetime import datetime

GAMEDATA_PATH = os.path.join(os.path.dirname(__file__), 'gamedata')

def cleanup_battle_reports(keep_last=50):
    """Garde seulement les N derniers rapports de bataille"""
    filepath = os.path.join(GAMEDATA_PATH, 'battle_reports.json')
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        reports = data.get('reports', [])
        original_count = len(reports)
        
        if original_count > keep_last:
            # Trier par timestamp décroissant et garder les N derniers
            sorted_reports = sorted(reports, key=lambda x: x.get('timestamp', 0), reverse=True)
            data['reports'] = sorted_reports[:keep_last]
            
            # Sauvegarder
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ battle_reports.json: {original_count} → {keep_last} rapports")
            return original_count - keep_last
        else:
            print(f"ℹ️ battle_reports.json: {original_count} rapports (aucun nettoyage nécessaire)")
            return 0
    except Exception as e:
        print(f"❌ Erreur battle_reports: {e}")
        return 0

def cleanup_transport_history(keep_last=50):
    """Garde seulement les N dernières entrées de transport_history (OPTIMISÉ)"""
    filepath = os.path.join(GAMEDATA_PATH, 'transport_history.json')
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Le fichier contient {"transport_history": [...]}
        history_list = data.get('transport_history', [])
        original_count = len(history_list)
        
        if original_count > keep_last:
            # Trier par date de complétion décroissante
            def get_timestamp(item):
                try:
                    timeline = item.get('timeline', {})
                    return timeline.get('completed', timeline.get('archived_at', 0))
                except:
                    return 0
            
            sorted_history = sorted(history_list, key=get_timestamp, reverse=True)
            data['transport_history'] = sorted_history[:keep_last]
            
            # Sauvegarder
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ transport_history.json: {original_count} → {keep_last} entrées")
            return original_count - keep_last
        else:
            print(f"ℹ️ transport_history.json: {original_count} entrées (aucun nettoyage nécessaire)")
            return 0
    except Exception as e:
        print(f"❌ Erreur transport_history: {e}")
        return 0

def cleanup_battle_notifications(keep_last=50):
    """Garde seulement les N dernières notifications de bataille"""
    filepath = os.path.join(GAMEDATA_PATH, 'battle_notifications.json')
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_count = len(data)
        
        if original_count > keep_last:
            # Convertir en liste
            items = [(k, v) for k, v in data.items()]
            
            # Trier par timestamp
            def get_timestamp(item):
                try:
                    return item[1].get('timestamp', 0)
                except:
                    return 0
            
            sorted_items = sorted(items, key=get_timestamp, reverse=True)
            
            # Garder les N derniers
            new_data = {k: v for k, v in sorted_items[:keep_last]}
            
            # Sauvegarder
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ battle_notifications.json: {original_count} → {keep_last} entrées")
            return original_count - keep_last
        else:
            print(f"ℹ️ battle_notifications.json: {original_count} entrées (aucun nettoyage nécessaire)")
            return 0
    except Exception as e:
        print(f"❌ Erreur battle_notifications: {e}")
        return 0

if __name__ == '__main__':
    print("🧹 Nettoyage des fichiers historiques...\n")
    
    total_removed = 0
    total_removed += cleanup_battle_reports(keep_last=50)
    total_removed += cleanup_transport_history(keep_last=20)  # Réduit à 20
    total_removed += cleanup_battle_notifications(keep_last=30)  # Réduit à 30
    
    print(f"\n✨ Nettoyage terminé ! {total_removed} entrées supprimées au total.")
    print("💡 Le jeu devrait être beaucoup plus rapide maintenant !")
