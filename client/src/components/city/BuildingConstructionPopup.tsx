// Composant séparé pour gérer la popup de construction de bâtiments
import React, { useRef, useEffect } from 'react';
import { Slot } from '../../types';
import { RESOURCE_EMOJIS } from '../../constants/resourceIcons';
import './BuildingConstructionPopup.css';

interface BuildingConstructionPopupProps {
  selectedSlot: Slot;
  buildingsList: any[];
  buildingCostsWithBonus: any;
  loadingBuildings: boolean;
  buildingsError: string;
  buildingActionLoading: boolean;
  buildingActionMsg: string | null;
  onClose: () => void;
  onConstructBuilding: (buildingName: string) => void;
}

const BuildingConstructionPopup: React.FC<BuildingConstructionPopupProps> = ({
  selectedSlot,
  buildingsList,
  buildingCostsWithBonus,
  loadingBuildings,
  buildingsError,
  buildingActionLoading,
  buildingActionMsg,
  onClose,
  onConstructBuilding
}) => {
  const popupRef = useRef<HTMLDivElement>(null);

  // Fermer en cliquant à l'extérieur
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onClose]);

  return (
    <div className="building-construction-popup" ref={popupRef}>
      <h3>Bâtiments disponibles pour le slot "{selectedSlot.type}"</h3>
      <button 
        onClick={onClose} 
        style={{position:'absolute',top:8,right:12,fontWeight:'bold'}}
      >
        X
      </button>
      
      {buildingActionMsg && (
        <div style={{
          marginBottom:8, 
          color: buildingActionMsg.startsWith('Erreur') ? 'red' : 'green'
        }}>
          {buildingActionMsg}
        </div>
      )}
      
      {loadingBuildings ? (
        <div>Chargement...</div>
      ) : buildingsError ? (
        <div style={{color:'red'}}>{buildingsError}</div>
      ) : buildingsList.length === 0 ? (
        <div>Aucun bâtiment disponible</div>
      ) : (
        <ul className="building-construction-list">
          {buildingsList
            .filter((building: any) => !building.is_limit_reached)  // ❌ Cacher ceux avec limite atteinte
            .map((building: any) => {
            const level1 = building.levels && building.levels[0];
            const baseCost = level1 && level1.cost ? level1.cost : {};
            const bonusCost = buildingCostsWithBonus[building.name];
            
            // Utiliser le coût de base si pas de bonus d'architecte significatif
            // ou si les économies sont nulles
            const hasRealArchitectBonus = bonusCost && 
              bonusCost.savings && 
              Object.values(bonusCost.savings).some((saving: any) => saving > 0);
            
            const displayCost = hasRealArchitectBonus ? bonusCost.actual_cost : baseCost;
            
            // Construire le chemin de l'image
            // Si l'image commence déjà par "assets/", l'utiliser telle quelle
            const imagePath = building.image 
              ? (building.image.startsWith('assets/') || building.image.startsWith('/assets/') 
                  ? `/${building.image.replace(/^\//, '')}` 
                  : `/assets/city/buildings/${building.image}`)
              : '/assets/city/buildings/standard.png';
            
            const isLocked = !building.has_research;  // 🔒 Verrouillé uniquement si recherche manquante
            
            return (
              <li 
                key={building.name} 
                className={`building-construction-item ${buildingActionLoading ? 'loading' : ''} ${isLocked ? 'locked' : ''}`}
                onClick={() => !isLocked && onConstructBuilding(building.name)}
                style={{ cursor: isLocked ? 'not-allowed' : 'pointer' }}
              >
                {/* Miniature du bâtiment */}
                <div style={{
                  width: '80px',
                  height: '80px',
                  marginRight: '12px',
                  flexShrink: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: '#f0f0f0',
                  borderRadius: '8px',
                  overflow: 'hidden'
                }}>
                  <img 
                    src={imagePath}
                    alt={building.name}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'contain'
                    }}
                    onError={(e) => {
                      e.currentTarget.src = '/assets/city/buildings/standard.png';
                    }}
                  />
                </div>
                
                <div style={{flex:1}}>
                  <div style={{fontWeight:'bold', fontSize:'1.1em', marginBottom:4, display:'flex', alignItems:'center', gap:8}}>
                    {building.name}
                    {isLocked && (
                      <span style={{
                        fontSize: '0.75em',
                        background: '#ff6b6b',
                        color: 'white',
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontWeight: 'normal'
                      }}>
                        🔬 Recherche à débloquer
                      </span>
                    )}
                  </div>
                  <div style={{color:'#666', fontSize:'0.97em', marginBottom:6}}>
                    {building.description || ''}
                  </div>
                  
                  {/* Coût */}
                  {displayCost && Object.keys(displayCost).length > 0 && (
                    <div style={{fontSize:'0.95em', color:'#444', marginTop:4}}>
                      <span style={{fontWeight:'bold', color:'#888'}}>Coût : </span>
                      {Object.entries(displayCost).map(([res, val]: any, i, arr) => {
                        const resourceEmoji = RESOURCE_EMOJIS[res] || '❓';
                        return (
                          <span key={res} style={{marginRight:6}}>
                            <span style={{fontSize:'1.1em', marginRight:3}}>
                              {resourceEmoji}
                            </span>
                            <span style={hasRealArchitectBonus ? {color: '#228B22', fontWeight: 'bold'} : {}}>
                              {val}
                            </span>
                            {hasRealArchitectBonus && bonusCost.savings && bonusCost.savings[res] && (
                              <span style={{
                                marginLeft: 2,
                                fontSize: '0.8em',
                                color: '#888',
                                textDecoration: 'line-through'
                              }}>
                                ({baseCost[res]})
                              </span>
                            )}
                            {i < arr.length-1 ? ',' : ''}
                          </span>
                        );
                      })}
                    </div>
                  )}
                  
                  {/* Temps de construction */}
                  <div style={{
                    fontSize: '0.85em',
                    color: '#666',
                    marginTop: 4,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4
                  }}>
                    <span style={{fontWeight:'bold', color:'#888'}}>⏱️ Temps : </span>
                    {bonusCost && bonusCost.actual_construction_time !== undefined ? (
                      <>
                        <span style={hasRealArchitectBonus ? {color: '#228B22', fontWeight: 'bold'} : {}}>
                          {bonusCost.actual_construction_time}s
                        </span>
                        {hasRealArchitectBonus && bonusCost.time_saved > 0 && (
                          <>
                            <span style={{
                              fontSize: '0.8em',
                              color: '#888',
                              textDecoration: 'line-through'
                            }}>
                              ({bonusCost.base_construction_time}s)
                            </span>
                            <span style={{
                              marginLeft: 4,
                              fontSize: '0.8em',
                              color: '#228B22',
                              fontWeight: 'bold'
                            }}>
                              (-{bonusCost.time_saved}s)
                            </span>
                          </>
                        )}
                      </>
                    ) : (
                      <span>{level1?.construction_time || 30}s</span>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
};

export default BuildingConstructionPopup;
