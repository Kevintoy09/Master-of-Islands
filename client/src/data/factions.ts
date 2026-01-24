// Configuration des factions basées sur les ressources de départ

export interface Faction {
  id: string;
  name: string;
  motto: string;
  description: string;
  bonus: {
    description: string;
    value: string;
    icon: string;
  };
  bonusDetails?: Array<{
    icon: string;
    text: string;
  }>;
  logo: string;
  baseResource: string;
  theme: {
    primary: string;
    secondary: string;
    accent: string;
  };
}

export const FACTIONS: Record<string, Faction> = {
  stone: {
    id: 'stone',
    name: 'City of Builders',
    motto: 'Pierre par pierre, nous bâtissons l\'éternité',
    description: 'Les architectes légendaires qui érigent des merveilles indestructibles. Maîtres de la construction, leur héritage défie le temps.',
    bonus: {
      description: '-10% de temps pour construire et développer les bâtiments',
      value: '-10%',
      icon: '🏛️'
    },
    logo: '/assets/island_selection/faction_stone.png',
    baseResource: 'stone',
    theme: {
      primary: '#7d6e63',
      secondary: '#5d4e42',
      accent: '#a1887f'
    }
  },
  iron: {
    id: 'iron',
    name: 'Born for War',
    motto: 'Le fer est notre loi, la victoire notre destin',
    description: 'Guerriers nés pour le combat, forgés dans le feu de la bataille. Leur armée est redoutable, leur détermination sans faille.',
    bonus: {
      description: 'Réduction du coût d\'entretien des unités militaires et du temps de fabrication',
      value: '-10%',
      icon: '⚔️'
    },
    bonusDetails: [
      { icon: '💰', text: '-10% coût d\'entretien des unités militaires' },
      { icon: '⏳', text: '-10% temps de fabrication des unités' }
    ],
    logo: '/assets/island_selection/faction_iron.png',
    baseResource: 'iron',
    theme: {
      primary: '#8b0000',
      secondary: '#590000',
      accent: '#b22222'
    }
  },
  cereal: {
    id: 'cereal',
    name: 'Population First',
    motto: 'La prospérité naît de l\'abondance',
    description: 'Gardiens de la fertilité et de la croissance. Leur peuple prospère et se multiplie grâce à des récoltes généreuses.',
    bonus: {
      description: '+ 10 points de satisfaction ce qui augmente la croissance de la population',
      value: '+10',
      icon: '🌾'
    },
    logo: '/assets/island_selection/faction_cereal.png',
    baseResource: 'cereal',
    theme: {
      primary: '#f9a825',
      secondary: '#c17900',
      accent: '#fbc02d'
    }
  },
  papyrus: {
    id: 'papyrus',
    name: 'Knowledge is Power',
    motto: 'Dans le savoir réside la vraie puissance',
    description: 'Érudits et savants qui maîtrisent les arcanes du savoir. Leurs découvertes façonnent le futur de la civilisation.',
    bonus: {
      description: '+10% de productivité dans les académies',
      value: '+10%',
      icon: '📜'
    },
    logo: '/assets/island_selection/faction_papyrus.png',
    baseResource: 'papyrus',
    theme: {
      primary: '#5e35b1',
      secondary: '#4527a0',
      accent: '#7e57c2'
    }
  }
};

export const getFactionByResource = (resource: string): Faction | null => {
  return FACTIONS[resource] || null;
};
