import React, { useState, useEffect } from "react";
import { Box, Typography, Container, Paper, Button } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { ArrowBack } from "@mui/icons-material";
import { useUser } from "../hooks/useUser";
import FactionWelcomePopup from "../popups/FactionWelcomePopup";
import { getFactionByResource, Faction } from "../data/factions";
import "../styles/theme.css";
import "../styles/login.css";

// Mappage des ressources vers les images et descriptions
const resourceConfig = {
  stone: {
    name: "Île de la Pierre",
    image: "/assets/island_selection/stone_island.png",
    icon: "/assets/icons/stone.png",
    description: "Départ robuste : production de pierre élevée, idéale pour les fortifications et constructions massives. Début lent sur les ressources agricoles.",
  },
  iron: {
    name: "Île du Fer", 
    image: "/assets/island_selection/iron_island.png",
    icon: "/assets/icons/iron.png",
    description: "Départ offensif : production de fer élevée, parfait pour l'armée et les armes. Début plus difficile pour la croissance urbaine.",
  },
  cereal: {
    name: "Île des Céréales",
    image: "/assets/island_selection/cereal_island.png", 
    icon: "/assets/icons/cereal.png",
    description: "Départ agricole : production de céréales abondante, croissance rapide de la population. Défense et construction plus lentes au début.",
  },
  papyrus: {
    name: "Île du Papyrus",
    image: "/assets/island_selection/papyrus_island.png",
    icon: "/assets/icons/papyrus.png", 
    description: "Départ savant : bonus de papyrus (recherche), accès rapide aux technologies. Début plus technique, croissance modérée.",
  },
} as const;

type Island = {
  id: string;
  name: string;
  coords: [number, number];
  miniature?: string;
  base_resource: string;
  advanced_resource: string;
};

const IslandSelectionPage: React.FC = () => {
  const navigate = useNavigate();
  const { logout } = useUser();
  const [suggestedIslands, setSuggestedIslands] = useState<Record<string, Island>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showBackground, setShowBackground] = useState(false);
  const [selectedFaction, setSelectedFaction] = useState<Faction | null>(null);
  const [factionPopupOpen, setFactionPopupOpen] = useState(false);

  // Afficher le background avec un léger délai
  useEffect(() => {
    const timer = setTimeout(() => {
      setShowBackground(true);
    }, 300);
    return () => clearTimeout(timer);
  }, []);

  // Charger les données des îles et les suggestions depuis l'API
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Charger les îles
        const response = await fetch('/api/universe');
        if (!response.ok) {
          throw new Error('Erreur lors du chargement des îles');
        }
        const data = await response.json();

        // Charger les suggestions pour chaque ressource
        const suggestions: Record<string, Island> = {};
        for (const resource of ['stone', 'iron', 'cereal', 'papyrus']) {
          try {
            const suggestionResponse = await fetch(`/api/islands/assignment/suggest/${resource}`);
            if (suggestionResponse.ok) {
              const suggestionData = await suggestionResponse.json();
              if (suggestionData.success && suggestionData.suggestion) {
                suggestions[resource] = suggestionData.suggestion.island;
              }
            }
          } catch (err) {
            console.warn(`Impossible de charger la suggestion pour ${resource}`);
          }
        }
        setSuggestedIslands(suggestions);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Suggérer automatiquement la meilleure île pour une ressource
  const handleSelectResource = async (baseResource: string) => {
    try {
      // Déterminer la faction selon la ressource
      const faction = getFactionByResource(baseResource);
      if (faction) {
        setSelectedFaction(faction);
        setFactionPopupOpen(true);
      }

      const response = await fetch(`/api/islands/assignment/suggest/${baseResource}`);
      if (!response.ok) {
        throw new Error('Aucune île disponible pour cette ressource');
      }
      const data = await response.json();
      if (data.success && data.suggestion) {
        // Stocker l'île suggérée temporairement
        sessionStorage.setItem('selectedIsland', JSON.stringify(data.suggestion.island));
      }
    } catch (err: any) {
      alert(`Erreur : ${err.message}`);
    }
  };

  // Gérer la fermeture du popup de faction et naviguer vers la sélection de ville
  const handleFactionConfirm = () => {
    setFactionPopupOpen(false);
    const selectedIsland = sessionStorage.getItem('selectedIsland');
    if (selectedIsland) {
      const island = JSON.parse(selectedIsland);
      navigate(`/island/${island.id}/city-selection`);
      sessionStorage.removeItem('selectedIsland');
    }
  };

  if (loading) {
    return (
      <div className="login-background">
        <Container maxWidth="md" className="login-container">
          <Paper elevation={12} className="login-panel roman-panel" sx={{ p: { xs: 2, sm: 4 } }}>
            <Typography variant="h5" align="center">Chargement des îles...</Typography>
          </Paper>
        </Container>
      </div>
    );
  }

  if (error) {
    return (
      <div className="login-background">
        <Container maxWidth="md" className="login-container">
          <Paper elevation={12} className="login-panel roman-panel" sx={{ p: { xs: 2, sm: 4 } }}>
            <Typography variant="h5" color="error" align="center">Erreur : {error}</Typography>
          </Paper>
        </Container>
      </div>
    );
  }

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
        <Paper elevation={12} className="login-panel roman-panel" sx={{ p: { xs: 2, sm: 4 } }}>
          {/* Bouton retour repositionné au-dessus du titre */}
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
            <Button
              variant="outlined"
              startIcon={<ArrowBack />}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                logout();
                navigate('/');
              }}
              className="roman-button secondary-button"
              sx={{
                minWidth: '120px',
                borderColor: 'var(--bronze)',
                color: 'var(--roman-red)',
                '&:hover': {
                  borderColor: 'var(--roman-gold)',
                  backgroundColor: 'rgba(218, 165, 32, 0.1)'
                }
              }}
            >
              Retour
            </Button>
          </Box>

          <Box className="login-header">            
            <Typography variant="h3" className="roman-title game-title" align="center">
              🏝️ Choisissez votre île de départ
            </Typography>
            <Typography variant="h6" className="roman-subtitle game-subtitle" align="center" sx={{ mb: 2 }}>
              Ce choix déterminera vos ressources principales et votre style de jeu !
            </Typography>
          </Box>

          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 3, justifyContent: "center", mb: 3 }}>
            {Object.entries(resourceConfig).map(([resource, config]) => {
              const suggestedIsland = suggestedIslands[resource];
              
              return (
                <Box
                  key={resource}
                  className="island-card"
                  sx={{
                    width: { xs: "100%", sm: 400 },
                    height: 120,
                    backgroundImage: `linear-gradient(rgba(47,27,20,0.45), rgba(47,27,20,0.25)), url(${config.image})`,
                    backgroundSize: "cover",
                    backgroundPosition: "center",
                    backgroundRepeat: "no-repeat",
                    border: "2px solid var(--bronze)",
                    borderRadius: "16px",
                    boxShadow: "var(--shadow-medium)",
                    cursor: "pointer",
                    transition: "all 0.2s",
                    p: 2,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    position: "relative",
                    overflow: "hidden",
                  }}
                  onClick={() => handleSelectResource(resource)}
                >
                  <Typography
                    variant="h5"
                    className="roman-title"
                    align="center"
                    sx={{ mb: 0.5, color: "var(--roman-red)", textShadow: "1px 1px 2px #fff", width: "100%" }}
                  >
                    {config.name}
                  </Typography>
                  {suggestedIsland && (
                    <Typography
                      variant="body2"
                      align="center"
                      sx={{ 
                        color: "var(--text-primary)", 
                        textShadow: "1px 1px 2px #fff", 
                        fontSize: "0.8em",
                        fontWeight: "bold",
                        mb: 0.5 
                      }}
                    >
                      {suggestedIsland.name} [{suggestedIsland.coords[0]}, {suggestedIsland.coords[1]}]
                    </Typography>
                  )}
                  <Typography
                    variant="body2"
                    className="roman-text"
                    align="center"
                    sx={{ color: "var(--text-primary)", textShadow: "1px 1px 2px #fff", width: "100%", fontSize: "0.85em" }}
                  >
                    {config.description}
                  </Typography>
                </Box>
              );
            })}
          </Box>

          <Box className="login-footer">
            <Typography variant="caption" className="roman-text" align="center" sx={{ opacity: 0.7 }}>
              Master of Islands v1.0 - Grèce Antique
            </Typography>
          </Box>
        </Paper>
      </Container>

      {/* Popup de bienvenue de la faction */}
      <FactionWelcomePopup
        open={factionPopupOpen}
        faction={selectedFaction}
        onClose={handleFactionConfirm}
        onBack={() => {
          setFactionPopupOpen(false);
          setSelectedFaction(null);
          sessionStorage.removeItem('selectedIsland');
        }}
      />
    </div>
  );
};

export default IslandSelectionPage;
