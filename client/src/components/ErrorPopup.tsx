import React, { useEffect } from 'react';
import './ErrorPopup.css';

interface ErrorPopupProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  message: string;
  icon?: string;
  autoClose?: number; // Fermeture automatique après X millisecondes (optionnel)
}

const ErrorPopup: React.FC<ErrorPopupProps> = ({
  isOpen,
  onClose,
  title = '⚠️ Attention',
  message,
  icon = '🚫',
  autoClose
}) => {
  // Fermeture automatique si défini
  useEffect(() => {
    if (isOpen && autoClose) {
      const timer = setTimeout(() => {
        onClose();
      }, autoClose);
      return () => clearTimeout(timer);
    }
  }, [isOpen, autoClose, onClose]);

  // Fermeture avec Escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="error-popup-overlay" onClick={onClose}>
      <div className="error-popup-container" onClick={(e) => e.stopPropagation()}>
        <button className="error-popup-close" onClick={onClose}>×</button>
        
        <div className="error-popup-icon">{icon}</div>
        
        <div className="error-popup-title">{title}</div>
        
        <div className="error-popup-message">{message}</div>
        
        <button className="error-popup-button" onClick={onClose}>
          Compris
        </button>
      </div>
    </div>
  );
};

export default ErrorPopup;
