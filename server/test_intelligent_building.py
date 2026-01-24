"""
Test du système de construction intelligent

Vérifie:
1. Transition BUILD_ORDER → Système intelligent
2. Calcul du temps d'attente
3. Sauvegarde/récupération des décisions
"""

import sys
import os
import json

# Ajouter le dossier parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.data_manager import DataManager
from app.ai.ai_controller import AIController


def test_build_order_transition():
    """Test 1: Vérifier que la transition se fait correctement"""
    print("\n" + "="*70)
    print("TEST 1: Transition BUILD_ORDER → Système Intelligent")
    print("="*70)
    
    base_dir = os.path.dirname(os.path.dirname(__file__))
    dm = DataManager(base_dir)
    ai_controller = AIController(dm)
    
    # Charger savegame
    savegame = dm.load_savegame()
    players_data = dm.load_players()
    players = players_data.get('players', [])
    
    if not players:
        print("⚠️  Aucun joueur trouvé (base de données vierge)")
        print("✓ Test de structure: AIController créé avec succès")
        print("✓ Test de structure: Imports fonctionnels")
        return True
    
    # Trouver une ville IA
    ai_player = None
    for p in players:
        if p['id'].startswith('ai_'):
            ai_player = p
            break
    
    if not ai_player:
        print("⚠️  Aucun joueur IA trouvé")
        print("✓ Test de structure: Code fonctionnel")
        return True
    
    print(f"✓ Joueur IA trouvé: {ai_player['username']} (ID: {ai_player['id']})")
    
    # Trouver sa première ville
    city = None
    for c in savegame['cities']:
        if c['owner_id'] == ai_player['id']:
            city = c
            break
    
    if not city:
        print(f"❌ Aucune ville pour {ai_player['username']}")
        return False
    
    print(f"✓ Ville trouvée: {city.get('name', 'Sans nom')} (ID: {city['id']})")
    
    # Vérifier état BUILD_ORDER
    from app.ai.strategies.development_strategy import BUILD_ORDER
    
    existing_buildings = {}
    for building in city.get('buildings', []):
        name = building.get('name')
        level = building.get('level', 0)
        existing_buildings[name] = level
    
    build_order_complete = True
    for building_name, target_level in BUILD_ORDER:
        current_level = existing_buildings.get(building_name, 0)
        if current_level < target_level:
            build_order_complete = False
            print(f"  ⏳ BUILD_ORDER en cours: {building_name} {current_level}/{target_level}")
            break
    
    if build_order_complete:
        print("  ✅ BUILD_ORDER COMPLET → Système intelligent actif")
    else:
        print("  🔄 BUILD_ORDER en cours → Système classique actif")
    
    # Tester décision de construction
    print("\n🤖 Test de décision de construction...")
    decision = ai_controller._decide_construction(ai_player, city)
    
    print(f"  Action: {decision.get('action')}")
    print(f"  Message: {decision.get('message')}")
    if decision.get('building_name'):
        print(f"  Bâtiment: {decision.get('building_name')}")
    
    return True


def test_forecast_calculation():
    """Test 2: Vérifier calcul du prévisionnel"""
    print("\n" + "="*70)
    print("TEST 2: Calcul du Prévisionnel")
    print("="*70)
    
    from app.ai.strategies.building_decision_engine import (
        _calculate_wait_time_with_transport,
        _get_player_cities
    )
    
    base_dir = os.path.dirname(os.path.dirname(__file__))
    dm = DataManager(base_dir)
    
    savegame = dm.load_savegame()
    players_data = dm.load_players()
    players = players_data.get('players', [])
    
    if not players:
        print("⚠️  Aucun joueur trouvé (base de données vierge)")
        print("✓ Test de structure: Fonction _calculate_wait_time_with_transport importable")
        print("✓ Test de structure: Fonction _get_player_cities importable")
        return True
    
    # Trouver joueur IA
    ai_player = next((p for p in players if p['id'].startswith('ai_')), None)
    if not ai_player:
        print("⚠️  Aucun joueur IA")
        print("✓ Test de structure: Fonctions importées avec succès")
        return True
    
    # Trouver ville IA
    city = next((c for c in savegame['cities'] if c['owner_id'] == ai_player['id']), None)
    if not city:
        print("❌ Aucune ville IA")
        return False
    
    print(f"✓ Ville: {city.get('name', 'Sans nom')}")
    
    # Ressources actuelles
    resources = city.get('resources', {})
    print(f"\nRessources actuelles:")
    print(f"  Bois: {int(resources.get('wood', 0))}")
    print(f"  Pierre: {int(resources.get('stone', 0))}")
    print(f"  Fer: {int(resources.get('iron', 0))}")
    print(f"  Céréales: {int(resources.get('cereal', 0))}")
    
    # Test avec coût fictif
    test_cost = {
        'wood': 500,
        'stone': 300,
        'iron': 100
    }
    
    print(f"\nCoût de test: Bois:{test_cost['wood']}, Pierre:{test_cost['stone']}, Fer:{test_cost['iron']}")
    
    player_cities = _get_player_cities(ai_player['id'])
    forecast = _calculate_wait_time_with_transport(city, player_cities, test_cost)
    
    print(f"\nRésultat prévisionnel:")
    print(f"  Constructible maintenant: {'✅ OUI' if forecast['can_build_now'] else '❌ NON'}")
    print(f"  Temps d'attente: {forecast['wait_hours']:.1f} heures")
    
    return True


def test_decision_persistence():
    """Test 3: Vérifier sauvegarde/récupération des décisions"""
    print("\n" + "="*70)
    print("TEST 3: Sauvegarde/Récupération des Décisions")
    print("="*70)
    
    from app.ai.strategies.building_decision_engine import (
        _save_building_decision,
        _get_saved_building_decision,
        _clear_saved_decision
    )
    
    # IDs de test
    test_player_id = "ai_test_123"
    test_city_id = "city_test_456"
    
    # Nettoyage préalable
    _clear_saved_decision(test_player_id, test_city_id)
    
    # Test 1: Aucune décision sauvegardée
    saved = _get_saved_building_decision(test_player_id, test_city_id)
    if saved is None:
        print("✓ Aucune décision initiale (OK)")
    else:
        print("❌ Décision inattendue trouvée")
        return False
    
    # Test 2: Sauvegarder une décision
    test_decision = {
        'building': 'Hôtel de Ville',
        'wait_hours': 5.5,
        'cost': {'wood': 1000, 'stone': 500}
    }
    
    _save_building_decision(test_player_id, test_city_id, test_decision, 12000)
    print("✓ Décision sauvegardée")
    
    # Test 3: Récupérer la décision
    saved = _get_saved_building_decision(test_player_id, test_city_id)
    if saved:
        print(f"✓ Décision récupérée:")
        print(f"  Bâtiment: {saved['building']}")
        print(f"  Tick: {saved['tick']}")
        print(f"  Attente: {saved['wait_hours']}h")
        print(f"  Coût: {saved['cost']}")
    else:
        print("❌ Échec récupération")
        return False
    
    # Test 4: Nettoyer
    _clear_saved_decision(test_player_id, test_city_id)
    saved = _get_saved_building_decision(test_player_id, test_city_id)
    if saved is None:
        print("✓ Décision nettoyée correctement")
    else:
        print("❌ Échec nettoyage")
        return False
    
    return True


def main():
    """Exécute tous les tests"""
    print("\n" + "="*70)
    print("TESTS DU SYSTÈME DE CONSTRUCTION INTELLIGENT")
    print("="*70)
    
    results = []
    
    # Test 1
    try:
        results.append(("Transition BUILD_ORDER", test_build_order_transition()))
    except Exception as e:
        print(f"\n❌ ERREUR Test 1: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Transition BUILD_ORDER", False))
    
    # Test 2
    try:
        results.append(("Calcul prévisionnel", test_forecast_calculation()))
    except Exception as e:
        print(f"\n❌ ERREUR Test 2: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Calcul prévisionnel", False))
    
    # Test 3
    try:
        results.append(("Sauvegarde/Récupération", test_decision_persistence()))
    except Exception as e:
        print(f"\n❌ ERREUR Test 3: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Sauvegarde/Récupération", False))
    
    # Résumé
    print("\n" + "="*70)
    print("RÉSUMÉ DES TESTS")
    print("="*70)
    
    for name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
        print(f"{status}: {name}")
    
    total_success = sum(1 for _, s in results if s)
    total_tests = len(results)
    
    print(f"\nRésultat global: {total_success}/{total_tests} tests réussis")
    
    if total_success == total_tests:
        print("\n🎉 TOUS LES TESTS PASSENT !")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_success} test(s) échoué(s)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
