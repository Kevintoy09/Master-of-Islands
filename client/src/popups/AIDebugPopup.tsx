import React, { useState, useEffect } from 'react';
import '../styles/AIDebugPopup.css';
import { useTurnLock } from '../context/TurnLockContext';

interface AIConfig {
  decision_weights: {
    priority_hero: number;
    priority_low_hp: number;
    priority_ranged: number;
    priority_closest: number;
    priority_threat_level: number;
  };
  behavior: {
    prefer_ranged_attacks: boolean;
    avoid_high_defense: boolean;
    focus_wounded: boolean;
  };
}

interface TargetScore {
  unitId: string;
  unitType: string;
  position: [number, number];
  totalScore: number;
  breakdown: {
    hero_bonus: number;
    hp_bonus: number;
    ranged_bonus: number;
    distance_penalty: number;
    threat_bonus: number;
  };
}

interface AIDebugPopupProps {
  battleId: string;
  onClose: () => void;
  deployedUnits: any[];
}

const AIDebugPopup: React.FC<AIDebugPopupProps> = ({ battleId, onClose, deployedUnits }) => {
  const [config, setConfig] = useState<AIConfig | null>(null);
  const [selectedUnitId, setSelectedUnitId] = useState<string>('');
  const [targetScores, setTargetScores] = useState<TargetScore[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [aiAutoEnabled, setAiAutoEnabled] = useState(false);
  const [loadingAutoStatus, setLoadingAutoStatus] = useState(true);
  const [timerPaused, setTimerPaused] = useState<boolean | null>(null);
  const [loadingTimer, setLoadingTimer] = useState(false);
  
  // Hook de verrouillage des tours
  const { isLocked: turnLockEnabled, toggleLock: toggleTurnLock } = useTurnLock();
  
  // États pour le drag & resize
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [position, setPosition] = useState({ x: window.innerWidth / 2, y: window.innerHeight / 2 });
  const [isMinimized, setIsMinimized] = useState(false);

  // Charger la config IA au démarrage
  useEffect(() => {
    loadAIConfig();
    loadAutoStatus();
  }, []);

  const loadTimerStatus = async () => {
    try {
      // Charger depuis battlesv2.json via l'endpoint de statut
      const response = await fetch(`/api/v2/battle/status/${battleId}`);
      if (!response.ok) {
        console.warn('⚠️ Endpoint status non disponible, timer par défaut: non pausé');
        setTimerPaused(false);
        return;
      }
      
      const data = await response.json();
      if (data && data.success) {
        // Vérifier si timer.paused existe dans les données de bataille
        setTimerPaused(data.timer?.paused || false);
      } else {
        setTimerPaused(false);
      }
    } catch (error) {
      console.error('❌ Erreur chargement statut timer:', error);
      setTimerPaused(false); // Par défaut: actif
    }
  };

  const toggleTimer = async () => {
    setLoadingTimer(true);
    try {
      // Toggle: inverse de l'état actuel
      const newPausedState = !timerPaused;
      
      const response = await fetch(`/api/v2/battles/${battleId}/timer/pause`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paused: newPausedState })
      });
      
      if (response.ok) {
        setTimerPaused(newPausedState);
        addLog(`⏱️ Timer ${newPausedState ? 'ARRÊTÉ' : 'REDÉMARRÉ'}`);
      } else {
        addLog('❌ Erreur lors du toggle du timer');
      }
    } catch (error) {
      console.error('❌ Erreur toggle timer:', error);
      addLog('❌ Erreur toggle timer');
    } finally {
      setLoadingTimer(false);
    }
  };

  const loadAIConfig = async () => {
    try {
      const response = await fetch('/api/v2/ai/config');
      const data = await response.json();
      setConfig(data);
      addLog('✅ Configuration IA chargée');
    } catch (error) {
      addLog(`❌ Erreur chargement config: ${error}`);
    }
  };

  const loadAutoStatus = async () => {
    try {
      const response = await fetch('/api/admin/ai/auto-status');
      const data = await response.json();
      if (data.success) {
        setAiAutoEnabled(data.ai_auto_enabled);
        addLog(`🤖 Auto-IA: ${data.ai_auto_enabled ? 'ACTIVÉE ✅' : 'DÉSACTIVÉE ❌'}`);
      }
    } catch (error) {
      addLog(`❌ Erreur chargement statut auto-IA: ${error}`);
    } finally {
      setLoadingAutoStatus(false);
    }
  };

  const toggleAutoAI = async () => {
    try {
      const response = await fetch('/api/admin/ai/toggle-auto', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const data = await response.json();
      if (data.success) {
        setAiAutoEnabled(data.ai_auto_enabled);
        addLog(`🤖 Auto-IA ${data.ai_auto_enabled ? 'ACTIVÉE ✅' : 'DÉSACTIVÉE ❌'}`);
      } else {
        addLog(`❌ Erreur toggle auto-IA`);
      }
    } catch (error) {
      addLog(`❌ Erreur: ${error}`);
    }
  };

  const saveAIConfig = async () => {
    if (!config) return;
    
    try {
      const response = await fetch('/api/v2/ai/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      
      if (response.ok) {
        addLog('✅ Configuration IA sauvegardée');
      } else {
        addLog('❌ Erreur sauvegarde config');
      }
    } catch (error) {
      addLog(`❌ Erreur: ${error}`);
    }
  };

  const testUnitBehavior = async () => {
    if (!selectedUnitId) {
      addLog('⚠️ Sélectionnez une unité');
      return;
    }

    setLoading(true);
    addLog(`🤖 Test comportement de ${selectedUnitId}...`);

    try {
      const response = await fetch('/api/v2/ai/test-unit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          battleId,
          unitId: selectedUnitId,
          config
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setTargetScores(data.targets);
        addLog(`📊 ${data.targets.length} cibles analysées`);
        addLog(`🎯 Meilleure cible: ${data.best_target?.unitId} (score: ${data.best_target?.totalScore.toFixed(1)})`);
      } else {
        addLog(`❌ ${data.error}`);
      }
    } catch (error) {
      addLog(`❌ Erreur: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  const testNextUnit = async () => {
    setLoading(true);
    addLog('🎮 Exécution de la prochaine unité IA...');

    try {
      const response = await fetch('/api/v2/ai/test-next-unit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          battleId,
          config
        })
      });

      const data = await response.json();
      
      if (data.success) {
        const unit = data.unit;
        const decision = data.decision;
        
        addLog(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
        addLog(`🎯 Unité: ${unit.unitId} (${unit.unitType})`);
        addLog(`   Position: [${unit.position.join(', ')}]`);
        addLog(`   HP: ${unit.current_hp}/${unit.max_hp}`);
        addLog(``);
        addLog(`📊 ANALYSE DES CIBLES (${decision.targets.length} cibles):`);
        
        decision.targets.forEach((target: any, idx: number) => {
          addLog(`   ${idx + 1}. ${target.unitId} - Score: ${target.totalScore.toFixed(1)}`);
          addLog(`      🦸 Héro: +${target.breakdown.hero_bonus} | ❤️ HP: +${target.breakdown.hp_bonus} | 🏹 Dist: +${target.breakdown.ranged_bonus}`);
          addLog(`      📍 Proximité: ${target.breakdown.distance_penalty.toFixed(1)} | ⚔️ Menace: +${target.breakdown.threat_bonus}`);
        });
        
        addLog(``);
        addLog(`✅ DÉCISION: Attaque ${decision.best_target.unitId}`);
        addLog(`   Score final: ${decision.best_target.totalScore.toFixed(1)}`);
        addLog(`   Dégâts estimés: ${decision.damage || 'N/A'}`);
        addLog(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
        
      } else {
        addLog(`⚠️ ${data.message || data.error}`);
      }
    } catch (error) {
      addLog(`❌ Erreur: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  const addLog = (message: string) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${message}`]);
  };

  const updateWeight = (key: keyof AIConfig['decision_weights'], value: number) => {
    if (!config) return;
    setConfig({
      ...config,
      decision_weights: {
        ...config.decision_weights,
        [key]: value
      }
    });
  };

  // Fonctions de drag
  const handleMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).classList.contains('popup-header')) {
      setIsDragging(true);
      setDragOffset({
        x: e.clientX - position.x,
        y: e.clientY - position.y
      });
    }
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragOffset.x,
        y: e.clientY - dragOffset.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, dragOffset]);

  if (!config) {
    return (
      <div className="ai-debug-popup" style={{ left: `${position.x}px`, top: `${position.y}px`, transform: 'translate(-50%, -50%)' }}>
        <div className="popup-header" style={{ cursor: 'move' }}>
          <h2>🤖 IA Debug Panel</h2>
          <button onClick={onClose} className="close-button">×</button>
        </div>
        <div className="loading">Chargement...</div>
      </div>
    );
  }

  return (
    <div 
      className={`ai-debug-popup ${isMinimized ? 'minimized' : ''}`}
      style={{ 
        left: `${position.x}px`, 
        top: `${position.y}px`,
        transform: 'translate(-50%, -50%)'
      }}
      onMouseDown={handleMouseDown}
    >
      <div className="popup-header" style={{ cursor: 'move' }}>
        <h2>🤖 IA Debug Panel</h2>
        <div className="header-buttons">
          <button 
            onClick={() => setIsMinimized(!isMinimized)} 
            className="minimize-button"
            title={isMinimized ? "Agrandir" : "Réduire"}
          >
            {isMinimized ? '🔼' : '🔽'}
          </button>
          <button onClick={onClose} className="close-button">×</button>
        </div>
      </div>

      {!isMinimized && (
      <div className="popup-content">
        {/* Section 0: Auto-IA Toggle */}
        <div className="auto-ai-section">
          <h3>🤖 Contrôle Auto-IA</h3>
          <div className="auto-toggle-container">
            <button 
              onClick={toggleAutoAI}
              disabled={loadingAutoStatus}
              className={`auto-toggle-button ${aiAutoEnabled ? 'enabled' : 'disabled'}`}
            >
              {loadingAutoStatus ? '⏳ Chargement...' : (
                <>
                  <span className="toggle-icon">{aiAutoEnabled ? '✅' : '❌'}</span>
                  <span className="toggle-text">Auto-IA: {aiAutoEnabled ? 'ACTIVÉE' : 'DÉSACTIVÉE'}</span>
                </>
              )}
            </button>
            <p className="toggle-hint">
              {aiAutoEnabled 
                ? '💡 L\'IA jouera automatiquement si le joueur ne fait rien pendant 20s' 
                : '💡 L\'IA ne jouera JAMAIS automatiquement (mode manuel uniquement)'}
            </p>
          </div>
          
          {/* Toggle Timer (Pause/Redémarrer) */}
          <div className="auto-toggle-container" style={{ marginTop: '10px' }}>
            <button 
              onClick={toggleTimer}
              disabled={loadingTimer || timerPaused === null}
              className={`auto-toggle-button ${timerPaused ? 'disabled' : 'enabled'}`}
            >
              {loadingTimer ? '⏳ Chargement...' : timerPaused === null ? '❓ Indisponible' : (
                <>
                  <span className="toggle-icon">{timerPaused ? '▶️' : '⏸️'}</span>
                  <span className="toggle-text">{timerPaused ? 'REDÉMARRER Timer' : 'PAUSE Timer'}</span>
                </>
              )}
            </button>
            <p className="toggle-hint">
              {timerPaused 
                ? '▶️ Cliquez pour redémarrer le timer automatique' 
                : '⏸️ Cliquez pour mettre le timer en pause'}
            </p>
          </div>

          {/* Toggle Player Turn Lock */}
          <div className="auto-toggle-container" style={{ marginTop: '10px' }}>
            <button 
              onClick={() => {
                toggleTurnLock();
                addLog(`🔒 Verrouillage tours ${!turnLockEnabled ? 'ACTIVÉ' : 'DÉSACTIVÉ'}`);
              }}
              className={`auto-toggle-button ${turnLockEnabled ? 'enabled' : 'disabled'}`}
            >
              <span className="toggle-icon">{turnLockEnabled ? '🔒' : '🔓'}</span>
              <span className="toggle-text">{turnLockEnabled ? 'VERROUILLAGE ON' : 'VERROUILLAGE OFF'}</span>
            </button>
            <p className="toggle-hint">
              {turnLockEnabled 
                ? '🔒 Seul le joueur actuel peut agir (mode normal)' 
                : '🔓 Tous les joueurs peuvent agir (mode test)'}
            </p>
          </div>

          {/* Boutons de Reddition (TEST UNIQUEMENT) */}
          <div className="auto-toggle-container" style={{ marginTop: '15px', borderTop: '1px solid #444', paddingTop: '15px' }}>
            <h4 style={{ color: '#ff6b6b', marginBottom: '10px' }}>🧪 Tests de Reddition</h4>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button 
                className="auto-toggle-button"
                style={{ backgroundColor: '#e74c3c', flex: 1 }}
                onClick={async () => {
                  try {
                    if (window.confirm('⚠️ [TEST] Faire se rendre l\'ATTAQUANT ?')) {
                      const response = await fetch(`/api/v2/battle/surrender/${battleId}/auto-attacker`, {
                        method: 'POST'
                      });
                      const data = await response.json();
                      if (data.success) {
                        alert('✅ Attaquant s\'est rendu !');
                        addLog('🏳️ TEST: Attaquant s\'est rendu');
                      } else {
                        alert(`❌ Erreur: ${data.error}`);
                      }
                    }
                  } catch (error) {
                    alert('❌ Erreur lors de la reddition');
                  }
                }}
              >
                🏳️ Attaquant se rend
              </button>
              
              <button 
                className="auto-toggle-button"
                style={{ backgroundColor: '#d63384', flex: 1 }}
                onClick={async () => {
                  try {
                    if (window.confirm('⚠️ [TEST] Faire se rendre le DÉFENSEUR ?')) {
                      const response = await fetch(`/api/v2/battle/surrender/${battleId}/auto`, {
                        method: 'POST'
                      });
                      const data = await response.json();
                      if (data.success) {
                        alert('✅ Défenseur s\'est rendu !');
                        addLog('🏳️ TEST: Défenseur s\'est rendu');
                      } else {
                        alert(`❌ Erreur: ${data.error}`);
                      }
                    }
                  } catch (error) {
                    alert('❌ Erreur lors de la reddition');
                  }
                }}
              >
                🏳️ Défenseur se rend
              </button>
            </div>
            <p className="toggle-hint" style={{ color: '#ff6b6b' }}>
              ⚠️ MODE TEST : Force la reddition de n'importe quelle équipe
            </p>
          </div>
        </div>

        {/* Section 1: Paramètres IA */}
        <div className="config-section">
          <h3>⚙️ Paramètres de Décision</h3>
          
          <div className="weight-slider">
            <label>
              🦸 Priorité Héros: <strong>{config.decision_weights.priority_hero}</strong>
            </label>
            <input
              type="range"
              min="0"
              max="150"
              value={config.decision_weights.priority_hero}
              onChange={(e) => updateWeight('priority_hero', Number(e.target.value))}
            />
          </div>

          <div className="weight-slider">
            <label>
              ❤️ Priorité Unités Blessées: <strong>{config.decision_weights.priority_low_hp}</strong>
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={config.decision_weights.priority_low_hp}
              onChange={(e) => updateWeight('priority_low_hp', Number(e.target.value))}
            />
          </div>

          <div className="weight-slider">
            <label>
              🏹 Priorité Unités à Distance: <strong>{config.decision_weights.priority_ranged}</strong>
            </label>
            <input
              type="range"
              min="0"
              max="80"
              value={config.decision_weights.priority_ranged}
              onChange={(e) => updateWeight('priority_ranged', Number(e.target.value))}
            />
          </div>

          <div className="weight-slider">
            <label>
              📍 Priorité Proximité: <strong>{config.decision_weights.priority_closest}</strong>
            </label>
            <input
              type="range"
              min="0"
              max="50"
              value={config.decision_weights.priority_closest}
              onChange={(e) => updateWeight('priority_closest', Number(e.target.value))}
            />
          </div>

          <button onClick={saveAIConfig} className="save-button">
            💾 Sauvegarder Config
          </button>
        </div>

        {/* Section 2: Test Unité */}
        <div className="test-section">
          <h3>🧪 Test Comportement</h3>
          
          <div className="test-controls">
            <button 
              onClick={testNextUnit} 
              disabled={loading}
              className="next-unit-button"
            >
              {loading ? '⏳ Calcul...' : '▶️ Jouer Prochaine Unité'}
            </button>
            <p className="test-hint">Exécute l'IA pour la prochaine unité avec logs détaillés</p>
          </div>

          <div className="separator">ou</div>

          <select 
            value={selectedUnitId} 
            onChange={(e) => setSelectedUnitId(e.target.value)}
            className="unit-selector"
          >
            <option value="">-- Sélectionner une unité --</option>
            {deployedUnits.map((unit, idx) => (
              <option key={`${unit.unitId}_${idx}`} value={unit.unitId}>
                {unit.unitId} - {unit.unitType}
              </option>
            ))}
          </select>

          <button 
            onClick={testUnitBehavior} 
            disabled={loading || !selectedUnitId}
            className="test-button"
          >
            {loading ? '⏳ Calcul...' : '🎯 Analyser Cibles'}
          </button>

          {/* Résultats des scores */}
          {targetScores.length > 0 && (
            <div className="scores-list">
              <h4>📊 Scores des Cibles</h4>
              {targetScores.map((target, idx) => (
                <div key={idx} className="target-score">
                  <div className="score-header">
                    <strong>{target.unitId}</strong>
                    <span className="total-score">{target.totalScore.toFixed(1)} pts</span>
                  </div>
                  <div className="score-breakdown">
                    {target.breakdown.hero_bonus > 0 && (
                      <span className="bonus-tag hero">🦸 +{target.breakdown.hero_bonus}</span>
                    )}
                    {target.breakdown.hp_bonus > 0 && (
                      <span className="bonus-tag hp">❤️ +{target.breakdown.hp_bonus}</span>
                    )}
                    {target.breakdown.ranged_bonus > 0 && (
                      <span className="bonus-tag ranged">🏹 +{target.breakdown.ranged_bonus}</span>
                    )}
                    {target.breakdown.distance_penalty < 0 && (
                      <span className="bonus-tag distance">📍 {target.breakdown.distance_penalty.toFixed(1)}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Section 3: Console de Logs */}
        <div className="logs-section">
          <h3>📋 Console</h3>
          <div className="logs-container">
            {logs.map((log, idx) => (
              <div key={idx} className="log-entry">{log}</div>
            ))}
          </div>
          <button onClick={() => setLogs([])} className="clear-logs">
            🗑️ Effacer
          </button>
        </div>
      </div>
      )}
    </div>
  );
};

export default AIDebugPopup;
