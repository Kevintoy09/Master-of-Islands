import { getApiUrl } from '../utils/api';

export interface PlayerResearchData {
  unlocked_research: string[];
  research_points: number;
  research_effects: {
    resource_bonuses?: { [key: string]: number };
  };
  faction?: string;
}

export interface UnlockResearchRequest {
  name: string;
  cost: {
    research_points: number;
    gold?: number;
  };
}

export interface UnlockResearchResponse {
  success: boolean;
  message: string;
  new_research_points?: number;
}

export class PlayerResearchService {
  private static async makeRequest(url: string, options: RequestInit = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const response = await fetch(`${getApiUrl()}${url}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  static async getPlayerResearch(playerId: string): Promise<PlayerResearchData> {
    const result = await this.makeRequest(`/api/research/player/${playerId}`);
    return result.data;
  }

  static async unlockResearch(
    playerId: string, 
    researchId: string, 
    researchData: UnlockResearchRequest
  ): Promise<UnlockResearchResponse> {
    return this.makeRequest(`/api/research/unlock/${playerId}/${researchId}`, {
      method: 'POST',
      body: JSON.stringify(researchData),
    });
  }

  static async getResearchPoints(playerId: string): Promise<number> {
    const result = await this.makeRequest(`/api/player/${playerId}/research-points`);
    return result.research_points;
  }
}