import React from 'react';
import BarracksPopupContent from '../popups/BarracksPopupContent';
import '../styles/BarracksPopupContent.css';

interface MilitaryGarrisonPopupProps {
  isOpen: boolean;
  onClose: () => void;
  cityId: string;
}

const MilitaryGarrisonPopup: React.FC<MilitaryGarrisonPopupProps> = ({
  isOpen,
  onClose,
  cityId,
}) => {
  if (!isOpen) return null;

  // Créer un objet city minimal avec l'ID
  const city = { id: cityId, name: '' };
  
  // Créer un objet building minimal pour la caserne 
  const building = { name: 'Caserne', level: 1 };

  return (
    <BarracksPopupContent
      city={city}
      building={building}
      onClose={onClose}
      onCityDataChange={() => {}}
      defaultTab="garrison"
    />
  );
};

export default MilitaryGarrisonPopup;