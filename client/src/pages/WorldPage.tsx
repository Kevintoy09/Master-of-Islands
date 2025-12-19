import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../hooks/useUser";
import { useZoomAndDrag } from "../hooks/useZoomAndDrag";
import { getApiUrl } from '../utils/api';
import { universeCache } from '../services/UniverseCache';
import { useGameShell } from "../context/GameShellContext";
// Layout géré par GameShell maintenant

function WorldViewPage() {
  const navigate = useNavigate();
  const { user } = useUser();
  const { currentActiveCity, activeIslandId } = useGameShell();
  const [islands, setIslands] = useState<any[]>([]);
  const [cities, setCities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [initialCenterDone, setInitialCenterDone] = useState(false);
  const availableHeight = window.innerHeight * 0.76; // 76% de la hauteur (100% - 24% barres)
  
  // Taille de la carte FIXE (même taille sur mobile et desktop)
  // Étendue : +44% largeur (1.2 × 1.2), +32% hauteur (1.15 × 1.15)
  const extendedMapWidth = 1920 * 20 * 1.2 * 1.2; // = 55,296 pixels
  const extendedMapHeight = 1080 * 20 * 1.15 * 1.15; // = 28,566 pixels

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
    minZoom: 0.1,
    maxZoom: 2,
    initialZoom: 0.3,
    mapWidth: extendedMapWidth,
    mapHeight: extendedMapHeight
  });

  useEffect(() => {
    Promise.all([
      fetch(`${getApiUrl()}/islands`).then(r => r.json()),
      universeCache.getUniverse(getApiUrl()),
      fetch(`${getApiUrl()}/api/savegame`).then(r => r.json()),
    ]).then(([islandsList, universe, savegame]) => {
      const universeIslands = universe.islands || [];
      
      // Compter le nombre de villes occupées par île depuis savegame.json
      const cityCountByIsland: Record<string, number> = {};
      const occupiedCities = savegame.cities || [];
      
      for (const city of occupiedCities) {
        if (city.owner && city.island_id) {
          cityCountByIsland[city.island_id] = (cityCountByIsland[city.island_id] || 0) + 1;
        }
      }
      
      const mergedIslands = islandsList.map((isle: any) => {
        const full = universeIslands.find((u: any) => u.id === isle.id);
        return full ? { ...isle, ...full, cityCount: cityCountByIsland[isle.id] || 0 } : { ...isle, cityCount: 0 };
      });
      setIslands(mergedIslands);
      const playerCityIds = user.cities || [];
      const allCities = [];
      for (const island of universeIslands) {
        for (const el of island.elements) {
          if (el.type === "city" && playerCityIds.includes(el.id)) {
            allCities.push({ ...el, island_id: island.id });
          }
        }
      }
      setCities(allCities);
      setLoading(false);
    });
  }, [user.cities]);

  // Grille 108x62 - îles entre colonnes 34-104 et lignes 6-56
  // Agrandi proportionnellement : +44% largeur, +32% hauteur (2ème itération)
  const GRID_COLS = 108;
  const GRID_ROWS = 62;

  function hexToPos([x, y]: number[]) {
    // Conversion directe : coordonnées de grille → pixels
    // x: 0-75, y: 0-45
    const cellWidth = extendedMapWidth / GRID_COLS;
    const cellHeight = extendedMapHeight / GRID_ROWS;
    
    const posX = x * cellWidth;
    const posY = y * cellHeight;
    
    return { left: posX, top: posY };
  }

  // Centrer la vue sur l'île de la ville active au chargement initial
  useEffect(() => {
    if (!initialCenterDone && islands.length > 0 && activeIslandId) {
      const activeIsland = islands.find(island => island.id === activeIslandId);
      if (activeIsland && activeIsland.coords) {
        const islandPos = hexToPos(activeIsland.coords);
        
        // Calculer l'offset pour centrer cette île
        const viewportWidth = window.innerWidth;
        const viewportHeight = availableHeight;
        
        const targetX = viewportWidth / 2 - islandPos.left * zoom;
        const targetY = viewportHeight / 2 - islandPos.top * zoom;
        
        setOffset({ x: targetX, y: targetY });
        setInitialCenterDone(true);
      }
    }
  }, [islands, activeIslandId, initialCenterDone, zoom, availableHeight, setOffset]);

  if (loading) return <div>Chargement de la carte...</div>;
  if (!islands || islands.length === 0 || !islands[0].coords) {
    return <div style={{color:'red',textAlign:'center',marginTop:40}}>Aucune île à afficher (données manquantes ou corrompues)</div>;
  }

  const ownedIslandIds = new Set(cities.map(c => c.island_id));

  return (
    /* Carte et boutons - Layout géré par GameShell */
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
        touchAction: "none",
        userSelect: "none",
        WebkitUserSelect: "none",
        WebkitTouchCallout: "none",
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
      <div
        style={{
          width: extendedMapWidth,
          height: extendedMapHeight,
          transform: `translate(${offset.x}px, ${offset.y}px) scale(${zoom})`,
          transformOrigin: "0 0",
          position: "absolute",
          left: 0,
          top: 0,
        }}
      >
        {/* Fond océan - Taille de la carte entière */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            background: "radial-gradient(ellipse at 85% 85%, #a8d8f0 0%, #6db3d8 10%, #3d8ab8 25%, #1e5a88 45%, #0d3555 65%, #051a2d 85%, #020a15 100%)",
            zIndex: 1,
            pointerEvents: "none",
            userSelect: "none"
          }}
        />
        {/* Texture océan */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            backgroundImage: "url(assets/world/ocean1.jpg)",
            backgroundRepeat: "repeat",
            backgroundSize: "600px 600px",
            opacity: 0.15,
            mixBlendMode: "overlay",
            zIndex: 2,
            pointerEvents: "none",
            userSelect: "none"
          }}
        />
        {/* Continent - 25% de la largeur de la carte (pas du viewport) */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "25%",
            height: "100%",
            backgroundImage: "url(assets/world/continent.png)",
            backgroundSize: "cover",
            backgroundRepeat: "no-repeat",
            backgroundPosition: "center",
            opacity: 0.85,
            zIndex: 3,
            pointerEvents: "none",
            userSelect: "none",
            filter: "drop-shadow(0 0 30px rgba(0,0,0,0.5))"
          }}
        />
        {/* Overlay sombre */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            background: "rgba(0,0,0,0.15)",
            zIndex: 4,
            pointerEvents: "none"
          }}
        />
          <h2
            style={{
              position: "absolute",
              left: "50%",
              top: 24,
              transform: "translateX(-50%)",
              color: "white",
              textShadow: "1px 1px 8px #000, 0 0 12px #000b",
              zIndex: 10,
              fontSize: "clamp(1.3em, 5vw, 2.6em)",
              fontWeight: 700,
              margin: 0,
              padding: "0 6vw",
              textAlign: "center",
              lineHeight: 1.2,
              maxWidth: "90vw",
              wordBreak: "break-word"
            }}
          >
            Carte du Monde
          </h2>
          
          {islands.map((island) => {
            const pos = hexToPos(island.coords);
            const owned = ownedIslandIds.has(island.id);
            
            // Utiliser la miniature spécifique de l'île depuis universe.json
            const miniatureUrl = island.miniature || 'assets/world/islands/island_stone_mini_1.png';
            
            return (
              <div key={island.id} style={{ position: "absolute", ...pos, display: "flex", flexDirection: "column", alignItems: "center", zIndex: 100 }}>
                <button
                  style={{
                    width: "500px",
                    height: "400px",
                    borderRadius: "20%",
                    backgroundColor: "transparent",
                    backgroundImage: `url(${miniatureUrl})`,
                    backgroundSize: "contain",
                    backgroundRepeat: "no-repeat",
                    backgroundPosition: "center",
                    border: owned ? "8px solid #ffe600" : "none",
                    color: "white",
                    fontWeight: "bold",
                    cursor: "pointer",
                    boxShadow: owned ? "0 0 30px 4px #ffe600aa" : "none",
                    position: "relative",
                    pointerEvents: "auto",
                    overflow: "visible"
                  }}
                  onClick={() => {
                    navigate(`/island/${island.id}`);
                  }}
                  title={island.name}
                >
                </button>
                <span style={{ 
                  fontSize: "clamp(2.4em, 6vw, 4em)",
                  lineHeight: "1.2",
                  color: "#ffffff",
                  fontWeight: "700",
                  textShadow: "2px 2px 6px #000, 0 0 12px #000, -1px -1px 3px #000",
                  marginTop: "12px",
                  textAlign: "center",
                  maxWidth: "300px",
                  padding: "4px 12px",
                  pointerEvents: "none",
                  position: "relative",
                  zIndex: 101
                }}>{island.name}</span>
                
                {/* Badge nombre de villes occupées - en dessous du nom */}
                {island.cityCount > 0 && (
                  <span style={{
                    fontSize: "clamp(1.8em, 4vw, 3em)",
                    lineHeight: "1.2",
                    color: "#ffd700",
                    fontWeight: "700",
                    textShadow: "3px 3px 8px #000, 0 0 15px #000, -2px -2px 4px #000",
                    marginTop: "8px",
                    textAlign: "center",
                    pointerEvents: "none",
                    position: "relative",
                    zIndex: 101
                  }}>
                    🏛️ {island.cityCount}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>
  );
}

export default WorldViewPage;