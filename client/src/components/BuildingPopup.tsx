import React, { useEffect, useState, useMemo } from "react";
import { createPortal } from "react-dom";
import BuildingPopupBase from "../popups/BuildingPopupBase";
import TownHallPopupContent from "../popups/TownHallPopupContent";
import AcademyPopupContent from "../popups/AcademyPopupContent";
import SawmillPopupContent from "../popups/SawmillPopupContent";
import ResourceCenterPopupContent from "../popups/ResourceCenterPopupContent";
import PortPopupContent from "../popups/PortPopupContent";
import EmbassyPopupContent from "../popups/EmbassyPopupContent";
import WindmillPopupContent from "../popups/WindmillPopupContent";
import WarehousePopupContent from "../popups/WarehousePopupContent";
import MarketPopupContent from "../popups/MarketPopupContent";
import ArchitectWorkshopPopupContent from "../popups/ArchitectWorkshopPopupContent";
import BarracksPopupContent from "../popups/BarracksPopupContent";
import ForgePopupContent from "../popups/ForgePopupContent";
import WallPopupContent from "../popups/WallPopupContent";
import SatisfactionPopup from "../popups/SatisfactionPopup";
import ThermesPopupContent from "../popups/ThermesPopupContent";
import PopulationManagementPopup from "../popups/PopulationManagementPopup";
import { useUser } from '../hooks/useUser';

interface City {
  id: string;
  name: string;
  owner: string | null;
  city_coords: [number, number];
  controlable: boolean;
  layout: string;
  buildings?: any[];
  resources?: Record<string, number>;
  gold_rate?: number;
  workers_assigned?: Record<string, number>; // Ajouter le champ manquant
}

interface CityBuilding {
  slot_id: string;
  name: string;
  level: number;
  construction_end?: number;
}

interface BuildingPopupProps {
  building: CityBuilding;
  buildingData: any;
  city: City;
  onClose: () => void;
  onDevelop: () => void;
  onDestroy: () => void;
  onFinishInstant: () => void;
  canFinishInstant: boolean;
  onRenameTownHall?: (newName: string) => void;
  onCityDataChange?: () => void; // Nouvelle prop pour notifier les changements
  defaultTab?: string; // Nouveau prop pour l'onglet par défaut
}

const BuildingPopup: React.FC<BuildingPopupProps> = ({
  building,
  buildingData,
  city,
  onClose,
  onDevelop,
  onDestroy,
  onFinishInstant,
  canFinishInstant,
  onRenameTownHall,
  onCityDataChange,
  defaultTab
}) => {
  const { user } = useUser();
  const [architectBonuses, setArchitectBonuses] = useState<{cost_reduction: number, time_reduction: number} | null>(null);
  const [constructionTimeMultiplier, setConstructionTimeMultiplier] = useState<number>(1.0);
  const [showSatisfactionPopup, setShowSatisfactionPopup] = useState(false);
  const [showPopulationPopup, setShowPopulationPopup] = useState(false);
  const [hideMainPopup, setHideMainPopup] = useState(false);
  const [currentTime, setCurrentTime] = useState(Math.floor(Date.now() / 1000));

  // Charger le multiplicateur de temps de construction global
  useEffect(() => {
    fetch('/admin/api/construction-multiplier/status')
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setConstructionTimeMultiplier(data.multiplier || 1.0);
        }
      })
      .catch(err => console.warn('Could not load construction time multiplier:', err));
  }, []);

  // Cacher l'hôtel de ville quand on ouvre les popups enfants (sans le démonter)
  const handleOpenSatisfaction = () => {
    setShowSatisfactionPopup(true);
    setHideMainPopup(true); // Cache l'hôtel de ville
  };

  const handleOpenPopulation = () => {
    setShowPopulationPopup(true);
    setHideMainPopup(true); // Cache l'hôtel de ville
  };

  // Restaurer la visibilité quand on ferme les popups enfants
  const handleCloseSatisfaction = () => {
    setShowSatisfactionPopup(false);
    setHideMainPopup(false);
  };

  const handleClosePopulation = () => {
    setShowPopulationPopup(false);
    setHideMainPopup(false);
  };

  // Effect séparé pour les bonus architecte - ne dépend que de city.id
  useEffect(() => {
    fetch(`/api/city/${city.id}/architect-bonuses`)
      .then(res => res.json())
      .then(data => {
        setArchitectBonuses(data);
      })
  }, [city.id]);

  // Mettre à jour le temps actuel chaque seconde pour le timer
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(Math.floor(Date.now() / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const now = currentTime;
  const isInConstruction = typeof building.construction_end === 'number' && building.construction_end > now;
  const timer = isInConstruction && typeof building.construction_end === 'number' ? building.construction_end - now : 0;
  
  // Utiliser directement buildingData du parent
  const effectiveBuildingData = buildingData;
  
  // Récupérer les effets et coûts correctement
  const currentLevelData = effectiveBuildingData?.levels?.find((l: any) => l.level === building.level);
  const nextLevelData = effectiveBuildingData?.levels?.find((l: any) => l.level === building.level + 1);
  
  const effectsCurrent = currentLevelData?.effect;
  const effectsNext = nextLevelData?.effect;
  
  // Calculer le coût et le temps avec useMemo pour recalculer quand les dépendances changent
  const { developmentCost, originalCost, constructionTime, originalTime } = useMemo(() => {
    const baseCost = nextLevelData?.cost;
    const originalCost = nextLevelData?.cost;
    const originalTime = nextLevelData?.construction_time;
    let adjustedCost = baseCost;
    let adjustedTime = originalTime;

    // Appliquer le bonus de coût architecte
    if (adjustedCost && architectBonuses?.cost_reduction) {
      const reduction = architectBonuses.cost_reduction / 100;
      adjustedCost = Object.fromEntries(
        Object.entries(adjustedCost).map(([resource, cost]) => [
          resource,
          Math.ceil((cost as number) * (1 - reduction))
        ])
      );
    }

    // Calculer le temps de construction avec multiplicateur global + bonus architecte + bonus faction
    if (adjustedTime) {
      // 1. Appliquer le multiplicateur global
      adjustedTime = adjustedTime * constructionTimeMultiplier;
      
      // 2. Puis appliquer le bonus architecte
      if (architectBonuses?.time_reduction) {
        const timeReduction = architectBonuses.time_reduction / 100;
        adjustedTime = adjustedTime * (1 - timeReduction);
      }
      
      // 3. 🏛️ Bonus faction Stone : -10% temps construction
      if (user?.faction === 'stone') {
        adjustedTime = adjustedTime * 0.9; // -10%
      }
      
      // 4. Arrondir et minimum 1 seconde
      adjustedTime = Math.max(1, Math.ceil(adjustedTime));
    }

    return {
      developmentCost: adjustedCost,
      originalCost,
      constructionTime: adjustedTime,
      originalTime
    };
  }, [nextLevelData, architectBonuses, constructionTimeMultiplier, user?.faction]);
  
  const formatEffects = (eff: any) => {
    if (!eff) return "Aucun.";
    return Object.entries(eff).map(([key, value]) => {
      // Formatage spécial pour certains types d'effets
      if (key === 'storage' || key === 'secure_storage') {
        const storageEntries = Object.entries(value as Record<string, number>);
        return `- ${key} : ${storageEntries.map(([res, val]) => `${res}:${val}`).join(', ')}`;
      }
      return `- ${key} : ${value}`;
    }).join('\n');
  };

  // Déterminer le texte du bouton de destruction selon le niveau
  const destroyButtonText = building.level > 1 
    ? `Rétrograder (niveau ${building.level} → ${building.level - 1})` 
    : "Détruire définitivement";

  // Détermine si on utilise un popup spécialisé (qui a son propre titre)
  const hasSpecializedPopup = ['Academy', 'Centre de Ressources', 'Scierie', 'Port', 'Ambassade', 'Windmill', 'Hôtel de Ville', "Forge d'Armement", 'Muraille'].includes(building.name);

  return (
    <>
      <div style={{ display: hideMainPopup ? 'none' : 'block' }}>
        <BuildingPopupBase
          title={effectiveBuildingData?.name || building.name} // Toujours passer le titre
          description={effectiveBuildingData?.description || ''}
          cost={developmentCost}
        originalCost={originalCost}
        constructionTime={constructionTime}
        originalTime={originalTime}
        level={building.level}
        effectsCurrent={effectsCurrent}
        effectsNext={effectsNext}
        timer={timer}
        onDevelop={!isInConstruction && nextLevelData ? onDevelop : undefined}
        onDestroy={!isInConstruction ? onDestroy : undefined}
        destroyButtonText={destroyButtonText}
        onFinishInstant={onFinishInstant}
        canFinishInstant={canFinishInstant}
        onClose={onClose}
      >
        {building.name === 'Hôtel de Ville' && city && (
          <TownHallPopupContent
            city={city}
            onRename={onRenameTownHall || (() => {})}
            onOpenSatisfaction={handleOpenSatisfaction}
            onOpenPopulation={handleOpenPopulation}
          />
        )}
        {building.name === 'Academy' && city && (
          <AcademyPopupContent
            city={city}
            building={building}
            onClose={onClose}
            onCityDataChange={onCityDataChange}
          />
        )}
        {building.name === 'Scierie' && city && (
          <SawmillPopupContent
            city={city}
            building={building}
            onClose={onClose}
            onCityDataChange={onCityDataChange}
          />
        )}
        {(building.name === 'Mine' || building.name === 'Centre de Ressources') && city && (
          <ResourceCenterPopupContent
            city={city}
            building={building}
            onClose={onClose}
            onCityDataChange={onCityDataChange}
          />
        )}
        {building.name === 'Port' && city && (
          <PortPopupContent
            city={city}
            building={building}
            onClose={onClose}
            onCityDataChange={onCityDataChange}
          />
        )}
        {building.name === 'Ambassade' && city && (
          <EmbassyPopupContent
            city={city}
            building={building}
            onClose={onClose}
            onCityDataChange={onCityDataChange}
          />
        )}
        {building.name === 'Windmill' && city && (
          <WindmillPopupContent
            city={city}
            building={building}
            onClose={onClose}
            onCityDataChange={onCityDataChange}
          />
        )}
        {building.name === 'Thermes' && city && (
          <ThermesPopupContent
            city={city}
            building={building}
            onClose={onClose}
            onCityDataChange={onCityDataChange}
          />
        )}
        {building.name === 'Entrepôt' && city && (
          <WarehousePopupContent
            city={city}
            building={building}
            onClose={onClose}
            onCityDataChange={onCityDataChange}
          />
        )}
        {building.name === 'Market' && city && (
          <MarketPopupContent
            city={city}
            building={building}
            onClose={onClose}
            onCityDataChange={onCityDataChange}
          />
        )}
        {building.name === "Atelier d'Architecte" && city && (
          <ArchitectWorkshopPopupContent
            city={city}
            building={building}
            onClose={onClose}
            onCityDataChange={onCityDataChange}
          />
        )}
        {building.name === 'Caserne' && city && (
          <BarracksPopupContent
            city={city}
            building={building}
            onClose={onClose}
            onCityDataChange={onCityDataChange}
            defaultTab={defaultTab as 'production' | 'garrison'}
          />
        )}
        {building.name === "Forge d'Armement" && city && (
          <ForgePopupContent
            city={city}
            building={building}
            onClose={onClose}
            onCityDataChange={onCityDataChange}
          />
        )}
        {building.name === 'Muraille' && city && (
          <WallPopupContent
            city={city}
            building={building}
            onClose={onClose}
            onCityDataChange={onCityDataChange}
          />
        )}
      </BuildingPopupBase>
      </div>

      {/* Popup de satisfaction - Rendu via Portal pour être au-dessus */}
      {showSatisfactionPopup && city && createPortal(
        <SatisfactionPopup
          cityId={city.id}
          cityName={city.name}
          onClose={handleCloseSatisfaction}
        />,
        document.body
      )}

      {/* Popup de gestion population - Rendu via Portal pour être au-dessus */}
      {showPopulationPopup && city && createPortal(
        <PopulationManagementPopup
          cityId={city.id}
          cityName={city.name}
          onClose={handleClosePopulation}
        />,
        document.body
      )}
    </>
  );
};

export default BuildingPopup;
