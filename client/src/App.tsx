
import React, { useEffect, useState, useRef } from "react";
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import CreateAccountPage from "./pages/CreateAccountPage";
import { UserProvider, useUser } from "./hooks/useUser";
import { GameShellProvider } from "./context/GameShellContext";
import { TurnLockProvider } from "./context/TurnLockContext";
import GameShell from "./components/GameShell";
import TutorialOverlay from "./components/TutorialOverlay";
import BattleNotificationToast from "./components/BattleNotificationToast";

// Pages de jeu
import IslandSelectionPage from "./pages/IslandSelectionPage";
import WorldPage from "./pages/WorldPage";
import IslandPage from "./pages/IslandPage";
import CityPage from "./pages/CityPage";
import CitySelectionPage from "./pages/CitySelectionPage";
import ResearchPage from "./components/ResearchPage";
import BattlefieldPage from "./pages/BattlefieldPage";
import LeaderboardPage from "./pages/LeaderboardPage";
import QuestsPage from "./pages/QuestsPage";
import SettingsPage from "./pages/SettingsPage";

// Exemple de composant qui gère la redirection après login
const AuthRedirect: React.FC = () => {
  const { user, isInitialized } = useUser();
  const navigate = useNavigate();
  const location = useLocation();
  
  useEffect(() => {
    // Attendre que l'initialisation soit terminée
    if (!isInitialized) return;
    
    // Si pas d'utilisateur, rediriger vers login
    if (!user.id) {
      if (location.pathname !== '/' && location.pathname !== '/create-account') {
        navigate('/');
      }
      return;
    }
    
    // Ne pas rediriger si déjà sur une page de sélection
    if (
      (location.pathname.startsWith("/island/") && location.pathname.includes("city-selection"))
      || location.pathname === "/island-selection"
    ) {
      return;
    }
    
    // Si l'utilisateur n'a pas de villes, rediriger vers island-selection
    if (user.cities.length === 0) {
      if (location.pathname !== "/island-selection") {
        navigate("/island-selection");
      }
    } else {
      // Utilisateur avec villes : autoriser certaines pages
      const allowed = ["/world", "/research", "/leaderboard", "/quests", "/settings"];
      const isIsland = /^\/island\/[\w-]+$/.test(location.pathname);
      const isCity = /^\/city\/[\w-]+$/.test(location.pathname);
      const isBattlefield = /^\/battlefield\/[\w-]+$/.test(location.pathname);
      
      if (!allowed.includes(location.pathname) && !isIsland && !isCity && !isBattlefield) {
        navigate("/world");
      }
    }
  }, [user, isInitialized, navigate, location]);
  return null;
};
// Composant pour gérer l'affichage du tutoriel
const TutorialManager: React.FC = () => {
  const { user } = useUser();
  const location = useLocation();
  const navigate = useNavigate();
  const [showTutorial, setShowTutorial] = useState(false);
  const firstShowRef = useRef(true);
  const timerRef = useRef<number | null>(null);
  const lastUserIdRef = useRef<string | number | null>(null);

  // Réinitialiser firstShowRef quand l'utilisateur change
  useEffect(() => {
    if (user.id && user.id !== lastUserIdRef.current) {
      firstShowRef.current = true;
      lastUserIdRef.current = user.id;
    }
  }, [user.id]);

  useEffect(() => {
    // Nettoyer le timer précédent
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }

    // Pas d'utilisateur = pas de tutoriel
    if (!user.id) {
      setShowTutorial(false);
      return;
    }

    // Ne jamais afficher sur les pages de sélection
    if (location.pathname === '/island-selection' || 
        location.pathname.includes('city-selection')) {
      setShowTutorial(false);
      return;
    }

    // Vérifier le statut du tutoriel
    const checkTutorial = async () => {
      try {
        const response = await fetch(`/api/tutorial/status/${user.id}`);
        const data = await response.json();
        
        // Tutoriel déjà complété = ne rien afficher
        if (!data.success || data.tutorial_completed) {
          setShowTutorial(false);
          return;
        }

        // Sur /world : première fois = délai 5s, sinon immédiat
        if (location.pathname === '/world') {
          if (firstShowRef.current) {
            // Masquer pendant le délai
            setShowTutorial(false);
            timerRef.current = window.setTimeout(() => {
              setShowTutorial(true);
              firstShowRef.current = false;
              timerRef.current = null;
            }, 5000);
          } else {
            setShowTutorial(true);
          }
          return;
        }

        // Sur /island et /city : toujours avec délai de 5 secondes
        if (location.pathname.startsWith('/island/') || 
            location.pathname.startsWith('/city/')) {
          // Masquer pendant le délai
          setShowTutorial(false);
          timerRef.current = window.setTimeout(() => {
            setShowTutorial(true);
            timerRef.current = null;
          }, 5000);
          return;
        }

        // Autres pages : ne pas afficher
        setShowTutorial(false);
      } catch (error) {
        console.error('Erreur tutoriel:', error);
        setShowTutorial(false);
      }
    };

    checkTutorial();

    // Cleanup : annuler le timer si le composant se démonte ou si la page change
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [user.id, location.pathname]);

  const handleComplete = () => {
    setShowTutorial(false);
    // Naviguer vers la page world pour rafraîchir l'état
    navigate('/world');
  };

  const handleSkip = () => {
    setShowTutorial(false);
  };

  if (!showTutorial || !user.id) return null;

  return (
    <TutorialOverlay
      playerId={user.id}
      onComplete={handleComplete}
      onSkip={handleSkip}
    />
  );
};

function App() {
  return (
    <UserProvider>
      <GameShellProvider>
        <TurnLockProvider>
          <Router>
            <AuthRedirect />
            <TutorialManager />
            <BattleNotificationToast />
            <Routes>
          {/* Pages sans barres (login, sélection, etc.) */}
          <Route path="/" element={<LoginPage />} />
          <Route path="/create-account" element={<CreateAccountPage />} />
          <Route path="/island-selection" element={<IslandSelectionPage />} />
          <Route path="/island/:id/city-selection" element={<CitySelectionPage />} />
          
          {/* Pages principales avec GameShell STABLE */}
          <Route path="/world" element={
            <GameShell>
              <WorldPage />
            </GameShell>
          } />
          <Route path="/island/:id" element={
            <GameShell>
              <IslandPage />
            </GameShell>
          } />
          <Route path="/city/:id" element={
            <GameShell>
              <CityPage />
            </GameShell>
          } />
          <Route path="/research" element={
            <GameShell>
              <ResearchPage />
            </GameShell>
          } />
          <Route path="/leaderboard" element={
            <GameShell>
              <LeaderboardPage />
            </GameShell>
          } />
          <Route path="/quests" element={
            <GameShell>
              <QuestsPage />
            </GameShell>
          } />
          <Route path="/settings" element={
            <SettingsPage />
          } />
          
          {/* Pages spéciales */}
          <Route path="/battlefield/:battleId" element={<BattlefieldPage />} />
        </Routes>
        </Router>
      </TurnLockProvider>
      </GameShellProvider>
    </UserProvider>
  );
}

export default App;
