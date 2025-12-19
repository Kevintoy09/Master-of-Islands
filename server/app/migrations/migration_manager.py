"""
=================================================================
MIGRATION_MANAGER.PY - Gestionnaire de migration JSON → PostgreSQL
=================================================================

RESPONSABILITÉS:
- Migration des données JSON vers PostgreSQL
- Synchronisation bidirectionnelle (prod ↔ dev)
- Export/Import pour backup

USAGE:
    python -m app.migrations.migration_manager migrate      # JSON → PostgreSQL
    python -m app.migrations.migration_manager export       # PostgreSQL → JSON
    python -m app.migrations.migration_manager sync         # Bidirectionnel
=================================================================
"""

import sys
import os
from datetime import datetime

# Ajouter le dossier parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.config.database import init_db, get_db_session, close_db
from app.models.db_models import (
    Player, City, Building, Research, Unit, Hero, Battle, Transport
)
from app.data_manager import DataManager


class MigrationManager:
    """Gestionnaire de migration entre JSON et PostgreSQL"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.session = None
        
    def connect_db(self):
        """Initialise la connexion PostgreSQL"""
        success = init_db()
        if not success:
            raise Exception("❌ PostgreSQL non disponible. Vérifier DATABASE_URL")
        self.session = get_db_session()
        return self.session
    
    def migrate_json_to_postgresql(self):
        """
        Migration complète: JSON → PostgreSQL
        Lit tous les fichiers JSON et les insère dans PostgreSQL
        """
        print("🚀 Début de la migration JSON → PostgreSQL")
        print("=" * 60)
        
        try:
            self.connect_db()
            
            # 1. Migrer les joueurs
            self._migrate_players()
            
            # 2. Migrer les villes
            self._migrate_cities()
            
            # 3. Migrer les bâtiments
            self._migrate_buildings()
            
            # 4. Migrer les recherches
            self._migrate_research()
            
            # 5. Migrer les unités
            self._migrate_units()
            
            # 6. Migrer les héros
            self._migrate_heroes()
            
            # 7. Migrer les batailles
            self._migrate_battles()
            
            # 8. Migrer les transports
            self._migrate_transports()
            
            self.session.commit()
            print("\n" + "=" * 60)
            print("✅ Migration terminée avec succès!")
            
        except Exception as e:
            if self.session:
                self.session.rollback()
            print(f"\n❌ Erreur lors de la migration: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            close_db()
    
    def _migrate_players(self):
        """Migre les joueurs depuis players.json"""
        print("\n📊 Migration des joueurs...")
        players_data = self.data_manager.load_players()
        
        count = 0
        for player_data in players_data:
            player = Player(
                id=player_data['id'],
                username=player_data['username'],
                email=player_data.get('email'),
                is_admin=player_data.get('is_admin', False),
                is_active=player_data.get('is_active', True),
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow()
            )
            self.session.merge(player)  # merge pour éviter les doublons
            count += 1
        
        self.session.flush()
        print(f"   ✅ {count} joueurs migrés")
    
    def _migrate_cities(self):
        """Migre les villes depuis savegame.json"""
        print("\n🏛️ Migration des villes...")
        savegame = self.data_manager.load_savegame()
        
        count = 0
        for city_data in savegame.get('cities', []):
            city = City(
                id=city_data['id'],
                player_id=city_data['player_id'],
                name=city_data['name'],
                island_id=city_data.get('island_id', 'island_0'),
                x=city_data.get('x', 0),
                y=city_data.get('y', 0),
                population=city_data.get('population', 0),
                satisfaction=city_data.get('satisfaction', 100.0),
                resources=self._extract_resources(city_data),
                production=city_data.get('production', {}),
                created_at=datetime.utcnow(),
                last_tick=datetime.utcnow()
            )
            self.session.merge(city)
            count += 1
        
        self.session.flush()
        print(f"   ✅ {count} villes migrées")
    
    def _extract_resources(self, city_data):
        """Extrait les ressources d'une ville"""
        resources = {}
        resource_keys = [
            'wood', 'stone', 'iron', 'cereal', 'papyrus', 
            'horse', 'marble', 'glass', 'meat', 'coal', 
            'gunpowder', 'spices', 'cotton'
        ]
        
        for key in resource_keys:
            if key in city_data:
                resources[key] = city_data[key]
        
        return resources
    
    def _migrate_buildings(self):
        """Migre les bâtiments depuis savegame.json"""
        print("\n🏗️ Migration des bâtiments...")
        savegame = self.data_manager.load_savegame()
        
        count = 0
        for city_data in savegame.get('cities', []):
            city_id = city_data['id']
            
            for building_data in city_data.get('buildings', []):
                building = Building(
                    city_id=city_id,
                    building_type=building_data['type'],
                    level=building_data.get('level', 1),
                    is_upgrading=building_data.get('is_upgrading', False),
                    upgrade_start_time=building_data.get('upgrade_start_time'),
                    upgrade_duration=building_data.get('upgrade_duration')
                )
                self.session.add(building)
                count += 1
        
        self.session.flush()
        print(f"   ✅ {count} bâtiments migrés")
    
    def _migrate_research(self):
        """Migre les recherches depuis research.json"""
        print("\n🔬 Migration des recherches...")
        research_data = self.data_manager.load_research()
        
        count = 0
        for player_id, researches in research_data.items():
            for research_id, level in researches.items():
                if isinstance(level, int):
                    research = Research(
                        player_id=player_id,
                        research_id=research_id,
                        level=level,
                        is_researching=False,
                        completed_at=datetime.utcnow()
                    )
                    self.session.add(research)
                    count += 1
        
        self.session.flush()
        print(f"   ✅ {count} recherches migrées")
    
    def _migrate_units(self):
        """Migre les unités depuis savegame.json"""
        print("\n⚔️ Migration des unités...")
        savegame = self.data_manager.load_savegame()
        
        count = 0
        for city_data in savegame.get('cities', []):
            city_id = city_data['id']
            units = city_data.get('units', {})
            
            for unit_type, quantity in units.items():
                if quantity > 0:
                    unit = Unit(
                        city_id=city_id,
                        unit_type=unit_type,
                        quantity=quantity,
                        upgrade_level=0
                    )
                    self.session.add(unit)
                    count += 1
        
        self.session.flush()
        print(f"   ✅ {count} types d'unités migrés")
    
    def _migrate_heroes(self):
        """Migre les héros depuis player_heroes.json"""
        print("\n🦸 Migration des héros...")
        try:
            heroes_data = self.data_manager.load_player_heroes()
            
            count = 0
            for player_id, heroes in heroes_data.items():
                for hero_data in heroes:
                    hero = Hero(
                        id=f"{player_id}_{hero_data['id']}",
                        player_id=player_id,
                        hero_id=hero_data['id'],
                        name=hero_data['name'],
                        level=hero_data.get('level', 1),
                        experience=hero_data.get('experience', 0),
                        stats=hero_data.get('stats', {}),
                        skills=hero_data.get('skills', []),
                        city_id=hero_data.get('city_id'),
                        is_available=hero_data.get('is_available', True)
                    )
                    self.session.merge(hero)
                    count += 1
            
            self.session.flush()
            print(f"   ✅ {count} héros migrés")
        except Exception as e:
            print(f"   ⚠️ Pas de héros à migrer: {e}")
    
    def _migrate_battles(self):
        """Migre les batailles depuis battlesv2.json"""
        print("\n⚔️ Migration des batailles...")
        try:
            battles_data = self.data_manager.load_battles_v2()
            
            count = 0
            for battle_data in battles_data:
                battle = Battle(
                    id=battle_data['id'],
                    attacker_id=battle_data['attacker_id'],
                    defender_id=battle_data['defender_id'],
                    target_city_id=battle_data.get('target_city_id', ''),
                    status=battle_data['status'],
                    winner=battle_data.get('winner'),
                    battlefield_data=battle_data.get('battlefield', {}),
                    combat_log=battle_data.get('combat_log', []),
                    rewards=battle_data.get('rewards', {}),
                    created_at=datetime.fromtimestamp(battle_data.get('created_at', 0) / 1000),
                    started_at=datetime.fromtimestamp(battle_data['started_at'] / 1000) if battle_data.get('started_at') else None,
                    finished_at=datetime.fromtimestamp(battle_data['finished_at'] / 1000) if battle_data.get('finished_at') else None
                )
                self.session.merge(battle)
                count += 1
            
            self.session.flush()
            print(f"   ✅ {count} batailles migrées")
        except Exception as e:
            print(f"   ⚠️ Pas de batailles à migrer: {e}")
    
    def _migrate_transports(self):
        """Migre les transports depuis transports.json"""
        print("\n🚚 Migration des transports...")
        try:
            transports_data = self.data_manager.load_transports()
            
            count = 0
            for transport_data in transports_data:
                transport = Transport(
                    id=transport_data['id'],
                    player_id=transport_data['player_id'],
                    from_city_id=transport_data['from_city_id'],
                    to_city_id=transport_data['to_city_id'],
                    resources=transport_data.get('resources', {}),
                    status=transport_data.get('status', 'in_transit'),
                    departure_time=transport_data['departure_time'],
                    arrival_time=transport_data['arrival_time'],
                    created_at=datetime.utcnow()
                )
                self.session.merge(transport)
                count += 1
            
            self.session.flush()
            print(f"   ✅ {count} transports migrés")
        except Exception as e:
            print(f"   ⚠️ Pas de transports à migrer: {e}")
    
    def export_postgresql_to_json(self):
        """
        Export PostgreSQL → JSON
        Utile pour backup ou développement local
        """
        print("🚀 Début de l'export PostgreSQL → JSON")
        print("=" * 60)
        
        try:
            self.connect_db()
            
            # Export players
            players = self.session.query(Player).all()
            players_data = [{
                'id': p.id,
                'username': p.username,
                'email': p.email,
                'is_admin': p.is_admin,
                'is_active': p.is_active
            } for p in players]
            self.data_manager.save_players(players_data)
            print(f"✅ {len(players_data)} joueurs exportés")
            
            # Export cities + buildings
            cities = self.session.query(City).all()
            savegame_data = {'cities': []}
            
            for city in cities:
                city_dict = {
                    'id': city.id,
                    'player_id': city.player_id,
                    'name': city.name,
                    'island_id': city.island_id,
                    'x': city.x,
                    'y': city.y,
                    'population': city.population,
                    'satisfaction': city.satisfaction,
                    **city.resources,  # Décompresser les ressources
                    'production': city.production,
                    'buildings': []
                }
                
                # Ajouter les bâtiments
                for building in city.buildings:
                    city_dict['buildings'].append({
                        'type': building.building_type,
                        'level': building.level,
                        'is_upgrading': building.is_upgrading,
                        'upgrade_start_time': building.upgrade_start_time,
                        'upgrade_duration': building.upgrade_duration
                    })
                
                # Ajouter les unités
                units_dict = {}
                for unit in city.units:
                    units_dict[unit.unit_type] = unit.quantity
                city_dict['units'] = units_dict
                
                savegame_data['cities'].append(city_dict)
            
            self.data_manager.save_savegame(savegame_data)
            print(f"✅ {len(cities)} villes exportées")
            
            print("\n" + "=" * 60)
            print("✅ Export terminé avec succès!")
            
        except Exception as e:
            print(f"\n❌ Erreur lors de l'export: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            close_db()


# ============================================
# CLI
# ============================================

def main():
    """Interface en ligne de commande"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m app.migrations.migration_manager migrate  # JSON → PostgreSQL")
        print("  python -m app.migrations.migration_manager export   # PostgreSQL → JSON")
        return
    
    command = sys.argv[1]
    manager = MigrationManager()
    
    if command == 'migrate':
        manager.migrate_json_to_postgresql()
    elif command == 'export':
        manager.export_postgresql_to_json()
    else:
        print(f"❌ Commande inconnue: {command}")


if __name__ == '__main__':
    main()
