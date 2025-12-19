"""Réduit le savegame aux 3 villes principales ET supprime les doublons"""
import json
import os

savegame_path = os.path.join(os.path.dirname(__file__), 'gamedata', 'savegame.json')

with open(savegame_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Garder seulement les 3 premières villes UNIQUES
keep_ids = ['city_id_93', 'city_id_1446', 'city_id_1445']
seen = set()
unique_cities = []

for city in data['cities']:
    city_id = city['id']
    if city_id in keep_ids and city_id not in seen:
        seen.add(city_id)
        unique_cities.append(city)

data['cities'] = unique_cities

with open(savegame_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Savegame réduit à {len(data['cities'])} villes UNIQUES:")
for city in data['cities']:
    print(f"  - {city['id']}: {city['name']}")
