# -*- coding: utf-8 -*-
"""
Quest Scheduler - Régénération automatique des quêtes quotidiennes
Gère la régénération à minuit et rattrape les jours manqués si le serveur était éteint
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class QuestScheduler:
    def __init__(self, quest_service):
        """
        Initialise le scheduler de quêtes
        
        Args:
            quest_service: Instance du QuestService
        """
        self.quest_service = quest_service
        self.scheduler = BackgroundScheduler(timezone='Europe/Paris')
        self.scheduler.start()
        logger.info("✅ Quest Scheduler initialisé")
        
    def start(self):
        """
        Démarre le scheduler avec :
        - Rattrapage des jours manqués au démarrage
        - Régénération automatique à minuit
        """
        # 1. Vérifier et rattraper les jours manqués au démarrage
        self._catchup_missed_days()
        
        # 2. Programmer la régénération quotidienne à minuit
        self.scheduler.add_job(
            func=self._daily_regeneration,
            trigger=CronTrigger(hour=0, minute=0),  # Tous les jours à 00:00
            id='daily_quest_regeneration',
            name='Régénération quotidienne des quêtes',
            replace_existing=True
        )
        logger.info("✅ Régénération quotidienne programmée à 00:00")
    
    def _catchup_missed_days(self):
        """
        Rattrape les jours manqués si le serveur était éteint
        """
        try:
            logger.info("🔍 Vérification des jours manqués...")
            
            all_player_data = self.quest_service.load_all_player_quests()
            today = datetime.now().strftime('%Y-%m-%d')
            players_regenerated = 0
            
            for username, user_data in all_player_data.items():
                daily_quests_data = user_data.get('daily_quests', {})
                last_generated = daily_quests_data.get('generated_date')
                
                if last_generated != today:
                    # Les quêtes ne sont pas à jour, régénérer
                    logger.info(f"📅 Régénération manquée pour {username} (dernière: {last_generated})")
                    self.quest_service.regenerate_daily_quests(username)
                    players_regenerated += 1
            
            if players_regenerated > 0:
                logger.info(f"✅ Rattrapage terminé: {players_regenerated} joueur(s) régénéré(s)")
            else:
                logger.info("✅ Aucun rattrapage nécessaire, toutes les quêtes sont à jour")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du rattrapage des jours manqués: {e}")
    
    def _daily_regeneration(self):
        """
        Fonction exécutée tous les jours à minuit
        Régénère les quêtes quotidiennes pour tous les joueurs
        """
        try:
            logger.info("🌙 Régénération quotidienne démarrée...")
            
            all_player_data = self.quest_service.load_all_player_quests()
            regenerated_count = 0
            
            for username in all_player_data.keys():
                try:
                    self.quest_service.regenerate_daily_quests(username)
                    regenerated_count += 1
                except Exception as e:
                    logger.error(f"❌ Erreur régénération pour {username}: {e}")
            
            logger.info(f"✅ Régénération terminée: {regenerated_count} joueur(s)")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la régénération quotidienne: {e}")
    
    def stop(self):
        """Arrête le scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 Quest Scheduler arrêté")

# Instance globale (sera initialisée dans __init__.py)
_quest_scheduler = None

def init_quest_scheduler(quest_service):
    """
    Initialise et démarre le scheduler global
    
    Args:
        quest_service: Instance du QuestService
    """
    global _quest_scheduler
    if _quest_scheduler is None:
        _quest_scheduler = QuestScheduler(quest_service)
        _quest_scheduler.start()
    return _quest_scheduler

def get_quest_scheduler():
    """Retourne l'instance du scheduler"""
    return _quest_scheduler
