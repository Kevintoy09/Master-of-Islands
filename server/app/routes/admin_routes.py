"""
Interface d'Administration - Contrôle du Temps Global + Ticks Manuels
====================================================================

Popup/Fenêtre indépendante pour piloter les paramètres temporels du jeu :
- Vitesse globale du jeu
- Mode de production  
- Monitoring en temps réel
- Statistiques de performance
- NOUVEAU: Ticks manuels simplifiés
"""

from flask import Blueprint, jsonify, request, render_template_string, render_template
from ..services.tick_service import TickService
import time
import os
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Template HTML pour l'interface d'administration
ADMIN_INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎮 Administration - Contrôle Temporel</title>
    <style>
        :root {
            --roman-red: #8B0000;
            --roman-gold: #DAA520;
            --roman-beige: #F5E6D3;
            --roman-brown: #4A3933;
            --roman-dark: #2F1B14;
            --roman-green: #2d5016;
            --bronze: #CD7F32;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Cinzel', 'Trajan Pro', 'Times New Roman', serif;
            background: linear-gradient(135deg, var(--roman-dark) 0%, var(--roman-brown) 100%);
            background-image: 
                radial-gradient(circle at 20% 50%, rgba(218, 165, 32, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(139, 0, 0, 0.1) 0%, transparent 50%),
                linear-gradient(135deg, var(--roman-dark) 0%, var(--roman-brown) 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .admin-container {
            max-width: 800px;
            margin: 0 auto;
            background: var(--roman-beige);
            border-radius: 6px;
            border: 3px solid var(--roman-gold);
            box-shadow: 
                0 0 20px rgba(218, 165, 32, 0.3),
                inset 0 0 15px rgba(139, 0, 0, 0.05),
                0 15px 40px rgba(0, 0, 0, 0.4);
            overflow: hidden;
        }
        
        .admin-header {
            background: linear-gradient(135deg, var(--bronze), var(--roman-gold));
            color: var(--roman-dark);
            padding: 15px 20px;
            text-align: center;
            border-bottom: 3px solid var(--roman-gold);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        }
        
        .admin-header h1 {
            font-size: 1.6em;
            margin-bottom: 5px;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
            letter-spacing: 1px;
        }
        
        .admin-header p {
            font-size: 0.9em;
            opacity: 0.85;
            font-style: italic;
        }
        
        .admin-content {
            padding: 15px;
            background: var(--roman-beige);
        }
        
        .control-section {
            background: linear-gradient(to bottom, #FFF8E7, var(--roman-beige));
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 15px;
            border: 2px solid var(--bronze);
            box-shadow: 
                0 2px 4px rgba(0, 0, 0, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.5);
        }
        
        .section-title {
            font-size: 1.1em;
            font-weight: bold;
            color: var(--bronze);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            padding-bottom: 8px;
            border-bottom: 2px solid var(--roman-gold);
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
        }
        
        .control-row {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 10px;
        }
        
        .control-label {
            font-weight: bold;
            color: var(--roman-brown);
            min-width: 200px;
            flex: 0 0 auto;
            font-size: 0.95em;
        }
        
        .status-badge {
            padding: 4px 12px;
            background: var(--roman-beige);
            border-radius: 4px;
            font-size: 0.85em;
            border: 1px solid var(--bronze);
            font-weight: 500;
        }
        
        .toggle-button {
            background: linear-gradient(to bottom, #4CAF50, #45a049);
            color: white;
            border: 2px solid #2d6b2f;
            padding: 6px 16px;
            border-radius: 4px;
            font-size: 0.9em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            font-family: inherit;
        }
        
        .toggle-button:hover {
            background: linear-gradient(to bottom, #5CBF60, #4CAF50);
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.25);
        }
        
        .toggle-button:active {
            transform: translateY(0);
        }
        
        .toggle-button.off {
            background: linear-gradient(to bottom, #888, #666);
            border-color: #444;
        }
        
        .toggle-button.off:hover {
            background: linear-gradient(to bottom, #999, #777);
        }
        
        .frequency-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 8px;
        }
        
        .freq-button {
            background: linear-gradient(to bottom, var(--roman-gold), #B8860B);
            color: var(--roman-dark);
            border: 2px solid var(--bronze);
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            font-family: inherit;
        }
        
        .freq-button:hover {
            background: linear-gradient(to bottom, #FFD700, var(--roman-gold));
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.25);
        }
        
        .freq-button:active {
            transform: translateY(0);
        }
        
        .freq-button.active {
            background: linear-gradient(to bottom, var(--roman-green), #1a3a0d);
            color: white;
            border-color: #0d2006;
            box-shadow: 0 2px 8px rgba(45, 80, 22, 0.4);
        }
        
        .close-button {
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0, 0, 0, 0.6);
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 0.9em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s ease;
            z-index: 10;
        }
        
        .close-button:hover {
            background: rgba(0, 0, 0, 0.8);
        }
    </style>
</head>
<body>
    <div class="admin-container">
        <div class="admin-header" style="position: relative;">
            <button class="close-button" onclick="window.close()">✕ Fermer</button>
            <h1>⚙️ MASTER OF ISLANDS - ADMIN</h1>
            <p>Panneau de Contrôle</p>
        </div>
        
        <div class="admin-content">
            <!-- Configuration des Ticks -->
            <div class="control-section">
                <div class="section-title">
                    ⚡ Configuration des Ticks
                </div>
                
                <!-- Visibilité HeaderBar -->
                <div class="control-row">
                    <span class="control-label">🎮 Boutons tick (HeaderBar)</span>
                    <button id="toggleTickBtn" class="toggle-button" onclick="toggleTickControls()">...</button>
                </div>

                <!-- Auto-Tick -->
                <div class="control-row">
                    <span class="control-label">⚡ Auto-Tick</span>
                    <button id="autoTickToggle" class="toggle-button" onclick="toggleAutoTick()">...</button>
                    <span class="status-badge" id="currentFrequency">-</span>
                </div>

                <!-- Fréquences -->
                <div style="margin-top: 12px;">
                    <div style="font-size: 0.9em; font-weight: bold; color: #4A3933; margin-bottom: 6px;">
                        Fréquence :
                    </div>
                    <div class="frequency-grid" id="tickFrequencyButtons">
                        <button class="freq-button" onclick="setTickFrequency(1)">1s</button>
                        <button class="freq-button" onclick="setTickFrequency(5)">5s</button>
                        <button class="freq-button" onclick="setTickFrequency(10)">10s ⭐</button>
                        <button class="freq-button" onclick="setTickFrequency(30)">30s</button>
                        <button class="freq-button" onclick="setTickFrequency(60)">1m</button>
                    </div>
                </div>

                <!-- Note -->
                <div style="background: #FFF3CD; border-left: 4px solid #CD7F32; padding: 8px 12px; margin-top: 12px; font-size: 0.85em; color: #4A3933;">
                    <strong>⚠️</strong> Les ticks affectent la production, la population et la consommation de toutes les villes.
                </div>
            </div>

            <!-- Contrôle IA -->
            <div class="control-section">
                <div class="section-title">
                    🤖 Gestion des Joueurs IA
                </div>
                
                <div style="margin-top: 12px;">
                    <button class="freq-button" onclick="openAIAdmin()" style="width: 100%; font-size: 1em; padding: 12px; background: linear-gradient(to bottom, #6a5acd, #483d8b);">
                        🎮 Ouvrir Interface IA
                    </button>
                </div>

                <!-- Note -->
                <div style="background: #FFF3CD; border-left: 4px solid #CD7F32; padding: 8px 12px; margin-top: 12px; font-size: 0.85em; color: #4A3933;">
                    <strong>ℹ️</strong> Créer, supprimer et contrôler les joueurs IA
                </div>
            </div>

            <!-- Vitesse de Construction -->
            <div class="control-section">
                <div class="section-title">
                    ⚙️ Vitesse de Construction
                </div>
                
                <div class="control-row">
                    <span class="control-label">⏱️ Multiplicateur de temps</span>
                    <span class="status-badge" id="currentMultiplier">×1.0</span>
                </div>

                <!-- Slider de multiplicateur -->
                <div style="margin-top: 12px;">
                    <div style="display: flex; gap: 12px; align-items: center;">
                        <input type="range" id="timeMultiplierSlider" min="0.01" max="10" step="0.01" value="1.0" 
                               style="flex: 1; height: 8px; border-radius: 4px; background: linear-gradient(to right, #2d5016, #DAA520, #8B0000); cursor: pointer;" 
                               oninput="updateMultiplierDisplay()" onchange="saveMultiplier()">
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.75em; color: #4A3933; margin-top: 4px;">
                        <span>100× plus rapide</span>
                        <span>Normal</span>
                        <span>10× plus lent</span>
                    </div>
                </div>

                <!-- Boutons rapides -->
                <div style="margin-top: 12px;">
                    <div style="font-size: 0.9em; font-weight: bold; color: #4A3933; margin-bottom: 6px;">
                        Presets rapides :
                    </div>
                    <div class="frequency-grid" style="grid-template-columns: repeat(7, 1fr);">
                        <button class="freq-button" onclick="setMultiplier(0.01)">×0.01</button>
                        <button class="freq-button" onclick="setMultiplier(0.1)">×0.1</button>
                        <button class="freq-button" onclick="setMultiplier(0.5)">×0.5</button>
                        <button class="freq-button" onclick="setMultiplier(1.0)">×1 ⭐</button>
                        <button class="freq-button" onclick="setMultiplier(2.0)">×2</button>
                        <button class="freq-button" onclick="setMultiplier(5.0)">×5</button>
                        <button class="freq-button" onclick="setMultiplier(10.0)">×10</button>
                    </div>
                </div>

                <!-- Note -->
                <div style="background: #FFF3CD; border-left: 4px solid #CD7F32; padding: 8px 12px; margin-top: 12px; font-size: 0.85em; color: #4A3933;">  
                    <strong>ℹ️</strong> Facteur appliqué aux temps de construction. <strong>×0.5 = 2× plus rapide</strong>, <strong>×2.0 = 2× plus lent</strong>.
                </div>
            </div>

            <!-- Rafraîchissement des données -->
            <div class="control-section">
                <div class="section-title">
                    🔄 Rafraîchissement des Données
                </div>
                
                <div class="control-row">
                    <span class="control-label">📊 Intervalle de rafraîchissement</span>
                    <span class="status-badge" id="currentRefreshInterval">-</span>
                </div>

                <!-- Intervalles disponibles -->
                <div style="margin-top: 12px;">
                    <div style="font-size: 0.9em; font-weight: bold; color: #4A3933; margin-bottom: 6px;">
                        Choisir l'intervalle :
                    </div>
                    <div class="frequency-grid" id="refreshIntervalButtons">
                        <button class="freq-button" onclick="setRefreshInterval(1)">1s</button>
                        <button class="freq-button" onclick="setRefreshInterval(3)">3s</button>
                        <button class="freq-button" onclick="setRefreshInterval(5)">5s</button>
                        <button class="freq-button" onclick="setRefreshInterval(10)">10s</button>
                        <button class="freq-button" onclick="setRefreshInterval(30)">30s</button>
                    </div>
                </div>

                <!-- Note -->
                <div style="background: #FFF3CD; border-left: 4px solid #CD7F32; padding: 8px 12px; margin-top: 12px; font-size: 0.85em; color: #4A3933;">
                    <strong>ℹ️</strong> Contrôle le rafraîchissement de l'or, des diamants, des points de recherche et de la population.
                </div>
            </div>

            <!-- Génération des Quêtes -->
            <div class="control-section">
                <div class="section-title">
                    🎯 Système de Quêtes
                </div>
                
                <!-- Quêtes Quotidiennes -->
                <div style="margin-bottom: 16px;">
                    <div style="font-size: 0.9em; color: #4A3933; margin-bottom: 8px;">
                        <strong>📅 Quêtes Quotidiennes :</strong><br>
                        Génère 5 quêtes aléatoires pour chaque joueur. <strong>À exécuter chaque jour.</strong>
                    </div>
                    
                    <button class="freq-button" onclick="generateDailyQuests()" 
                            style="width: 100%; font-size: 1em; padding: 12px; background: linear-gradient(to bottom, var(--roman-gold), var(--bronze));">
                        🌅 Générer Quêtes Quotidiennes
                    </button>
                    
                    <div id="dailyQuestResult" style="margin-top: 12px; padding: 10px; border-radius: 4px; display: none;"></div>
                </div>

                <!-- Quêtes Hebdomadaires -->
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 0.9em; color: #4A3933; margin-bottom: 8px;">
                        <strong>📆 Quêtes Hebdomadaires :</strong><br>
                        Met à jour les 3 quêtes actives (progression chronologique). <strong>À exécuter chaque semaine.</strong>
                    </div>
                    
                    <button class="freq-button" onclick="generateWeeklyQuests()" 
                            style="width: 100%; font-size: 1em; padding: 12px; background: linear-gradient(to bottom, #6a5acd, #483d8b);">
                        📅 Générer Quêtes Hebdomadaires
                    </button>
                    
                    <div id="weeklyQuestResult" style="margin-top: 12px; padding: 10px; border-radius: 4px; display: none;"></div>
                </div>

                <!-- Note -->
                <div style="background: #FFF3CD; border-left: 4px solid #CD7F32; padding: 8px 12px; margin-top: 12px; font-size: 0.85em; color: #4A3933;">
                    <strong>ℹ️</strong> Les quêtes quotidiennes sont aléatoires. Les quêtes hebdomadaires suivent une progression chronologique (15 quêtes totales).
                </div>
            </div>

            <!-- Gestion des Données JSON -->
            <div class="control-section">
                <div class="section-title">
                    📁 Gestion des Données JSON
                </div>
                
                <!-- Sélecteur de fichier -->
                <div style="margin-bottom: 16px;">
                    <label style="display: block; margin-bottom: 8px; font-weight: bold; color: var(--roman-dark);">
                        Fichier à éditer :
                    </label>
                    <select id="jsonFileSelector" onchange="loadJsonFile()" 
                            style="width: 100%; padding: 10px; border: 2px solid var(--bronze); border-radius: 4px; font-size: 1em; background: white; cursor: pointer;">
                        <option value="">-- Sélectionner un fichier --</option>
                        <option value="players.json">👥 players.json</option>
                        <option value="savegame.json">💾 savegame.json</option>
                        <option value="player_quests.json">🎯 player_quests.json</option>
                        <option value="player_heroes.json">🦸 player_heroes.json</option>
                        <option value="player_profiles.json">📋 player_profiles.json</option>
                        <option value="player_unit_improvements.json">⚔️ player_unit_improvements.json</option>
                        <option value="battlefields_v2.json">🗺️ battlefields_v2.json</option>
                        <option value="battlesv2.json">⚔️ battlesv2.json</option>
                        <option value="battle_reports.json">📜 battle_reports.json</option>
                        <option value="battle_replays.json">🎬 battle_replays.json</option>
                        <option value="battle_notifications.json">🔔 battle_notifications.json</option>
                        <option value="transports.json">🚢 transports.json</option>
                        <option value="transport_history.json">📊 transport_history.json</option>
                        <option value="messages.json">✉️ messages.json</option>
                        <option value="notifications.json">📬 notifications.json</option>
                        <option value="market.json">🏛️ market.json</option>
                        <option value="resource_sites.json">🏔️ resource_sites.json</option>
                        <option value="ai_auto_cycles.json">🤖 ai_auto_cycles.json</option>
                        <option value="ai_console_logs.json">📝 ai_console_logs.json</option>
                        <option value="ai_strategies_state.json">🎯 ai_strategies_state.json</option>
                    </select>
                </div>

                <!-- Zone d'édition -->
                <div style="margin-bottom: 16px;">
                    <label style="display: block; margin-bottom: 8px; font-weight: bold; color: var(--roman-dark);">
                        Contenu JSON :
                    </label>
                    <textarea id="jsonEditor" 
                              style="width: 100%; height: 400px; padding: 12px; border: 2px solid var(--bronze); border-radius: 4px; font-family: 'Courier New', monospace; font-size: 0.9em; resize: vertical;"
                              placeholder="Sélectionnez un fichier pour afficher son contenu..."></textarea>
                </div>

                <!-- Boutons d'action -->
                <div style="display: flex; gap: 12px; margin-bottom: 16px;">
                    <button class="freq-button" onclick="saveJsonFile()" 
                            style="flex: 1; font-size: 1em; padding: 12px; background: linear-gradient(to bottom, var(--roman-green), #1a3a0d);">
                        💾 Sauvegarder
                    </button>
                    <button class="freq-button" onclick="formatJson()" 
                            style="flex: 1; font-size: 1em; padding: 12px; background: linear-gradient(to bottom, #6a5acd, #483d8b);">
                        ✨ Formatter JSON
                    </button>
                    <button class="freq-button" onclick="loadJsonFile()" 
                            style="flex: 1; font-size: 1em; padding: 12px; background: linear-gradient(to bottom, var(--bronze), #8B4513);">
                        🔄 Recharger
                    </button>
                    <button class="freq-button" onclick="resetJsonFile()" 
                            style="flex: 1; font-size: 1em; padding: 12px; background: linear-gradient(to bottom, var(--roman-red), #5a0000);">
                        🗑️ Réinitialiser
                    </button>
                </div>

                <!-- Messages de résultat -->
                <div id="jsonEditorResult" style="padding: 10px; border-radius: 4px; display: none;"></div>

                <!-- Note de sécurité -->
                <div style="background: #f8d7da; border-left: 4px solid #8B0000; padding: 8px 12px; margin-top: 12px; font-size: 0.85em; color: #8B0000;">
                    <strong>⚠️ ATTENTION :</strong> Les modifications sont directes et immédiates. Assurez-vous que le JSON est valide avant de sauvegarder.
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentAutoTickEnabled = false;
        let currentFrequency = 1;
        let tickControlsVisible = true;
        let currentRefreshInterval = 5;
        let currentMultiplier = 1.0;

        // Charger l'état initial au chargement de la page
        window.addEventListener('load', () => {
            loadTickControlsStatus();
            loadAutoTickStatus();
            loadRefreshInterval();
            loadMultiplier();
            // Rafraîchir toutes les 2 secondes
            setInterval(() => {
                loadAutoTickStatus();
            }, 2000);
        });

        // Charger le statut d'affichage des contrôles de tick
        async function loadTickControlsStatus() {
            try {
                const response = await fetch('/admin/api/tick-controls-status');
                const data = await response.json();
                if (data.success) {
                    tickControlsVisible = data.visible;
                    updateTickControlsButton();
                }
            } catch (error) {
                // En cas d'erreur, mettre à jour quand même avec la valeur par défaut
                updateTickControlsButton();
            }
        }

        // Mettre à jour l'affichage du bouton de contrôle des ticks
        function updateTickControlsButton() {
            const btn = document.getElementById('toggleTickBtn');
            if (!btn) return;
            
            if (tickControlsVisible) {
                btn.textContent = 'ON';
                btn.classList.remove('off');
            } else {
                btn.textContent = 'OFF';
                btn.classList.add('off');
            }
        }

        // Toggle de la visibilité des contrôles de tick
        async function toggleTickControls() {
            try {
                const response = await fetch('/admin/api/toggle-tick-controls', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ visible: !tickControlsVisible })
                });
                const data = await response.json();
                
                if (data.success) {
                    tickControlsVisible = data.visible;
                    updateTickControlsButton();
                    // Pas d'alert, l'UI se met à jour
                } else {
                    alert('Erreur: ' + data.error);
                }
            } catch (error) {
                alert('❌ Erreur de communication avec le serveur');
                console.error(error);
            }
        }

        // Charger le statut de l'auto-tick
        async function loadAutoTickStatus() {
            try {
                const response = await fetch('/admin/api/auto-tick/status');
                const data = await response.json();
                
                if (data.success) {
                    currentAutoTickEnabled = data.settings.running || false;
                    currentFrequency = data.settings.interval_seconds || 1;
                    updateAutoTickButton();
                    updateFrequencyDisplay();
                }
            } catch (error) {
                // En cas d'erreur, mettre à jour quand même avec les valeurs par défaut
                updateAutoTickButton();
                updateFrequencyDisplay();
            }
        }

        // Mettre à jour l'affichage du bouton auto-tick
        function updateAutoTickButton() {
            const btn = document.getElementById('autoTickToggle');
            if (!btn) return;
            
            if (currentAutoTickEnabled) {
                btn.textContent = 'ON';
                btn.classList.remove('off');
            } else {
                btn.textContent = 'OFF';
                btn.classList.add('off');
            }
        }

        // Mettre à jour l'affichage de la fréquence
        function updateFrequencyDisplay() {
            const display = document.getElementById('currentFrequency');
            const buttons = document.querySelectorAll('#tickFrequencyButtons .freq-button');
            
            // Formater l'affichage
            let freqText = '';
            if (currentFrequency < 60) {
                freqText = currentFrequency + 's';
            } else {
                const minutes = currentFrequency / 60;
                freqText = minutes + 'min';
            }
            display.textContent = freqText;
            
            // Mettre en surbrillance le bouton actif
            buttons.forEach(btn => {
                const freq = parseInt(btn.getAttribute('onclick').match(/\\d+/)[0]);
                if (freq === currentFrequency) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
        }

        // Toggle de l'auto-tick
        async function toggleAutoTick() {
            try {
                const newState = !currentAutoTickEnabled;
                const response = await fetch('/admin/api/auto-tick', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        enabled: newState,
                        interval_seconds: currentFrequency
                    })
                });
                const data = await response.json();
                
                if (data.success) {
                    currentAutoTickEnabled = newState;
                    updateAutoTickButton();
                    // Pas d'alert, l'UI se met à jour
                } else {
                    alert('Erreur: ' + data.error);
                }
            } catch (error) {
                alert('❌ Erreur de communication avec le serveur');
                console.error(error);
            }
        }

        // Définir la fréquence des ticks
        async function setTickFrequency(seconds) {
            try {
                currentFrequency = seconds;
                updateFrequencyDisplay();
                
                // Toujours sauvegarder la fréquence, même si l'auto-tick n'est pas activé
                const response = await fetch('/admin/api/auto-tick', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        enabled: currentAutoTickEnabled,
                        interval_seconds: seconds
                    })
                });
                const data = await response.json();
                
                if (!data.success) {
                    alert('Erreur: ' + data.error);
                }
            } catch (error) {
                alert('Erreur de communication avec le serveur');
            }
        }

        // Charger l'intervalle de rafraîchissement
        async function loadRefreshInterval() {
            try {
                const response = await fetch('/admin/api/refresh-interval/status');
                const data = await response.json();
                
                if (data.success) {
                    currentRefreshInterval = data.interval_seconds || 5;
                    updateRefreshIntervalDisplay();
                }
            } catch (error) {
                updateRefreshIntervalDisplay();
            }
        }

        // Mettre à jour l'affichage de l'intervalle
        function updateRefreshIntervalDisplay() {
            const display = document.getElementById('currentRefreshInterval');
            const buttons = document.querySelectorAll('#refreshIntervalButtons .freq-button');
            
            // Formater l'affichage
            let intervalText = '';
            if (currentRefreshInterval < 60) {
                intervalText = currentRefreshInterval + 's';
            } else {
                const minutes = currentRefreshInterval / 60;
                intervalText = minutes + 'min';
            }
            display.textContent = intervalText;
            
            // Mettre en surbrillance le bouton actif
            buttons.forEach(btn => {
                const interval = parseInt(btn.getAttribute('onclick').match(/\\d+/)[0]);
                if (interval === currentRefreshInterval) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
        }

        // Définir l'intervalle de rafraîchissement
        async function setRefreshInterval(seconds) {
            try {
                const response = await fetch('/admin/api/refresh-interval', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ interval_seconds: seconds })
                });
                
                if (!response.ok) {
                    alert('Erreur HTTP: ' + response.status);
                    return;
                }
                
                const data = await response.json();
                
                if (data.success) {
                    currentRefreshInterval = seconds;
                    updateRefreshIntervalDisplay();
                    
                    // Info: le changement prendra effet automatiquement
                    alert('Intervalle modifie a ' + seconds + 's ! Le changement prendra effet automatiquement dans les 2 prochaines secondes.');
                } else {
                    alert('Erreur: ' + data.error);
                }
            } catch (error) {
                alert('Erreur de communication avec le serveur: ' + error.message);
            }
        }

        // Charger le multiplicateur de temps de construction
        async function loadMultiplier() {
            try {
                const response = await fetch('/admin/api/construction-multiplier/status');
                const data = await response.json();
                
                if (data.success) {
                    currentMultiplier = data.multiplier || 1.0;
                    document.getElementById('timeMultiplierSlider').value = currentMultiplier;
                    updateMultiplierDisplay();
                }
            } catch (error) {
                console.error('❌ Erreur chargement multiplicateur:', error);
            }
        }

        // Mettre à jour l'affichage du multiplicateur
        function updateMultiplierDisplay() {
            const slider = document.getElementById('timeMultiplierSlider');
            const display = document.getElementById('currentMultiplier');
            const value = parseFloat(slider.value);
            
            // Afficher 2 décimales si < 0.1, sinon 1 décimale
            const formatted = value < 0.1 ? value.toFixed(2) : value.toFixed(1);
            display.textContent = '×' + formatted;
            
            // Changer la couleur selon la valeur
            if (value < 0.5) {
                display.style.background = '#d4edda';
                display.style.color = '#2d5016';
                display.style.fontWeight = 'bold';
            } else if (value > 2) {
                display.style.background = '#f8d7da';
                display.style.color = '#8B0000';
                display.style.fontWeight = 'bold';
            } else {
                display.style.background = '#F5E6D3';
                display.style.color = '#4A3933';
                display.style.fontWeight = 'normal';
            }
        }

        // Sauvegarder le multiplicateur
        async function saveMultiplier() {
            const slider = document.getElementById('timeMultiplierSlider');
            const value = parseFloat(slider.value);
            
            try {
                const response = await fetch('/admin/api/construction-multiplier', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ multiplier: value })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentMultiplier = value;
                    console.log('✅ Multiplicateur sauvegardé dans admin_settings.json');
                } else {
                    console.error('❌ Erreur:', data.error);
                    alert('Erreur: ' + data.error);
                }
            } catch (error) {
                console.error('❌ Erreur communication:', error);
                alert('Erreur de communication: ' + error.message);
            }
        }

        // Définir un preset de multiplicateur
        function setMultiplier(value) {
            document.getElementById('timeMultiplierSlider').value = value;
            updateMultiplierDisplay();
            saveMultiplier();
        }

        // Ouvrir l'interface IA
        function openAIAdmin() {
            const width = 1200;
            const height = 800;
            const left = (screen.width - width) / 2;
            const top = (screen.height - height) / 2;
            
            window.open(
                '/admin/ai',
                'AIAdmin',
                `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
            );
        }

        // Générer des quêtes quotidiennes
        async function generateDailyQuests() {
            const resultDiv = document.getElementById('dailyQuestResult');
            const button = event.target;
            
            // Demander confirmation
            if (!confirm('⚠️ Générer de nouvelles quêtes quotidiennes pour tous les joueurs ?\\n\\nCette action remplacera les quêtes quotidiennes actuelles.')) {
                return;
            }
            
            // Désactiver le bouton et afficher le chargement
            button.disabled = true;
            button.textContent = '⏳ Génération...';
            resultDiv.style.display = 'block';
            resultDiv.style.background = '#FFF3CD';
            resultDiv.style.color = '#4A3933';
            resultDiv.textContent = '⏳ Génération des quêtes quotidiennes...';
            
            try {
                const response = await fetch('/admin/api/generate-daily-quests', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    resultDiv.style.background = '#d4edda';
                    resultDiv.style.color = '#2d5016';
                    resultDiv.innerHTML = `<strong>${data.message}</strong>`;
                } else {
                    resultDiv.style.background = '#f8d7da';
                    resultDiv.style.color = '#8B0000';
                    resultDiv.innerHTML = `<strong>❌ Erreur :</strong> ${data.message}`;
                }
            } catch (error) {
                resultDiv.style.background = '#f8d7da';
                resultDiv.style.color = '#8B0000';
                resultDiv.innerHTML = `<strong>❌ Erreur :</strong> ${error.message}`;
            } finally {
                button.disabled = false;
                button.textContent = '🌅 Générer Quêtes Quotidiennes';
            }
        }

        // Générer des quêtes hebdomadaires
        async function generateWeeklyQuests() {
            const resultDiv = document.getElementById('weeklyQuestResult');
            const button = event.target;
            
            // Demander confirmation
            if (!confirm('⚠️ Générer/mettre à jour les quêtes hebdomadaires pour tous les joueurs ?\\n\\nCette action mettra à jour les 3 quêtes actives.')) {
                return;
            }
            
            // Désactiver le bouton et afficher le chargement
            button.disabled = true;
            button.textContent = '⏳ Génération...';
            resultDiv.style.display = 'block';
            resultDiv.style.background = '#FFF3CD';
            resultDiv.style.color = '#4A3933';
            resultDiv.textContent = '⏳ Génération des quêtes hebdomadaires...';
            
            try {
                const response = await fetch('/admin/api/generate-weekly-quests', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    resultDiv.style.background = '#d4edda';
                    resultDiv.style.color = '#2d5016';
                    resultDiv.innerHTML = `<strong>${data.message}</strong>`;
                } else {
                    resultDiv.style.background = '#f8d7da';
                    resultDiv.style.color = '#8B0000';
                    resultDiv.innerHTML = `<strong>❌ Erreur :</strong> ${data.message}`;
                }
            } catch (error) {
                resultDiv.style.background = '#f8d7da';
                resultDiv.style.color = '#8B0000';
                resultDiv.innerHTML = `<strong>❌ Erreur :</strong> ${error.message}`;
            } finally {
                button.disabled = false;
                button.textContent = '📅 Générer Quêtes Hebdomadaires';
            }
        }

        // === GESTION DES FICHIERS JSON ===
        
        let currentJsonFile = '';
        
        async function loadJsonFile() {
            const selector = document.getElementById('jsonFileSelector');
            const editor = document.getElementById('jsonEditor');
            const resultDiv = document.getElementById('jsonEditorResult');
            
            currentJsonFile = selector.value;
            
            if (!currentJsonFile) {
                editor.value = '';
                return;
            }
            
            try {
                const response = await fetch(`/admin/api/json-data/${currentJsonFile}`);
                const data = await response.json();
                
                if (data.success) {
                    editor.value = JSON.stringify(data.content, null, 2);
                    resultDiv.style.display = 'block';
                    resultDiv.style.background = '#d4edda';
                    resultDiv.style.color = '#2d5016';
                    resultDiv.innerHTML = `<strong>✅ Chargé :</strong> ${currentJsonFile} (${data.size})`;
                } else {
                    resultDiv.style.display = 'block';
                    resultDiv.style.background = '#f8d7da';
                    resultDiv.style.color = '#8B0000';
                    resultDiv.innerHTML = `<strong>❌ Erreur :</strong> ${data.message}`;
                }
            } catch (error) {
                resultDiv.style.display = 'block';
                resultDiv.style.background = '#f8d7da';
                resultDiv.style.color = '#8B0000';
                resultDiv.innerHTML = `<strong>❌ Erreur :</strong> ${error.message}`;
            }
        }
        
        async function saveJsonFile() {
            const editor = document.getElementById('jsonEditor');
            const resultDiv = document.getElementById('jsonEditorResult');
            
            if (!currentJsonFile) {
                alert('⚠️ Veuillez sélectionner un fichier');
                return;
            }
            
            // Vérifier que le JSON est valide
            try {
                JSON.parse(editor.value);
            } catch (e) {
                resultDiv.style.display = 'block';
                resultDiv.style.background = '#f8d7da';
                resultDiv.style.color = '#8B0000';
                resultDiv.innerHTML = `<strong>❌ JSON invalide :</strong> ${e.message}`;
                return;
            }
            
            // Demander confirmation
            if (!confirm(`⚠️ ATTENTION :\\n\\nVoulez-vous vraiment sauvegarder les modifications de ${currentJsonFile} ?\\n\\nCette action est IRRÉVERSIBLE !`)) {
                return;
            }
            
            try {
                const response = await fetch(`/admin/api/json-data/${currentJsonFile}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: JSON.parse(editor.value) })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    resultDiv.style.display = 'block';
                    resultDiv.style.background = '#d4edda';
                    resultDiv.style.color = '#2d5016';
                    resultDiv.innerHTML = `<strong>✅ Sauvegardé :</strong> ${currentJsonFile}`;
                } else {
                    resultDiv.style.display = 'block';
                    resultDiv.style.background = '#f8d7da';
                    resultDiv.style.color = '#8B0000';
                    resultDiv.innerHTML = `<strong>❌ Erreur :</strong> ${data.message}`;
                }
            } catch (error) {
                resultDiv.style.display = 'block';
                resultDiv.style.background = '#f8d7da';
                resultDiv.style.color = '#8B0000';
                resultDiv.innerHTML = `<strong>❌ Erreur :</strong> ${error.message}`;
            }
        }
        
        function formatJson() {
            const editor = document.getElementById('jsonEditor');
            const resultDiv = document.getElementById('jsonEditorResult');
            
            try {
                const parsed = JSON.parse(editor.value);
                editor.value = JSON.stringify(parsed, null, 2);
                
                resultDiv.style.display = 'block';
                resultDiv.style.background = '#d4edda';
                resultDiv.style.color = '#2d5016';
                resultDiv.innerHTML = '<strong>✅ JSON formaté avec succès</strong>';
            } catch (e) {
                resultDiv.style.display = 'block';
                resultDiv.style.background = '#f8d7da';
                resultDiv.style.color = '#8B0000';
                resultDiv.innerHTML = `<strong>❌ JSON invalide :</strong> ${e.message}`;
            }
        }
        
        async function resetJsonFile() {
            const editor = document.getElementById('jsonEditor');
            const resultDiv = document.getElementById('jsonEditorResult');
            
            if (!currentJsonFile) {
                alert('⚠️ Veuillez sélectionner un fichier');
                return;
            }
            
            // Demander confirmation avec avertissement sévère
            const confirmMessage = `⚠️⚠️⚠️ ATTENTION CRITIQUE ⚠️⚠️⚠️

Vous êtes sur le point de RÉINITIALISER complètement :
${currentJsonFile}

Cette action va :
❌ SUPPRIMER toutes les données actuelles
❌ Restaurer une structure VIERGE par défaut
❌ Cette action est IRRÉVERSIBLE

Êtes-vous ABSOLUMENT SÛR de vouloir continuer ?`;

            if (!confirm(confirmMessage)) {
                return;
            }
            
            // Double confirmation pour les fichiers critiques
            if (['players.json', 'savegame.json'].includes(currentJsonFile)) {
                if (!confirm(`⚠️ DERNIÈRE CONFIRMATION :\\n\\nVous allez réinitialiser ${currentJsonFile}.\\nTOUTES LES DONNÉES SERONT PERDUES !\\n\\nContinuer ?`)) {
                    return;
                }
            }
            
            try {
                const response = await fetch(`/admin/api/reset-json-data/${currentJsonFile}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Recharger le contenu réinitialisé
                    editor.value = JSON.stringify(data.content, null, 2);
                    
                    resultDiv.style.display = 'block';
                    resultDiv.style.background = '#d4edda';
                    resultDiv.style.color = '#2d5016';
                    resultDiv.innerHTML = `<strong>✅ Réinitialisé :</strong> ${currentJsonFile} (backup créé)`;
                } else {
                    resultDiv.style.display = 'block';
                    resultDiv.style.background = '#f8d7da';
                    resultDiv.style.color = '#8B0000';
                    resultDiv.innerHTML = `<strong>❌ Erreur :</strong> ${data.message}`;
                }
            } catch (error) {
                resultDiv.style.display = 'block';
                resultDiv.style.background = '#f8d7da';
                resultDiv.style.color = '#8B0000';
                resultDiv.innerHTML = `<strong>❌ Erreur :</strong> ${error.message}`;
            }
        }
    </script>
</body>
</html>
"""

@admin_bp.route('/')
def admin_interface():
    """Interface d'administration principale"""
    return render_template_string(ADMIN_INTERFACE_HTML)

@admin_bp.route('/api/tick-controls-status')
def get_tick_controls_status():
    """Get visibility status of HeaderBar tick controls"""
    try:
        settings_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'admin_settings.json')
        
        # Créer le fichier s'il n'existe pas
        if not os.path.exists(settings_file):
            default_settings = {"tick_controls_visible": True}
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            with open(settings_file, 'w') as f:
                json.dump(default_settings, f)
        
        # Lire les paramètres
        with open(settings_file, 'r') as f:
            settings = json.load(f)
        
        return jsonify({
            'success': True,
            'visible': settings.get('tick_controls_visible', True)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/toggle-tick-controls', methods=['POST'])
def toggle_tick_controls():
    """Toggle visibility of HeaderBar tick controls"""
    try:
        data = request.get_json()
        visible = data.get('visible', True)
        
        settings_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'admin_settings.json')
        
        # Créer ou mettre à jour le fichier
        settings = {"tick_controls_visible": visible}
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        
        return jsonify({
            'success': True,
            'visible': visible
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/refresh-interval/status')
def get_refresh_interval_status():
    """Get current refresh interval for HeaderBar data"""
    try:
        settings_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'admin_settings.json')
        
        if not os.path.exists(settings_file):
            default_settings = {"tick_controls_visible": True, "refresh_interval_seconds": 5}
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            with open(settings_file, 'w') as f:
                json.dump(default_settings, f)
        
        with open(settings_file, 'r') as f:
            settings = json.load(f)
        
        return jsonify({
            'success': True,
            'interval_seconds': settings.get('refresh_interval_seconds', 5)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/refresh-interval', methods=['POST'])
def set_refresh_interval():
    """Set refresh interval for HeaderBar data"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data received'}), 400
            
        interval_seconds = data.get('interval_seconds', 5)
        
        settings_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'admin_settings.json')
        
        # Charger les paramètres existants
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        else:
            settings = {"tick_controls_visible": True}
        
        # Mettre à jour l'intervalle
        settings['refresh_interval_seconds'] = interval_seconds
        
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        
        return jsonify({
            'success': True,
            'interval_seconds': interval_seconds
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# AUTO-TICK CONTROL ENDPOINTS
# ============================================================================

@admin_bp.route('/api/auto-tick', methods=['POST'])
def toggle_auto_tick():
    """Active/désactive l'auto-tick intégré au ManualTickService"""
    try:
        from flask import current_app
        tick_service = current_app.config.get('TICK_SERVICE')
        if not tick_service:
            return jsonify({'success': False, 'error': 'TickService not available'}), 500
            
        data = request.get_json()
        enabled = data.get('enabled', False)
        interval_seconds = data.get('interval_seconds', 1.0)
        
        # Changer l'intervalle (redémarre automatiquement si nécessaire)
        tick_service.set_auto_tick_interval(interval_seconds)
        
        # Démarrer/arrêter selon la demande
        if enabled and not tick_service.auto_tick_running:
            tick_service.start_auto_tick()
        elif not enabled and tick_service.auto_tick_running:
            tick_service.stop_auto_tick()
        
        # Récupérer le statut actuel
        status = tick_service.get_auto_tick_status()
        
        # Sauvegarder dans admin_settings.json centralisé
        try:
            import json
            import os
            settings_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'admin_settings.json')
            
            # Charger les paramètres existants
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    admin_settings = json.load(f)
            else:
                admin_settings = {}
            
            # Mettre à jour les paramètres d'auto-tick
            admin_settings['auto_tick_enabled'] = enabled
            admin_settings['auto_tick_interval_seconds'] = status['interval_seconds']
            
            # Sauvegarder
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(admin_settings, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save auto-tick settings: {e}")
        
        return jsonify({
            'success': True,
            'settings': {
                'enabled': enabled,
                'running': status['running'],
                'interval_seconds': status['interval_seconds']
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/auto-tick/status', methods=['GET'])
def get_auto_tick_status():
    """Récupère le statut de l'auto-tick intégré"""
    try:
        from flask import current_app
        tick_service = current_app.config.get('TICK_SERVICE')
        if not tick_service:
            return jsonify({'success': False, 'error': 'TickService not available'}), 500
            
        # Status de l'auto-tick intégré
        status = tick_service.get_auto_tick_status()
        
        return jsonify({
            'success': True,
            'settings': status
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# MANUAL TICK ENDPOINT
# ============================================================================

@admin_bp.route('/api/manual-tick', methods=['POST'])
def execute_manual_tick():
    """Exécute un tick manuel sur toutes les villes"""
    try:
        from flask import current_app
        tick_service = current_app.config.get('TICK_SERVICE')
        if not tick_service:
            return jsonify({'success': False, 'error': 'TickService not available'}), 500
        
        # Forcer la sauvegarde pour les ticks manuels
        was_running = tick_service.auto_tick_running
        tick_service.auto_tick_running = True
        raw_results = tick_service.execute_tick()
        tick_service.auto_tick_running = was_running
        
        # Adapter le format pour le HeaderBar
        results = {
            'gold_updated': raw_results.get('total_production', {}).get('gold', 0),
            'research_updated': raw_results.get('total_production', {}).get('research_points', 0),
            'population_updated': raw_results.get('cities_updated', 0),
            'cities_count': raw_results.get('cities_updated', 0),
            'players_count': raw_results.get('players_updated', 0)
        }
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# AI AUTO ENDPOINTS (pour AIDebugPopup.tsx)
# ============================================================================

@admin_bp.route('/api/admin/ai/auto-status')
def get_ai_auto_status():
    """Get current AI auto-execution status (appelé par AIDebugPopup)"""
    try:
        from flask import current_app
        data_manager = current_app.config.get('DATA_MANAGER')
        if not data_manager:
            return jsonify({'success': False, 'error': 'DataManager not available'}), 500
        
        enabled = data_manager.is_ai_auto_enabled()
        
        return jsonify({
            'success': True,
            'ai_auto_enabled': enabled
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/admin/ai/toggle-auto', methods=['POST'])
def toggle_ai_auto():
    """Toggle AI auto-execution on/off (appelé par AIDebugPopup)"""
    try:
        from flask import current_app
        data_manager = current_app.config.get('DATA_MANAGER')
        if not data_manager:
            return jsonify({'success': False, 'error': 'DataManager not available'}), 500
        
        # Récupérer l'état actuel
        settings = data_manager.load_admin_settings()
        current_state = settings.get('ai_auto_enabled', False)
        
        # Inverser l'état
        new_state = not current_state
        settings['ai_auto_enabled'] = new_state
        
        # Sauvegarder
        data_manager.save_admin_settings(settings)
        
        return jsonify({
            'success': True,
            'ai_auto_enabled': new_state
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# CONSTRUCTION TIME MULTIPLIER ENDPOINTS
# ============================================================================

@admin_bp.route('/api/construction-multiplier/status', methods=['GET'])
def get_construction_multiplier_status():
    """Get current construction time multiplier"""
    try:
        settings_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'admin_settings.json')
        
        if not os.path.exists(settings_file):
            return jsonify({
                'success': True,
                'multiplier': 1.0
            })
        
        with open(settings_file, 'r') as f:
            settings = json.load(f)
        
        return jsonify({
            'success': True,
            'multiplier': settings.get('construction_time_multiplier', 1.0)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/construction-multiplier', methods=['POST'])
def set_construction_multiplier():
    """Set construction time multiplier"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data received'}), 400
            
        multiplier = data.get('multiplier', 1.0)
        
        # Valider le multiplicateur (entre 0.01 et 10)
        if multiplier < 0.01 or multiplier > 10:
            return jsonify({'success': False, 'error': 'Multiplier must be between 0.01 and 10'}), 400
        
        settings_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'admin_settings.json')
        
        # Charger les paramètres existants
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        else:
            settings = {}
        
        # Mettre à jour le multiplicateur
        settings['construction_time_multiplier'] = multiplier
        
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        
        return jsonify({
            'success': True,
            'multiplier': multiplier
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# QUEST GENERATION ENDPOINT
# ============================================================================

@admin_bp.route('/api/generate-daily-quests', methods=['POST'])
def generate_daily_quests():
    """Génère des quêtes quotidiennes aléatoires pour tous les joueurs (à exécuter chaque jour)"""
    try:
        from app.services.quest_service import quest_service
        from datetime import datetime
        
        # Charger la liste des joueurs
        players_file = os.path.join(os.path.dirname(__file__), '..', '..', 'gamedata', 'players.json')
        with open(players_file, 'r', encoding='utf-8') as f:
            players_data = json.load(f)
        
        players = players_data.get('players', [])
        players_updated = 0
        total_quests = 0
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Charger player_quests.json
        player_quests_file = os.path.join(os.path.dirname(__file__), '..', '..', 'gamedata', 'player_quests.json')
        with open(player_quests_file, 'r', encoding='utf-8') as f:
            player_quests_data = json.load(f)
        
        for player in players:
            username = player.get('username')
            if not username:
                continue
            
            # Calculer le niveau du joueur
            player_level = quest_service.calculate_player_level(username)
            
            # Générer 5 quêtes aléatoires (format simplifié)
            daily_quests = quest_service.generate_daily_quests(username)
            
            # Initialiser le joueur s'il n'existe pas
            if username not in player_quests_data:
                player_quests_data[username] = {
                    "level": player_level,
                    "daily_quests": {
                        "generated_date": today,
                        "quests": []
                    },
                    "weekly_quests": {
                        "generated_date": today,
                        "quests": []
                    },
                    "unclaimed_rewards": [],
                    "completed_weekly_quests": []
                }
            
            # Mettre à jour les quêtes quotidiennes (format simplifié)
            player_quests_data[username]['daily_quests'] = {
                "generated_date": today,
                "quests": daily_quests  # Format simplifié: {id, progress, stars_earned, rewards_claimed}
            }
            
            player_quests_data[username]['level'] = player_level
            
            players_updated += 1
            total_quests += len(daily_quests)
        
        # Sauvegarder avec formatage compact
        quest_service.save_all_player_quests(player_quests_data)
        
        return jsonify({
            'success': True,
            'players_updated': players_updated,
            'total_quests': total_quests,
            'message': f'✅ {players_updated} joueur(s) avec {total_quests} quêtes quotidiennes générées'
        })
        
    except Exception as e:
        print(f"❌ Error generating daily quests: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/generate-weekly-quests', methods=['POST'])
def generate_weekly_quests():
    """Génère/met à jour les quêtes hebdomadaires pour tous les joueurs (à exécuter chaque semaine)"""
    try:
        from app.services.quest_service import quest_service
        from datetime import datetime
        
        # Charger la liste des joueurs
        players_file = os.path.join(os.path.dirname(__file__), '..', '..', 'gamedata', 'players.json')
        with open(players_file, 'r', encoding='utf-8') as f:
            players_data = json.load(f)
        
        players = players_data.get('players', [])
        players_updated = 0
        total_quests = 0
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Charger player_quests.json
        player_quests_file = os.path.join(os.path.dirname(__file__), '..', '..', 'gamedata', 'player_quests.json')
        with open(player_quests_file, 'r', encoding='utf-8') as f:
            player_quests_data = json.load(f)
        
        for player in players:
            username = player.get('username')
            if not username:
                continue
            
            # Calculer le niveau du joueur
            player_level = quest_service.calculate_player_level(username)
            
            # Générer les quêtes principales (progression chronologique)
            weekly_quests = quest_service.generate_main_quests(username)
            
            # Initialiser le joueur s'il n'existe pas
            if username not in player_quests_data:
                player_quests_data[username] = {
                    "level": player_level,
                    "daily_quests": {
                        "generated_date": today,
                        "quests": []
                    },
                    "weekly_quests": {
                        "generated_date": today,
                        "quests": []
                    },
                    "unclaimed_rewards": [],
                    "completed_weekly_quests": []
                }
            
            # Mettre à jour les quêtes hebdomadaires
            player_quests_data[username]['weekly_quests'] = {
                "generated_date": today,
                "quests": weekly_quests  # Format: {id, progress, is_completed}
            }
            
            player_quests_data[username]['level'] = player_level
            
            players_updated += 1
            total_quests += len(weekly_quests)
        
        # Sauvegarder avec formatage compact
        quest_service.save_all_player_quests(player_quests_data)
        
        return jsonify({
            'success': True,
            'players_updated': players_updated,
            'total_quests': total_quests,
            'message': f'✅ {players_updated} joueur(s) avec {total_quests} quêtes hebdomadaires générées'
        })
        
    except Exception as e:
        print(f"❌ Error generating weekly quests: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/json-data/<filename>')
def get_json_data(filename):
    """Récupère le contenu d'un fichier JSON"""
    try:
        # Liste des fichiers autorisés
        allowed_files = [
            'players.json', 'savegame.json', 'player_quests.json',
            'player_heroes.json', 'player_profiles.json', 'player_unit_improvements.json',
            'battlefields_v2.json', 'battlesv2.json', 'battle_reports.json',
            'battle_replays.json', 'battle_notifications.json',
            'transports.json', 'transport_history.json',
            'messages.json', 'notifications.json', 'market.json',
            'resource_sites.json', 'ai_auto_cycles.json', 'ai_console_logs.json', 'ai_strategies_state.json'
        ]
        
        if filename not in allowed_files:
            return jsonify({'success': False, 'message': 'Fichier non autorisé'}), 403
        
        file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'gamedata', filename)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'Fichier non trouvé'}), 404
        
        # Lire le fichier
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        # Calculer la taille
        file_size = os.path.getsize(file_path)
        if file_size < 1024:
            size_str = f"{file_size} octets"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.2f} Ko"
        else:
            size_str = f"{file_size / (1024 * 1024):.2f} Mo"
        
        return jsonify({
            'success': True,
            'content': content,
            'size': size_str
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/api/json-data/<filename>', methods=['POST'])
def save_json_data(filename):
    """Sauvegarde le contenu d'un fichier JSON"""
    try:
        # Liste des fichiers autorisés
        allowed_files = [
            'players.json', 'savegame.json', 'player_quests.json',
            'player_heroes.json', 'player_profiles.json', 'player_unit_improvements.json',
            'battlefields_v2.json', 'battlesv2.json', 'battle_reports.json',
            'battle_replays.json', 'battle_notifications.json',
            'transports.json', 'transport_history.json',
            'messages.json', 'notifications.json', 'market.json',
            'resource_sites.json', 'ai_auto_cycles.json', 'ai_console_logs.json', 'ai_strategies_state.json'
        ]
        
        if filename not in allowed_files:
            return jsonify({'success': False, 'message': 'Fichier non autorisé'}), 403
        
        data = request.get_json()
        content = data.get('content')
        
        if content is None:
            return jsonify({'success': False, 'message': 'Contenu manquant'}), 400
        
        file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'gamedata', filename)
        
        # Créer une sauvegarde avant modification
        backup_path = file_path + '.backup'
        if os.path.exists(file_path):
            import shutil
            shutil.copy2(file_path, backup_path)
        
        # Sauvegarder le nouveau contenu
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        
        # Si c'est players.json, nettoyer ai_strategies_state.json
        if filename == 'players.json':
            try:
                # Récupérer la liste des IDs de joueurs IA restants
                remaining_ai_players = set()
                for player in content.get('players', []):
                    if player.get('is_ai', False):
                        remaining_ai_players.add(player.get('id'))
                
                # Charger ai_strategies_state.json
                ai_state_path = os.path.join(os.path.dirname(__file__), '..', '..', 'gamedata', 'ai_strategies_state.json')
                
                if os.path.exists(ai_state_path):
                    with open(ai_state_path, 'r', encoding='utf-8') as f:
                        ai_state = json.load(f)
                    
                    # Supprimer les entrées des joueurs qui n'existent plus
                    players_to_remove = [pid for pid in ai_state.keys() if pid not in remaining_ai_players]
                    
                    if players_to_remove:
                        for pid in players_to_remove:
                            del ai_state[pid]
                        
                        # Sauvegarder ai_strategies_state.json nettoyé
                        with open(ai_state_path, 'w', encoding='utf-8') as f:
                            json.dump(ai_state, f, indent=2, ensure_ascii=False)
                        
                        print(f"✅ Nettoyage ai_strategies_state.json: {len(players_to_remove)} joueurs supprimés")
            
            except Exception as e:
                print(f"⚠️ Erreur nettoyage ai_strategies_state.json: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Fichier {filename} sauvegardé avec succès (backup créé)'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/api/reset-json-data/<filename>', methods=['POST'])
def reset_json_data(filename):
    """Réinitialise un fichier JSON avec sa structure par défaut"""
    try:
        # Liste des fichiers autorisés
        allowed_files = [
            'players.json', 'savegame.json', 'player_quests.json',
            'player_heroes.json', 'player_profiles.json', 'player_unit_improvements.json',
            'battlefields_v2.json', 'battlesv2.json', 'battle_reports.json',
            'battle_replays.json', 'battle_notifications.json',
            'transports.json', 'transport_history.json',
            'messages.json', 'notifications.json', 'market.json',
            'resource_sites.json', 'ai_auto_cycles.json', 'ai_console_logs.json', 'ai_strategies_state.json'
        ]
        
        if filename not in allowed_files:
            return jsonify({'success': False, 'message': 'Fichier non autorisé'}), 403
        
        # Définir les structures par défaut pour chaque fichier
        default_structures = {
            'players.json': {"players": []},
            'savegame.json': {"cities": [], "timestamp": 0},
            'player_quests.json': {},
            'player_heroes.json': {},
            'player_profiles.json': {},
            'player_unit_improvements.json': {},
            'battlefields_v2.json': {},
            'battlesv2.json': {},
            'battle_reports.json': {"reports": []},
            'battle_replays.json': {"replays": []},
            'battle_notifications.json': {},
            'transports.json': {"transports": [], "next_id": 1},
            'transport_history.json': {"transport_history": []},
            'messages.json': {"messages": []},
            'notifications.json': {"notifications": []},
            'market.json': {
                "offers": [],
                "next_offer_id": 1
            }
        }
        
        # Récupérer la structure par défaut
        default_content = default_structures.get(filename, {})
        
        file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'gamedata', filename)
        
        # Créer une sauvegarde avant réinitialisation
        backup_path = file_path + '.backup'
        if os.path.exists(file_path):
            import shutil
            shutil.copy2(file_path, backup_path)
        
        # Écrire la structure par défaut
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(default_content, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'message': f'Fichier {filename} réinitialisé avec succès (backup créé)',
            'content': default_content
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# =============================================================================
# INTERFACE D'ADMINISTRATION DES IA
# =============================================================================

@admin_bp.route('/ai')
def ai_admin_interface():
    """Interface d'administration des joueurs IA"""
    return render_template('ai_admin.html')
