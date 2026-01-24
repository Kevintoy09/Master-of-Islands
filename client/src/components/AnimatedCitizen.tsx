import React, { useState, useEffect } from 'react';
import styles from './AnimatedCitizen.module.css';

interface AnimatedCitizenProps {
  citizenId: number;
  cityLayout: string;
}

// Points de passage pour différents itinéraires
const WAYPOINTS_ROUTES = [
  [ // Route 1 - Diagonale Nord-Est vers Sud-Ouest
    { x: 1500, y: 1000 },
    { x: 1300, y: 750 },
    { x: 1450, y: 500 },
    { x: 600, y: 250 },
    { x: 450, y: 300 },
    { x: 300, y: 250 },
  ],
  [ // Route 2 - Horizontale centre
    { x: 1100, y: 800 },
    { x: 1300, y: 220 },
    { x: 500, y: 200 },
    { x: 1400, y: 220 },
    { x: 500, y: 240 },
    { x: 300, y: 200 },
  ],
  [ // Route 3 - Verticale gauche
    { x: 200, y: 100 },
    { x: 220, y: 200 },
    { x: 200, y: 300 },
    { x: 180, y: 400 },
    { x: 200, y: 300 },
    { x: 220, y: 200 },
  ],
  [ // Route 4 - Circuit central
    { x: 350, y: 250 },
    { x: 500, y: 280 },
    { x: 1550, y: 350 },
    { x: 400, y: 380 },
    { x: 250, y: 350 },
    { x: 300, y: 280 },
  ],
  [ // Route 5 - Zigzag
    { x: 150, y: 300 },
    { x: 350, y: 1320 },
    { x: 250, y: 400 },
    { x: 450, y: 380 },
    { x: 1350, y: 450 },
    { x: 250, y: 350 },
  ],
  [ // Route 6 - Diagonale inverse
    { x: 1600, y: 150 },
    { x: 1500, y: 800 },
    { x: 400, y: 250 },
    { x: 300, y: 300 },
    { x: 400, y: 350 },
    { x: 500, y: 300 },
  ],
];

// Calcul de la direction selon le déplacement
const getDirection = (fromX: number, fromY: number, toX: number, toY: number): string => {
  const dx = toX - fromX;
  const dy = toY - fromY;
  const angle = Math.atan2(dy, dx) * (180 / Math.PI);
  
  // Convertir l'angle en direction (8 directions)
  if (angle >= -22.5 && angle < 22.5) return 'E';
  if (angle >= 22.5 && angle < 67.5) return 'SE';
  if (angle >= 67.5 && angle < 112.5) return 'S';
  if (angle >= 112.5 && angle < 157.5) return 'SW';
  if (angle >= 157.5 || angle < -157.5) return 'W';
  if (angle >= -157.5 && angle < -112.5) return 'NW';
  if (angle >= -112.5 && angle < -67.5) return 'N';
  if (angle >= -67.5 && angle < -22.5) return 'NE';
  return 'S';
};

const AnimatedCitizen: React.FC<AnimatedCitizenProps> = ({ citizenId, cityLayout }) => {
  const waypoints = WAYPOINTS_ROUTES[(citizenId - 1) % WAYPOINTS_ROUTES.length];
  const initialWaypointIndex = 0;
  
  const [position, setPosition] = useState(waypoints[initialWaypointIndex]);
  const [targetPosition, setTargetPosition] = useState(waypoints[1]);
  const [direction, setDirection] = useState('S');
  const [frame, setFrame] = useState(0);
  const [waypointIndex, setWaypointIndex] = useState(initialWaypointIndex);

  const totalFrames = 10;
  const moveSpeed = 2; // pixels par frame

  // Animation des frames
  useEffect(() => {
    const frameInterval = setInterval(() => {
      setFrame((prev) => (prev + 1) % totalFrames);
    }, 100);
    return () => clearInterval(frameInterval);
  }, [totalFrames]);

  // Déplacement progressif du personnage
  useEffect(() => {
    const moveInterval = setInterval(() => {
      setPosition((currentPos) => {
        const dx = targetPosition.x - currentPos.x;
        const dy = targetPosition.y - currentPos.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < moveSpeed) {
          // Atteint la cible, passer au waypoint suivant
          const nextWaypointIndex = (waypointIndex + 1) % waypoints.length;
          const nextWaypoint = waypoints[nextWaypointIndex];
          
          const newDirection = getDirection(
            currentPos.x,
            currentPos.y,
            nextWaypoint.x,
            nextWaypoint.y
          );
          
          setDirection(newDirection);
          setTargetPosition(nextWaypoint);
          setWaypointIndex(nextWaypointIndex);
          
          return currentPos;
        }

        // Se déplacer progressivement vers la cible
        const ratio = moveSpeed / distance;
        return {
          x: currentPos.x + dx * ratio,
          y: currentPos.y + dy * ratio,
        };
      });
    }, 50); // 20 FPS pour le mouvement
    return () => clearInterval(moveInterval);
  }, [targetPosition, waypointIndex, waypoints]);

  // Configuration du sprite
  const frameWidth = 191;
  const frameHeight = 123;
  const displayWidth = Math.floor(frameWidth / 4);
  const displayHeight = Math.floor(frameHeight / 4);
  const spriteX = -frame * frameWidth;

  return (
    <div
      className={styles.citizen}
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        width: `${displayWidth}px`,
        height: `${displayHeight}px`,
      }}
    >
      <div
        className={styles.sprite}
        style={{
          backgroundImage: `url(/assets/city/elements/citizen_1/${direction}.png)`,
          backgroundPosition: `${spriteX / 4}px 0`,
          backgroundSize: `${1910 / 4}px ${123 / 4}px`,
          width: `${displayWidth}px`,
          height: `${displayHeight}px`,
        }}
      />
    </div>
  );
};

export default AnimatedCitizen;
