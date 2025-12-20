import { useState, useCallback } from 'react';

interface UseZoomAndDragOptions {
  minZoom?: number;
  maxZoom?: number;
  initialZoom?: number;
  mapWidth?: number;
  mapHeight?: number;
}

export const useZoomAndDrag = (options: UseZoomAndDragOptions = {}) => {
  const {
    minZoom = 0.5,
    maxZoom = 2.5,
    initialZoom = 1,
    mapWidth = window.innerWidth,
    mapHeight = window.innerHeight
  } = options;

  const [zoom, setZoom] = useState(initialZoom);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [drag, setDrag] = useState<{ startX: number, startY: number, origX: number, origY: number } | null>(null);
  const [lastTouchDistance, setLastTouchDistance] = useState<number | null>(null);
  const [hasDragged, setHasDragged] = useState(false); // Pour détecter si c'est un drag ou un click

  // Fonction pour contraindre les offsets pendant le drag (permet d'aller aux bords)
  const constrainOffsetForDrag = useCallback((offsetX: number, offsetY: number, currentZoom: number) => {
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const scaledMapWidth = mapWidth * currentZoom;
    const scaledMapHeight = mapHeight * currentZoom;
    
    // Ajouter des marges pour compenser les zones masquées par header et bottombar
    const headerMargin = 80; // Environ la hauteur du header
    const bottombarMargin = 80; // Environ la hauteur du bottombar
    
    // Pour le drag : on peut aller jusqu'aux bords PLUS les marges pour voir les zones masquées
    let minX = viewportWidth - scaledMapWidth; // Bord gauche visible
    let maxX = 0; // Bord droit visible
    let minY = viewportHeight - scaledMapHeight - bottombarMargin; // Bord haut visible + marge bottombar
    let maxY = headerMargin; // Bord bas visible + marge header
    
    // Si la carte est plus petite que la viewport, la centrer
    if (scaledMapWidth <= viewportWidth) {
      const centerX = (viewportWidth - scaledMapWidth) / 2;
      minX = maxX = centerX;
    }
    
    if (scaledMapHeight <= viewportHeight) {
      const centerY = (viewportHeight - scaledMapHeight) / 2;
      minY = maxY = centerY;
    }
    
    // Appliquer les contraintes
    offsetX = Math.max(minX, Math.min(maxX, offsetX));
    offsetY = Math.max(minY, Math.min(maxY, offsetY));
    
    return { x: offsetX, y: offsetY };
  }, [mapWidth, mapHeight]);

  // Fonction pour contraindre les offsets pendant le zoom (empêche de voir du vide)
  const constrainOffsetForZoom = useCallback((offsetX: number, offsetY: number, currentZoom: number) => {
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const scaledMapWidth = mapWidth * currentZoom;
    const scaledMapHeight = mapHeight * currentZoom;
    
    // Pour le zoom : la carte doit toujours remplir l'écran (pas de vide visible)
    // Si la carte est plus petite que la viewport, empêcher de dézoom davantage
    if (scaledMapWidth < viewportWidth || scaledMapHeight < viewportHeight) {
      // Calculer le zoom minimum pour que la carte remplisse l'écran
      const minZoomX = viewportWidth / mapWidth;
      const minZoomY = viewportHeight / mapHeight;
      const calculatedMinZoom = Math.max(minZoomX, minZoomY);
      
      // Si on est en dessous du zoom minimum, on force le recentrage
      if (currentZoom < calculatedMinZoom) {
        const centerX = (viewportWidth - scaledMapWidth) / 2;
        const centerY = (viewportHeight - scaledMapHeight) / 2;
        return { x: centerX, y: centerY };
      }
    }
    
    // Sinon, utiliser les mêmes contraintes que le drag
    return constrainOffsetForDrag(offsetX, offsetY, currentZoom);
  }, [mapWidth, mapHeight, constrainOffsetForDrag]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    // Ignorer les clics sur les boutons et éléments interactifs
    const target = e.target as HTMLElement;
    if (target.tagName === 'BUTTON' || target.closest('button')) {
      return;
    }
    
    setHasDragged(false);
    setDrag({
      startX: e.clientX,
      startY: e.clientY,
      origX: offset.x,
      origY: offset.y,
    });
  }, [offset]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (drag) {
      const deltaX = e.clientX - drag.startX;
      const deltaY = e.clientY - drag.startY;
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
      
      // Si le mouvement dépasse 5px, c'est un drag
      if (distance > 5) {
        setHasDragged(true);
      }
      
      const newOffsetX = drag.origX + deltaX;
      const newOffsetY = drag.origY + deltaY;
      const constrainedOffset = constrainOffsetForDrag(newOffsetX, newOffsetY, zoom);
      setOffset(constrainedOffset);
    }
  }, [drag, zoom, constrainOffsetForDrag]);

  const handleMouseUp = useCallback(() => {
    setDrag(null);
    // Réinitialiser hasDragged après mouseUp (avec un léger délai pour que les onClick puissent lire l'état)
    setTimeout(() => setHasDragged(false), 0);
  }, []);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    
    // Obtenir la position de la souris dans la viewport
    const mouseX = e.clientX;
    const mouseY = e.clientY;
    
    // Calculer le zoom minimum pour éviter de voir du vide
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const minZoomX = viewportWidth / mapWidth;
    const minZoomY = viewportHeight / mapHeight;
    const dynamicMinZoom = Math.max(minZoomX, minZoomY);
    
    // Calculer le nouveau zoom avec le minimum dynamique
    const zoomDelta = -e.deltaY * 0.001;
    let newZoom = zoom + zoomDelta;
    newZoom = Math.max(Math.max(dynamicMinZoom, minZoom), Math.min(maxZoom, newZoom));
    
    // Si le zoom n'a pas changé, ne rien faire
    if (newZoom === zoom) return;
    
    // Calculer la position dans la carte avant le zoom
    const mapX = (mouseX - offset.x) / zoom;
    const mapY = (mouseY - offset.y) / zoom;
    
    // Calculer le nouvel offset pour que le point sous la souris reste fixe
    const newOffsetX = mouseX - mapX * newZoom;
    const newOffsetY = mouseY - mapY * newZoom;
    
    // Appliquer les contraintes
    const constrainedOffset = constrainOffsetForZoom(newOffsetX, newOffsetY, newZoom);
    
    setOffset(constrainedOffset);
    setZoom(newZoom);
  }, [zoom, offset, mapWidth, mapHeight, minZoom, maxZoom, constrainOffsetForZoom]);

  // Fonction pour centrer la vue sur un point spécifique
  const centerOnPoint = useCallback((x: number, y: number) => {
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    const targetX = viewportWidth / 2 - x * zoom;
    const targetY = viewportHeight / 2 - y * zoom;
    
    const constrainedOffset = constrainOffsetForZoom(targetX, targetY, zoom);
    setOffset(constrainedOffset);
  }, [zoom, constrainOffsetForZoom]);

  // Fonction utilitaire pour calculer la distance entre deux points tactiles
  const getTouchDistance = useCallback((touch1: React.Touch, touch2: React.Touch) => {
    const dx = touch1.clientX - touch2.clientX;
    const dy = touch1.clientY - touch2.clientY;
    return Math.sqrt(dx * dx + dy * dy);
  }, []);

  // Gestion du début des événements tactiles
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    // Ignorer les touches sur les boutons et éléments interactifs
    const target = e.target as HTMLElement;
    if (target.tagName === 'BUTTON' || target.closest('button')) {
      return;
    }
    
    if (e.touches.length === 2) {
      // Pinch-to-zoom avec deux doigts
      e.preventDefault();
      const distance = getTouchDistance(e.touches[0], e.touches[1]);
      setLastTouchDistance(distance);
      setDrag(null); // Arrêter le drag s'il était en cours
    } else if (e.touches.length === 1) {
      // Drag avec un doigt
      const touch = e.touches[0];
      setHasDragged(false);
      setDrag({
        startX: touch.clientX,
        startY: touch.clientY,
        origX: offset.x,
        origY: offset.y
      });
      setLastTouchDistance(null);
    }
  }, [offset, getTouchDistance]);

  // Gestion du mouvement tactile
  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 2 && lastTouchDistance !== null) {
      // Pinch-to-zoom
      e.preventDefault();
      const distance = getTouchDistance(e.touches[0], e.touches[1]);
      const scale = distance / lastTouchDistance;
      
      // Calculer le centre du pinch
      const centerX = (e.touches[0].clientX + e.touches[1].clientX) / 2;
      const centerY = (e.touches[0].clientY + e.touches[1].clientY) / 2;
      
      // Appliquer le zoom avec le même algorithme que la molette
      const newZoom = Math.max(minZoom, Math.min(maxZoom, zoom * scale));
      
      if (newZoom !== zoom) {
        // Calculer le nouvel offset pour zoomer sur le centre du pinch
        const scaleFactor = newZoom / zoom;
        const newOffsetX = centerX - (centerX - offset.x) * scaleFactor;
        const newOffsetY = centerY - (centerY - offset.y) * scaleFactor;
        
        const constrainedOffset = constrainOffsetForZoom(newOffsetX, newOffsetY, newZoom);
        setOffset(constrainedOffset);
        setZoom(newZoom);
      }
      
      setLastTouchDistance(distance);
    } else if (e.touches.length === 1 && drag) {
      // Drag avec un doigt
      e.preventDefault();
      const touch = e.touches[0];
      const deltaX = touch.clientX - drag.startX;
      const deltaY = touch.clientY - drag.startY;
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
      
      // Si le mouvement dépasse 10px sur mobile, c'est un drag (seuil plus élevé que desktop)
      if (distance > 10) {
        setHasDragged(true);
      }
      
      const newOffsetX = drag.origX + deltaX;
      const newOffsetY = drag.origY + deltaY;
      const constrainedOffset = constrainOffsetForDrag(newOffsetX, newOffsetY, zoom);
      setOffset(constrainedOffset);
    }
  }, [drag, zoom, offset, lastTouchDistance, minZoom, maxZoom, constrainOffsetForDrag, constrainOffsetForZoom, getTouchDistance]);

  // Gestion de la fin des événements tactiles
  const handleTouchEnd = useCallback(() => {
    setDrag(null);
    setLastTouchDistance(null);
    // Réinitialiser hasDragged après touchEnd (avec un léger délai pour que les onClick puissent lire l'état)
    setTimeout(() => setHasDragged(false), 0);
  }, []);

  return {
    zoom,
    offset,
    drag,
    hasDragged,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    handleWheel,
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
    centerOnPoint,
    setZoom,
    setOffset
  };
};
