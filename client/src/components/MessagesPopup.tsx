import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Box, Typography, Tab, Tabs, Button, Paper, List, ListItem, ListItemButton, ListItemText, Badge, IconButton, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import { Mail, MailOutline, Send, Delete, Attachment, AdminPanelSettings } from '@mui/icons-material';
import { useUser } from '../hooks/useUser';
import { getApiUrl } from '../utils/api';
import '../styles/menu.css';

interface Message {
  id: string;
  sender_id: string;
  sender_name?: string;
  recipient_id: string;
  recipient_name?: string;
  subject: string;
  content: string;
  timestamp: string;
  read: boolean;
  is_admin_message: boolean;
  attachment?: string | null;
}

interface MessagesPopupProps {
  isOpen: boolean;
  onClose: () => void;
  preselectedRecipient?: string;
}

const MessagesPopup: React.FC<MessagesPopupProps> = ({ isOpen, onClose, preselectedRecipient }) => {
  const { user } = useUser();
  const [searchParams] = useSearchParams();
  const [tab, setTab] = useState(0); // 0: Boîte de réception, 1: Envoyés
  const [inbox, setInbox] = useState<Message[]>([]);
  const [sent, setSent] = useState<Message[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [composeOpen, setComposeOpen] = useState(false);
  const [adminMessageOpen, setAdminMessageOpen] = useState(false);
  const [players, setPlayers] = useState<Array<{ id: string; username: string }>>([]);

  // Champs pour composer un message
  const [recipientId, setRecipientId] = useState('');
  const [subject, setSubject] = useState('');
  const [content, setContent] = useState('');
  const [attachment, setAttachment] = useState<File | null>(null);

  // Ouvrir automatiquement le dialog de composition si un destinataire est fourni
  useEffect(() => {
    if (preselectedRecipient && !composeOpen) {
      setRecipientId(preselectedRecipient);
      setComposeOpen(true);
    }
  }, [preselectedRecipient]);

  useEffect(() => {
    if (isOpen && user?.id) {
      loadInbox();
      loadSent();
      loadPlayers();
    }
  }, [isOpen, user?.id]);

  const loadInbox = async () => {
    try {
      const url = `${getApiUrl()}/api/messages/inbox/${user.id}`;
      const response = await fetch(url);
      const data = await response.json();
      setInbox(data.messages || []);
      setUnreadCount(data.unread_count || 0);
    } catch (error) {
      console.error('❌ [MessagesPopup] Erreur chargement boîte de réception:', error);
    }
  };

  const loadSent = async () => {
    try {
      const url = `${getApiUrl()}/api/messages/sent/${user.id}`;
      const response = await fetch(url);
      const data = await response.json();
      setSent(data.messages || []);
    } catch (error) {
      console.error('❌ [MessagesPopup] Erreur chargement messages envoyés:', error);
    }
  };

  const loadPlayers = async () => {
    try {
      const url = `${getApiUrl()}/api/messages/players`;
      const response = await fetch(url);
      const data = await response.json();
      setPlayers(data.players || []);
    } catch (error) {
      console.error('❌ [MessagesPopup] Erreur chargement liste joueurs:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!recipientId || !content) {
      alert('Veuillez remplir tous les champs requis');
      return;
    }

    try {
      const response = await fetch(`${getApiUrl()}/api/messages/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sender_id: user.id,
          recipient_id: recipientId,
          subject: subject || '(Pas de sujet)',
          content
        })
      });

      if (response.ok) {
        alert('Message envoyé !');
        setComposeOpen(false);
        setRecipientId('');
        setSubject('');
        setContent('');
        loadSent(); // Recharger les messages envoyés
      } else {
        alert('Erreur lors de l\'envoi du message');
      }
    } catch (error) {
      console.error('Erreur envoi message:', error);
      alert('Erreur réseau');
    }
  };

  const handleSendAdminMessage = async () => {
    if (!content) {
      alert('Veuillez remplir le message');
      return;
    }

    try {
      if (attachment) {
        // Envoi avec pièce jointe
        const formData = new FormData();
        formData.append('sender_id', String(user.id));
        formData.append('subject', subject || '(Support)');
        formData.append('content', content);
        formData.append('attachment', attachment);

        const response = await fetch(`${getApiUrl()}/api/messages/send-with-attachment`, {
          method: 'POST',
          body: formData
        });

        if (response.ok) {
          alert('Message envoyé à l\'administrateur !');
          setAdminMessageOpen(false);
          setSubject('');
          setContent('');
          setAttachment(null);
          loadSent();
        } else {
          alert('Erreur lors de l\'envoi');
        }
      } else {
        // Envoi simple
        const response = await fetch(`${getApiUrl()}/api/messages/send`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sender_id: user.id,
            recipient_id: 'admin',
            subject: subject || '(Support)',
            content,
            is_admin_message: true
          })
        });

        if (response.ok) {
          alert('Message envoyé à l\'administrateur !');
          setAdminMessageOpen(false);
          setSubject('');
          setContent('');
          loadSent();
        } else {
          alert('Erreur lors de l\'envoi');
        }
      }
    } catch (error) {
      console.error('Erreur envoi message admin:', error);
      alert('Erreur réseau');
    }
  };

  const handleReadMessage = async (msg: Message) => {
    setSelectedMessage(msg);
    
    if (!msg.read && tab === 0) {
      try {
        await fetch(`${getApiUrl()}/api/messages/read/${msg.id}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ player_id: user.id })
        });
        loadInbox(); // Recharger pour mettre à jour le statut
      } catch (error) {
        console.error('Erreur marquage message lu:', error);
      }
    }
  };

  const handleDeleteMessage = async (messageId: string) => {
    if (!window.confirm('Supprimer ce message ?')) return;

    try {
      await fetch(`${getApiUrl()}/api/messages/delete/${messageId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_id: user.id })
      });
      
      if (tab === 0) loadInbox();
      else loadSent();
      
      setSelectedMessage(null);
    } catch (error) {
      console.error('Erreur suppression message:', error);
    }
  };

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'À l\'instant';
    if (diffMins < 60) return `Il y a ${diffMins}min`;
    if (diffHours < 24) return `Il y a ${diffHours}h`;
    if (diffDays < 7) return `Il y a ${diffDays}j`;
    return date.toLocaleDateString('fr-FR');
  };

  const messages = tab === 0 ? inbox : sent;

  if (!isOpen) return null;

  return (
    <div className="popup-overlay" onClick={onClose}>
      <div className="popup-base" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '900px', maxHeight: '80vh', overflow: 'auto' }}>
        <button className="popup-close-button" onClick={onClose}>×</button>
        
        <div className="popup-content">
          <h3 className="popup-title">📬 Messagerie</h3>

          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <Button variant="contained" onClick={() => setComposeOpen(true)}>
              ✉️ Nouveau message
            </Button>
            <Button variant="outlined" onClick={() => setAdminMessageOpen(true)}>
              🛠️ Contacter l'admin
            </Button>
          </Box>

          <Tabs value={tab} onChange={(e, newValue) => setTab(newValue)}>
            <Tab label={`📥 Reçus (${inbox.length})`} />
            <Tab label={`📤 Envoyés (${sent.length})`} />
          </Tabs>

          <Paper sx={{ mt: 2, p: 2, maxHeight: '400px', overflow: 'auto' }}>
            <List>
              {messages.length === 0 ? (
                <ListItem>
                  <ListItemText primary="Aucun message" />
                </ListItem>
              ) : (
                messages.map((msg) => (
                  <ListItem
                    key={msg.id}
                    disablePadding
                    sx={{
                      bgcolor: !msg.read && tab === 0 ? 'action.hover' : 'inherit',
                      borderBottom: '1px solid',
                      borderColor: 'divider',
                    }}
                  >
                    <ListItemButton onClick={() => handleReadMessage(msg)}>
                      <IconButton size="small" sx={{ mr: 1 }}>
                        {!msg.read && tab === 0 ? <Mail color="primary" /> : <MailOutline />}
                      </IconButton>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="subtitle2" fontWeight={!msg.read && tab === 0 ? 'bold' : 'normal'}>
                              {tab === 0 ? msg.sender_name : msg.recipient_name}
                            </Typography>
                            {msg.is_admin_message && <AdminPanelSettings fontSize="small" color="warning" />}
                            {msg.attachment && <Attachment fontSize="small" />}
                          </Box>
                        }
                        secondary={
                          <>
                            <Typography variant="body2" fontWeight={!msg.read && tab === 0 ? 'bold' : 'normal'}>
                              {msg.subject}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {formatDate(msg.timestamp)}
                            </Typography>
                          </>
                        }
                      />
                    </ListItemButton>
                  </ListItem>
                ))
              )}
            </List>
          </Paper>

          {selectedMessage && (
            <Paper sx={{ mt: 2, p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">{selectedMessage.subject}</Typography>
                <IconButton onClick={() => handleDeleteMessage(selectedMessage.id)}>
                  <Delete />
                </IconButton>
              </Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                De: {selectedMessage.sender_name} | {formatDate(selectedMessage.timestamp)}
              </Typography>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', mt: 2 }}>
                {selectedMessage.content}
              </Typography>
              {selectedMessage.attachment && (
                <Button href={selectedMessage.attachment} target="_blank" sx={{ mt: 2 }}>
                  📎 Pièce jointe
                </Button>
              )}
            </Paper>
          )}
        </div>

        {/* Dialog Composer un message */}
        <Dialog open={composeOpen} onClose={() => setComposeOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>✉️ Nouveau message</DialogTitle>
          <DialogContent>
            <FormControl fullWidth sx={{ mt: 2 }}>
              <InputLabel>Destinataire</InputLabel>
              <Select value={recipientId} onChange={(e) => setRecipientId(e.target.value)}>
                {players.map((p) => (
                  <MenuItem key={p.id} value={p.id}>{p.username}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Sujet"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              sx={{ mt: 2 }}
            />
            <TextField
              fullWidth
              label="Message"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              multiline
              rows={4}
              sx={{ mt: 2 }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setComposeOpen(false)}>Annuler</Button>
            <Button onClick={handleSendMessage} variant="contained" startIcon={<Send />}>
              Envoyer
            </Button>
          </DialogActions>
        </Dialog>

        {/* Dialog Contacter l'admin */}
        <Dialog 
          open={adminMessageOpen} 
          onClose={() => {
            setAdminMessageOpen(false);
            setSubject('');
            setContent('');
            setAttachment(null);
          }} 
          maxWidth="sm" 
          fullWidth
          PaperProps={{
            sx: {
              position: 'fixed',
              zIndex: 10000
            }
          }}
        >
          <DialogTitle>🛠️ Contacter l'administrateur</DialogTitle>
          <DialogContent sx={{ pt: 3 }}>
            <TextField
              fullWidth
              label="Sujet"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              sx={{ mt: 2 }}
            />
            <TextField
              fullWidth
              label="Message"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              multiline
              rows={4}
              sx={{ mt: 2 }}
            />
            <Button variant="outlined" component="label" sx={{ mt: 2 }}>
              📎 Joindre un fichier
              <input type="file" hidden onChange={(e) => setAttachment(e.target.files?.[0] || null)} />
            </Button>
            {attachment && <Typography variant="caption" sx={{ ml: 2 }}>{attachment.name}</Typography>}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setAdminMessageOpen(false)}>Annuler</Button>
            <Button onClick={handleSendAdminMessage} variant="contained" startIcon={<Send />}>
              Envoyer
            </Button>
          </DialogActions>
        </Dialog>
      </div>
    </div>
  );
};

export default MessagesPopup;
