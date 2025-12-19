// Export des popups de bâtiments de production
import AcademyPopupContent from './AcademyPopupContent';
import SawmillPopupContent from './SawmillPopupContent';
import ResourceCenterPopupContent from './ResourceCenterPopupContent';
import EmbassyPopupContent from './EmbassyPopupContent';
import PortPopupContent from './PortPopupContent';
import WindmillPopupContent from './WindmillPopupContent';
import WarehousePopupContent from './WarehousePopupContent';
import MarketPopupContent from './MarketPopupContent';

export { 
  AcademyPopupContent, 
  SawmillPopupContent, 
  ResourceCenterPopupContent, 
  EmbassyPopupContent, 
  PortPopupContent, 
  WindmillPopupContent, 
  WarehousePopupContent, 
  MarketPopupContent 
};

// Types pour les props des popups
export interface BuildingPopupProps {
  city: any;
  building: any;
  onClose: () => void;
  onCityDataChange?: () => void;
}

// Fonction utilitaire pour déterminer quel popup utiliser
export function getBuildingPopupComponent(buildingName: string) {
  // Test ultra simple pour Market - toutes les variantes possibles
  if (buildingName === 'Market' || 
      buildingName === 'market' || 
      buildingName === 'Marché' || 
      buildingName === 'marché') {
    return MarketPopupContent;
  }
  
  const lowerName = buildingName?.toLowerCase();
  
  switch (lowerName) {
    case 'academy':
    case 'académie':
      return AcademyPopupContent;
    case 'scierie':
    case 'sawmill':
      return SawmillPopupContent;
    case 'mine':
    case 'centre de ressources':
    case 'resource center':
      return ResourceCenterPopupContent;
    case 'ambassade':
    case 'embassy':
      return EmbassyPopupContent;
    case 'port':
      return PortPopupContent;
    case 'moulin':
    case 'windmill':
      return WindmillPopupContent;
    case 'entrepôt':
    case 'warehouse':
      return WarehousePopupContent;
    case 'marché':
    case 'market':
      return MarketPopupContent;
    default:
      return null;
  }
}
