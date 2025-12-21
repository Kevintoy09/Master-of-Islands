/**
 * TUTORIAL_OVERLAY.TSX - Composant Principal du Tutoriel
 * 
 * RÔLE:
 *   Affiche l'overlay interactif du tutoriel par-dessus l'interface du jeu.
 *   Gère la progression, la validation et les récompenses.
 * 
 * RESPONSABILITÉS:
 *   1. Affichage de l'étape actuelle (titre, description, spotlight)
 *   2. Positionnement intelligent de la tooltip (évite les bords de l'écran)
 *   3. Gestion du spotlight (surbrillance de l'élément cible)
 *   4. Validation des actions du joueur (click, api_check, path_check)
 *   5. Appel API pour créditer les récompenses (/api/tutorial/complete)
 *   6. Persistance de la progression (rechargement de page)
 *   7. Navigation automatique entre les pages (World → Island → City)
 * 
 * SYSTÈME DE VALIDATION:
 *   - 'manual' : Bouton "Suivant" (pas de validation automatique)
 *   - 'click' : Attend que le joueur clique sur l'élément target
 *   - 'api_check' : Interroge l'API avec apiCondition (ex: recherche débloquée)
 *   - 'element_exists' : Attend qu'un élément apparaisse dans le DOM
 *   - 'path_check' : Vérifie que le joueur est sur la bonne page (pathname)
 * 
 * SYSTÈME DE SPOTLIGHT:
 *   - Crée un effet de surbrillance autour de l'élément cible
 *   - Overlay sombre avec découpe transparente (clip-path)
 *   - Tooltip positionnée intelligemment (top, bottom, left, right, center)
 *   - Recalcul automatique lors du scroll/resize
 * 
 * Z-INDEX ARCHITECTURE:
 *   - Overlay de base : 2147483647 (max CSS)
 *   - Tooltip : 2147483648 (!important)
 *   - Bouton minimiser : 2147483649 (!important)
 *   - Garantit que le tutoriel est TOUJOURS visible par-dessus tout
 * 
 * GESTION DES RÉCOMPENSES:
 *   1. Validation de l'action → actionCompleted = true
 *   2. Bouton "Suivant" cliqué
 *   3. POST /api/tutorial/complete { player_id, step_id, reward }
 *   4. Backend crédite les récompenses
 *   5. Passage à l'étape suivante
 * 
 * NAVIGATION MULTI-PAGES:
 *   - WorldPage (étapes 0-2) : Sélection de l'île
 *   - IslandPage (étapes 3-5) : Vue de l'île, ressources
 *   - CityPage (étapes 6+) : Construction, recherche, production
 *   - Navigation automatique via path_check + bouton "Suivant"
 * 
 * ÉTAT LOCAL:
 *   - currentStepIndex : Index de l'étape actuelle (0-12)
 *   - spotlightRect : Position de l'élément surligné
 *   - tooltipPosition : Position de la tooltip
 *   - actionCompleted : Validation de l'action en cours
 *   - isMinimized : Tutoriel minimisé (petit badge)
 *   - isLoading : Chargement de la progression depuis l'API
 * 
 * HOOKS UTILISÉS:
 *   - useEffect : Validation automatique, chargement progression, spotlight
 *   - useRef : Persistance des valeurs entre renders (wasActionCompletedRef, playerIdRef)
 *   - useState : Gestion de l'état du tutoriel
 * 
 * POINTS CLÉS:
 *   - Rechargement de page : Le tutoriel reprend automatiquement (via API)
 *   - Double validation : Frontend vérifie, Backend confirme et crédite
 *   - Spotlight dynamique : Suit l'élément cible même si la page bouge
 *   - Auto-minimisation : Bouton pour masquer temporairement
 * 
 * OPTIMISATIONS:
 *   - Debounce sur les recalculs de position (resize/scroll)
 *   - Cleanup des event listeners (évite les fuites mémoire)
 *   - Refs pour éviter les validations multiples
 * 
 * HISTORIQUE:
 *   - Ajout du système de validation automatique (api_check, path_check)
 *   - Z-index à 2147483647 pour garantir la visibilité
 *   - Support des étapes multi-pages (World → Island → City)
 *   - Auto-minimisation pendant les actions longues
 *   - Persistance de progression complète
 */

import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';
import { useNavigate, useLocation } from 'react-router-dom';
import { tutorialSteps, getTutorialStep, getNextTutorialStep, TutorialStep } from '../config/tutorialSteps';
import '../styles/tutorial.css';

interface TutorialOverlayProps {
  playerId: string | number;
  onComplete: () => void;
  onSkip: () => void;
}

const TutorialOverlay: React.FC<TutorialOverlayProps> = ({ playerId, onComplete, onSkip }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [spotlightRect, setSpotlightRect] = useState<DOMRect | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ 
    top: window.innerHeight / 2 - 200, 
    left: window.innerWidth / 2 - 250 
  });
  const [actionCompleted, setActionCompleted] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const location = useLocation();
  const tooltipRef = useRef<HTMLDivElement>(null);
  const wasActionCompletedRef = useRef(false);
  const playerIdRef = useRef(playerId); // Stocker playerId dans une ref pour validation API

  // Charger la progression au montage
  useEffect(() => {
    const loadProgress = async () => {
      try {
        const response = await fetch(`/api/tutorial/status/${playerId}`);
        const data = await response.json();
        if (data.current_step) {
          const stepIndex = tutorialSteps.findIndex(s => s.id === data.current_step);
          if (stepIndex !== -1) {
            setCurrentStepIndex(stepIndex);
          }
        }
      } catch (error) {
        console.error('Erreur chargement progression tutoriel:', error);
      } finally {
        setIsLoading(false);
      }
    };
    loadProgress();
  }, [playerId]);

  const currentStep = tutorialSteps[currentStepIndex];
  const progress = ((currentStepIndex + 1) / tutorialSteps.length) * 100;

  // Vérifier si on est sur la bonne page
  const isOnCorrectPage = !currentStep.page || location.pathname === currentStep.page;

  // Auto-minimiser au chargement d'une étape nécessitant une action
  useEffect(() => {
    // Toujours maximiser la première étape (bienvenue)
    if (currentStepIndex === 0) {
      setIsMinimized(false);
    } else if (currentStep.validation) {
      // Étape nécessitant une action du joueur -> minimiser pour laisser place
      setIsMinimized(true);
    } else {
      // Étape informative -> maximiser pour afficher le message
      setIsMinimized(false);
    }
  }, [currentStepIndex, currentStep]);

  // Maximiser automatiquement quand l'action est accomplie
  useEffect(() => {
    if (actionCompleted && !wasActionCompletedRef.current && isMinimized) {
      // L'action vient d'être accomplie et le tutoriel est minimisé
      setIsMinimized(false);
      // Optionnel : notification sonore ou visuelle
    }
    wasActionCompletedRef.current = actionCompleted;
  }, [actionCompleted, isMinimized]);

  // Validation automatique de l'action
  useEffect(() => {
    if (!currentStep.validation || !isOnCorrectPage) {
      setActionCompleted(false);
      wasActionCompletedRef.current = false;
      return;
    }

    const checkValidation = () => {
      const validation = currentStep.validation!;

      switch (validation.type) {
        case 'element_exists':
          // Vérifier si l'élément existe dans le DOM
          if (validation.target) {
            const element = document.querySelector(validation.target);
            if (element) {
              setActionCompleted(true);
            }
          }
          break;

        case 'click':
          // Attendre qu'un clic soit détecté sur l'élément cible
          if (validation.target) {
            const element = document.querySelector(validation.target);
            if (element) {
              const handleClick = () => {
                setActionCompleted(true);
                element.removeEventListener('click', handleClick);
              };
              element.addEventListener('click', handleClick);
              return () => element.removeEventListener('click', handleClick);
            }
          }
          break;

        case 'api_check':
          // Vérifier via un appel API
          if (validation.apiEndpoint && validation.apiCondition) {
            // Construire l'URL avec playerId si nécessaire
            let apiUrl = validation.apiEndpoint;
            if (apiUrl.includes('/player') && !apiUrl.includes(playerIdRef.current as string)) {
              apiUrl = `${apiUrl}/${playerIdRef.current}`;
            }
            
            fetch(apiUrl)
              .then(res => res.json())
              .then(data => {
                // Passer playerId à la condition de validation
                if (validation.apiCondition!(data, playerIdRef.current as string)) {
                  setActionCompleted(true);
                }
              })
              .catch(console.error);
          }
          break;

        case 'path_check':
          // Vérifier le pathname actuel
          if (validation.pathPattern) {
            if (validation.pathPattern.test(location.pathname)) {
              setActionCompleted(true);
            }
          }
          break;

        case 'manual':
        default:
          // Validation manuelle par le bouton
          setActionCompleted(false);
          break;
      }
    };

    // Vérifier immédiatement
    checkValidation();

    // Revérifier périodiquement pour element_exists, api_check et path_check
    if (currentStep.validation.type === 'element_exists' || currentStep.validation.type === 'api_check' || currentStep.validation.type === 'path_check') {
      const interval = setInterval(checkValidation, 500);
      return () => clearInterval(interval);
    }
  }, [currentStep, isOnCorrectPage, location.pathname]);

  // Mettre à jour le spotlight quand l'étape change
  useEffect(() => {
    if (!currentStep) return;

    // Si on n'est pas sur la bonne page, ne pas chercher l'élément
    if (!isOnCorrectPage) {
      setSpotlightRect(null);
      return;
    }

    // Trouver l'élément ciblé
    if (currentStep.target) {
      const updateSpotlight = () => {
        const targetElement = document.querySelector(currentStep.target!);
        if (targetElement) {
          const rect = targetElement.getBoundingClientRect();
          setSpotlightRect(rect);
        } else {
          setSpotlightRect(null);
        }
      };

      // Attendre que le DOM soit prêt
      setTimeout(updateSpotlight, 300);

      // Observer les changements de taille
      const resizeObserver = new ResizeObserver(updateSpotlight);
      if (document.body) {
        resizeObserver.observe(document.body);
      }

      return () => resizeObserver.disconnect();
    } else {
      setSpotlightRect(null);
    }
  }, [currentStep, location.pathname, isOnCorrectPage]);

  // Calculer la position du tooltip
  useEffect(() => {
    if (!tooltipRef.current) return;

    const calculatePosition = () => {
      if (!tooltipRef.current) return;
      
      const tooltipRect = tooltipRef.current.getBoundingClientRect();
      let top = 0;
      let left = 0;

      if (currentStep.position === 'center' || !spotlightRect) {
        // Centré
        top = window.innerHeight / 2 - tooltipRect.height / 2;
        left = window.innerWidth / 2 - tooltipRect.width / 2;
      } else if (spotlightRect) {
      // Positionner selon l'élément ciblé
      const spacing = 20;

      switch (currentStep.position) {
        case 'top':
          top = spotlightRect.top - tooltipRect.height - spacing;
          left = spotlightRect.left + spotlightRect.width / 2 - tooltipRect.width / 2;
          break;
        case 'bottom':
          top = spotlightRect.bottom + spacing;
          left = spotlightRect.left + spotlightRect.width / 2 - tooltipRect.width / 2;
          break;
        case 'left':
          top = spotlightRect.top + spotlightRect.height / 2 - tooltipRect.height / 2;
          left = spotlightRect.left - tooltipRect.width - spacing;
          break;
        case 'right':
          top = spotlightRect.top + spotlightRect.height / 2 - tooltipRect.height / 2;
          left = spotlightRect.right + spacing;
          break;
      }

        // Ajuster si hors écran
        if (top < 10) top = 10;
        if (left < 10) left = 10;
        if (top + tooltipRect.height > window.innerHeight - 10) {
          top = window.innerHeight - tooltipRect.height - 10;
        }
        if (left + tooltipRect.width > window.innerWidth - 10) {
          left = window.innerWidth - tooltipRect.width - 10;
        }
      }

      setTooltipPosition({ top, left });
    };

    // Calculer immédiatement
    calculatePosition();
    
    // Recalculer après un court délai pour s'assurer que le DOM est complètement rendu
    const timer = setTimeout(calculatePosition, 100);
    
    return () => clearTimeout(timer);
  }, [spotlightRect, currentStep, tooltipRef]);

  // Gestion du drag (souris + tactile)
  useEffect(() => {
    if (!isDragging) return;

    const handleMove = (clientX: number, clientY: number) => {
      if (tooltipRef.current) {
        const newLeft = clientX - dragOffset.x;
        const newTop = clientY - dragOffset.y;
        
        // Limites de l'écran
        const maxLeft = window.innerWidth - tooltipRef.current.offsetWidth - 10;
        const maxTop = window.innerHeight - tooltipRef.current.offsetHeight - 10;
        
        setTooltipPosition({
          left: Math.max(10, Math.min(newLeft, maxLeft)),
          top: Math.max(10, Math.min(newTop, maxTop))
        });
      }
    };

    const handleMouseMove = (e: MouseEvent) => {
      handleMove(e.clientX, e.clientY);
    };

    const handleTouchMove = (e: TouchEvent) => {
      if (e.touches.length > 0) {
        handleMove(e.touches[0].clientX, e.touches[0].clientY);
      }
    };

    const handleEnd = () => {
      setIsDragging(false);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleEnd);
    window.addEventListener('touchmove', handleTouchMove, { passive: false });
    window.addEventListener('touchend', handleEnd);
    
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleEnd);
      window.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('touchend', handleEnd);
    };
  }, [isDragging, dragOffset]);

  // Afficher un loader pendant le chargement
  if (isLoading) {
    return (
      <div className="tutorial-overlay" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ background: 'white', padding: '30px', borderRadius: '10px', textAlign: 'center' }}>
          <div style={{ fontSize: '24px', marginBottom: '10px' }}>⏳</div>
          <div>Chargement du tutoriel...</div>
        </div>
      </div>
    );
  }

  // Attribuer la récompense et passer à l'étape suivante
  const handleNext = async () => {
    if (!currentStep) return;

    // Vérifier si l'action est requise et complétée
    if (currentStep.validation && currentStep.validation.type !== 'manual' && !actionCompleted) {
      // Minimiser automatiquement le tutoriel pour montrer au joueur quoi faire
      setIsMinimized(true);
      return;
    }

    // Enregistrer la progression et attribuer la récompense
    try {
      const response = await fetch(`/api/tutorial/complete-step`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_id: playerId,
          step_id: currentStep.id,
          reward: currentStep.reward
        })
      });

      if (!response.ok) {
        console.error('Erreur lors de la validation de l\'étape');
      }
    } catch (error) {
      console.error('Erreur réseau:', error);
    }

    // Réinitialiser actionCompleted pour la prochaine étape
    setActionCompleted(false);

    // Passer à l'étape suivante
    if (currentStepIndex < tutorialSteps.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
    } else {
      // Tutoriel terminé
      await completeTutorial();
    }
  };

  // Terminer le tutoriel
  const completeTutorial = async () => {
    try {
      await fetch(`/api/tutorial/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_id: playerId })
      });
    } catch (error) {
      console.error('Erreur lors de la finalisation du tutoriel:', error);
    }

    onComplete();
  };

  // Passer le tutoriel
  const handleSkip = async () => {
    if (window.confirm('Es-tu sûr de vouloir passer le tutoriel ? Tu perdras toutes les récompenses !')) {
      try {
        await fetch(`/api/tutorial/skip`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ player_id: playerId })
        });
      } catch (error) {
        console.error('Erreur lors de l\'annulation du tutoriel:', error);
      }

      onSkip();
    }
  };

  const handlePrevious = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(currentStepIndex - 1);
      setActionCompleted(false);
    }
  };

  // Fonction pour obtenir l'icône de ressource
  const getResourceIcon = (resource: string): string => {
    const icons: Record<string, string> = {
      wood: '🪵',
      stone: '🪨',
      gold: '🪙',
      papyrus: '📜',
      cereal: '🌾',
      iron: '⚙️',
      research_points: '🔬',
      sword: '⚔️',
      archer: '🏹',
      spear: '🗡️'
    };
    return icons[resource] || '📦';
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('.tutorial-header')) {
      setIsDragging(true);
      setDragOffset({
        x: e.clientX - tooltipPosition.left,
        y: e.clientY - tooltipPosition.top
      });
    }
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    if ((e.target as HTMLElement).closest('.tutorial-header') && e.touches.length > 0) {
      setIsDragging(true);
      setDragOffset({
        x: e.touches[0].clientX - tooltipPosition.left,
        y: e.touches[0].clientY - tooltipPosition.top
      });
    }
  };

  if (!currentStep) return null;

  // Mode minimisé : bouton compact dans la bottombar (à droite des diamants)
  if (isMinimized) {
    const container = document.getElementById('tutorial-minimized-container');
    
    // Si le conteneur n'existe pas encore, afficher un fallback en position fixe
    if (!container) {
      return (
        <button 
          className="tutorial-minimized-bottombar tutorial-minimized-fallback"
          onClick={() => setIsMinimized(false)}
          title="Tutoriel en cours - Cliquez pour reprendre"
          style={{
            position: 'fixed',
            bottom: '10px',
            right: '10px',
            zIndex: 999999
          }}
        >
          📚
          {actionCompleted && <span className="tutorial-badge-check">✅</span>}
        </button>
      );
    }
    
    return ReactDOM.createPortal(
      <button 
        className="tutorial-minimized-bottombar"
        onClick={() => setIsMinimized(false)}
        title="Tutoriel en cours - Cliquez pour reprendre"
      >
        📚
        {actionCompleted && <span className="tutorial-badge-check">✅</span>}
      </button>,
      container
    );
  }

  return (
    <>
      {/* Overlay sombre */}
      <div 
        className="tutorial-overlay" 
        onClick={() => currentStep.validation && !actionCompleted && setIsMinimized(true)}
        title={currentStep.validation && !actionCompleted ? "Clique pour réduire le tutoriel" : ""}
      />
      
      {/* Indicateur de clic sur overlay (si action requise) */}
      {currentStep.validation && !actionCompleted && (
        <div className="tutorial-overlay-hint">
          Clique n'importe où pour réduire le tutoriel ⬇️
        </div>
      )}

      {/* Spotlight sur l'élément ciblé */}
      {spotlightRect && (
        <div
          className="tutorial-spotlight"
          style={{
            top: spotlightRect.top - 8,
            left: spotlightRect.left - 8,
            width: spotlightRect.width + 16,
            height: spotlightRect.height + 16
          }}
        />
      )}

      {/* Tooltip avec instructions */}
      <div
        ref={tooltipRef}
        className={`tutorial-tooltip position-${currentStep.position || 'center'} ${isDragging ? 'dragging' : ''}`}
        style={{
          top: tooltipPosition.top,
          left: tooltipPosition.left,
          cursor: isDragging ? 'grabbing' : 'default'
        }}
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
      >
        {/* En-tête */}
        <div className="tutorial-header" style={{ cursor: 'grab' }}>
          <h3 className="tutorial-title">{currentStep.title}</h3>
          <div className="tutorial-header-actions">
            <span className="tutorial-step-counter">
              {currentStepIndex + 1} / {tutorialSteps.length}
            </span>
            {currentStep.validation && !actionCompleted && (
              <button 
                className="tutorial-minimize-btn"
                onClick={() => setIsMinimized(true)}
                title="Réduire le tutoriel pour effectuer l'action"
              >
                ⬇️
              </button>
            )}
          </div>
        </div>

        {/* Description */}
        <p className="tutorial-description">{currentStep.description}</p>

        {/* Alerte si pas sur la bonne page */}
        {!isOnCorrectPage && (
          <div className="tutorial-page-warning">
            ⚠️ Veuillez naviguer vers la page indiquée pour continuer le tutoriel
          </div>
        )}

        {/* Indicateur de validation d'action */}
        {currentStep.validation && currentStep.validation.type !== 'manual' && (
          <div className={`tutorial-action-status ${actionCompleted ? 'completed' : 'pending'}`}>
            {actionCompleted ? (
              <>
                <span className="status-icon">✅</span>
                <span className="status-text">Action accomplie ! Tu peux continuer.</span>
              </>
            ) : (
              <>
                <span className="status-icon">⏳</span>
                <div className="status-text">
                  Accomplis l'action demandée pour continuer...
                  <br />
                  <small style={{ opacity: 0.7 }}>Clique sur ⬇️ pour réduire le tutoriel</small>
                </div>
              </>
            )}
          </div>
        )}

        {/* Récompense */}
        {currentStep.reward && (
          <div className="tutorial-reward">
            <div className="tutorial-reward-title">
              {currentStep.reward.description}
            </div>
            <div className="tutorial-reward-items">
              {Object.entries(currentStep.reward.value).map(([resource, amount]) => (
                <span key={resource} className="tutorial-reward-item">
                  {getResourceIcon(resource)} +{amount}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Barre de progression */}
        <div className="tutorial-progress">
          <div className="tutorial-progress-bar">
            <div 
              className="tutorial-progress-fill" 
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="tutorial-progress-text">
            Progression : {Math.round(progress)}%
          </div>
        </div>

        {/* Boutons d'action */}
        <div className="tutorial-actions">
          {currentStepIndex > 0 && (
            <button 
              className="tutorial-button tutorial-button-secondary"
              onClick={handlePrevious}
            >
              ← Retour
            </button>
          )}
          
          <button 
            className="tutorial-button tutorial-button-skip"
            onClick={handleSkip}
          >
            Passer le tutoriel
          </button>

          <button 
            className="tutorial-button tutorial-button-primary"
            onClick={handleNext}
          >
            {currentStep.nextButton || 'Suivant'} →
          </button>
        </div>
      </div>
    </>
  );
};

// Helper pour obtenir l'icône d'une ressource
function getResourceIcon(resource: string): string {
  const icons: { [key: string]: string } = {
    wood: '🪵',
    stone: '🪨',
    gold: '🪙',
    iron: '⚙️',
    research_points: '🔬',
    warrior: '⚔️',
    archer: '🏹',
    cavalry: '🐎'
  };
  return icons[resource] || '❓';
}

export default TutorialOverlay;
