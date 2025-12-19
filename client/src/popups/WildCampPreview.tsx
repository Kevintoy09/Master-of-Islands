import React, { useState, useEffect } from 'react';
import { getResourceEmoji, getResourceLabel } from '../constants/resourceIcons';

interface WildCampPreviewProps {
  isOpen: boolean;
  onClose: () => void;
  village: any; // Les données du village barbares depuis IslandPage
  onAttackVillage?: (village: any) => void;
}

interface WildCampInfo {
  level: number;
  description: string;
  difficulty: string;
  units: { [key: string]: number };
  rewards: { [key: string]: number };
}

const WildCampPreview: React.FC<WildCampPreviewProps> = ({
  isOpen,
  onClose,
  village,
  onAttackVillage
}) => {
  const [loading, setLoading] = useState(false);
  const [villageInfo, setVillageInfo] = useState<WildCampInfo | null>(null);

  // Charger les données depuis l'API existante
  useEffect(() => {
    if (isOpen && village && village.barbarianLevel) {
      loadVillageData();
    }
  }, [isOpen, village]);

  const loadVillageData = async () => {
    if (!village?.barbarianLevel) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/pillage/barbarian-preview/${village.barbarianLevel}`);
      
      if (response.ok) {
        const result = await response.json();
        if (result.success && result.data) {
          setVillageInfo({
            level: result.data.level,
            description: result.data.description || `Camp des sauvages de niveau ${result.data.level}`,
            difficulty: result.data.difficulty || (result.data.level <= 2 ? 'Facile' : result.data.level <= 4 ? 'Moyen' : 'Difficile'),
            units: result.data.units || {},
            rewards: result.data.pillable_resources || {}
          });
        } else {
          console.error('❌ [WildCampPreview] Erreur API:', result.error);
          setVillageInfo(null);
        }
      } else {
        console.error('❌ [WildCampPreview] Erreur HTTP:', response.status);
        setVillageInfo(null);
      }
    } catch (error) {
      console.error('❌ [WildCampPreview] Erreur réseau:', error);
      setVillageInfo(null);
    } finally {
      setLoading(false);
    }
  };



  const handleAttack = () => {
    if (village && onAttackVillage) {
      onAttackVillage(village);
      onClose();
    }
  };

  // Fonction pour obtenir l'icône d'une unité
  const getUnitIcon = (unitType: string): string => {
    // Normaliser le nom pour correspondre aux fichiers
    const normalizedUnitType = unitType.toLowerCase().replace(/ /g, '_');
    return `/assets/units/${normalizedUnitType}.png`;
  };

  // Fonction pour traduire le nom de l'unité en français
  const translateUnitName = (unitType: string): string => {
    const translations: { [key: string]: string } = {
      'barbarian_archer': 'Archer barbare',
      'barbarian_warrior': 'Guerrier barbare',
      'barbarian_raider': 'Pillard barbare',
      'slinger': 'Frondeur',
      'archer': 'Archer',
      'militia': 'Milice',
      'infantry_light': 'Infanterie légère',
      'infantry_heavy': 'Infanterie lourde',
      'pikeman': 'Piquier',
      'cavalry_light': 'Cavalerie légère',
      'cavalry_heavy': 'Cavalerie lourde',
      'catapult': 'Catapulte',
      'ballista': 'Baliste',
      'battering_ram': 'Bélier',
      'tribal_shaman': 'Chaman tribal',
      'bandit_leader': 'Chef bandit'
    };
    return translations[unitType] || unitType.replace(/_/g, ' ');
  };

  if (!isOpen) return null;

  return (
    <div 
      className="barbarian-village-popup-overlay"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 1000000,
        padding: '15px',
        boxSizing: 'border-box'
      }}
    >
      <div 
        className="barbarian-village-popup"
        style={{
          background: 'var(--bg-light)',
          border: '3px solid var(--bg-secondary)',
          borderRadius: '12px',
          width: '90%',
          maxWidth: '500px',
          maxHeight: '85vh',
          overflowY: 'auto',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.8)',
          fontFamily: 'var(--font-primary)'
        }}
      >
        {/* En-tête */}
        <div 
          className="barbarian-village-header"
          style={{
            background: 'var(--bg-secondary)',
            color: 'white',
            padding: '8px 12px',
            borderRadius: '9px 9px 0 0',
            borderBottom: '2px solid var(--bg-tertiary)',
            position: 'relative'
          }}
        >
          <button 
            onClick={onClose} 
            style={{
              position: 'absolute',
              top: '6px',
              right: '8px',
              background: 'none',
              border: 'none',
              color: 'white',
              fontSize: '24px',
              cursor: 'pointer',
              padding: '0',
              width: '28px',
              height: '28px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 'bold',
              lineHeight: '1'
            }}
          >
            ×
          </button>
          
          <div style={{ textAlign: 'center' }}>
            <h2 style={{ 
              margin: 0, 
              fontSize: '0.95em', 
              fontWeight: 'bold',
              textShadow: '1px 1px 2px rgba(0, 0, 0, 0.5)',
              marginBottom: '4px'
            }}>
              ⚔️ Camp des Sauvages
            </h2>
            {villageInfo && (
              <div style={{ marginTop: '4px' }}>
                <div style={{
                  display: 'inline-block',
                  background: 'rgba(255, 215, 0, 0.2)',
                  padding: '4px 12px',
                  borderRadius: '12px',
                  border: '2px solid #ffd700',
                  fontSize: '0.85em',
                  fontWeight: 'bold',
                  color: '#ffd700',
                  textShadow: '1px 1px 2px rgba(0, 0, 0, 0.8)'
                }}>
                  Niveau {villageInfo.level}
                </div>
              </div>
            )}
          </div>
        </div>

        <div style={{ padding: '16px' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '30px', fontSize: '1em' }}>
              <div style={{ fontSize: '2.5em', marginBottom: '12px' }}>⏳</div>
              <p>Chargement...</p>
            </div>
          ) : villageInfo ? (
            <div className="village-content">
              {/* Description */}
              {villageInfo.description && (
                <div style={{ 
                  background: 'rgba(139, 69, 19, 0.15)',
                  borderRadius: '8px',
                  padding: '12px',
                  marginBottom: '16px',
                  fontSize: '0.9em',
                  lineHeight: '1.4',
                  fontStyle: 'italic'
                }}>
                  {villageInfo.description}
                </div>
              )}

              {/* Unités défenseuses */}
              <div style={{ marginBottom: '18px' }}>
                <h3 style={{ 
                  fontSize: '1.1em', 
                  marginBottom: '10px',
                  color: 'var(--bg-secondary)',
                  paddingBottom: '6px',
                  borderBottom: '2px solid var(--bg-tertiary)'
                }}>
                  ⚔️ Garnison Ennemie
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {Object.entries(villageInfo.units).map(([unitType, count]) => (
                    <div 
                      key={unitType}
                      style={{
                        background: 'rgba(139, 69, 19, 0.15)',
                        borderRadius: '8px',
                        padding: '10px 12px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px'
                      }}
                    >
                      <div style={{
                        background: 'rgba(0, 0, 0, 0.15)',
                        borderRadius: '8px',
                        padding: '6px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}>
                        <img 
                          src={getUnitIcon(unitType)} 
                          alt={translateUnitName(unitType)}
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = '/assets/units/default.png';
                          }}
                          style={{
                            width: '53px',
                            height: '53px',
                            objectFit: 'contain'
                          }}
                        />
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '0.95em', marginBottom: '2px' }}>
                          {translateUnitName(unitType)}
                        </div>
                        <div style={{ 
                          fontSize: '1.15em', 
                          fontWeight: 'bold',
                          color: '#d4af37'
                        }}>
                          ×{count as number}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Récompenses */}
              <div style={{ marginBottom: '16px' }}>
                <h3 style={{ 
                  fontSize: '1.1em', 
                  marginBottom: '10px',
                  color: 'var(--bg-secondary)',
                  paddingBottom: '6px',
                  borderBottom: '2px solid var(--bg-tertiary)'
                }}>
                  💰 Butin de Guerre
                </h3>
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', 
                  gap: '8px' 
                }}>
                  {Object.entries(villageInfo.rewards).map(([resource, amount]) => (
                    <div 
                      key={resource}
                      style={{
                        background: 'rgba(139, 69, 19, 0.15)',
                        borderRadius: '8px',
                        padding: '10px',
                        textAlign: 'center'
                      }}
                    >
                      <div style={{ fontSize: '1.8em', marginBottom: '4px' }}>
                        {getResourceEmoji(resource)}
                      </div>
                      <div style={{ fontSize: '0.85em', marginBottom: '4px', opacity: 0.9 }}>
                        {getResourceLabel(resource)}
                      </div>
                      <div style={{ 
                        fontSize: '1.2em', 
                        fontWeight: 'bold',
                        color: '#d4af37'
                      }}>
                        {amount as number}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Boutons d'action */}
              <div style={{ 
                display: 'flex', 
                gap: '10px', 
                marginTop: '18px'
              }}>
                <button 
                  onClick={handleAttack} 
                  style={{
                    flex: '1',
                    background: '#8b0000',
                    color: 'white',
                    border: 'none',
                    padding: '12px 20px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '1em',
                    fontWeight: 'bold',
                    boxShadow: '0 3px 12px rgba(139,0,0,0.4)',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#a00000';
                    e.currentTarget.style.transform = 'translateY(-1px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = '#8b0000';
                    e.currentTarget.style.transform = 'translateY(0)';
                  }}
                >
                  ⚔️ Lancer l'Attaque
                </button>
                <button 
                  onClick={onClose} 
                  style={{
                    background: 'var(--bg-secondary)',
                    color: 'white',
                    border: 'none',
                    padding: '12px 20px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '1em',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.opacity = '0.9';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.opacity = '1';
                  }}
                >
                  Annuler
                </button>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '30px' }}>
              <div style={{ fontSize: '2.5em', marginBottom: '12px' }}>❌</div>
              <p>Impossible de charger les informations du village.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WildCampPreview;
