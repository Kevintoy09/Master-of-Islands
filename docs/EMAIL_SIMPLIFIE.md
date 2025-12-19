# Système d'email simplifié pour la messagerie

## Comment ça fonctionne

Quand un joueur envoie un message à l'administrateur, le système **enregistre une notification** dans un fichier JSON au lieu d'envoyer directement un email.

### Fichier de notifications

**Emplacement** : `server/data/admin_email_notifications.json`

Ce fichier contient toutes les notifications d'emails à envoyer à `contact@masterofisland.com`.

### Structure d'une notification

```json
{
  "id": "email_1733577600000",
  "timestamp": "2025-12-07T14:30:00",
  "to": "contact@masterofisland.com",
  "from": "NomDuJoueur",
  "subject": "[Master of Island] Sujet du message",
  "content": "Contenu du message du joueur...",
  "attachment_url": "https://votre-domaine.com/uploads/attachments/capture.png",
  "sent": false
}
```

## Envoi des emails

Vous avez **3 options** pour envoyer les emails :

### Option 1 : Manuellement (Simple)

1. Consultez le fichier `server/data/admin_email_notifications.json`
2. Pour chaque notification avec `"sent": false` :
   - Copiez le contenu
   - Envoyez un email depuis votre client email habituel
   - Marquez `"sent": true` dans le fichier

**Avantages** : Aucune configuration technique, vous contrôlez tout
**Inconvénients** : Manuel, nécessite de vérifier régulièrement

### Option 2 : Script automatique avec votre serveur email

Créez un script Python simple qui lit le fichier JSON et envoie les emails :

```python
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_pending_emails():
    with open('server/data/admin_email_notifications.json', 'r') as f:
        notifications = json.load(f)
    
    # Configuration email (remplacez par vos paramètres)
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "votre-email@gmail.com"
    password = "votre-mot-de-passe-app"
    
    for notif in notifications:
        if not notif['sent']:
            # Créer l'email
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = notif['to']
            msg['Subject'] = notif['subject']
            
            body = f"""
De : {notif['from']}
Date : {notif['timestamp']}

Message :
{notif['content']}
"""
            if notif['attachment_url']:
                body += f"\n\nPièce jointe : {notif['attachment_url']}"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Envoyer
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, password)
                server.send_message(msg)
            
            # Marquer comme envoyé
            notif['sent'] = True
    
    # Sauvegarder
    with open('server/data/admin_email_notifications.json', 'w') as f:
        json.dump(notifications, f, indent=2)

# Exécuter périodiquement (cron job, scheduler, etc.)
send_pending_emails()
```

**Exécution** : Ajoutez ce script à un cron job ou un scheduler Windows pour qu'il s'exécute automatiquement toutes les 5-10 minutes.

**Avantages** : Automatique, fiable, vous gardez le contrôle
**Inconvénients** : Nécessite une configuration initiale

### Option 3 : Service webhook externe (Zapier, Make, etc.)

1. Créez un webhook qui lit le fichier JSON depuis l'URL publique
2. Configurez une action "Envoyer email"
3. Programmez l'exécution toutes les X minutes

**Avantages** : Pas de code, interface visuelle
**Inconvénients** : Payant pour usage fréquent, dépend d'un service tiers

## Consultation des messages admin

Les messages admin sont toujours disponibles dans :
- **Messagerie interne** : L'admin peut se connecter au jeu et lire les messages
- **Fichier JSON** : `server/data/messages.json` contient tous les messages
- **Notifications email** : `server/data/admin_email_notifications.json` pour envoi email

## Pourquoi cette approche ?

### Avantages

1. **Pas de configuration SMTP complexe** : Pas besoin de configurer Gmail, SendGrid, etc.
2. **Pas de dépendances** : Flask-Mail n'est plus nécessaire
3. **Fiable** : Les notifications sont toujours enregistrées même si l'envoi échoue
4. **Flexible** : Vous choisissez comment et quand envoyer les emails
5. **Traçable** : Toutes les notifications sont dans un fichier lisible
6. **Gratuit** : Pas de quota, pas de limite

### Désavantages

1. **Pas d'envoi instantané** : Les emails ne partent pas immédiatement
2. **Nécessite une action manuelle ou un script** : Pas d'automatisation intégrée

## Recommandation

Pour démarrer, utilisez **Option 1 (manuel)** pour valider que tout fonctionne.

Ensuite, passez à **Option 2 (script Python)** avec un cron job pour automatiser :

```bash
# Linux/Mac - Cron job toutes les 10 minutes
*/10 * * * * cd /chemin/vers/game59 && python3 send_emails.py

# Windows - Task Scheduler
# Créez une tâche qui exécute python send_emails.py toutes les 10 minutes
```

## Alternative : Email direct depuis le jeu (si vous le souhaitez vraiment)

Si vous voulez vraiment envoyer des emails directement depuis le jeu, la solution la plus simple est d'utiliser un **service transactionnel** :

### SendGrid (gratuit jusqu'à 100 emails/jour)

```bash
pip install sendgrid
```

```python
# Dans messages.py
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email_notification(sender_name, subject, content, attachment_url=None):
    try:
        message = Mail(
            from_email='noreply@masterofisland.com',
            to_emails='contact@masterofisland.com',
            subject=f'[Master of Island] {subject}',
            html_content=f'<strong>De:</strong> {sender_name}<br><br>{content}'
        )
        
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        return True
    except Exception as e:
        print(f"Erreur: {e}")
        return False
```

**Configuration Railway** :
- Variable : `SENDGRID_API_KEY`
- Valeur : Votre clé API SendGrid

**Avantages** : Simple, rapide, fiable
**Inconvénients** : Nécessite un compte SendGrid

## En résumé

🎯 **Actuellement** : Les notifications sont enregistrées dans `admin_email_notifications.json`

📧 **Pour envoyer les emails** : Choisissez l'une des 3 options ci-dessus

✅ **Recommandé pour démarrer** : Consultez manuellement le fichier JSON et envoyez les emails depuis votre client email habituel

🚀 **Recommandé pour production** : Script Python automatisé avec cron job (Option 2)
