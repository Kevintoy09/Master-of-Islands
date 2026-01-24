import React from "react";
import styles from "./CityMap.module.css";
import ConstructionTimer from "./ConstructionTimer";
import AnimatedCitizen from "./AnimatedCitizen";
import CityAnimations from "./CityAnimations";
import { Slot, CityLayout, CityBuilding } from "../types";

interface CityMapProps {
  layout: CityLayout;
  cityBuildings: CityBuilding[];
  allBuildingsData: Record<string, any>;
  onSlotClick: (slot: Slot, built?: CityBuilding) => void;
  isResearchUnlocked?: (researchId: string) => boolean;
  getInstantFinishThreshold?: () => number;
  onFinishInstant?: (slotId: string) => void;
  hasUnclaimedQuestRewards?: boolean;
}

const CityMap: React.FC<CityMapProps> = ({ 
  layout, 
  cityBuildings, 
  allBuildingsData, 
  onSlotClick, 
  isResearchUnlocked,
  getInstantFinishThreshold,
  onFinishInstant,
  hasUnclaimedQuestRewards = false
}) => {
  // Bâtiments avec fumée
  const shouldShowSmoke = (buildingName: string) => {
    const smokingBuildings = [
      'Scierie',
      'Windmill',
      'Caserne',
      'Port',
      'Thermes',
      'Centre de Ressources',
      'Maison du Chef de Village'
    ];
    return smokingBuildings.includes(buildingName);
  };

  // Fonction pour obtenir l'image du slot ou bâtiment
  const getSlotImage = (slot: Slot, built?: CityBuilding) => {
    if (slot.locked) {
      return '/assets/city/slots/slot_locked.png';
    }
    
    if (built) {
      // Utiliser directement le chemin image du JSON
      const buildingData = allBuildingsData[built.name];
      if (buildingData?.image) {
        return `/${buildingData.image}`;
      }
      // Fallback si pas d'image définie
      return '/assets/city/buildings/standard.png';
    }
    
    // Slot vide selon le type
    return `/assets/city/slots/slot_${slot.type}.png`;
  };

  return (
    <div
      className={styles["city-map-container"]}
    >
      {layout.slots.map((slot) => {
        const built = cityBuildings.find((b) => b.slot_id === slot.id);
        let overlayContent: React.ReactNode = null;
        let isBuilding = false;
        
        if (built) {
          const bData = allBuildingsData[built.name] || {};
          const now = Math.floor(Date.now() / 1000);
          if (built.construction_end && built.construction_end > now) {
            isBuilding = true;
            const secLeft = built.construction_end - now;
            
            // Vérifier si on peut terminer instantanément
            const threshold = getInstantFinishThreshold?.() ?? 0;
            const canFinishInstant = threshold > 0 && secLeft <= threshold;
            
            overlayContent = (
              <div style={{
                position: 'absolute',
                bottom: '5px',
                left: '50%',
                transform: 'translateX(-50%)',
                background: 'rgba(0,0,0,0.7)',
                padding: '4px 8px',
                borderRadius: '4px',
                whiteSpace: 'nowrap'
              }}>
                <span style={{fontSize:'0.7em', color:'#ffa500', fontWeight:'bold'}}>Construction</span>
                <ConstructionTimer 
                  timeRemaining={secLeft}
                  showInstantFinish={canFinishInstant}
                  onInstantFinish={() => onFinishInstant?.(slot.id)}
                />
              </div>
            );
          }
        }
        
        const slotImage = getSlotImage(slot, built);
        // Positionnement adapté au nouveau conteneur 1920×1080
        // slot.x (0-900) et slot.y (0-700) sont les anciennes coordonnées
        // On les convertit vers 1920×1080 avec transformation 0.6x/0.4y
        // 540px devient 1152px (1920*0.6), 280px devient 432px (1080*0.4)
        const left = (slot.x / 900) * 1152; // Convertir de 0-540 vers 0-1152
        const top = (slot.y / 700) * 432;   // Convertir de 0-280 vers 0-432
        
        return (
          <React.Fragment key={slot.id}>
          <div
            className={styles["city-map-slot"]}
            style={{ 
              left: `${left}px`, 
              top: `${top}px`,
              cursor: slot.locked ? 'not-allowed' : 'pointer',
              opacity: slot.locked ? 0.6 : 1
            }}
            title={built ? `${built.name} (niveau ${built.level})` : slot.type}
            onClick={() => {
              if (slot.locked) return;
              onSlotClick(slot, built);
            }}
          >
            {/* Image du slot ou bâtiment */}
            <img
              src={slotImage}
              alt={built ? built.name : slot.type}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'contain',
                pointerEvents: 'none'
              }}
              onError={(e) => {
                // Fallback sur image standard si l'image n'existe pas
                e.currentTarget.src = '/assets/city/buildings/standard.png';
              }}
            />
            
            {/* Overlay pour construction ou niveau */}
            {overlayContent}
            
            {/* Badge niveau pour bâtiments construits */}
            {built && !isBuilding && (
              <div style={{
                position: 'absolute',
                top: '5px',
                right: '5px',
                background: '#d4a853',
                color: '#fff',
                borderRadius: '50%',
                width: '24px',
                height: '24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.8em',
                fontWeight: 'bold',
                boxShadow: '0 2px 4px rgba(0,0,0,0.3)'
              }}>
                {built.level}
              </div>
            )}

            {/* Fumée pour bâtiments de production */}
            {built && !isBuilding && shouldShowSmoke(built.name) && (
              <div className={styles["building-smoke"]}>
                <div className={styles["smoke-puff"]}></div>
                <div className={styles["smoke-puff"]}></div>
                <div className={styles["smoke-puff"]}></div>
              </div>
            )}

            {/* Bonhomme animé pour les récompenses de quêtes (slot_17 = Maison du Chef) */}
            {slot.id === 'slot_17' && built && hasUnclaimedQuestRewards && (
              <div style={{
                position: 'absolute',
                top: '-10px',
                right: '-10px',
                fontSize: '32px',
                animation: 'bounce 1s ease-in-out infinite',
                filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5))',
                cursor: 'pointer',
                zIndex: 10
              }}>
                🧙‍♂️
              </div>
            )}
          </div>
          {/* Animations drapeaux/étoiles positionnées en absolute HORS du slot */}
          {built && !isBuilding && (
            <CityAnimations
              key={`anim-${slot.id}`}
              type="building"
              buildingName={built.name}
              slotPosition={{ left, top }}
            />
          )}
        </React.Fragment>
      );
    })}

    {/* Feu de bois devant la Maison du Chef (slot_17) */}
    {(() => {
      const chiefSlot = layout.slots.find(s => s.id === 'slot_17');
      const chiefBuilding = cityBuildings.find(b => b.slot_id === 'slot_17');
      if (chiefSlot && chiefBuilding && chiefBuilding.name === 'Maison du Chef de Village') {
        // Calculer la position du feu selon le layout
        const left = (chiefSlot.x / 900) * 1152;
        const top = (chiefSlot.y / 700) * 432;
        return <CityAnimations type="campfire" campfirePosition={{ x: left + 40, y: top + 80 }} />;
      }
      return null;
    })()}

    {/* Citoyens animés qui se déplacent */}
    <AnimatedCitizen citizenId={1} cityLayout="city_type_1" />
    <AnimatedCitizen citizenId={2} cityLayout="city_type_1" />
    <AnimatedCitizen citizenId={3} cityLayout="city_type_1" />
    <AnimatedCitizen citizenId={4} cityLayout="city_type_1" />
    <AnimatedCitizen citizenId={5} cityLayout="city_type_1" />
    <AnimatedCitizen citizenId={6} cityLayout="city_type_1" />
    </div>
  );
};

export default CityMap;
