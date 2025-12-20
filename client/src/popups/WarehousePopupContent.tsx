import React, { useState, useEffect } from 'react';
import { getResourceEmoji } from '../constants/resourceIcons';
import './WarehousePopupContent.css';

interface WarehousePopupContentProps {
  city: any;
  building: any;
  onClose: () => void;
  onCityDataChange?: () => void;
}

interface StorageData {
  total_storage: Record<string, number>;
  secure_storage: Record<string, number>;
  current_resources: Record<string, number>;
}

const WarehousePopupContent: React.FC<WarehousePopupContentProps> = ({
  city,
  building,
  onClose,
  onCityDataChange,
}) => {
  const [storageData, setStorageData] = useState<StorageData | null>(null);
  const [loading, setLoading] = useState(true);

  // Récupérer les données de stockage depuis l'API
  useEffect(() => {
    const fetchStorageData = async () => {
      try {
        const response = await fetch(`/api/city/${city.id}/storage`);
        const data = await response.json();
        setStorageData(data);
        setLoading(false);
      } catch (error) {
        console.error('Erreur lors du chargement des données de stockage:', error);
        setLoading(false);
      }
    };

    if (city?.id) {
      fetchStorageData();
    }
  }, [city?.id]);

  // Récupérer les entrepôts depuis les bâtiments de la ville
  const cityBuildings = city?.buildings || [];
  const warehouses = cityBuildings.filter((building: any) => building.name === 'Entrepôt');
  const totalWarehouses = warehouses.length;
  const maxWarehouses = 4;

  // Fonction pour formater les nombres de manière compacte
  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    } else {
      return Math.floor(num).toString();
    }
  };

  // Fonction pour obtenir l'emoji de la ressource
  const getResourceEmoji = (resource: string) => {
    const emojis: Record<string, string> = {
      wood: '🪵', stone: '🪨', iron: '⚙️', cereal: '🌾', papyrus: '📜',
      wine: '�', marble: '🏛️', horse: '🐎', glass: '🪟',
      gunpowder: '💥', coal: '⚫', cotton: '🌸', spices: '🌶️'
    };
    return emojis[resource] || '📦';
  };

  // Fonction pour traduire le nom de la ressource
  const translateResource = (resource: string) => {
    const translations: Record<string, string> = {
      wood: 'Bois', stone: 'Pierre', iron: 'Fer', cereal: 'Céréales', papyrus: 'Papyrus',
      wine: 'Vin', marble: 'Marbre', horse: 'Chevaux', glass: 'Verre',
      gunpowder: 'Poudre', coal: 'Charbon', cotton: 'Coton', spices: 'Épices'
    };
    return translations[resource] || resource;
  };

  // Catégoriser les ressources
  const categorizeResources = (resources: Record<string, number>) => {
    const basic = ['wood', 'stone', 'iron', 'cereal', 'papyrus'];
    const advanced = ['wine', 'marble', 'horse', 'glass'];
    const rare = ['gunpowder', 'coal', 'cotton', 'spices'];

    return {
      basic: basic.filter(r => resources[r] !== undefined),
      advanced: advanced.filter(r => resources[r] !== undefined),
      rare: rare.filter(r => resources[r] !== undefined)
    };
  };

  if (loading) {
    return (
      <div className="popup-content">
        <div className="warehouse-header">
          <h3>📦 Entrepôt - Niveau {building.level}</h3>
        </div>
        <div className="warehouse-loading">
          <p>Chargement des données de stockage...</p>
        </div>
        <div className="warehouse-actions">
          <button onClick={onClose} className="btn-close">Fermer</button>
        </div>
      </div>
    );
  }

  const categories = storageData ? categorizeResources(storageData.total_storage) : { basic: [], advanced: [], rare: [] };

  return (
    <div className="popup-content warehouse-popup">
      {/* En-tête */}
      <div className="warehouse-header">
        <h3>📦 Entrepôt - Niveau {building.level}</h3>
        <div className="warehouse-summary">
          <div>Entrepôts construits : {totalWarehouses} / {maxWarehouses}</div>
          <div>Capacité totale : {storageData ? formatNumber(Object.values(storageData.total_storage).reduce((a, b) => a + b, 0)) : '...'}</div>
        </div>
      </div>

      {/* Liste des entrepôts */}
      {warehouses.length > 0 && (
        <div className="warehouse-section">
          <h4>🏗️ Entrepôts de la ville</h4>
          <div className="warehouse-list">
            {warehouses.map((warehouse: any, index: number) => (
              <div key={index} className="warehouse-item">
                📦 Entrepôt {index + 1} - Niveau {warehouse.level}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Capacités de stockage sous forme de tableau */}
      {storageData && (
        <div className="warehouse-section">
          <h4>📊 Capacités de stockage</h4>
          
          <div className="storage-table-container">
            <table className="storage-table compact mobile-optimized"
                   style={{fontSize: window.innerWidth < 768 ? '1.05em' : '1em'}}>
              <thead>
                <tr>
                  <th>Res.</th>
                  <th>Act.</th>
                  <th>Séc.</th>
                  <th>Pill.</th>
                  <th>Max</th>
                </tr>
              </thead>
              <tbody>
                {/* Ressources de base */}
                {categories.basic.map(resource => {
                  const current = storageData.current_resources[resource] || 0;
                  const secure = storageData.secure_storage[resource] || 0;
                  const canBePillaged = Math.max(0, current - secure);
                  const maxCapacity = storageData.total_storage[resource];
                  
                  return (
                    <tr key={resource} className="resource-row basic">
                      <td className="resource-name">
                        {getResourceEmoji(resource)}
                      </td>
                      <td className="current-amount">
                        {formatNumber(current)}
                      </td>
                      <td className="secure-amount">
                        {formatNumber(secure)}
                      </td>
                      <td className="pillage-amount">
                        {formatNumber(canBePillaged)}
                      </td>
                      <td className="max-capacity">
                        {formatNumber(maxCapacity)}
                      </td>
                    </tr>
                  );
                })}
                
                {/* Ressources avancées */}
                {categories.advanced.map(resource => {
                  const current = storageData.current_resources[resource] || 0;
                  const secure = storageData.secure_storage[resource] || 0;
                  const canBePillaged = Math.max(0, current - secure);
                  const maxCapacity = storageData.total_storage[resource];
                  
                  return (
                    <tr key={resource} className="resource-row advanced">
                      <td className="resource-name">
                        {getResourceEmoji(resource)}
                      </td>
                      <td className="current-amount">
                        {formatNumber(current)}
                      </td>
                      <td className="secure-amount">
                        {formatNumber(secure)}
                      </td>
                      <td className="pillage-amount">
                        {formatNumber(canBePillaged)}
                      </td>
                      <td className="max-capacity">
                        {formatNumber(maxCapacity)}
                      </td>
                    </tr>
                  );
                })}
                
                {/* Ressources rares */}
                {categories.rare.map(resource => {
                  const current = storageData.current_resources[resource] || 0;
                  const secure = storageData.secure_storage[resource] || 0;
                  const canBePillaged = Math.max(0, current - secure);
                  const maxCapacity = storageData.total_storage[resource];
                  
                  return (
                    <tr key={resource} className="resource-row rare">
                      <td className="resource-name">
                        {getResourceEmoji(resource)}
                      </td>
                      <td className="current-amount">
                        {formatNumber(current)}
                      </td>
                      <td className="secure-amount">
                        {formatNumber(secure)}
                      </td>
                      <td className="pillage-amount">
                        {formatNumber(canBePillaged)}
                      </td>
                      <td className="max-capacity">
                        {formatNumber(maxCapacity)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Informations */}
      <div className="warehouse-section">
        <h4>💡 Informations</h4>
        <div className="warehouse-info">
          <p>🔒 <strong>Stockage sécurisé :</strong> Ces ressources ne peuvent pas être pillées lors d'attaques.</p>
          <p>📈 <strong>Amélioration :</strong> Construisez plus d'entrepôts ou améliorez-les pour augmenter vos capacités.</p>
          <p>⚠️ <strong>Limite :</strong> Vous ne pouvez pas dépasser la capacité de stockage disponible.</p>
        </div>
      </div>

      {/* Actions */}
      <div className="warehouse-actions">
        <button onClick={onClose} className="btn-close">Fermer</button>
      </div>
    </div>
  );
};

export default WarehousePopupContent;
