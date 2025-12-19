import React, { useState, useEffect } from 'react';
import { marketStyles } from './MarketStyles';
import { RESOURCE_EMOJIS, RESOURCE_LABELS, getResourceEmoji, getResourceLabel } from '../constants/resourceIcons';

// Types
interface MarketPopupContentProps {
  city: any;
  building: any;
  onClose: () => void;
  onCityDataChange?: () => void;
}

interface MarketOffer {
  offer_id: string;
  resource: string;
  quantity: number;
  price_per_unit: number;
  total_price: number;
  created_at: number;
}

interface MarketCapabilities {
  total_capacity: number;
  used_capacity: number;
  available_capacity: number;
  market_range: number;
}

// Constantes pour les ressources disponibles dans le dropdown
const resourceTypesWithEmojis = [
  { key: 'wood', label: `${RESOURCE_EMOJIS.wood} ${RESOURCE_LABELS.wood}` },
  { key: 'stone', label: `${RESOURCE_EMOJIS.stone} ${RESOURCE_LABELS.stone}` },
  { key: 'iron', label: `${RESOURCE_EMOJIS.iron} ${RESOURCE_LABELS.iron}` },
  { key: 'glass', label: `${RESOURCE_EMOJIS.glass} ${RESOURCE_LABELS.glass}` },
  { key: 'marble', label: `${RESOURCE_EMOJIS.marble} ${RESOURCE_LABELS.marble}` },
  { key: 'cereal', label: `${RESOURCE_EMOJIS.cereal} ${RESOURCE_LABELS.cereal}` },
  { key: 'papyrus', label: `${RESOURCE_EMOJIS.papyrus} ${RESOURCE_LABELS.papyrus}` },
  { key: 'horse', label: `${RESOURCE_EMOJIS.horse} ${RESOURCE_LABELS.horse}` },
  { key: 'wine', label: `${RESOURCE_EMOJIS.wine} ${RESOURCE_LABELS.wine}` },
  { key: 'coal', label: `${RESOURCE_EMOJIS.coal} ${RESOURCE_LABELS.coal}` },
  { key: 'gunpowder', label: `${RESOURCE_EMOJIS.gunpowder} ${RESOURCE_LABELS.gunpowder}` },
  { key: 'spices', label: `${RESOURCE_EMOJIS.spices} ${RESOURCE_LABELS.spices}` },
  { key: 'cotton', label: `${RESOURCE_EMOJIS.cotton} ${RESOURCE_LABELS.cotton}` }
];

const MarketPopupContent: React.FC<MarketPopupContentProps> = ({ city, building, onClose, onCityDataChange }) => {
  const [activeTab, setActiveTab] = useState<'mes-offres' | 'vendre' | 'acheter'>('mes-offres');
  const [loading, setLoading] = useState(false);
  const [marketCapabilities, setMarketCapabilities] = useState<MarketCapabilities | null>(null);
  const [myOffers, setMyOffers] = useState<MarketOffer[]>([]);
  const [availableOffers, setAvailableOffers] = useState<any[]>([]);
  
  // États pour le formulaire de vente
  const [sellResource, setSellResource] = useState('wood');
  const [sellQuantity, setSellQuantity] = useState('');
  const [sellPrice, setSellPrice] = useState('');
  
  // État pour le filtrage des offres d'achat
  const [filterResource, setFilterResource] = useState<string>('all');

  useEffect(() => {
    fetchMarketData();
  }, [city.id]);

  const fetchMarketData = async () => {
    setLoading(true);
    try {
      // Récupérer les capacités du marché
      const capabilitiesResponse = await fetch(`/api/city/${city.id}/market/capabilities`);
      if (capabilitiesResponse.ok) {
        const data = await capabilitiesResponse.json();
        setMarketCapabilities(data.capabilities || null);
      }

      // Récupérer mes offres
      const myOffersResponse = await fetch(`/api/city/${city.id}/market/my-offers`);
      if (myOffersResponse.ok) {
        const offers = await myOffersResponse.json();
        // S'assurer que c'est un tableau et extraire les offres
        const offersArray = offers.offers || [];
        setMyOffers(Array.isArray(offersArray) ? offersArray : []);
      } else {
        setMyOffers([]);
      }

      // Récupérer les offres disponibles
      const availableOffersResponse = await fetch(`/api/city/${city.id}/market/available-offers`);
      if (availableOffersResponse.ok) {
        const offers = await availableOffersResponse.json();
        // S'assurer que c'est un tableau et extraire les offres
        const offersArray = offers.offers || [];
        setAvailableOffers(Array.isArray(offersArray) ? offersArray : []);
      } else {
        setAvailableOffers([]);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des données du marché:', error);
      setMyOffers([]);
      setAvailableOffers([]);
    } finally {
      setLoading(false);
    }
  };

  // Calculer les ressources de la ville (sans logs pour éviter la boucle)
  const cityResources = city.resources || {};
  const maxResourceToSell = cityResources[sellResource] || 0;

  // Formater une date simple
  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString('fr-FR');
  };

  // Créer une offre
  const handleCreateOffer = async () => {
    const quantity = parseInt(sellQuantity);
    const pricePerUnit = parseFloat(sellPrice);
    
    if (!quantity || !pricePerUnit || quantity <= 0 || pricePerUnit <= 0) {
      alert('Veuillez entrer des valeurs valides');
      return;
    }

    if (quantity > maxResourceToSell) {
      alert(`Vous n'avez que ${maxResourceToSell} ${sellResource} disponible`);
      return;
    }

    if (marketCapabilities && marketCapabilities.available_capacity < quantity) {
      alert(`Capacité insuffisante du marché. Capacité disponible: ${marketCapabilities.available_capacity}`);
      return;
    }

    try {
      const response = await fetch(`/api/city/${city.id}/market/create-offer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resource_type: sellResource,
          quantity: quantity,
          price_per_unit: pricePerUnit,
        }),
      });
      
      if (response.ok) {
        alert('Offre créée avec succès !');
        setSellQuantity('');
        setSellPrice('');
        // Recharger les données pour voir la nouvelle offre
        await fetchMarketData();
        // Changer d'onglet pour voir l'offre créée
        setActiveTab('mes-offres');
        if (onCityDataChange) onCityDataChange();
      } else {
        const error = await response.json();
        alert(`Erreur: ${error.error}`);
      }
    } catch (error) {
      console.error('Network error:', error);
      alert('Erreur lors de la création de l\'offre');
    }
  };

  // Acheter une offre
  const handleBuyOffer = async (offerId: string) => {
    if (!window.confirm('Confirmer l\'achat de cette offre ?')) return;

    try {
      const response = await fetch(`/api/city/${city.id}/market/buy-offer/${offerId}`, {
        method: 'POST'
      });

      if (response.ok) {
        alert('Achat réussi !');
        fetchMarketData();
        if (onCityDataChange) onCityDataChange();
      } else {
        const error = await response.json();
        alert(`Erreur: ${error.error}`);
      }
    } catch (error) {
      console.error('Erreur lors de l\'achat:', error);
      alert('Erreur lors de l\'achat');
    }
  };

  // Annuler une offre
  const handleCancelOffer = async (offerId: string) => {
    if (!window.confirm('Confirmer l\'annulation de cette offre ?')) return;

    try {
      const response = await fetch(`/api/city/${city.id}/market/cancel-offer/${offerId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        alert('Offre annulée !');
        fetchMarketData();
        if (onCityDataChange) onCityDataChange();
      } else {
        const error = await response.json();
        alert(`Erreur: ${error.error}`);
      }
    } catch (error) {
      console.error('Erreur lors de l\'annulation:', error);
      alert('Erreur lors de l\'annulation');
    }
  };

  // Rendu des onglets
  const renderTabContent = () => {
    if (loading) {
      return (
        <div style={marketStyles.loading}>
          <div style={{ fontSize: '32px', marginBottom: '15px' }}>⏳</div>
          <p>Chargement des données du marché...</p>
        </div>
      );
    }

    switch (activeTab) {
      case 'mes-offres':
        return (
          <div style={marketStyles.tabContainer}>
            <h4 style={{...marketStyles.sectionTitle, padding: '10px', margin: '0 0 15px 0', fontSize: '16px'}}>
              <span style={{ fontSize: '20px' }}>📦</span>
              Mes Offres en cours
            </h4>
            {!Array.isArray(myOffers) || myOffers.length === 0 ? (
              <div style={marketStyles.empty}>
                <div style={{ fontSize: '48px', marginBottom: '15px' }}>🛒</div>
                <p style={{ margin: 0, fontWeight: 'bold' }}>Aucune offre active</p>
                <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#666' }}>Créez votre première offre dans l'onglet "Vendre"</p>
              </div>
            ) : (
              <div style={marketStyles.offersList}>
                {myOffers.map((offer: any) => (
                  <div key={offer.id} style={{
                    ...marketStyles.myOfferCard,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 16px',
                    minHeight: 'auto'
                  }}>
                    <div style={marketStyles.offerSidebar}></div>
                    
                    {/* Contenu compact en 2 lignes */}
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                      flex: 1,
                      marginLeft: '10px',
                      fontSize: '12px'
                    }}>
                      {/* Ligne 1: Ressource et prix */}
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px'
                      }}>
                        <span style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          fontWeight: 'bold',
                          color: '#8B4513',
                          fontSize: '14px'
                        }}>
                          {getResourceEmoji(offer.resource_type)} {offer.quantity} {getResourceLabel(offer.resource_type)}
                        </span>
                        
                        <span style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          color: '#666'
                        }}>
                          💰 {offer.price_per_unit} or/u
                        </span>
                        
                        <span style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          fontWeight: 'bold',
                          color: '#28a745'
                        }}>
                          🪙 {offer.total_price} or
                        </span>
                      </div>
                      
                      {/* Ligne 2: Date */}
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        color: '#999',
                        fontSize: '11px'
                      }}>
                        📅 Créée le {formatDate(offer.created_at)}
                      </div>
                    </div>
                    
                    <button 
                      onClick={() => handleCancelOffer(offer.offer_id)}
                      style={{
                        ...marketStyles.cancelButton,
                        padding: '8px 12px',
                        fontSize: '11px'
                      }}
                      onMouseOver={(e) => {
                        e.currentTarget.style.background = 'linear-gradient(135deg, #C82333, #A71E2A)';
                        e.currentTarget.style.transform = 'translateY(-2px)';
                        e.currentTarget.style.boxShadow = '0 6px 16px rgba(220, 53, 69, 0.5)';
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.background = 'linear-gradient(135deg, #DC3545, #C82333)';
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(220, 53, 69, 0.4)';
                      }}
                    >
                      ❌ Annuler
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        );

      case 'vendre':
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <h4 style={{...marketStyles.sectionTitle, padding: '10px', margin: '0 0 15px 0', fontSize: '16px'}}>
              <span style={{ fontSize: '20px' }}>💰</span>
              Créer une offre de vente
            </h4>
            <div style={marketStyles.sellForm}>
              <div style={marketStyles.formField}>
                <label style={marketStyles.label}>
                  <span style={{ fontSize: '18px' }}>📦</span>
                  Ressource :
                </label>
                <select 
                  value={sellResource} 
                  onChange={(e) => setSellResource(e.target.value)}
                  style={marketStyles.input}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = '#8B4513';
                    e.currentTarget.style.boxShadow = '0 0 0 4px rgba(139, 69, 19, 0.15)';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(139, 69, 19, 0.2)';
                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.05)';
                    e.currentTarget.style.transform = 'translateY(0)';
                  }}
                >
                  {resourceTypesWithEmojis.map(resource => (
                    <option key={resource.key} value={resource.key}>{resource.label}</option>
                  ))}
                </select>
              </div>

              <div style={marketStyles.formField}>
                <label style={marketStyles.label}>
                  <span style={{ fontSize: '18px' }}>🔢</span>
                  Quantité (max: {maxResourceToSell}) :
                </label>
                <input 
                  type="number" 
                  value={sellQuantity}
                  onChange={(e) => setSellQuantity(e.target.value)}
                  min="1"
                  max={maxResourceToSell}
                  placeholder="Quantité"
                  style={marketStyles.input}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = '#8B4513';
                    e.currentTarget.style.boxShadow = '0 0 0 4px rgba(139, 69, 19, 0.15)';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(139, 69, 19, 0.2)';
                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.05)';
                    e.currentTarget.style.transform = 'translateY(0)';
                  }}
                />
              </div>

              <div style={marketStyles.formField}>
                <label style={marketStyles.label}>
                  <span style={{ fontSize: '18px' }}>🪙</span>
                  Prix par unité (or) :
                </label>
                <input 
                  type="number" 
                  value={sellPrice}
                  onChange={(e) => setSellPrice(e.target.value)}
                  min="0.1"
                  step="0.1"
                  placeholder="Prix"
                  style={marketStyles.input}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = '#8B4513';
                    e.currentTarget.style.boxShadow = '0 0 0 4px rgba(139, 69, 19, 0.15)';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(139, 69, 19, 0.2)';
                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.05)';
                    e.currentTarget.style.transform = 'translateY(0)';
                  }}
                />
              </div>

              {sellQuantity && sellPrice && (
                <div style={marketStyles.offerSummary}>
                  <div style={marketStyles.summaryIcon}>
                    💰
                  </div>
                  <div style={marketStyles.summaryRow}>
                    <span>📦 Ressource:</span>
                    <span style={{ fontWeight: 'bold' }}>{sellQuantity} {sellResource}</span>
                  </div>
                  <div style={marketStyles.summaryRow}>
                    <span>🪙 Prix total:</span>
                    <span style={{ fontWeight: 'bold', color: '#28a745' }}>{(parseInt(sellQuantity) * parseFloat(sellPrice)).toFixed(1)} or</span>
                  </div>
                  <div style={marketStyles.summaryTotal}>
                    <span>📊 Capacité:</span>
                    <span>{sellQuantity} / {marketCapabilities?.total_capacity || 0}</span>
                  </div>
                </div>
              )}

              <button 
                onClick={handleCreateOffer}
                disabled={!sellQuantity || !sellPrice || parseInt(sellQuantity) > maxResourceToSell}
                style={{
                  ...marketStyles.createOfferButton,
                  background: (!sellQuantity || !sellPrice || parseInt(sellQuantity) > maxResourceToSell) 
                    ? '#CCC' 
                    : 'linear-gradient(135deg, #8B4513, #A0522D)',
                  color: 'white',
                  cursor: (!sellQuantity || !sellPrice || parseInt(sellQuantity) > maxResourceToSell) 
                    ? 'not-allowed' 
                    : 'pointer',
                  boxShadow: (!sellQuantity || !sellPrice || parseInt(sellQuantity) > maxResourceToSell) 
                    ? 'none' 
                    : '0 8px 25px rgba(139, 69, 19, 0.4)'
                }}
                onMouseOver={(e) => {
                  if (!(!sellQuantity || !sellPrice || parseInt(sellQuantity) > maxResourceToSell)) {
                    e.currentTarget.style.background = 'linear-gradient(135deg, #A0522D, #CD853F)';
                    e.currentTarget.style.transform = 'translateY(-3px)';
                    e.currentTarget.style.boxShadow = '0 12px 35px rgba(139, 69, 19, 0.5)';
                  }
                }}
                onMouseOut={(e) => {
                  if (!(!sellQuantity || !sellPrice || parseInt(sellQuantity) > maxResourceToSell)) {
                    e.currentTarget.style.background = 'linear-gradient(135deg, #8B4513, #A0522D)';
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 8px 25px rgba(139, 69, 19, 0.4)';
                  }
                }}
              >
                <span style={{ fontSize: '20px' }}>✨</span>
                Créer l'offre
              </button>
            </div>
          </div>
        );

      case 'acheter':
        // Filtrer les offres selon le type de ressource sélectionné
        const filteredOffers = filterResource === 'all' 
          ? availableOffers 
          : availableOffers.filter(offer => offer.resource_type === filterResource);

        return (
          <div style={marketStyles.tabContainer}>
            <h4 style={{...marketStyles.sectionTitle, padding: '10px', margin: '0 0 15px 0', fontSize: '16px'}}>
              <span style={{ fontSize: '20px' }}>🛒</span>
              Offres disponibles à l'achat
            </h4>
            
            {/* Filtre par ressource */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              marginBottom: '15px',
              padding: '8px 12px',
              background: 'rgba(139, 69, 19, 0.05)',
              borderRadius: '8px',
              border: '1px solid rgba(139, 69, 19, 0.15)'
            }}>
              <span style={{
                fontSize: '14px',
                fontWeight: 'bold',
                color: '#8B4513'
              }}>🔍 Filtrer :</span>
              <select 
                value={filterResource} 
                onChange={(e) => setFilterResource(e.target.value)}
                style={{
                  ...marketStyles.input,
                  padding: '6px 10px',
                  fontSize: '12px',
                  minWidth: '200px'
                }}
              >
                <option value="all">Toutes les ressources</option>
                {resourceTypesWithEmojis.map(resource => (
                  <option key={resource.key} value={resource.key}>{resource.label}</option>
                ))}
              </select>
              <span style={{
                fontSize: '12px',
                color: '#666',
                marginLeft: 'auto'
              }}>
                {filteredOffers.length} offre(s) disponible(s)
              </span>
            </div>
            
            {!Array.isArray(filteredOffers) || filteredOffers.length === 0 ? (
              <div style={marketStyles.empty}>
                <div style={{ fontSize: '36px', marginBottom: '10px' }}>🏪</div>
                <p style={{ margin: 0, fontWeight: 'bold' }}>
                  {filterResource === 'all' ? 'Aucune offre disponible' : `Aucune offre de ${resourceTypesWithEmojis.find(r => r.key === filterResource)?.label || filterResource}`}
                </p>
                <p style={{ margin: '5px 0 0 0', fontSize: '12px', color: '#666' }}>
                  {filterResource === 'all' ? 'Revenez plus tard ou explorez d\'autres marchés' : 'Essayez un autre type de ressource'}
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '400px', overflowY: 'auto' }}>
                {filteredOffers.map((offer, index) => (
                  <div key={offer.id || index} style={{
                    background: 'linear-gradient(135deg, #fff 0%, #f8f9fa 100%)',
                    border: '2px solid rgba(139, 69, 19, 0.2)',
                    borderRadius: '8px',
                    padding: '15px',
                    transition: 'all 0.3s ease',
                    boxShadow: '0 2px 8px rgba(139, 69, 19, 0.1)',
                    position: 'relative',
                    overflow: 'hidden',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    minHeight: '60px'
                  }}>
                    <div style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '6px',
                      height: '100%',
                      background: 'linear-gradient(to bottom, #007BFF, #0056B3)'
                    }}></div>
                    
                    {/* Informations principales */}
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '6px',
                      flex: 1,
                      marginLeft: '12px'
                    }}>
                      {/* Ligne 1: Ressource et quantité */}
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}>
                        <span style={{ fontSize: '18px' }}>{getResourceEmoji(offer.resource_type)}</span>
                        <strong style={{
                          color: '#8B4513',
                          fontSize: '16px',
                          fontWeight: 'bold'
                        }}>
                          {offer.quantity} {getResourceLabel(offer.resource_type)}
                        </strong>
                      </div>
                      
                      {/* Ligne 2: Ville et Joueur */}
                      <div style={{
                        display: 'flex',
                        gap: '15px',
                        fontSize: '13px'
                      }}>
                        <span style={{
                          color: '#0066cc',
                          fontWeight: 'bold'
                        }}>
                          🏛️ {offer.seller_city_name || 'Ville inconnue'}
                        </span>
                        <span style={{
                          color: '#228B22',
                          fontWeight: 'bold'
                        }}>
                          👤 {offer.seller_player_name || 'Joueur inconnu'}
                        </span>
                      </div>
                      
                      {/* Ligne 3: Prix */}
                      <div style={{
                        display: 'flex',
                        gap: '15px',
                        fontSize: '13px'
                      }}>
                        <span style={{
                          color: '#8B4513',
                          fontWeight: 'bold'
                        }}>
                          💰 {offer.price_per_unit} or/u
                        </span>
                        <span style={{
                          color: '#28a745',
                          fontWeight: 'bold',
                          fontSize: '14px'
                        }}>
                          🪙 {offer.total_cost || (offer.quantity * offer.price_per_unit)} or
                        </span>
                      </div>
                    </div>
                    
                    {/* Bouton d'achat */}
                    <button 
                      onClick={() => handleBuyOffer(offer.id)}
                      style={{
                        padding: '8px 12px',
                        background: 'linear-gradient(135deg, #28A745, #218838)',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        cursor: 'pointer',
                        transition: 'all 0.3s ease',
                        textTransform: 'uppercase',
                        letterSpacing: '0.3px',
                        minWidth: '80px',
                        boxShadow: '0 2px 6px rgba(40, 167, 69, 0.3)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '4px'
                      }}
                      onMouseOver={(e) => {
                        e.currentTarget.style.background = 'linear-gradient(135deg, #218838, #1E7E34)';
                        e.currentTarget.style.transform = 'translateY(-1px)';
                        e.currentTarget.style.boxShadow = '0 3px 8px rgba(40, 167, 69, 0.4)';
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.background = 'linear-gradient(135deg, #28A745, #218838)';
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = '0 2px 6px rgba(40, 167, 69, 0.3)';
                      }}
                    >
                      <span style={{ fontSize: '10px' }}>💳</span>
                      Acheter
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="market-popup">
      <div className="market-header" style={marketStyles.header}>
        <h3 style={marketStyles.title}>
          🏛️ Marché - Niveau {building.level}
        </h3>
        
        <div style={marketStyles.infoContainer}>
          <div style={marketStyles.infoCard}>
            <span style={marketStyles.infoLabel}>
              🌍 Portée du marché
            </span>
            <span style={marketStyles.infoValue}>
              {marketCapabilities?.market_range || 0} unités
            </span>
            <div style={{ fontSize: '8px', color: '#888', marginTop: '1px' }}>
              Distance max pour commercer
            </div>
          </div>
          
          <div style={marketStyles.infoCard}>
            <span style={marketStyles.infoLabel}>
              📦 Capacité de vente
            </span>
            <span style={marketStyles.infoValue}>
              {marketCapabilities?.used_capacity || 0} / {marketCapabilities?.total_capacity || 0}
            </span>
          </div>
        </div>
      </div>

      <div className="market-tabs" style={marketStyles.tabs}>
        <button 
          className={`market-tab ${activeTab === 'mes-offres' ? 'active' : ''}`}
          onClick={() => setActiveTab('mes-offres')}
          style={{
            ...marketStyles.tab,
            background: activeTab === 'mes-offres' ? 'linear-gradient(to bottom, #FFF8DC, #F5F5DC)' : 'linear-gradient(to bottom, #E8E8E8, #D3D3D3)',
            borderRight: '1px solid #8B4513',
            color: activeTab === 'mes-offres' ? '#8B4513' : '#666',
            transform: activeTab === 'mes-offres' ? 'translateY(-4px)' : 'none',
            zIndex: activeTab === 'mes-offres' ? 10 : 1,
            boxShadow: activeTab === 'mes-offres' ? '0 -2px 8px rgba(139, 69, 19, 0.3)' : 'none'
          }}
        >
          Offres en cours
        </button>
        <button 
          className={`market-tab ${activeTab === 'vendre' ? 'active' : ''}`}
          onClick={() => setActiveTab('vendre')}
          style={{
            ...marketStyles.tab,
            background: activeTab === 'vendre' ? 'linear-gradient(to bottom, #FFF8DC, #F5F5DC)' : 'linear-gradient(to bottom, #E8E8E8, #D3D3D3)',
            borderRight: '1px solid #8B4513',
            color: activeTab === 'vendre' ? '#8B4513' : '#666',
            transform: activeTab === 'vendre' ? 'translateY(-4px)' : 'none',
            zIndex: activeTab === 'vendre' ? 10 : 1,
            boxShadow: activeTab === 'vendre' ? '0 -2px 8px rgba(139, 69, 19, 0.3)' : 'none'
          }}
        >
          Vendre
        </button>
        <button 
          className={`market-tab ${activeTab === 'acheter' ? 'active' : ''}`}
          onClick={() => setActiveTab('acheter')}
          style={{
            ...marketStyles.tab,
            background: activeTab === 'acheter' ? 'linear-gradient(to bottom, #FFF8DC, #F5F5DC)' : 'linear-gradient(to bottom, #E8E8E8, #D3D3D3)',
            borderRight: '2px solid #8B4513',
            color: activeTab === 'acheter' ? '#8B4513' : '#666',
            transform: activeTab === 'acheter' ? 'translateY(-4px)' : 'none',
            zIndex: activeTab === 'acheter' ? 10 : 1,
            boxShadow: activeTab === 'acheter' ? '0 -2px 8px rgba(139, 69, 19, 0.3)' : 'none'
          }}
        >
          Acheter
        </button>
      </div>

      <div className="market-content" style={marketStyles.content}>
        {renderTabContent()}
      </div>
    </div>
  );
};

export default MarketPopupContent;
