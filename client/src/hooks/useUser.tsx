import React, { createContext, useContext, useState, useEffect } from "react";
import { getApiUrl } from '../utils/api';


export type UserState = {
  id: string | null;
  username: string | null;
  cities: Array<string>;
  research_points?: number;
  // Ajoute ici d'autres propriétés utiles (islands, ressources, etc.)
};

const defaultUser: UserState = {
  id: null,
  username: null,
  cities: [],
};

// Clés pour localStorage
const STORAGE_KEY = 'master_of_islands_user_session';

const UserContext = createContext<{
  user: UserState;
  setUser: React.Dispatch<React.SetStateAction<UserState>>;
  syncFromServer: () => Promise<void>;
  logout: () => void;
  isInitialized: boolean;
}>({ 
  user: defaultUser, 
  setUser: () => {}, 
  syncFromServer: async () => {}, 
  logout: () => {},
  isInitialized: false
});

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserState>(defaultUser);
  const [isInitialized, setIsInitialized] = useState(false);

  // Sauvegarde automatique dans localStorage à chaque changement d'utilisateur
  useEffect(() => {
    if (isInitialized && user.id) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
    }
  }, [user, isInitialized]);

  // Restauration automatique depuis localStorage au démarrage
  useEffect(() => {
    const restoreUserSession = async () => {
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          const storedUser: UserState = JSON.parse(stored);
          if (storedUser.id) {
            // Valider la session avec le serveur en vérifiant si le joueur existe dans savegame
            const response = await fetch(`${getApiUrl()}/api/universe`);
            
            if (response.ok) {
              const universeData = await response.json();
              // Vérifier si l'utilisateur existe toujours dans les villes
              const cities = universeData.cities || [];
              const userExists = cities.some((city: any) => city.owner === storedUser.id);
              
              if (userExists) {
                // Restaurer l'utilisateur avec ses données stockées
                setUser(storedUser);
              } else {
                // Utilisateur n'existe plus, mais garder la session si c'est un nouveau joueur
                // (il n'a peut-être pas encore de ville)
                setUser(storedUser);
              }
            } else {
              // Serveur inaccessible, restaurer quand même la session locale
              setUser(storedUser);
            }
          }
        }
      } catch (error) {
        // En cas d'erreur réseau, restaurer quand même la session locale
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          try {
            const storedUser: UserState = JSON.parse(stored);
            if (storedUser.id) {
              setUser(storedUser);
            }
          } catch (parseError) {
            localStorage.removeItem(STORAGE_KEY);
          }
        }
      } finally {
        setIsInitialized(true);
      }
    };

    restoreUserSession();
  }, []);

  // Synchronise l'état utilisateur depuis le serveur (inspiré de sync_from_server Kivy)
  const syncFromServer = async () => {
    if (!user.id) return;
    try {
      const response = await fetch(`${getApiUrl()}/player/${user.id}`);
      if (!response.ok) throw new Error("Erreur de synchronisation");
      const data = await response.json();
      setUser((prev) => ({ ...prev, ...data }));
    } catch (e) {
      // Optionnel : gestion d'erreur globale
    }
  };

  // Fonction de déconnexion propre
  const logout = () => {
    localStorage.removeItem(STORAGE_KEY);
    setUser(defaultUser);
  };

  return (
    <UserContext.Provider value={{ user, setUser, syncFromServer, logout, isInitialized }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => useContext(UserContext);
