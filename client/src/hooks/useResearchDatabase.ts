import { useState, useEffect } from 'react';

// Interface pour les recherches (identique à celle de researchDatabase.ts)
export interface Research {
  id: string;
  level: number;
  name: string;
  age: string;
  description: string;
  cost: {
    research_points: number;
    gold?: number;
  };
  prerequisites: string[];
  effect: any;
  category: 'economy' | 'science' | 'warfare' | 'marine';
  exclusive_group?: string; // Groupe de choix exclusifs
}

interface ResearchDatabase {
  researches: Research[];
  categories: string[];
}

interface ResearchByCategory {
  researches: Research[];
  category: string;
  count: number;
}

// Hook pour récupérer toute la base de données des recherches
export const useResearchDatabase = () => {
  const [data, setData] = useState<ResearchDatabase | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchResearchDatabase = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/research/database');
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const researchData = await response.json();
        setData(researchData);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erreur lors du chargement des recherches');
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchResearchDatabase();
  }, []);

  const getResearchById = (id: string): Research | undefined => {
    if (!data) return undefined;
    return data.researches.find(research => research.id === id);
  };

  return { 
    data, 
    loading, 
    error,
    getResearchById
  };
};

// Hook pour récupérer les recherches d'une catégorie
export const useResearchByCategory = (category: string) => {
  const [data, setData] = useState<ResearchByCategory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!category) return;

    const fetchResearchByCategory = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/research/database/${category}`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const researchData = await response.json();
        setData(researchData);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erreur lors du chargement des recherches');
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchResearchByCategory();
  }, [category]);

  return { data, loading, error };
};

// Fonctions utilitaires compatibles avec l'ancien système
export const getResearchesByCategory = (researches: Research[], category: Research['category']): Research[] => {
  return researches.filter(research => research.category === category);
};

export const getResearchById = (researches: Research[], id: string): Research | undefined => {
  return researches.find(research => research.id === id);
};

export const getAllCategories = (): Research['category'][] => {
  return ['economy', 'science', 'warfare', 'marine'];
};

