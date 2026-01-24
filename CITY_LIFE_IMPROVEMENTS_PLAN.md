# 🏛️ PLAN D'AMÉLIORATION - VIE DANS LA CITYPAGE

## 📊 État actuel
- ✅ Image de fond fixe 1920×1080 (4 layouts différents)
- ✅ Bâtiments PNG positionnés en slots
- ✅ Animation hover basique (scale 1.1)
- ✅ Glow construction en cours
- ❌ **AUCUN élément vivant/animé**

---

## 🎯 OBJECTIFS
Transformer la CityPage d'une **image statique** en un **environnement vivant** qui donne envie d'y rester

---

## 🚀 PHASE 1 : Quick Wins (2-3h d'implémentation)

### 1.1 Animations CSS des bâtiments existants
**Fichier** : `CityMap.module.css`

```css
/* Fumée/vapeur sur bâtiments actifs */
.building-smoke {
  position: absolute;
  top: -30px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 40px;
  background: radial-gradient(circle, rgba(200,200,200,0.4), transparent);
  animation: smoke-rise 3s ease-in-out infinite;
  pointer-events: none;
}

@keyframes smoke-rise {
  0% { 
    opacity: 0.6; 
    transform: translateX(-50%) translateY(0) scale(0.5); 
  }
  100% { 
    opacity: 0; 
    transform: translateX(-50%) translateY(-40px) scale(1.5); 
  }
}

/* Lueur activité sur Hôtel de Ville, Academy, Barracks */
.building-activity-glow {
  animation: activity-pulse 2s ease-in-out infinite;
}

@keyframes activity-pulse {
  0%, 100% { filter: drop-shadow(0 0 5px rgba(255, 215, 0, 0.3)); }
  50% { filter: drop-shadow(0 0 15px rgba(255, 215, 0, 0.6)); }
}

/* Animation de battement sur bâtiment en construction */
.building-under-construction {
  animation: construction-beat 0.8s ease-in-out infinite;
}

@keyframes construction-beat {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

/* Particules scintillantes autour de Academy (recherche) */
.research-sparkles {
  position: absolute;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.sparkle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: #FFD700;
  border-radius: 50%;
  animation: sparkle-twinkle 2s ease-in-out infinite;
}

@keyframes sparkle-twinkle {
  0%, 100% { opacity: 0; transform: scale(0); }
  50% { opacity: 1; transform: scale(1); }
}
```

**Implémentation** : Ajouter des classes conditionnelles dans `CityMap.tsx` selon le type de bâtiment

---

### 1.2 Citoyens animés (sprites CSS simples)
**Fichier** : `CityMap.tsx` + nouveau composant `CitizenSprite.tsx`

```tsx
// CitizenSprite.tsx
interface CitizenSpriteProps {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  delay: number;
}

const CitizenSprite: React.FC<CitizenSpriteProps> = ({ startX, startY, endX, endY, delay }) => {
  return (
    <div
      className="citizen-sprite"
      style={{
        position: 'absolute',
        left: `${startX}px`,
        top: `${startY}px`,
        width: '20px',
        height: '20px',
        fontSize: '20px',
        animation: `walk-path 8s linear ${delay}s infinite`,
        '--end-x': `${endX}px`,
        '--end-y': `${endY}px`,
      } as React.CSSProperties}
    >
      🚶
    </div>
  );
};
```

```css
/* CityMap.module.css */
@keyframes walk-path {
  0% { 
    left: var(--start-x, 0); 
    top: var(--start-y, 0); 
  }
  100% { 
    left: var(--end-x, 0); 
    top: var(--end-y, 0); 
  }
}

.citizen-sprite {
  --start-x: 0px;
  --start-y: 0px;
  --end-x: 0px;
  --end-y: 0px;
  z-index: 5;
  pointer-events: none;
  filter: drop-shadow(0 1px 2px rgba(0,0,0,0.3));
}
```

**Nombre** : 5-8 citoyens par ville (selon population)

---

### 1.3 Oiseaux/nuages en arrière-plan
**Fichier** : `CityPage.tsx`

```tsx
// Dans le render, avant l'image de fond
<div className="ambient-elements">
  {/* Nuages flottants */}
  <div className="cloud cloud-1" style={{ top: '10%', animationDuration: '45s' }}>☁️</div>
  <div className="cloud cloud-2" style={{ top: '15%', animationDuration: '60s', animationDelay: '10s' }}>☁️</div>
  
  {/* Oiseaux occasionnels */}
  <div className="bird bird-1" style={{ top: '20%', animationDuration: '20s' }}>🕊️</div>
  <div className="bird bird-2" style={{ top: '25%', animationDuration: '25s', animationDelay: '8s' }}>🦅</div>
</div>
```

```css
.cloud {
  position: absolute;
  left: -100px;
  animation: float-across linear infinite;
  font-size: 40px;
  opacity: 0.5;
  z-index: 0;
}

@keyframes float-across {
  from { left: -100px; }
  to { left: 100%; }
}

.bird {
  position: absolute;
  right: -50px;
  animation: bird-fly linear infinite;
  font-size: 24px;
  z-index: 0;
}

@keyframes bird-fly {
  from { 
    right: -50px; 
    transform: translateY(0) rotate(-10deg); 
  }
  50% { 
    transform: translateY(-20px) rotate(-10deg); 
  }
  to { 
    right: 120%; 
    transform: translateY(0) rotate(-10deg); 
  }
}
```

---

## 🎨 PHASE 2 : Polish Visuel (4-6h)

### 2.1 Particules de célébration
**Fichier** : Nouveau `ParticleSystem.tsx`

```tsx
interface ParticleSystemProps {
  x: number;
  y: number;
  type: 'construction' | 'level-up' | 'research';
  count: number;
}

const ParticleSystem: React.FC<ParticleSystemProps> = ({ x, y, type, count }) => {
  const particles = Array.from({ length: count }, (_, i) => ({
    id: i,
    emoji: type === 'construction' ? '🔨' : type === 'research' ? '✨' : '⭐',
    delay: i * 0.1,
    angle: (360 / count) * i,
  }));

  return (
    <div style={{ position: 'absolute', left: x, top: y, pointerEvents: 'none' }}>
      {particles.map((p) => (
        <div
          key={p.id}
          className="particle"
          style={{
            '--angle': `${p.angle}deg`,
            animationDelay: `${p.delay}s`,
          } as React.CSSProperties}
        >
          {p.emoji}
        </div>
      ))}
    </div>
  );
};
```

```css
.particle {
  position: absolute;
  animation: particle-burst 1.2s ease-out forwards;
  font-size: 20px;
}

@keyframes particle-burst {
  0% {
    opacity: 1;
    transform: translate(0, 0) rotate(0deg) scale(1);
  }
  100% {
    opacity: 0;
    transform: translate(
      calc(cos(var(--angle)) * 80px),
      calc(sin(var(--angle)) * 80px)
    ) rotate(360deg) scale(0.3);
  }
}
```

**Trigger** : 
- Construction terminée
- Bâtiment level up
- Recherche terminée

---

### 2.2 Cycle jour/nuit subtil
**Fichier** : `CityPage.tsx`

```tsx
const [timeOfDay, setTimeOfDay] = useState<'day' | 'evening' | 'night'>('day');

useEffect(() => {
  const updateTime = () => {
    const hour = new Date().getHours();
    if (hour >= 6 && hour < 18) setTimeOfDay('day');
    else if (hour >= 18 && hour < 22) setTimeOfDay('evening');
    else setTimeOfDay('night');
  };
  
  updateTime();
  const interval = setInterval(updateTime, 60000); // Check every minute
  return () => clearInterval(interval);
}, []);
```

```css
.city-overlay-day { background: rgba(255, 255, 255, 0); }
.city-overlay-evening { background: rgba(255, 140, 0, 0.1); }
.city-overlay-night { background: rgba(0, 0, 50, 0.3); }
```

Overlay avec transition de 3s entre états

---

### 2.3 Effets météo aléatoires (optionnel)
```tsx
const [weather, setWeather] = useState<'clear' | 'rain' | 'snow'>('clear');

// Rain particles
<div className="rain-container">
  {weather === 'rain' && Array.from({ length: 50 }).map((_, i) => (
    <div key={i} className="raindrop" style={{ left: `${Math.random() * 100}%`, animationDelay: `${Math.random() * 2}s` }} />
  ))}
</div>
```

---

## 🔥 PHASE 3 : Game Feel Avancé (6-8h)

### 3.1 Sons environnementaux
**Fichiers audio** : `/public/assets/sounds/`
- `ambient-city.mp3` (marché, foule lointaine)
- `construction.mp3` (marteau, scie)
- `building-complete.mp3` (cloche)
- `citizens-chat.mp3` (voix)

```tsx
const playSound = (soundName: string, volume = 0.3) => {
  const audio = new Audio(`/assets/sounds/${soundName}.mp3`);
  audio.volume = volume;
  audio.play().catch(() => {}); // Ignore errors
};

// Trigger
useEffect(() => {
  if (selectedBuilding?.status === 'completed') {
    playSound('building-complete');
  }
}, [selectedBuilding]);
```

---

### 3.2 Animations de ressources transportées
**Fichier** : `ResourceTransportAnimation.tsx`

Quand un transport arrive :
- Petit chariot/bateau animé qui entre dans la ville
- "+500 🪵 +200 🪨" flottant au-dessus
- Particules dorées

```tsx
const ResourceArrivedAnimation: React.FC<{ resources: Record<string, number> }> = ({ resources }) => {
  return (
    <div className="resource-arrival">
      <div className="cart-animation">🚚</div>
      <div className="resource-popup">
        {Object.entries(resources).map(([key, value]) => (
          <div key={key} className="resource-line">
            +{value} {RESOURCE_EMOJIS[key]}
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

### 3.3 Bannières/drapeaux flottants
Sur Hôtel de Ville et muraille :

```css
.flag {
  position: absolute;
  top: 0;
  left: 50%;
  transform-origin: top left;
  animation: flag-wave 2s ease-in-out infinite;
}

@keyframes flag-wave {
  0%, 100% { transform: rotate(0deg) scaleY(1); }
  25% { transform: rotate(5deg) scaleY(0.95); }
  75% { transform: rotate(-5deg) scaleY(0.95); }
}
```

---

## 📊 MÉTRIQUES DE SUCCÈS

### Avant
- Temps moyen sur CityPage : **45 secondes**
- Taux d'interaction : **2 clics/visite**
- Sentiment : "C'est joli mais statique"

### Après (objectif)
- Temps moyen sur CityPage : **2-3 minutes**
- Taux d'interaction : **5+ clics/visite**
- Sentiment : "Ça bouge, c'est vivant !"

---

## 🗂️ FICHIERS À MODIFIER

### Phase 1 (Quick Wins)
1. ✏️ `client/src/components/CityMap.module.css` (+80 lignes)
2. ✏️ `client/src/components/CityMap.tsx` (+40 lignes)
3. ✏️ `client/src/pages/CityPage.tsx` (+30 lignes)
4. ➕ `client/src/components/CitizenSprite.tsx` (nouveau, 50 lignes)

### Phase 2 (Polish)
5. ➕ `client/src/components/ParticleSystem.tsx` (nouveau, 80 lignes)
6. ✏️ `client/src/pages/CityPage.tsx` (+60 lignes pour cycle jour/nuit)

### Phase 3 (Avancé)
7. ➕ `client/public/assets/sounds/` (fichiers audio)
8. ➕ `client/src/components/ResourceTransportAnimation.tsx` (nouveau, 100 lignes)
9. ➕ `client/src/hooks/useAmbientSounds.ts` (nouveau, 60 lignes)

---

## 💡 RECOMMANDATIONS TECHNIQUES

### Performance
- Utiliser `will-change` CSS pour animations
- Limiter nombre de citoyens selon CPU (5-8 max)
- Particules : max 20 simultanées, auto-cleanup après 2s
- Sons : volume 0.3 par défaut, mutable par user

### Mobile
- Désactiver citoyens sur petit écran (<768px)
- Réduire particules de moitié
- Pas de cycle jour/nuit (économie batterie)

### Accessibilité
- Option "Réduire les animations" dans Settings
- Sons désactivables via HeaderBar
- Pas de clignotements >3Hz (épilepsie)

---

## 🎯 ORDRE D'IMPLÉMENTATION SUGGÉRÉ

1. **Jour 1 : Animations bâtiments** (fumée, glow, construction)
2. **Jour 2 : Citoyens animés** (5-6 sprites)
3. **Jour 3 : Oiseaux/nuages + particules célébration**
4. **Jour 4 : Cycle jour/nuit**
5. **Jour 5 : Sons de base** (construction, célébration)
6. **Jour 6 : Polish final** (drapeaux, optimisations)

---

## 🚀 DÉMARRAGE RAPIDE

Voulez-vous que je commence par :
- **A** : Animations CSS des bâtiments (le plus facile, impact immédiat)
- **B** : Citoyens animés (effet "wow" garanti)
- **C** : Système de particules (explosions de joie)
- **D** : Cycle jour/nuit (ambiance immersive)

**Ma recommandation : Commencer par A + B (combinaison parfaite pour démo rapide)**
