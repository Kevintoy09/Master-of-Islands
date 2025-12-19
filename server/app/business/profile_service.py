"""
=================================================================
PROFILE_SERVICE.PY - Service pour la gestion des profils joueurs
=================================================================

RESPONSABILITÉS:
- Gestion des profils personnels des joueurs (séparé du gameplay)
- Stockage des coordonnées et informations personnelles
- Validation des données de profil
- Interface avec player_profiles.json

MÉTHODES PRINCIPALES:
- create_profile()           → Création nouveau profil
- get_profile()              → Récupération profil par player_id
- update_profile()           → Mise à jour profil
- validate_email()           → Validation format email
- search_profiles()          → Recherche profils par critères

RÈGLES D'USAGE:
✓ Séparer complètement des données de jeu
✓ Respect RGPD pour données personnelles
✓ Validation stricte des emails
✓ Chiffrement des données sensibles (optionnel)

DÉPENDANCES:
- DataManager pour persistance
- Validators pour validation
=================================================================
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from ..core.exceptions import GameValidationError


class ProfileService:
    """Service pour la gestion des profils personnels des joueurs"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        # CORRECTION: Utiliser gamedata_dir au lieu de data_dir
        self.profiles_file = os.path.join(data_manager.gamedata_dir, 'player_profiles.json')
        self._ensure_profiles_file()
    
    def _ensure_profiles_file(self):
        """Assure l'existence du fichier des profils"""
        if not os.path.exists(self.profiles_file):
            initial_data = {
                "profiles": {},
                "metadata": {
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "description": "Profils personnels des joueurs",
                    "version": "1.0"
                }
            }
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)
    
    def _load_profiles(self) -> Dict:
        """Charge les profils depuis le fichier JSON"""
        try:
            with open(self.profiles_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"profiles": {}, "metadata": {}}
    
    def _save_profiles(self, profiles_data: Dict):
        """Sauvegarde les profils dans le fichier JSON"""
        try:
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise GameValidationError(f"Erreur sauvegarde profils: {str(e)}")
    
    def validate_email(self, email: str) -> bool:
        """Valide le format d'un email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))
    
    def email_exists(self, email: str) -> bool:
        """Vérifie si un email existe déjà"""
        profiles_data = self._load_profiles()
        email_lower = email.strip().lower()
        
        for profile in profiles_data.get("profiles", {}).values():
            if profile.get("email", "").lower() == email_lower:
                return True
        return False
    
    def create_profile(self, player_id: str, profile_data: Dict) -> Dict:
        """
        Crée un nouveau profil pour un joueur
        
        Args:
            player_id: ID unique du joueur
            profile_data: Données du profil (firstName, lastName, email, etc.)
        
        Returns:
            Dict: Profil créé
        """
        # Validation des données obligatoires
        required_fields = ['firstName', 'lastName', 'email']
        for field in required_fields:
            if not profile_data.get(field, '').strip():
                raise GameValidationError(f"Le champ {field} est obligatoire")
        
        # Validation email
        email = profile_data['email'].strip()
        if not self.validate_email(email):
            raise GameValidationError("Format d'email invalide")
        
        # Vérification unicité email
        if self.email_exists(email):
            raise GameValidationError("Cette adresse email est déjà utilisée")
        
        # Chargement des profils existants
        profiles_data = self._load_profiles()
        
        # Vérification que le joueur n'a pas déjà un profil
        if player_id in profiles_data.get("profiles", {}):
            raise GameValidationError("Ce joueur a déjà un profil")
        
        # Création du nouveau profil
        new_profile = {
            "player_id": player_id,
            "username": profile_data.get('username', ''),
            "password": profile_data.get('password', ''),
            "firstName": profile_data['firstName'].strip(),
            "lastName": profile_data['lastName'].strip(),
            "email": email.lower(),
            "birthDate": profile_data.get('birthDate', ''),
            "country": profile_data.get('country', ''),
            "city": profile_data.get('city', '').strip(),
            "phone": profile_data.get('phone', '').strip(),
            "newsletter": profile_data.get('newsletter', False),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "is_email_verified": False,
            "verification_token": None
        }
        
        # Ajout du profil
        profiles_data["profiles"][player_id] = new_profile
        
        # Sauvegarde
        self._save_profiles(profiles_data)
        
        return new_profile
    
    def get_profile(self, player_id: str) -> Optional[Dict]:
        """Récupère le profil d'un joueur"""
        profiles_data = self._load_profiles()
        return profiles_data.get("profiles", {}).get(player_id)
    
    def update_profile(self, player_id: str, updates: Dict) -> Dict:
        """Met à jour le profil d'un joueur"""
        profiles_data = self._load_profiles()
        
        if player_id not in profiles_data.get("profiles", {}):
            raise GameValidationError("Profil non trouvé")
        
        profile = profiles_data["profiles"][player_id]
        
        # Validation email si modifié
        if 'email' in updates:
            new_email = updates['email'].strip().lower()
            if new_email != profile.get('email', ''):
                if not self.validate_email(new_email):
                    raise GameValidationError("Format d'email invalide")
                if self.email_exists(new_email):
                    raise GameValidationError("Cette adresse email est déjà utilisée")
                profile['is_email_verified'] = False  # Re-vérification nécessaire
        
        # Mise à jour des champs
        for key, value in updates.items():
            if key in ['firstName', 'lastName', 'city', 'phone']:
                profile[key] = str(value).strip()
            elif key in ['email']:
                profile[key] = str(value).strip().lower()
            elif key in ['username', 'password']:
                profile[key] = str(value).strip()
            elif key in ['country', 'birthDate']:
                profile[key] = str(value)
            elif key in ['newsletter']:
                profile[key] = bool(value)
        
        profile['updated_at'] = datetime.utcnow().isoformat() + "Z"
        
        # Sauvegarde
        self._save_profiles(profiles_data)
        
        return profile
    
    def search_profiles(self, criteria: Dict) -> List[Dict]:
        """Recherche des profils selon des critères"""
        profiles_data = self._load_profiles()
        results = []
        
        for profile in profiles_data.get("profiles", {}).values():
            match = True
            
            # Filtre par pays
            if 'country' in criteria:
                if profile.get('country', '') != criteria['country']:
                    match = False
            
            # Filtre par newsletter
            if 'newsletter' in criteria:
                if profile.get('newsletter', False) != criteria['newsletter']:
                    match = False
            
            # Filtre par email vérifié
            if 'email_verified' in criteria:
                if profile.get('is_email_verified', False) != criteria['email_verified']:
                    match = False
            
            if match:
                # Retourner une version sans données sensibles
                safe_profile = {
                    "player_id": profile['player_id'],
                    "firstName": profile['firstName'],
                    "lastName": profile['lastName'],
                    "country": profile.get('country', ''),
                    "created_at": profile['created_at']
                }
                results.append(safe_profile)
        
        return results
    
    def get_profile_stats(self) -> Dict:
        """Retourne des statistiques sur les profils"""
        profiles_data = self._load_profiles()
        profiles = profiles_data.get("profiles", {})
        
        countries = {}
        verified_emails = 0
        newsletter_subscribers = 0
        
        for profile in profiles.values():
            # Comptage par pays
            country = profile.get('country', 'Non spécifié')
            countries[country] = countries.get(country, 0) + 1
            
            # Emails vérifiés
            if profile.get('is_email_verified', False):
                verified_emails += 1
            
            # Newsletter
            if profile.get('newsletter', False):
                newsletter_subscribers += 1
        
        return {
            "total_profiles": len(profiles),
            "verified_emails": verified_emails,
            "newsletter_subscribers": newsletter_subscribers,
            "countries": countries
        }