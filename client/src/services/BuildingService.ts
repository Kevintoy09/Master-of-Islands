// Service centralisé pour toutes les API liées aux bâtiments

export class BuildingService {
  
  static async buildBuilding(cityId: string, slotId: string, buildingName: string): Promise<any> {
    const res = await fetch(`/api/city/${cityId}/build`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slot_id: slotId, building: buildingName })
    });
    
    if (!res.ok) {
      let errMsg = 'Erreur lors de la construction';
      try {
        const text = await res.text();
        try {
          const err = JSON.parse(text);
          errMsg = err.message || text || errMsg;
        } catch {
          errMsg = text || errMsg;
        }
      } catch {}
      throw new Error(errMsg);
    }
    
    return res.json();
  }

  static async destroyBuilding(cityId: string, slotId: string): Promise<any> {
    const res = await fetch(`/api/city/${cityId}/destroy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slot_id: slotId })
    });
    
    if (!res.ok) {
      let errMsg = 'Erreur lors de la destruction';
      try {
        const text = await res.text();
        try {
          const err = JSON.parse(text);
          errMsg = err.message || text || errMsg;
        } catch { 
          errMsg = text || errMsg; 
        }
      } catch {}
      throw new Error(errMsg);
    }
    
    return res.json();
  }

  static async finishConstruction(cityId: string, slotId: string): Promise<any> {
    const res = await fetch(`/api/city/${cityId}/finish-construction`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slot_id: slotId })
    });
    
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.error || 'Erreur lors de la finalisation');
    }
    
    return res.json();
  }

  static async getAvailableBuildings(cityId: string, slotType: string): Promise<any> {
    const res = await fetch(`/api/city/${cityId}/buildings?slot_type=${slotType}`);
    if (!res.ok) {
      throw new Error("Impossible de charger les bâtiments");
    }
    return res.json();
  }

  static async getBuildingCosts(cityId: string): Promise<any> {
    const res = await fetch(`/api/city/${cityId}/building-costs`);
    if (!res.ok) {
      throw new Error("Impossible de charger les coûts");
    }
    return res.json();
  }
}
