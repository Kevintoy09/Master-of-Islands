import React, { useState, useEffect } from 'react';
import { useUser } from '../hooks/useUser';
import { usePlayerResearch } from '../hooks/usePlayerResearch';
import { Slider, IconButton } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import RemoveIcon from '@mui/icons-material/Remove';

interface AcademyPopupContentProps {
  city: any; // Type à améliorer plus tard
  building: any; // Données du bâtiment académie
  onClose: () => void;
  onCityDataChange?: () => void; // Fonction pour notifier les changements
}

const AcademyPopupContent: React.FC<AcademyPopupContentProps> = ({
  city,
  building,
  onClose,
  onCityDataChange,
}) => {
  const { user } = useUser();
  const { playerResearchData, getResearchById } = usePlayerResearch();
  const [workerInput, setWorkerInput] = useState('0');
  const [researchPoints, setResearchPoints] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isUserTyping, setIsUserTyping] = useState(false); // Pour savoir si l'utilisateur tape
  
  // États locaux pour les données qui peuvent changer
  const [currentWorkers, setCurrentWorkers] = useState(0);
  const [freePopulation, setFreePopulation] = useState(0);
  
  // Données de base du bâtiment
  const buildingLevel = building?.level || 1;
  const buildingName = building?.name || 'academy';
  // Normaliser la clé pour récupérer les ouvriers (toujours en minuscule)
  const workerKey = buildingName.toLowerCase() === 'academy' ? 'academy' : buildingName;
  
  // Données calculées depuis l'effet du bâtiment (valeurs réelles)
  const maxWorkers = building?.effect?.max_workers || getMaxWorkersForLevel(buildingLevel);
  const baseResearchPointsPerWorker = building?.effect?.research_points_per_worker || getResearchPointsPerWorker(buildingLevel);
  
  // Calculer le bonus de recherche "Écriture" (+10%)
  const researchBonus = calculateResearchBonus(playerResearchData, getResearchById);
  const researchPointsPerWorker = baseResearchPointsPerWorker * researchBonus;
  const totalProductivity = currentWorkers * researchPointsPerWorker;
  
  // Initialiser les données depuis les props
  useEffect(() => {
    // Ne pas traiter si city ou workers_assigned n'est pas défini
    if (!city || !city.workers_assigned) {
      return;
    }
    
    // Pour l'académie, additionner toutes les variantes possibles (pour nettoyer les anciennes données)
    let initialWorkers = 0;
    const workerAssigned = city.workers_assigned || {};
    
    // Additionner toutes les variantes de clés d'académie qui pourraient exister
    for (const key of ['Academy', 'academy', 'ACADEMY']) {
      initialWorkers += workerAssigned[key] || 0;
    }
    
    const initialFreePopulation = city?.resources?.population_free || 0;
    
    setCurrentWorkers(initialWorkers);
    setFreePopulation(initialFreePopulation);
    
    // Ne mettre à jour l'input que si l'utilisateur n'est pas en train de taper
    if (!isUserTyping) {
      setWorkerInput(initialWorkers.toString());
    }
  }, [city?.workers_assigned, city?.resources?.population_free, isUserTyping]);

  useEffect(() => {
    loadPlayerResearchPoints();
  }, [user?.id]);

  // Mise à jour automatique des points de recherche toutes les secondes
  useEffect(() => {
    if (!user?.id) return;

    const interval = setInterval(() => {
      loadPlayerResearchPoints();
    }, 1000); // Mise à jour toutes les secondes

    return () => clearInterval(interval);
  }, [user?.id]);

  // Fonction pour récupérer les points de recherche du joueur
  const loadPlayerResearchPoints = async () => {
    if (!user?.id) return;
    
    try {
      const response = await fetch(`/api/player/${user.id}/research-points`);
      if (response.ok) {
        const data = await response.json();
        setResearchPoints(data.research_points || 0);
      }
    } catch (err) {
      console.error('Erreur chargement points de recherche:', err);
    }
  };

  // Fonction pour recharger les données de la ville
  const reloadCityData = async () => {
    if (!city?.id) return;
    
    try {
      const response = await fetch(`/api/city-state/${city.id}`);
      if (response.ok) {
        const data = await response.json();
        
        // Pour l'académie, additionner toutes les variantes possibles
        let updatedWorkers = 0;
        const workerAssigned = data.workers_assigned || {};
        for (const key of ['Academy', 'academy', 'ACADEMY']) {
          const workers = workerAssigned[key] || 0;
          updatedWorkers += workers;
        }
        
        const updatedFreePopulation = data.resources?.population_free || 0;
        
        setCurrentWorkers(updatedWorkers);
        setFreePopulation(updatedFreePopulation);
      }
    } catch (err) {
      console.error('Erreur rechargement données ville:', err);
    }
  };

  // Fonction pour assigner des ouvriers
  const assignWorkers = async () => {
    const newWorkers = parseInt(workerInput);
    
    if (isNaN(newWorkers) || newWorkers < 0) {
      setError('Nombre d\'ouvriers invalide');
      return;
    }
    
    if (newWorkers > maxWorkers) {
      setError(`Maximum ${maxWorkers} ouvriers pour ce niveau`);
      return;
    }
    
    const workerDifference = newWorkers - currentWorkers;
    if (workerDifference > freePopulation) {
      setError(`Population libre insuffisante (${freePopulation} disponible)`);
      return;
    }

    if (!user?.id) {
      setError('Vous devez être connecté');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/city/${city.id}/assign-workers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          building_type: buildingName,
          workers: newWorkers,
          player_id: user.id
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Erreur lors de l\'assignation');
      }
      
      const result = await response.json();
      
      // Mettre à jour les points de recherche si retournés
      if (result.research_points !== undefined) {
        setResearchPoints(result.research_points);
      }
      
      // Mettre à jour les données locales
      setCurrentWorkers(newWorkers);
      if (result.population_free !== undefined) {
        setFreePopulation(result.population_free);
      }
      
      // Mettre à jour l'input seulement après succès de l'assignation
      setWorkerInput(newWorkers.toString());
      setIsUserTyping(false); // L'utilisateur a fini de taper
      
      // Recharger les données de la ville et de l'utilisateur
      await loadPlayerResearchPoints();
      await reloadCityData(); // Recharger les données de la ville pour s'assurer de la cohérence
      
      // Notifier le parent pour qu'il recharge ses données
      if (onCityDataChange) {
        onCityDataChange();
      }
      
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="popup-content">
      <h3 className="popup-title">Académie - Niveau {buildingLevel}</h3>
      
      {/* Points de recherche globaux */}
      <div className="popup-section highlight">
        <div className="popup-section-title">
          📚 Points de recherche : {researchPoints.toFixed(1)}
        </div>
        <div className="popup-section-subtitle">
          Points partagés entre toutes vos villes
        </div>
      </div>

      {/* Informations population et ouvriers */}
      <div className="popup-stats-grid">
        <div>👥 Population libre : <strong>{freePopulation}</strong></div>
        <div>🏭 Capacité max : <strong>{maxWorkers} ouvriers</strong></div>
      </div>

      {/* Productivité */}
      <div className="popup-section info">
        <div><strong>Productivité :</strong></div>
        <div>
          • {researchPointsPerWorker.toFixed(1)} points/ouvrier/h
          {researchBonus > 1 && (
            <span style={{ color: '#4caf50', marginLeft: '5px' }}>
              {playerResearchData?.unlocked_research?.includes('ecriture') && (
                <>(+{((researchBonus / (playerResearchData?.faction === 'papyrus' ? 1.1 : 1) - 1) * 100).toFixed(0)}% Écriture)</>
              )}
              {playerResearchData?.faction === 'papyrus' && (
                <> (+10% Faction Papyrus)</>
              )}
            </span>
          )}
        </div>
        <div>• Production estimée : <strong>{totalProductivity.toFixed(1)} points/h</strong></div>
      </div>

      {/* Contrôle des ouvriers */}
      <div className="popup-section warning">
        <div className="popup-worker-controls">
          <div className="popup-worker-title">
            Ouvriers assignés : {currentWorkers} / {maxWorkers}
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '10px' }}>
            <IconButton
              onClick={() => {
                const newValue = Math.max(0, parseInt(workerInput) - 1);
                setWorkerInput(newValue.toString());
                setIsUserTyping(true);
              }}
              disabled={loading || parseInt(workerInput) <= 0}
              size="small"
              sx={{ color: '#ff5252' }}
            >
              <RemoveIcon />
            </IconButton>
            
            <div style={{ flex: 1 }}>
              <Slider
                value={parseInt(workerInput) || 0}
                onChange={(_, value) => {
                  setWorkerInput(value.toString());
                  setIsUserTyping(true);
                }}
                min={0}
                max={maxWorkers}
                marks
                valueLabelDisplay="auto"
                disabled={loading}
                sx={{
                  color: '#4caf50',
                  '& .MuiSlider-thumb': {
                    backgroundColor: '#fff',
                    border: '2px solid currentColor',
                  },
                  '& .MuiSlider-mark': {
                    backgroundColor: '#bfbfbf',
                  },
                  '& .MuiSlider-markActive': {
                    backgroundColor: 'currentColor',
                  },
                }}
              />
            </div>
            
            <IconButton
              onClick={() => {
                const newValue = Math.min(maxWorkers, parseInt(workerInput) + 1);
                setWorkerInput(newValue.toString());
                setIsUserTyping(true);
              }}
              disabled={loading || parseInt(workerInput) >= maxWorkers}
              size="small"
              sx={{ color: '#4caf50' }}
            >
              <AddIcon />
            </IconButton>
          </div>
          
          <div style={{ marginTop: '15px' }}>
            <button
              onClick={assignWorkers}
              disabled={loading || parseInt(workerInput) === currentWorkers}
              className="popup-action-button primary"
              style={{ width: '100%' }}
            >
              {loading ? 'Assignation...' : 'Confirmer'}
            </button>
          </div>
          
          {error && (
            <div className="popup-error-message">
              ⚠️ {error}
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="popup-actions">
        <button
          onClick={onClose}
          className="popup-action-button secondary"
        >
          Fermer
        </button>
      </div>
    </div>
  );
};

// Fonctions utilitaires (à adapter selon vos données)
function getMaxWorkersForLevel(level: number): number {
  // À adapter selon votre configuration
  const baseWorkers = 8;
  return baseWorkers + (level - 1) * 2;
}

function getResearchPointsPerWorker(level: number): number {
  // Production : 1 point par ouvrier par seconde
  return 1;
}

// Calculer le multiplicateur de bonus de recherche (Écriture = +10%)
function calculateResearchBonus(playerResearchData: any, getResearchById: any): number {
  if (!playerResearchData?.unlocked_research) return 1.0;
  
  let bonusMultiplier = 1.0;
  
  // Vérifier si "Écriture" est débloquée
  if (playerResearchData.unlocked_research.includes('ecriture')) {
    const ecritureResearch = getResearchById('ecriture');
    if (ecritureResearch?.effect?.research_points_bonus) {
      bonusMultiplier += ecritureResearch.effect.research_points_bonus / 100.0;
    }
  }
  
  // 📜 Bonus de faction papyrus : +10% productivité
  if (playerResearchData?.faction === 'papyrus') {
    bonusMultiplier *= 1.1;
  }
  
  return bonusMultiplier;
}

export default AcademyPopupContent;
