// Hook custom pour gérer l'état global de la ville
import { useState, useEffect, useCallback } from 'react';
import { City } from '../../types';
import { CityService } from '../../services/CityService';

interface UseCityOptions {
  cityId: string | undefined;
}

export const useCity = ({ cityId }: UseCityOptions) => {
  const [city, setCity] = useState<City | null>(null);
  const [layout, setLayout] = useState<any>(null);
  const [allBuildingsData, setAllBuildingsData] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fonction pour recharger les données de la ville
  const reloadCityData = useCallback(async (): Promise<any> => {
    if (!cityId) return null;
    
    try {
      const cityData = await CityService.getCityState(cityId);
      setCity(cityData);
      return cityData; // RETOURNER cityData !
    } catch (err: any) {
      console.error("Erreur rechargement ville:", err);
      setError("Erreur de rechargement de la ville : " + err.message);
      throw err;
    }
  }, [cityId]);

  // Chargement initial
  useEffect(() => {
    if (!cityId) return;
    
    setLoading(true);
    setError(null);
    
    const loadInitialData = async () => {
      try {
        const [cityData, universeData] = await Promise.all([
          CityService.getCityState(cityId),
          CityService.getUniverseData()
        ]);
        
        setCity(cityData);
        
        const layoutId = cityData.city_layout || cityData.layout;
        if (layoutId) {
          const cityLayout = universeData.city_layouts[layoutId];
          setLayout(cityLayout);
        }
        setAllBuildingsData(universeData.buildings || {});
        
      } catch (err: any) {
        setError("Erreur de chargement de la ville : " + err.message);
      } finally {
        setLoading(false);
      }
    };
    
    loadInitialData();
  }, [cityId]);

  // Vérification périodique des bâtiments terminés
  useEffect(() => {
    if (!cityId) return;

    const checkBuildingsCompletion = async () => {
      try {
        // Recharger les données de la ville pour vérifier les bâtiments terminés
        await reloadCityData();
      } catch (err) {
        console.error("Erreur lors de la vérification des bâtiments:", err);
      }
    };

    // Vérifier toutes les 60 secondes (réduit de 30s pour performance)
    const interval = setInterval(checkBuildingsCompletion, 60000);

    return () => clearInterval(interval);
  }, [cityId, reloadCityData]);

  // Fonctions utilitaires
  const updateCity = useCallback((updater: (city: City) => City) => {
    setCity(prevCity => prevCity ? updater(prevCity) : null);
  }, []);

  const renameTownHall = useCallback(async (newName: string) => {
    if (!city) return;
    
    const updated = await CityService.renameTownHall(city.id, newName);
    updateCity(c => ({ ...c, name: updated.name }));
    
    // Déclencher un événement global pour mettre à jour le HeaderBar
    window.dispatchEvent(new CustomEvent('cityRenamed', { 
      detail: { 
        cityId: city.id, 
        newName: updated.name 
      } 
    }));
  }, [city, updateCity]);

  return {
    city,
    layout,
    allBuildingsData,
    loading,
    error,
    reloadCityData,
    updateCity,
    renameTownHall
  };
};
