/**
 * Utilitaires pour la gestion et le formatage du temps
 */

/**
 * Formate un temps en secondes vers un format lisible
 */
export const formatTime = (seconds: number): string => {
  if (seconds <= 0) return "Terminé";
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  } else {
    return `${secs}s`;
  }
};

/**
 * Formate un temps en secondes vers un format détaillé avec jours
 */
export const formatDetailedTime = (seconds: number): { display: string; parts: string[] } => {
  if (seconds <= 0) return { display: '0s', parts: [] };

  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  const parts = [];
  let display = '';

  if (days > 0) {
    parts.push(`${days}j`);
    display += `${days}j `;
  }
  if (hours > 0) {
    parts.push(`${hours}h`);
    display += `${hours}h `;
  }
  if (minutes > 0) {
    parts.push(`${minutes}m`);
    display += `${minutes}m `;
  }
  if (secs > 0 || (days === 0 && hours === 0 && minutes === 0)) {
    parts.push(`${secs}s`);
    display += `${secs}s`;
  }

  return { display: display.trim(), parts };
};

/**
 * Formate un temps pour les timers de ressources (format heure:minute)
 */
export const formatTimerDisplay = (seconds: number): string => {
  if (seconds <= 0) return "00:00";
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
  } else {
    const secs = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
};