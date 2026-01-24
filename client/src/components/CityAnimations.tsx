import React, { useState, useEffect } from 'react';

interface CityAnimationsProps {
  buildingName?: string;
  slotPosition?: { left: number; top: number };
  campfirePosition?: { x: number; y: number };
  type: 'building' | 'campfire';
}

const CityAnimations: React.FC<CityAnimationsProps> = ({
  buildingName,
  slotPosition,
  campfirePosition,
  type,
}) => {
  const [flameFrame, setFlameFrame] = useState(0);

  useEffect(() => {
    if (type === 'campfire') {
      const interval = setInterval(() => {
        setFlameFrame((prev) => (prev + 1) % 3);
      }, 200);
      return () => clearInterval(interval);
    }
  }, [type]);

  // ===== CAMPFIRE =====
  if (type === 'campfire' && campfirePosition) {
    return (
      <div
        style={{
          position: 'absolute',
          left: `${campfirePosition.x}px`,
          top: `${campfirePosition.y}px`,
          pointerEvents: 'none',
          zIndex: 9,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        {/* Bûches */}
        <div style={{ fontSize: '24px', position: 'relative', zIndex: 1 }}>
          🪵
        </div>
        
      {/* Flamme unique animée */}
      <div
        style={{
          position: 'absolute',
          bottom: '8px',
          zIndex: 2,
        }}
      >
        <span
          style={{
            fontSize: '24px',
            display: 'inline-block',
            transform: `translateY(${flameFrame === 0 ? '-3px' : flameFrame === 1 ? '-5px' : '-2px'}) scale(${flameFrame === 0 ? 1.1 : flameFrame === 1 ? 0.95 : 1.05})`,
            transition: 'transform 0.2s ease',
          }}
        >
          🔥
        </span>
      </div>
      
      {/* Fumée */}
      <div
        style={{
          position: 'absolute',
          bottom: '20px',
          fontSize: '16px',
          animation: 'campfireSmokeRise 3s ease-in-out infinite',
          opacity: 0,
        }}
      >
        💨
      </div>
      
      <style>{`
        @keyframes campfireSmokeRise {
          0% {
            transform: translateY(0px) translateX(0px);
            opacity: 0;
          }
          20% {
            opacity: 0.4;
          }
          100% {
            transform: translateY(-40px) translateX(10px);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  );
  }

  // ===== BUILDING ANIMATIONS =====
  if (type === 'building' && buildingName && slotPosition) {
    // Hôtel de Ville - Drapeaux
    if (buildingName === "Hôtel de Ville") {
      return (
        <div
          style={{
            position: 'absolute',
            left: `${slotPosition.left}px`,
            top: `${slotPosition.top}px`,
            width: '100px',
            height: '100px',
            pointerEvents: 'none',
            zIndex: 10,
            overflow: 'visible',
          }}
        >
          {/* Drapeau coin bas gauche */}
          <div
            style={{
              position: 'absolute',
              left: '0px',
              bottom: '0px',
              fontSize: '30px',
              animation: 'flag-wave 2.5s ease-in-out infinite',
              filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.4))',
            }}
          >
            🚩
          </div>
          {/* Drapeau coin bas droit */}
          <div
            style={{
              position: 'absolute',
              right: '0px',
              bottom: '0px',
              fontSize: '30px',
              animation: 'flag-wave 2.5s ease-in-out infinite',
              animationDelay: '0.5s',
              filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.4))',
            }}
          >
            🚩
          </div>
          
          <style>{`
            @keyframes flag-wave {
              0%, 100% { transform: rotate(0deg) scaleX(1); }
              25% { transform: rotate(12deg) scaleX(0.92); }
              50% { transform: rotate(0deg) scaleX(1); }
              75% { transform: rotate(-12deg) scaleX(0.92); }
            }
          `}</style>
        </div>
      );
    }

    // Academy - Étoiles
    if (buildingName === "Academy") {
      return (
        <div
          style={{
            position: 'absolute',
            left: `${slotPosition.left}px`,
            top: `${slotPosition.top}px`,
            width: '100px',
            height: '100px',
            pointerEvents: 'none',
            zIndex: 10,
            overflow: 'visible',
          }}
        >
          <div
            style={{
              position: 'absolute',
              left: '30px',
              bottom: '50px',
              fontSize: '22px',
              animation: 'star-rise 4s ease-out infinite',
              opacity: 0,
              filter: 'drop-shadow(0 0 4px rgba(255, 215, 0, 0.8))',
            }}
          >
            ⭐
          </div>
          <div
            style={{
              position: 'absolute',
              left: '50px',
              bottom: '55px',
              fontSize: '22px',
              animation: 'star-rise 4s ease-out infinite',
              animationDelay: '1.3s',
              opacity: 0,
              filter: 'drop-shadow(0 0 4px rgba(255, 215, 0, 0.8))',
            }}
          >
            ⭐
          </div>
          <div
            style={{
              position: 'absolute',
              left: '40px',
              bottom: '45px',
              fontSize: '22px',
              animation: 'star-rise 4s ease-out infinite',
              animationDelay: '2.6s',
              opacity: 0,
              filter: 'drop-shadow(0 0 4px rgba(255, 215, 0, 0.8))',
            }}
          >
            ⭐
          </div>
          
          <style>{`
            @keyframes star-rise {
              0% {
                transform: translateY(0) scale(0.4) rotate(0deg);
                opacity: 0;
              }
              15% {
                opacity: 1;
              }
              85% {
                opacity: 0.9;
              }
              100% {
                transform: translateY(-90px) scale(1.3) rotate(180deg);
                opacity: 0;
              }
            }
          `}</style>
        </div>
      );
    }
  }

  return null;
};

export default CityAnimations;
