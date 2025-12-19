import json

# Charger le savegame
with open('data/savegame.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Ajouter wild_camp_level à toutes les villes qui ne l'ont pas
cities_updated = 0
for city in data.get('cities', []):
    if 'wild_camp_level' not in city:
        city['wild_camp_level'] = 1
        cities_updated += 1
        print(f"✅ {city['id']} ({city['name']}) - wild_camp_level = 1")

# Sauvegarder
with open('data/savegame.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n✅ {cities_updated} villes mises à jour avec wild_camp_level = 1")


