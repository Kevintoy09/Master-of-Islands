# Configuration de l'envoi d'emails pour la messagerie

## Vue d'ensemble

Le système de messagerie envoie automatiquement un email à `contact@masterofisland.com` lorsqu'un joueur contacte l'administrateur.

## Configuration requise

### 1. Installer les dépendances

```bash
cd server
pip install -r requirements.txt
```

Cela installera `flask-mail==0.9.1` qui est nécessaire pour l'envoi d'emails.

### 2. Configurer les variables d'environnement

Créez ou modifiez le fichier `.env` dans le dossier `server/` :

#### Option A : Gmail (recommandé pour les tests)

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=votre-email@gmail.com
MAIL_PASSWORD=votre-mot-de-passe-app
MAIL_DEFAULT_SENDER=noreply@masterofisland.com
```

**Important pour Gmail** : Vous devez générer un "mot de passe d'application" :
1. Accédez à https://myaccount.google.com/security
2. Activez la validation en deux étapes
3. Générez un "mot de passe d'application" dans "Sécurité" > "Mots de passe d'application"
4. Utilisez ce mot de passe de 16 caractères dans `MAIL_PASSWORD`

#### Option B : SendGrid (recommandé pour la production)

```env
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=apikey
MAIL_PASSWORD=votre-cle-api-sendgrid
MAIL_DEFAULT_SENDER=noreply@masterofisland.com
```

Pour SendGrid :
1. Créez un compte sur https://sendgrid.com/
2. Générez une clé API dans Settings > API Keys
3. Utilisez "apikey" comme username et votre clé API comme password

#### Option C : Serveur SMTP personnalisé

```env
MAIL_SERVER=smtp.votre-serveur.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=votre-username
MAIL_PASSWORD=votre-password
MAIL_DEFAULT_SENDER=noreply@masterofisland.com
```

### 3. Configuration sur Railway (production)

Sur Railway, ajoutez ces variables d'environnement dans l'interface web :
1. Allez dans votre projet > Variables
2. Ajoutez chaque variable (MAIL_SERVER, MAIL_PORT, etc.)
3. Railway redémarrera automatiquement l'application

## Fonctionnement

### Quand un email est envoyé ?

Un email est automatiquement envoyé à `contact@masterofisland.com` dans deux cas :

1. **Message simple à l'admin** : Lorsqu'un joueur utilise le bouton "Contacter l'admin" dans la messagerie
2. **Message avec pièce jointe** : Lorsqu'un joueur envoie un rapport de bug avec capture d'écran

### Contenu de l'email

```
Objet: [Master of Island] <Sujet du message>

De : <Nom du joueur>
Sujet : <Sujet du message>

Message :
<Contenu du message>

Pièce jointe disponible : <URL si fichier joint>
```

### Structure du code

**Fichiers modifiés :**

1. `server/app/__init__.py` :
   - Import de Flask-Mail
   - Configuration MAIL_* depuis variables d'environnement
   - Initialisation de l'instance Mail et stockage dans app.config

2. `server/app/messages.py` :
   - Nouvelle fonction `send_email_to_admin()` qui utilise Flask-Mail
   - Modification de `send_message()` : envoie email si recipient_id == 'admin'
   - Modification de `send_message_with_attachment()` : envoie toujours email avec URL de la pièce jointe

## Dépannage

### Erreur : "Flask-Mail non configuré"

Vérifiez que :
- Flask-Mail est installé : `pip list | grep -i flask-mail`
- Les variables d'environnement sont définies
- Le fichier `.env` est dans `server/` et chargé

### Erreur : "SMTPAuthenticationError"

- **Gmail** : Vérifiez que vous utilisez un mot de passe d'application (pas votre mot de passe normal)
- **SendGrid** : Vérifiez que votre clé API est valide et n'a pas expiré
- Vérifiez le username (pour SendGrid, doit être exactement "apikey")

### Email non reçu

1. Vérifiez les logs du serveur pour les messages `✉️ Email envoyé` ou `❌ Erreur lors de l'envoi`
2. Vérifiez le dossier spam de contact@masterofisland.com
3. Pour Gmail/SendGrid, vérifiez les quotas (limite d'envoi journalière)
4. Testez avec une configuration locale d'abord

### Mode développement sans email

Si vous voulez tester sans configurer d'email, le système fonctionne normalement :
- Les messages sont toujours sauvegardés dans `messages.json`
- L'admin peut les lire dans la messagerie interne
- Un message de log apparaît : `⚠️ Flask-Mail non configuré, email non envoyé`

## Test manuel

Pour tester l'envoi d'email :

```python
from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'votre-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'votre-mot-de-passe-app'
app.config['MAIL_DEFAULT_SENDER'] = 'noreply@masterofisland.com'

mail = Mail(app)

with app.app_context():
    msg = Message(
        subject="Test Master of Island",
        recipients=["contact@masterofisland.com"],
        body="Ceci est un test d'envoi d'email"
    )
    mail.send(msg)
    print("Email envoyé !")
```

## Pièces jointes

Les pièces jointes sont stockées dans `server/uploads/attachments/` et limitées à :
- **Taille max** : 5 MB
- **Extensions autorisées** : png, jpg, jpeg, gif, pdf, txt, doc, docx

L'email contient l'URL de téléchargement : `https://votre-domaine.com/uploads/attachments/fichier.png`

## Sécurité

⚠️ **Important** :
- Ne committez JAMAIS le fichier `.env` dans Git
- Utilisez des mots de passe d'application, pas vos mots de passe principaux
- Sur Railway, les variables d'environnement sont sécurisées
- Surveillez les quotas d'envoi pour éviter l'abus
