/**
 * CombatTutorialPopup.tsx
 * Tutoriel multi-pages expliquant tout le système de combat
 */

import React, { useState } from 'react';
import './CombatTutorialPopup.css';

interface CombatTutorialPopupProps {
  isOpen: boolean;
  onClose: () => void;
}

const CombatTutorialPopup: React.FC<CombatTutorialPopupProps> = ({ isOpen, onClose }) => {
  const [currentPage, setCurrentPage] = useState(0);

  if (!isOpen) return null;

  const pages = [
    // Page 0: Introduction
    {
      title: "📚 Guide du Système de Combat",
      content: (
        <div className="tutorial-page">
          <h2>Bienvenue dans le guide complet du combat !</h2>
          <p>Ce tutoriel vous explique tous les aspects du système de bataille.</p>
          
          <div className="tutorial-section">
            <h3>📋 Au programme :</h3>
            <ul>
              <li>⚔️ Les bases du combat</li>
              <li>🤖 Gestion automatique / manuelle</li>
              <li>🎯 Déploiement des unités</li>
              <li>🚶 Mouvements et positionnement</li>
              <li>⚡ Système d'attaque</li>
              <li>🌍 Effets de terrain</li>
              <li>🧮 Héros et auras</li>
              <li>🏰 Murs et fortifications</li>
              <li>🏆 Conditions de victoire</li>
              <li>📊 Calculs de combat détaillés</li>
              <li>🎮 Interface et contrôles</li>
            </ul>
          </div>

          <p className="tutorial-tip">💡 Utilisez les flèches pour naviguer entre les pages</p>
        </div>
      )
    },

    // Page 1: Bases du combat
    {
      title: "⚔️ Les Bases du Combat",
      content: (
        <div className="tutorial-page">
          <h3>Phases d'une bataille</h3>
          
          <div className="tutorial-section">
            <h4>1️⃣ Phase de Déploiement</h4>
            <p>• Placez vos unités sur votre zone de départ</p>
            <p>• Maximum 8-10 unités par stack selon le type</p>
            <p>• Les héros peuvent être déployés individuellement</p>
          </div>

          <div className="tutorial-section">
            <h4>2️⃣ Phase de Combat</h4>
            <p>• Tour par tour alterné (Attaquant → Défenseur)</p>
            <p>• Chaque joueur peut agir avec toutes ses unités</p>
            <p>• Déplacez, attaquez ou passez votre tour</p>
          </div>

          <div className="tutorial-section">
            <h4>3️⃣ Phase de Victoire</h4>
            <p>• La bataille se termine quand un camp est éliminé</p>
            <p>• Le vainqueur peut piller les ressources</p>
            <p>• Les unités survivantes retournent à la garnison</p>
          </div>

          <div className="tutorial-tip">
            <strong>⏱️ Timer automatique :</strong> Si vous ne jouez pas pendant le temps imparti, votre tour passe automatiquement.
          </div>
        </div>
      )
    },

    // Page 2: Gestion Auto/Manuel (IMPORTANT - placé en 3ème position)
    {
      title: "🤖 Gestion Automatique / Manuelle",
      content: (
        <div className="tutorial-page">
          <h3>Comment se déroule un tour de combat</h3>
          
          <div className="tutorial-section">
            <h4>🎮 Contrôle de vos unités</h4>
            <p>• <strong>À votre tour</strong>, vous pouvez jouer manuellement vos unités</p>
            <p>• Sélectionnez une unité, déplacez-la et attaquez si vous le souhaitez</p>
            <p>• Vous avez un temps limité pour effectuer vos actions</p>
            <p>• Cliquez sur "Fin de tour" quand vous avez terminé</p>
          </div>

          <div className="tutorial-section">
            <h4>⏱️ Timer et IA automatique</h4>
            <p>• Si aucune action n'est effectuée avant la fin du timer</p>
            <p>• <strong>L'IA jouera automatiquement pour vous</strong></p>
            <p>• Elle choisira les meilleures actions possibles</p>
            <p>• Cela évite les batailles bloquées ou les abandons</p>
          </div>

          <div className="tutorial-section">
            <h4>🎯 Déploiement des unités</h4>
            <p>• <strong>Mode manuel :</strong> Placez vous-même vos unités sur la zone de départ</p>
            <p>• <strong>Mode automatique :</strong> Les unités sont déployées automatiquement</p>
            <p>• Vous devez déployer dans le temps imparti</p>
            <p>• Le déploiement auto optimise les positions selon le type d'unité</p>
          </div>

          <div className="tutorial-tip">
            <strong>💡 Conseil :</strong> Jouez activement pour garder le contrôle ! L'IA est compétente mais ne connaît pas votre stratégie.
          </div>
        </div>
      )
    },

    // Page 3: Déploiement
    {
      title: "🎯 Déploiement des Unités",
      content: (
        <div className="tutorial-page">
          <h3>Comment déployer vos troupes</h3>
          
          <div className="tutorial-section">
            <h4>🔵 Zone de déploiement</h4>
            <p>• Les hexagones bleus/rouges indiquent où vous pouvez placer vos unités</p>
            <p>• L'attaquant déploie en bas, le défenseur en haut</p>
            <p>• Vous ne pouvez pas placer d'unités sur les murs</p>
          </div>

          <div className="tutorial-section">
            <h4>📦 Stacks d'unités</h4>
            <p>• Les unités sont groupées en stacks pour économiser de l'espace</p>
            <p>• Taille max : 8-10 unités selon le type</p>
            <p>• Un stack combat comme une seule entité</p>
          </div>

          <div className="tutorial-section">
            <h4>🦸 Héros</h4>
            <p>• Les héros sont toujours déployés seuls (pas de stack)</p>
            <p>• Ils fournissent une aura aux unités alliées proches</p>
            <p>• Priorité de déploiement : placez-les en premier !</p>
          </div>

          <div className="tutorial-tip">
            <strong>✅ Conseil :</strong> Déployez vos héros au centre pour maximiser leur aura.
          </div>
        </div>
      )
    },

    // Page 3: Mouvements
    {
      title: "🚶 Mouvements et Positionnement",
      content: (
        <div className="tutorial-page">
          <h3>Se déplacer sur le champ de bataille</h3>
          
          <div className="tutorial-section">
            <h4>🎯 Sélection d'unité</h4>
            <p>1. Cliquez sur une unité pour la sélectionner</p>
            <p>2. Les hexagones verts montrent où elle peut se déplacer</p>
            <p>3. Cliquez sur un hexagone vert pour déplacer</p>
          </div>

          <div className="tutorial-section">
            <h4>📏 Points de mouvement</h4>
            <p>• Infanterie légère : 3-4 hexagones</p>
            <p>• Infanterie lourde : 2-3 hexagones</p>
            <p>• Cavalerie : 4-5 hexagones</p>
            <p>• Unités à distance : 2-3 hexagones</p>
          </div>

          <div className="tutorial-section">
            <h4>🚫 Obstacles</h4>
            <p>• Vous ne pouvez pas traverser les murs</p>
            <p>• Vous ne pouvez pas vous déplacer sur une case occupée</p>
            <p>• Certains terrains ralentissent le mouvement</p>
          </div>

          <div className="tutorial-tip">
            <strong>⚡ Astuce :</strong> Une unité qui a attaqué ne peut plus bouger ce tour.
          </div>
        </div>
      )
    },

    // Page 4: Attaques
    {
      title: "⚡ Système d'Attaque",
      content: (
        <div className="tutorial-page">
          <h3>Comment attaquer l'ennemi</h3>
          
          <div className="tutorial-section">
            <h4>⚔️ Attaque au corps à corps</h4>
            <p>1. Sélectionnez votre unité</p>
            <p>2. Cliquez sur une unité ennemie adjacente</p>
            <p>3. Le popup de combat s'ouvre avec les stats</p>
            <p>4. Confirmez pour lancer l'attaque</p>
          </div>

          <div className="tutorial-section">
            <h4>🏹 Attaque à distance</h4>
            <p>• Portée : 2-3 hexagones selon l'unité</p>
            <p>• Pas besoin d'être adjacent</p>
            <p>• Cliquez directement sur la cible</p>
            <p>• Bonus de dégâts depuis les hauteurs</p>
          </div>

          <div className="tutorial-section">
            <h4>📊 Calcul des dégâts</h4>
            <p>• Attaque × multiplicateur de terrain</p>
            <p>• Défense × bonus de position</p>
            <p>• HP de l'unité × nombre dans le stack</p>
            <p>• Contre-attaque si unité au corps à corps</p>
          </div>

          <div className="tutorial-tip">
            <strong>🎯 Contre système :</strong> Lances battent cavalerie, épées battent lances, cavalerie bat épées.
          </div>
        </div>
      )
    },

    // Page 5: Terrains
    {
      title: "🌍 Effets de Terrain",
      content: (
        <div className="tutorial-page">
          <h3>Le terrain influence le combat</h3>
          
          <div className="tutorial-section">
            <h4>🏔️ Types de terrain</h4>
            <p><strong>Plaines :</strong> Aucun bonus (neutre)</p>
            <p><strong>Forêt :</strong> Bonus défensif, pénalité offensive</p>
            <p><strong>Collines :</strong> Bonus offensif et défensif</p>
            <p><strong>Montagnes :</strong> Fort bonus défensif, pénalité de mouvement</p>
            <p><strong>Marais :</strong> Pénalités de mouvement et d'attaque</p>
            <p><strong>Rivière :</strong> Pénalité de mouvement</p>
          </div>

          <div className="tutorial-section">
            <h4>🎯 Stratégie</h4>
            <p>• Placez vos archers sur les collines</p>
            <p>• Cachez votre infanterie dans les forêts</p>
            <p>• Évitez les marais avec la cavalerie</p>
            <p>• Utilisez les montagnes pour bloquer</p>
          </div>

          <div className="tutorial-tip">
            <strong>💡 Astuce :</strong> Le terrain de l'attaquant ET du défenseur compte !
          </div>
        </div>
      )
    },

    // Page 6: Héros et auras
    {
      title: "🦸 Héros et Auras",
      content: (
        <div className="tutorial-page">
          <h3>Les héros changent la bataille</h3>
          
          <div className="tutorial-section">
            <h4>⭐ Aura des héros</h4>
            <p>• Portée : Variable selon le niveau du héros</p>
            <p>• Affecte toutes les unités alliées dans la zone</p>
            <p>• Les unités dans l'aura brillent en doré</p>
          </div>

          <div className="tutorial-section">
            <h4>🎁 Bonus d'aura</h4>
            <p>• Bonus d'attaque (dépend du héros et du niveau)</p>
            <p>• Bonus de défense (dépend du héros et du niveau)</p>
            <p>• HP supplémentaires (variable)</p>
            <p>• Points de mouvement bonus (possible)</p>
          </div>

          <div className="tutorial-section">
            <h4>⚠️ Vulnérabilité</h4>
            <p>• Les héros ont peu de HP</p>
            <p>• Si un héros meurt, l'aura disparaît</p>
            <p>• Protégez vos héros avec de l'infanterie lourde</p>
          </div>

          <div className="tutorial-tip">
            <strong>🏆 Priorité :</strong> L'IA cible toujours les héros en premier !
          </div>
        </div>
      )
    },

    // Page 7: Murs
    {
      title: "🏰 Murs et Fortifications",
      content: (
        <div className="tutorial-page">
          <h3>Défendre avec des murs</h3>
          
          <div className="tutorial-section">
            <h4>🧱 Fonctionnement</h4>
            <p>• Les murs bloquent le passage</p>
            <p>• Doivent être détruits pour avancer</p>
            <p>• Ont des HP indépendants (affichés en jaune)</p>
            <p>• Plusieurs niveaux : bois, pierre, fer</p>
          </div>

          <div className="tutorial-section">
            <h4>⚔️ Attaquer un mur</h4>
            <p>1. Sélectionnez une unité adjacente au mur</p>
            <p>2. Cliquez sur le mur jaune</p>
            <p>3. Le popup d'interaction s'ouvre</p>
            <p>4. Choisissez "Attaquer le mur"</p>
          </div>

          <div className="tutorial-section">
            <h4>🛡️ Résistance</h4>
            <p>• Mur en bois : 100-150 HP</p>
            <p>• Mur en pierre : 200-300 HP</p>
            <p>• Mur en fer : 400-500 HP</p>
          </div>

          <div className="tutorial-tip">
            <strong>💥 Conseil :</strong> Les béliers et catapultes font x3 dégâts aux murs !
          </div>
        </div>
      )
    },

    // Page 8: Victoire
    {
      title: "🏆 Conditions de Victoire",
      content: (
        <div className="tutorial-page">
          <h3>Comment gagner une bataille</h3>
          
          <div className="tutorial-section">
            <h4>✅ Victoire par élimination</h4>
            <p>• Détruisez toutes les unités ennemies</p>
            <p>• Victoire automatique et immédiate</p>
            <p>• Popup de pillage s'ouvre</p>
          </div>

          <div className="tutorial-section">
            <h4>🏳️ Victoire par reddition</h4>
            <p>• L'adversaire peut se rendre à tout moment</p>
            <p>• Bouton "Se rendre" dans le menu</p>
            <p>• Les unités survivantes sont redistribuées</p>
          </div>

          <div className="tutorial-section">
            <h4>😰 Victoire par moral</h4>
            <p>• Si le moral tombe à 0, reddition automatique</p>
            <p>• Le moral baisse quand des unités meurent</p>
            <p>• Les héros donnent un bonus de moral</p>
          </div>

          <div className="tutorial-section">
            <h4>🎁 Récompenses</h4>
            <p>• Pillage des ressources de la ville</p>
            <p>• XP pour vos unités survivantes</p>
            <p>• Points de gloire pour le classement</p>
          </div>
        </div>
      )
    },

    // Page 9: Calculs de combat
    {
      title: "📊 Calculs de Combat Détaillés",
      content: (
        <div className="tutorial-page">
          <h3>Comment sont calculés les dégâts</h3>
          
          <div className="tutorial-section">
            <h4>⚔️ Formule de base</h4>
            <p><strong>Dégâts = (Attaque × Taille Stack × Bonus Terrain) - (Défense × Bonus Position)</strong></p>
            <p>• <strong>Attaque :</strong> Stat de base de l'unité attaquante</p>
            <p>• <strong>Taille Stack :</strong> Nombre d'unités dans le groupe</p>
            <p>• <strong>Bonus Terrain :</strong> Multiplicateur selon le terrain</p>
            <p>• <strong>Défense :</strong> Capacité à absorber les dégâts</p>
          </div>

          <div className="tutorial-section">
            <h4>🌍 Modificateurs de terrain</h4>
            <p>• Collines : Bonus à l'attaque pour les unités à distance</p>
            <p>• Forêts : Bonus défensif pour l'infanterie</p>
            <p>• Marais : Pénalité pour tous</p>
            <p>• Plaines : Neutre (multiplicateur x1)</p>
          </div>

          <div className="tutorial-section">
            <h4>🧮 Aura des héros</h4>
            <p>• <strong>Portée :</strong> Variable selon le niveau du héros</p>
            <p>• <strong>Bonus Attaque/Défense :</strong> Dépend du type et niveau du héros</p>
            <p>• <strong>HP supplémentaires :</strong> Augmente la survie du stack</p>
            <p>• Les bonus s'appliquent automatiquement dans les calculs</p>
          </div>

          <div className="tutorial-section">
            <h4>🔄 Contre-attaque</h4>
            <p>• Les unités au corps à corps ripostent automatiquement</p>
            <p>• Les unités à distance NE ripostent PAS</p>
            <p>• La riposte utilise les mêmes calculs de dégâts</p>
            <p>• Affiché dans le popup de combat avant confirmation</p>
          </div>

          <div className="tutorial-tip">
            <strong>📝 Popup de combat :</strong> Avant chaque attaque, un popup affiche les dégâts prévus, les bonus, les pénalités et la riposte éventuelle. Lisez-le attentivement !
          </div>
        </div>
      )
    },

    // Page 10: Interface
    {
      title: "🎮 Interface et Contrôles",
      content: (
        <div className="tutorial-page">
          <h3>Utiliser l'interface de combat</h3>
          
          <div className="tutorial-section">
            <h4>🖱️ Contrôles de base</h4>
            <p>• <strong>Clic gauche :</strong> Sélectionner une unité</p>
            <p>• <strong>Molette :</strong> Zoom avant/arrière</p>
            <p>• <strong>Clic droit :</strong> Déplacer la caméra</p>
            <p>• <strong>Double-clic :</strong> Centrer sur l'unité</p>
          </div>

          <div className="tutorial-section">
            <h4>🎛️ Boutons du menu</h4>
            <p>• <strong>Fin de tour :</strong> Passer au joueur suivant</p>
            <p>• <strong>Infos Unité :</strong> Voir les stats détaillées</p>
            <p>• <strong>Se rendre :</strong> Abandonner la bataille</p>
            <p>• <strong>Retour :</strong> Quitter la bataille (si terminée)</p>
          </div>

          <div className="tutorial-section">
            <h4>📊 Informations affichées</h4>
            <p>• Round actuel en haut de l'écran</p>
            <p>• Tour du joueur courant (bleu/rouge)</p>
            <p>• Statistiques des équipes (unités, moral)</p>
            <p>• Points de vie des unités (barre de vie)</p>
          </div>

          <div className="tutorial-tip">
            <strong>💡 Astuce :</strong> Survolez une unité pour voir rapidement ses statistiques et son état actuel.
          </div>
        </div>
      )
    }
  ];

  const currentPageData = pages[currentPage];

  const handleNext = () => {
    if (currentPage < pages.length - 1) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handlePrevious = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleClose = () => {
    setCurrentPage(0);
    onClose();
  };

  return (
    <div className="combat-tutorial-overlay">
      <div className="combat-tutorial-popup">
        {/* Header */}
        <div className="tutorial-header">
          <h2>{currentPageData.title}</h2>
          <button className="tutorial-close" onClick={handleClose}>✕</button>
        </div>

        {/* Content */}
        <div className="tutorial-content">
          {currentPageData.content}
        </div>

        {/* Footer with navigation */}
        <div className="tutorial-footer">
          <button 
            className="tutorial-nav-button" 
            onClick={handlePrevious}
            disabled={currentPage === 0}
          >
            ← Précédent
          </button>

          <div className="tutorial-pagination">
            {pages.map((_, index) => (
              <span 
                key={index}
                className={`tutorial-dot ${index === currentPage ? 'active' : ''}`}
                onClick={() => setCurrentPage(index)}
              />
            ))}
          </div>

          <button 
            className="tutorial-nav-button" 
            onClick={handleNext}
            disabled={currentPage === pages.length - 1}
          >
            Suivant →
          </button>
        </div>

        {/* Page counter */}
        <div className="tutorial-page-counter">
          Page {currentPage + 1} / {pages.length}
        </div>
      </div>
    </div>
  );
};

export default CombatTutorialPopup;
