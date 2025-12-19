
import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Box, Typography, Button, Container, Paper, CircularProgress, Dialog, DialogTitle, DialogContent, DialogActions, TextField } from "@mui/material";
// Suppression de Grid, structure flexbox à la place
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { getApiUrl } from '../utils/api';
import { universeCache } from '../services/UniverseCache';
import { useUser } from "../hooks/useUser";
import "../styles/theme.css";
import "../styles/login.css";

const CitySelectionPage: React.FC = () => {
  const { id: islandId } = useParams();
  const [cities, setCities] = useState<any[]>([]);
  const [island, setIsland] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showRenameDialog, setShowRenameDialog] = useState(false);
  const [selectedCityId, setSelectedCityId] = useState<string>("");
  const [selectedCityName, setSelectedCityName] = useState<string>("");
  const [newCityName, setNewCityName] = useState<string>("");
  const [showBackground, setShowBackground] = useState(false);
  const navigate = useNavigate();
  const { user, setUser } = useUser();

  // Afficher le background avec un léger délai
  useEffect(() => {
    const timer = setTimeout(() => {
      setShowBackground(true);
    }, 300);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    // Charger les données de l'île et les villes avec les vrais propriétaires
    const fetchData = async () => {
      try {
        // Charger les données complètes de l'univers avec cache
        const universeData = await universeCache.getUniverse(getApiUrl());
        
        // Trouver l'île
        const foundIsland = universeData.islands.find((i: any) => i.id === islandId);
        if (!foundIsland) throw new Error("Île introuvable");
        setIsland(foundIsland);
        
        // Extraire les villes de cette île et fusionner avec les données sauvegardées
        let islandCities = foundIsland.elements.filter((el: any) => el.type === "city");
        
        // Si des données de villes sauvegardées existent, les fusionner
        if (Array.isArray(universeData.cities)) {
          islandCities = islandCities.map((cityElement: any) => {
            const savedCity = universeData.cities.find((c: any) => c.id === cityElement.id);
            return savedCity ? { ...cityElement, ...savedCity } : cityElement;
          });
        }
        
        setCities(islandCities);
        setLoading(false);
      } catch (err: any) {
        setError("Erreur de chargement des données : " + err.message);
        setLoading(false);
      }
    };

    fetchData();
  }, [islandId]);

  const handleClaim = async (cityId: string, cityName: string) => {
    setError("");
    try {
      const response = await fetch(`${getApiUrl()}/api/city/colonize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player_id: user.id, city_id: cityId }),
      });
      const data = await response.json();
      if (!response.ok || !data.success) {
        setError(data.error || data.message || "Erreur lors de la réclamation de la ville");
        return;
      }
      
      // Invalider le cache immédiatement après colonisation
      universeCache.invalidate();
      
      // Ville réclamée avec succès - maintenant proposer le renommage
      // IMPORTANT : Utiliser l'ID renvoyé par le serveur, pas celui du frontend !
      const serverCityId = data.city?.id || cityId;
      const serverCityName = data.city?.name || cityName;
      
      setSelectedCityId(serverCityId);
      setSelectedCityName(serverCityName);
      setNewCityName(serverCityName); // Pré-remplir avec le nom actuel
      setShowRenameDialog(true);
      
    } catch (e) {
      setError("Erreur réseau ou serveur");
    }
  };

  const handleRename = async () => {
    if (!newCityName.trim()) {
      setError("Le nom de la ville ne peut pas être vide");
      return;
    }

    try {
      const response = await fetch(`${getApiUrl()}/api/city/${selectedCityId}/rename`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newCityName.trim() }),
      });
      const data = await response.json();
      
      if (!response.ok || !data.success) {
        setError(data.error || "Erreur lors du renommage de la ville");
        return;
      }
      
      // Fermer le dialog et rediriger vers le monde
      setShowRenameDialog(false);
      setUser((prev: any) => ({ ...prev, cities: [...prev.cities, selectedCityId] }));
      navigate('/world');
      
    } catch (e) {
      setError("Erreur réseau lors du renommage");
    }
  };

  const handleSkipRename = () => {
    // Fermer le dialog et rediriger vers le monde sans renommer
    setShowRenameDialog(false);
    setUser((prev: any) => ({ ...prev, cities: [...prev.cities, selectedCityId] }));
    navigate('/world');
  };

  const handleCancelRename = () => {
    // Fermer le dialog et rester sur la page
    setShowRenameDialog(false);
    setSelectedCityId("");
    setSelectedCityName("");
    setNewCityName("");
  };

  const handleBack = () => {
    navigate("/island-selection");
  };

  return (
    <div 
      className="login-background" 
      style={{
        backgroundImage: showBackground ? 'url(/assets/pages/island-selection_page.jpg)' : 'none',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        transition: 'background-image 0.5s ease-in-out'
      }}
    >
      <Container maxWidth="md" className="login-container">
        <Paper elevation={12} className="login-panel roman-panel" sx={{ p: { xs: 2, sm: 4 }, display: 'flex', flexDirection: 'column', minHeight: 480, justifyContent: 'space-between' }}>
          <Box className="login-header" sx={{ mb: 2 }}>
            <Typography variant="h3" className="roman-title game-title" align="center">
              🏛️ Sélectionnez votre ville
            </Typography>
            {island && (
              <Typography variant="h6" className="roman-subtitle" align="center" sx={{ mt: 1, color: 'var(--text-secondary)' }}>
                {island.name} [{island.coords[0]}, {island.coords[1]}]
              </Typography>
            )}
          </Box>

          <Box sx={{ flexGrow: 1, width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
            {loading ? (
              <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: 120 }}>
                <CircularProgress color="primary" />
              </Box>
            ) : error ? (
              <Box className="error-message" sx={{ mb: 2 }}>
                <Typography color="error" className="roman-text">
                  ⚠️ {error}
                </Typography>
              </Box>
            ) : (
              cities.map(city => (
                <Paper
                  key={city.id}
                  elevation={city.owner ? 1 : 3}
                  sx={{
                    width: { xs: '100%', sm: 340, md: 360 },
                    maxWidth: 400,
                    minHeight: 72,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    p: 0,
                    borderRadius: 3,
                    background: city.owner ? 'var(--parchment)' : '#fff',
                    boxSizing: 'border-box',
                    mb: 1,
                  }}
                >
                  <Button
                    variant="contained"
                    color={city.owner ? "secondary" : "primary"}
                    disabled={!!city.owner}
                    fullWidth
                    onClick={() => handleClaim(city.id, city.name)}
                    className={city.owner ? "secondary-button" : "primary-button"}
                    sx={{
                      minHeight: 72,
                      width: '100%',
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      borderRadius: 2,
                      background: city.owner ? 'var(--parchment)' : 'var(--roman-gold)',
                      color: city.owner ? 'var(--roman-red)' : 'var(--text-primary)',
                      boxShadow: city.owner ? 'none' : 'var(--shadow-medium)',
                      transition: 'background 0.2s',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      '&:hover': {
                        background: city.owner ? 'var(--parchment)' : 'var(--bronze)',
                      },
                    }}
                  >
                    <Box sx={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', px: 2 }}>
                      <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '1.1rem', color: city.owner ? 'var(--roman-red)' : 'var(--text-primary)' }}>
                        {city.name}
                      </Typography>
                      {city.owner == null ? (
                        <Typography variant="body2" sx={{ color: '#2e7d32', fontWeight: 500 }}>
                          (Libre)
                        </Typography>
                      ) : (
                        <Typography variant="body2" sx={{ color: '#c62828', fontWeight: 500 }}>
                          (Occupée par {city.owner})
                        </Typography>
                      )}
                    </Box>
                  </Button>
                </Paper>
              ))
            )}
          </Box>

          <Box sx={{ mt: 3, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
            <Button
              startIcon={<ArrowBackIcon />}
              onClick={handleBack}
              variant="outlined"
              color="primary"
              sx={{ minWidth: 0, borderColor: "var(--bronze)", color: "var(--roman-red)", mb: 1 }}
              className="secondary-button"
            >
              Retour
            </Button>
            <Typography variant="caption" className="roman-text" align="center" sx={{ opacity: 0.7 }}>
              Master of Islands v1.0 - Grèce Antique
            </Typography>
          </Box>
        </Paper>
      </Container>

      {/* Dialog de renommage de ville */}
      <Dialog 
        open={showRenameDialog} 
        onClose={handleCancelRename}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          className: "roman-panel",
          sx: { 
            borderRadius: 3,
            border: '2px solid var(--bronze)',
            background: 'var(--parchment)'
          }
        }}
      >
        <DialogTitle sx={{ 
          textAlign: 'center', 
          color: 'var(--roman-red)',
          fontFamily: 'var(--font-title)',
          fontSize: '1.5rem',
          fontWeight: 'bold'
        }}>
          🏛️ Nommer votre nouvelle ville
        </DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <Typography variant="body1" sx={{ 
            mb: 2, 
            textAlign: 'center',
            color: 'var(--text-secondary)',
            fontFamily: 'var(--font-body)'
          }}>
            Félicitations ! Vous venez de coloniser une nouvelle ville.
            <br />
            Souhaitez-vous lui donner un nom personnalisé ?
          </Typography>
          <TextField
            fullWidth
            label="Nom de la ville"
            variant="outlined"
            value={newCityName}
            onChange={(e) => setNewCityName(e.target.value)}
            placeholder={selectedCityName}
            inputProps={{ maxLength: 50 }}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
                background: '#fff',
                '& fieldset': {
                  borderColor: 'var(--bronze)',
                },
                '&:hover fieldset': {
                  borderColor: 'var(--roman-gold)',
                },
                '&.Mui-focused fieldset': {
                  borderColor: 'var(--roman-red)',
                },
              },
              '& .MuiInputLabel-root': {
                color: 'var(--text-secondary)',
              },
            }}
          />
          {error && (
            <Typography color="error" sx={{ mt: 1, fontSize: '0.875rem' }}>
              ⚠️ {error}
            </Typography>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1, justifyContent: 'center' }}>
          <Button 
            onClick={handleRename}
            variant="contained"
            className="primary-button"
            sx={{
              background: 'var(--roman-gold)',
              color: 'var(--text-primary)',
              fontWeight: 600,
              px: 3,
              '&:hover': {
                background: 'var(--bronze)',
              },
            }}
          >
            Renommer
          </Button>
          <Button 
            onClick={handleSkipRename}
            variant="outlined"
            className="secondary-button"
            sx={{
              borderColor: 'var(--bronze)',
              color: 'var(--roman-red)',
              fontWeight: 600,
              px: 3,
              '&:hover': {
                borderColor: 'var(--roman-red)',
                background: 'rgba(139, 69, 19, 0.1)',
              },
            }}
          >
            Garder le nom actuel
          </Button>
          <Button 
            onClick={handleCancelRename}
            variant="text"
            sx={{
              color: 'var(--text-secondary)',
              fontWeight: 500,
              px: 2,
              '&:hover': {
                background: 'rgba(0, 0, 0, 0.1)',
              },
            }}
          >
            Annuler
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default CitySelectionPage;
