"""
Système de messagerie interne du jeu
Permet aux joueurs de communiquer entre eux et avec l'administration
"""
import os
import json
import time
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app.data_manager import DataManager

messages_bp = Blueprint('messages', __name__)
# Initialiser DataManager avec le bon base_dir
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dm = DataManager(BASE_DIR)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'attachments')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'doc', 'docx'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# Créer le dossier uploads si nécessaire
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_messages():
    """Charge les messages depuis le fichier JSON"""
    messages_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'messages.json')
    try:
        with open(messages_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_messages(messages):
    """Sauvegarde les messages dans le fichier JSON"""
    messages_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'messages.json')
    with open(messages_file, 'w', encoding='utf-8') as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)

def send_email_notification(sender_name, subject, content, attachment_url=None):
    """
    Sauvegarde la notification d'email pour l'admin dans un fichier JSON.
    L'admin peut ensuite consulter ces notifications et envoyer des emails manuellement
    ou configurer un système externe pour les envoyer automatiquement.
    """
    try:
        notifications_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'admin_email_notifications.json')
        
        # Charger les notifications existantes
        try:
            with open(notifications_file, 'r', encoding='utf-8') as f:
                notifications = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            notifications = []
        
        # Créer la nouvelle notification
        notification = {
            'id': f"email_{int(time.time() * 1000)}",
            'timestamp': datetime.now().isoformat(),
            'to': 'contact@masterofisland.com',
            'from': sender_name,
            'subject': f"[Master of Island] {subject}",
            'content': content,
            'attachment_url': attachment_url,
            'sent': False
        }
        
        notifications.append(notification)
        
        # Sauvegarder
        with open(notifications_file, 'w', encoding='utf-8') as f:
            json.dump(notifications, f, indent=2, ensure_ascii=False)
        
        print(f"📧 Notification email enregistrée pour contact@masterofisland.com depuis {sender_name}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'enregistrement de la notification : {str(e)}")
        return False

@messages_bp.route('/api/messages/send', methods=['POST'])
def send_message():
    """Envoyer un message à un autre joueur ou à l'admin"""
    data = request.json
    
    sender_id = data.get('sender_id')
    recipient_id = data.get('recipient_id')
    subject = data.get('subject', '(Sans objet)')
    content = data.get('content', '')
    is_admin_message = data.get('is_admin_message', False)
    
    if not sender_id or not recipient_id or not content:
        return jsonify({'error': 'Expéditeur, destinataire et contenu requis'}), 400
    
    messages = load_messages()
    
    new_message = {
        'id': f"msg_{int(time.time() * 1000)}",
        'sender_id': sender_id,
        'recipient_id': recipient_id,
        'subject': subject,
        'content': content,
        'timestamp': datetime.now().isoformat(),
        'read': False,
        'is_admin_message': is_admin_message,
        'attachment': None,
        'deleted_by_sender': False,
        'deleted_by_recipient': False
    }
    
    messages.append(new_message)
    save_messages(messages)
    
    # Si c'est un message pour l'admin, créer une notification email
    if recipient_id == 'admin':
        players_data = dm.load_players()
        players = players_data.get('players', [])
        sender = next((p for p in players if p['id'] == sender_id), None)
        sender_name = sender['username'] if sender else sender_id
        send_email_notification(sender_name, subject, content)
    
    return jsonify({
        'success': True,
        'message': 'Message envoyé avec succès',
        'message_id': new_message['id']
    })

@messages_bp.route('/api/messages/send-with-attachment', methods=['POST'])
def send_message_with_attachment():
    """Envoyer un message avec pièce jointe (pour contacter l'admin)"""
    sender_id = request.form.get('sender_id')
    recipient_id = request.form.get('recipient_id', 'admin')
    subject = request.form.get('subject', '(Sans objet)')
    content = request.form.get('content', '')
    
    if not sender_id or not content:
        return jsonify({'error': 'Expéditeur et contenu requis'}), 400
    
    attachment_path = None
    
    # Gérer la pièce jointe si présente
    if 'attachment' in request.files:
        file = request.files['attachment']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = int(time.time() * 1000)
            unique_filename = f"{timestamp}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(filepath)
            attachment_path = f"uploads/attachments/{unique_filename}"
    
    messages = load_messages()
    
    new_message = {
        'id': f"msg_{int(time.time() * 1000)}",
        'sender_id': sender_id,
        'recipient_id': recipient_id,
        'subject': subject,
        'content': content,
        'timestamp': datetime.now().isoformat(),
        'read': False,
        'is_admin_message': True,
        'attachment': attachment_path,
        'deleted_by_sender': False,
        'deleted_by_recipient': False
    }
    
    messages.append(new_message)
    save_messages(messages)
    
    # Créer une notification email pour l'administrateur
    players_data = dm.load_players()
    players = players_data.get('players', [])
    sender = next((p for p in players if p['id'] == sender_id), None)
    sender_name = sender['username'] if sender else sender_id
    
    # URL de la pièce jointe si présente
    attachment_url = None
    if attachment_path:
        base_url = request.url_root.rstrip('/')
        attachment_url = f"{base_url}/{attachment_path}"
    
    send_email_notification(sender_name, subject, content, attachment_url)
    
    return jsonify({
        'success': True,
        'message': 'Message envoyé à l\'administrateur avec succès',
        'message_id': new_message['id']
    })

@messages_bp.route('/api/messages/inbox/<player_id>', methods=['GET'])
def get_inbox(player_id):
    """Récupérer les messages reçus par un joueur"""
    messages = load_messages()
    
    inbox = [
        msg for msg in messages
        if msg['recipient_id'] == player_id and not msg['deleted_by_recipient']
    ]
    
    # Trier par date décroissante (plus récent d'abord)
    inbox.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Charger les infos des expéditeurs
    players_data = dm.load_players()
    players = players_data.get('players', [])
    
    for msg in inbox:
        if msg['sender_id'] == 'admin':
            msg['sender_name'] = 'Administrateur'
        else:
            sender = next((p for p in players if p['id'] == msg['sender_id']), None)
            msg['sender_name'] = sender.get('username', 'Joueur inconnu') if sender else 'Joueur inconnu'
    
    return jsonify({
        'messages': inbox,
        'unread_count': sum(1 for msg in inbox if not msg['read'])
    })

@messages_bp.route('/api/messages/sent/<player_id>', methods=['GET'])
def get_sent(player_id):
    """Récupérer les messages envoyés par un joueur"""
    messages = load_messages()
    
    sent = [
        msg for msg in messages
        if msg['sender_id'] == player_id and not msg['deleted_by_sender']
    ]
    
    # Trier par date décroissante
    sent.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Charger les infos des destinataires
    players_data = dm.load_players()
    players = players_data.get('players', [])
    
    for msg in sent:
        if msg['recipient_id'] == 'admin':
            msg['recipient_name'] = 'Administrateur'
        else:
            recipient = next((p for p in players if p['id'] == msg['recipient_id']), None)
            msg['recipient_name'] = recipient.get('username', 'Joueur inconnu') if recipient else 'Joueur inconnu'
    
    return jsonify({'messages': sent})

@messages_bp.route('/api/messages/read/<message_id>', methods=['POST'])
def mark_as_read(message_id):
    """Marquer un message comme lu"""
    messages = load_messages()
    
    for msg in messages:
        if msg['id'] == message_id:
            msg['read'] = True
            save_messages(messages)
            return jsonify({'success': True})
    
    return jsonify({'error': 'Message non trouvé'}), 404

@messages_bp.route('/api/messages/delete/<message_id>', methods=['POST'])
def delete_message(message_id):
    """Supprimer un message (soft delete)"""
    data = request.json
    player_id = data.get('player_id')
    
    if not player_id:
        return jsonify({'error': 'ID joueur requis'}), 400
    
    messages = load_messages()
    
    for msg in messages:
        if msg['id'] == message_id:
            # Soft delete : marquer comme supprimé selon le rôle du joueur
            if msg['sender_id'] == player_id:
                msg['deleted_by_sender'] = True
            if msg['recipient_id'] == player_id:
                msg['deleted_by_recipient'] = True
            
            save_messages(messages)
            return jsonify({'success': True})
    
    return jsonify({'error': 'Message non trouvé'}), 404

@messages_bp.route('/api/messages/unread-count/<player_id>', methods=['GET'])
def get_unread_count(player_id):
    """Obtenir le nombre de messages non lus"""
    messages = load_messages()
    
    unread = sum(
        1 for msg in messages
        if msg['recipient_id'] == player_id 
        and not msg['read'] 
        and not msg['deleted_by_recipient']
    )
    
    return jsonify({'unread_count': unread})

@messages_bp.route('/api/messages/players', methods=['GET'])
def get_players_list():
    """Récupérer la liste des joueurs pour composer un message"""
    players_data = dm.load_players()
    players = players_data.get('players', [])
    
    players_list = [
        {
            'id': p['id'],
            'username': p['username']
        }
        for p in players
        if p.get('username')
    ]
    
    return jsonify({'players': players_list})
