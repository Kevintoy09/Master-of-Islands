import React, { useEffect, useState } from 'react';
import { Dialog, DialogContent, Box, Typography, IconButton } from '@mui/material';
import { Close } from '@mui/icons-material';
import { Faction, FACTIONS } from '../data/factions';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import '../styles/FactionStatsPopup.css';

interface FactionStatsPopupProps {
  open: boolean;
  onClose: () => void;
  playerFaction: string | null; // ID de la faction du joueur (stone, iron, cereal, papyrus)
}

const FactionStatsPopup: React.FC<FactionStatsPopupProps> = ({ open, onClose, playerFaction }) => {
  const [factionStats, setFactionStats] = useState<{ faction: string; count: number; percentage: number }[]>([]);
  const [loading, setLoading] = useState(true);

  const faction: Faction | null = playerFaction ? FACTIONS[playerFaction] : null;

  useEffect(() => {
    if (open) {
      loadFactionStats();
    }
  }, [open]);

  const loadFactionStats = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/players/faction-stats');
      if (response.ok) {
        const data = await response.json();
        setFactionStats(data.stats || []);
      }
    } catch (error) {
      console.error('Erreur chargement stats factions:', error);
    } finally {
      setLoading(false);
    }
  };

  // Données pour le graphique
  const chartData = factionStats.map(stat => ({
    name: FACTIONS[stat.faction]?.name || stat.faction,
    value: stat.count,
    percentage: stat.percentage
  }));

  // Couleurs pour chaque faction
  const COLORS: Record<string, string> = {
    stone: '#a1887f',
    iron: '#b22222',
    cereal: '#fbc02d',
    papyrus: '#7e57c2'
  };

  if (!faction) return null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        className: 'faction-stats-dialog roman-panel',
        style: {
          background: 'linear-gradient(135deg, rgba(47, 27, 20, 0.98) 0%, rgba(36, 20, 15, 0.98) 100%)',
          borderRadius: '8px',
          border: `3px solid ${faction.theme.accent}`,
        }
      }}
    >
      <DialogContent className="faction-stats-content">
        {/* Header avec bouton fermer */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4" className="roman-title" sx={{ color: faction.theme.accent }}>
            Ma Faction
          </Typography>
          <IconButton onClick={onClose} sx={{ color: 'var(--bronze)' }}>
            <Close />
          </IconButton>
        </Box>

        {/* Logo et info faction */}
        <Box className="faction-info-section">
          <Box className="faction-logo-small">
            <img src={faction.logo} alt={faction.name} />
          </Box>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h5" className="roman-title" sx={{ color: faction.theme.accent, mb: 1 }}>
              {faction.name}
            </Typography>
            <Typography variant="body2" className="roman-text" sx={{ color: 'var(--roman-gold)', fontStyle: 'italic', mb: 2 }}>
              "{faction.motto}"
            </Typography>
            <Typography variant="body1" className="roman-text" sx={{ color: '#d4c5a9', mb: 2 }}>
              {faction.description}
            </Typography>
          </Box>
        </Box>

        {/* Bonus de faction */}
        <Box className="faction-bonus-section">
          <Typography variant="h6" className="roman-subtitle" sx={{ color: faction.theme.accent, mb: 1 }}>
            <span style={{ fontSize: '1.5rem', marginRight: '8px' }}>{faction.bonus.icon}</span>
            Bonus de Faction
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h4" sx={{ color: 'var(--roman-gold)', fontWeight: 'bold' }}>
              {faction.bonus.value}
            </Typography>
            <Typography variant="body1" className="roman-text" sx={{ color: '#d4c5a9' }}>
              {faction.bonus.description}
            </Typography>
          </Box>
          {/* Détails des bonus si disponibles */}
          {faction.bonusDetails && faction.bonusDetails.length > 0 && (
            <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
              {faction.bonusDetails.map((detail, index) => (
                <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <span style={{ fontSize: '1.2rem' }}>{detail.icon}</span>
                  <Typography variant="body2" className="roman-text" sx={{ color: '#d4c5a9' }}>
                    {detail.text}
                  </Typography>
                </Box>
              ))}
            </Box>
          )}
        </Box>

        {/* Statistiques globales */}
        <Box className="faction-global-stats">
          <Typography variant="h6" className="roman-subtitle" sx={{ color: 'var(--roman-gold)', mb: 2 }}>
            📊 Répartition des Factions dans le Monde
          </Typography>

          {loading ? (
            <Typography className="roman-text" sx={{ textAlign: 'center', color: '#999' }}>
              Chargement...
            </Typography>
          ) : chartData.length > 0 ? (
            <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
              {/* Graphique circulaire */}
              <Box sx={{ flex: 1, minHeight: 250 }}>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={(entry: any) => `${entry.percent ? (entry.percent * 100).toFixed(1) : 0}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {chartData.map((entry, index) => {
                        const factionKey = factionStats[index]?.faction || 'stone';
                        return <Cell key={`cell-${index}`} fill={COLORS[factionKey] || '#999'} />;
                      })}
                    </Pie>
                    <Tooltip 
                      contentStyle={{
                        background: 'rgba(0,0,0,0.8)',
                        border: '1px solid var(--bronze)',
                        borderRadius: '4px',
                        color: '#fff'
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </Box>

              {/* Légende détaillée */}
              <Box sx={{ flex: 1 }}>
                {factionStats.map(stat => {
                  const f = FACTIONS[stat.faction];
                  if (!f) return null;
                  return (
                    <Box 
                      key={stat.faction} 
                      className="faction-stat-row"
                      sx={{
                        background: stat.faction === playerFaction ? 'rgba(218, 165, 32, 0.1)' : 'transparent',
                        border: stat.faction === playerFaction ? '1px solid var(--roman-gold)' : '1px solid transparent',
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box 
                          sx={{ 
                            width: 16, 
                            height: 16, 
                            borderRadius: '50%', 
                            background: COLORS[stat.faction] 
                          }} 
                        />
                        <Typography className="roman-text" sx={{ color: '#d4c5a9', fontWeight: stat.faction === playerFaction ? 'bold' : 'normal' }}>
                          {f.name}
                        </Typography>
                      </Box>
                      <Typography className="roman-text" sx={{ color: 'var(--roman-gold)' }}>
                        {stat.count} joueurs ({stat.percentage.toFixed(1)}%)
                      </Typography>
                    </Box>
                  );
                })}
              </Box>
            </Box>
          ) : (
            <Typography className="roman-text" sx={{ textAlign: 'center', color: '#999' }}>
              Aucune statistique disponible
            </Typography>
          )}
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default FactionStatsPopup;
