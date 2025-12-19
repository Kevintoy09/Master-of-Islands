import React, { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { createPortal } from "react-dom";
import { useUser } from "../hooks/useUser";
import { useUnlockedResources } from "../hooks/useUnlockedResources";
import { useZoomAndDrag } from "../hooks/useZoomAndDrag";
import { useGameShell } from "../context/GameShellContext";
import { getApiUrl } from '../utils/api';
import { PerformanceMonitor } from '../utils/performanceMonitor';
import { universeCache } from '../services/UniverseCache';
import ResourceSitePopup from "../components/ResourceSitePopup";
import CityPopup from "../popups/CityPopup";
import TransportPopup from "../popups/TransportPopup";
import AttackPopupV3 from "../popups/AttackPopupV3";
import WildCampPreview from "../popups/WildCampPreview";
import SimpleBattlefieldV2 from "../components/SimpleBattlefieldV2";


import battleStatusService from "../services/BattleStatusService";
import { UnifiedBattleLoaderService } from "../services/UnifiedBattleLoaderService";

type Island = {
  id: string;
  name: string;
  coords: [number, number];
  background: string;
  miniature?: string;
  base_resource: string;
  advanced_resource: string;
  city_layout: string;
  elements: any[];
};

const IslandPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, setUser } = useUser();
  const { isResourceUnlocked } = useUnlockedResources(user?.id || null);
  const gameShell = useGameShell();
  const [island, setIsland] = useState<Island | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedSite, setSelectedSite] = useState<{siteType: string, islandId: string} | null>(null);
  const [selectedCity, setSelectedCity] = useState<any>(null);
  const [isCityPopupOpen, setCityPopupOpen] = useState(false);
  const [citiesData, setCitiesData] = useState<any[]>([]);
  const [siteLevels, setSiteLevels] = useState<{[key: string]: number}>({});
  const [battlefieldCities, setBattlefieldCities] = useState<Set<string>>(new Set()); // Villes avec champ de bataille
  
  // États pour le transport popup
  const [showTransportPopup, setShowTransportPopup] = useState(false);
  const [transportDestinationCity, setTransportDestinationCity] = useState<any>(null);

  // États pour l'attaque des villages barbares
  const [isAttackPopupOpen, setIsAttackPopupOpen] = useState(false);
  const [attackTargetCity, setAttackTargetCity] = useState<any>(null);

  // États pour la prévisualisation des villages barbares
  const [showWildCampPreview, setShowWildCampPreview] = useState(false);
  const [selectedWildCamp, setselectedWildCamp] = useState<any>(null);

  // État pour l'ouverture automatique de l'aperçu depuis l'Army page
  const [autoOpenBattlefieldId, setAutoOpenBattlefieldId] = useState<string | null>(null);

  // États pour l'ouverture directe du battlefield via l'icône
  const [simpleBattlefieldOpen, setSimpleBattlefieldOpen] = useState(false);
  const [simpleBattlefieldData, setSimpleBattlefieldData] = useState<any>(null);



  // Hook pour le zoom et drag
  const {
    zoom,
    offset,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    handleWheel,
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd
  } = useZoomAndDrag({
    minZoom: 0.3,
    maxZoom: 3,
    initialZoom: 0.75,
    mapWidth: 2912, // Largeur réelle de l'image d'île
    mapHeight: 1632 // Hauteur réelle de l'image d'île
  });

  // Sites de ressources cliquables
  const RESOURCE_SITES = [
    'forest', 'quarry', 'cereal_field', 'mine', 'papyrus_field', 
    'horse_ranch', 'marble_quarry', 'glass_workshop', 'vineyard'
  ];

  // Mapping des sites vers les ressources correspondantes
  const SITE_TO_RESOURCE = {
    'forest': 'wood',
    'quarry': 'stone', 
    'cereal_field': 'cereal',
    'mine': 'iron',
    'papyrus_field': 'papyrus',
    'horse_ranch': 'horse',
    'marble_quarry': 'marble',
    'glass_workshop': 'glass',
    'vineyard': 'wine'
  };

  // Mapping des types vers les icônes
  const TYPE_TO_ICON = {
    'forest': '/assets/island/icons/ressource_forest.png',
    'quarry': '/assets/island/icons/ressource_stone.png',
    'cereal_field': '/assets/island/icons/ressource_cereal.png',
    'mine': '/assets/island/icons/ressource_iron.png',
    'papyrus_field': '/assets/island/icons/ressource_papyrus.png',
    'horse_ranch': '/assets/island/icons/ressource_horse.png',
    'marble_quarry': '/assets/island/icons/ressource_marble.png',
    'glass_workshop': '/assets/island/icons/ressource_glass.png',
    'vineyard': '/assets/island/icons/ressource_wine.png'
  };

  // Fonction utilitaire pour obtenir le nom d'affichage d'une ville
  const getCityDisplayName = useCallback((cityElement: any) => {
    const cityData = citiesData.find(city => city.id === cityElement.id);
    return cityData ? cityData.name : cityElement.id;
  }, [citiesData]);

  // Fonction pour charger les villes avec batailles en cours
  const loadBattlefieldCities = useCallback(async () => {
    try {
      const citiesWithBattles = await battleStatusService.getCitiesWithBattles();
      setBattlefieldCities(new Set(citiesWithBattles));
    } catch (error) {
      console.warn('Erreur lors du chargement des villes avec batailles:', error);
      setBattlefieldCities(new Set());
    }
  }, []);

  const handleSiteClick = (siteType: string) => {
    if (RESOURCE_SITES.includes(siteType) && island) {
      // Vérifier si la ressource est débloquée
      const resourceType = SITE_TO_RESOURCE[siteType as keyof typeof SITE_TO_RESOURCE];
      if (resourceType && !isResourceUnlocked(resourceType)) {
        // Afficher un message d'information au lieu d'ouvrir le popup
        alert(`Cette ressource (${resourceType}) n'est pas encore débloquée. Recherchez les technologies appropriées pour y accéder.`);
        return;
      }
      setSelectedSite({ siteType, islandId: island.id });
    }
  };

  // Fonction transport marchandises (nouvelle logique utilisant la ville active)
  const handleTransportGoods = async (destinationCity: any) => {
    // Fermer le city popup
    setCityPopupOpen(false);
    setSelectedCity(null);
    
    if (!user?.id) {
      alert('Erreur : utilisateur non connecté');
      return;
    }

    if (!gameShell.currentActiveCity) {
      alert('Erreur : aucune ville active sélectionnée');
      return;
    }

    if (gameShell.currentActiveCity.id === destinationCity.id) {
      alert('Vous ne pouvez pas faire un transport vers la même ville');
      return;
    }

    try {
      // Récupérer les détails de la ville active pour vérifier le port
      const response = await fetch(`${getApiUrl()}/api/city-state/${gameShell.currentActiveCity.id}`);
      if (!response.ok) {
        throw new Error('Erreur lors du chargement des données de la ville');
      }
      
      const cityData = await response.json();
      const buildings = cityData.buildings || [];
      
      // Vérifier si la ville active a un port
      const hasPort = buildings.some((building: any) => 
        building && building.name && 
        building.name.toLowerCase().includes('port') && 
        building.level >= 1
      );
      
      if (!hasPort) {
        alert('Votre ville actuelle n\'a pas de port. Vous devez construire un port pour pouvoir faire des transports.');
        return;
      }

      // Mettre à jour currentActiveCity avec les données fraîches récupérées de l'API
      const updatedActiveCity = {
        id: cityData.id,
        name: cityData.name,
        resources: cityData.resources || {},
        buildings: buildings
      };
      gameShell.setCurrentActiveCity(updatedActiveCity);

      // Ouvrir directement le transport popup avec la ville active comme source
      setTransportDestinationCity(destinationCity);
      setShowTransportPopup(true);
      
    } catch (err: any) {
      alert('Erreur lors de la vérification du port : ' + err.message);
    }
  };



  // Fonction colonisation accessible partout
  const handleColonize = async (city: any) => {
    try {
      const response = await fetch(`${getApiUrl()}/api/city/colonize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ city_id: city.id, player_id: user.id })
      });
      const result = await response.json();
      if (response.ok) {
        alert('Colonie créée avec succès !');
        
        // Invalider le cache et recharger
        universeCache.invalidate();
        const refreshData = await universeCache.getUniverse(getApiUrl(), true);
        
        // Mettre à jour les données des villes
        let allCities = Array.isArray(refreshData.cities) && refreshData.cities.length > 0 ? refreshData.cities : [];
        if (allCities.length === 0 && Array.isArray(refreshData.islands)) {
          refreshData.islands.forEach((isle: any) => {
            if (Array.isArray(isle.elements)) {
              isle.elements.forEach((elem: any) => {
                if (elem.type === "city") {
                  let enriched = elem;
                  if (Array.isArray(refreshData.cities)) {
                    const foundCity = refreshData.cities.find((c: any) => c.id === elem.id);
                    if (foundCity) {
                      enriched = { ...elem, ...foundCity };
                    }
                  }
                  allCities.push(enriched);
                }
              });
            }
          });
        }
        setCitiesData(allCities);
        
        // Mettre à jour les données de l'île actuelle pour forcer le re-render
        const updatedIsland = refreshData.islands.find((i: any) => i.id === id);
        if (updatedIsland) {
          setIsland(updatedIsland);
        }
        
        // Mettre à jour l'état utilisateur pour que WorldPage voie les nouvelles villes
        setUser((prev: any) => ({ 
          ...prev, 
          cities: [...(prev.cities || []), city.id] 
        }));
      } else {
        alert('Erreur : ' + (result.message || 'Impossible de coloniser.'));
      }
    } catch (err) {
      alert('Erreur réseau ou serveur.');
    }
  };

  // Fonction pour ouvrir directement un battlefield via l'icône
  const handleBattlefieldIconClick = async (cityId: string) => {
    try {
      // Charger la bataille pour cette ville
      const battle = await UnifiedBattleLoaderService.loadBattleFromCity(cityId);
      
      if (!battle) {
        alert('❌ Aucune bataille active trouvée pour cette ville.');
        return;
      }

      // Trouver les données de la ville dans citiesData ou créer des données pour village barbare
      let defenderCity;
      if (cityId.startsWith('wild_camp_')) {
        // Pour les villages barbares, créer des données fictives
        const islandId = cityId.replace('wild_camp_', '');
        defenderCity = { 
          id: cityId, 
          name: `Camp des Sauvages (Île ${islandId})`,
          owner: 'barbarian',
          isBarbarian: true
        };
      } else {
        // Pour les villes normales, chercher dans citiesData
        const cityData = citiesData.find(city => city.id === cityId);
        defenderCity = cityData || { id: cityId, name: `Ville ${cityId}` };
      }
      
      // Créer les données de bataille pour SimpleBattlefieldV2
      const battleInfo = {
        attackerCity: gameShell.currentActiveCity || null,
        defenderCity: defenderCity,
        attackerUnits: battle.forces?.attackers || {},
        defenderUnits: battle.forces?.defenders || {},
        movementId: null,
        battleId: battle.battleId,
        battlefieldTemplateId: battle.map || 'auto',
        targetCityId: cityId,
        gamePhase: 'deployment' as 'deployment' | 'battle' | 'victory',
        currentPlayer: 'attacker' as 'attacker' | 'defender'
      };

      // Ouvrir SimpleBattlefieldV2
      setSimpleBattlefieldData(battleInfo);
      setSimpleBattlefieldOpen(true);
      
      // Masquer les barres du jeu pour le mode plein écran
      document.body.classList.add('battlefield-fullscreen');
      
    } catch (error) {
      console.error('Erreur ouverture battlefield:', error);
      alert('Erreur lors de l\'ouverture du battlefield.');
    }
  };

  // Fonction pour récupérer les niveaux des sites de ressources
  const fetchSiteLevels = useCallback(async (islandId: string) => {
    if (!user?.id || !island) return;
    
    const newSiteLevels: {[key: string]: number} = {};
    
    // Ne récupérer les niveaux que pour les sites qui existent réellement sur cette île
    const sitesOnIsland = island.elements
      .filter((el: any) => RESOURCE_SITES.includes(el.type))
      .map((el: any) => el.type);
    
    // Utiliser Promise.all pour paralléliser les requêtes
    const sitePromises = sitesOnIsland.map(async (siteType) => {
      try {
        const response = await fetch(`${getApiUrl()}/api/resources/site/${islandId}/${siteType}/info?player_id=${user.id}`);
        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            return { siteType, level: data.level || 1 };
          }
        }
        return { siteType, level: 1 }; // Niveau par défaut
      } catch (error) {
        console.error(`Erreur chargement niveau ${siteType}:`, error);
        return { siteType, level: 1 }; // Niveau par défaut en cas d'erreur
      }
    });

    const results = await Promise.all(sitePromises);
    results.forEach(({ siteType, level }) => {
      newSiteLevels[siteType] = level;
    });

    setSiteLevels(newSiteLevels);
  }, [user?.id, island, RESOURCE_SITES]);

  // Fonction pour récupérer les villes avec champ de bataille actif
  const fetchBattlefieldCities = useCallback(async () => {
    try {
      const response = await fetch(`${getApiUrl()}/api/v2/battlefields/all`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      if (data.success && data.battlefields) {
        const citiesWithBattlefield = new Set<string>();
        Object.values(data.battlefields).forEach((battlefield: any) => {
          if (battlefield.location) {
            citiesWithBattlefield.add(battlefield.location);
          }
        });
        setBattlefieldCities(citiesWithBattlefield);
      }
    } catch (error) {
      console.error('⚠️ Erreur lors du chargement des champs de bataille:', error);
      // En cas d'erreur, on garde l'état précédent (pas de reset)
    }
  }, []);

  useEffect(() => {
    const loadIsland = async () => {
      try {
        // Utiliser le cache au lieu de fetch direct
        const data = await universeCache.getUniverse(getApiUrl());
        
        const found: Island | undefined = data.islands.find((i: Island) => i.id === id);
        if (!found) {
          setError("Île introuvable");
        } else {
          setIsland(found);
          // Reconstruction de citiesData si data.cities absent ou vide
          let allCities = Array.isArray(data.cities) && data.cities.length > 0 ? data.cities : [];
          if (allCities.length === 0 && Array.isArray(data.islands)) {
            data.islands.forEach((isle: any) => {
              if (Array.isArray(isle.elements)) {
                isle.elements.forEach((elem: any) => {
                  if (elem.type === "city") {
                    let enriched = elem;
                    if (Array.isArray(data.cities)) {
                      const foundCity = data.cities.find((c: any) => c.id === elem.id);
                      if (foundCity) {
                        enriched = { ...elem, ...foundCity };
                      }
                    }
                    allCities.push(enriched);
                  }
                });
              }
            });
          }
          setCitiesData(allCities);
          fetchSiteLevels(found.id);
          fetchBattlefieldCities(); // Charger les champs de bataille actifs
        }
        setLoading(false);
      } catch (err: any) {
        setError("Erreur de chargement des données : " + err.message);
        setLoading(false);
      }
    };
    
    loadIsland();
  }, [id]);



  // Écouter les événements de renommage de ville
  useEffect(() => {
    const handleCityRenamed = (event: CustomEvent) => {
      const { cityId, newName } = event.detail;
      setCitiesData(prevCities => 
        prevCities.map(city => 
          city.id === cityId ? { ...city, name: newName } : city
        )
      );
    };

    window.addEventListener('cityRenamed', handleCityRenamed as EventListener);
    
    return () => {
      window.removeEventListener('cityRenamed', handleCityRenamed as EventListener);
    };
  }, []);

  // Charger les villes avec batailles en cours quand les données des villes changent
  useEffect(() => {
    if (citiesData.length > 0) {
      // Chargement initial
      loadBattlefieldCities();
      
      // Recharger toutes les 5 secondes pour maintenir à jour (réduit de 10s à 5s)
      const interval = setInterval(() => {
  // console.log('🔄 [IslandPage] Rechargement périodique des batailles...');
        loadBattlefieldCities();
      }, 5000);
      
      return () => clearInterval(interval);
    }
  }, [citiesData, loadBattlefieldCities]);

  // Écouter les événements de changement de bataille pour rafraîchir immédiatement
  useEffect(() => {
    const handleBattleChange = () => {
      // Événement de changement de bataille détecté
      // battleStatusService.invalidateCache();
      // loadBattlefieldCities();
    };

    // Écouter les événements personnalisés de fin de bataille
    window.addEventListener('battleEnded', handleBattleChange);
    window.addEventListener('battleCreated', handleBattleChange);
    
    return () => {
      window.removeEventListener('battleEnded', handleBattleChange);
      window.removeEventListener('battleCreated', handleBattleChange);
    };
  }, [loadBattlefieldCities]);

  // Détecter les paramètres URL pour ouvrir automatiquement l'attaque
  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    const openAttack = urlParams.get('openAttack');
    const battleId = urlParams.get('battleId');
    

    
    if (openAttack && island && island.elements) {

      
      // Chercher dans les éléments de l'île (villages barbares ET villes joueurs)
      let targetElement = island.elements.find(element => element.id === openAttack);
      
      // Si pas trouvé et c'est un camp sauvage, essayer de chercher par type
      if (!targetElement && openAttack.startsWith('wild_camp_')) {
        const wildCamps = island.elements.filter(element => element.type === 'wild_camp');
        
        // Prendre le premier camp sauvage trouvé comme fallback
        if (wildCamps.length > 0) {
          targetElement = { ...wildCamps[0], id: openAttack };
        }
      }
      
      if (targetElement) {
        
        // Toujours ouvrir AttackPopupV3, même avec un battleId
        // Si on a un battleId, on simulera automatiquement le clic sur "Aperçu"
        if (targetElement.type === 'wild_camp') {
          // Pour les camps de sauvages, utiliser l'élément directement
          setAttackTargetCity(targetElement);
        } else if (targetElement.type === 'city') {
          // Pour les villes joueurs, chercher les données enrichies dans citiesData
          const enrichedCity = citiesData.find(city => city.id === targetElement.id) || targetElement;
          setAttackTargetCity(enrichedCity);
        }
        
        setIsAttackPopupOpen(true);
        
        // Si on a un battleId, le stocker pour l'ouverture automatique
        if (battleId) {
          setAutoOpenBattlefieldId(battleId);
        }
        
        // Nettoyer les paramètres URL pour éviter la réouverture
        navigate(location.pathname, { replace: true });
      }
    }
  }, [island, citiesData, location.search, navigate, location.pathname]);

  // Effet pour simuler automatiquement le clic sur "Aperçu" quand on a un battleId
  useEffect(() => {
    if (isAttackPopupOpen && autoOpenBattlefieldId) {
      // Attendre que le popup soit rendu, puis chercher et cliquer sur le bouton "Aperçu"
      const timer = setTimeout(() => {
        // Chercher tous les boutons et trouver celui qui contient "Aperçu"
        const buttons = Array.from(document.querySelectorAll('button'));
        const previewButton = buttons.find(button => 
          button.textContent?.includes('Aperçu') || button.textContent?.includes('Preview')
        );
        
        if (previewButton) {
          previewButton.click();
          setAutoOpenBattlefieldId(null); // Reset pour éviter les clics répétés
        }
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [isAttackPopupOpen, autoOpenBattlefieldId]);

  // Constantes de style pour améliorer la lisibilité
  const PULSE_ANIMATION_CSS = `
    @keyframes pulse {
      0% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.2); opacity: 0.7; }
      100% { transform: scale(1); opacity: 1; }
    }
    @keyframes flicker {
      0%, 100% { transform: scale(1) translateY(0); opacity: 1; }
      25% { transform: scale(1.1) translateY(-2px); opacity: 0.9; }
      50% { transform: scale(0.95) translateY(1px); opacity: 1; }
      75% { transform: scale(1.05) translateY(-1px); opacity: 0.95; }
    }
  `;

  const BATTLEFIELD_ICON_STYLE = {
    position: "absolute" as const,
    width: 36,
    height: 36,
    zIndex: 15,
    filter: "drop-shadow(2px 2px 6px rgba(0,0,0,0.7))",
    animation: "pulse 1.5s infinite"
  };

  if (loading) return <div>Chargement...</div>;
  if (error) return <div style={{color:'red',textAlign:'center',marginTop:40}}>{error}</div>;
  if (!island) return null;

  return (
    <>
      <style>{PULSE_ANIMATION_CSS}</style>
      {/* Carte avec zoom et drag */}
      <div
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          overflow: "hidden",
          cursor: "grab",
          zIndex: 1,
          touchAction: "none", // Désactive tous les gestes natifs du navigateur
          userSelect: "none", // Empêche la sélection de texte
          WebkitUserSelect: "none",
          WebkitTouchCallout: "none", // Désactive le menu contextuel sur iOS
        }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {/* Conteneur de la carte avec transformations */}
        <div
          style={{
            position: "absolute",
            width: "2912px", // Largeur réelle de l'image d'île
            height: "1632px", // Hauteur réelle de l'image d'île
            transform: `translate(${offset.x}px, ${offset.y}px) scale(${zoom})`,
            transformOrigin: "0 0",
          }}
        >
      {/* Fond d'île */}
      <img
        src={`/${island.background}`}
        alt="île"
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
          zIndex: 1,
          pointerEvents: "none",
          userSelect: "none"
        }}
      />
      {/* Overlay sombre supprimé pour voir le background */}
      {/* Contenu */}
      <div style={{
        position: "relative",
        zIndex: 3,
        width: "100%",
        height: "100%",
        paddingBottom: "80px",
        overflowY: "visible",
      }}>
        <h2 style={{
          position: "absolute",
          left: "50%",
          top: "24px",
          transform: "translateX(-50%)",
          color: "white",
          textShadow: "1px 1px 8px #000, 0 0 12px #000b",
          zIndex: 10,
          fontSize: "2em",
          fontWeight: 700,
          margin: 0,
          padding: "0 60px",
          textAlign: "center",
          lineHeight: 1.2,
          maxWidth: "90%",
          wordBreak: "break-word"
        }}>
          {island.name} (ID : {id})
        </h2>
        {/* Affichage des éléments de l'île */}
        {island.elements && island.elements.map((el: any) => {
          if (el.type === "city") {
            const isMine = user && Array.isArray(user.cities) && user.cities.includes(el.id);
            // Récupérer les vraies données de la ville depuis citiesData
            const cityData = citiesData.find((c: any) => c.id === el.id);
            const cityOwner = cityData ? cityData.owner : el.owner;
            const isOccupied = Boolean(cityOwner);
            const hasBattlefield = battlefieldCities.has(el.id); // Vérifier si la ville a un champ de bataille
            
            return (
              <div key={el.id} style={{ position: "relative" }}>
                {/* Logo de guerre si champ de bataille présent */}
                {hasBattlefield && (
                  <div
                    title="Champ de bataille actif - Cliquer pour ouvrir directement"
                    style={{
                      position: "absolute",
                      left: el.city_coords[0] * 0.6 + 45,
                      top: el.city_coords[1] * 0.4 - 38,
                      width: 80,
                      height: 80,
                      fontSize: "64px",
                      cursor: "pointer",
                      zIndex: 15,
                      filter: "drop-shadow(0 0 8px rgba(255, 100, 0, 0.8))",
                      animation: "flicker 1.2s ease-in-out infinite",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center"
                    }}
                    onMouseUp={(e) => {
                      e.stopPropagation();
                      e.preventDefault();
                      handleBattlefieldIconClick(el.id);
                    }}
                    onTouchEnd={(e) => {
                      e.stopPropagation();
                      e.preventDefault();
                      handleBattlefieldIconClick(el.id);
                    }}
                  >
                    🔥
                  </div>
                )}
                <div
                  style={{
                    position: "absolute",
                    left: el.city_coords[0] * 0.6,
                    top: el.city_coords[1] * 0.4,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    cursor: "pointer",
                    zIndex: 10
                  }}
                  onClick={() => {
                    // Utiliser les données de la ville depuis citiesData si disponibles
                    let fullCity = cityData || el;
                    setSelectedCity(fullCity);
                    setCityPopupOpen(true);
                  }}
                >
                  {/* Icône de la ville */}
                  <img
                    src={isOccupied ? "/assets/island/icons/city_1.png" : "/assets/island/icons/empty_slot.png"}
                    alt={getCityDisplayName(el)}
                    title={getCityDisplayName(el)}
                    style={{
                      width: 160,
                      height: 120,
                      objectFit: "contain",
                      filter: isMine ? "drop-shadow(0 0 8px #ffe600)" : "none",
                      transition: "transform 0.2s ease"
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = "scale(1.1)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = "scale(1)";
                    }}
                  />
                  {/* Nom de la ville en dessous */}
                  <div
                    style={{
                      marginTop: 4,
                      padding: "4px 8px",
                      background: isMine ? "#fffbe0" : isOccupied ? "#eee" : "#fff",
                      border: isMine ? "2px solid #ffe600" : "2px solid #666",
                      borderRadius: 8,
                      fontWeight: "bold",
                      color: "#222",
                      fontSize: 12,
                      boxShadow: isMine ? "0 0 12px 2px #ffe60088" : "0 0 6px #0002",
                      whiteSpace: "nowrap"
                    }}
                  >
                    {getCityDisplayName(el)}
                  </div>
                </div>
              </div>
            );
          } else if (el.type === "wild_camp") {
            // Affichage spécial pour les villages barbares
            const barbarianVillageId = `wild_camp_${island?.id}`;
            const hasBattlefieldBarbarian = battlefieldCities.has(barbarianVillageId);
            
            return (
              <div key={`wild_camp_${island?.id}`} style={{ position: "relative" }}>
                {/* Logo de guerre si champ de bataille présent pour village barbare */}
                {hasBattlefieldBarbarian && (
                  <div
                    title="Champ de bataille actif - Cliquer pour ouvrir directement"
                    style={{
                      position: "absolute",
                      left: el.city_coords[0] * 0.6 + 50,
                      top: el.city_coords[1] * 0.4 - 38,
                      width: 80,
                      height: 80,
                      fontSize: "64px",
                      cursor: "pointer",
                      zIndex: 20,
                      filter: "drop-shadow(0 0 8px rgba(255, 100, 0, 0.8))",
                      animation: "flicker 1.2s ease-in-out infinite",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      pointerEvents: "auto"
                    }}
                    onMouseUp={(e) => {
                      e.stopPropagation();
                      e.preventDefault();
                      handleBattlefieldIconClick(barbarianVillageId);
                    }}
                    onTouchEnd={(e) => {
                      e.stopPropagation();
                      e.preventDefault();
                      handleBattlefieldIconClick(barbarianVillageId);
                    }}
                  >
                    🔥
                  </div>
                )}
                <button
                  style={{
                  position: "absolute",
                  left: el.city_coords[0] * 0.6,
                  top: el.city_coords[1] * 0.4,
                  width: 200,
                  height: 180,
                  background: `url(/assets/island/icons/barbarian_camp.png) center top 16px/160px 120px no-repeat`,
                  border: "none",
                  borderRadius: 0,
                  display: "flex",
                  alignItems: "flex-end",
                  justifyContent: "center",
                  fontSize: 11,
                  color: "white",
                  zIndex: 8,
                  cursor: "pointer",
                  fontWeight: "bold",
                  textShadow: "2px 2px 4px rgba(0,0,0,1)",
                  padding: "0 4px 6px 4px",
                  textAlign: "center",
                  backgroundColor: "transparent",
                  transition: "transform 0.2s ease"
                }}
                title="Camp des Sauvages - Cliquez pour attaquer !"
                onClick={async () => {
                  if (gameShell.currentActiveCity) {
                    if (!gameShell.currentActiveCity || !gameShell.currentActiveCity.id) {
                      alert('Vous devez d\'abord sélectionner une ville dans le header pour attaquer');
                      return;
                    }
                    
                    const currentPlayer = user?.id || 'player_1';
                    
                    try {
                      const response = await fetch(`/api/check-city-ownership/${currentPlayer}/${island?.id}`);
                      const result = await response.json();
                      
                      if (!result.has_city) {
                        alert('Vous devez posséder une ville sur cette île pour attaquer ce camp des sauvages !');
                        return;
                      }
                      
                      const level = result.city_level || 1;
                      
                      const barbarianCity = {
                        id: `wild_camp_${island?.id}`,
                        name: `Camp des Sauvages (Niveau ${level})`,
                        owner_id: 'barbarian',
                        island_id: island?.id,
                        city_coords: el.city_coords || [500, 400],
                        isBarbarian: true,
                        barbarianLevel: level
                      };

                      setselectedWildCamp(barbarianCity);
                      setShowWildCampPreview(true);
                    } catch (error) {
                      console.error('Erreur lors de la vérification de propriété:', error);
                      alert('Erreur lors de la vérification de propriété de la ville');
                      return;
                    }
                  } else {
                    alert('Vous devez d\'abord sélectionner une ville dans le header pour attaquer');
                  }
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = "scale(1.1)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = "scale(1)";
                }}
              >
                Camp des Sauvages
              </button>
              </div>
            );
          } else {
            // Affichage des sites de ressources et autres éléments
            const isResourceSite = RESOURCE_SITES.includes(el.type);
            
            // Vérifier si la ressource est débloquée pour ce site
            const resourceType = SITE_TO_RESOURCE[el.type as keyof typeof SITE_TO_RESOURCE];
            const isUnlocked = !resourceType || isResourceUnlocked(resourceType);
            const iconPath = TYPE_TO_ICON[el.type as keyof typeof TYPE_TO_ICON];
            
            return (
              <button
                key={el.type + (el.id || Math.random())}
                style={{
                  position: "absolute",
                  left: el.city_coords[0] * 0.6,
                  top: el.city_coords[1] * 0.4,
                  width: isResourceSite ? 160 : 80,
                  height: isResourceSite ? 120 : 80,
                  background: isResourceSite && iconPath ? 
                    `url(${iconPath}) center/contain no-repeat transparent` :
                    (isResourceSite ? 
                      "transparent" : "#eee"),
                  border: isResourceSite ? "none" : "1px solid #999",
                  borderRadius: isResourceSite ? 0 : "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: isResourceSite ? 10 : 12,
                  color: isResourceSite ? 
                    (isUnlocked ? "white" : "rgba(255, 255, 255, 0.4)") : 
                    "#333",
                  zIndex: 5,
                  boxShadow: isResourceSite ? "none" : "0 0 4px #0001",
                  cursor: isResourceSite ? (isUnlocked ? "pointer" : "not-allowed") : "default",
                  fontWeight: isResourceSite ? "bold" : "normal",
                  textShadow: "none",
                  transition: "transform 0.2s ease",
                  padding: 0,
                  textAlign: "center",
                  opacity: isResourceSite && !isUnlocked ? 0.5 : 1,
                  filter: isResourceSite && !isUnlocked ? "grayscale(80%) brightness(0.7)" : "none"
                }}
                title={`${el.type.replace(/_/g, " ")}${isResourceSite ? 
                  (isUnlocked ? 
                    ` - Niveau ${siteLevels[el.type] || 1} (Cliquez pour gérer)` :
                    ` - VERROUILLÉ (Recherchez les technologies appropriées pour débloquer)`
                  ) : ''}`}
                onClick={() => {
                  if (isResourceSite) {
                    handleSiteClick(el.type);
                  }
                }}
                onTouchStart={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  if (isResourceSite) {
                    handleSiteClick(el.type);
                  }
                }}
                onMouseEnter={(e) => {
                  if (isResourceSite && isUnlocked) {
                    e.currentTarget.style.transform = "scale(1.1)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (isResourceSite) {
                    e.currentTarget.style.transform = "scale(1)";
                  }
                }}
              >
                <div style={{ textAlign: "center", lineHeight: "1.1" }}>
                  <div style={{ fontSize: "9px", marginBottom: "2px" }}>
                    {el.type.replace(/_/g, " ")}
                  </div>
                  {isResourceSite && siteLevels[el.type] && (
                    <div style={{ 
                      fontSize: "8px", 
                      background: "rgba(0,0,0,0.3)", 
                      borderRadius: "3px", 
                      padding: "1px 3px" 
                    }}>
                      Niv {siteLevels[el.type]}
                    </div>
                  )}
                </div>
              </button>
            );
          }
        })}
      </div>
        </div>
      </div>
      
      {/* Popups rendus en dehors du conteneur transformé pour éviter les problèmes de positionnement mobile */}
      {/* Popup du site de ressource */}
      {selectedSite && (
        <>
          <ResourceSitePopup
            isOpen={true}
            onClose={() => {
              setSelectedSite(null);
              if (island) {
                fetchSiteLevels(island.id);
              }
            }}
            siteType={selectedSite.siteType}
            islandId={selectedSite.islandId}
            activeCityId={gameShell.currentActiveCity?.id}
          />
        </>
      )}
      {/* Popup d'infos ville */}
      {isCityPopupOpen && selectedCity && (
        <CityPopup
          city={selectedCity}
          player={user}
          ownedCities={citiesData.filter(c => c.owner === user?.id)}
          currentActiveCity={gameShell.currentActiveCity}
          isOpen={isCityPopupOpen}
          onClose={() => { setCityPopupOpen(false); setSelectedCity(null); }}
          onEnterCity={(city) => {
            navigate(`/city/${city.id}`);
          }}
          onViewCity={(city) => {
            navigate(`/city/${city.id}?readonly=1`);
          }}
          onColonize={handleColonize}
          onTransportGoods={handleTransportGoods}
        />
      )}
      
      {/* Popup de transport */}
      {showTransportPopup && gameShell.currentActiveCity && transportDestinationCity && (
        <TransportPopup
          sourceCity={{
            id: gameShell.currentActiveCity.id,
            name: gameShell.currentActiveCity.name,
            resources: gameShell.currentActiveCity.resources || {},
            buildings: gameShell.currentActiveCity.buildings || []
          }}
          destinationCity={{
            id: transportDestinationCity.id,
            name: transportDestinationCity.name
          }}
          onClose={() => {
            setShowTransportPopup(false);
            setTransportDestinationCity(null);
          }}
        />
      )}

      {/* WildCampPreview pour prévisualiser les villages barbares */}
      {showWildCampPreview && selectedWildCamp && (
        <WildCampPreview
          isOpen={showWildCampPreview}
          onClose={() => {
            setShowWildCampPreview(false);
            setselectedWildCamp(null);
          }}
          village={selectedWildCamp}
          onAttackVillage={(village) => {
            // Fermer le preview et ouvrir l'attack popup
            setShowWildCampPreview(false);
            setAttackTargetCity(village);
            setIsAttackPopupOpen(true);
          }}
        />
      )}

      {/* AttackPopupV3 pour attaquer les villages barbares */}
      {isAttackPopupOpen && attackTargetCity && gameShell.currentActiveCity && (
        <AttackPopupV3
          isOpen={isAttackPopupOpen}
          onClose={() => {
            setIsAttackPopupOpen(false);
            setAttackTargetCity(null);
            setAutoOpenBattlefieldId(null); // Reset également le battleId
          }}
          attackerCity={gameShell.currentActiveCity}
          targetCity={attackTargetCity}
          player={user}
        />
      )}

      {/* SimpleBattlefieldV2 ouvert directement depuis l'icône */}
      {simpleBattlefieldOpen && simpleBattlefieldData && createPortal(
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            zIndex: 9999,
            background: '#000',
          }}
        >
          <SimpleBattlefieldV2
            gamePhase={simpleBattlefieldData.gamePhase}
            currentPlayer={simpleBattlefieldData.currentPlayer}
            attackerUnits={simpleBattlefieldData.attackerUnits}
            defenderUnits={simpleBattlefieldData.defenderUnits}
            targetCityId={simpleBattlefieldData.targetCityId}
            battleId={simpleBattlefieldData.battleId}
            battlefieldTemplateId={simpleBattlefieldData.battlefieldTemplateId}
            onClose={() => {
              setSimpleBattlefieldOpen(false);
              setSimpleBattlefieldData(null);
              // Restaurer les barres du jeu
              document.body.classList.remove('battlefield-fullscreen');
            }}
          />
        </div>,
        document.body
      )}
      
    </>
  );
};

export default IslandPage;


