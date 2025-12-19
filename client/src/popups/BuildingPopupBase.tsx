
import React, { useEffect, useState } from "react";
import { RESOURCE_EMOJIS } from "../constants/resourceIcons";
import { formatTime } from "../utils/timeUtils";

interface BuildingPopupBaseProps {
  title?: string; // Titre pour l'affichage en haut
  description?: string;
  cost?: Record<string, number>;
  originalCost?: Record<string, number>;
  constructionTime?: number;
  level?: number;
  effectsCurrent?: Record<string, number>; // Changé en objet pour le tableau
  effectsNext?: Record<string, number>; // Changé en objet pour le tableau
  timer?: number; // secondes restantes
  onDevelop?: () => void;
  onDestroy?: () => void;
  destroyButtonText?: string; // Texte personnalisé pour le bouton de destruction
  onFinishInstant?: () => void;
  canFinishInstant?: boolean;
  onClose: () => void;
  error?: string;
  children?: React.ReactNode;
}



// Fonction pour traduire les noms d'effets en français
const translateEffectName = (effectName: string): string => {
  const translations: Record<string, string> = {
    'food_capacity': 'Capacité nourriture',
    'population_capacity': 'Capacité population',
    'population_growth': 'Croissance population',
    'wood_production': 'Production bois',
    'stone_production': 'Production pierre',
    'iron_production': 'Production fer',
    'cereal_production': 'Production céréales',
    'wine_production': 'Production vin',
    'marble_production': 'Production marbre',
    'glass_production': 'Production verre',
    'horses_production': 'Production chevaux',
    'research_production': 'Production recherche',
    'construction_time_reduction': 'Réduction temps construction',
    'satisfaction_bonus': 'Bonus satisfaction',
    'trade_bonus': 'Bonus commerce',
    'defense_bonus': 'Bonus défense'
  };
  return translations[effectName] || effectName;
};

// Fonction pour créer le tableau comparatif des effets
const createEffectsTable = (effectsCurrent?: Record<string, number>, effectsNext?: Record<string, number>) => {
  if (!effectsCurrent && !effectsNext) return null;

  // Combiner toutes les clés d'effets
  const allEffectKeys = new Set([
    ...(effectsCurrent ? Object.keys(effectsCurrent) : []),
    ...(effectsNext ? Object.keys(effectsNext) : [])
  ]);

  if (allEffectKeys.size === 0) return null;

  return (
    <div className="popup-effects-table">
      <div className="popup-effects-table-header">
        <div className="popup-effects-table-title"><b>Effets</b></div>
        <div className="popup-effects-table-current"><b>Niv. actuel</b></div>
        <div className="popup-effects-table-next"><b>Niv. suivant</b></div>
      </div>
      {Array.from(allEffectKeys).map(effectKey => (
        <div key={effectKey} className="popup-effects-table-row">
          <div className="popup-effects-table-name">{translateEffectName(effectKey)}</div>
          <div className="popup-effects-table-current-value">
            {effectsCurrent?.[effectKey] !== undefined ? 
              (typeof effectsCurrent[effectKey] === 'object' ? 
                JSON.stringify(effectsCurrent[effectKey]) : 
                effectsCurrent[effectKey]
              ) : '-'
            }
          </div>
          <div className="popup-effects-table-next-value">
            {effectsNext?.[effectKey] !== undefined ? 
              (typeof effectsNext[effectKey] === 'object' ? 
                JSON.stringify(effectsNext[effectKey]) : 
                effectsNext[effectKey]
              ) : '-'
            }
          </div>
        </div>
      ))}
    </div>
  );
};

// Fonction pour formater les coûts avec émojis
const formatCostWithEmojis = (cost: Record<string, number>) => {
  return Object.entries(cost).map(([res, val]) => 
    `${RESOURCE_EMOJIS[res] || res} : ${val}`
  ).join(' | ');
};

const BuildingPopupBase: React.FC<BuildingPopupBaseProps> = ({
  title, description, cost, originalCost, constructionTime, level, effectsCurrent, effectsNext, timer,
  onDevelop, onDestroy, destroyButtonText, onFinishInstant, canFinishInstant, onClose, error, children
}) => {
  const [secLeft, setSecLeft] = useState(timer || 0);
  const [isDetailsCollapsed, setIsDetailsCollapsed] = useState(true); // Réduit par défaut

  useEffect(() => {
    setSecLeft(timer || 0);
    if (timer && timer > 0) {
      const interval = setInterval(() => setSecLeft(s => (s > 0 ? s - 1 : 0)), 1000);
      return () => clearInterval(interval);
    }
  }, [timer]);

  return (
    <div className="popup-overlay" onClick={onClose}>
      <div className="popup-base" onClick={(e) => e.stopPropagation()}>
        <button onClick={onClose} className="popup-close-button">×</button>
        {error && (
          <div className="popup-error">{error}</div>
        )}

        {/* Titre centré en haut */}
        {title && (
          <div className="popup-title-centered">
            <h3>{title}</h3>
          </div>
        )}

        {/* Informations alignées à gauche */}
        {(description || typeof level === 'number') && (
          <div className="popup-info-left">
            {description && <div className="popup-description">{description}</div>}
            {typeof level === 'number' && (
              <div className="popup-level" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <b>Niveau : {level}</b>
                {/* Bouton de réduction/agrandissement */}
                {(effectsCurrent || effectsNext || cost || constructionTime !== undefined) && (
                  <button 
                    onClick={() => setIsDetailsCollapsed(!isDetailsCollapsed)}
                    style={{
                      background: 'none',
                      border: '1px solid #ccc',
                      borderRadius: '4px',
                      padding: '4px 8px',
                      cursor: 'pointer',
                      fontSize: '0.9em'
                    }}
                    title={isDetailsCollapsed ? "Afficher les détails" : "Masquer les détails"}
                  >
                    {isDetailsCollapsed ? '📊 Détails ▼' : '📊 Détails ▲'}
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* Timer si en construction */}
        {typeof secLeft === 'number' && timer !== undefined && timer > 0 && (
          <div className="popup-timer">Temps restant : {formatTime(secLeft)}</div>
        )}

        {/* Section détails (collapsible) */}
        {!isDetailsCollapsed && (
          <>
            {/* Tableau comparatif des effets */}
            {createEffectsTable(effectsCurrent, effectsNext)}

            {/* Coût et temps de construction regroupés */}
            {(cost || constructionTime !== undefined) && (
              <div className="popup-cost-construction">
                {cost && (
                  <div className="popup-cost">
                    <b>Coût :</b> {formatCostWithEmojis(cost)}
                    {originalCost && JSON.stringify(originalCost) !== JSON.stringify(cost) && (
                      <span style={{color: '#888', fontSize: '0.9em', marginLeft: '8px'}}>
                        (original: {formatCostWithEmojis(originalCost)})
                      </span>
                    )}
                  </div>
                )}
                {constructionTime !== undefined && (
                  <div className="popup-construction-time">
                    <b>Temps de construction :</b> {constructionTime}s
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* Boutons d'action */}
        {(onDevelop || onDestroy || onFinishInstant) && (
          <div className="popup-buttons">
            {onDevelop && <button onClick={onDevelop} className="popup-button">Développer</button>}
            {onDestroy && <button onClick={onDestroy} className="popup-button destroy">{destroyButtonText || "Détruire"}</button>}
            {onFinishInstant && <button onClick={onFinishInstant} className="popup-button instant" disabled={!canFinishInstant}>Terminer instantanément</button>}
          </div>
        )}

        {/* Contenu additionnel */}
        <div>
          {children}
        </div>
      </div>
    </div>
  );
};

export default BuildingPopupBase;
