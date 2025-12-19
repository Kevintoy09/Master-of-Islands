import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useUser } from '../hooks/useUser';
import { getResourceEmoji, getResourceLabel, getUIEmoji } from '../constants/resourceIcons';

interface TransportsListPopupProps {
  onClose: () => void;
}

interface Transport {
  id: string;
  source_player_id: string;
  source_city: string;
  destination_city: string;
  destination_player_id: string;
  resources: { [key: string]: number };
  ships_needed: number;
  status: string;
  remaining_time: number;
  loading_time: number;
  travel_time: number;
  created_at: number;
  last_update: number;
  is_cross_player: boolean;
  timeline: {
    created: number;
    loading_start?: number;
    loading_end?: number;
    travel_start?: number;
    travel_end?: number;
    return_start?: number;
    return_end?: number;
    completed?: number;
  };
  // Ajouté pour la gestion du timing local
  server_remaining_time?: number;
  last_update_timestamp?: number;
}

interface PlayerInfo {
  id: string;
  transport_ships_total: number;
  transport_ships_busy: number;
}

const TRANSPORT_STATES = {
  WAITING: 'waiting',
  LOADING: 'loading', 
  TRAVELING: 'traveling',
  BATTLE_WAITING: 'battle_waiting',  // ✅ État d'attaque en attente de bataille
  RETURNING: 'returning',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled'
};

const TransportsListPopup: React.FC<TransportsListPopupProps> = ({ onClose }) => {
  const { user } = useUser();
  const [transports, setTransports] = useState<Transport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [playerInfo, setPlayerInfo] = useState<PlayerInfo | null>(null);
  const [confirmCancel, setConfirmCancel] = useState<{
    show: boolean;
    transportId: string;
    transportName: string;
  }>({ show: false, transportId: '', transportName: '' });

  // Référence pour forcer le re-render du timing local
  const localTimerRef = useRef<NodeJS.Timeout | null>(null);
  const [, forceUpdate] = useState({});

  // Charger les données initiales
  useEffect(() => {
    if (!user?.id) return;

    const loadInitialData = async () => {
      setLoading(true);
      try {
        // Charger les infos du joueur
        const playerResponse = await fetch(`/api/player/${user.id}`);
        if (playerResponse.ok) {
          const playerData = await playerResponse.json();
          setPlayerInfo({
            id: playerData.id,
            transport_ships_total: playerData.transport_ships_total || 5,
            transport_ships_busy: playerData.transport_ships_busy || 0
          });
        }

        // Charger les transports
        await loadTransports();
      } catch (err) {
        setError('Erreur lors du chargement des données');
        console.error('Erreur chargement initial:', err);
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, [user?.id]);

  // Charger la liste des transports
  const loadTransports = async () => {
    if (!user?.id) return;

    try {
      const response = await fetch(`/api/transports/player/${user.id}`);
      if (response.ok) {
        const data = await response.json();
        // Filtrer les transports actifs (ne supprimer que ceux qui sont vraiment archivés)
        const activeTransports = (data.transports || []).filter((transport: Transport) => 
          // Garder tous les transports sauf ceux qui sont définitivement terminés
          transport.status !== TRANSPORT_STATES.COMPLETED && 
          transport.status !== TRANSPORT_STATES.CANCELLED
        );
        
        // Ajouter les données de timing local lors du chargement
        const now = Date.now();
        const transportsWithTiming = activeTransports.map((transport: Transport) => ({
          ...transport,
          server_remaining_time: transport.remaining_time,
          last_update_timestamp: now
        }));
        
        // Trier par created_at décroissant (plus récents en premier)
        // created_at est maintenant un timestamp Unix, pas une string
        const sortedTransports = transportsWithTiming.sort((a: Transport, b: Transport) => {
          return b.created_at - a.created_at; // Ordre décroissant
        });
        
        setTransports(sortedTransports);
        setError("");
      } else {
        setError('Erreur lors du chargement des transports');
      }
    } catch (err) {
      setError('Erreur de connexion');
      console.error('Erreur transport:', err);
    }
  };

  // Mettre à jour automatiquement toutes les 5 secondes (données serveur)
  useEffect(() => {
    if (!user?.id) return;

    const interval = setInterval(() => {
      loadTransports();
    }, 5000); // ✅ Mise à jour plus fréquente pour une meilleure réactivité

    return () => clearInterval(interval);
  }, [user?.id]);

  // Timer local pour mise à jour fluide du temps restant (100ms)
  useEffect(() => {
    localTimerRef.current = setInterval(() => {
      setTransports(currentTransports => {
        const now = Date.now();
        return currentTransports.map(transport => {
          if (!transport.last_update_timestamp || !transport.server_remaining_time) {
            return transport;
          }

          // Calculer le temps écoulé depuis la dernière mise à jour serveur (en secondes)
          const elapsedSeconds = (now - transport.last_update_timestamp) / 1000;
          const newRemainingTime = Math.max(0, transport.server_remaining_time - elapsedSeconds);

          return {
            ...transport,
            remaining_time: newRemainingTime
          };
        });
      });

      // Forcer le re-render pour l'affichage
      forceUpdate({});
    }, 100); // Mise à jour locale toutes les 100ms pour un affichage fluide

    return () => {
      if (localTimerRef.current) {
        clearInterval(localTimerRef.current);
      }
    };
  }, []);

  // Annuler un transport
  const handleCancelTransport = async (transportId: string) => {
    try {
      const response = await fetch(`/api/transport/${transportId}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        // Recharger immédiatement les transports depuis le backend
        // pour vérifier que l'annulation a bien été sauvegardée
        await loadTransports();
        setConfirmCancel({ show: false, transportId: '', transportName: '' });
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Erreur lors de l\'annulation');
      }
    } catch (err) {
      setError('Erreur de connexion');
      console.error('Erreur annulation:', err);
    }
  };

  // Ouvrir la confirmation d'annulation
  const openCancelConfirmation = (transportId: string, sourceName: string, destName: string) => {
    setConfirmCancel({
      show: true,
      transportId,
      transportName: `${sourceName} → ${destName}`
    });
  };

  // Calculer le progrès et les infos d'un transport
  const getTransportInfo = useCallback((transport: Transport) => {
    const status = transport.status;
    
    let progress = 0.0;
    let statusText = "";
    let timeText = "";
    let progressColor = "var(--accent-color)";

    // Utiliser le temps calculé localement pour un affichage fluide
    const remainingTime = Math.max(0, transport.remaining_time);

    switch (status) {
      case TRANSPORT_STATES.WAITING:
        progress = 0.0;
        statusText = "⏳ En attente";
        timeText = `${Math.ceil(remainingTime)}s avant chargement`;
        progressColor = "#666";
        break;

      case TRANSPORT_STATES.LOADING:
        if (transport.loading_time && transport.loading_time > 0) {
          const elapsed = Math.max(0, transport.loading_time - remainingTime);
          progress = Math.min(1.0, elapsed / transport.loading_time) * 0.25; // Chargement = 0-25%
        }
        statusText = "📦 Chargement";
        timeText = `${Math.ceil(remainingTime)}s restant`;
        progressColor = "#FFA500";
        break;

      case TRANSPORT_STATES.TRAVELING:
        if (transport.travel_time && transport.travel_time > 0) {
          const elapsed = Math.max(0, transport.travel_time - remainingTime);
          const travelProgress = Math.min(1.0, elapsed / transport.travel_time);
          progress = 0.25 + (travelProgress * 0.5); // Voyage = 25-75%
        }
        statusText = "🚢 En transit";
        timeText = `${Math.ceil(remainingTime)}s restant`;
        progressColor = "#4CAF50";
        break;

      case TRANSPORT_STATES.BATTLE_WAITING:
        progress = 0.75; // Bataille en cours = 75%
        statusText = "⚔️ En bataille";
        timeText = "Bataille en cours...";
        progressColor = "#FF9800"; // Orange pour la bataille
        break;

      case TRANSPORT_STATES.RETURNING:
        if (transport.travel_time && transport.travel_time > 0) {
          const elapsed = Math.max(0, transport.travel_time - remainingTime);
          const returnProgress = Math.min(1.0, elapsed / transport.travel_time);
          progress = 0.75 + (returnProgress * 0.25); // Retour = 75-100%
        }
        statusText = "🔄 Retour";
        timeText = `${Math.ceil(remainingTime)}s restant`;
        progressColor = "#2196F3";
        break;

      case TRANSPORT_STATES.COMPLETED:
        progress = 1.0;
        statusText = "✅ Terminé";
        timeText = "Transport complété";
        progressColor = "#4CAF50";
        break;

      case TRANSPORT_STATES.CANCELLED:
        progress = 0.0;
        statusText = "❌ Annulé";
        timeText = "Transport annulé";
        progressColor = "#F44336";
        break;

      default:
        progress = 0.0;
        statusText = `❓ État inconnu (${status})`;
        timeText = "";
        progressColor = "#666";
        console.warn(`État de transport inconnu: "${status}"`);
    }

    return { progress, statusText, timeText, progressColor };
  }, []);

  // Formater les ressources transportées avec style amélioré
  const formatResourcesAsElements = (resources: { [key: string]: number }) => {
    const resourceEntries = Object.entries(resources)
      .filter(([, value]) => value > 0)
      .sort(([a], [b]) => {
        // Trier : unités d'abord, puis ressources
        const aIsUnit = a.startsWith('unit_');
        const bIsUnit = b.startsWith('unit_');
        if (aIsUnit && !bIsUnit) return -1;
        if (!aIsUnit && bIsUnit) return 1;
        return a.localeCompare(b);
      });

    if (resourceEntries.length === 0) {
      return <span style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>Aucune ressource</span>;
    }

    return (
      <div style={{ 
        display: 'flex', 
        flexWrap: 'wrap', 
        gap: '8px',
        fontSize: '0.85em'
      }}>
        {resourceEntries.map(([key, value]) => {
          const isUnit = key.startsWith('unit_');
          const displayKey = isUnit ? key.replace('unit_', '') : key;
          const emoji = isUnit ? '⚔️' : getResourceEmoji(key);
          const label = isUnit ? 
            displayKey.charAt(0).toUpperCase() + displayKey.slice(1).replace('_', ' ') : 
            getResourceLabel(key);
          
          return (
            <span 
              key={key}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '2px 6px',
                backgroundColor: isUnit ? 'rgba(139, 69, 19, 0.1)' : 'rgba(34, 139, 34, 0.1)',
                borderRadius: '12px',
                border: `1px solid ${isUnit ? 'rgba(139, 69, 19, 0.3)' : 'rgba(34, 139, 34, 0.3)'}`,
                whiteSpace: 'nowrap',
                fontSize: '0.9em'
              }}
            >
              <span style={{ fontSize: '1.1em' }}>{emoji}</span>
              <span style={{ fontWeight: 500 }}>{value}</span>
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.9em' }}>
                {label}
              </span>
            </span>
          );
        })}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="popup-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
        <div className="popup-base" style={{ 
          maxWidth: '600px', 
          minWidth: '320px',
          width: '90vw',
          maxHeight: '85vh',
          margin: '2vh auto'
        }}>
          <button 
            className="popup-close-button" 
            onClick={onClose}
            style={{
              fontSize: '24px',
              width: '40px',
              height: '40px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '50%',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              border: '2px solid var(--border-color)',
              cursor: 'pointer'
            }}
          >
            ✕
          </button>
          <div className="popup-section">
            <div className="popup-section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {getUIEmoji('time')} Chargement des transports...
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="popup-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="popup-base" style={{ 
        maxWidth: '600px', 
        minWidth: '320px',
        width: '90vw',
        maxHeight: '85vh',
        margin: '2vh auto'
      }}>
        <button 
          className="popup-close-button" 
          onClick={onClose}
          style={{
            fontSize: '24px',
            width: '40px',
            height: '40px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '50%',
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            border: '2px solid var(--border-color)',
            cursor: 'pointer',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
            e.currentTarget.style.transform = 'scale(1.1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
            e.currentTarget.style.transform = 'scale(1)';
          }}
        >
          ✕
        </button>
        
        {/* En-tête */}
        <div className="popup-section">
          <div className="popup-section-title">{getUIEmoji('transport_popup')} Transports en cours</div>
          <div className="popup-section-details" style={{ fontSize: '0.9em' }}>
            Tous les transports de vos ports
          </div>
          {playerInfo && (
            <div style={{ 
              marginTop: '12px',
              display: 'flex',
              flexWrap: 'wrap',
              gap: '12px',
              fontSize: '0.9em'
            }}>
              <div style={{
                padding: '8px 12px',
                backgroundColor: 'rgba(34, 139, 34, 0.1)',
                borderRadius: '20px',
                border: '1px solid rgba(34, 139, 34, 0.3)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                {getUIEmoji('ship')} <strong>{playerInfo.transport_ships_total - playerInfo.transport_ships_busy}</strong> / {playerInfo.transport_ships_total} libres
              </div>
              <div style={{
                padding: '8px 12px',
                backgroundColor: 'rgba(255, 165, 0, 0.1)',
                borderRadius: '20px',
                border: '1px solid rgba(255, 165, 0, 0.3)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                🚚 <strong>{transports.length}</strong> actifs
              </div>
            </div>
          )}
        </div>

        {/* Message d'erreur */}
        {error && (
          <div className="popup-error-message">
            {error}
          </div>
        )}

        {/* Liste des transports */}
        <div className="popup-section" style={{ 
          maxHeight: '60vh', 
          overflowY: 'auto',
          padding: '8px'
        }}>
          {transports.length === 0 ? (
            <div className="popup-section-details" style={{ textAlign: 'center', padding: '20px' }}>
              Aucun transport en cours
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {transports.map((transport) => {
                const info = getTransportInfo(transport);
                
                return (
                  <div 
                    key={transport.id}
                    className="popup-sub-section"
                    style={{ 
                      border: '1px solid var(--border-color)',
                      borderRadius: '12px',
                      padding: '16px',
                      backgroundColor: 'var(--background-secondary)',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                      transition: 'transform 0.2s ease, box-shadow 0.2s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.15)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                    }}
                  >
                    {/* En-tête du transport */}
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'flex-start',
                      marginBottom: '12px',
                      flexWrap: 'wrap',
                      gap: '8px'
                    }}>
                      <div className="popup-section-title" style={{ 
                        fontSize: '1em', 
                        margin: 0,
                        minWidth: '0',
                        flex: '1'
                      }}>
                        <strong>{transport.source_city}</strong> → <strong>{transport.destination_city}</strong>
                      </div>
                      <div style={{ 
                        fontSize: '0.9em', 
                        color: 'var(--text-secondary)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        flexShrink: '0'
                      }}>
                        {getUIEmoji('ship')} {transport.ships_needed}
                      </div>
                    </div>

                    {/* Ressources transportées */}
                    <div style={{ marginBottom: '12px' }}>
                      {formatResourcesAsElements(transport.resources)}
                    </div>

                    {/* État et temps */}
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center', 
                      marginBottom: '12px',
                      flexWrap: 'wrap',
                      gap: '8px'
                    }}>
                      <div style={{ 
                        fontWeight: 'bold', 
                        color: 'var(--text-primary)',
                        padding: '4px 8px',
                        backgroundColor: `${info.progressColor}20`,
                        borderRadius: '20px',
                        border: `1px solid ${info.progressColor}40`,
                        fontSize: '0.9em'
                      }}>
                        {info.statusText}
                      </div>
                      <div style={{ 
                        fontSize: '0.9em', 
                        color: 'var(--text-secondary)',
                        fontWeight: '500'
                      }}>
                        {info.timeText}
                      </div>
                    </div>

                    {/* Indicateurs de phases améliorés */}
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      marginBottom: '8px', 
                      fontSize: '1.2em',
                      padding: '0 8px'
                    }}>
                      <div style={{ 
                        display: 'flex', 
                        flexDirection: 'column', 
                        alignItems: 'center',
                        opacity: info.progress >= 0 ? 1 : 0.3
                      }}>
                        <span>📦</span>
                        <span style={{ fontSize: '0.6em', marginTop: '2px' }}>Charge</span>
                      </div>
                      <div style={{ 
                        display: 'flex', 
                        flexDirection: 'column', 
                        alignItems: 'center',
                        opacity: info.progress >= 0.25 ? 1 : 0.3
                      }}>
                        <span>🚢</span>
                        <span style={{ fontSize: '0.6em', marginTop: '2px' }}>Voyage</span>
                      </div>
                      <div style={{ 
                        display: 'flex', 
                        flexDirection: 'column', 
                        alignItems: 'center',
                        opacity: info.progress >= 0.75 ? 1 : 0.3
                      }}>
                        <span>🔄</span>
                        <span style={{ fontSize: '0.6em', marginTop: '2px' }}>Retour</span>
                      </div>
                      <div style={{ 
                        display: 'flex', 
                        flexDirection: 'column', 
                        alignItems: 'center',
                        opacity: info.progress >= 1 ? 1 : 0.3
                      }}>
                        <span>✅</span>
                        <span style={{ fontSize: '0.6em', marginTop: '2px' }}>Fini</span>
                      </div>
                    </div>

                    {/* Barre de progression améliorée */}
                    <div style={{ marginBottom: '12px' }}>
                      <div 
                        style={{
                          width: '100%',
                          height: '12px',
                          backgroundColor: 'var(--background-tertiary)',
                          borderRadius: '6px',
                          overflow: 'hidden',
                          position: 'relative',
                          border: '1px solid var(--border-color)'
                        }}
                      >
                        {/* Marqueurs de phases */}
                        <div style={{ position: 'absolute', left: '25%', top: 0, width: '1px', height: '100%', backgroundColor: 'rgba(255,255,255,0.3)' }} />
                        <div style={{ position: 'absolute', left: '75%', top: 0, width: '1px', height: '100%', backgroundColor: 'rgba(255,255,255,0.3)' }} />
                        
                        {/* Barre de progression */}
                        <div
                          style={{
                            width: `${info.progress * 100}%`,
                            height: '100%',
                            backgroundColor: info.progressColor,
                            transition: 'width 0.3s ease',
                            borderRadius: '4px'
                          }}
                        />
                      </div>
                      
                      {/* Pourcentage */}
                      <div style={{ 
                        fontSize: '0.8em', 
                        color: 'var(--text-secondary)', 
                        textAlign: 'right',
                        marginTop: '2px'
                      }}>
                        {Math.round(info.progress * 100)}%
                      </div>
                    </div>

                    {/* Actions */}
                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                      {transport.status !== TRANSPORT_STATES.COMPLETED && 
                       transport.status !== TRANSPORT_STATES.CANCELLED && (
                        <button
                          className="popup-action-button secondary"
                          style={{ padding: '4px 12px', fontSize: '0.8em' }}
                          onClick={() => openCancelConfirmation(transport.id, transport.source_city, transport.destination_city)}
                        >
                          Annuler
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="popup-actions">
          <button 
            className="popup-action-button primary" 
            onClick={onClose}
          >
            Fermer
          </button>
        </div>
      </div>

      {/* Popup de confirmation d'annulation */}
      {confirmCancel.show && (
        <div className="popup-overlay" style={{ zIndex: 1001 }}>
          <div className="popup-base" style={{ maxWidth: '400px', minWidth: '300px' }}>
            <div className="popup-section">
              <div className="popup-section-title">⚠️ Confirmer l'annulation</div>
              <div className="popup-section-details" style={{ marginTop: '10px' }}>
                Êtes-vous sûr de vouloir annuler ce transport ?
              </div>
              <div style={{ 
                fontWeight: 'bold', 
                marginTop: '8px', 
                padding: '8px',
                backgroundColor: 'var(--background-secondary)',
                borderRadius: '4px'
              }}>
                {confirmCancel.transportName}
              </div>
            </div>
            
            <div className="popup-actions">
              <button 
                className="popup-action-button secondary" 
                onClick={() => setConfirmCancel({ show: false, transportId: '', transportName: '' })}
              >
                Non, garder
              </button>
              <button 
                className="popup-action-button primary" 
                onClick={() => handleCancelTransport(confirmCancel.transportId)}
                style={{ backgroundColor: 'var(--roman-red)' }}
              >
                Oui, annuler
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TransportsListPopup;
