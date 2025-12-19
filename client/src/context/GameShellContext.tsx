import React, { createContext, useContext, useState } from 'react';

interface GameShellContextType {
  // Ville active
  activeCityId: string;
  setActiveCityId: (id: string) => void;
  currentActiveCity: any;
  setCurrentActiveCity: (city: any) => void;
  
  // Ressources de la ville
  cityResources: { [key: string]: number };
  setCityResources: (resources: { [key: string]: number }) => void;
  
  // Informations de la ville
  cityName: string;
  setCityName: (name: string) => void;
  
  // Île active
  activeIslandId: string;
  setActiveIslandId: (id: string) => void;
  
  // Ressources globales
  globalResources: { [key: string]: number };
  setGlobalResources: (resources: { [key: string]: number }) => void;
  
  // Autres états
  goldProductionRate: number;
  setGoldProductionRate: (rate: number) => void;
  
  playerInfo: any;
  setPlayerInfo: (info: any) => void;
  
  userCities: Array<{id: string, name: string}>;
  setUserCities: (cities: Array<{id: string, name: string}>) => void;
  
  activeTransportsCount: number;
  setActiveTransportsCount: (count: number) => void;
}

const GameShellContext = createContext<GameShellContextType | undefined>(undefined);

export const useGameShell = () => {
  const context = useContext(GameShellContext);
  if (!context) {
    throw new Error('useGameShell must be used within a GameShellProvider');
  }
  return context;
};

export const GameShellProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeCityId, setActiveCityId] = useState<string>("");
  const [currentActiveCity, setCurrentActiveCity] = useState<any>(null);
  const [cityResources, setCityResources] = useState<{ [key: string]: number }>({});
  const [cityName, setCityName] = useState<string>("");
  const [activeIslandId, setActiveIslandId] = useState<string>("");
  const [globalResources, setGlobalResources] = useState<{ [key: string]: number }>({});
  const [goldProductionRate, setGoldProductionRate] = useState<number>(0);
  const [playerInfo, setPlayerInfo] = useState<any>({
    transport_ships_total: 0,
    transport_ships_available: 0
  });
  const [userCities, setUserCities] = useState<Array<{id: string, name: string}>>([]);
  const [activeTransportsCount, setActiveTransportsCount] = useState<number>(0);

  const value = {
    activeCityId,
    setActiveCityId,
    currentActiveCity,
    setCurrentActiveCity,
    cityResources,
    setCityResources,
    cityName,
    setCityName,
    activeIslandId,
    setActiveIslandId,
    globalResources,
    setGlobalResources,
    goldProductionRate,
    setGoldProductionRate,
    playerInfo,
    setPlayerInfo,
    userCities,
    setUserCities,
    activeTransportsCount,
    setActiveTransportsCount
  };

  return (
    <GameShellContext.Provider value={value}>
      {children}
    </GameShellContext.Provider>
  );
};