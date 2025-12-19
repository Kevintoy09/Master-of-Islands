import React from 'react';

interface CitySelectionPopupProps {
  cities: Array<{
    id: string;
    name: string;
    island_coords?: [number, number];
  }>;
  title: string;
  onSelectCity: (city: any) => void;
  onClose: () => void;
}

const CitySelectionPopup: React.FC<CitySelectionPopupProps> = ({
  cities,
  title,
  onSelectCity,
  onClose
}) => {
  return (
    <div className="popup-overlay" onClick={onClose}>
      <div className="popup-content" onClick={(e) => e.stopPropagation()}>
        <div className="popup-header">
          <h2 className="popup-title">{title}</h2>
          <button className="popup-close" onClick={onClose}>×</button>
        </div>

        <div className="popup-body">
          <div className="popup-section">
            <div className="popup-section-title">🏛️ Sélectionnez une ville</div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: 'var(--spacing-sm)',
              marginTop: 'var(--spacing-sm)'
            }}>
              {cities.map((city) => (
                <button
                  key={city.id}
                  onClick={() => onSelectCity(city)}
                  className="roman-button"
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    padding: 'var(--spacing-md)',
                    textAlign: 'center'
                  }}
                >
                  <div className="roman-subtitle" style={{ marginBottom: '4px' }}>
                    {city.name}
                  </div>
                  <div className="roman-text" style={{ fontSize: '0.8em', opacity: 0.7 }}>
                    {city.island_coords ? 
                      `Île (${city.island_coords[0]},${city.island_coords[1]})` : 
                      'Île inconnue'
                    }
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="popup-actions">
          <button onClick={onClose} className="roman-button secondary">
            Annuler
          </button>
        </div>
      </div>
    </div>
  );
};

export default CitySelectionPopup;
