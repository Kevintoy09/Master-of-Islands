/**
 * Contexte de verrouillage des tours
 * Empêche de contrôler les unités ennemies quand activé
 */

import React, { createContext, useContext, useState, useCallback } from 'react';

interface TurnLockContextType {
  isLocked: boolean;
  toggleLock: () => void;
  canControlUnit: (unitOwner: string, currentPlayer: string) => boolean;
}

const TurnLockContext = createContext<TurnLockContextType | undefined>(undefined);

export const TurnLockProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isLocked, setIsLocked] = useState<boolean>(false);

  const toggleLock = useCallback(() => {
    setIsLocked(prev => !prev);
  }, []);

  const canControlUnit = useCallback((unitOwner: string, currentPlayer: string) => {
    // Si déverrouillé, tout est autorisé
    if (!isLocked) return true;
    
    // Si verrouillé, vérifier que c'est bien l'unité du joueur actuel
    return unitOwner === currentPlayer;
  }, [isLocked]);

  return (
    <TurnLockContext.Provider value={{ isLocked, toggleLock, canControlUnit }}>
      {children}
    </TurnLockContext.Provider>
  );
};

export const useTurnLock = () => {
  const context = useContext(TurnLockContext);
  if (!context) {
    throw new Error('useTurnLock must be used within TurnLockProvider');
  }
  return context;
};
