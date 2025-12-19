import React, { useState, useEffect } from 'react';

interface BarbarianVillagePreviewProps {
  isOpen: boolean;
  onClose: () => void;
  village: any; // Les données du village barbares depuis IslandPage
  onAttackVillage?: (village: any) => void;
}

interface BarbarianVillageInfo {
  level: number;
  description: string;
  difficulty: string;
  units: { [key: string]: number };
  rewards: { [key: string]: number };
}

const BarbarianVillagePreview: React.FC<BarbarianVillagePreviewProps> = ({
  isOpen,
  onClose,
  village,
  onAttackVillage
}) => {
  const [loading, setLoading] = useState(false);
  const [villageInfo, setVillageInfo] = useState<BarbarianVillageInfo | null>(null);

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
          console.error('❌ [BarbarianVillagePreview] Erreur API:', result.error);
          setVillageInfo(null);
        }
      } else {
        console.error('❌ [BarbarianVillagePreview] Erreur HTTP:', response.status);
        setVillageInfo(null);
      }
    } catch (error) {
      console.error('❌ [BarbarianVillagePreview] Erreur réseau:', error);
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
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'flex-start',
        zIndex: 1000000,
        paddingTop: '16vh',
        paddingBottom: '6vh',
        boxSizing: 'border-box'
      }}
    >
      <div 
        className="barbarian-village-popup"
        style={{
          background: 'var(--bg-light)',
          border: '3px solid var(--bg-secondary)',
          borderRadius: 'var(--border-radius-large)',
          width: '80%',
          maxWidth: '450px',
          maxHeight: '75vh',
          overflowY: 'auto',
          boxShadow: 'var(--shadow-heavy)',
          fontFamily: 'var(--font-primary)'
        }}
      >
        <div 
          className="barbarian-village-header"
          style={{
            background: 'var(--bg-secondary)',
            color: 'white',
            padding: '15px 20px',
            borderRadius: 'var(--border-radius-large) var(--border-radius-large) 0 0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '2px solid var(--bg-tertiary)'
          }}
        >
          <h2 style={{ margin: 0, fontSize: '1.3em', fontWeight: 'bold', textShadow: '1px 1px 2px rgba(0, 0, 0, 0.5)' }}>
            🏺 Camp des Sauvages - Niveau {villageInfo?.level || '?'}
          </h2>
          <button 
            onClick={onClose} 
            style={{
              background: 'none',
              border: 'none',
              color: 'white',
              fontSize: '24px',
              cursor: 'pointer',
              padding: '0',
              width: '30px',
              height: '30px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            ×
          </button>
        </div>

        <div style={{ padding: '20px' }}>
          {loading ? (
            <div className="loading-content">
              <p>Chargement des informations du village...</p>
            </div>
          ) : villageInfo ? (
            <div className="village-content">
            <div className="village-info" style={{ marginBottom: '20px' }}>
              <p style={{ margin: '8px 0' }}><strong>Description:</strong> {villageInfo.description}</p>
              <p style={{ margin: '8px 0' }}><strong>Difficulté:</strong> <span style={{ color: villageInfo.difficulty === 'Facile' ? '#4caf50' : villageInfo.difficulty === 'Moyen' ? '#ff9800' : '#f44336' }}>{villageInfo.difficulty}</span></p>
            </div>

            <div className="village-units" style={{ marginBottom: '20px' }}>
              <h3 style={{ color: 'var(--bg-secondary)', marginBottom: '10px' }}>🛡️ Unités défenseuses</h3>
              <div className="units-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                {Object.entries(villageInfo.units).map(([unitType, count]) => (
                  <div 
                    key={unitType} 
                    className="unit-item"
                    style={{
                      background: 'var(--bg-tertiary)',
                      padding: '8px',
                      borderRadius: '6px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: '12px'
                    }}
                  >
                    <span className="unit-name">{unitType.replace('_', ' ')}</span>
                    <span className="unit-count" style={{ fontWeight: 'bold' }}>x{count as number}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="village-rewards" style={{ marginBottom: '20px' }}>
              <h3 style={{ color: 'var(--bg-secondary)', marginBottom: '10px' }}>💰 Récompenses potentielles</h3>
              <div className="rewards-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                {Object.entries(villageInfo.rewards).map(([resource, amount]) => (
                  <div 
                    key={resource} 
                    className="reward-item"
                    style={{
                      background: 'var(--bg-tertiary)',
                      padding: '8px',
                      borderRadius: '6px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: '12px'
                    }}
                  >
                    <span className="resource-name">{resource}</span>
                    <span className="resource-amount" style={{ fontWeight: 'bold', color: '#d4af37' }}>{amount as number}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="popup-actions" style={{ marginTop: '20px', display: 'flex', gap: '10px', justifyContent: 'center' }}>
              <button 
                onClick={handleAttack} 
                style={{
                  background: 'linear-gradient(135deg, #8b0000 0%, #600000 100%)',
                  color: 'white',
                  border: 'none',
                  padding: '10px 20px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  boxShadow: '0 3px 12px rgba(139,0,0,0.4)',
                  transition: 'all 0.2s ease'
                }}
              >
                ⚔️ Attaquer le village
              </button>
              <button 
                onClick={onClose} 
                style={{
                  background: 'var(--bg-secondary)',
                  color: 'white',
                  border: 'none',
                  padding: '10px 20px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Annuler
              </button>
            </div>
            </div>
          ) : (
            <div className="error-content">
              <p>Impossible de charger les informations du village.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BarbarianVillagePreview;
