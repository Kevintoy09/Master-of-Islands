# Guide de la Messagerie - Master of Island

## 🎯 Fonctionnalités

### Pour les joueurs

1. **Icône d'enveloppe en haut à gauche** 📧
   - Toujours visible sur toutes les pages
   - Badge rouge avec le nombre de messages non lus
   - Cliquez pour ouvrir la messagerie

2. **Messagerie joueur-à-joueur**
   - Envoyez des messages à d'autres joueurs
   - Recevez des réponses
   - Suivez vos conversations dans "Envoyés" et "Reçus"

3. **Contacter l'administrateur**
   - Signalez des bugs
   - Posez des questions
   - Joignez des captures d'écran (PNG, JPG, PDF jusqu'à 5 MB)

### Pour l'administrateur

- Reçoit les messages dans la messagerie interne
- **ET** reçoit un email sur contact@masterofisland.com (si configuré)
- Les pièces jointes sont accessibles via URL dans l'email

## 💡 Comment utiliser

### Ouvrir la messagerie

**Option 1** : Cliquez sur l'icône d'enveloppe 📧 en haut à gauche de l'écran

**Option 2** : Depuis le menu ☰, cliquez sur "📬 Messagerie"

**Option 3** : Depuis une ville d'un autre joueur, cliquez sur "✉️ Envoyer un message"

### Envoyer un message à un joueur

1. Ouvrez la messagerie
2. Cliquez sur "✍️ Nouveau message"
3. Sélectionnez le destinataire dans la liste
4. Écrivez votre sujet et message
5. Cliquez sur "📤 Envoyer"

### Contacter l'administrateur

1. Ouvrez la messagerie
2. Cliquez sur "📞 Contacter l'admin"
3. Écrivez votre sujet et message
4. (Optionnel) Joignez une capture d'écran pour un bug
5. Cliquez sur "📤 Envoyer"

### Lire vos messages

1. Ouvrez la messagerie
2. Onglet "📥 Reçus" pour voir les messages reçus
3. Cliquez sur un message pour le lire
4. Les messages non lus sont en **gras**
5. Utilisez le bouton "🗑️ Supprimer" si nécessaire

### Vérifier vos messages envoyés

1. Ouvrez la messagerie
2. Onglet "📤 Envoyés"
3. Consultez l'historique de vos messages
4. Vérifiez si le destinataire a lu votre message

## 🎨 Interface

### Badge de notification
- **Bleu** : Nombre de messages non lus
- **Position** : En haut à droite de l'icône d'enveloppe

### Onglets
- **📥 Reçus** : Messages que vous avez reçus
- **📤 Envoyés** : Messages que vous avez envoyés

### Actions disponibles
- ✍️ Nouveau message
- 📞 Contacter l'admin
- 📖 Lire un message
- 🗑️ Supprimer un message

## 📱 Mobile

L'interface s'adapte automatiquement aux petits écrans :
- Popup plein écran sur mobile
- Boutons tactiles optimisés
- Défilement vertical pour les longues listes

## 🔒 Confidentialité

- Les messages sont privés entre expéditeur et destinataire
- L'administrateur peut lire les messages qui lui sont adressés
- Les messages supprimés ne sont plus visibles
- Les pièces jointes sont stockées de manière sécurisée

## 🐛 Signaler un bug

Pour signaler un bug efficacement :

1. **Prenez une capture d'écran** du problème
2. **Contactez l'admin** via la messagerie
3. **Décrivez le problème** :
   - Que faisiez-vous ?
   - Qu'est-ce qui s'est passé ?
   - Qu'attendiez-vous ?
4. **Joignez la capture** d'écran
5. **Envoyez** le message

L'admin recevra un email immédiatement avec tous les détails !

## ⚙️ Configuration technique

### Pour les développeurs

Voir la documentation complète dans :
- `docs/EMAIL_CONFIGURATION.md` - Configuration SMTP et variables d'environnement
- `server/app/messages.py` - Backend API
- `client/src/components/MessagesPopup.tsx` - Interface utilisateur

### Fichiers de données

- **Messages** : `server/data/messages.json`
- **Pièces jointes** : `server/uploads/attachments/`

### API Endpoints

```
POST   /api/messages/send                    - Envoyer un message
POST   /api/messages/send-with-attachment    - Envoyer avec pièce jointe
GET    /api/messages/inbox/<player_id>       - Boîte de réception
GET    /api/messages/sent/<player_id>        - Messages envoyés
POST   /api/messages/read/<message_id>       - Marquer comme lu
POST   /api/messages/delete/<message_id>     - Supprimer
GET    /api/messages/unread-count/<player_id> - Nombre non lus
GET    /api/messages/players                 - Liste des joueurs
```

## 🚀 Déploiement

Le système de messagerie est automatiquement déployé avec l'application.

**Prérequis pour les emails :**
1. Configurer les variables d'environnement MAIL_*
2. Redémarrer l'application
3. Tester l'envoi d'un message admin

Sans configuration email, la messagerie fonctionne normalement mais sans notification email.

## ❓ FAQ

**Q: Puis-je envoyer des messages à plusieurs joueurs ?**
R: Non, actuellement un message = un destinataire. Vous pouvez envoyer plusieurs messages.

**Q: Quels fichiers puis-je joindre ?**
R: PNG, JPG, JPEG, GIF, PDF, TXT, DOC, DOCX jusqu'à 5 MB.

**Q: L'admin voit-il mes messages aux autres joueurs ?**
R: Non, seuls les messages adressés à "admin" sont visibles par l'administrateur.

**Q: Puis-je récupérer un message supprimé ?**
R: Non, la suppression est définitive.

**Q: Combien de temps les messages sont conservés ?**
R: Indéfiniment, jusqu'à ce qu'ils soient supprimés manuellement.

**Q: Y a-t-il une limite de messages ?**
R: Non, mais évitez le spam pour ne pas surcharger le système.
