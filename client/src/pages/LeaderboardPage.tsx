import React, { useState, useEffect } from 'react';
import { useUser } from '../hooks/useUser';
import '../styles/LeaderboardPage.css';

interface PlayerStats {
  rank: number;
  player_id: string;
  username: string;
  general_score: number;
  construction_points: number;
  research_points_invested: number;
  military_xp: number;
  units_killed: number;
  units_lost: number;
  victories: number;
  defeats: number;
  quest_points: number;
}

type Category = 'general' | 'construction' | 'research' | 'military_xp' | 'units_killed' | 'units_lost' | 'victories' | 'quests';

const LeaderboardPage: React.FC = () => {
  const { user } = useUser();
  const [leaderboard, setLeaderboard] = useState<PlayerStats[]>([]);
  const [category, setCategory] = useState<Category>('general');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLeaderboard();
  }, [category]);

  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/leaderboard/${category}`);
      const data = await response.json();

      if (data.success) {
        setLeaderboard(data.leaderboard);
      }
    } catch (error) {
      console.error('Erreur chargement classement:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryTitle = () => {
    const titles: Record<Category, string> = {
      general: 'Classement Général',
      construction: 'Points de Construction',
      research: 'Points de Recherche',
      military_xp: 'Expérience Militaire',
      units_killed: 'Unités Tuées',
      units_lost: 'Unités Perdues',
      victories: 'Victoires',
      quests: 'Points de Quêtes'
    };
    return titles[category];
  };

  const getCategoryIcon = () => {
    const icons: Record<Category, string> = {
      general: '🏆',
      construction: '🏗️',
      research: '🔬',
      military_xp: '⚔️',
      units_killed: '💀',
      units_lost: '☠️',
      victories: '🎖️',
      quests: '🎯'
    };
    return icons[category];
  };

  const getCategoryValue = (player: PlayerStats) => {
    const values: Record<Category, number> = {
      general: player.general_score,
      construction: player.construction_points,
      research: player.research_points_invested,
      military_xp: player.military_xp,
      units_killed: player.units_killed,
      units_lost: player.units_lost,
      victories: player.victories,
      quests: player.quest_points
    };
    return values[category];
  };

  const getRankClass = (rank: number) => {
    if (rank === 1) return 'rank-gold';
    if (rank === 2) return 'rank-silver';
    if (rank === 3) return 'rank-bronze';
    return '';
  };

  const getRankIcon = (rank: number) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `${rank}.`;
  };

  return (
    <div className="leaderboard-page">
      <div className="leaderboard-header">
        <h1>📊 Statistiques & Classement</h1>
        <p className="leaderboard-subtitle">Comparez vos performances avec les autres joueurs</p>
      </div>

      {/* Filtres de catégorie */}
      <div className="category-filters">
        <button
          className={`category-btn ${category === 'general' ? 'active' : ''}`}
          onClick={() => setCategory('general')}
        >
          🏆 Général
        </button>
        <button
          className={`category-btn ${category === 'construction' ? 'active' : ''}`}
          onClick={() => setCategory('construction')}
        >
          🏗️ Construction
        </button>
        <button
          className={`category-btn ${category === 'research' ? 'active' : ''}`}
          onClick={() => setCategory('research')}
        >
          🔬 Recherche
        </button>
        <button
          className={`category-btn ${category === 'military_xp' ? 'active' : ''}`}
          onClick={() => setCategory('military_xp')}
        >
          ⚔️ XP Militaire
        </button>
        <button
          className={`category-btn ${category === 'units_killed' ? 'active' : ''}`}
          onClick={() => setCategory('units_killed')}
        >
          💀 Unités Tuées
        </button>
        <button
          className={`category-btn ${category === 'units_lost' ? 'active' : ''}`}
          onClick={() => setCategory('units_lost')}
        >
          ☠️ Unités Perdues
        </button>
        <button
          className={`category-btn ${category === 'victories' ? 'active' : ''}`}
          onClick={() => setCategory('victories')}
        >
          🎖️ Victoires
        </button>
        <button
          className={`category-btn ${category === 'quests' ? 'active' : ''}`}
          onClick={() => setCategory('quests')}
        >
          🎯 Quêtes
        </button>
      </div>

      {/* Titre de la catégorie */}
      <div className="category-title">
        <h2>
          {getCategoryIcon()} {getCategoryTitle()}
        </h2>
      </div>

      {/* Tableau de classement */}
      {loading ? (
        <div className="loading">Chargement du classement...</div>
      ) : (
        <div className="leaderboard-table-container">
          <table className="leaderboard-table">
            <thead>
              <tr>
                <th className="col-rank">Rang</th>
                <th className="col-username">Joueur</th>
                <th className="col-score">Score</th>
                {category === 'general' && (
                  <>
                    <th className="col-detail">Construction</th>
                    <th className="col-detail">Recherche</th>
                    <th className="col-detail">Victoires</th>
                  </>
                )}
              </tr>
            </thead>
            <tbody>
              {leaderboard.map((player) => {
                const isCurrentUser = user?.id === player.player_id;
                return (
                  <tr
                    key={player.player_id}
                    className={`${getRankClass(player.rank)} ${isCurrentUser ? 'current-user' : ''}`}
                  >
                    <td className="col-rank">
                      <span className="rank-badge">{getRankIcon(player.rank)}</span>
                    </td>
                    <td className="col-username">
                      {player.username}
                      {isCurrentUser && <span className="you-badge">Vous</span>}
                    </td>
                    <td className="col-score">
                      <strong>{getCategoryValue(player).toLocaleString()}</strong>
                    </td>
                    {category === 'general' && (
                      <>
                        <td className="col-detail">{player.construction_points.toLocaleString()}</td>
                        <td className="col-detail">{player.research_points_invested.toLocaleString()}</td>
                        <td className="col-detail">{player.victories}</td>
                      </>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>

          {leaderboard.length === 0 && (
            <div className="no-data">Aucune donnée disponible</div>
          )}
        </div>
      )}
    </div>
  );
};

export default LeaderboardPage;
