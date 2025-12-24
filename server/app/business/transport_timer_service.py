"""
TRANSPORT_TIMER_SERVICE.PY - Service de gestion automatique des états de transport
==================================================================================

RESPONSABILITÉS:
- Mise à jour automatique des transports toutes les secondes
- Transitions d'états : waiting → loading → traveling → returning → completed
- Gestion des files d'attente (démarrage automatique du transport suivant)
- Archivage automatique des transports terminés

LOGIQUE DES TRANSITIONS:
1. waiting → loading : Quand le port se libère
2. loading → traveling : Quand remaining_time atteint 0
3. traveling → returning/completed : Quand arrivée à destination
4. returning → completed : Quand retour terminé  
5. completed → archived : Déplacement vers transport_history.json

INTÉGRATION:
- Appelé par GameLoopManager toutes les secondes
- Thread-safe avec les autres services
==================================================================================
"""

import time
from typing import Dict, List, Any
from app.data_manager import DataManager
from app.business.notification_service import NotificationService

class TransportTimerService:
    
    TRANSPORT_STATES = {
        'WAITING': 'waiting',
        'LOADING': 'loading', 
        'TRAVELING': 'traveling',
        'RETURNING': 'returning',
        'COMPLETED': 'completed',
        'BATTLE_WAITING': 'battle_waiting',  # Statut pour les attaques en attente de fin de bataille
        'PROTECTION_WAITING': 'protection_waiting'  # Statut pour les protections en attente de rappel
    }
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.notification_service = NotificationService(data_manager)
        
    def update_all_transports(self) -> Dict[str, Any]:
        """
        Met à jour tous les transports actifs.
        Appelé toutes les secondes par GameLoopManager.
        
        Returns: {"updated": int, "completed": int, "started": int}
        """
        try:
            transports_data = self.data_manager.load_transports()
            if not transports_data or not transports_data.get('transports'):
                return {"updated": 0, "completed": 0, "started": 0}
            
            updated_count = 0
            completed_count = 0
            started_count = 0
            transports_to_remove = []
            
            current_time = time.time()
            
            # 1. METTRE À JOUR LES TIMERS ET TRANSITIONS
            for i, transport in enumerate(transports_data['transports']):
                if self._update_transport_timer(transport, current_time):
                    updated_count += 1
                
                # Marquer pour suppression si terminé
                if transport['status'] == self.TRANSPORT_STATES['COMPLETED']:
                    transports_to_remove.append(i)
                    completed_count += 1
            
            # 2. ARCHIVER LES TRANSPORTS TERMINÉS
            if transports_to_remove:
                self._archive_completed_transports(transports_data, transports_to_remove)
            
            # 3. DÉMARRER TRANSPORTS EN ATTENTE
            started_count = self._start_waiting_transports(transports_data, current_time)
            
            # 4. SAUVEGARDER
            if updated_count > 0 or completed_count > 0 or started_count > 0:
                self.data_manager.save_transports(transports_data, force_save=True)
            
            return {
                "updated": updated_count,
                "completed": completed_count, 
                "started": started_count
            }
            
        except Exception as e:
            print(f"❌ Erreur update_all_transports: {e}")
            return {"updated": 0, "completed": 0, "started": 0}
    
    def _update_transport_timer(self, transport: Dict[str, Any], current_time: float) -> bool:
        """
        Met à jour le timer d'un transport et effectue les transitions d'états.
        
        Returns: True si le transport a été modifié
        """
        status = transport['status']
        
        # Ignorer les transports terminés, en attente, ou en attente de bataille
        if status in [self.TRANSPORT_STATES['COMPLETED'], self.TRANSPORT_STATES['WAITING'], self.TRANSPORT_STATES['BATTLE_WAITING'], self.TRANSPORT_STATES['PROTECTION_WAITING']]:
            return False
        
        # Calculer le temps écoulé depuis le début de la phase actuelle
        phase_start_time = self._get_current_phase_start_time(transport)
        if phase_start_time is None:
            return False
            
        total_elapsed = current_time - phase_start_time
        
        # Calculer le temps restant basé sur la durée totale de la phase
        if status == self.TRANSPORT_STATES['LOADING']:
            phase_duration = transport['loading_time']
        elif status == self.TRANSPORT_STATES['TRAVELING']:
            phase_duration = transport['travel_time']
        elif status == self.TRANSPORT_STATES['RETURNING']:
            # Vérifier si c'est un retour après annulation (demi-tour)
            if transport.get('cancelled_return', False):
                # Pour un demi-tour, utiliser le temps de retour spécifique calculé lors de l'annulation
                # Ne pas recalculer basé sur phase_start_time, utiliser remaining_time directement
                return self._update_cancelled_return_timer(transport, current_time)
            else:
                # Retour normal après livraison - utiliser return_end timestamp
                return_end = transport.get('timeline', {}).get('return_end')
                if return_end is None:
                    return False
                
                # return_end est déjà en secondes (timestamp Unix)
                return_end_seconds = return_end
                
                # Vérifier si le voyage retour est terminé
                if current_time >= return_end_seconds:
                    return self._handle_state_transition(transport, current_time)
                
                # Calculer remaining_time en secondes pour cohérence
                transport['remaining_time'] = max(0, int(return_end_seconds - current_time))
                return True
        else:
            return False
        
        transport['remaining_time'] = max(0, phase_duration - total_elapsed)
        
        # Log désactivé pour éviter le spam dans les logs
        
        # Vérifier les transitions d'états
        if transport['remaining_time'] <= 0:
            return self._handle_state_transition(transport, current_time)
        
        return True  # Timer mis à jour
    
    def _update_cancelled_return_timer(self, transport: Dict[str, Any], current_time: float) -> bool:
        """Met à jour le timer pour un transport annulé en demi-tour."""
        try:
            return_start_time = transport['timeline'].get('return_start')
            if return_start_time is None:
                return False
            
            # Calculer le temps écoulé depuis le début du demi-tour
            time_elapsed = current_time - return_start_time
            
            # Récupérer le temps de demi-tour initial calculé lors de l'annulation
            initial_return_time = transport.get('initial_return_time')
            if initial_return_time is None:
                # Fallback: reconstruire depuis les données actuelles
                initial_return_time = transport['remaining_time'] + time_elapsed
                transport['initial_return_time'] = initial_return_time
                # Reconstruction automatique du timer de retour
            
            # Mettre à jour le remaining_time
            transport['remaining_time'] = max(0, initial_return_time - time_elapsed)
            
            # Vérifier la transition d'état
            if transport['remaining_time'] <= 0:
                return self._handle_state_transition(transport, current_time)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur mise à jour timer demi-tour transport {transport.get('id', 'unknown')}: {e}")
            return False
    
    def _get_current_phase_start_time(self, transport: Dict[str, Any]) -> float:
        """Retourne le timestamp de début de la phase actuelle."""
        status = transport['status']
        timeline = transport['timeline']
        
        if status == self.TRANSPORT_STATES['LOADING']:
            return timeline.get('loading_start')
        elif status == self.TRANSPORT_STATES['TRAVELING']:
            return timeline.get('travel_start')
        elif status == self.TRANSPORT_STATES['RETURNING']:
            return timeline.get('return_start')
        
        return None
    
    def _handle_state_transition(self, transport: Dict[str, Any], current_time: float) -> bool:
        """Gère les transitions d'états quand le timer atteint 0."""
        
        status = transport['status']
        
        if status == self.TRANSPORT_STATES['LOADING']:
            # LOADING → TRAVELING
            transport['status'] = self.TRANSPORT_STATES['TRAVELING']
            transport['remaining_time'] = transport['travel_time']
            transport['last_update'] = current_time  # Reset timestamp pour nouvelle phase
            transport['timeline']['loading_end'] = current_time
            transport['timeline']['travel_start'] = current_time
            return True
            
        elif status == self.TRANSPORT_STATES['TRAVELING']:
            # TRAVELING → RETURNING/COMPLETED
            self._handle_arrival(transport, current_time)
            return True
            
        elif status == self.TRANSPORT_STATES['RETURNING']:
            # RETURNING → COMPLETED
            transport['status'] = self.TRANSPORT_STATES['COMPLETED']
            transport['timeline']['completed'] = current_time
            
            # Vérifier si c'est un transport annulé qui revient
            if transport.get('cancelled_return', False):
                # Rembourser les ressources à la ville source
                source_city_id = transport['source_city']
                resources_to_refund = transport.get('resources_to_refund', transport['resources'])
                
                if resources_to_refund and any(amount > 0 for amount in resources_to_refund.values()):
                    self._refund_resources_to_source(transport, resources_to_refund)
                
                # Restaurer les héros à la ville source
                self._restore_heroes_to_source(transport)
            
            # Vérifier si c'est un transport de retour de bataille
            elif (transport.get('transport_type') == 'attack' or 
                  transport.get('type') == 'attack' or
                  (transport.get('is_cross_player') and 
                   transport.get('timeline', {}).get('battle_start') and
                   any(key.startswith('unit_') for key in transport.get('resources', {}).keys()))):
                # Créditer la ville d'origine avec les ressources pillées et unités survivantes
                self._credit_battle_return(transport)
                # Les héros sont déjà gérés dans _credit_battle_return
            else:
                # Transport normal qui revient - restaurer les héros
                self._restore_heroes_to_source(transport)
            
            # Libérer les bateaux
            self._free_ships(transport)
            return True
        
        return False
    
    def _handle_arrival(self, transport: Dict[str, Any], current_time: float):
        """Gère l'arrivée à destination."""
        
        transport['timeline']['travel_end'] = current_time
        
        # Vérifier le type de transport
        transport_type = transport.get('transport_type', 'resources')
        
        if transport_type == 'attack':
            # 🚀 Transport d'attaque : déclencher une bataille et rester en attente
            self._handle_attack_arrival(transport, current_time)
            
            # Les transports d'attaque restent en attente de fin de bataille
            transport['status'] = self.TRANSPORT_STATES['BATTLE_WAITING']
            transport['timeline']['battle_start'] = current_time
            
        elif transport_type == 'protection':
            # 🛡️ Transport de protection : ajouter les unités à la garrison de la ville cible
            self._handle_protection_arrival(transport, current_time)
            
            # ✅ NOUVEAU : Les transports de protection restent en attente comme les attaques
            transport['status'] = self.TRANSPORT_STATES['PROTECTION_WAITING']
            transport['timeline']['protection_start'] = current_time
            
            print(f"🛡️ [PROTECTION] Bateaux en attente à {transport['destination_city']} - rappel manuel nécessaire")
            
        else:
            # Transport normal : créditer ressources/unités à la destination
            self._credit_resources_to_destination(transport)
            
            if transport['is_cross_player']:
                # Cross-player = retour nécessaire
                transport['status'] = self.TRANSPORT_STATES['RETURNING']
                transport['remaining_time'] = transport['travel_time']  # Même durée pour le retour
                transport['last_update'] = current_time  # Reset timestamp pour le retour
                transport['timeline']['return_start'] = current_time
                transport['timeline']['return_end'] = current_time + transport['travel_time']  # Définir la fin du retour
            else:
                # Same-player = transport terminé
                transport['status'] = self.TRANSPORT_STATES['COMPLETED']
                transport['timeline']['completed'] = current_time
            
            # Libérer les bateaux immédiatement
            self._free_ships(transport)
    
    def _start_waiting_transports(self, transports_data: Dict[str, Any], current_time: float) -> int:
        """Démarre les transports en attente si leur port est libre."""
        
        started_count = 0
        
        for transport in transports_data['transports']:
            if transport['status'] != self.TRANSPORT_STATES['WAITING']:
                continue
            
            # Vérifier si le port est maintenant libre
            if self._is_port_free_for_city(transports_data['transports'], transport['source_city']):
                # Démarrer le chargement
                transport['status'] = self.TRANSPORT_STATES['LOADING']
                transport['remaining_time'] = transport['loading_time']
                transport['last_update'] = current_time  # Initialiser le timestamp
                transport['timeline']['loading_start'] = current_time
                started_count += 1
        
        return started_count
    
    def _is_port_free_for_city(self, transports: List[Dict[str, Any]], city_id: str) -> bool:
        """Vérifie si le port d'une ville est libre (pas de chargement en cours)."""
        
        for transport in transports:
            if (transport['source_city'] == city_id and 
                transport['status'] == self.TRANSPORT_STATES['LOADING']):
                return False
        
        return True
    
    def _credit_resources_to_destination(self, transport: Dict[str, Any]):
        """Crédite les ressources à la ville de destination."""
        try:
            destination_city = transport['destination_city']
            resources = transport['resources']
            heroes = transport.get('heroes', [])
            
            savegame = self.data_manager.load_savegame()
            cities = savegame.get('cities', [])
            city = next((c for c in cities if c.get('id') == destination_city), None)
            
            if not city:
                print(f"❌ Ville destination {destination_city} non trouvée pour crédit ressources")
                return False
            
            city_resources = city.get('resources', {})
            city_garrison = city.get('military', {}).get('garrison', {})
            
            # Ajouter les ressources ET les unités
            for resource_type, amount in resources.items():
                if amount > 0:  # Ignorer les ressources à 0
                    # Gérer les unités (préfixées par "unit_") - nouvelle structure
                    if resource_type.startswith("unit_"):
                        unit_type = resource_type[5:]  # Enlever "unit_" du début
                        city_owner = city.get('owner') or city.get('ownerId', 'unknown')
                        
                        # Initialiser le groupe du propriétaire si nécessaire
                        if city_owner not in city_garrison:
                            city_garrison[city_owner] = {}
                        
                        # Ajouter au propriétaire
                        if unit_type in city_garrison[city_owner]:
                            city_garrison[city_owner][unit_type]['quantity'] += amount
                        else:
                            city_garrison[city_owner][unit_type] = {'quantity': amount}

                    else:
                        # Ressources classiques
                        current_amount = city_resources.get(resource_type, 0)
                        city_resources[resource_type] = current_amount + amount
            
            # Ajouter les héros à la ville de destination
            if heroes:
                self._credit_heroes_to_destination(city, heroes, transport.get('source_player_id'))
            
            # Sauvegarder avec force_save pour éviter le throttling
            save_success = self.data_manager.save_savegame(savegame, force_save=True)
            
            if save_success:
                # Envoyer une notification au joueur propriétaire de la ville de destination
                destination_player_id = transport.get('destination_player_id')
                source_city = transport.get('source_city', 'Ville inconnue')
                
                if destination_player_id:
                    try:
                        self.notification_service.create_transport_notification(
                            player_id=destination_player_id,
                            from_city=source_city,
                            to_city=destination_city,
                            resources=resources
                        )
                    except Exception as e:
                        print(f"⚠️ Erreur création notification transport: {e}")
                        
            return save_success
                
        except Exception as e:
            print(f"❌ Erreur crédit ressources destination: {e}")
            return False
    
    def _handle_attack_arrival(self, transport: Dict[str, Any], current_time: float):
        """Gère l'arrivée d'un transport d'attaque : déclenche une bataille."""
        try:
            
            # Extraire les données du transport
            source_city = transport['source_city']
            target_city = transport['destination_city']
            units = {}
            heroes = []
            
            # Convertir les ressources "unit_" en unités
            for resource_type, amount in transport.get('resources', {}).items():
                if resource_type.startswith("unit_") and amount > 0:
                    unit_type = resource_type[5:]  # Enlever "unit_"
                    units[unit_type] = amount
            
            # Extraire les héros du transport
            heroes = transport.get('heroes', [])
            
            # Préparer les données pour l'API de bataille
            battle_data = {
                'source_city_id': source_city,
                'target_city_id': target_city,
                'units': units,
                'heroes': heroes,
                'battlefield_template_id': transport.get('battlefield_template_id', 'default_working_v2'),
                'ships': transport.get('ships_needed', 1),
                'owner': transport.get('player_id')
            }
            
            # Appeler le service de bataille avec skip_troop_deduction=True
            try:
                from app.routes.battle_routes_v2 import get_battle_creation_service_v2
                
                service = get_battle_creation_service_v2()
                result = service.create_battle(
                    attacker_city_id=source_city,
                    target_city_id=target_city,
                    units=units,
                    heroes=heroes,
                    ships=battle_data['ships'],
                    battlefield_template_id=battle_data['battlefield_template_id'],
                    attacker_player_id=battle_data['owner'],
                    skip_troop_deduction=True,  # Les troupes ont déjà été déduites lors du transport
                    transport_id=transport['id']  # 🆕 Lier le transport au battlefield
                )
                
                if result.get('success'):
                    # Vider les ressources du transport car elles sont maintenant dans la bataille
                    transport['resources'] = {}
                    return True
                else:
                    print(f"❌ Erreur création bataille: {result.get('error')}")
                    
            except Exception as e:
                print(f"❌ Erreur création bataille: {e}")
                
            return False
            
        except Exception as e:
            print(f"❌ Erreur handle_attack_arrival: {e}")
            return False
    
    def _free_ships(self, transport: Dict[str, Any]):
        """Libère les bateaux utilisés par le transport."""
        try:
            # Pour les transports d'attaque, les bateaux appartiennent TOUJOURS à l'attaquant
            transport_type = transport.get('transport_type', 'resources')
            
            if transport_type == 'attack':
                # Pour les transports d'attaque, déterminer si c'est un retour de bataille
                # Les transports de retour ont leurs rôles inversés, donc les bateaux appartiennent à destination_player_id
                is_battle_return = (transport.get('timeline', {}).get('return_start') is not None)
                
                if is_battle_return:
                    # Transport d'attaque de retour : les bateaux appartiennent à destination_player_id (vrai attaquant)
                    player_id = transport['destination_player_id']
                else:
                    # Transport d'attaque aller : les bateaux appartiennent à source_player_id (attaquant)
                    player_id = transport['source_player_id']
            else:
                # Transport normal : bateaux pour source_player_id
                player_id = transport['source_player_id']
            
            ships_count = transport['ships_needed']
            
            players_data = self.data_manager.load_players()
            players = players_data.get('players', [])
            player = next((p for p in players if p.get('id') == player_id), None)
            
            if not player:
                print(f"❌ Joueur {player_id} non trouvé pour libérer bateaux")
                return False
            
            # Décrémenter le nombre de bateaux occupés
            current_busy = player.get('transport_ships_busy', 0)
            new_busy = max(0, current_busy - ships_count)
            player['transport_ships_busy'] = new_busy
            
            # Bateaux libérés avec succès
            
            # Sauvegarder avec force_save pour éviter le throttling
            save_result = self.data_manager.save_players(players_data, force_save=True)
            return save_result
                
        except Exception as e:
            print(f"❌ Erreur libération bateaux: {e}")
            return False
    
    def _refund_resources_to_source(self, transport: Dict[str, Any], resources_to_refund: Dict[str, int]):
        """Rembourse les ressources à la ville source lors d'un transport annulé."""
        try:
            source_city_id = transport['source_city']
            savegame = self.data_manager.load_savegame()
            cities = savegame.get('cities', [])
            city = next((c for c in cities if c.get('id') == source_city_id), None)
            
            if not city:
                print(f"❌ Ville {source_city_id} non trouvée pour remboursement")
                return False
            
            city_resources = city.get('resources', {})
            
            # Ajouter les ressources remboursées
            for resource_type, amount in resources_to_refund.items():
                if amount > 0:  # Ignorer les ressources à 0
                    current_amount = city_resources.get(resource_type, 0)
                    city_resources[resource_type] = current_amount + amount
            
            # Sauvegarder
            self.data_manager.save_savegame(savegame)
            return True
                
        except Exception as e:
            print(f"❌ Erreur remboursement ressources transport annulé: {e}")
            return False

    def _credit_battle_return(self, transport: Dict[str, Any]):
        """Crédite la ville d'origine avec les ressources pillées et unités survivantes au retour de bataille."""
        try:
            # Détecter si c'est un transport d'attaque
            is_attack_transport = (
                transport.get('transport_type') == 'attack' or 
                transport.get('type') == 'attack' or
                (transport.get('is_cross_player') and 
                 transport.get('timeline', {}).get('battle_start') and
                 any(key.startswith('unit_') for key in transport.get('resources', {}).keys()))
            )
            
            # Pour un transport d'attaque, créditer TOUJOURS la ville de l'attaquant (destination)
            if is_attack_transport:
                source_city_id = transport['destination_city']  # Ville de l'attaquant
            else:
                source_city_id = transport['source_city']  # Transport normal
            savegame = self.data_manager.load_savegame()
            cities = savegame.get('cities', [])
            city = next((c for c in cities if c.get('id') == source_city_id), None)
            
            if not city:
                print(f"❌ Ville {source_city_id} non trouvée pour retour de bataille")
                return False
            
            city_resources = city.get('resources', {})
            
            # Créditer toutes les ressources (incluant les ressources pillées et les unités)
            transport_resources = transport.get('resources', {})
            resources_credited = {}
            units_credited = {}
            
            # Créer la structure military/garrison si elle n'existe pas
            if 'military' not in city:
                city['military'] = {}
            if 'garrison' not in city['military']:
                city['military']['garrison'] = {}
            
            city_garrison = city['military']['garrison']
            
            for resource_type, amount in transport_resources.items():
                if amount > 0:
                    # Gérer les unités (préfixées par "unit_") - nouvelle structure
                    if resource_type.startswith('unit_'):
                        unit_type = resource_type[5:]  # Enlever "unit_" du début
                        city_owner = city.get('owner') or city.get('ownerId', 'unknown')
                        
                        # Initialiser le groupe du propriétaire si nécessaire
                        if city_owner not in city_garrison:
                            city_garrison[city_owner] = {}
                        
                        # Ajouter au propriétaire (FIX: utiliser addition normale pour éviter accumulation)
                        if unit_type in city_garrison[city_owner]:
                            current_qty = city_garrison[city_owner][unit_type].get('quantity', 0)
                            city_garrison[city_owner][unit_type]['quantity'] = current_qty + amount
                        else:
                            city_garrison[city_owner][unit_type] = {'quantity': amount}
                        units_credited[resource_type] = amount
                    else:
                        # Ressources classiques
                        current_amount = city_resources.get(resource_type, 0)
                        city_resources[resource_type] = current_amount + amount
                        units_credited[resource_type] = amount
            
            # Restaurer les héros à la ville d'origine (attaquant)
            heroes = transport.get('heroes', [])
            if heroes:
                self._credit_heroes_to_destination(city, heroes, transport.get('destination_player_id', transport.get('source_player_id')))
            
            # Sauvegarder
            self.data_manager.save_savegame(savegame, force_save=True)
            
            # Afficher les ressources et unités créditées
            if resources_credited or units_credited:
                print(f"✅ Retour de bataille: ville {source_city_id} créditée")
                if resources_credited:
                    print(f"   📦 Ressources: {resources_credited}")
                if units_credited:
                    print(f"   ⚔️ Unités: {units_credited}")
            
            return True
                
        except Exception as e:
            print(f"❌ Erreur crédit retour de bataille: {e}")
            return False
    
    def _archive_completed_transports(self, transports_data: Dict[str, Any], indices_to_remove: List[int]):
        """Archive les transports terminés et les supprime de la liste active."""
        
        try:
            # Charger l'historique
            history_data = self.data_manager.load_transport_history()
            
            # Archiver les transports terminés (en ordre inverse pour préserver les indices)
            for i in sorted(indices_to_remove, reverse=True):
                transport = transports_data['transports'][i]
                
                # Créer un résumé pour l'historique
                summary = {
                    "id": transport['id'],
                    "source_player_id": transport['source_player_id'],
                    "source_city": transport['source_city'],
                    "destination_city": transport['destination_city'],
                    "resources": transport['resources'],
                    "ships_needed": transport['ships_needed'],
                    "is_cross_player": transport['is_cross_player'],
                    "timeline": transport['timeline'],
                    "archived_at": time.time()
                }
                
                history_data['transport_history'].append(summary)
                
                # Supprimer de la liste active
                del transports_data['transports'][i]
            
            # Sauvegarder l'historique
            self.data_manager.save_transport_history(history_data, force_save=True)
            
        except Exception as e:
            print(f"❌ Erreur archivage transports: {e}")
    
    def complete_battle_transports(self, battle_id: str):
        """
        Libère tous les transports d'attaque en attente pour une bataille spécifique.
        Cette fonction est appelée quand une bataille se termine.
        
        Args:
            battle_id: ID de la bataille terminée
        """
        try:
            transports_data = self.data_manager.load_transports()
            current_time = time.time()
            completed_transports = []
            
            for transport in transports_data.get('transports', []):
                # Vérifier si c'est un transport d'attaque en attente pour cette bataille
                if (transport.get('status') == self.TRANSPORT_STATES['BATTLE_WAITING'] and 
                    transport.get('transport_type') == 'attack'):
                    
                    # Optionnel : vérifier que le transport correspond à cette bataille
                    # Pour l'instant, on libère tous les transports d'attaque en attente
                    
                    if transport['is_cross_player']:
                        # Cross-player = commencer le retour
                        transport['status'] = self.TRANSPORT_STATES['RETURNING']
                        transport['remaining_time'] = transport['travel_time']
                        transport['last_update'] = current_time
                        transport['timeline']['return_start'] = current_time
                        transport['timeline']['return_end'] = current_time + transport['travel_time']
                        print(f"🚢 Transport d'attaque {transport['id']} commence le retour")
                    else:
                        # Same-player = transport terminé
                        transport['status'] = self.TRANSPORT_STATES['COMPLETED']
                        transport['timeline']['completed'] = current_time
                        self._free_ships(transport)
                        print(f"✅ Transport d'attaque {transport['id']} terminé")
                    
                    completed_transports.append(transport['id'])
            
            if completed_transports:
                self.data_manager.save_transports(transports_data, force_save=True)
                print(f"⚔️ {len(completed_transports)} transports d'attaque libérés pour bataille {battle_id}")
            
            return completed_transports
            
        except Exception as e:
            print(f"❌ Erreur libération transports bataille: {e}")
            return []

    def _handle_protection_arrival(self, transport: Dict[str, Any], current_time: float):
        """Gère l'arrivée d'un transport de protection - ajoute les unités à la garrison de la ville cible."""
        try:
            destination_city = transport['destination_city']
            source_player_id = transport['source_player_id']
            
            # ✅ CORRECTIF: Les unités sont dans transport['resources'] avec préfixe "unit_"
            resources = transport.get('resources', {})
            units = {}
            for key, value in resources.items():
                if key.startswith('unit_'):
                    unit_type = key.replace('unit_', '')  # Retirer le préfixe "unit_"
                    units[unit_type] = value
            
            print(f"🛡️ [PROTECTION_ARRIVAL] Arrivée protection à {destination_city}")
            print(f"🛡️ [PROTECTION_ARRIVAL] Joueur protecteur: {source_player_id}, Unités: {units}")
            print(f"🛡️ [PROTECTION_ARRIVAL] Resources brutes: {resources}")
            
            # Charger les données de sauvegarde
            savegame = self.data_manager.load_savegame()
            cities = savegame.get('cities', [])
            city = next((c for c in cities if c.get('id') == destination_city), None)
            
            if not city:
                print(f"❌ [PROTECTION_ARRIVAL] Ville {destination_city} non trouvée")
                return False
            
            # Initialiser la structure militaire si nécessaire
            if 'military' not in city:
                city['military'] = {}
            if 'garrison' not in city['military']:
                city['military']['garrison'] = {}
            
            city_garrison = city['military']['garrison']
            
            # Initialiser le groupe du joueur protecteur si nécessaire
            if source_player_id not in city_garrison:
                city_garrison[source_player_id] = {}
            
            # Ajouter les unités au groupe du joueur protecteur
            for unit_type, quantity in units.items():
                if quantity > 0:
                    if unit_type in city_garrison[source_player_id]:
                        city_garrison[source_player_id][unit_type]['quantity'] += quantity
                        print(f"💰 [PROTECTION_ARRIVAL] {destination_city}: +{quantity} {unit_type} dans garrison[{source_player_id}] (total: {city_garrison[source_player_id][unit_type]['quantity']})")
                    else:
                        city_garrison[source_player_id][unit_type] = {'quantity': quantity}
                        print(f"💰 [PROTECTION_ARRIVAL] {destination_city}: +{quantity} {unit_type} dans garrison[{source_player_id}] (nouveau)")
            
            # Ajouter les héros au groupe du joueur protecteur
            heroes = transport.get('heroes', [])
            if heroes:
                self._credit_heroes_to_destination(city, heroes, source_player_id)
            
            # Sauvegarder
            save_success = self.data_manager.save_savegame(savegame, force_save=True)
            
            if save_success:
                print(f"✅ [PROTECTION_ARRIVAL] Protection terminée: {source_player_id} protège {destination_city}")
                
                # Envoyer notification au propriétaire de la ville protégée
                city_owner = city.get('owner') or city.get('ownerId')
                if city_owner and city_owner != source_player_id:
                    self.notification_service.add_notification(
                        player_id=city_owner,
                        message=f"🛡️ Vos alliés protègent {city.get('name', destination_city)} !",
                        notification_type="protection_received"
                    )
                
                # Envoyer notification au protecteur
                self.notification_service.add_notification(
                    player_id=source_player_id,
                    message=f"🛡️ Vos unités protègent maintenant {city.get('name', destination_city)} !",
                    notification_type="protection_sent"
                )
                
                return True
            else:
                print(f"❌ [PROTECTION_ARRIVAL] Échec sauvegarde pour {destination_city}")
                return False
                
        except Exception as e:
            print(f"❌ [PROTECTION_ARRIVAL] Erreur: {str(e)}")
            return False
    
    def _credit_heroes_to_destination(self, city: Dict[str, Any], heroes: List[str], source_player_id: str):
        """Ajoute les héros à la ville de destination."""
        try:
            if not heroes:
                return True
            
            # Initialiser la structure militaire si nécessaire
            if 'military' not in city:
                city['military'] = {}
            if 'heroes' not in city['military']:
                city['military']['heroes'] = {}
            
            heroes_section = city['military']['heroes']
            
            # Pour chaque héros, le remettre en statut 'garrison' dans la ville de destination
            for hero_id in heroes:
                if hero_id in heroes_section:
                    # Le héros existe déjà, simplement changer son statut
                    heroes_section[hero_id]['status'] = 'garrison'
                    print(f"👑 Héros {hero_id} restauré en garnison dans {city['id']}")
                else:
                    # Le héros n'existe pas, créer une entrée de base
                    # Note: Les données complètes du héros devraient venir d'une DB centrale
                    heroes_section[hero_id] = {
                        'owner': source_player_id,
                        'status': 'garrison'
                    }
                    print(f"👑 Héros {hero_id} ajouté en garnison dans {city['id']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur crédit héros destination: {e}")
            return False
    
    def _restore_heroes_to_source(self, transport: Dict[str, Any]):
        """Restaure les héros à la ville source quand un transport revient."""
        try:
            heroes = transport.get('heroes', [])
            if not heroes:
                return True
                
            source_city_id = transport['source_city']
            source_player_id = transport['source_player_id']
            
            savegame = self.data_manager.load_savegame()
            cities = savegame.get('cities', [])
            city = next((c for c in cities if c.get('id') == source_city_id), None)
            
            if not city:
                print(f"❌ Ville source {source_city_id} non trouvée pour restaurer héros")
                return False
            
            # Initialiser la structure militaire si nécessaire
            if 'military' not in city:
                city['military'] = {}
            if 'heroes' not in city['military']:
                city['military']['heroes'] = {}
            
            heroes_section = city['military']['heroes']
            
            # Restaurer chaque héros en statut 'garrison'
            for hero_id in heroes:
                if hero_id in heroes_section:
                    heroes_section[hero_id]['status'] = 'garrison'
                    print(f"👑 Héros {hero_id} restauré en garnison dans {source_city_id}")
                else:
                    # Le héros n'existe pas, créer une entrée de base
                    heroes_section[hero_id] = {
                        'owner': source_player_id,
                        'status': 'garrison'
                    }
                    print(f"👑 Héros {hero_id} restauré (créé) en garnison dans {source_city_id}")
            
            # Sauvegarder
            return self.data_manager.save_savegame(savegame, force_save=True)
            
        except Exception as e:
            print(f"❌ Erreur restauration héros source: {e}")
            return False

