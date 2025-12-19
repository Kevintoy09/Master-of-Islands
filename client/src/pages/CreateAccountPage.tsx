import React, { useState } from "react";
import { Button, TextField, Typography, Box, Container, Paper, InputAdornment, IconButton, CircularProgress, MenuItem, Checkbox, FormControlLabel, Divider, Stepper, Step, StepLabel, Alert } from "@mui/material";
import { PersonOutline, LockOutlined, Visibility, VisibilityOff, Email, Phone, LocationOn, CalendarToday, Flag, Person } from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import { getApiUrl } from '../utils/api';
import { useUser } from '../hooks/useUser';
import "../styles/theme.css";
import "../styles/login.css";
import masterLogo from "../images/master-of-islands-logo.png";

const CreateAccountPage: React.FC = () => {
  // États du formulaire de base
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [email, setEmail] = useState("");
  
  // États du profil complet
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [country, setCountry] = useState("");
  const [city, setCity] = useState("");
  const [phone, setPhone] = useState("");
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [acceptNewsletter, setAcceptNewsletter] = useState(false);
  
  // États UI
  const [activeStep, setActiveStep] = useState(0);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showPanel, setShowPanel] = useState(false);
  
  // États pour vérification username
  const [usernameStatus, setUsernameStatus] = useState<'idle' | 'checking' | 'available' | 'taken'>('idle');
  const [usernameMessage, setUsernameMessage] = useState("");
  const navigate = useNavigate();
  const { setUser } = useUser();

  // Délai d'affichage du panel pour admirer l'image de fond
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setShowPanel(true);
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  const countries = [
    'France', 'Belgique', 'Suisse', 'Canada', 'Maroc', 'Tunisie', 'Algérie',
    'Allemagne', 'Espagne', 'Italie', 'Portugal', 'Royaume-Uni', 'États-Unis', 'Grèce',
    'Autre'
  ];
  
  const steps = ['Compte', 'Profil', 'Confirmation'];

  const validateStep = (step: number): boolean => {
    switch (step) {
      case 0: // Compte
        if (!username.trim()) {
          setError("Nom d'utilisateur requis");
          return false;
        }
        if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
          setError("Email valide requis");
          return false;
        }
        if (!password.trim()) {
          setError("Le mot de passe est requis");
          return false;
        }
        if (password !== confirmPassword) {
          setError("Les mots de passe ne correspondent pas");
          return false;
        }
        return true;
      case 1: // Profil
        if (!firstName.trim() || !lastName.trim()) {
          setError("Nom et prénom sont requis");
          return false;
        }
        if (!country) {
          setError("Veuillez sélectionner votre pays");
          return false;
        }
        return true;
      case 2: // Confirmation
        if (!acceptTerms) {
          setError("Vous devez accepter les conditions d'utilisation");
          return false;
        }
        return true;
      default:
        return true;
    }
  };

  const handleNext = () => {
    setError("");
    if (validateStep(activeStep)) {
      if (activeStep === steps.length - 1) {
        handleCreateAccount();
      } else {
        setActiveStep(prev => prev + 1);
      }
    }
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
    setError("");
  };

  const checkUsernameAvailability = async (usernameToCheck: string) => {
    if (!usernameToCheck.trim() || usernameToCheck.length < 2) {
      setUsernameStatus('idle');
      setUsernameMessage("");
      return;
    }

    setUsernameStatus('checking');
    setUsernameMessage("Vérification...");

    try {
      const response = await fetch(`${getApiUrl()}/api/check-username/${encodeURIComponent(usernameToCheck)}`);
      const data = await response.json();
      
      if (data.available) {
        setUsernameStatus('available');
        setUsernameMessage("✓ Nom d'utilisateur disponible");
      } else {
        setUsernameStatus('taken');
        setUsernameMessage(data.message || "Nom d'utilisateur non disponible");
      }
    } catch (e) {
      setUsernameStatus('idle');
      setUsernameMessage("");
    }
  };

  const handleUsernameChange = (newUsername: string) => {
    setUsername(newUsername);
    // Déboucer la vérification
    const timeoutId = setTimeout(() => {
      checkUsernameAvailability(newUsername);
    }, 500);
    
    return () => clearTimeout(timeoutId);
  };

  const handleCreateAccount = async () => {
    setError("");
    setIsLoading(true);
    
    try {
      const accountData = {
        // Données de compte
        username: username.trim(),
        password: password,
        email: email.trim(),
        
        // Données de profil
        profile: {
          firstName: firstName.trim(),
          lastName: lastName.trim(),
          birthDate: birthDate,
          country: country,
          city: city.trim(),
          phone: phone.trim(),
          newsletter: acceptNewsletter,
          createdAt: new Date().toISOString()
        }
      };
      
      const response = await fetch(`${getApiUrl()}/create-account-complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(accountData),
      });
      
      const data = await response.json();
      if (!response.ok || !data.success) {
        setError(data.error || "Erreur lors de la création du compte");
        setIsLoading(false);
        return;
      }
      
      // Compte créé avec succès - rediriger vers la page de login
      // Cela force le joueur à se connecter explicitement, ce qui déclenche start_session()
      navigate('/', { 
        state: { 
          message: `Compte créé avec succès pour ${data.player.username} ! Veuillez vous connecter.`,
          username: data.player.username 
        } 
      });
    } catch (e) {
      setError("Erreur réseau ou serveur");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleCreateAccount();
    }
  };

  return (
    <div 
      className="login-background"
      style={{
        backgroundImage: `linear-gradient(
          rgba(47, 27, 20, 0.7), 
          rgba(47, 27, 20, 0.5)
        ), url(/assets/pages/create-account_page.jpg)`
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
          <Box className="login-header">
            <Box 
              component="img" 
              src={masterLogo} 
              alt="Master of Islands Logo" 
              className="login-logo"
              sx={{
                width: '120px',
                height: 'auto',
                margin: '0 auto 1rem',
                display: 'block',
                filter: 'drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3))',
                animation: 'float 3s ease-in-out infinite'
              }}
            />
            <Typography variant="h3" className="roman-title game-title" align="center" sx={{ textTransform: 'uppercase' }}>
              Master of Islands
            </Typography>
            <Typography variant="h6" className="roman-subtitle game-subtitle" align="center">
              Créez votre compte joueur
            </Typography>
          </Box>

          {/* Frise grecque séparatrice */}
          <Box 
            component="img" 
            src="/assets/components/ancient-greek-meander.svg" 
            alt="Frise grecque" 
            sx={{
              width: '170%',
              height: '24px',
              margin: '1.5rem 0',
              opacity: 0.6,
              position: 'relative',
              left: '-35%'
            }}
          />

          {/* Stepper */}
          <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 3 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel sx={{
                  '& .MuiStepLabel-label': { color: 'var(--text-secondary)' },
                  '& .MuiStepLabel-label.Mui-active': { color: 'var(--roman-gold)' },
                  '& .MuiStepLabel-label.Mui-completed': { color: 'var(--roman-red)' }
                }}>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          <Box className="login-form">
            {/* Étape 1: Informations de compte */}
            {activeStep === 0 && (
              <Box>
                <Typography variant="h6" sx={{ mb: 2, color: 'var(--roman-red)', textAlign: 'center' }}>
                  🏛️ Informations de connexion
                </Typography>
                <TextField
                  label="Nom d'utilisateur"
                  variant="outlined"
                  fullWidth
                  value={username}
                  onChange={e => {
                    const newValue = e.target.value;
                    setUsername(newValue);
                    handleUsernameChange(newValue);
                  }}
                  className="roman-input"
                  helperText={usernameMessage}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <PersonOutline className="input-icon" />
                      </InputAdornment>
                    ),
                    endAdornment: usernameStatus === 'checking' ? (
                      <InputAdornment position="end">
                        <CircularProgress size={20} />
                      </InputAdornment>
                    ) : usernameStatus === 'available' ? (
                      <InputAdornment position="end" sx={{ color: 'green' }}>
                        ✓
                      </InputAdornment>
                    ) : usernameStatus === 'taken' ? (
                      <InputAdornment position="end" sx={{ color: 'red' }}>
                        ✗
                      </InputAdornment>
                    ) : null,
                  }}
                  sx={{
                    marginBottom: 2,
                    '& .MuiOutlinedInput-root': {
                      '& fieldset': { 
                        borderColor: usernameStatus === 'available' ? 'green' : 
                                   usernameStatus === 'taken' ? 'red' : 'var(--bronze)' 
                      },
                      '&:hover fieldset': { borderColor: 'var(--roman-gold)' },
                      '&.Mui-focused fieldset': { borderColor: 'var(--roman-gold)' },
                    },
                    '& .MuiFormHelperText-root': {
                      color: usernameStatus === 'available' ? 'green' : 
                             usernameStatus === 'taken' ? 'red' : 'inherit'
                    }
                  }}
                />
                <TextField
                  label="Adresse email"
                  type="email"
                  variant="outlined"
                  fullWidth
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  className="roman-input"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Email className="input-icon" />
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    marginBottom: 2,
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
                  onChange={e => setPassword(e.target.value)}
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
                    marginBottom: 2,
                    '& .MuiOutlinedInput-root': {
                      '& fieldset': { borderColor: 'var(--bronze)' },
                      '&:hover fieldset': { borderColor: 'var(--roman-gold)' },
                      '&.Mui-focused fieldset': { borderColor: 'var(--roman-gold)' },
                    },
                  }}
                />
                <TextField
                  label="Confirmer le mot de passe"
                  type={showConfirm ? 'text' : 'password'}
                  variant="outlined"
                  fullWidth
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
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
                          onClick={() => setShowConfirm(!showConfirm)}
                          edge="end"
                          className="password-toggle"
                        >
                          {showConfirm ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    marginBottom: 2,
                    '& .MuiOutlinedInput-root': {
                      '& fieldset': { borderColor: 'var(--bronze)' },
                      '&:hover fieldset': { borderColor: 'var(--roman-gold)' },
                      '&.Mui-focused fieldset': { borderColor: 'var(--roman-gold)' },
                    },
                  }}
                />
              </Box>
            )}

            {/* Étape 2: Profil personnel */}
            {activeStep === 1 && (
              <Box>
                <Typography variant="h6" sx={{ mb: 2, color: 'var(--roman-red)', textAlign: 'center' }}>
                  👤 Profil personnel
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  <TextField
                    label="Prénom"
                    variant="outlined"
                    fullWidth
                    value={firstName}
                    onChange={e => setFirstName(e.target.value)}
                    className="roman-input"
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Person className="input-icon" />
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': { borderColor: 'var(--bronze)' },
                        '&:hover fieldset': { borderColor: 'var(--roman-gold)' },
                        '&.Mui-focused fieldset': { borderColor: 'var(--roman-gold)' },
                      },
                    }}
                  />
                  <TextField
                    label="Nom de famille"
                    variant="outlined"
                    fullWidth
                    value={lastName}
                    onChange={e => setLastName(e.target.value)}
                    className="roman-input"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': { borderColor: 'var(--bronze)' },
                        '&:hover fieldset': { borderColor: 'var(--roman-gold)' },
                        '&.Mui-focused fieldset': { borderColor: 'var(--roman-gold)' },
                      },
                    }}
                  />
                </Box>
                <TextField
                  label="Date de naissance"
                  type="date"
                  variant="outlined"
                  fullWidth
                  value={birthDate}
                  onChange={e => setBirthDate(e.target.value)}
                  className="roman-input"
                  InputLabelProps={{ shrink: true }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <CalendarToday className="input-icon" />
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    marginBottom: 2,
                    '& .MuiOutlinedInput-root': {
                      '& fieldset': { borderColor: 'var(--bronze)' },
                      '&:hover fieldset': { borderColor: 'var(--roman-gold)' },
                      '&.Mui-focused fieldset': { borderColor: 'var(--roman-gold)' },
                    },
                  }}
                />
                <TextField
                  select
                  label="Pays de résidence"
                  variant="outlined"
                  fullWidth
                  value={country}
                  onChange={e => setCountry(e.target.value)}
                  className="roman-input"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Flag className="input-icon" />
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    marginBottom: 2,
                    '& .MuiOutlinedInput-root': {
                      '& fieldset': { borderColor: 'var(--bronze)' },
                      '&:hover fieldset': { borderColor: 'var(--roman-gold)' },
                      '&.Mui-focused fieldset': { borderColor: 'var(--roman-gold)' },
                    },
                  }}
                >
                  {countries.map((c) => (
                    <MenuItem key={c} value={c}>{c}</MenuItem>
                  ))}
                </TextField>
                <TextField
                  label="Ville (optionnel)"
                  variant="outlined"
                  fullWidth
                  value={city}
                  onChange={e => setCity(e.target.value)}
                  className="roman-input"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <LocationOn className="input-icon" />
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    marginBottom: 2,
                    '& .MuiOutlinedInput-root': {
                      '& fieldset': { borderColor: 'var(--bronze)' },
                      '&:hover fieldset': { borderColor: 'var(--roman-gold)' },
                      '&.Mui-focused fieldset': { borderColor: 'var(--roman-gold)' },
                    },
                  }}
                />
                <TextField
                  label="Téléphone (optionnel)"
                  variant="outlined"
                  fullWidth
                  value={phone}
                  onChange={e => setPhone(e.target.value)}
                  className="roman-input"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Phone className="input-icon" />
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    marginBottom: 2,
                    '& .MuiOutlinedInput-root': {
                      '& fieldset': { borderColor: 'var(--bronze)' },
                      '&:hover fieldset': { borderColor: 'var(--roman-gold)' },
                      '&.Mui-focused fieldset': { borderColor: 'var(--roman-gold)' },
                    },
                  }}
                />
              </Box>
            )}

            {/* Étape 3: Confirmation et conditions */}
            {activeStep === 2 && (
              <Box>
                <Typography variant="h6" sx={{ mb: 2, color: 'var(--roman-red)', textAlign: 'center' }}>
                  ✅ Finalisation
                </Typography>
                
                <Paper sx={{ p: 2, mb: 2, bgcolor: 'rgba(245, 245, 220, 0.7)' }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                    📋 Résumé de votre compte :
                  </Typography>
                  <Typography variant="body2">👤 <strong>{firstName} {lastName}</strong></Typography>
                  <Typography variant="body2">📧 {email}</Typography>
                  <Typography variant="body2">🎮 Nom d'utilisateur: {username}</Typography>
                  <Typography variant="body2">🌍 {country}{city && `, ${city}`}</Typography>
                </Paper>

                <FormControlLabel
                  control={
                    <Checkbox
                      checked={acceptTerms}
                      onChange={e => setAcceptTerms(e.target.checked)}
                      sx={{
                        color: 'var(--bronze)',
                        '&.Mui-checked': { color: 'var(--roman-gold)' }
                      }}
                    />
                  }
                  label={
                    <Typography variant="body2">
                      J'accepte les <strong>conditions d'utilisation</strong> et la <strong>politique de confidentialité</strong> *
                    </Typography>
                  }
                  sx={{ mb: 1, alignItems: 'flex-start' }}
                />
                
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={acceptNewsletter}
                      onChange={e => setAcceptNewsletter(e.target.checked)}
                      sx={{
                        color: 'var(--bronze)',
                        '&.Mui-checked': { color: 'var(--roman-gold)' }
                      }}
                    />
                  }
                  label={
                    <Typography variant="body2">
                      Je souhaite recevoir les actualités du jeu par email (optionnel)
                    </Typography>
                  }
                  sx={{ mb: 2, alignItems: 'flex-start' }}
                />
              </Box>
            )}

            {/* Messages d'erreur */}
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {/* Boutons de navigation */}
            <Box className="login-actions" sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
              <Button
                variant="outlined"
                onClick={activeStep === 0 ? () => navigate("/") : handleBack}
                className="roman-button secondary-button"
                sx={{ 
                  minHeight: '48px',
                  minWidth: '120px',
                  borderColor: 'var(--bronze)',
                  color: 'var(--roman-red)',
                  '&:hover': {
                    borderColor: 'var(--roman-gold)',
                    backgroundColor: 'rgba(218, 165, 32, 0.1)'
                  }
                }}
              >
                {activeStep === 0 ? '🛡️ Connexion' : '⬅️ Précédent'}
              </Button>

              <Button
                variant="contained"
                onClick={handleNext}
                disabled={isLoading}
                className="roman-button primary-button"
                sx={{ 
                  minHeight: '48px',
                  minWidth: '120px',
                  fontSize: { xs: '1rem', sm: '1.1rem' }
                }}
              >
                {isLoading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : activeStep === steps.length - 1 ? (
                  '⚔️ Créer le compte'
                ) : (
                  'Suivant ➡️'
                )}
              </Button>
            </Box>
          </Box>
          <Box className="login-footer">
            <Typography variant="caption" className="roman-text" align="center" sx={{ opacity: 0.7 }}>
              Master of Islands v1.0 - Grèce Antique
            </Typography>
          </Box>
        </Paper>
        )}
      </Container>
    </div>
  );
};

export default CreateAccountPage;
