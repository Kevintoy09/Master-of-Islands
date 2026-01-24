import React from 'react';
import { Dialog, DialogContent, Box, Typography, Button } from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import { Faction } from '../data/factions';
import '../styles/FactionWelcomePopup.css';

interface FactionWelcomePopupProps {
  open: boolean;
  faction: Faction | null;
  onClose: () => void;
  onBack?: () => void;
}

const FactionWelcomePopup: React.FC<FactionWelcomePopupProps> = ({ open, faction, onClose, onBack }) => {
  if (!faction) return null;

  return (
    <Dialog
      open={open}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        className: 'faction-welcome-dialog roman-panel',
        style: {
          background: 'linear-gradient(135deg, rgba(47, 27, 20, 0.98) 0%, rgba(36, 20, 15, 0.98) 100%)',
          borderRadius: '8px',
          border: `3px solid ${faction.theme.accent}`,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
        }
      }}
    >
      <DialogContent className="faction-welcome-content">
        {/* Bouton retour */}
        {onBack && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
            <Button
              variant="outlined"
              startIcon={<ArrowBack />}
              onClick={onBack}
              className="roman-button secondary-button"
              sx={{
                borderColor: 'var(--bronze)',
                color: 'var(--roman-red)',
                '&:hover': {
                  borderColor: 'var(--roman-gold)',
                  backgroundColor: 'rgba(218, 165, 32, 0.1)'
                }
              }}
            >
              Retour
            </Button>
          </Box>
        )}
        {/* Header avec logo */}
        <Box className="faction-header">
          <Box 
            className="faction-logo-container"
            sx={{
              borderColor: faction.theme.accent,
              boxShadow: `0 0 30px ${faction.theme.accent}60`,
            }}
          >
            <img 
              src={faction.logo} 
              alt={faction.name}
              className="faction-logo"
            />
          </Box>
          
          <Typography 
            variant="h3" 
            className="roman-title faction-title"
            sx={{ 
              color: faction.theme.accent,
              textShadow: `2px 2px 4px rgba(0,0,0,0.7)`,
            }}
          >
            {faction.name}
          </Typography>
          
          <Typography 
            variant="h6" 
            className="roman-subtitle faction-motto"
            sx={{ fontStyle: 'italic', color: 'var(--roman-gold)' }}
          >
            "{faction.motto}"
          </Typography>
        </Box>

        {/* Description */}
        <Box className="faction-description">
          <Typography variant="body1" sx={{ color: '#e0e0e0', lineHeight: 1.8 }}>
            {faction.description}
          </Typography>
        </Box>

        {/* Bonus */}
        <Box 
          className="faction-bonus"
          sx={{
            background: `linear-gradient(135deg, ${faction.theme.primary}40 0%, ${faction.theme.secondary}40 100%)`,
            borderColor: faction.theme.accent,
          }}
        >
          <Box className="bonus-icon" sx={{ fontSize: '3rem' }}>
            {faction.bonus.icon}
          </Box>
          <Typography variant="h5" sx={{ color: faction.theme.accent, fontWeight: 'bold' }}>
            Bonus de faction
          </Typography>
          <Typography variant="h4" sx={{ color: '#d4af37', fontWeight: 'bold', my: 1 }}>
            {faction.bonus.value}
          </Typography>
          <Typography variant="body1" sx={{ color: '#e0e0e0' }}>
            {faction.bonus.description}
          </Typography>
          {/* Détails des bonus si disponibles */}
          {faction.bonusDetails && faction.bonusDetails.length > 0 && (
            <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 1, alignItems: 'center' }}>
              {faction.bonusDetails.map((detail, index) => (
                <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <span style={{ fontSize: '1.2rem' }}>{detail.icon}</span>
                  <Typography variant="body2" sx={{ color: '#d4c5a9' }}>
                    {detail.text}
                  </Typography>
                </Box>
              ))}
            </Box>
          )}
        </Box>

        {/* Footer decoratif */}
        <Box className="faction-footer">
          <Box 
            className="decorative-line"
            sx={{
              background: `linear-gradient(90deg, transparent, ${faction.theme.accent}, transparent)`,
            }}
          />
          <Typography variant="caption" sx={{ color: '#999', fontStyle: 'italic' }}>
            Votre destin est scellé. Que la gloire vous accompagne.
          </Typography>
        </Box>

        {/* Bouton de confirmation */}
        <Button
          variant="contained"
          fullWidth
          onClick={onClose}
          className="roman-button primary-button"
          sx={{
            mt: 3,
            py: 1.5,
            fontSize: '1.1rem',
            fontWeight: 'bold',
            background: `linear-gradient(135deg, ${faction.theme.primary} 0%, ${faction.theme.secondary} 100%)`,
            border: `2px solid ${faction.theme.accent}`,
            color: '#fff',
            '&:hover': {
              background: `linear-gradient(135deg, ${faction.theme.secondary} 0%, ${faction.theme.primary} 100%)`,
              boxShadow: `0 4px 12px ${faction.theme.accent}80`,
              transform: 'translateY(-2px)',
            }
          }}
        >
          ⚔️ Commencer mon règne
        </Button>
      </DialogContent>
    </Dialog>
  );
};

export default FactionWelcomePopup;
