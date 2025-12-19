import { useState, useEffect } from 'react';

interface TransportConstants {
  transport_speed: number;
  ship_capacity: number;
}

export const useTransportConstants = () => {
  const [constants, setConstants] = useState<TransportConstants | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchConstants = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/transport/constants');
        
        if (response.ok) {
          const data = await response.json();
          setConstants({
            transport_speed: data.transport_speed,
            ship_capacity: data.ship_capacity
          });
          setError(null);
        } else {
          setError('Erreur lors du chargement des constantes');
        }
      } catch (err) {
        setError('Erreur de connexion');
        console.error('Erreur constantes transport:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchConstants();
  }, []);

  return { constants, loading, error };
};
