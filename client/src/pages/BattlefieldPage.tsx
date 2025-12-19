import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import SimpleBattlefieldV2 from '../components/SimpleBattlefieldV2';
import { getApiUrl } from '../utils/api';

interface BattlefieldPageProps {}

const BattlefieldPage: React.FC<BattlefieldPageProps> = () => {
  const { battleId } = useParams<{ battleId: string }>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    if (!battleId) {
      setError('ID de bataille manquant');
      setLoading(false);
      return;
    }
    
    // Vérifier que la bataille existe
    const checkBattleExists = async () => {
      try {
        console.log('🔍 [Mobile] Chargement battlefield:', `${getApiUrl()}/api/military/battlefield_v2/${battleId}`);
        const response = await fetch(`${getApiUrl()}/api/military/battlefield_v2/${battleId}`);
        if (response.ok) {
          const data = await response.json();
          console.log('✅ [Mobile] Données battlefield reçues:', data);
          if (!data.battlefield) {
            console.error('❌ [Mobile] Battlefield introuvable dans les données');
            setError(`Bataille ${battleId} introuvable`);
          } else {
            console.log('✅ [Mobile] Battlefield trouvé, chargement OK');
          }
        } else {
          console.error('❌ [Mobile] Erreur HTTP battlefield:', response.status, response.statusText);
          setError('Erreur lors du chargement des données de bataille');
        }
      } catch (err) {
        setError('Erreur de connexion');
      } finally {
        setLoading(false);
      }
    };
    
    checkBattleExists();
  }, [battleId]);
  
  if (loading) {
    return (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          background: 'var(--bg-primary)',
          color: 'var(--roman-gold)',
          fontSize: '1.5em',
          fontFamily: 'var(--secondary-font)'
        }}>
          🎮 Chargement de la bataille...
        </div>
    );
  }
  
  if (error) {
    return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          height: 'calc(100vh - 140px)',
          background: 'var(--bg-primary)',
          color: 'var(--text-light)',
          textAlign: 'center',
          padding: '20px'
        }}>
          <h2 style={{ color: 'var(--roman-red)', marginBottom: '20px' }}>
            ⚠️ Erreur
          </h2>
          <p style={{ fontSize: '1.2em', marginBottom: '30px' }}>
            {error}
          </p>
          <button
            onClick={() => window.history.back()}
            style={{
              padding: '12px 24px',
              backgroundColor: 'var(--roman-gold)',
              color: 'var(--bg-primary)',
              border: 'none',
              borderRadius: '8px',
              fontSize: '1.1em',
              fontWeight: 'bold',
              cursor: 'pointer',
              fontFamily: 'var(--secondary-font)'
            }}
          >
            ← Retour
          </button>
        </div>
    );
  }
  
  return (
    <div style={{ 
      height: '100vh', 
      width: '100vw',
      position: 'fixed',
      top: 0,
      left: 0,
      zIndex: 9999,
      background: 'var(--bg-primary)'
    }}>
      <SimpleBattlefieldV2 
        battleId={battleId!}
        gamePhase="battle"
        currentPlayer="attacker"
      />
    </div>
  );
};

export default BattlefieldPage;