import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import '../styles/UnitTransportPopup.css';
import { getApiUrl } from '../utils/api';

// ===== TYPES =====
interface UnitStats {
  name?: string;
  attack: number;
  defense: number;
  health: number;
  attack_melee?: number;
  defense_melee?: number;
  hp?: number;
  movement: number;
  cost?: { [resource: string]: number };
}

interface HeroData {
  hero_id: string;
  instance_id: string;
  current_level: number;
  name?: string;
  status?: string;
  owner?: string;
  is_available?: boolean;
  calculated_stats?: {
    hp: number;
    attack_melee: number;
    defense_melee: number;
    defense_ranged: number;
    movement: number;
    range: number;
  };
  calculated_bonuses?: {
    offensive_bonus: number;
    defensive_bonus: number;
    movement_bonus: number;
    moral_bonus: number;
    aura_radius: number;
  };
}

interface City {
  id: string;
  name: string;
  owner: string;
  x: number;
  y: number;
}

interface UnitTransportPopupProps {
  isOpen: boolean;
  onClose: () => void;
  sourceCity: City;
  destinationCity: City;
  transportType?: 'movement' | 'attack' | 'reinforcement';
  onTransportStart?: (transportData: any) => void;
}

// ===== COMPOSANT PRINCIPAL =====
const UnitTransportPopup: React.FC<UnitTransportPopupProps> = ({
  isOpen,
  onClose,
  sourceCity,
  destinationCity,
  transportType = 'movement',
  onTransportStart
}) => {
  
  // ===== ÉTATS =====
  const [selectedUnits, setSelectedUnits] = useState<{ [unitType: string]: number }>({});
  const [availableUnits, setAvailableUnits] = useState<{ [unitType: string]: number }>({});
  const [unitStats, setUnitStats] = useState<{ [unitType: string]: UnitStats }>({});
  const [selectedHeroes, setSelectedHeroes] = useState<{ [heroId: string]: boolean }>({});
  const [availableHeroes, setAvailableHeroes] = useState<{ [heroId: string]: HeroData }>({});
  const [ships, setShips] = useState(1);
  const [estimatedTime, setEstimatedTime] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [isTransporting, setIsTransporting] = useState(false); // Protection double-clic
  
  const isMobile = window.innerWidth <= 768;

  // Prévention du scroll derrière le popup
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = 'unset';
      };
    }
  }, [isOpen]);

  // Charger les données au montage et quand les villes changent
  useEffect(() => {
    if (isOpen && sourceCity) {
      // Réinitialiser les états
      setSelectedUnits({});
      setSelectedHeroes({});
      setAvailableUnits({});
      setAvailableHeroes({});
      setShips(1);
      setEstimatedTime('');
      
      // Charger les données
      setLoading(true);
      Promise.all([
        loadUnitsData(),
        loadUnitStats(),
        loadHeroesData()
      ]).finally(() => {
        setLoading(false);
      });
    }
  }, [isOpen, sourceCity]);

  // Calculer les bateaux nécessaires et le temps de voyage
  useEffect(() => {
    if (!loading && (Object.keys(selectedUnits).length > 0 || Object.keys(selectedHeroes).some(h => selectedHeroes[h]))) {
      calculateTransportParams();
    } else {
      setShips(1);
      setEstimatedTime('');
    }
  }, [selectedUnits, selectedHeroes, loading]);

  // ===== FONCTIONS DE CHARGEMENT (INSPIRÉES D'ATTACKPOPUPV3) =====
  const loadUnitsData = async () => {
    try {
      if (!sourceCity?.id) {
        console.error('🏰 [UnitTransport] ERREUR: Pas d\'ID de ville source!');
        setAvailableUnits({});
        return;
      }
      
      console.log('🏰 [UnitTransport] Chargement unités pour ville:', sourceCity.id);
      const response = await fetch(`${getApiUrl()}/api/military/city/units/${sourceCity.id}`);
      
      if (response.ok) {
        const unitsData = await response.json();
        console.log('🏰 [UnitTransport] Réponse unités complète:', unitsData);
        
        if (unitsData.success && unitsData.garrison) {
          const garrison = unitsData.garrison;
          const availableUnitsMap: { [unitType: string]: number } = {};
          
          // COPIE EXACTE DU CODE AttackPopupV3 QUI MARCHE
          for (const [unitType, unitData] of Object.entries(garrison)) {
            if (typeof unitData === 'number') {
              availableUnitsMap[unitType] = unitData;
            }
            else if (unitData && typeof unitData === 'object' && 'quantity' in unitData) {
              availableUnitsMap[unitType] = (unitData as any).quantity || 0;
            }
          }
          
          console.log('✅ [UnitTransport] Unités extraites:', availableUnitsMap);
          setAvailableUnits(availableUnitsMap);
        } else {
          console.warn('⚠️ [UnitTransport] Pas de garrison dans la réponse:', unitsData);
          setAvailableUnits({});
        }
      } else {
        const errorText = await response.text();
        console.error('❌ [UnitTransport] Erreur HTTP unités:', response.status, response.statusText, errorText);
        setAvailableUnits({});
      }
    } catch (error) {
      console.error('❌ [UnitTransport] Erreur chargement unités:', error);
      setAvailableUnits({});
    }
  };

  const loadUnitStats = async () => {
    try {
      const statsResponse = await fetch(`${getApiUrl()}/api/v2/unit_stats`);
      if (statsResponse.ok) {
        const allStatsData = await statsResponse.json();
        const allUnitsStats = {
          ...(allStatsData.stone_age || {}),
          ...(allStatsData.classical_age || {}),
          ...(allStatsData.medieval_age || {}),
          ...(allStatsData.renaissance_age || {}),
          ...(allStatsData.napoleonic_age || {}),
          ...(allStatsData.enemy_units || {})
        };
        setUnitStats(allUnitsStats);
        console.log('✅ [UnitTransport] Stats unités chargées:', Object.keys(allUnitsStats));
      }
    } catch (error) {
      console.error('❌ [UnitTransport] Erreur chargement stats unités:', error);
    }
  };

  const loadHeroesData = async () => {
    try {
      // 1. Récupérer les héros en garnison depuis l'API
      const response = await fetch(`${getApiUrl()}/api/military/city/heroes/${sourceCity.id}`);
      
      if (response.ok) {
        const heroesData = await response.json();
        console.log('🦸‍♂️ [UnitTransport] Réponse héros complète:', heroesData);
        
        if (heroesData.success && heroesData.heroes) {
          const heroesMap: { [heroId: string]: HeroData } = {};
          
          // Convertir la liste en map pour faciliter l'accès
          heroesData.heroes.forEach((hero: HeroData) => {
            if (hero.is_available) {
              heroesMap[hero.instance_id] = hero;
            }
          });
          
          console.log('✅ [UnitTransport] Héros disponibles:', heroesMap);
          setAvailableHeroes(heroesMap);
        } else {
          console.warn('⚠️ [UnitTransport] Pas de héros dans la réponse:', heroesData);
          setAvailableHeroes({});
        }
      } else {
        const errorText = await response.text();
        console.error('❌ [UnitTransport] Erreur HTTP héros:', response.status, response.statusText, errorText);
        setAvailableHeroes({});
      }
    } catch (error) {
      console.error('❌ [UnitTransport] Erreur chargement héros:', error);
      setAvailableHeroes({});
    }
  };

  const calculateTransportParams = async () => {
    try {
      const totalUnits = Object.values(selectedUnits).reduce((sum, count) => sum + count, 0);
      const totalHeroes = Object.values(selectedHeroes).filter(Boolean).length;
      
      if (totalUnits === 0 && totalHeroes === 0) {
        setShips(1);
        setEstimatedTime('');
        return;
      }

      // Calculer le poids total (approximatif)
      let totalWeight = 0;
      Object.entries(selectedUnits).forEach(([unitType, count]) => {
        const unitWeight = getUnitWeight(unitType);
        totalWeight += unitWeight * count;
      });
      totalWeight += totalHeroes; // 1 poids par héros

      // Calculer bateaux nécessaires (capacité par bateau: 50)
      const shipCapacity = 50;
      const shipsNeeded = Math.max(1, Math.ceil(totalWeight / shipCapacity));
      setShips(shipsNeeded);

      // Estimer le temps de voyage (basé sur l'unité la plus lente)
      const slowestSpeed = getSlowestUnitSpeed();
      const distance = calculateDistance(sourceCity, destinationCity);
      const travelTimeMinutes = Math.max(1, Math.ceil(distance / slowestSpeed));
      
      setEstimatedTime(`~${travelTimeMinutes} min`);
      
    } catch (error) {
      console.error('❌ Erreur calcul paramètres transport:', error);
    }
  };

  const getUnitWeight = (unitType: string): number => {
    const weights: { [key: string]: number } = {
      'archer': 1,
      'spearman': 2,
      'swordsman': 2,
      'cavalry': 3,
      'catapult': 5
    };
    return weights[unitType] || 2;
  };

  const getSlowestUnitSpeed = (): number => {
    let slowestSpeed = 5; // Vitesse par défaut
    
    Object.entries(selectedUnits).forEach(([unitType, count]) => {
      if (count > 0) {
        const unitStat = unitStats[unitType];
        const speed = unitStat?.movement || 3;
        if (speed < slowestSpeed) {
          slowestSpeed = speed;
        }
      }
    });
    
    return slowestSpeed;
  };

  const calculateDistance = (city1: City, city2: City): number => {
    const dx = city2.x - city1.x;
    const dy = city2.y - city1.y;
    return Math.sqrt(dx * dx + dy * dy);
  };

  const handleUnitChange = (unitType: string, value: number) => {
    const maxAvailable = availableUnits[unitType] || 0;
    const newValue = Math.max(0, Math.min(value, maxAvailable));
    
    setSelectedUnits(prev => ({
      ...prev,
      [unitType]: newValue
    }));
  };

  const handleHeroToggle = (heroId: string) => {
    setSelectedHeroes(prev => ({
      ...prev,
      [heroId]: !prev[heroId]
    }));
  };

  const handleTransport = async () => {
    if (isTransporting) return;
    
    const totalUnits = Object.values(selectedUnits).reduce((sum, count) => sum + count, 0);
    const selectedHeroIds = Object.entries(selectedHeroes)
      .filter(([_, selected]) => selected)
      .map(([heroId, _]) => heroId);
    
    if (totalUnits === 0 && selectedHeroIds.length === 0) {
      alert('Veuillez sélectionner au moins une unité ou un héros à transporter.');
      return;
    }

    setIsTransporting(true);
    
    try {
      // Filtrer les unités avec quantité > 0
      const unitsToTransport = Object.fromEntries(
        Object.entries(selectedUnits).filter(([_, count]) => count > 0)
      );

      const transportData = {
        player_id: sourceCity.owner,
        source_city: sourceCity.id,
        destination_city: destinationCity.id,
        units: unitsToTransport,
        heroes: selectedHeroIds,
        type: transportType
      };

      const response = await fetch('/api/unit-transports', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(transportData),
      });

      const result = await response.json();

      if (result.success) {
        console.log('✅ Transport d\'unités créé:', result);
        
        // Callback personnalisé si fourni
        if (onTransportStart) {
          onTransportStart(result);
        }
        
        // Fermer le popup
        onClose();
        
        // Message de confirmation
        alert(`Transport d'unités créé avec succès ! ID: ${result.transport_id}`);
        
      } else {
        console.error('❌ Erreur création transport:', result.error);
        alert(`Erreur: ${result.error}`);
      }
      
    } catch (error) {
      console.error('❌ Erreur requête transport:', error);
      alert('Erreur lors de la création du transport. Vérifiez la connexion.');
    } finally {
      setIsTransporting(false);
    }
  };

  const getTransportTypeLabel = () => {
    switch (transportType) {
      case 'attack': return 'Attaque';
      case 'reinforcement': return 'Renfort';
      case 'movement': 
      default: return 'Déplacement';
    }
  };

  const getTransportTypeDescription = () => {
    switch (transportType) {
      case 'attack': return 'Les unités attaqueront la ville cible puis reviendront automatiquement.';
      case 'reinforcement': return 'Les unités rejoindront une bataille en cours.';
      case 'movement': 
      default: return 'Les unités seront déplacées définitivement vers la ville de destination.';
    }
  };

  // ===== RENDU =====
  if (!isOpen) return null;

  const content = (
    <div className="unit-transport-popup-overlay" onClick={onClose}>
      <div className="unit-transport-popup-content" onClick={e => e.stopPropagation()}>
        
        {/* En-tête */}
        <div className="unit-transport-popup-header">
          <h2>Transport d'unités - {getTransportTypeLabel()}</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        {/* Informations du transport */}
        <div className="transport-info">
          <div className="route-info">
            <span className="city-name">{sourceCity.name}</span>
            <span className="arrow"> → </span>
            <span className="city-name">{destinationCity.name}</span>
          </div>
          <div className="transport-description">
            {getTransportTypeDescription()}
          </div>
        </div>

        {/* Contenu principal */}
        <div className="unit-transport-popup-body">
          {loading ? (
            <div className="loading">Chargement des données...</div>
          ) : (
            <>
              {/* Section Unités */}
              <div className="units-section">
                <h3>Unités disponibles</h3>
                <div className="units-grid">
                  {Object.keys(availableUnits).length === 0 ? (
                    <div style={{padding: '20px', textAlign: 'center', color: '#999'}}>
                      Aucune unité disponible dans cette ville
                    </div>
                  ) : (
                    Object.entries(availableUnits).map(([unitType, available]) => (
                      <div key={unitType} className="unit-selector">
                        <div className="unit-info">
                          <span className="unit-name">{unitStats[unitType]?.name || unitType}</span>
                          <span className="unit-available">({available} disponibles)</span>
                        </div>
                      <div className="unit-controls">
                        <button 
                          onClick={() => handleUnitChange(unitType, (selectedUnits[unitType] || 0) - 1)}
                          disabled={!selectedUnits[unitType]}
                        >
                          -
                        </button>
                        <input
                          type="number"
                          min="0"
                          max={available}
                          value={selectedUnits[unitType] || 0}
                          onChange={(e) => handleUnitChange(unitType, parseInt(e.target.value) || 0)}
                        />
                        <button 
                          onClick={() => handleUnitChange(unitType, (selectedUnits[unitType] || 0) + 1)}
                          disabled={(selectedUnits[unitType] || 0) >= available}
                        >
                          +
                        </button>
                      </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Section Héros */}
              {Object.keys(availableHeroes).length > 0 && (
                <div className="heroes-section">
                  <h3>Héros disponibles</h3>
                  <div className="heroes-grid">
                    {Object.entries(availableHeroes).map(([heroId, hero]) => (
                      <div key={heroId} className="hero-selector">
                        <label>
                          <input
                            type="checkbox"
                            checked={selectedHeroes[heroId] || false}
                            onChange={() => handleHeroToggle(heroId)}
                          />
                          <span className="hero-name">
                            {hero.name || hero.hero_id} (Niv. {hero.current_level})
                          </span>
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Résumé du transport */}
              <div className="transport-summary">
                <h3>Résumé du transport</h3>
                <div className="summary-info">
                  <div className="summary-item">
                    <span>Bateaux nécessaires:</span>
                    <span>{ships}</span>
                  </div>
                  <div className="summary-item">
                    <span>Temps estimé:</span>
                    <span>{estimatedTime || 'Non calculé'}</span>
                  </div>
                  <div className="summary-item">
                    <span>Unités sélectionnées:</span>
                    <span>{Object.values(selectedUnits).reduce((sum, count) => sum + count, 0)}</span>
                  </div>
                  <div className="summary-item">
                    <span>Héros sélectionnés:</span>
                    <span>{Object.values(selectedHeroes).filter(Boolean).length}</span>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Pied de page */}
        <div className="unit-transport-popup-footer">
          <button className="cancel-button" onClick={onClose}>
            Annuler
          </button>
          <button 
            className="transport-button"
            onClick={handleTransport}
            disabled={loading || isTransporting || 
              (Object.values(selectedUnits).reduce((sum, count) => sum + count, 0) === 0 &&
               Object.values(selectedHeroes).filter(Boolean).length === 0)}
          >
            {isTransporting ? 'Transport en cours...' : `Lancer le ${getTransportTypeLabel().toLowerCase()}`}
          </button>
        </div>
        
      </div>
    </div>
  );

  return createPortal(content, document.body);
};

export default UnitTransportPopup;