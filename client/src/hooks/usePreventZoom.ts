import { useEffect } from 'react';

/**
 * SOLUTION COMPLÈTE ANTI-ZOOM POPUP
 * 
 * UN SEUL FICHIER POUR TOUT GÉRER !
 * Code testé et fonctionnel sur Firefox et autres navigateurs.
 */

// =============================================================================
// HOOK POUR EMPÊCHER LE ZOOM
// =============================================================================

/**
 * Hook pour empêcher le zoom sur un popup/composant
 * @param isActive - Si true, active la prévention du zoom
 */
export const usePreventZoom = (isActive: boolean = true) => {
  useEffect(() => {
    if (!isActive) return;

    const preventZoom = (e: KeyboardEvent) => {
      // Bloquer Ctrl + touches de zoom
      if (e.ctrlKey && ['+', '-', '=', '0'].includes(e.key)) {
        e.preventDefault();
        e.stopImmediatePropagation();
      }
    };

    const preventWheelZoom = (e: WheelEvent) => {
      // Bloquer Ctrl + molette
      if (e.ctrlKey) {
        e.preventDefault();
        e.stopImmediatePropagation();
      }
    };

    // Ajouter les event listeners de manière agressive
    document.addEventListener('keydown', preventZoom, { capture: true, passive: false });
    document.addEventListener('wheel', preventWheelZoom, { capture: true, passive: false });
    window.addEventListener('wheel', preventWheelZoom, { capture: true, passive: false });

    return () => {
      document.removeEventListener('keydown', preventZoom, { capture: true });
      document.removeEventListener('wheel', preventWheelZoom, { capture: true });
      window.removeEventListener('wheel', preventWheelZoom, { capture: true });
    };
  }, [isActive]);
};

// =============================================================================
// HANDLERS REACT POUR ÉVÉNEMENTS
// =============================================================================

/**
 * Handler pour l'overlay - BLOQUE SEULEMENT ZOOM CTRL+WHEEL
 * À utiliser sur l'élément de fond du popup
 */
export const handleOverlayWheel = (e: React.WheelEvent) => {
  // Ne bloquer que le zoom (Ctrl+wheel), pas la molette normale
  if (e.ctrlKey || e.metaKey) {
    e.preventDefault();
    e.stopPropagation();
  }
  // ✅ CORRECTION: Laisser passer la molette normale pour le zoom du battlefield
};

/**
 * Handler pour le contenu - AUTORISE scroll sauf zoom
 * À utiliser sur le container de contenu du popup
 */
export const handleContentWheel = (e: React.WheelEvent) => {
  if (e.ctrlKey) {
    e.preventDefault();
    e.stopPropagation();
  }
  // Pour le scroll normal, on laisse passer
};

// =============================================================================
// EXPORT DEFAULT
// =============================================================================

export default usePreventZoom;