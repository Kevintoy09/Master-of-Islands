import React, { useState, useEffect } from 'react';
import '../styles/BarracksPopupContent.css';
import { formatTime } from '../utils/timeUtils';
import HeroDetailPopup from './HeroDetailPopup';
import UnitDetailPopup from './UnitDetailPopup';
import { useUser } from '../hooks/useUser';

interface UnitStats {
  name: string;
  category: string;
  hp: number;
  attack_melee: number;
  defense_melee: number;
  attack_ranged: number;
  defense_ranged: number;
  range: number;
  movement: number;
  weight: number;
  food_consumption: number;
  gold_cost_per_hour: number;
  max_stack_size: number;
  production_cost: {
    wood?: number;
    stone?: number;
    iron?: number;
    horse?: number;
    population?: number;
  };
  production_time: number;
  required_barracks_level: number;
  required_research: string | null;
  special_abilities: string[];
  era?: string;
  ai_controlled?: boolean;
  description?: string;
}

interface ProductionQueueItem {
  // Ancienne méthode (une seule unité)
  unit_type?: string;
  quantity?: number;
  // Nouvelle méthode batch (plusieurs unités)
  is_batch?: boolean;
  units?: Array<{
    type: string;
    name: string;
    quantity: number;
  }>;
  // Commun aux deux méthodes
  remaining_time: number;
  total_time: number;
}

interface City {
  id: string;
  name: string;
  resources?: Record<string, number>;
  researches?: string[];
}

interface CityBuilding {
  name: string;
  level: number;
}

interface BarracksPopupContentProps {
  city: City;
  building: CityBuilding;
  onClose: () => void;
  onCityDataChange?: () => void;
  defaultTab?: 'production' | 'garrison';
}

const BarracksPopupContent: React.FC<BarracksPopupContentProps> = ({
  city,
  building,
  onClose,
  onCityDataChange,
  defaultTab = 'production'
}) => {
  const { user, syncFromServer } = useUser();
  const [unitStats, setUnitStats] = useState<Record<string, UnitStats>>({});
  const [productionQueue, setProductionQueue] = useState<ProductionQueueItem[]>([]);
  const [selectedQuantities, setSelectedQuantities] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'production' | 'garrison'>(defaultTab);
  const [garrison, setGarrison] = useState<Record<string, number>>({});
  const [heroes, setHeroes] = useState<Record<string, any>>({});
  const [selectedHero, setSelectedHero] = useState<any>(null);
  const [showHeroDetail, setShowHeroDetail] = useState(false);
  const [selectedUnit, setSelectedUnit] = useState<{type: string, stats: UnitStats} | null>(null);
  const [showUnitDetail, setShowUnitDetail] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState<number>(0);
  const [returningHero, setReturningHero] = useState<string | null>(null);
  const [factionBonuses, setFactionBonuses] = useState<any>(null);

  // Synchroniser les données du joueur (recherches) au montage
  useEffect(() => {
    if (user?.id) {
      syncFromServer();
      fetchFactionBonuses();
    }
  }, []);

  const fetchFactionBonuses = async () => {
    if (!user?.id) return;
    try {
      const response = await fetch(`/api/game/faction-bonuses?player_id=${user.id}`);
      const data = await response.json();
      if (response.ok) {
        setFactionBonuses(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des bonus de faction:', error);
    }
  };

  useEffect(() => {
    fetchUnitStats();
    fetchProductionQueue();
    fetchGarrison();
    fetchHeroes();
    
    // Polling de la queue toutes les 2 secondes
    const queueInterval = setInterval(() => {
      fetchProductionQueue();
      fetchGarrison();
    }, 2000);
    
    return () => clearInterval(queueInterval);
  }, [city.id]);

  // Timer local qui décrémente chaque seconde
  useEffect(() => {
    if (timeRemaining > 0 && loading) {
      const timer = window.setInterval(() => {
        setTimeRemaining(prev => (prev <= 1 ? 0 : prev - 1));
      }, 1000);
      
      return () => clearInterval(timer);
    }
  }, [timeRemaining, loading]);

  const fetchUnitStats = async () => {
    try {
      const response = await fetch('/api/military/unit-stats');
      const data = await response.json();
      setUnitStats(data);
    } catch (error) {
      console.error('Erreur lors du chargement des stats d\'unités:', error);
    }
  };

  const fetchProductionQueue = async () => {
    try {
      const response = await fetch(`/api/military/production/queue/${city.id}`);
      const data = await response.json();
      
      if (data.success) {
        setProductionQueue(data.queue || []);
        
        if (data.queue && data.queue.length > 0) {
          const firstItem = data.queue[0];
          if (firstItem.remaining_time > 0) {
            setTimeRemaining(prev => {
              const diff = Math.abs(prev - firstItem.remaining_time);
              return (prev === 0 || diff > 3) ? firstItem.remaining_time : prev;
            });
            setLoading(true);
            
            // Restaurer les quantités sélectionnées si c'est un batch
            if (firstItem.is_batch && firstItem.units && Object.keys(selectedQuantities).length === 0) {
              const restored: Record<string, number> = {};
              firstItem.units.forEach((u: any) => {
                restored[u.type] = u.quantity;
              });
              setSelectedQuantities(restored);
            } else if (firstItem.unit_type && Object.keys(selectedQuantities).length === 0) {
              // Ancienne méthode : une seule unité
              setSelectedQuantities({ [firstItem.unit_type]: firstItem.quantity || 0 });
            }
          }
        } else if (loading) {
          setTimeRemaining(0);
          setLoading(false);
          setSelectedQuantities({});
        }
      }
    } catch (error) {
      console.error('Erreur lors du chargement de la file de production:', error);
    }
  };

  const fetchGarrison = async () => {
    try {
      const endpoint = `/api/military/city/units/${city.id}`;
      
      const response = await fetch(endpoint);
      
      const data = await response.json();
      
      if (data.success) {
        const garrisonData = data.garrison || {};
        setGarrison(garrisonData);
      }
    } catch (error) {
      // Erreur silencieuse - UI garde l'état précédent
    }
  };

  const fetchHeroes = async () => {
    try {
      const endpoint = `/api/military/city/heroes/${city.id}`;
      
      const response = await fetch(endpoint);
      
      const data = await response.json();
      
      if (data.success) {
        const heroesData = data.heroes || {};
        setHeroes(heroesData);
      }
    } catch (error) {
      setHeroes({});
    }
  };

  const getAvailableUnits = () => {
    // Afficher toutes les unités sans filtrage par ère
    return Object.entries(unitStats)
      .filter(([_, unit]) => !unit.ai_controlled) // Exclure uniquement les unités ennemies (AI)
      .sort((a, b) => a[1].required_barracks_level - b[1].required_barracks_level);
  };

  const isUnitAvailable = (unit: UnitStats) => {
    // Vérifier le niveau de caserne
    if (building.level < unit.required_barracks_level) {
      return false;
    }
    // Vérifier la recherche requise (si elle existe)
    if (unit.required_research && unit.required_research !== null) {
      const playerResearches = user?.unlocked_research || [];
      if (!playerResearches.includes(unit.required_research)) {
        return false;
      }
    }
    return true;
  };

  const getRequirementMessage = (unit: UnitStats) => {
    const messages = [];
    if (building.level < unit.required_barracks_level) {
      messages.push(`niveau de construction ${unit.required_barracks_level}`);
    }
    if (unit.required_research && unit.required_research !== null) {
      const playerResearches = user?.unlocked_research || [];
      if (!playerResearches.includes(unit.required_research)) {
        const researchName = unit.required_research.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        messages.push(`la recherche ${researchName}`);
      }
    }
    return `Requiert ${messages.join(' et ')}`;
  };

  const calculateCost = (unit: UnitStats, quantity: number) => {
    let timeReduction = Math.min(0.55, (building.level - 1) * 0.05);
    const costReduction = Math.min(0.45, (building.level - 1) * 0.05);
    
    // Bonus de faction Fer : -10% sur le temps
    if (factionBonuses?.unit_production_time_reduction) {
      timeReduction += factionBonuses.unit_production_time_reduction / 100;
      timeReduction = Math.min(0.75, timeReduction); // Cap à 75%
    }
    
    const adjustedCost = {
      wood: Math.floor((unit.production_cost.wood || 0) * (1 - costReduction) * quantity),
      stone: Math.floor((unit.production_cost.stone || 0) * (1 - costReduction) * quantity),
      iron: Math.floor((unit.production_cost.iron || 0) * (1 - costReduction) * quantity),
      horse: Math.floor((unit.production_cost.horse || 0) * (1 - costReduction) * quantity),
      population: Math.floor((unit.production_cost.population || 0) * quantity)
    };
    
    const adjustedTime = Math.floor(unit.production_time * (1 - timeReduction) * quantity);
    
    return { cost: adjustedCost, time: adjustedTime };
  };

  const canAfford = (cost: any) => {
    const resources = city.resources || {};
    const availablePopulation = Math.floor(resources.population_free || 0);
    
    return (
      resources.wood >= (cost.wood || 0) &&
      resources.stone >= (cost.stone || 0) &&
      resources.iron >= (cost.iron || 0) &&
      resources.horse >= (cost.horse || 0) &&
      availablePopulation >= (cost.population || 0)
    );
  };

  const handleQuantityChange = (unitType: string, quantity: number) => {
    setSelectedQuantities(prev => ({
      ...prev,
      [unitType]: Math.max(0, quantity)
    }));
  };

  const startProduction = async (unitType: string) => {
    const quantity = selectedQuantities[unitType] || 1;
    const unit = unitStats[unitType];
    
    if (!unit) return;

    const { cost } = calculateCost(unit, quantity);
    
    if (!canAfford(cost)) {
      alert('Ressources insuffisantes !');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/military/production/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          city_id: city.id,
          unit_type: unitType,
          quantity: quantity
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setSelectedQuantities(prev => ({ ...prev, [unitType]: 0 }));
        fetchProductionQueue();
        
        fetchGarrison(); // Rafraîchir la garnison après production
        
        // Notifier le changement pour rafraîchir les données de la ville
        if (onCityDataChange) {
          onCityDataChange();
        }
        alert(`${quantity}x ${unit.name} produit(s) avec succès !`);
      } else {
        alert(data.message || 'Erreur lors du lancement de la production');
      }
    } catch (error) {
      alert('Erreur lors de la production');
    } finally {
      setLoading(false);
    }
  };

  const getCategoryIcon = (category: string, unitType?: string) => {
    // Utiliser les images PNG au lieu d'emojis
    if (unitType) {
      return (
        <img 
          src={`/assets/units/${unitType}.png`} 
          alt={unitType}
          onError={(e) => {
            // Fallback vers image par défaut si l'image n'existe pas
            (e.target as HTMLImageElement).src = '/assets/units/default.png';
          }}
          style={{ width: '100%', height: '100%', objectFit: 'contain' }}
        />
      );
    }
    // Fallback si pas de unitType
    return <img src="/assets/units/default.png" alt="unit" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />;
  };

  const getAvailablePopulation = () => {
    const resources = city.resources || {};
    // Utiliser population_free comme population disponible pour recruter des unités
    return Math.floor(resources.population_free || 0);
  };

  const isResourceAffordable = (resourceType: string, required: number) => {
    const resources = city.resources || {};
    
    switch (resourceType) {
      case 'population':
        return Math.floor(resources.population_free || 0) >= required;
      default:
        return (resources[resourceType] || 0) >= required;
    }
  };



  const calculateTotalSelection = () => {
    const totals = {
      wood: 0,
      stone: 0,
      iron: 0,
      horse: 0,
      population: 0,
      time: 0,
      units: [] as Array<{ type: string; name: string; quantity: number }>
    };

    Object.entries(selectedQuantities).forEach(([unitType, quantity]) => {
      if (quantity > 0) {
        const unit = unitStats[unitType];
        if (unit) {
          const { cost, time } = calculateCost(unit, quantity);
          totals.wood += cost.wood || 0;
          totals.stone += cost.stone || 0;
          totals.iron += cost.iron || 0;
          totals.horse += cost.horse || 0;
          totals.population += cost.population || 0;
          totals.time += time;
          totals.units.push({
            type: unitType,
            name: unit.name,
            quantity
          });
        }
      }
    });

    return totals;
  };

  const cancelProduction = async () => {
    if (window.confirm('Voulez-vous vraiment annuler la production en cours ? Les ressources ne seront pas recréditées.')) {
      try {
        const response = await fetch(`/api/military/production/cancel/${city.id}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        if (data.success) {
          setTimeRemaining(0);
          setLoading(false);
          setSelectedQuantities({});
          await fetchProductionQueue();
          fetchGarrison();
          if (onCityDataChange) {
            onCityDataChange();
          }
        } else {
          alert(`Erreur: ${data.message}`);
        }
      } catch (error) {
        alert('Erreur lors de l\'annulation de la production');
      }
    }
  };

  const startBatchProduction = async () => {
    const totalSelection = calculateTotalSelection();
    
    if (totalSelection.units.length === 0) {
      alert('Veuillez sélectionner au moins une unité à produire');
      return;
    }

    if (!canAfford({
      wood: totalSelection.wood,
      stone: totalSelection.stone,
      iron: totalSelection.iron,
      horse: totalSelection.horse,
      population: totalSelection.population
    })) {
      alert('Ressources insuffisantes pour cette production !');
      return;
    }

    setLoading(true);
    
    try {
      // Produire toutes les unités en une seule commande batch
      const response = await fetch('/api/military/production/start-batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          city_id: city.id,
          units: totalSelection.units.map(u => ({
            unit_type: u.type,
            quantity: u.quantity
          }))
        }),
      });

      const data = await response.json();
      if (!data.success) {
        alert(`Erreur: ${data.message}`);
        setLoading(false);
        return;
      }

      // NE PAS réinitialiser les quantités ici - on veut garder le résumé visible avec le timer
      // Les quantités seront réinitialisées quand la production sera terminée
      
      // Rafraîchir immédiatement la queue pour afficher le timer
      await fetchProductionQueue();
      fetchGarrison();
      
      if (onCityDataChange) {
        onCityDataChange();
      }
      
      // Pas d'alerte - le timer s'affichera automatiquement
    } catch (error) {
      alert('Erreur lors de la production');
      setLoading(false);
      setTimeRemaining(0);
    }
    // NE PAS mettre setLoading(false) ici - le polling le fera quand la production est terminée
  };

  const renderUnitCard = ([unitType, unit]: [string, UnitStats]) => {
    const quantity = selectedQuantities[unitType] || 0;
    const { cost, time } = calculateCost(unit, quantity > 0 ? quantity : 1);
    const available = isUnitAvailable(unit);
    const garrisonCount = garrison[unitType] || 0;

    return (
      <div key={unitType} className="ikariam-unit-row">
        {/* Colonne 1: Image + Effectif en garnison */}
        <div 
          className="unit-image-col" 
          onClick={() => {
            setSelectedUnit({ type: unitType, stats: unit });
            setShowUnitDetail(true);
          }}
          style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center' }}
        >
          <div className={`unit-icon-large ${unit.category}`}>
            {getCategoryIcon(unit.category, unitType)}
          </div>
          {/* Affichage de l'effectif en garnison */}
          {garrisonCount > 0 && (
            <div style={{
              fontSize: '14px',
              fontWeight: 'bold',
              color: '#666',
              marginTop: '1px',
              textAlign: 'center'
            }}>
              {garrisonCount}
            </div>
          )}
        </div>

        {/* Colonne 2: Nom + Coûts OU Message de prérequis */}
        <div className="unit-details-col">
          {/* Ligne 1: Nom */}
          <h4 className="unit-name-ikariam">{unit.name}</h4>
          
          {available ? (
            /* Ligne 2: Coûts de production */
            <div className="unit-costs-row">
              {cost.population > 0 && (
                <span className={`cost-item ${isResourceAffordable('population', cost.population) ? 'ok' : 'missing'}`}>
                  👥 {cost.population}
                </span>
              )}
              {cost.wood > 0 && (
                <span className={`cost-item ${isResourceAffordable('wood', cost.wood) ? 'ok' : 'missing'}`}>
                  🪵 {cost.wood}
                </span>
              )}
              {cost.stone > 0 && (
                <span className={`cost-item ${isResourceAffordable('stone', cost.stone) ? 'ok' : 'missing'}`}>
                  🪨 {cost.stone}
                </span>
              )}
              {cost.iron > 0 && (
                <span className={`cost-item ${isResourceAffordable('iron', cost.iron) ? 'ok' : 'missing'}`}>
                  ⚙️ {cost.iron}
                </span>
              )}
              {cost.horse > 0 && (
                <span className={`cost-item ${isResourceAffordable('horse', cost.horse) ? 'ok' : 'missing'}`}>
                  🐎 {cost.horse}
                </span>
              )}
              <span className="cost-item time-cost">
                ⏳ {formatTime(time)}
              </span>
              {unit.gold_cost_per_hour > 0 && (
                <span className="cost-item maintenance-cost">
                  <span className="cost-icon-stack">
                    <span className="icon-hourglass">⏳</span>
                    <span className="icon-gold">🪙</span>
                  </span>
                  {unit.gold_cost_per_hour}/h
                </span>
              )}
            </div>
          ) : (
            /* Message de prérequis */
            <div className="requirement-message">
              {getRequirementMessage(unit)}
            </div>
          )}
        </div>

        {/* Colonne 3: Boutons +/- + Input (seulement si disponible) */}
        {available && <div className="unit-controls-col">
          {/* Ligne 1: Boutons +/- */}
          <div className="quantity-controls">
            <button 
              className="qty-btn-ikariam minus"
              onClick={() => handleQuantityChange(unitType, Math.max(0, quantity - 1))}
              disabled={quantity === 0}
            >
              −
            </button>
            <button 
              className="qty-btn-ikariam plus"
              onClick={() => handleQuantityChange(unitType, quantity + 1)}
            >
              +
            </button>
          </div>
          
          {/* Ligne 2: Input textbox */}
          <input
            type="number"
            className="quantity-input-ikariam"
            value={quantity}
            min="0"
            onChange={(e) => {
              const val = parseInt(e.target.value) || 0;
              handleQuantityChange(unitType, Math.max(0, val));
            }}
          />
        </div>}
      </div>
    );
  };

  const renderProductionSummary = () => {
    const totals = calculateTotalSelection();
    
    if (totals.units.length === 0) {
      return null;
    }

    return (
      <div className="production-summary-ikariam">
        {/* Ligne 1: Miniatures des unités avec effectif */}
        <div className="summary-units-row">
          {totals.units.map((unit, index) => (
            <div key={index} className="summary-unit-item">
              <div className="summary-unit-icon">
                <img 
                  src={`/assets/units/${unit.type}.png`}
                  alt={unit.name}
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/assets/units/default.png';
                  }}
                />
              </div>
              <div className="summary-unit-count">×{unit.quantity}</div>
              <div className="summary-unit-name">{unit.name}</div>
            </div>
          ))}
        </div>

        {/* Ligne 2: Coût global */}
        <div className="summary-costs-row">
          <strong>Coût total :</strong>
          {totals.population > 0 && <span className="summary-cost">👥 {totals.population}</span>}
          {totals.wood > 0 && <span className="summary-cost">🪵 {totals.wood}</span>}
          {totals.stone > 0 && <span className="summary-cost">🪨 {totals.stone}</span>}
          {totals.iron > 0 && <span className="summary-cost">⚙️ {totals.iron}</span>}
          {totals.horse > 0 && <span className="summary-cost">🐎 {totals.horse}</span>}
          <span className="summary-cost time">⏳ {loading ? formatTime(timeRemaining) : formatTime(totals.time)}</span>
        </div>

        {/* Ligne 3: Boutons produire/annuler au centre */}
        <div className="summary-action-row">
          {loading ? (
            <>
              <button
                onClick={cancelProduction}
                className="cancel-production-btn"
              >
                ❌ Annuler
              </button>
              <div className="production-progress-text">
                ⏳ Production en cours... ({formatTime(timeRemaining)} restant)
              </div>
            </>
          ) : (
            <button
              onClick={startBatchProduction}
              disabled={loading}
              className="produce-all-btn enabled"
            >
              🔨 Produire
            </button>
          )}
        </div>
      </div>
    );
  };

  const renderProductionQueue = () => (
    <div className="production-queue">
      <h3 className="queue-title">File de production</h3>
      {productionQueue.length === 0 ? (
        <p className="no-production">Aucune production en cours</p>
      ) : (
        productionQueue.map((item, index) => {
          // Vérifier si c'est un batch (nouvelle méthode) ou une seule unité (ancienne)
          const isBatch = item.is_batch && item.units;
          
          return (
            <div key={index} className="queue-item">
              <div className="queue-info">
                <div>
                  {isBatch && item.units ? (
                    <>
                      <h4 className="queue-unit-name">Commande groupée</h4>
                      <p className="queue-quantity">
                        {item.units.map((u: any, i: number) => (
                          <span key={i}>
                            {i > 0 && ', '}
                            {u.quantity}x {u.name}
                          </span>
                        ))}
                      </p>
                    </>
                  ) : (
                    <>
                      <h4 className="queue-unit-name">{item.unit_type && unitStats[item.unit_type]?.name || item.unit_type || 'Unité'}</h4>
                      <p className="queue-quantity">Quantité: {item.quantity || 0}</p>
                    </>
                  )}
                </div>
                <div className="queue-time">
                  <p>Temps restant:</p>
                  <p className="time-remaining">{formatTime(item.remaining_time)}</p>
                </div>
              </div>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{
                    width: `${((item.total_time - item.remaining_time) / item.total_time) * 100}%`
                  }}
                ></div>
              </div>
              <button 
                className="cancel-queue-btn"
                onClick={cancelProduction}
                title="Annuler cette production"
              >
                ❌
              </button>
            </div>
          );
        })
      )}
    </div>
  );

  const getSpecialtyIcon = (specialty: string) => {
    const icons = {
      offensive: '⚔️',
      defensive: '🛡️',
      movement: '🏃‍♂️',
      moral: '👑'
    };
    return icons[specialty as keyof typeof icons] || '⚡';
  };

  const getSpecialtyColor = (specialty: string) => {
    const colors = {
      offensive: '#e74c3c',
      defensive: '#3498db',  
      movement: '#f39c12',
      moral: '#9b59b6'
    };
    return colors[specialty as keyof typeof colors] || '#95a5a6';
  };

  const getRarityColor = (rarity: string) => {
    const colors = {
      legendary: '#f1c40f',
      epic: '#9b59b6',
      rare: '#3498db',
      common: '#95a5a6'
    };
    return colors[rarity as keyof typeof colors] || '#95a5a6';
  };

  const handleReturnHeroToGarrison = async (heroInstanceId: string) => {
    // eslint-disable-next-line no-restricted-globals
    if (!confirm('Voulez-vous vraiment forcer le retour de ce héros en garnison ? Cette action ne devrait être utilisée qu\'en cas de bug.')) {
      return;
    }

    setReturningHero(heroInstanceId);
    try {
      const response = await fetch(`/api/military/hero/${heroInstanceId}/return-garrison`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (data.success) {
        alert('✅ Héros remis en garnison avec succès !');
        fetchHeroes(); // Rafraîchir la liste
      } else {
        alert(`❌ ${data.message}`);
      }
    } catch (error) {
      console.error('Erreur lors du retour du héros:', error);
      alert('❌ Erreur lors du retour du héros');
    } finally {
      setReturningHero(null);
    }
  };

  const renderGarrison = () => (
    <div className="garrison-display">
      <h3 className="garrison-title">🏰 Garnison de {city.name}</h3>
      
      {/* Section Héros */}
      {Object.keys(heroes).length > 0 && (
        <div className="heroes-section">
          <h4 className="section-title">🎖️ Héros</h4>
          <div className="heroes-grid">
            {Object.entries(heroes).map(([heroInstanceId, hero]) => (
              <div 
                key={heroInstanceId} 
                className="hero-card-garrison clickable"
                onClick={() => {
                  setSelectedHero(hero);
                  setShowHeroDetail(true);
                }}
              >
                <div className="hero-header">
                  <div className="hero-name-section">
                    <h5 className="hero-name">{hero.name}</h5>
                    <span 
                      className="hero-rarity"
                      style={{ color: getRarityColor(hero?.rarity || 'common') }}
                    >
                      ★ {(hero?.rarity || 'common').toUpperCase()}
                    </span>
                  </div>
                  <div 
                    className="hero-specialty-badge"
                    style={{ backgroundColor: getSpecialtyColor(hero?.specialty || '') }}
                  >
                    {getSpecialtyIcon(hero?.specialty || '')}
                  </div>
                </div>
                
                <div className="hero-level">
                  Niveau {hero?.current_level ?? 1} • {hero?.current_experience ?? 0} XP
                </div>
                
                <div className="hero-stats-mini">
                  <span>⚔️ {hero?.calculated_stats?.attack_melee ?? 0}</span>
                  <span>🛡️ {hero?.calculated_stats?.defense_melee ?? 0}</span>
                  <span>❤️ {hero?.calculated_stats?.hp ?? 0}</span>
                  <span>🏃‍♂️ {hero?.calculated_stats?.movement ?? 0}</span>
                </div>
                
                <div className="hero-bonuses">
                  <div className="bonus-row">
                    <span>Offensive: +{hero?.calculated_bonuses?.offensive_bonus ?? 0}%</span>
                    <span>Défensive: +{hero?.calculated_bonuses?.defensive_bonus ?? 0}%</span>
                  </div>
                  <div className="bonus-row">
                    <span>Moral: +{hero?.calculated_bonuses?.moral_bonus ?? 0}%</span>
                    <span>Rayon: {hero?.calculated_bonuses?.aura_radius ?? 0}</span>
                  </div>
                </div>
                
                <div className="hero-experience">
                  <div>🎯 Batailles: {hero?.battles_fought ?? 0}</div>
                  <div>🏆 Victoires: {hero?.victories ?? 0}</div>
                  <div>💀 Unités tuées: {hero?.units_killed ?? 0}</div>
                </div>
                
                <div className="hero-status">
                  {hero?.status === 'garrison' ? (
                    <span className="status-badge status-garrison">En garnison</span>
                  ) : (
                    <>
                      <span className="status-badge" style={{ backgroundColor: '#e67e22' }}>
                        {hero?.status || 'Statut inconnu'}
                      </span>
                      <button
                        className="hero-return-button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleReturnHeroToGarrison(heroInstanceId);
                        }}
                        disabled={returningHero === heroInstanceId}
                        style={{
                          marginTop: '8px',
                          padding: '4px 8px',
                          fontSize: '12px',
                          backgroundColor: '#e74c3c',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: returningHero === heroInstanceId ? 'not-allowed' : 'pointer',
                          opacity: returningHero === heroInstanceId ? 0.6 : 1
                        }}
                      >
                        {returningHero === heroInstanceId ? '⏳ Retour...' : '🔄 Forcer retour'}
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Section Unités */}
      {Object.keys(garrison).length > 0 && (
        <div className="units-section">
          <h4 className="section-title">⚔️ Unités</h4>
          <div className="garrison-units">
            {Object.entries(garrison).map(([unitType, quantity]) => {
              const unitInfo = unitStats[unitType];
              if (!unitInfo || quantity <= 0) return null;
              
              return (
                <div key={unitType} className="garrison-unit-card">
                  <div className="unit-icon">
                    <div className={`unit-icon-small ${unitInfo.category}`}>
                      {getCategoryIcon(unitInfo.category, unitType)}
                    </div>
                  </div>
                  <div className="unit-details">
                    <h4 className="unit-name">{unitInfo.name}</h4>
                    <p className="unit-quantity">Quantité: <strong>{quantity}</strong></p>
                    <div className="unit-stats-mini">
                      <span>⚔️ {unitInfo.attack_melee}/{unitInfo.attack_ranged}</span>
                      <span>🛡️ {unitInfo.defense_melee}/{unitInfo.defense_ranged}</span>
                      <span>❤️ {unitInfo.hp}</span>
                    </div>
                  </div>
                  <div className="unit-actions">
                    <p className="unit-status">En garnison</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Message si aucune force */}
      {Object.keys(garrison).length === 0 && Object.keys(heroes).length === 0 && (
        <div className="no-units">
          <p>Aucune force présente dans cette ville</p>
          <p className="hint">Produisez des unités dans l'onglet "Production" et recrutez des héros via la recherche</p>
        </div>
      )}
    </div>
  );

  return (
    <div className="barracks-popup-content">
      <div className="barracks-header">
        <h2>Caserne - Niveau {building.level}</h2>
        {factionBonuses && factionBonuses.faction === 'iron' && (
          <div className="faction-bonus-indicator">
            ⚔️ Faction Fer - Bonus actifs :
            <div className="bonus-details">
              <span className="bonus-item">💰 -10% coûts maintenance</span>
              <span className="bonus-item">⏳ -10% temps production</span>
            </div>
          </div>
        )}
      </div>

      <div className="barracks-tabs">
        <div className="tab-navigation">
          <button 
            className={`tab-button ${activeTab === 'production' ? 'active' : ''}`}
            onClick={() => setActiveTab('production')}
          >
            Production d'unités
          </button>
          <button 
            className={`tab-button ${activeTab === 'garrison' ? 'active' : ''}`}
            onClick={() => setActiveTab('garrison')}
          >
            🏰 Garnison
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'production' && (
            <div className="production-tab-ikariam">
              {/* Récapitulatif de sélection en haut */}
              {renderProductionSummary()}
              
              {/* File de production - affichée si des unités sont en cours */}
              {productionQueue.length > 0 && renderProductionQueue()}
              
              {/* Liste des unités disponibles */}
              <div className="units-list-ikariam">
                {getAvailableUnits().map(renderUnitCard)}
              </div>
            </div>
          )}
          
          {activeTab === 'garrison' && renderGarrison()}
        </div>
        
        {/* Hero Detail Popup */}
        {showHeroDetail && selectedHero && (
          <HeroDetailPopup
            hero={selectedHero}
            cityId={city.id}
            onClose={() => {
              setShowHeroDetail(false);
              setSelectedHero(null);
            }}
            onHeroUpdated={() => {
              fetchHeroes(); // Recharge les données des héros après level up
            }}
          />
        )}
        
        {/* Unit Detail Popup */}
        {showUnitDetail && selectedUnit && (
          <UnitDetailPopup
            isOpen={showUnitDetail}
            onClose={() => {
              setShowUnitDetail(false);
              setSelectedUnit(null);
            }}
            unit={selectedUnit.stats}
            unitType={selectedUnit.type}
            allUnits={getAvailableUnits()}
            onUnitChange={(newUnitType) => {
              const newUnit = unitStats[newUnitType];
              if (newUnit) {
                setSelectedUnit({ type: newUnitType, stats: newUnit });
              }
            }}
          />
        )}
      </div>
    </div>
  );
};

export default BarracksPopupContent;
