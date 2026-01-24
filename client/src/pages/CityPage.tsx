import React, { useMemo, useEffect } from "react";

import { useParams, useLocation, useNavigate } from "react-router-dom";
import { useUser } from "../hooks/useUser";
import CityMap from "../components/CityMap";
import BuildingPopup from "../components/BuildingPopup";
import BuildingConstructionPopup from "../components/city/BuildingConstructionPopup";
import ErrorPopup from "../components/ErrorPopup";
import { useAutoUpdatePopulation } from "../hooks/useAutoUpdatePopulation";
import { usePlayerResearch } from "../hooks/usePlayerResearch";
import { useCity } from "../hooks/city/useCity";
import { useBuildingManagement } from "../hooks/city/useBuildingManagement";
import { useBuildingConstruction } from "../hooks/city/useBuildingConstruction";
import { useZoomAndDrag } from "../hooks/useZoomAndDrag";

const CityPage: React.FC = () => {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useUser();
  
  // Détection du mode lecture seule
  const searchParams = new URLSearchParams(location.search);
  const isReadonly = searchParams.get('readonly') === '1';
  
  // État pour l'onglet par défaut à ouvrir
  const [defaultTabToOpen, setDefaultTabToOpen] = React.useState<string | undefined>(undefined);
  
  // État pour les récompenses de quêtes non réclamées
  const [hasUnclaimedQuestRewards, setHasUnclaimedQuestRewards] = React.useState(false);

  // Hooks principaux
  const { 
    city, 
    layout, 
    allBuildingsData, 
    loading, 
    error, 
    reloadCityData, 
    renameTownHall
  } = useCity({ cityId: id });

  const {
    selectedBuilding,
    setSelectedBuilding,
    developBuilding,
    destroyBuilding,
    finishInstantConstruction,
    canFinishInstant,
    updateSelectedBuildingFromCity,
    errorPopup: buildingErrorPopup,
    setErrorPopup: setBuildingErrorPopup
  } = useBuildingManagement({ 
    cityId: id, 
    onCityDataChange: async () => {
      const cityData = await reloadCityData();
      updateSelectedBuildingFromCity(cityData);
      return cityData;
    }
  });

  const {
    selectedSlot,
    buildingsList,
    buildingCostsWithBonus,
    loadingBuildings,
    buildingsError,
    buildingActionLoading: constructionLoading,
    buildingActionMsg: constructionMsg,
    errorPopup: constructionErrorPopup,
    setErrorPopup: setConstructionErrorPopup,
    handleSlotClick,
    constructBuilding,
    closeConstructionPopup
  } = useBuildingConstruction({ 
    cityId: id, 
    onCityDataChange: reloadCityData 
  });

  // Hooks secondaires  
  const { error: populationError } = useAutoUpdatePopulation({ 
    cityId: id, 
    enabled: !!city 
  });
  const { isResearchUnlocked, getInstantFinishThreshold } = usePlayerResearch();

  // Vérifier les récompenses de quêtes non réclamées
  useEffect(() => {
    if (!user?.username) {
      setHasUnclaimedQuestRewards(false);
      return;
    }

    const checkUnclaimedQuestRewards = async () => {
      try {
        const response = await fetch(`/api/quests/unclaimed?username=${user.username}`);
        if (response.ok) {
          const data = await response.json();
          const hasRewards = (data.unclaimed_rewards || []).length > 0;
          setHasUnclaimedQuestRewards(hasRewards);
        }
      } catch (error) {
        console.error('Erreur vérification récompenses de quêtes:', error);
      }
    };

    checkUnclaimedQuestRewards();
    const interval = setInterval(checkUnclaimedQuestRewards, 30000);

    return () => clearInterval(interval);
  }, [user?.username]);

  // Dimensions de l'image (1920×1080)
  const mapWidth = 1920;
  const mapHeight = 1080;

  // Calculer zoom pour remplir l'écran complètement (sans zones blanches)
  const calculateInitialZoom = () => {
    const screenWidth = window.innerWidth;
    const screenHeight = window.innerHeight;
    
    // Zoom pour remplir TOUT l'écran (on prend le max pour couvrir complètement)
    const zoomX = screenWidth / mapWidth;
    const zoomY = screenHeight / mapHeight;
    
    // Math.max garantit qu'il n'y aura pas de blanc
    return Math.max(zoomX, zoomY);
  };

  // minZoom = zoom initial pour ne jamais voir de blanc
  const minZoom = calculateInitialZoom();

  // Calculer offset initial pour centrer l'image
  const calculateInitialOffset = () => {
    const screenWidth = window.innerWidth;
    const screenHeight = window.innerHeight;
    const scaledWidth = mapWidth * minZoom;
    const scaledHeight = mapHeight * minZoom;
    
    // Centrer l'image zoomée
    const offsetX = (screenWidth - scaledWidth) / 2;
    const offsetY = (screenHeight - scaledHeight) / 2;
    
    return { x: offsetX, y: offsetY };
  };

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
    handleTouchEnd,
    setOffset
  } = useZoomAndDrag({
    minZoom: minZoom,
    maxZoom: 3,
    initialZoom: minZoom,
    mapWidth: mapWidth,
    mapHeight: mapHeight
  });

  // Appliquer l'offset initial au chargement
  React.useEffect(() => {
    const initialOffset = calculateInitialOffset();
    setOffset(initialOffset);
  }, []);

  // Mémoriser buildingData pour éviter les re-rendus
  const buildingData = useMemo(() => {
    if (!selectedBuilding) return {};
    return allBuildingsData[selectedBuilding.name] || {};
  }, [allBuildingsData, selectedBuilding]);

  // Gérer l'ouverture automatique de la caserne via URL
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const openBuilding = searchParams.get('openBuilding');
    const tab = searchParams.get('tab');
    
    if (openBuilding === 'barracks' && city && city.buildings) {
      // Trouver la caserne dans les bâtiments de la ville
      const barracks = city.buildings.find((building: any) => 
        building.name === 'Caserne' || building.type === 'barracks'
      );
      
      if (barracks) {
        // Définir l'onglet par défaut et ouvrir la caserne
        setDefaultTabToOpen(tab === 'garrison' ? 'garrison' : undefined);
        setSelectedBuilding(barracks);
        
        // Nettoyer l'URL immédiatement
        const newUrl = location.pathname;
        window.history.replaceState({}, '', newUrl);
      }
    } else if (!openBuilding) {
      // Réinitialiser l'onglet par défaut si pas de paramètres URL
      setDefaultTabToOpen(undefined);
    }
  }, [location.search, city, setSelectedBuilding]);

  // Fonction pour terminer construction instantanée depuis la carte
  const handleFinishInstantFromMap = async (slotId: string) => {
    if (!city) return;
    await finishInstantConstruction(slotId);
  };

  // Gérer les clics sur les slots
  const handleSlotClickWrapper = async (slot: any, built?: any) => {
    if (built) {
      // Si c'est la Maison du Chef de Village, ouvrir la page des quêtes
      if (built.name === 'Maison du Chef de Village') {
        navigate('/quests');
        return;
      }
      setSelectedBuilding(built);
      return;
    }
    await handleSlotClick(slot);
  };

  // Wrappers de compatibilité pour les types
  const selectedBuildingWrapper = selectedBuilding ? {
    name: selectedBuilding.name,
    level: selectedBuilding.level,
    status: selectedBuilding.status || 'completed'
  } : null;

  const cityWrapper = city ? {
    id: city.id,
    name: city.name || "Nouvelle ville",
    owner: city.owner,
    city_coords: city.city_coords || [0, 0] as [number, number],
    controlable: city.controlable,
    layout: city.layout || city.city_layout || (layout && layout.id) || "default_city_layout",
    buildings: Array.isArray(city.buildings) ? city.buildings : [],
    resources: city.resources || {},
    workers_assigned: city.workers_assigned || {}
  } : null;

  if (loading) {
    return <div>Chargement...</div>;
  }

  if (error) {
    return <div style={{color: 'red'}}>{error}</div>;
  }

  return (
    <>
      {/* Affichage d'erreur pour la population */}
      {populationError && (
        <div style={{
          position: 'fixed',
          top: 85,
          right: 10,
          background: '#ffebee',
          color: '#c62828',
          padding: '8px 12px',
          borderRadius: 4,
          fontSize: '0.8em',
          zIndex: 1001,
          border: '1px solid #ef5350'
        }}>
          Erreur population: {populationError}
        </div>
      )}

        {/* Carte avec zoom et drag */}
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            overflow: 'hidden',
            cursor: 'grab',
            zIndex: 1,
            touchAction: 'none', // Désactive tous les gestes natifs du navigateur
            userSelect: 'none', // Empêche la sélection de texte
            WebkitUserSelect: 'none',
            WebkitTouchCallout: 'none', // Désactive le menu contextuel sur iOS
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
              position: 'absolute',
              width: '100%',
              height: '100%',
              transform: `translate(${offset.x}px, ${offset.y}px) scale(${zoom})`,
              transformOrigin: '0 0',
            }}
          >
            {/* Conteneur 1920×1080 avec image et slots ENSEMBLE (incrustés) */}
            <div style={{ 
              position: 'absolute',
              top: 0,
              left: 0,
              width: '1920px',
              height: '1080px',
            }}>
              {/* Image de fond 1920×1080 */}
              {layout && layout.background && (
                <img
                  src={`/${layout.background}`}
                  alt="ville"
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "1920px",
                    height: "1080px",
                    objectFit: "fill",
                    zIndex: 1,
                    pointerEvents: "none",
                    userSelect: "none"
                  }}
                />
              )}
              
              {/* Slots positionnés sur l'image */}
              <div style={{ 
                position: 'absolute',
                top: 0,
                left: 0,
                width: '1920px',
                height: '1080px',
                zIndex: 2
              }}>
                {layout && (
                  <CityMap
                    layout={layout}
                    cityBuildings={city ? city.buildings || [] : []}
                    allBuildingsData={allBuildingsData}
                    isResearchUnlocked={isResearchUnlocked}
                    getInstantFinishThreshold={getInstantFinishThreshold}
                    onFinishInstant={isReadonly ? (() => {}) : handleFinishInstantFromMap}
                    onSlotClick={isReadonly ? (() => {}) : handleSlotClickWrapper}
                    hasUnclaimedQuestRewards={hasUnclaimedQuestRewards}
                  />
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Popup de construction */}
        {!isReadonly && selectedSlot && (
          <BuildingConstructionPopup
            selectedSlot={selectedSlot}
            buildingsList={buildingsList}
            buildingCostsWithBonus={buildingCostsWithBonus}
            loadingBuildings={loadingBuildings}
            buildingsError={buildingsError}
            buildingActionLoading={constructionLoading}
            buildingActionMsg={constructionMsg}
            onClose={closeConstructionPopup}
            onConstructBuilding={constructBuilding}
          />
        )}

        {/* Popup de bâtiment */}
        {!isReadonly && selectedBuilding && selectedBuildingWrapper && cityWrapper && (
          <BuildingPopup
            key={selectedBuilding.slot_id}
            building={selectedBuilding}
            buildingData={buildingData}
            city={cityWrapper}
            onClose={() => {
              setSelectedBuilding(null);
              setDefaultTabToOpen(undefined); // Réinitialiser l'onglet par défaut
            }}
            onCityDataChange={reloadCityData}
            onDevelop={() => developBuilding(selectedBuilding)}
            onDestroy={() => destroyBuilding(selectedBuilding)}
            onFinishInstant={() => finishInstantConstruction(selectedBuilding.slot_id)}
            canFinishInstant={canFinishInstant}
            onRenameTownHall={renameTownHall}
            defaultTab={defaultTabToOpen}
          />
        )}

        {/* Popup d'erreur pour la construction */}
        {constructionErrorPopup && (
          <ErrorPopup
            isOpen={true}
            onClose={() => setConstructionErrorPopup(null)}
            title={constructionErrorPopup.title}
            message={constructionErrorPopup.message}
            icon={constructionErrorPopup.icon}
          />
        )}

        {/* Popup d'erreur pour le développement */}
        {buildingErrorPopup && (
          <ErrorPopup
            isOpen={true}
            onClose={() => setBuildingErrorPopup(null)}
            title={buildingErrorPopup.title}
            message={buildingErrorPopup.message}
            icon={buildingErrorPopup.icon}
          />
        )}

        {/* Overlay lecture seule */}
        {isReadonly && (
          <div style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.25)',
            zIndex: 10000,
            pointerEvents: 'auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 28,
            color: '#fff',
            fontWeight: 700,
            textShadow: '1px 1px 8px #000',
            userSelect: 'none',
          }}>
            <div style={{
              background: 'rgba(30,30,30,0.7)',
              borderRadius: 16,
              padding: '32px 48px',
              boxShadow: '0 0 32px #000',
              border: '2px solid #fff3',
            }}>
              <span>Consultation uniquement<br />Aucune action possible</span>
            </div>
          </div>
        )}
    </>
  );
};

export default CityPage;