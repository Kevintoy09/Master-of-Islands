"""
Script pour nettoyer les doublons dans savegame.json
"""
import json
import os

savegame_path = os.path.join(os.path.dirname(__file__), 'gamedata', 'savegame.json')

# Charger le savegame
with open(savegame_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Supprimer les doublons de villes (garder la première occurrence de chaque ID)
cities = data.get('cities', [])
seen_ids = set()
unique_cities = []

for city in cities:
    city_id = city.get('id')
    if city_id and city_id not in seen_ids:
        seen_ids.add(city_id)
        unique_cities.append(city)
        print(f"✅ Conservé: {city_id} - {city.get('name')}")
    else:
        print(f"❌ Doublon supprimé: {city_id} - {city.get('name')}")

data['cities'] = unique_cities

print(f"\n📊 Résultat: {len(cities)} villes → {len(unique_cities)} villes uniques")

# Sauvegarder
with open(savegame_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Savegame nettoyé: {savegame_path}")
