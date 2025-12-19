import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../hooks/useUser';
import './SettingsPage.css';

const SettingsPage: React.FC = () => {
    const { user, setUser, logout } = useUser();
    const navigate = useNavigate();
    
    const [username, setUsername] = useState(user?.username || '');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);
    
    // Charger l'email depuis le profil au démarrage
    useEffect(() => {
        const loadProfile = async () => {
            if (!user?.id) return;
            
            try {
                const response = await fetch(`/api/settings/profile?player_id=${user.id}`);
                
                if (!response.ok) {
                    setError('Erreur lors du chargement du profil');
                    return;
                }
                
                const data = await response.json();
                setEmail(data.email || '');
            } catch (err) {
                setError('Erreur de connexion');
            }
        };
        loadProfile();
    }, [user?.id]);

    const handleUpdateUsername = async () => {
        if (username.length < 3 || username.length > 20) {
            setError('Le nom d\'utilisateur doit contenir entre 3 et 20 caractères');
            return;
        }

        setLoading(true);
        setError('');
        setSuccess('');

        try {
            const response = await fetch('/api/settings/update-username', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    player_id: user?.id,
                    username: username
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Erreur lors de la mise à jour');
            }

            setSuccess('✅ Nom d\'utilisateur modifié avec succès');
            
            // Mettre à jour le contexte
            if (user) {
                setUser({ ...user, username: data.username });
            }
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleUpdateEmail = async () => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            setError('Format d\'email invalide');
            return;
        }

        setLoading(true);
        setError('');
        setSuccess('');

        try {
            const response = await fetch('/api/settings/update-email', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    player_id: user?.id,
                    email: email
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Erreur lors de la mise à jour');
            }

            setSuccess('✅ Email modifié avec succès (vérification requise)');
            
            // L'email est stocké dans le profil, pas dans UserState
            // On met juste à jour l'état local
            setEmail(data.email);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleUpdatePassword = async () => {
        if (password.length < 4) {
            setError('Le mot de passe doit contenir au moins 4 caractères');
            return;
        }

        setLoading(true);
        setError('');
        setSuccess('');

        try {
            const response = await fetch('/api/settings/update-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    player_id: user?.id,
                    password: password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Erreur lors de la mise à jour');
            }

            setSuccess('✅ Mot de passe modifié avec succès');
            setPassword('');
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteAccount = async () => {
        setLoading(true);
        setError('');

        try {
            const response = await fetch('/api/settings/delete-account', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    player_id: user?.id
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Erreur lors de la suppression');
            }

            // Déconnexion et redirection vers la page de connexion
            logout();
            navigate('/');
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
            setShowDeleteConfirm(false);
        }
    };

    return (
        <div className="settings-page">
            <div className="settings-header">
                <button className="back-button" onClick={() => navigate('/profile')}>
                    ← Retour au profil
                </button>
                <h1>⚙️ Paramètres du compte</h1>
            </div>

            <div className="settings-content">
                {error && <div className="error-message">{error}</div>}
                {success && <div className="success-message">{success}</div>}

                {/* Section 1: Changer le nom d'utilisateur */}
                <div className="settings-section">
                    <h2>Nom d'utilisateur</h2>
                    <div className="input-group">
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Nouveau nom d'utilisateur"
                            disabled={loading}
                        />
                        <button onClick={handleUpdateUsername} disabled={loading}>
                            {loading ? 'Mise à jour...' : 'Mettre à jour'}
                        </button>
                    </div>
                    <p className="hint">Entre 3 et 20 caractères</p>
                </div>

                {/* Section 2: Modifier l'email */}
                <div className="settings-section">
                    <h2>Adresse e-mail</h2>
                    <div className="input-group">
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="Nouvelle adresse e-mail"
                            disabled={loading}
                        />
                        <button onClick={handleUpdateEmail} disabled={loading}>
                            {loading ? 'Mise à jour...' : 'Mettre à jour'}
                        </button>
                    </div>
                    <p className="hint">Format: utilisateur@example.com</p>
                </div>

                {/* Section 3: Modifier le mot de passe */}
                <div className="settings-section">
                    <h2>Mot de passe</h2>
                    <div className="input-group">
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Nouveau mot de passe"
                            disabled={loading}
                        />
                        <button onClick={handleUpdatePassword} disabled={loading}>
                            {loading ? 'Mise à jour...' : 'Mettre à jour'}
                        </button>
                    </div>
                    <p className="hint">Minimum 4 caractères</p>
                </div>

                {/* Section 4: Supprimer le compte */}
                <div className="settings-section danger-zone">
                    <h2>⚠️ Zone dangereuse</h2>
                    <button 
                        className="delete-button" 
                        onClick={() => setShowDeleteConfirm(true)}
                        disabled={loading}
                    >
                        Supprimer définitivement mon compte
                    </button>
                </div>
            </div>

            {/* Modal de confirmation de suppression */}
            {showDeleteConfirm && (
                <div className="modal-overlay" onClick={() => setShowDeleteConfirm(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <h2>⚠️ Supprimer votre compte ?</h2>
                        <p>Cette action est <strong>DÉFINITIVE</strong> et supprimera :</p>
                        <ul>
                            <li>Toutes vos villes et ressources</li>
                            <li>Tous vos héros et unités</li>
                            <li>Toutes vos recherches et améliorations</li>
                            <li>Tous vos messages et notifications</li>
                            <li>Votre profil et vos statistiques</li>
                            <li>Votre progression et vos quêtes</li>
                        </ul>
                        <p className="warning-text">
                            ⛔ Vous ne pourrez <strong>PAS</strong> récupérer ces données !
                        </p>
                        <div className="modal-buttons">
                            <button 
                                className="cancel-button" 
                                onClick={() => setShowDeleteConfirm(false)}
                            >
                                Annuler
                            </button>
                            <button 
                                className="confirm-delete-button" 
                                onClick={handleDeleteAccount}
                                disabled={loading}
                            >
                                {loading ? 'Suppression...' : 'Oui, supprimer mon compte'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SettingsPage;
