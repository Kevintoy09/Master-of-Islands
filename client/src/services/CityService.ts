// Service centralisé pour toutes les API liées aux villes
import { City } from '../types';

export class CityService {
  
  static async getCityState(cityId: string): Promise<City> {
    const res = await fetch(`/api/city-state/${cityId}`);
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || "API ville inaccessible");
    }
    const text = await res.text();
    return JSON.parse(text);
  }

  static async getUniverseData(): Promise<any> {
    const res = await fetch('/api/universe');
    if (!res.ok) {
      throw new Error("Impossible de charger les données univers");
    }
    return res.json();
  }

  static async renameTownHall(cityId: string, newName: string): Promise<any> {
    const res = await fetch(`/api/city/${cityId}/rename`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName })
    });
    if (!res.ok) {
      throw new Error("Erreur lors du renommage");
    }
    return res.json();
  }

  static async updateTaxRate(cityId: string, rate: number): Promise<any> {
    const res = await fetch(`/api/city/${cityId}/tax-rate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tax_rate: rate })
    });
    if (!res.ok) {
      throw new Error("Erreur lors du changement de taux d'impôt");
    }
    return res.json();
  }
}
