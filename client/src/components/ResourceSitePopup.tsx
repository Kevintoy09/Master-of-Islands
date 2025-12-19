import React, { useState, useEffect } from 'react';
import './ResourceSitePopup.css';
import { useUser } from '../hooks/useUser';

interface ResourceSiteInfo {
  level: number;
  max_workers_per_city: number;
  base_yield: number;
  upgrade_cost: { [key: string]: number };
  upgrade_time: number;
  upgrade_in_progress: boolean;
  upgrade_remaining_time: number;
  next_level_benefits: {
    max_workers_per_city: number;
  };
  all_cities: Array<{
    city_id: string;
    city_name: string;
    player: string;
    workers: number;
  }>;
  player_cities: Array<{
    city_id: string;
    city_name: string;
    player: string;
    workers: number;
    free_population: number;
  }>;
  donations: { [city_id: string]: { [resource: string]: number } };
  donations_history: { [city_id: string]: { [resource: string]: number } };
}

interface ResourceSitePopupProps {
  isOpen: boolean;
  onClose: () => void;
  siteType: string;
  islandId: string;
  activeCityId?: string; // Ajout de l'ID de la ville active
}

const SITE_LABELS: { [key: string]: string } = {
  forest: "Forêt",
  quarry: "Carrière",
  grain_field: "Champ de céréales",
  iron_mine: "Mine de fer",
  papyrus_pond: "Étang de papyrus",
  horse_ranch: "Ranch de chevaux",
  marble_mine: "Mine de marbre",
  glassworks: "Verrerie",
  pasture: "Pâturage",
  coal_mine: "Mine de charbon",
  gunpowder_lab: "Laboratoire de poudre",
  spice_garden: "Jardin d'épices",
  cotton_field: "Champ de coton"
};

const RESOURCE_LABELS: { [key: string]: string } = {
  wood: "Bois",
  stone: "Pierre",
  iron: "Fer",
  cereal: "Céréales",
  papyrus: "Papyrus",
  horse: "Chevaux",
  marble: "Marbre",
  glass: "Verre",
  wine: "Vin",
  coal: "Charbon",
  gunpowder: "Poudre",
  spices: "Épices",
  cotton: "Coton"
};

const ResourceSitePopup: React.FC<ResourceSitePopupProps> = ({
  isOpen,
  onClose,
  siteType,
  islandId,
  activeCityId
}) => {
  const { user } = useUser(); // Accès aux informations du joueur connecté
  const [siteInfo, setSiteInfo] = useState<ResourceSiteInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [workerInput, setWorkerInput] = useState('0');
  const [donationAmount, setDonationAmount] = useState('0');
  const [selectedResource, setSelectedResource] = useState('');
  const [upgradeTimer, setUpgradeTimer] = useState(0);
  const [canClose, setCanClose] = useState(false); // Empêcher la fermeture immédiate

  // Activer la possibilité de fermer le popup après un délai
  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => {
        setCanClose(true);
      }, 500); // Délai de 500ms avant de pouvoir fermer
      
      return () => {
        clearTimeout(timer);
        setCanClose(false);
      };
    }
  }, [isOpen]);

  // Fetch des informations du site
  const fetchSiteInfo = async () => {
    setLoading(true);
    setError(null);
    try {
      // Vérifier que l'utilisateur est connecté
      if (!user?.id) {
        throw new Error('Vous devez être connecté pour accéder aux sites de ressources');
      }
      
      const response = await fetch(`/api/resources/site/${islandId}/${siteType}/info?player_id=${user.id}`);
      if (!response.ok) {
        throw new Error('Erreur lors du chargement du site');
      }
      const data = await response.json();
      setSiteInfo(data);
      
      // Configure la valeur par défaut du slider et input
      const playerCity = data.player_cities?.[0];
      if (playerCity) {
        setWorkerInput(playerCity.workers.toString());
      }
      
      // Configure la ressource de don par défaut
      const upgradeCostKeys = Object.keys(data.upgrade_cost || {});
      if (upgradeCostKeys.length > 0) {
        setSelectedResource(upgradeCostKeys[0]);
      }
      
      // Configure le timer si un upgrade est en cours
      if (data.upgrade_in_progress) {
        setUpgradeTimer(data.upgrade_remaining_time);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    } finally {
      setLoading(false);
    }
  };

  // Assigner des ouvriers
  const assignWorkers = async () => {
    if (!siteInfo?.player_cities?.[0]) return;
    
    // Vérification que l'utilisateur est connecté
    if (!user?.id) {
      setError('Vous devez être connecté pour assigner des ouvriers');
      return;
    }
    
    const workers = parseInt(workerInput);
    const playerCity = siteInfo.player_cities[0];
    
    if (workers < 0 || workers > siteInfo.max_workers_per_city) {
      setError(`Nombre d'ouvriers invalide (0-${siteInfo.max_workers_per_city})`);
      return;
    }

    // Note: La validation de population libre est faite côté serveur
    // avec les bonnes règles métier (validation d'île, etc.)

    try {
      const response = await fetch(`/api/resources/site/${islandId}/${siteType}/assign-workers?player_id=${user?.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workers,
          city_id: playerCity.city_id,
          active_city_id: activeCityId || playerCity.city_id // Utiliser activeCityId ou fallback
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Erreur lors de l\'assignation');
      }
      
      const result = await response.json();
      
      // Déclencher la mise à jour de production
      try {
        await fetch('/api/update-production', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
      } catch (productionError) {
        console.warn('Erreur lors de la mise à jour de production:', productionError);
      }
      
      // Refresh les données
      fetchSiteInfo();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    }
  };

  // Faire un don
  const makeDonation = async () => {
    if (!siteInfo?.player_cities?.[0] || !selectedResource) return;
    
    const amount = parseInt(donationAmount);
    const playerCity = siteInfo.player_cities[0];
    
    if (amount <= 0) {
      setError('Montant de don invalide');
      return;
    }

    try {
      const response = await fetch(`/api/resources/site/${islandId}/${siteType}/donate?player_id=${user?.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resource_type: selectedResource,
          amount,
          city_id: playerCity.city_id,
          active_city_id: activeCityId || playerCity.city_id // Utiliser activeCityId ou fallback
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Erreur lors du don');
      }
      
      // Reset le champ de don et refresh
      setDonationAmount('0');
      fetchSiteInfo();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    }
  };

  // Timer d'upgrade
  useEffect(() => {
    if (upgradeTimer > 0) {
      const interval = setInterval(() => {
        setUpgradeTimer(prev => {
          if (prev <= 1) {
            fetchSiteInfo(); // Refresh quand le timer se termine
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      
      return () => clearInterval(interval);
    }
  }, [upgradeTimer]);

  // Fetch initial
  useEffect(() => {
    if (isOpen) {
      fetchSiteInfo();
    }
  }, [isOpen, islandId, siteType]);

  // Calcul des ressources restantes pour l'upgrade
  const calculateRemainingResources = () => {
    if (!siteInfo?.upgrade_cost) return {};
    
    const remaining: { [key: string]: number } = {};
    Object.entries(siteInfo.upgrade_cost).forEach(([resource, needed]) => {
      const donated = Object.values(siteInfo.donations || {}).reduce((sum, cityDonations) => {
        return sum + (cityDonations[resource] || 0);
      }, 0);
      remaining[resource] = Math.max(0, needed - donated);
    });
    
    return remaining;
  };

  const formatTimer = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (!isOpen) return null;

  return (
    <div className="resource-site-popup-overlay" 
         onClick={(e) => {
           if (e.target === e.currentTarget && canClose) {
             onClose();
           }
         }}
         onTouchEnd={(e) => {
           if (e.target === e.currentTarget && canClose) {
             onClose();
           }
         }}>
      <div className="resource-site-popup" 
           onClick={(e) => e.stopPropagation()}
           onTouchStart={(e) => e.stopPropagation()}
           onTouchEnd={(e) => e.stopPropagation()}>
        <button className="popup-close-button" onClick={onClose}>×</button>
        
        <div className="popup-content">
          <h3 className="popup-title">{SITE_LABELS[siteType] || siteType}</h3>

          {loading && <div className="popup-section">Chargement...</div>}
          {error && <div className="popup-error-message">{error}</div>}
          
          {siteInfo && (
            <>
              {/* Informations du site */}
              <div className="popup-section info">
                <div className="popup-section-title">Informations du site</div>
                <div className="popup-stats-grid">
                  <div>Niveau : {siteInfo.level}</div>
                  <div>Récolte : {siteInfo.base_yield}/ouv./sec</div>
                  <div>Ouvriers max : {siteInfo.max_workers_per_city}</div>
                  <div>Ressource : {RESOURCE_LABELS[siteType] || siteType}</div>
                </div>
              </div>

              {/* Assignation d'ouvriers */}
              {siteInfo.player_cities && siteInfo.player_cities.length > 0 ? (
                <div className="popup-section warning">
                  <div className="popup-worker-controls">
                    <div className="popup-worker-title">
                      Affecter des ouvriers au site
                    </div>
                    
                    <div className="popup-input-group">
                      <input
                        type="number"
                        value={workerInput}
                        onChange={(e) => setWorkerInput(e.target.value)}
                        min="0"
                        max={siteInfo.max_workers_per_city}
                        className="popup-number-input"
                        placeholder="Nombre"
                      />
                      <button onClick={assignWorkers} className="popup-action-button primary">
                        Affecter
                      </button>
                    </div>
                    
                    <div style={{ marginTop: '8px' }}>
                      <input
                        type="range"
                        min="0"
                        max={siteInfo.max_workers_per_city}
                        value={workerInput}
                        onChange={(e) => setWorkerInput(e.target.value)}
                        style={{ width: '100%', marginBottom: '4px' }}
                      />
                      <div className="popup-stats-grid">
                        <div>Affectés : {siteInfo.player_cities[0].workers}</div>
                        <div>Libres : {siteInfo.player_cities[0].free_population}</div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="popup-section">
                  <div className="popup-section-subtitle" style={{ textAlign: 'center', fontStyle: 'italic' }}>
                    Vous devez posséder une ville sur cette île pour affecter des ouvriers.
                  </div>
                </div>
              )}

              {/* Informations d'upgrade */}
              <div className="popup-section info">
                <div className="popup-section-title">Développement du site</div>
                <div>Temps d'upgrade : {siteInfo.upgrade_time} sec</div>
                {upgradeTimer > 0 && (
                  <div className="popup-timer">
                    Timer : {formatTimer(upgradeTimer)}
                  </div>
                )}
                <div className="popup-section-subtitle">
                  Prochain niveau : max {siteInfo.next_level_benefits.max_workers_per_city} ouvriers/ville
                </div>
              </div>

              {/* Coût d'upgrade et dons */}
              {Object.keys(siteInfo.upgrade_cost).length > 0 && (
                <div className="popup-section highlight">
                  <div className="popup-section-title">Ressources nécessaires</div>
                  <div className="popup-section-details">
                    {Object.entries(siteInfo.upgrade_cost)
                      .map(([res, amount]) => `${amount} ${RESOURCE_LABELS[res] || res}`)
                      .join(', ')}
                  </div>

                  {(() => {
                    const remaining = calculateRemainingResources();
                    const hasRemaining = Object.values(remaining).some(val => val > 0);
                    return hasRemaining && (
                      <div className="popup-section-subtitle">
                        Restants : {Object.entries(remaining)
                          .filter(([_, amount]) => amount > 0)
                          .map(([res, amount]) => `${amount} ${RESOURCE_LABELS[res] || res}`)
                          .join(', ')}
                      </div>
                    );
                  })()}

                  {/* Donation */}
                  <div className="popup-input-group" style={{ marginTop: '8px' }}>
                    <input
                      type="number"
                      value={donationAmount}
                      onChange={(e) => setDonationAmount(e.target.value)}
                      min="0"
                      className="popup-number-input"
                      placeholder="Quantité"
                    />
                    <select
                      value={selectedResource}
                      onChange={(e) => setSelectedResource(e.target.value)}
                      className="popup-text-input"
                      style={{ width: 'auto' }}
                    >
                      {Object.keys(siteInfo.upgrade_cost).map(resource => (
                        <option key={resource} value={resource}>
                          {RESOURCE_LABELS[resource] || resource}
                        </option>
                      ))}
                    </select>
                    <button onClick={makeDonation} className="popup-action-button primary">
                      Donner
                    </button>
                  </div>
                </div>
              )}

              {/* Liste des villes */}
              <div className="popup-section">
                <div className="popup-section-title">Villes et joueurs sur l'île</div>
                <div className="popup-table-header">
                  <span>Ville</span>
                  <span>Joueur</span>
                  <span>Ouvriers</span>
                  <span>Dons</span>
                </div>
                {siteInfo.all_cities.map((city) => {
                  const cityDonations = siteInfo.donations_history[city.city_id] || {};
                  const donationText = Object.keys(cityDonations).length > 0
                    ? Object.entries(cityDonations)
                        .map(([res, amount]) => `${amount} ${RESOURCE_LABELS[res] || res}`)
                        .join(' + ')
                    : '0';
                  
                  return (
                    <div key={city.city_id} className="popup-table-row">
                      <span>{city.city_name}</span>
                      <span>{city.player}</span>
                      <span>{city.workers}</span>
                      <span>{donationText}</span>
                    </div>
                  );
                })}
              </div>

              {/* Actions */}
              <div className="popup-actions">
                <button onClick={onClose} className="popup-action-button secondary">
                  Retour à l'Île
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResourceSitePopup;
