import React, { useState, useEffect, useCallback } from "react";
import "./HeaderBar.css";
import ResourceProductionPopup from "./ResourceProductionPopup";
import PopulationInfoPopup from "./PopulationInfoPopup";
import GoldProductionPopup from "./GoldProductionPopup";
import { RESOURCE_EMOJIS, RESOURCE_LABELS } from "../constants/resourceIcons";
import { useUnlockedResources } from "../hooks/useUnlockedResources";
import { getApiUrl } from "../utils/api";
import { useRefreshInterval } from "../hooks/useRefreshInterval";

interface HeaderBarProps {
  cityName: string;
  cityId?: string;
  resources: { [key: string]: number | string };
  storageLimits?: { [key: string]: number };  // Nouvelle propriété
  populationInfo?: {
    current_population: number;
    max_capacity: number;
    growth_per_hour: number;
    real_growth_per_hour: number;
    time_multiplier: number;
    time_info: string;
  };
  userCities: Array<{id: string, name: string}>;
  activeCityId: string;
  onCityChange: (cityId: string) => void;
  playerInfo?: {
    transport_ships_total?: number;
    transport_ships_available?: number;
    player_id?: string;  // Ajout du player_id
  };
  onTransportShipsClick?: () => void;
  activeTransportsCount: number;
  goldProductionRate?: number;
  onMilitaryClick?: () => void;
  hasActiveBattles?: boolean;  // Nouv eau: indique si le joueur a des batailles actives
}

const HeaderBar: React.FC<HeaderBarProps> = ({ 
  cityName, 
  cityId, 
  resources,
  storageLimits = {},
  populationInfo, 
  userCities, 
  activeCityId, 
  onCityChange,
  playerInfo,
  onTransportShipsClick,
  goldProductionRate,
  onMilitaryClick,
  hasActiveBattles = false
}) => {
  // États pour le popup de production
  const [selectedResource, setSelectedResource] = useState<{
    key: string;
    name: string;
    amount: number;
  } | null>(null);

  // État pour le popup de population
  const [showPopulationPopup, setShowPopulationPopup] = useState(false);

  // État pour le popup d'or
  const [showGoldPopup, setShowGoldPopup] = useState(false);

  // État pour la réduction du headerbar
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Hook pour vérifier les ressources débloquées
  const { isResourceUnlocked, loading: resourcesLoading } = useUnlockedResources(playerInfo?.player_id || null);

  // État pour le tick manuel
  const [isExecutingTick, setIsExecutingTick] = useState(false);
  const [tickFeedback, setTickFeedback] = useState<string | null>(null);
  // État de visibilité des contrôles de tick (contrôlé depuis l'admin)
  const [showTickControls, setShowTickControls] = useState<boolean>(true);

  // Les ressources sont prêtes quand elles ne sont plus en chargement
  const isResourceDataReady = !resourcesLoading;

  // Vérifier quelles lignes de ressources doivent être affichées
  const line3Resources = ["marble", "wine", "horse", "glass"];
  const line3HasVisible = isResourceDataReady && line3Resources.some(resource => isResourceUnlocked(resource));
  
  const line4Resources = ["coal", "gunpowder", "spices", "cotton"];
  const line4HasVisible = isResourceDataReady && line4Resources.some(resource => isResourceUnlocked(resource));

  // Calculer la hauteur selon les lignes visibles
  const getHeaderHeight = () => {
    if (isCollapsed) return { height: "5vh", minHeight: "40px", maxHeight: "61px" };
    
    let visibleLines = 2; // Lignes 1 et 2 toujours visibles
    if (line3HasVisible) visibleLines++;
    if (line4HasVisible) visibleLines++;
    
    // Calcul simple : environ 3.8vh par ligne
    const vhHeight = visibleLines * 3.8;
    const pxHeight = visibleLines * 30 + 20; // 30px par ligne + padding
    
    return {
      height: `${vhHeight}vh`,
      minHeight: `${pxHeight}px`,
      maxHeight: `${Math.min(pxHeight + 20, 150)}px`
    };
  };

  const headerStyle = getHeaderHeight();

  // Écouteurs d'événements pour les clics depuis le BottomNavBar
  React.useEffect(() => {
    const handleGoldPopupEvent = () => {
      setShowGoldPopup(true);
    };

    const handleTransportPopupEvent = () => {
      if (onTransportShipsClick) {
        onTransportShipsClick();
      }
    };

    // Ajouter les écouteurs d'événements
    window.addEventListener('openGoldPopup', handleGoldPopupEvent);
    window.addEventListener('openTransportPopup', handleTransportPopupEvent);

    // Nettoyer les écouteurs au démontage
    return () => {
      window.removeEventListener('openGoldPopup', handleGoldPopupEvent);
      window.removeEventListener('openTransportPopup', handleTransportPopupEvent);
    };
  }, [onTransportShipsClick]);

  // Charger le statut de visibilité des contrôles de tick depuis l'admin
  const loadTickControlsVisibility = useCallback(async () => {
    try {
      const response = await fetch(`${getApiUrl()}/admin/api/tick-controls-status`);
      const data = await response.json();
      if (data.success) {
        setShowTickControls(data.visible);
      }
    } catch (error) {
      console.error('Erreur lors du chargement de la visibilité des contrôles:', error);
      // En cas d'erreur, garder les contrôles visibles par défaut
    }
  }, []);

  // Utiliser le hook de rafraîchissement dynamique - importer en haut du fichier
  useRefreshInterval(loadTickControlsVisibility);

  // Fonction pour exécuter un tick manuel
  const executeManualTick = async (event?: React.MouseEvent) => {
    event?.preventDefault();
    event?.stopPropagation();
    
    if (isExecutingTick) return;
    
    setIsExecutingTick(true);
    setTickFeedback(null);
    
    try {
      const response = await fetch('/admin/api/manual-tick', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const result = await response.json();
      
      if (result.success) {
        const { gold_updated, research_updated, population_updated } = result.results;
        setTickFeedback(`✅ Tick: ${gold_updated} or, ${research_updated} recherche, ${population_updated} pop`);
        
        // Les ressources seront actualisées lors du prochain rafraîchissement automatique
        // ou quand l'utilisateur naviguera
      } else {
        setTickFeedback(`❌ Erreur: ${result.error}`);
      }
    } catch (error) {
      setTickFeedback(`❌ Erreur réseau: ${error}`);
    } finally {
      setIsExecutingTick(false);
      
      // Effacer le feedback après 3 secondes
      setTimeout(() => {
        setTickFeedback(null);
      }, 3000);
    }
  };



  // Styles réutilisables optimisés pour économiser l'espace horizontal
  const bubbleStyles = {
    golden: {
      background: "#B8860B",
      border: "1px solid #FFD700",
      borderRadius: "9px",
      padding: "2px 4px",             // Padding latéral réduit pour mobile
      margin: "0 1px",                // Marge réduite
      boxShadow: "0 1px 3px rgba(0, 0, 0, 0.3)",
      fontSize: "1.0em",              // Police légèrement réduite
      minHeight: "15px",              // Hauteur réduite (-30%)
      lineHeight: "1.2"
    },
    bronze: {
      background: "#8B4513",
      border: "1px solid #DAA520",
      borderRadius: "9px",
      padding: "2px 4px",             // Padding latéral réduit pour mobile
      margin: "0 1px",                // Marge réduite
      boxShadow: "0 1px 3px rgba(0, 0, 0, 0.3)",
      fontSize: "1.0em",              // Police légèrement réduite
      minHeight: "15px",              // Hauteur réduite (-30%)
      lineHeight: "1.2"
    },
    selector: {
      background: "#8B4513",
      border: "1px solid #DAA520",
      borderRadius: "9px",
      padding: "3px 5px",             // Padding légèrement augmenté
      margin: "0 2px",                // Marge légèrement augmentée
      boxShadow: "0 1px 3px rgba(0, 0, 0, 0.3)",
      fontSize: "1.1em",              // Police légèrement augmentée
      minHeight: "18px",              // Hauteur légèrement augmentée
      lineHeight: "1.2",
      cursor: "pointer",
      color: "white",
      outline: "none"
    }
  };

  // Fonction utilitaire pour garantir qu'on a un nombre
  const asNumber = (value: number | string | undefined): number => {
    if (typeof value === 'number') {
      // Gérer les NaN et valeurs infinies
      if (isNaN(value) || !isFinite(value)) return 0;
      return value;
    }
    if (typeof value === 'string') {
      const parsed = parseFloat(value);
      if (isNaN(parsed) || !isFinite(parsed)) return 0;
      return parsed;
    }
    return 0;
  };

  // Fonction pour formater les nombres avec K/M et maximum 4 caractères
  const formatNumber = (value: number): string => {
    if (value < 10000) {
      return Math.floor(value).toString();
    } else if (value < 1000000) {
      return (value / 1000).toFixed(1) + 'K';
    } else {
      return (value / 1000000).toFixed(1) + 'M';
    }
  };

  // Fonction pour obtenir le style de couleur selon la capacité de stockage
  const getResourceStyle = (resourceKey: string, bubbleStyle: React.CSSProperties): React.CSSProperties => {
    const amount = asNumber(resources[resourceKey]);
    const limit = storageLimits[resourceKey];
    
    if (!limit || limit === 0) return bubbleStyle;
    
    const percentage = (amount / limit) * 100;
    
    if (percentage >= 100) {
      // Rouge gras quand max atteint
      return {
        ...bubbleStyle,
        color: '#ff0000',
        fontWeight: 'bold',
        textShadow: '0 0 3px rgba(255, 0, 0, 0.5)'
      };
    } else if (percentage >= 75) {
      // Orange quand >=75%
      return {
        ...bubbleStyle,
        color: '#ff8c00'
      };
    }
    
    return bubbleStyle;
  };

  // Ressources qui ont une production (excluent les ressources statiques)
  const productionResources = ['wood', 'stone', 'iron', 'cereal', 'papyrus', 'marble', 'wine', 'horse', 'glass', 'coal', 'gunpowder', 'spices', 'cotton'];

  // Handler pour le clic sur une ressource
  const handleResourceClick = (resourceKey: string) => {
    // Si c'est les bateaux de transport, appeler le callback spécial
    if (resourceKey === 'transport_ships' && onTransportShipsClick) {
      onTransportShipsClick();
      return;
    }
    
    // Si c'est la population, ouvrir le popup de population
    if (resourceKey === 'population' && cityId) {
      setShowPopulationPopup(true);
      return;
    }
    
    // Si c'est l'or, ouvrir le popup de production d'or
    if (resourceKey === 'gold') {
      setShowGoldPopup(true);
      return;
    }
    
    // Vérifier si c'est une ressource avec production
    if (productionResources.includes(resourceKey) && cityId) {
      setSelectedResource({
        key: resourceKey,
        name: RESOURCE_LABELS[resourceKey] || resourceKey,
        amount: asNumber(resources[resourceKey])
      });
    } else {
      // Pour les autres ressources, on peut afficher une alerte ou faire une action par défaut
      
    }
  };



  return (
    <>
      <header
      className="header-bar"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        maxWidth: "100vw",
        minWidth: 0,
        height: headerStyle.height,
        minHeight: headerStyle.minHeight,
        maxHeight: headerStyle.maxHeight,
        background: "var(--bg-secondary)",
        color: "var(--text-light)",
        zIndex: 1000,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-start",
        padding: "6px 6px 3px 6px", // Padding légèrement augmenté
        boxSizing: "border-box",
        overflowX: "auto",
        boxShadow: "var(--shadow-heavy)",
        borderBottom: "3px solid #ecf0f1"
      }}
    >
      {/* LIGNE 1: PLAYER INFO - Différente visuellement */}
      <div className="header-bar__line header-bar__player-line" style={{
        marginBottom: 4, // Espacement légèrement augmenté
        minHeight: "26px" // Hauteur augmentée pour équilibrer avec bottombar
      }}>
        {/* Spinner de sélection de ville - déplacé en première position */}
        {userCities && userCities.length > 0 && (
          <select
            className="header-bar__city-selector"
            value={activeCityId && userCities.find(city => city.id === activeCityId) ? activeCityId : userCities[0]?.id || ''}
            onChange={(e) => onCityChange(e.target.value)}
            style={{
              ...bubbleStyles.selector,
              fontWeight: "bold",
              minWidth: "60px",  // Légèrement plus large en première position
              fontSize: "1.0em"  // Police augmentée
            }}
          >
            {userCities.map((city) => (
              <option key={city.id} value={city.id}>
                {city.name}
              </option>
            ))}
          </select>
        )}
        
        {/* Population - déplacée en ligne 1 */}
        <span 
          className="header-bar__res-item" 
          onClick={() => handleResourceClick("population")}
          style={{ 
            ...bubbleStyles.bronze,
            fontWeight: "bold",
            minWidth: "60px"
          }}
        >
          <span className="header-bar__res-value-badge" style={{ fontSize: '16px' }}>
            <span style={{ fontSize: '16px', marginRight: '2px' }}>{RESOURCE_EMOJIS.population_total}</span>
            {`${Math.floor(asNumber(resources.population_free))}/${Math.floor(asNumber(resources.population_total))}`}
            {populationInfo && populationInfo.max_capacity && (
              <span style={{ color: '#888', fontSize: '11px' }}>_{Math.floor(asNumber(populationInfo.max_capacity))}</span>
            )}
          </span>
        </span>

        {/* Bouton militaire - déplacé en ligne 1 */}
        <button
          onClick={onMilitaryClick}
          style={{
            background: hasActiveBattles ? "linear-gradient(135deg, #ff6b35 0%, #ff8c42 100%)" : "#8b4513",
            border: hasActiveBattles ? "2px solid #ffa500" : "1px solid #A0522D", 
            borderRadius: "8px",
            padding: "2px 6px",
            margin: "0 1px",
            boxShadow: hasActiveBattles ? "0 0 15px rgba(255, 140, 66, 0.8), 0 1px 3px rgba(0, 0, 0, 0.3)" : "0 1px 3px rgba(0, 0, 0, 0.3)",
            fontSize: "16px",
            minHeight: "16px",
            cursor: "pointer",
            color: "#f4e4bc",
            outline: "none",
            minWidth: "auto",
            animation: hasActiveBattles ? "flicker-glow 1.2s ease-in-out infinite" : "none",
            position: "relative",
            filter: "none"
          }}
          title={hasActiveBattles ? "Bataille en cours ! Cliquez pour gérer" : "Gestion militaire"}
        >
          ⚔️
        </button>

        
        {/* Bouton Tick Manuel - Contrôlé depuis l'interface admin */}
        {showTickControls && (
          <button
            type="button"
            onClick={executeManualTick}
            disabled={isExecutingTick}
            style={{
              background: isExecutingTick ? "#666" : "#4CAF50",
              border: "2px solid #45a049", 
              borderRadius: "14px",
              padding: "3px 8px",
              margin: "0 2px",
              boxShadow: "0 2.7px 5.4px rgba(0, 0, 0, 0.4)",
              fontSize: "14px",
              minHeight: "18px",
              cursor: isExecutingTick ? "not-allowed" : "pointer",
              color: "#fff",
              outline: "none",
              minWidth: "auto",
              opacity: isExecutingTick ? 0.6 : 1
            }}
            title={isExecutingTick ? "Exécution en cours..." : "Exécuter un tick manuel (or, recherche, population)"}
          >
            {isExecutingTick ? "⏳" : "⚡"}
          </button>
        )}
        
        {/* Bouton de réduction/agrandissement */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          style={{
            background: "#D3D3D3",  // Gris clair uniforme
            border: "2px solid #A9A9A9",  // Bordure gris plus foncé
            borderRadius: "14px",
            padding: "3px 6px",   // Réduit de 5px 8px pour mobile
            margin: "0 2px",      // Réduit de 4px à 2px pour mobile
            boxShadow: "0 2.7px 5.4px rgba(0, 0, 0, 0.4)",
            fontSize: "18px",     // Police augmentée
            minHeight: "18px",
            cursor: "pointer",
            color: "#333",        // Texte sombre sur fond clair
            outline: "none",
            minWidth: "auto"
          }}
          title={isCollapsed ? "Agrandir le headerbar" : "Réduire le headerbar"}
        >
          {isCollapsed ? "🔼" : "🔽"}
        </button>
      </div>

      {/* LIGNES 2, 3 et 4 - Masquées si réduit */}
      {!isCollapsed && (
        <>
      {/* LIGNE 2: RESSOURCES PRINCIPALES + POPULATION */}
      <div className="header-bar__line header-bar__city-line" style={{ 
        marginBottom: 3, // Espacement réduit entre les lignes
        minHeight: "24px" // Hauteur augmentée de +20%
      }}>
        {/* Ressources principales de la ville : bois, pierre, céréales, fer, papyrus */}
        {["wood", "stone", "cereal", "iron", "papyrus"].map((key) => (
          key in resources ? (
            <span 
              key={key}
              className="header-bar__res-item"
              onClick={() => handleResourceClick(key)}
              style={getResourceStyle(key, bubbleStyles.bronze)}
            >
              <span className="header-bar__res-value-badge">
                <span style={{ fontSize: '16px', marginRight: '2px' }}>{RESOURCE_EMOJIS[key]}</span>
                {formatNumber(asNumber(resources[key]))}
              </span>
              {key === 'cereal' && asNumber(resources['cereal_consumption_per_tick']) > 0 && (
                <span style={{ color: '#FFB6C1', fontSize: '0.8em', marginLeft: 2 }}>
                  -{(asNumber(resources['cereal_consumption_per_tick']) * 360).toFixed(1)}
                </span>
              )}
            </span>
          ) : null
        ))}
      </div>

      {/* LIGNE 3: RESSOURCES SECONDAIRES - Affichée seulement si des ressources sont débloquées */}
      {isResourceDataReady && line3HasVisible && (
        <div className="header-bar__line header-bar__secondary-line" style={{ 
          marginBottom: 3, // Espacement réduit entre les lignes
          minHeight: "24px" // Hauteur augmentée de +20%
        }}>
          {["marble", "wine", "horse", "glass"].map((key) => (
            isResourceUnlocked(key) ? (
              <span 
                key={key}
                className="header-bar__res-item"
                onClick={() => handleResourceClick(key)}
                style={getResourceStyle(key, bubbleStyles.bronze)}
              >
                <span className="header-bar__res-value-badge">
                  <span style={{ fontSize: '11px', marginRight: '1px' }}>{RESOURCE_EMOJIS[key]}</span>
                  {formatNumber(asNumber(resources[key]))}
                </span>
              </span>
            ) : null
          ))}
        </div>
      )}

      {/* LIGNE 4: RESSOURCES AVANCÉES - Affichée seulement si des ressources sont débloquées */}
      {isResourceDataReady && line4HasVisible && (
        <div className="header-bar__line header-bar__advanced-line" style={{
          minHeight: "20px" // Hauteur augmentée de +20%
        }}>
          {["coal", "gunpowder", "spices", "cotton"].map((key) => (
            isResourceUnlocked(key) ? (
              <span 
                key={key}
                className="header-bar__res-item"
                onClick={() => handleResourceClick(key)}
                style={getResourceStyle(key, bubbleStyles.bronze)}
              >
                <span className="header-bar__res-value-badge">
                  <span style={{ fontSize: '15px', marginRight: '2px' }}>{RESOURCE_EMOJIS[key]}</span>
                  {formatNumber(asNumber(resources[key]))}
                </span>
              </span>
            ) : null
          ))}
        </div>
      )}
        </>
      )}
    </header>

    {/* Feedback du tick manuel */}
    {tickFeedback && (
      <div
        style={{
          position: "fixed",
          top: "60px",
          right: "10px",
          background: tickFeedback.startsWith("✅") ? "#4CAF50" : "#f44336",
          color: "white",
          padding: "8px 12px",
          borderRadius: "8px",
          boxShadow: "0 4px 8px rgba(0, 0, 0, 0.3)",
          zIndex: 10000,
          fontSize: "14px",
          fontWeight: "bold",
          maxWidth: "300px",
          wordWrap: "break-word"
        }}
      >
        {tickFeedback}
      </div>
    )}

    {/* Popup de production des ressources */}
    {selectedResource && (
      <ResourceProductionPopup
        resourceKey={selectedResource.key}
        resourceName={selectedResource.name}
        currentAmount={selectedResource.amount}
        cityId={cityId}
        onClose={() => setSelectedResource(null)}
      />
    )}

    {/* Popup d'informations de population */}
    {showPopulationPopup && cityId && (
      <PopulationInfoPopup
        cityId={cityId}
        cityName={cityName}
        onClose={() => setShowPopulationPopup(false)}
      />
    )}

    {/* Popup de production d'or */}
    {showGoldPopup && (
      <GoldProductionPopup
        onClose={() => setShowGoldPopup(false)}
      />
    )}
  </>
  );
};

export default HeaderBar;
