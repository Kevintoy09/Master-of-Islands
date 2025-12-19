
import React, { useState } from "react";
import { Button, TextField, Typography, Box, Container, Paper, InputAdornment, IconButton, CircularProgress, Alert } from "@mui/material";
import { PersonOutline, LockOutlined, Visibility, VisibilityOff } from "@mui/icons-material";
import { useNavigate, useLocation } from "react-router-dom";
import { useUser } from "../hooks/useUser";
import { getApiUrl } from '../utils/api';
import "../styles/theme.css";
import "../styles/login.css";
// import loginBackground from "../images/login_background.png";
import masterLogo from "../images/master-of-islands-logo.png";

const LoginPage: React.FC = () => {
  const location = useLocation();
  const [username, setUsername] = useState(location.state?.username || "");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState(location.state?.message || "");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showPanel, setShowPanel] = useState(false);
  const [showAdminPrompt, setShowAdminPrompt] = useState(false);
  const [adminPassword, setAdminPassword] = useState("");
  const [adminError, setAdminError] = useState("");
  const navigate = useNavigate();
  const { setUser } = useUser();

  // Délai d'affichage du panel pour admirer l'image de fond
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setShowPanel(true);
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  const handleLogin = async () => {
    setError("");
    setIsLoading(true);
    
    if (!username) {
      setError("Nom d'utilisateur requis.");
      setIsLoading(false);
      return;
    }
    
    try {
      const response = await fetch(`${getApiUrl()}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      
      if (!response.ok) {
        throw new Error("Login échoué");
      }
      
      const data = await response.json();
      
      const userData = {
        id: data.id,
        username: data.username,
        cities: data.city_ids || [],
        research_points: data.research_points || 0,
      };
      
      setUser(userData);
      // La redirection sera gérée automatiquement par AuthRedirect
    } catch (e) {
      setError("Nom d'utilisateur ou mot de passe incorrect");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleLogin();
    }
  };

  const handleAdminAccess = () => {
    if (adminPassword === "admin") {
      window.open(`${getApiUrl()}/admin`, '_blank');
      setShowAdminPrompt(false);
      setAdminPassword("");
      setAdminError("");
    } else {
      setAdminError("Mot de passe incorrect");
      setAdminPassword("");
    }
  };

  const handleAdminKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleAdminAccess();
    } else if (event.key === 'Escape') {
      setShowAdminPrompt(false);
      setAdminPassword("");
      setAdminError("");
    }
  };

  return (
    <div 
      className="login-background"
      style={{
        backgroundImage: `linear-gradient(
          rgba(47, 27, 20, 0.7), 
          rgba(47, 27, 20, 0.5)
        ), url(/assets/pages/login_page.jpg)`
      }}
    >
      <Container maxWidth="sm" className="login-container">
        {showPanel && (
        <Paper elevation={12} className="login-panel roman-panel" sx={{ 
          animation: 'slideInUp 0.6s ease-out',
          '@keyframes slideInUp': {
            from: { transform: 'translateY(50px)', opacity: 0 },
            to: { transform: 'translateY(0)', opacity: 1 }
          }
        }}>
          {/* En-tête avec logo et titre du jeu */}
          <Box className="login-header">
            <Box 
              component="img" 
              src={masterLogo} 
              alt="Master of Islands Logo" 
              className="login-logo"
              sx={{
                width: '100px',
                height: 'auto',
                margin: '0 auto 0.5rem',
                display: 'block',
                filter: 'drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3))',
                animation: 'float 3s ease-in-out infinite'
              }}
            />
            <Typography variant="h3" className="roman-title game-title" align="center" sx={{ textTransform: 'uppercase', mb: 8.4 }}>
              Master of Islands
            </Typography>
            <Typography variant="h6" className="roman-subtitle game-subtitle" align="center">
              Devenez le Maître des Îles
            </Typography>
          </Box>

          {/* Frise grecque séparatrice */}
          <Box 
            component="img" 
            src="/assets/components/ancient-greek-meander.svg" 
            alt="Frise grecque" 
            sx={{
              width: '170%',
              height: '20px',
              margin: '0.8rem 0',
              opacity: 0.6,
              position: 'relative',
              left: '-35%'
            }}
          />

          {/* Formulaire de connexion */}
          <Box className="login-form">
            <TextField
              label="Nom d'utilisateur"
              variant="outlined"
              fullWidth
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyPress={handleKeyPress}
              className="roman-input"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <PersonOutline className="input-icon" />
                  </InputAdornment>
                ),
              }}
              sx={{
                marginBottom: 1.5,
                '& .MuiOutlinedInput-root': {
                  '& fieldset': { borderColor: 'var(--bronze)' },
                  '&:hover fieldset': { borderColor: 'var(--roman-gold)' },
                  '&.Mui-focused fieldset': { borderColor: 'var(--roman-gold)' },
                },
              }}
            />

            <TextField
              label="Mot de passe"
              type={showPassword ? 'text' : 'password'}
              variant="outlined"
              fullWidth
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyPress={handleKeyPress}
              className="roman-input"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LockOutlined className="input-icon" />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                      className="password-toggle"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{
                marginBottom: 1.5,
                '& .MuiOutlinedInput-root': {
                  '& fieldset': { borderColor: 'var(--bronze)' },
                  '&:hover fieldset': { borderColor: 'var(--roman-gold)' },
                  '&.Mui-focused fieldset': { borderColor: 'var(--roman-gold)' },
                },
              }}
            />

            {successMessage && (
              <Alert severity="success" sx={{ mb: 2 }}>
                {successMessage}
              </Alert>
            )}

            {error && (
              <Box className="error-message" sx={{ mb: 2 }}>
                <Typography color="error" className="roman-text">
                  ⚠️ {error}
                </Typography>
              </Box>
            )}

            {/* Boutons d'action */}
            <Box className="login-actions">
              <Button
                variant="contained"
                fullWidth
                size="large"
                onClick={handleLogin}
                disabled={isLoading}
                className="roman-button primary-button"
                sx={{ 
                  mb: 1.5, 
                  minHeight: '44px',
                  fontSize: { xs: '0.95rem', sm: '1rem' }
                }}
              >
                {isLoading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  '🏛️ Se connecter'
                )}
              </Button>

              <Button
                variant="outlined"
                fullWidth
                size="large"
                onClick={() => navigate("/create-account")}
                className="roman-button secondary-button"
                sx={{ 
                  mb: 1,
                  minHeight: '44px',
                  fontSize: { xs: '0.95rem', sm: '1rem' },
                  borderColor: 'var(--bronze)',
                  color: 'var(--roman-red)',
                  '&:hover': {
                    borderColor: 'var(--roman-gold)',
                    backgroundColor: 'rgba(218, 165, 32, 0.1)'
                  }
                }}
              >
                ⚔️ Créer un compte
              </Button>

              <Button
                variant="text"
                fullWidth
                size="large"
                onClick={() => navigate("/world")}
                className="world-access-button"
                sx={{ 
                  color: 'var(--roman-green)',
                  fontWeight: 'bold',
                  fontSize: { xs: '0.85rem', sm: '0.95rem' },
                  minHeight: '40px',
                  mb: 0.13
                }}
              >
                🌍 Carte du Monde
              </Button>

              <Button
                variant="text"
                fullWidth
                size="small"
                onClick={() => setShowAdminPrompt(true)}
                sx={{ 
                  color: 'rgba(218, 165, 32, 0.5)',
                  fontSize: '0.75rem',
                  mt: 0.33,
                  '&:hover': {
                    color: 'var(--roman-gold)',
                    backgroundColor: 'rgba(218, 165, 32, 0.05)'
                  }
                }}
              >
                ⚙️ Administration
              </Button>
            </Box>
          </Box>

          {/* Footer avec version */}
          <Box className="login-footer">
            <Typography variant="caption" className="roman-text" align="center" sx={{ opacity: 0.7 }}>
              Master of Islands v1.0 - Grèce Antique
            </Typography>
          </Box>
        </Paper>
        )}

        {/* Popup Admin Password */}
        {showAdminPrompt && (
          <Box
            sx={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 9999,
            }}
            onClick={() => {
              setShowAdminPrompt(false);
              setAdminPassword("");
              setAdminError("");
            }}
          >
            <Paper
              elevation={24}
              className="roman-panel"
              onClick={(e) => e.stopPropagation()}
              sx={{
                padding: 4,
                minWidth: { xs: '90%', sm: '400px' },
                maxWidth: '500px',
                backgroundColor: 'var(--roman-beige)',
                border: '3px solid var(--roman-gold)',
                borderRadius: '8px',
              }}
            >
              <Typography variant="h5" className="roman-title" align="center" sx={{ mb: 3, color: 'var(--roman-red)' }}>
                🔐 Accès Administration
              </Typography>

              <TextField
                fullWidth
                type="password"
                label="Mot de passe administrateur"
                value={adminPassword}
                onChange={(e) => {
                  setAdminPassword(e.target.value);
                  setAdminError("");
                }}
                onKeyPress={handleAdminKeyPress}
                autoFocus
                className="roman-input"
                sx={{ mb: 2 }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <LockOutlined sx={{ color: 'var(--roman-gold)' }} />
                    </InputAdornment>
                  ),
                }}
              />

              {adminError && (
                <Typography color="error" align="center" sx={{ mb: 2, fontWeight: 'bold' }}>
                  ⚠️ {adminError}
                </Typography>
              )}

              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  fullWidth
                  onClick={handleAdminAccess}
                  className="roman-button primary-button"
                  sx={{ minHeight: '44px' }}
                >
                  ✓ Accéder
                </Button>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => {
                    setShowAdminPrompt(false);
                    setAdminPassword("");
                    setAdminError("");
                  }}
                  className="roman-button secondary-button"
                  sx={{ minHeight: '44px' }}
                >
                  ✗ Annuler
                </Button>
              </Box>

              <Typography variant="caption" align="center" sx={{ display: 'block', mt: 2, opacity: 0.6 }}>
                Appuyez sur Échap pour annuler
              </Typography>
            </Paper>
          </Box>
        )}
      </Container>
    </div>
  );
};

export default LoginPage;
