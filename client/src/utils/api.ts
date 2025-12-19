// Utilitaire pour interagir avec l'API Flask
// Configuration automatique de l'URL selon l'environnement
// Fix: Production utilise URL relative pour Railway
const getApiUrl = () => {
  if (process.env.NODE_ENV === 'production') {
    return ""; // Production: URL relative
  }
  
  // Développement local
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return "http://localhost:5000";
  }
  
  // Réseau local (mobile/tablette)
  return "http://192.168.1.246:5000";
};

export { getApiUrl }; // Export pour utilisation dans d'autres fichiers
export const API_URL = getApiUrl(); // Préfixe racine Flask

export async function login(username: string, password: string) {
  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) throw new Error("Login échoué");
  return response.json();
}

export async function getIslands() {
  const response = await fetch(`${API_URL}/api/city/islands`);
  if (!response.ok) throw new Error("Impossible de charger les îles");
  return response.json();
}

export async function selectIsland(userId: string, islandId: string) {
  const response = await fetch(`${API_URL}/api/city/select-island`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ userId, islandId }),
  });
  if (!response.ok) throw new Error("Sélection d'île échouée");
  return response.json();
}

// Ajoute ici d'autres fonctions pour l'API (getWorld, getCity, etc.)
