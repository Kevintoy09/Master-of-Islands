import React, { useState, useEffect, useCallback } from 'react';
import { useUser } from '../hooks/useUser';
import { useTransportConstants } from '../hooks/useTransportConstants';

interface TransportPopupProps {
  sourceCity: {
    id: string;
    name: string;
    resources: { [key: string]: number };
    buildings?: Array<{ name: string; level: number; slot_id: string; }>;
  };
  destinationCity: {
    id: string;
    name: string;
  };
  onTransportCreated?: () => void;
  onClose: () => void;
}

interface PlayerInfo {
  transport_ships_total: number;
  transport_ships_available: number;
}

const TransportPopup: React.FC<TransportPopupProps> = ({
  sourceCity,
  destinationCity,
  onClose,
  onTransportCreated
}) => {
  const { user } = useUser();
  const { constants: transportConstants, loading: constantsLoading } = useTransportConstants();
  const [playerInfo, setPlayerInfo] = useState<PlayerInfo | null>(null);
  const [selectedResources, setSelectedResources] = useState<{ [key: string]: number }>({});
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [transportInfo, setTransportInfo] = useState<{
    distance: number;
    transport_time: number;
    transport_speed: number;
  } | null>(null);

  // Configuration des ressources
  const RESOURCES = [
    { name: "wood", label: "Bois", icon: "🪵" },
    { name: "stone", label: "Pierre", icon: "🪨" },
    { name: "cereal", label: "Céréales", icon: "🌾" },
    { name: "iron", label: "Fer", icon: "⚙️" },
    { name: "papyrus", label: "Papyrus", icon: "📜" },
  ];

  // Fonction pour obtenir la vitesse de chargement du port de la ville source
  const getLoadingSpeed = (): number => {
    // Chercher le port dans les bâtiments de la ville source
    if (sourceCity.buildings) {
      const port = sourceCity.buildings.find(building => 
        building.name && building.name.toLowerCase().includes('port')
      );
      if (port) {
        // Vitesse de chargement basée sur les vraies valeurs du buildings.json
        const loadingSpeeds = {
          1: 10,
          2: 14,
          3: 19
        };
        return loadingSpeeds[port.level as keyof typeof loadingSpeeds] || 10;
      }
    }
    return 10; // Port niveau 1 par défaut si pas trouvé
  };

  // Initialiser les ressources sélectionnées
  useEffect(() => {
    if (!transportConstants) return;
    
    const initial: { [key: string]: number } = {};
    RESOURCES.forEach(res => {
      initial[res.name] = 0;
    });
    setSelectedResources(initial);
  }, [transportConstants]);

  // Charger les informations du joueur et les transports en cours
  useEffect(() => {
    if (!user?.id) return;

    const loadPlayerInfo = async () => {
      try {
        const response = await fetch(`/api/player/${user.id}/info`);
        if (response.ok) {
          const data = await response.json();
          setPlayerInfo({
            transport_ships_total: data.player_info?.transport_ships_total || 0,
            transport_ships_available: data.player_info?.transport_ships_available || 0
          });
          // Plus besoin de loadTransports(), les bateaux occupés sont déjà calculés côté serveur
        }
      } catch (err) {
        console.error('Erreur lors du chargement des infos joueur:', err);
      }
    };

    loadPlayerInfo();
  }, [user?.id]);

  // Charger les informations de transport (distance, temps)
  useEffect(() => {
    if (!sourceCity?.id || !destinationCity?.id) return;

    const loadTransportInfo = async () => {
      try {
        const response = await fetch(`/api/transport/distance/${sourceCity.id}/${destinationCity.id}`);
        if (response.ok) {
          const data = await response.json();
          setTransportInfo({
            distance: data.distance,
            transport_time: data.transport_time,
            transport_speed: data.transport_speed
          });
          setError("");
        } else {
          const errorData = await response.json();
          setError(errorData.error || "Erreur lors du calcul de distance");
          setTransportInfo(null);
        }
      } catch (err) {
        console.error('Erreur lors du chargement des informations de transport:', err);
        setError("Erreur de connexion lors du calcul de distance");
        setTransportInfo(null);
      }
    };

    loadTransportInfo();
  }, [sourceCity?.id, destinationCity?.id]);

  // Calculer le maximum pour un slider donné
  const getSliderMax = useCallback((resourceName: string): number => {
    if (!transportConstants) return 0;
    
    const stock = sourceCity.resources[resourceName] || 0;
    const shipsAvailable = playerInfo?.transport_ships_available || 0;
    const maxCapacity = shipsAvailable * transportConstants.ship_capacity;
    const othersTotal = Object.entries(selectedResources)
      .filter(([key]) => key !== resourceName)
      .reduce((sum, [, value]) => sum + value, 0);
    return Math.min(stock, Math.max(0, maxCapacity - othersTotal));
  }, [sourceCity.resources, playerInfo?.transport_ships_available, selectedResources, transportConstants]);

  // Calculer les totaux et statistiques
  const calculateStats = useCallback(() => {
    if (!transportConstants) {
      return {
        total: 0,
        shipsNeeded: 0,
        shipsAvailable: 0,
        shipsToSend: 0,
        loadingTime: 0,
        transportTime: 0,
        distance: 0
      };
    }

    const total = Object.values(selectedResources).reduce((sum, value) => sum + value, 0);
    const shipsNeeded = total > 0 ? Math.ceil(total / transportConstants.ship_capacity) : 0;
    const shipsAvailable = playerInfo?.transport_ships_available || 0;
    const shipsToSend = Math.min(shipsNeeded, shipsAvailable);
    const loadingTime = total / getLoadingSpeed();
    const transportTime = transportInfo?.transport_time || (100 / transportConstants.transport_speed);
    const distance = transportInfo?.distance || 100;
    return {
      total,
      shipsNeeded,
      shipsAvailable,
      shipsToSend,
      loadingTime,
      transportTime,
      distance
    };
  }, [selectedResources, playerInfo?.transport_ships_available, transportInfo, getLoadingSpeed, transportConstants]);

  if (constantsLoading || !transportConstants) {
    return (
      <div className="popup-overlay">
        <div className="popup-base" style={{ maxWidth: '400px' }}>
          <button className="popup-close-button" onClick={onClose}>×</button>
          <div className="popup-section">
            <div className="popup-section-title">⏳ Chargement...</div>
          </div>
        </div>
      </div>
    );
  }

  const SHIP_CAPACITY = transportConstants.ship_capacity;
  const TRANSPORT_SPEED = transportConstants.transport_speed;

  // Mettre à jour une ressource sélectionnée
  const updateResource = (resourceName: string, value: number) => {
    const maxValue = getSliderMax(resourceName);
    const clampedValue = Math.max(0, Math.min(maxValue, value));
    
    setSelectedResources(prev => ({
      ...prev,
      [resourceName]: clampedValue
    }));
  };

  const stats = calculateStats();

  // Valider et envoyer le transport
  const handleValidate = async () => {
    if (!transportInfo) {
      setError("Impossible de calculer la distance de transport. Vérifiez que les deux villes ont un port construit.");
      return;
    }

    if (stats.shipsAvailable <= 0) {
      setError("Aucun bateau disponible pour ce transport.");
      return;
    }

    if (stats.total === 0) {
      setError("Sélectionnez au moins une ressource à transporter.");
      return;
    }

    if (stats.shipsNeeded > stats.shipsAvailable) {
      setError(`Pas assez de bateaux. Requis: ${stats.shipsNeeded}, disponibles: ${stats.shipsAvailable}`);
      return;
    }

    setError("");
    setLoading(true);

    try {
      const payload = {
        player_id: user?.id,
        source_city_id: sourceCity.id,
        destination_city_id: destinationCity.id,
        resources: selectedResources,
        ships_needed: stats.shipsToSend,
        loading_time: stats.loadingTime,
        transport_time: stats.transportTime
      };

      const response = await fetch(`/api/transport/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        if (onTransportCreated) {
          onTransportCreated();
        }
        onClose();
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Erreur lors de la création du transport');
      }
    } catch (err) {
      setError('Erreur de connexion');
      console.error('Erreur transport:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="popup-overlay">
      <div className="popup-base" style={{ maxWidth: '600px', minWidth: '500px' }}>
        <button className="popup-close-button" onClick={onClose}>×</button>
        
        {/* En-tête */}
        <div className="popup-section">
          <div className="popup-section-title">🚢 Transport de marchandises</div>
          <div className="popup-section-details">
            De <strong>{sourceCity.name}</strong> ({sourceCity.id}) vers <strong>{destinationCity.name}</strong> ({destinationCity.id})
          </div>
          <div className="popup-stats-grid" style={{ marginTop: '8px' }}>
            <div>Bateaux disponibles: <strong>{stats.shipsAvailable}</strong></div>
            <div>Capacité par bateau: <strong>{SHIP_CAPACITY}</strong></div>
          </div>
        </div>

        {/* Message d'erreur */}
        {error && (
          <div className="popup-error-message">
            {error}
          </div>
        )}

        {/* Sélection des ressources */}
        <div className="popup-section">
          <div className="popup-section-title">📦 Ressources à transporter</div>
          
          {RESOURCES.map(resource => {
            const stock = sourceCity.resources[resource.name] || 0;
            const maxValue = getSliderMax(resource.name);
            const currentValue = selectedResources[resource.name] || 0;
            
            return (
              <div key={resource.name} className="popup-input-group" style={{ marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px', fontSize: '0.9em' }}>
                  <span>{resource.icon}</span>
                  <span style={{ marginLeft: '6px', fontWeight: 'bold', flex: 1 }}>{resource.label}</span>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.8em' }}>
                    Stock: {Math.floor(stock)} | Max: {Math.floor(maxValue)}
                  </span>
                </div>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <input
                    type="range"
                    min="0"
                    max={maxValue}
                    value={currentValue}
                    onChange={(e) => updateResource(resource.name, parseInt(e.target.value))}
                    style={{ flex: 1 }}
                    disabled={maxValue === 0}
                  />
                  <input
                    type="number"
                    min="0"
                    max={maxValue}
                    value={currentValue}
                    onChange={(e) => updateResource(resource.name, parseInt(e.target.value) || 0)}
                    className="popup-number-input"
                    style={{ width: '80px' }}
                    disabled={maxValue === 0}
                  />
                </div>
              </div>
            );
          })}
        </div>

        {/* Résumé du transport */}
        <div className="popup-section highlight">
          <div className="popup-section-title">📊 Résumé du transport</div>
          <div className="popup-stats-grid three-col">
            <div>Total: <strong>{stats.total}</strong></div>
            <div>Bateaux requis: <strong>{stats.shipsNeeded}</strong></div>
            <div>Bateaux envoyés: <strong>{stats.shipsToSend}</strong></div>
          </div>
          
          <div className="popup-stats-grid" style={{ marginTop: '8px' }}>
            <div>Distance: <strong>{stats.distance.toFixed(1)} unités</strong></div>
            <div>Vitesse transport: <strong>{transportInfo?.transport_speed || TRANSPORT_SPEED} u/s</strong></div>
            <div>Temps de chargement: <strong>{stats.loadingTime.toFixed(1)}s</strong></div>
            <div>Temps de transport: <strong>{stats.transportTime.toFixed(1)}s</strong></div>
          </div>
        </div>

        {/* Actions */}
        <div className="popup-actions">
          <button 
            className="popup-action-button secondary" 
            onClick={onClose}
            disabled={loading}
          >
            Annuler
          </button>
          <button 
            className="popup-action-button primary" 
            onClick={handleValidate}
            disabled={loading || stats.total === 0 || stats.shipsAvailable === 0 || !transportInfo}
          >
            {loading ? 'Envoi...' : 'Valider le transport'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default TransportPopup;
