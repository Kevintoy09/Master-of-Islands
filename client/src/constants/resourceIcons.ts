/**
 * Configuration centralisée des icônes/émojis pour les ressources
 * Utilisé dans HeaderBar, popups, et autres composants
 */

export const RESOURCE_EMOJIS: { [key: string]: string } = {
  // Ressources de base
  wood: "🪵",
  stone: "🗿", // Pierre de l'île de Pâques - plus représentatif que 🪨
  iron: "⛏️", // Pioche - plus représentatif que ⚙️ pour le minerai
  cereal: "🌾",
  papyrus: "📜",
  horse: "🐎",
  marble: "🏛️", // Temple grec - évoque l'architecture en marbre
  glass: "🔷",
  wine: "🍇",
  coal: "⚫", // Carré noir - forme géométrique simple
  gunpowder: "💥", // Tonneau en bois pour stocker la poudre
  spices: "🌶️",
  cotton: "☁️",
  
  // Ressources spéciales
  gold: "🪙",
  diamonds: "💎",
  transport_ships: "⛵", // Voilier antique - plus rustique que 🚢
  
  // Population
  population_total: "👥",
  population_free: "🧑", // Personne seule pour "libre"
  population: "👥",
  
  // Recherche
  research_points: "🔬", // Microscope au lieu de ⭐
  research: "🔬",
  
  // Quêtes
  quest_points: "🏆",
  
  // Autres
  city: "🏰", // Château - cité fortifiée
  player: "👤"
};

/**
 * Émojis spécialisés pour les interfaces utilisateur
 */
export const UI_EMOJIS: { [key: string]: string } = {
  // Popups et fenêtres
  population_popup: "🏘️",
  production_popup: "⚙️",
  building_popup: "🏗️",
  research_popup: "🔬",
  transport_popup: "🚚",
  gold_popup: "🏦",
  
  // Statistiques et indicateurs
  growth: "📈",
  decline: "📉",
  statistics: "📊",
  info: "💡",
  warning: "⚠️",
  error: "❌",
  success: "✅",
  
  // Actions
  build: "🔨",
  destroy: "💥",
  upgrade: "⬆️",
  downgrade: "⬇️",
  close: "✖️",
  
  // Catégories de bâtiments
  military: "⚔️",
  economic: "💰",
  cultural: "🎭",
  defensive: "🛡️",
  
  // Temps et progression
  time: "⏰",
  speed: "⚡",
  progress: "📈",
  
  // Notifications et transport
  ship: "🚢",
  research: "🔬",
  message: "📨",
  general: "📋"
};

/**
 * Labels français pour les ressources
 */
export const RESOURCE_LABELS: { [key: string]: string } = {
  wood: "Bois",
  stone: "Pierre",
  iron: "Fer",
  cereal: "Céréales",
  papyrus: "Papyrus",
  horse: "Chevaux",
  marble: "Marbre",
  glass: "Verre",
  wine: "Vin",
  coal: "Charbon",
  gunpowder: "Poudre",
  spices: "Épices",
  cotton: "Coton",
  gold: "Or",
  diamonds: "Diamants",
  transport_ships: "Bateaux",
  population_total: "Pop. totale",
  population_free: "Pop. libre",
  research_points: "Recherche",
  quest_points: "Points de quête",
  cereal_needed: "Céréales nécessaires"
};

/**
 * Fonction utilitaire pour obtenir l'emoji d'une ressource
 */
export const getResourceEmoji = (resourceKey: string): string => {
  return RESOURCE_EMOJIS[resourceKey] || "❓";
};

/**
 * Fonction utilitaire pour obtenir le label d'une ressource
 */
export const getResourceLabel = (resourceKey: string): string => {
  return RESOURCE_LABELS[resourceKey] || resourceKey;
};

/**
 * Fonction utilitaire pour obtenir un emoji d'interface
 */
export const getUIEmoji = (uiKey: string): string => {
  return UI_EMOJIS[uiKey] || "❓";
};
