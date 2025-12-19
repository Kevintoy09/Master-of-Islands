import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/research.css';
import type { Research } from '../hooks/useResearchDatabase';
import { useUser } from '../hooks/useUser';
import { usePlayerResearch } from '../hooks/usePlayerResearch';
import HeroSelectionPopup from '../popups/HeroSelectionPopup';

const ResearchPage: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState<Research['category']>('economy');
  const [showHeroSelection, setShowHeroSelection] = useState(false);
  const navigate = useNavigate();
  const { user } = useUser();
  const { 
    playerResearchData, 
    isResearchUnlocked, 
    loadPlayerResearch,
    canUnlockResearch,
    unlockResearch,
    researchDatabase,
    getResearchById,
    getResearchesByCategory,
    getAllCategories
  } = usePlayerResearch();

  // State pour les points de recherche en temps réel
  const [researchPoints, setResearchPoints] = useState(0);

  // Charger les points de recherche au chargement
  useEffect(() => {
    const fetchResearchPoints = async () => {
      if (user.id) {
        try {
          const response = await fetch(`/api/player/${user.id}/research-points`);
          const data = await response.json();
          if (data.research_points !== undefined) {
            setResearchPoints(Math.round(data.research_points));
          }
        } catch (error) {
          console.error('Erreur lors du chargement des points de recherche:', error);
        }
      }
    };

    fetchResearchPoints();
    
    // Actualiser périodiquement
    const interval = setInterval(fetchResearchPoints, 10000); // Réduit de 5s à 10s pour performance
    return () => clearInterval(interval);
  }, [user.id]);

  // Fonction pour formater l'affichage des points de recherche
  const formatResearchPoints = (points: number): string => {
    if (points >= 10000) {
      return `${Math.floor(points / 1000)}k`;
    } else if (points >= 1000) {
      return `${(points / 1000).toFixed(1)}k`;
    }
    return points.toString();
  };
  // Utilisation de la base de données centralisée
  const researchData = {
    economy: getResearchesByCategory('economy'),
    science: getResearchesByCategory('science'),
    warfare: getResearchesByCategory('warfare'),
    marine: getResearchesByCategory('marine')
  };

  const getCategoryIcon = (category: Research['category']) => {
    const icons = {
      economy: '💰',
      science: '🔬',
      warfare: '⚔️',
      marine: '⚓'
    };
    return icons[category];
  };

  const getCategoryTitle = (category: Research['category']) => {
    const titles = {
      economy: 'Économie',
      science: 'Science',
      warfare: 'Militaire',
      marine: 'Marine'
    };
    return titles[category];
  };

  // Fonction pour obtenir le nom d'une recherche par son ID
  const getResearchName = (id: string): string => {
    const research = getResearchById(id);
    return research?.name || id;
  };

  const getResourceIcon = (resource: string) => {
    const icons: { [key: string]: string } = {
      research_points: '🔬',
      wood: '🪵',
      stone: '🪨',
      gold: '🪙',
      iron: '⚙️',
      charcoal: '⚫'
    };
    return icons[resource] || '❓';
  };

  const renderResearch = (research: Research, index: number) => {
    // Détecter si c'est une recherche "à venir"
    const isComingSoon = research.id.startsWith('coming_soon');
    
    // Utiliser UNIQUEMENT les données du serveur
    const isUnlockedFromServer = isResearchUnlocked(research.id);
    
    // Vérifier si une autre recherche du même groupe exclusif est débloquée
    let isBlockedByExclusiveGroup = false;
    let blockedByResearchName = '';
    if (research.exclusive_group && !isUnlockedFromServer && researchDatabase) {
      const groupResearches = researchDatabase.filter(
        (r: Research) => r.exclusive_group === research.exclusive_group && r.id !== research.id
      );
      for (const groupResearch of groupResearches) {
        if (isResearchUnlocked(groupResearch.id)) {
          isBlockedByExclusiveGroup = true;
          blockedByResearchName = groupResearch.name;
          break;
        }
      }
    }
    
    const isAvailable = !isUnlockedFromServer && !isComingSoon && !isBlockedByExclusiveGroup;
    
    let statusClass = 'locked';
    let buttonText = 'Verrouillé';
    let buttonClass = 'disabled';
    
    if (isComingSoon) {
      statusClass = 'coming-soon';
      buttonText = 'Prochainement';
      buttonClass = 'disabled';
    } else if (isUnlockedFromServer) {
      statusClass = 'completed';
      buttonText = 'Débloquée';
      buttonClass = 'completed';
    } else if (isBlockedByExclusiveGroup) {
      statusClass = 'blocked-exclusive';
      buttonText = '🔒 Bloqué';
      buttonClass = 'disabled';
    } else if (isAvailable) {
      statusClass = 'available';
      buttonText = 'Débloquer';
      buttonClass = 'available';
    }
    
    const ageClass = research.age === 'Fer' ? 'age-fer' : '';
    
    return (
      <div key={index} className={`research-item ${statusClass} ${ageClass}`}>
        <div className="research-header">
          <div className="research-level">Niv. {research.level}</div>
          <div className="research-cost">
            {Object.entries(research.cost).map(([resource, amount]) => (
              <span key={resource} className="cost-item">
                {getResourceIcon(resource)} {amount}
              </span>
            ))}
          </div>
          <div className="research-age">{research.age}</div>
          {isUnlockedFromServer && <div className="research-status completed">✓</div>}
        </div>
        
        <h4 className="research-name">{research.name}</h4>
        <p className="research-description">{research.description}</p>
        
        {research.exclusive_group && (
          <div className="exclusive-choice-badge">
            ⚠️ Choix exclusif
          </div>
        )}
        
        {isBlockedByExclusiveGroup && (
          <div className="blocked-message">
            🔒 Bloqué car vous avez choisi "{blockedByResearchName}"
          </div>
        )}
        
        <button 
          className={`research-button ${buttonClass}`}
          disabled={isUnlockedFromServer && research.id !== 'premiers_heros'}
          onClick={() => handleResearchAction(research)}
        >
          {research.id === 'premiers_heros' && isUnlockedFromServer ? 'Choisir un Héros' : buttonText}
        </button>
      </div>
    );
  };

  // Fonction pour regrouper et afficher l'arbre de recherche avec les choix multiples
  const renderResearchTree = (researches: Research[]) => {
    const rendered: any[] = [];
    const processedIndices = new Set<number>();
    
    researches.forEach((research, index) => {
      if (processedIndices.has(index)) return;
      
      // Vérifier si cette recherche fait partie d'un groupe exclusif
      if (research.exclusive_group) {
        // Trouver toutes les recherches du même groupe exclusif
        const groupResearches = researches.filter((r, i) => 
          r.exclusive_group === research.exclusive_group && !processedIndices.has(i)
        );
        
        if (groupResearches.length > 1) {
          // Marquer tous les indices comme traités
          groupResearches.forEach(r => {
            const idx = researches.indexOf(r);
            if (idx !== -1) processedIndices.add(idx);
          });
          
          // Créer un conteneur pour les choix multiples
          rendered.push(
            <div key={`group-${research.exclusive_group}`} className="research-choices-container">
              {groupResearches.map((r, i) => renderResearch(r, researches.indexOf(r)))}
            </div>
          );
          return;
        }
      }
      
      // Recherche normale (pas de groupe ou groupe avec un seul élément)
      processedIndices.add(index);
      rendered.push(renderResearch(research, index));
    });
    
    return rendered;
  };

  const handleResearchAction = async (research: Research) => {
    // Si c'est "premiers_heros" et déjà débloqué, réouvrir la sélection de héros
    if (research.id === 'premiers_heros' && isResearchUnlocked(research.id)) {
      setShowHeroSelection(true);
      return;
    }
    
    if (isResearchUnlocked(research.id)) return;
    
    // Vérifier d'abord les prérequis
    const canUnlock = canUnlockResearch(research.id);
    
    if (canUnlock.canUnlock) {
      // Si c'est une recherche exclusive, demander confirmation
      if (research.exclusive_group && researchDatabase) {
        const groupResearches = researchDatabase.filter(
          (r: Research) => r.exclusive_group === research.exclusive_group && r.id !== research.id
        );
        const otherChoicesNames = groupResearches.map((r: Research) => r.name).join(', ');
        
        const confirmed = window.confirm(
          `⚠️ ATTENTION : Choix exclusif !\n\n` +
          `Vous êtes sur le point de débloquer "${research.name}".\n\n` +
          `Ce choix est DÉFINITIF et bloquera les autres options : ${otherChoicesNames}\n\n` +
          `Voulez-vous continuer ?`
        );
        
        if (!confirmed) {
          return; // Annuler si le joueur refuse
        }
      }
      
      const result = await unlockResearch(research.id, {
        name: research.name,
        cost: research.cost
      });
      
      // Si c'est la recherche "Premiers Héros", ouvrir le popup de sélection
      if (research.id === 'premiers_heros' && result.success) {
        setShowHeroSelection(true);
      } else {
        alert(result.message);
      }
    } else {
      alert(`Impossible de débloquer: ${canUnlock.reason}`);
    }
  };

  const handleHeroSelection = async (heroId: string) => {
    try {
      const response = await fetch(`/api/heroes/select/${user.id}/${heroId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const result = await response.json();
      
      if (result.success) {
        alert(`🎉 ${result.message}`);
        // Recharger les données du joueur si nécessaire
        loadPlayerResearch();
      } else {
        alert(`❌ ${result.message}`);
      }
    } catch (error) {
      console.error('Erreur lors de la sélection du héros:', error);
      alert('❌ Erreur lors de la sélection du héros');
    }
  };

  return (
    <div className="research-page">
      <div className="research-header-bar">
        <div className="research-header-left">
          <button 
            className="back-button"
            onClick={() => navigate(-1)}
            title="Retour"
          >
            ← Retour
          </button>
          <h2>Centre de Recherche</h2>
        </div>
        <div className="research-status-bar">
          <div className="current-research-points">
            🔬 Points de Recherche: {formatResearchPoints(researchPoints)}
          </div>
        </div>
      </div>
      
      <div className="research-categories">
        {getAllCategories().map(category => (
          <button
            key={category}
            className={`category-button ${activeCategory === category ? 'active' : ''}`}
            onClick={() => setActiveCategory(category)}
          >
            <span className="category-icon">{getCategoryIcon(category)}</span>
            <span className="category-title">{getCategoryTitle(category)}</span>
          </button>
        ))}
      </div>
      
      <div className="research-content">
        <h3 className="research-branch-title">
          {getCategoryIcon(activeCategory)} {getCategoryTitle(activeCategory)}
        </h3>
        
        <div className="research-tree">
          {renderResearchTree(researchData[activeCategory])}
        </div>
      </div>
      
      {user.id && (
        <HeroSelectionPopup
          isOpen={showHeroSelection}
          onClose={() => setShowHeroSelection(false)}
          onSelectHero={handleHeroSelection}
          playerId={user.id}
        />
      )}
    </div>
  );
};

export default ResearchPage;
