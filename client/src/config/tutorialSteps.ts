/**
 * TUTORIAL_STEPS.TS - Configuration du Système de Tutoriel
 * 
 * RÔLE:
 *   Définit toutes les étapes du tutoriel interactif du jeu.
 *   Chaque étape guide le joueur à travers les fonctionnalités de base.
 * 
 * RESPONSABILITÉS:
 *   1. Définition des étapes du tutoriel (titre, description, position)
 *   2. Configuration des récompenses (ressources, points de recherche)
 *   3. Validation automatique des actions du joueur
 *   4. Gestion de la progression entre les pages (World → Island → City)
 * 
 * SYSTÈME DE VALIDATION:
 *   - 'manual' : Le joueur clique sur "Suivant"
 *   - 'click' : Attend que le joueur clique sur un élément spécifique
 *   - 'api_check' : Vérifie une condition via l'API (ex: recherche débloquée)
 *   - 'element_exists' : Attend qu'un élément apparaisse dans le DOM
 *   - 'path_check' : Vérifie que le joueur est sur la bonne page
 * 
 * ARCHITECTURE:
 *   Étape 0-2 : WorldPage (sélection île)
 *   Étape 3-5 : IslandPage (vue île, ressources)
 *   Étape 6-12 : CityPage (bâtiments, recherches, production)
 * 
 * RÉCOMPENSES:
 *   - Ressources : wood, stone, gold, etc.
 *   - Points de recherche : research_points
 *   - Créditées automatiquement via l'API /api/tutorial/complete
 * 
 * SYSTÈME DE Z-INDEX:
 *   - Tutorial overlay : 2147483647 (max CSS avec !important)
 *   - Garantit que le tutoriel apparaît toujours au-dessus de tout
 * 
 * POINTS CLÉS:
 *   - Chaque étape a un ID unique (ex: 'welcome_world', 'build_sawmill')
 *   - Les récompenses sont définies dans le champ 'reward'
 *   - La validation se fait côté frontend ET backend (double sécurité)
 *   - Le tutoriel persiste même après rechargement de page
 * 
 * UTILISATION:
 *   import { tutorialSteps } from './config/tutorialSteps';
 *   const currentStep = tutorialSteps[stepIndex];
 * 
 * HISTORIQUE:
 *   - Ajout de 3 étapes d'introduction (WorldPage, IslandPage, CityPage)
 *   - Validation automatique via 'path_check' pour la navigation
 *   - Système de récompenses automatique
 *   - Z-index à 2147483647 pour toujours être visible
 *   - Simplification : suppression du champ 'action' inutilisé
 */

export interface TutorialStep {
  id: string;
  title: string;
  description: string;
  target?: string; // Sélecteur CSS de l'élément à surligner
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
  page?: string; // Page où afficher cette étape
  reward?: {
    type: 'resources' | 'research_points' | 'building' | 'units';
    description: string;
    value: Record<string, number>;
  };
  nextButton?: string;
  skipButton?: boolean;
  // Validation automatique
  validation?: {
    type: 'click' | 'api_check' | 'element_exists' | 'manual' | 'path_check';
    target?: string; // Pour click: élément à cliquer, pour element_exists: sélecteur à vérifier
    apiEndpoint?: string; // Pour api_check: endpoint à interroger
    apiCondition?: (data: any, playerId?: string) => boolean; // Fonction de validation de la réponse API
    pathPattern?: RegExp; // Pour path_check: pattern du pathname à vérifier
  };
}

export const tutorialSteps: TutorialStep[] = [
  // Étape 0: Bienvenue sur la carte du monde
  {
    id: 'welcome_world',
    title: '🌍 Bienvenue sur la Carte du Monde !',
    description: 'Bienvenue sur la carte du monde ! Tu peux voir toutes les îles que tu pourras coloniser. Clique sur ton île qui est en surbrillance pour commencer ton aventure !',
    position: 'center',
    page: '/world',
    validation: {
      type: 'api_check',
      apiEndpoint: '/api/universe',
      apiCondition: (data: any, playerId?: string) => {
        // Validation : le joueur doit avoir cliqué sur une île (avoir une ville)
        const cities = data?.cities || [];
        return cities.some((c: any) => c.owner === playerId);
      }
    },
    nextButton: 'Cliquer sur mon île',
    skipButton: true
  },

  // Étape 1: Présentation de l'île
  {
    id: 'welcome_island',
    title: '🏝️ Bienvenue sur ton Île !',
    description: 'Voici ton île ! Tu peux voir ta ville en surbrillance. Clique sur ta ville pour y entrer et commencer à la développer.',
    position: 'center',
    validation: {
      type: 'path_check',
      pathPattern: /^\/(island\/\d+|city\/city_id_\d+)$/
    },
    nextButton: 'J\'ai cliqué sur mon île'
  },

  // Étape 2: Bienvenue dans la ville
  {
    id: 'welcome_city',
    title: '🏘️ Bienvenue dans ta Ville !',
    description: 'Voici ta ville ! C\'est ici que tu vas construire des bâtiments et gérer tes ressources. Commence par construire un Hôtel de Ville pour débloquer toutes les fonctionnalités.',
    position: 'center',
    validation: {
      type: 'path_check',
      pathPattern: /^\/city\/city_id_\d+$/
    },
    reward: {
      type: 'resources',
      description: '🎁 Bonus de bienvenue',
      value: { wood: 100, stone: 100, gold: 50 }
    },
    nextButton: 'J\'ai cliqué sur ma ville'
  },

  // Étape 3: Construction Hôtel de Ville
  {
    id: 'build_townhall',
    title: '🏛️ Construction de l\'Hôtel de Ville',
    description: 'L\'Hôtel de Ville est le cœur de ton village ! Construis-le sur un emplacement vide pour commencer ton développement.',
    target: '.grid-cell.empty',
    position: 'top',
    reward: {
      type: 'resources',
      description: '🎁 Ressources de démarrage',
      value: { population: 30, wood: 50, cereal: 50 }
    },
    validation: {
      type: 'api_check',
      apiEndpoint: '/api/universe',
      apiCondition: (data: any, playerId?: string) => {
        const cities = data?.cities || [];
        const playerCity = cities.find((c: any) => c.owner === playerId);
        if (playerCity) {
          const buildings = playerCity.buildings || [];
          return buildings.some((b: any) => b.name === 'Hôtel de Ville' && b.status === 'Terminé');
        }
        return false;
      }
    },
    nextButton: 'Construire l\'Hôtel de Ville'
  },

  // Étape 4: Construction Académie
  {
    id: 'build_academy',
    title: '🎓 Construction de l\'Académie',
    description: 'L\'Académie génère des points de recherche ! Construis-la pour débloquer des technologies avancées.',
    target: '.grid-cell.empty',
    position: 'top',
    reward: {
      type: 'resources',
      description: '🎁 Bonus de connaissance + Population',
      value: { gold: 30, research_points: 20, population: 10 }
    },
    validation: {
      type: 'api_check',
      apiEndpoint: '/api/universe',
      apiCondition: (data: any, playerId?: string) => {
        const cities = data?.cities || [];
        const playerCity = cities.find((c: any) => c.owner === playerId);
        if (playerCity) {
          const buildings = playerCity.buildings || [];
          return buildings.some((b: any) => b.name === 'Academy' && b.status === 'Terminé');
        }
        return false;
      }
    },
    nextButton: 'Construire l\'Académie'
  },

  // Étape 4: Affecter ouvrier à l'Académie
  {
    id: 'assign_worker_academy',
    title: '👷 Affecter des ouvriers',
    description: 'Pour que l\'Académie produise des points de recherche, tu dois y affecter des ouvriers ! Clique sur l\'Académie puis affecte au moins 5 ouvriers.',
    target: '.building-card',
    position: 'top',
    reward: {
      type: 'resources',
      description: '🎁 Bonus de productivité',
      value: { gold: 40, research_points: 30 }
    },
    validation: {
      type: 'api_check',
      apiEndpoint: '/api/universe',
      apiCondition: (data: any, playerId?: string) => {
        const cities = data?.cities || [];
        const playerCity = cities.find((c: any) => c.owner === playerId);
        if (playerCity) {
          const workers = playerCity.workers_assigned || {};
          return (workers.academy || 0) >= 5;
        }
        return false;
      }
    },
    nextButton: 'Affecter les ouvriers',
    skipButton: true
  },

  // Étape 5: Débloquer la recherche Maison du Chef de Village
  {
    id: 'unlock_chief_house',
    title: '📚 Recherche : Maison du Chef de Village',
    description: 'Va dans le menu Recherche et débloque la technologie "Maison du Chef de Village" pour accéder aux quêtes quotidiennes ! Une fois débloquée, clique sur le bouton ci-dessous.',
    target: 'a[href="/research"]',
    position: 'bottom',
    page: '/village',
    reward: {
      type: 'research_points',
      description: '🎁 Points de recherche bonus',
      value: { research_points: 50 }
    },
    validation: {
      type: 'manual'
    },
    nextButton: 'J\'ai débloqué la Maison du Chef'
  },

  // Étape 6: Affecter ouvriers à la forêt
  {
    id: 'assign_worker_forest',
    title: '🌲 Production de bois',
    description: 'Pour produire du bois, affecte au moins 5 ouvriers à la forêt ! Clique sur une forêt (case avec des arbres) puis affecte des ouvriers.',
    target: '.resource-cell',
    position: 'top',
    reward: {
      type: 'resources',
      description: '🎁 Bonus de production',
      value: { wood: 50, gold: 30 }
    },
    validation: {
      type: 'api_check',
      apiEndpoint: '/api/universe',
      apiCondition: (data: any, playerId?: string) => {
        const cities = data?.cities || [];
        const playerCity = cities.find((c: any) => c.owner === playerId);
        if (playerCity) {
          const workers = playerCity.workers_assigned || {};
          return (workers.forest || 0) >= 5;
        }
        return false;
      }
    },
    nextButton: 'Affecter les ouvriers',
    skipButton: true
  },

  // Étape 7: Construction Caserne
  {
    id: 'build_barracks',
    title: '⚔️ Construction de la Caserne',
    description: 'Pour former une armée, tu as besoin d\'une Caserne ! Retourne à ton village et construis-la.',
    target: '.grid-cell.empty',
    position: 'top',
    reward: {
      type: 'resources',
      description: '🎁 Ressources militaires',
      value: { gold: 60, iron: 30 }
    },
    validation: {
      type: 'api_check',
      apiEndpoint: '/api/universe',
      apiCondition: (data: any, playerId?: string) => {
        const cities = data?.cities || [];
        const playerCity = cities.find((c: any) => c.owner === playerId);
        if (playerCity) {
          const buildings = playerCity.buildings || [];
          return buildings.some((b: any) => b.name === 'Caserne' && b.status === 'Terminé');
        }
        return false;
      }
    },
    nextButton: 'Construire la Caserne'
  },

  // Étape 7: Formation de 5 Miliciens
  {
    id: 'train_militia',
    title: '⚔️ Formation de Miliciens',
    description: 'Clique sur la Caserne et forme 5 Miliciens ! Ce sont des unités de base très efficaces pour débuter.',
    target: '.building-card',
    position: 'top',
    reward: {
      type: 'units',
      description: '🎁 Renfort militaire',
      value: { militia: 5 }
    },
    validation: {
      type: 'api_check',
      apiEndpoint: '/api/universe',
      apiCondition: (data: any, playerId?: string) => {
        const cities = data?.cities || [];
        const playerCity = cities.find((c: any) => c.owner === playerId);
        if (playerCity) {
          const garrison = playerCity.military?.garrison || {};
          const playerGarrison = garrison[playerId || ''] || {};
          const militia = playerGarrison.militia?.quantity || 0;
          return militia >= 5;
        }
        return false;
      }
    },
    nextButton: 'Former les Miliciens',
    skipButton: true
  },

  // Étape 8: Construire un Port
  {
    id: 'build_port',
    title: '🚢 Construire un Port',
    description: 'Construis un Port pour pouvoir transporter des ressources et des troupes entre tes villes !',
    target: '.building-slot',
    position: 'top',
    reward: {
      type: 'resources',
      description: '🎁 Aide à la construction',
      value: { wood: 100, stone: 50 }
    },
    validation: {
      type: 'api_check',
      apiEndpoint: '/api/universe',
      apiCondition: (data: any, playerId?: string) => {
        const cities = data?.cities || [];
        const playerCity = cities.find((c: any) => c.owner === playerId);
        if (playerCity) {
          const buildings = playerCity.buildings || [];
          return buildings.some((b: any) => b.name === 'Port' && b.status === 'Terminé');
        }
        return false;
      }
    },
    nextButton: 'Construire le Port'
  },

  // Étape 9: Attaquer un camp des sauvages
  {
    id: 'attack_barbarian',
    title: '⚔️ Premier combat !',
    description: 'Il est temps de tester ton armée ! Va sur la carte de l\'Île et clique sur un camp des sauvages (point rouge) pour l\'attaquer.',
    target: 'a[href="/island"]',
    position: 'bottom',
    reward: {
      type: 'resources',
      description: '🎁 Récompense de combat',
      value: { gold: 100, wood: 50, stone: 50 }
    },
    validation: {
      type: 'manual'
    },
    nextButton: 'Aller à l\'Île'
  },

  // Étape 10: Continuer l'exploration
  {
    id: 'continue_exploration',
    title: '🗺️ Continue ton aventure !',
    description: 'Tu as maintenant toutes les bases ! Continue à développer ton village, attaque d\'autres camps des sauvages, et étends ton empire sur l\'île.',
    position: 'center',
    reward: {
      type: 'resources',
      description: '🎁 Récompenses d\'exploration',
      value: { wood: 100, stone: 100, gold: 100, iron: 50 }
    },
    nextButton: 'Compris !'
  },

  // Étape finale
  {
    id: 'tutorial_complete',
    title: '🎉 Tutoriel terminé !',
    description: 'Félicitations ! Tu maîtrises les bases. Continue à développer ton empire, recherche de nouvelles technologies, et conquiers l\'île ! Voici un cadeau de fin de tutoriel.',
    position: 'center',
    reward: {
      type: 'resources',
      description: '🎁 Récompense finale',
      value: { wood: 200, stone: 200, gold: 150, iron: 50 }
    },
    nextButton: 'Commencer l\'aventure !',
    skipButton: false
  }
];

// Fonction pour obtenir les récompenses totales du tutoriel
export function getTotalTutorialRewards(): Record<string, number> {
  const total: Record<string, number> = {};
  
  tutorialSteps.forEach(step => {
    if (step.reward && step.reward.value) {
      Object.entries(step.reward.value).forEach(([resource, amount]) => {
        total[resource] = (total[resource] || 0) + amount;
      });
    }
  });
  
  return total;
}

// Fonction pour obtenir une étape par ID
export function getTutorialStep(stepId: string): TutorialStep | undefined {
  return tutorialSteps.find(step => step.id === stepId);
}

// Fonction pour obtenir l'étape suivante
export function getNextTutorialStep(currentStepId: string): TutorialStep | null {
  const currentIndex = tutorialSteps.findIndex(step => step.id === currentStepId);
  if (currentIndex === -1 || currentIndex === tutorialSteps.length - 1) {
    return null;
  }
  return tutorialSteps[currentIndex + 1];
}
