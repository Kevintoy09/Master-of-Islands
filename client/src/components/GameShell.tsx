import React, { useEffect, useState, useCallback } from 'react';
import { useLocation, useParams, useNavigate } from "react-router-dom";
import { useUser } from "../hooks/useUser";
import { useAutoUpdatePopulation } from "../hooks/useAutoUpdatePopulation";
import { useGameShell } from "../context/GameShellContext";
import { useRefreshInterval } from "../hooks/useRefreshInterval";
import { getApiUrl } from "../utils/api";
import HeaderBar from "./HeaderBar";
import BottomNavBar from "./BottomNavBar";
import TransportsListPopup from "../popups/TransportsListPopup";
import ArmyPopup from "../popups/ArmyPopup";
import './Layout.css';

/**
 * GameShell - Coquille de jeu stable
 * Gère HeaderBar + BottomNavBar de manière centralisée et STABLE
 * Seul le contenu (children) change selon la route
 */
interface GameShellProps {
  children: React.ReactNode;
}

const GameShell: React.FC<GameShellProps> = ({ children }) => {
  const { user } = useUser();
  const location = useLocation();
  const params = useParams();
  const navigate = useNavigate();
  
  // Utiliser le contexte GameShell au lieu d'états locaux
  const gameShell = useGameShell();
  
  // États UI locaux (non partagés)
  const [showTransportsList, setShowTransportsList] = useState(false);
  const [hasActiveBattles, setHasActiveBattles] = useState(false);
  const [showArmyPopup, setShowArmyPopup] = useState(false);

  // Charger la liste des villes du joueur - UNE FOIS et stable
  useEffect(() => {
    if (!user?.id) {
      gameShell.setUserCities([]);
      return;
    }
    
    const fetchUserCities = async () => {
      try {
        const response = await fetch(`/api/auth/player/${user.id}/cities`);
        if (response.ok) {
          const data = await response.json();
          gameShell.setUserCities(data.cities || []);
        }
      } catch (err) {
        console.error('Erreur lors du chargement des villes du joueur:', err);
      }
    };

    fetchUserCities();
  }, [user?.id]);

  // Détermine la ville active selon l'URL - stable entre les pages
  useEffect(() => {
    // Pages qui n'ont pas besoin de ville active (ne pas gérer la ville)
    const pagesWithoutCity = ['/research', '/army', '/leaderboard', '/quests'];
    if (pagesWithoutCity.some(path => location.pathname.startsWith(path))) {
      return; // Ne rien faire pour ces pages
    }
    
    let cityId = "";
    
    // Si on est sur /city/:id, utilise l'ID de l'URL
    if (location.pathname.startsWith('/city/') && params.id) {
      cityId = params.id;
    }
    // Pour les autres pages, garde la ville active ou utilise la première
    else if (user && user.cities && user.cities.length > 0) {
      if (gameShell.activeCityId && user.cities.includes(gameShell.activeCityId)) {
        return; // Garder la ville actuelle
      }
      cityId = user.cities[0];
    }
    
    if (cityId && cityId !== gameShell.activeCityId) {
      gameShell.setActiveCityId(cityId);
    }
  }, [location.pathname, params.id, user, gameShell.activeCityId]);

  // Hook pour population - stable
  const { populationData } = useAutoUpdatePopulation({
    cityId: gameShell.activeCityId,
    enabled: !!gameShell.activeCityId
  });

  // Fonction pour charger les ressources de la ville active
  const fetchCityData = useCallback(async () => {
    if (!gameShell.activeCityId) return;
    
    try {
      // Transports actifs
      if (user?.id) {
        try {
          const transportsResponse = await fetch(`/api/transports/player/${user.id}`);
          if (transportsResponse.ok) {
            const transportsData = await transportsResponse.json();
            const activeTransports = (transportsData.transports || []).filter((transport: any) => 
              transport.status === 'loading' || transport.status === 'traveling' || transport.status === 'unloading'
            );
            gameShell.setActiveTransportsCount(activeTransports.length);
          }
        } catch (err) {
          console.warn('Erreur comptage transports:', err);
        }
      }

      // Données de ville
      const response = await fetch(`/api/city-state/${gameShell.activeCityId}`);
      if (response.ok) {
        const data = await response.json();
        gameShell.setCityName(data.name || "Ville inconnue");
        gameShell.setCityResources(data.resources || {});
        gameShell.setActiveIslandId(data.island_id || "");
        
        // Mettre à jour currentActiveCity avec les données complètes
        gameShell.setCurrentActiveCity({
          id: gameShell.activeCityId,
          name: data.name || "Ville inconnue",
          resources: data.resources || {},
          buildings: data.buildings || [],
          island_id: data.island_id
        });
      }
    } catch (err) {
      console.error('Erreur lors du chargement des ressources de la ville:', err);
    }
  }, [gameShell.activeCityId, user?.id]);

  // Vérifier périodiquement s'il y a des batailles actives pour le joueur
  useEffect(() => {
    if (!user?.id) {
      setHasActiveBattles(false);
      return;
    }

    const checkActiveBattles = async () => {
      try {
        const response = await fetch(`${getApiUrl()}/api/v2/battles/check-player/${user.id}`);
        if (response.ok) {
          const data = await response.json();
          setHasActiveBattles(data.has_active_battles || false);
        }
      } catch (err) {
        console.error('Erreur vérification batailles actives:', err);
      }
    };

    checkActiveBattles();
    const interval = setInterval(checkActiveBattles, 30000); // Vérifier toutes les 30 secondes (réduit de 10s pour performance)

    return () => clearInterval(interval);
  }, [user?.id]);

  // Réinitialiser les ressources si pas de ville active
  useEffect(() => {
    if (!gameShell.activeCityId) {
      gameShell.setCityResources({});
      gameShell.setCityName("");
      gameShell.setActiveIslandId("");
    }
  }, [gameShell.activeCityId]);

  // Utiliser le hook de rafraîchissement centralisé pour les ressources de la ville
  useRefreshInterval(fetchCityData, [gameShell.activeCityId, user?.id]);

  // Fonction pour charger les données globales
  const fetchGlobalData = useCallback(async () => {
    if (!user?.id) return;
    
    try {
      const playerResponse = await fetch(`/api/auth/player/${user.id}`);
      if (playerResponse.ok) {
        const playerData = await playerResponse.json();
        gameShell.setPlayerInfo(playerData);
        gameShell.setGlobalResources({
          gold: playerData.gold || 0,
          diamonds: playerData.diamonds || 0,
          research_points: playerData.research_points || 0
        });
      }

      // Note: Production d'or globale pas encore implémentée côté serveur
      gameShell.setGoldProductionRate(0);
    } catch (error) {
      console.error('Erreur lors du chargement des données globales:', error);
    }
  }, [user?.id, gameShell]);

  // Utiliser le hook de rafraîchissement dynamique pour les données globales
  useRefreshInterval(fetchGlobalData);

  // Handlers stables
  const handleCityChange = async (newCityId: string) => {
    if (newCityId !== gameShell.activeCityId) {
      gameShell.setActiveCityId(newCityId);
      
      // Charger immédiatement les données complètes de la nouvelle ville active
      try {
        const response = await fetch(`/api/city-state/${newCityId}`);
        if (response.ok) {
          const cityData = await response.json();
          gameShell.setCurrentActiveCity({
            id: newCityId,
            name: cityData.name || "Ville inconnue",
            resources: cityData.resources || {},
            buildings: cityData.buildings || [],
            island_id: cityData.island_id
          });
        }
      } catch (error) {
        console.error('Erreur lors du chargement de la ville active:', error);
      }
      
      navigate(`/city/${newCityId}`);
    }
  };

  const handleTransportShipsClick = () => {
    setShowTransportsList(true);
  };

  const handleMilitaryClick = () => {
    setShowArmyPopup(true);
  };

  // Combiner toutes les ressources pour HeaderBar
  const allResources = {
    ...gameShell.cityResources,
    ...gameShell.globalResources,
    population_total: populationData?.population || 0,
    population_free: populationData?.population_free || 0
  };

  // Adapter format population pour HeaderBar
  const populationInfo = populationData ? {
    current_population: populationData.population,
    max_capacity: populationData.info.max_capacity,
    growth_per_hour: populationData.info.base_growth_per_hour,
    real_growth_per_hour: populationData.info.real_growth_per_hour,
    time_multiplier: populationData.info.time_multiplier,
    time_info: populationData.info.time_info
  } : undefined;

  return (
    <div className="layout-container">
      {/* HeaderBar FIXE - ne se recharge jamais */}
      <HeaderBar 
        cityName={gameShell.cityName}
        cityId={gameShell.activeCityId}
        resources={allResources}
        populationInfo={populationInfo}
        userCities={gameShell.userCities}
        activeCityId={gameShell.activeCityId}
        onCityChange={handleCityChange}
        playerInfo={{
          ...gameShell.playerInfo,
          player_id: user?.id
        }}
        activeTransportsCount={gameShell.activeTransportsCount}
        onTransportShipsClick={handleTransportShipsClick}
        goldProductionRate={gameShell.goldProductionRate}
        onMilitaryClick={handleMilitaryClick}
        hasActiveBattles={hasActiveBattles}
      />
      
      {/* ZONE DE CONTENU - seule partie qui change */}
      <div className="main-content">
        {children}
      </div>
      
      {/* BottomNavBar FIXE - ne se recharge jamais */}
      <BottomNavBar 
        activeCityId={gameShell.activeCityId}
        activeIslandId={gameShell.activeIslandId}
        playerResources={{
          gold: gameShell.globalResources.gold || 0,
          research_points: gameShell.globalResources.research_points || 0,
          transport_ships: gameShell.playerInfo.transport_ships_available || 0,
          diamonds: gameShell.globalResources.diamonds || 0
        }}
        playerInfo={{
          transport_ships_total: gameShell.playerInfo.transport_ships_total || 0,
          transport_ships_available: gameShell.playerInfo.transport_ships_available || 0
        }}
      />

      {/* Popups */}
      {showTransportsList && (
        <TransportsListPopup onClose={() => setShowTransportsList(false)} />
      )}
      
      {showArmyPopup && (
        <ArmyPopup onClose={() => setShowArmyPopup(false)} />
      )}
    </div>
  );
};

export default GameShell;