import React, { useState, useEffect } from 'react';
import { getResourceEmoji, getUIEmoji } from '../constants/resourceIcons';
import './ResourceProductionPopup.css';

interface ResourceProductionPopupProps {
  resourceKey: string;
  resourceName: string;
  currentAmount: number;
  cityId?: string;
  onClose: () => void;
}

interface ProductionDetails {
  baseProduction: number;
  buildingBonus: number;
  researchBonus: number;
  specialBonus: number;
  totalProduction: number;
  siteProduction: number;
  passiveProduction: number;
  storageCapacity: number;
}

const ResourceProductionPopup: React.FC<ResourceProductionPopupProps> = ({
  resourceKey,
  resourceName,
  currentAmount,
  cityId,
  onClose
}) => {
  const [productionDetails, setProductionDetails] = useState<ProductionDetails>({
    baseProduction: 10.0,
    buildingBonus: 0,
    researchBonus: 0,
    specialBonus: 0,
    totalProduction: 10.0,
    siteProduction: 0,
    passiveProduction: 10.0,
    storageCapacity: 10000
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Charger les détails de production
  useEffect(() => {
    loadProductionDetails();
    loadStorageCapacity();
  }, [resourceKey, cityId]);

  const loadStorageCapacity = async () => {
    if (!cityId) return;
    
    try {
      // Ajouter un timestamp pour éviter le cache
      const timestamp = Date.now();
      const response = await fetch(`/api/city/${cityId}/storage?t=${timestamp}`);
      if (response.ok) {
        const storageData = await response.json();
        const capacity = storageData.total_storage?.[resourceKey] || 0;
        
        setProductionDetails(prev => ({
          ...prev,
          storageCapacity: capacity
        }));
      }
    } catch (err) {
      console.error('Erreur lors du chargement de la capacité de stockage:', err);
    }
  };

  const loadProductionDetails = async () => {
    if (!cityId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      
      // Utiliser le nouvel endpoint de production corrigé avec anti-cache
      const timestamp = Date.now();
      const response = await fetch(`/api/city/${cityId}/production/${resourceKey}?t=${timestamp}`);
      
      if (response.ok) {
        const productionData = await response.json();
        
        setProductionDetails({
          baseProduction: productionData.baseProduction || 0,
          buildingBonus: productionData.buildingBonus || 0,
          researchBonus: productionData.researchBonus || 0,
          specialBonus: productionData.specialBonus || 0,
          totalProduction: productionData.totalProduction || 0,
          siteProduction: 0, // Inclus dans baseProduction maintenant
          passiveProduction: productionData.totalProduction || 0,
          storageCapacity: productionData.storageCapacity || 0
        });
      } else {
        const errorText = await response.text();
        setError(`Erreur API (${response.status}): ${errorText}`);
      }
    } catch (err) {
      setError(`Erreur de connexion: ${err instanceof Error ? err.message : 'Erreur inconnue'}`);
    } finally {
      setLoading(false);
    }
  };

  // Fonction pour formater les nombres de manière compacte
  const formatNumber = (num: number): string => {
    const rounded = Math.floor(num);
    if (rounded >= 1000000) {
      return (rounded / 1000000).toFixed(1) + 'M';
    } else if (rounded >= 1000) {
      return (rounded / 1000).toFixed(1) + 'K';
    } else {
      return rounded.toString();
    }
  };

  // Fonction pour expliquer les bonus de bâtiments selon la ressource
  const getBuildingBonusExplanation = (resourceKey: string, bonus: number): string => {
    switch (resourceKey) {
      case 'wood':
        return `Ce bonus provient de votre Scierie (niveau ${bonus/10}). La Scierie améliore UNIQUEMENT la production de bois.`;
      case 'stone':
      case 'iron':
      case 'cereal':
      case 'papyrus':
        // Bonus Centre de Ressources: niveau 1=10%, niveau 2=20%, niveau 3=30% (corrigé selon buildings.json)
        const level = bonus === 15 ? 1 : bonus === 25 ? 2 : bonus === 40 ? 3 : Math.ceil(bonus/15);
        return `Ce bonus provient de votre Centre de Ressources (niveau ${level}). Le Centre de Ressources améliore la production de pierre, fer, céréales et papyrus.`;
      default:
        return `Cette ressource n'est actuellement affectée par aucun bâtiment spécialisé.`;
    }
  };

  // Fonction pour recommander des bâtiments selon la ressource
  const getBuildingRecommendation = (resourceKey: string): string => {
    switch (resourceKey) {
      case 'wood':
        return `Construisez une Scierie pour améliorer la production de bois (+10/20/30% selon le niveau).`;
      case 'stone':
      case 'iron':
      case 'cereal':
      case 'papyrus':
        return `Construisez un Centre de Ressources pour améliorer la production de pierre, fer, céréales et papyrus (+15/25/40% selon le niveau).`;
      default:
        return `Cette ressource n'a pas de bâtiment spécialisé pour le moment.`;
    }
  };

  return (
    <div className="resource-popup-overlay" onClick={onClose}>
      <div className="resource-popup-content" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="resource-popup-header">
          <div className="resource-popup-title">
            {getResourceEmoji(resourceKey)} {resourceName}
          </div>
          <button className="resource-popup-close" onClick={onClose}>
            ✕
          </button>
        </div>

        {loading ? (
          <div className="resource-popup-loading">
            🔄 Chargement...
          </div>
        ) : error ? (
          <div className="resource-popup-error">
            ⚠️ {error}
          </div>
        ) : (
          <>
            {/* Quantité actuelle */}
            <div className="resource-popup-section">
              <div className="resource-popup-current">
                <div className="resource-popup-amount">
                  {Math.floor(currentAmount).toLocaleString('fr-FR')}
                </div>
                <div className="resource-popup-capacity">
                  Capacité de stockage : {formatNumber(productionDetails.storageCapacity)}
                </div>
              </div>
            </div>

            {/* Détail de la production */}
            <div className="resource-popup-section">
              <div className="resource-popup-section-title">
                {getUIEmoji('stats')} Détail de la production
              </div>
              
              <div className="resource-popup-production-list">
                <div className="resource-popup-production-item base">
                  <span>Production passive de base :</span>
                  <span>{productionDetails.baseProduction.toFixed(1)}/heure</span>
                </div>
                
                <div className={`resource-popup-production-item ${productionDetails.buildingBonus > 0 ? 'bonus' : 'neutral'}`}>
                  <span>+ Bonus bâtiment :</span>
                  <span>+{productionDetails.buildingBonus}%</span>
                </div>
                
                {productionDetails.researchBonus > 0 ? (
                  <div className="resource-popup-production-item bonus">
                    <span>+ Bonus recherche :</span>
                    <span>+{productionDetails.researchBonus}%</span>
                  </div>
                ) : (
                  <div className="resource-popup-production-item neutral">
                    <span>+ Bonus recherche :</span>
                    <span>+0%</span>
                  </div>
                )}
                
                {productionDetails.specialBonus > 0 ? (
                  <div className="resource-popup-production-item bonus">
                    <span>+ Bonus spécial :</span>
                    <span>+{productionDetails.specialBonus}%</span>
                  </div>
                ) : (
                  <div className="resource-popup-production-item neutral">
                    <span>+ Bonus spécial :</span>
                    <span>+0%</span>
                  </div>
                )}
                
                <div className="resource-popup-production-divider">
                  <span>Sous-total (production passive) :</span>
                  <span>{productionDetails.passiveProduction.toFixed(1)}/heure</span>
                </div>
                
                {productionDetails.siteProduction > 0 && (
                  <div className="resource-popup-production-item site">
                    <span>+ Production des sites (ouvriers) :</span>
                    <span>+{productionDetails.siteProduction.toFixed(1)}/heure</span>
                  </div>
                )}
              </div>

              {/* Total */}
              <div className="resource-popup-total">
                <div className="resource-popup-total-line">
                  <span>Total :</span>
                  <span>{productionDetails.totalProduction.toFixed(1)}/heure</span>
                </div>
              </div>
            </div>

            {/* Informations supplémentaires */}
            <div className="resource-popup-section info">
              <div className="resource-popup-info-title">
                💡 Sources de bonus
              </div>
              <div className="resource-popup-info-text">
                {productionDetails.buildingBonus > 0 ? (
                  <>
                    <strong>Bonus bâtiment actuel : +{productionDetails.buildingBonus}%</strong><br/>
                    {getBuildingBonusExplanation(resourceKey, productionDetails.buildingBonus)}
                  </>
                ) : (
                  <>
                    <strong>Aucun bonus bâtiment actuel</strong><br/>
                    {getBuildingRecommendation(resourceKey)}
                  </>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ResourceProductionPopup;
