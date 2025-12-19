import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../hooks/useUser';
import { getResourceEmoji } from '../constants/resourceIcons';
import '../styles/QuestsPage.css';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button } from '@mui/material';

interface Quest {
  id: string;
  title: string;
  description: string;
  type: string;
  icon?: string;
  target: number;
  targets?: number[];  // Les 3 paliers [100, 200, 300]
  rewards?: Array<{    // Les 3 récompenses
    gold?: number;
    research_points?: number;
    diamonds?: number;
    quest_points?: number;
  }>;
  current_progress: number;
  reward_xp?: number;
  reward_stars?: number;
  is_completed: boolean;
  is_claimed: boolean;
  help_text?: string;  // Texte d'aide pour guider le joueur
}

interface UnclaimedReward {
  quest_id: string;
  quest_title?: string;
  quest_type?: string;  // 'daily' ou 'weekly'
  star_level?: number;  // Pour daily quests
  rewards: {
    gold?: number;
    research_points?: number;
    diamonds?: number;
    quest_points?: number;
  };
  awarded_at?: string;  // Pour daily quests
  expires_at?: string;  // Pour daily quests
}

interface PlayerStats {
  quest_points: number;
  level: number;
  current_threshold: number;
  next_threshold: number | null;
  points_in_current_level: number;
  points_needed_for_next_level: number;
  progress_percentage: number;
  is_max_level: boolean;
}

const QuestsPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useUser();
  const [activeTab, setActiveTab] = useState<'quests' | 'rewards'>('quests');
  const [dailyQuests, setDailyQuests] = useState<Quest[]>([]);
  const [weeklyQuests, setWeeklyQuests] = useState<Quest[]>([]);
  const [unclaimedRewards, setUnclaimedRewards] = useState<UnclaimedReward[]>([]);
  const [playerStats, setPlayerStats] = useState<PlayerStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [helpDialogOpen, setHelpDialogOpen] = useState(false);
  const [selectedQuest, setSelectedQuest] = useState<Quest | null>(null);

  useEffect(() => {
    const loadQuests = async () => {
      if (!user?.username) return;

      try {
        setLoading(true);
        
        // Charger les statistiques du joueur
        const statsResponse = await fetch(`/api/quests/player-stats?username=${user.username}`);
        if (statsResponse.ok) {
          const statsData = await statsResponse.json();
          setPlayerStats(statsData);
        }
        
        // Charger les quêtes quotidiennes
        const dailyResponse = await fetch(`/api/quests/daily?username=${user.username}`);
        if (dailyResponse.ok) {
          const dailyData = await dailyResponse.json();
          setDailyQuests(dailyData.quests || []);
        }

        // Charger les quêtes hebdomadaires
        const weeklyResponse = await fetch(`/api/quests/weekly?username=${user.username}`);
        if (weeklyResponse.ok) {
          const weeklyData = await weeklyResponse.json();
          setWeeklyQuests(weeklyData.quests || []);
        }

        // Charger les récompenses non réclamées
        const rewardsResponse = await fetch(`/api/quests/unclaimed?username=${user.username}`);
        if (rewardsResponse.ok) {
          const rewardsData = await rewardsResponse.json();
          setUnclaimedRewards(rewardsData.unclaimed_rewards || []);
        }

        setLoading(false);
      } catch (err) {
        console.error('Erreur lors du chargement des quêtes:', err);
        setError('Impossible de charger les quêtes');
        setLoading(false);
      }
    };

    loadQuests();
    
    // ❌ DÉSACTIVÉ : Rechargement automatique trop lourd (ralentit le jeu)
    // Le rechargement manuel via le bouton suffit
    /*
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        loadQuests();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
    */
  }, [user?.username]);

  const getProgressPercentage = (current: number, target: number) => {
    return Math.min(100, (current / target) * 100);
  };

  const getQuestIcon = (type: string) => {
    const icons: { [key: string]: string } = {
      'economic': '🏛️',
      'military': '⚔️',
      'research': '📚',
      'trade': '🚢',
      'building': '🏗️',
      'resource': '⛏️',
      'default': '🎯'
    };
    return icons[type] || icons['default'];
  };

  const getDaysUntilExpiry = (expiresAt: string): number => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diffTime = expiry.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return Math.max(0, diffDays);
  };

  // Grouper les récompenses quotidiennes par quest_id (ignorer les weekly)
  const groupedRewards = unclaimedRewards
    .filter(r => r.quest_type !== 'weekly')  // Seulement les daily
    .reduce((acc, reward) => {
      if (!acc[reward.quest_id]) {
        acc[reward.quest_id] = {
          quest_id: reward.quest_id,
          quest_title: reward.quest_title || '',
          expires_at: reward.expires_at || '',
          stars: []
        };
      }
      acc[reward.quest_id].stars.push({
        star_level: reward.star_level || 0,
        rewards: reward.rewards
      });
      return acc;
    }, {} as Record<string, { quest_id: string; quest_title: string; expires_at: string; stars: Array<{ star_level: number; rewards: any }> }>);

  const handleClaimWeeklyReward = async (questId: string) => {
    if (!user?.username) return;

    try {
      const response = await fetch('/api/quests/claim-weekly-reward', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username: user.username,
          quest_id: questId
        })
      });

      if (response.ok) {
        // Recharger les quêtes hebdomadaires pour afficher la suivante
        const weeklyResponse = await fetch(`/api/quests/weekly?username=${user.username}`);
        if (weeklyResponse.ok) {
          const weeklyData = await weeklyResponse.json();
          setWeeklyQuests(weeklyData.quests || []);
        }

        // Recharger les récompenses et stats
        const rewardsResponse = await fetch(`/api/quests/unclaimed?username=${user.username}`);
        if (rewardsResponse.ok) {
          const rewardsData = await rewardsResponse.json();
          setUnclaimedRewards(rewardsData.unclaimed_rewards || []);
        }

        const statsResponse = await fetch(`/api/quests/player-stats?username=${user.username}`);
        if (statsResponse.ok) {
          const statsData = await statsResponse.json();
          setPlayerStats(statsData);
        }
      }
    } catch (error) {
      console.error('Erreur lors de la réclamation:', error);
    }
  };

  const handleClaimAllStars = async (questId: string, starLevels: number[]) => {
    if (!user?.username) return;

    try {
      // Réclamer toutes les étoiles en série
      for (const starLevel of starLevels) {
        await fetch('/api/quests/claim-reward', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: user.username,
            quest_id: questId,
            star_level: starLevel
          })
        });
      }

      // Recharger les récompenses et stats
      const rewardsResponse = await fetch(`/api/quests/unclaimed?username=${user.username}`);
      if (rewardsResponse.ok) {
        const rewardsData = await rewardsResponse.json();
        setUnclaimedRewards(rewardsData.unclaimed_rewards || []);
      }
      
      // Recharger les stats pour mettre à jour les points de quête
      const statsResponse = await fetch(`/api/quests/player-stats?username=${user.username}`);
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setPlayerStats(statsData);
      }
    } catch (err) {
      console.error('Erreur lors de la réclamation:', err);
    }
  };

  return (
    <div className="quests-overlay" onClick={() => navigate(-1)}>
      <div className="quests-popup" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="quests-popup-header">
          <h2>📜 Journal des Quêtes</h2>
          <button className="close-button" onClick={() => navigate(-1)}>
            ×
          </button>
        </div>

        {/* Player Stats Bar */}
        {playerStats && (
          <div style={{
            background: 'linear-gradient(135deg, #f5e6d3 0%, #e8d5b7 100%)',
            border: '2px solid #8b6f47',
            borderRadius: '8px',
            padding: '8px 10px',
            marginBottom: '12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
            width: '100%',
            maxWidth: '100%',
            boxSizing: 'border-box'
          }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '4px',
              width: '100%'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '18px', fontWeight: 'bold', color: '#d4af37' }}>
                  🏆 Niv. {playerStats.level}
                </span>
                <span style={{ fontSize: '11px', color: '#8b7355' }}>
                  ({playerStats.quest_points} {getResourceEmoji('quest_points')} pts)
                </span>
              </div>
              {!playerStats.is_max_level && (
                <span style={{ fontSize: '11px', color: '#8b6f47', fontWeight: '600' }}>
                  +{playerStats.points_needed_for_next_level - playerStats.points_in_current_level} → niv. {playerStats.level + 1}
                </span>
              )}
            </div>
            
            {/* Barre de progression */}
            {!playerStats.is_max_level ? (
              <div style={{ 
                width: '100%', 
                boxSizing: 'border-box'
              }}>
                <div style={{
                  width: '100%',
                  height: '16px',
                  background: '#d4c5a0',
                  borderRadius: '8px',
                  overflow: 'hidden',
                  border: '2px solid #8b6f47',
                  position: 'relative',
                  boxSizing: 'border-box'
                }}>
                  <div style={{
                    width: `${playerStats.progress_percentage}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #d4af37 0%, #f4d03f 100%)',
                    transition: 'width 0.3s ease',
                    position: 'relative',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
                      animation: 'shimmer 2s infinite'
                    }} />
                  </div>
                  <span style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    fontSize: '10px',
                    fontWeight: 'bold',
                    color: '#3d2817',
                    textShadow: '0 0 3px rgba(255,255,255,0.8)',
                    whiteSpace: 'nowrap'
                  }}>
                    {playerStats.points_in_current_level} / {playerStats.points_needed_for_next_level} ({playerStats.progress_percentage.toFixed(0)}%)
                  </span>
                </div>
              </div>
            ) : (
              <div style={{
                textAlign: 'center',
                padding: '4px 6px',
                background: 'linear-gradient(90deg, #d4af37 0%, #f4d03f 100%)',
                borderRadius: '6px',
                width: '100%',
                boxSizing: 'border-box',
                border: '2px solid #8b6f47',
                fontWeight: 'bold',
                fontSize: '13px',
                color: '#3d2817'
              }}>
                🌟 NIVEAU MAX 🌟
              </div>
            )}
          </div>
        )}

        {/* Tabs */}
        <div style={{ display: 'flex', borderBottom: '2px solid #8b6f47', marginBottom: '20px' }}>
          <button
            onClick={() => setActiveTab('quests')}
            style={{
              flex: 1,
              padding: '12px',
              background: activeTab === 'quests' ? '#d4af37' : 'transparent',
              border: 'none',
              borderBottom: activeTab === 'quests' ? '3px solid #8b6f47' : 'none',
              color: activeTab === 'quests' ? '#3d2817' : '#8b7355',
              fontWeight: 'bold',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            📋 Quêtes
          </button>
          <button
            onClick={() => setActiveTab('rewards')}
            style={{
              flex: 1,
              padding: '12px',
              background: activeTab === 'rewards' ? '#d4af37' : 'transparent',
              border: 'none',
              borderBottom: activeTab === 'rewards' ? '3px solid #8b6f47' : 'none',
              color: activeTab === 'rewards' ? '#3d2817' : '#8b7355',
              fontWeight: 'bold',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            🎁 Récompenses ({unclaimedRewards.length})
          </button>
        </div>

        {/* Content */}
        <div className="quests-popup-content">
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <p>Chargement...</p>
            </div>
          ) : error ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#d32f2f' }}>
              <p>{error}</p>
            </div>
          ) : activeTab === 'rewards' ? (
            /* Onglet Récompenses */
            <div>
              <h3 style={{ marginBottom: '20px', color: '#d4af37' }}>🎁 Récompenses Disponibles</h3>
              {unclaimedRewards.length === 0 ? (
                <p style={{ textAlign: 'center', color: '#8b7355', padding: '40px' }}>
                  Aucune récompense à récupérer pour le moment
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {/* Récompenses hebdomadaires */}
                  {unclaimedRewards.filter(r => r.quest_type === 'weekly').map((reward, idx) => (
                    <div
                      key={reward.quest_id || `weekly-${idx}`}
                      style={{
                        background: 'linear-gradient(135deg, #e6d5f5 0%, #d5b7e8 100%)',
                        border: '2px solid #8b47a1',
                        borderRadius: '8px',
                        padding: '12px 16px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '14px', color: '#6a3d7f', marginBottom: '4px' }}>
                          ⭐ Quête Hebdomadaire
                        </div>
                        <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#3d1755', marginBottom: '8px' }}>
                          {reward.quest_id.replace(/_/g, ' ').replace(/week \d+ /, '')}
                        </div>
                        <div style={{ fontSize: '15px', color: '#8b47a1', fontWeight: '600' }}>
                          {reward.rewards.gold && `${getResourceEmoji('gold')}${reward.rewards.gold} `}
                          {reward.rewards.research_points && `${getResourceEmoji('research_points')}${reward.rewards.research_points} `}
                          {reward.rewards.diamonds && `${getResourceEmoji('diamonds')}${reward.rewards.diamonds} `}
                          {reward.rewards.quest_points && `${getResourceEmoji('quest_points')}${reward.rewards.quest_points}`}
                        </div>
                      </div>
                      <button
                        onClick={() => handleClaimWeeklyReward(reward.quest_id || '')}
                        style={{
                          padding: '8px 16px',
                          background: '#a855f7',
                          border: '2px solid #8b47a1',
                          borderRadius: '4px',
                          color: 'white',
                          fontWeight: 'bold',
                          cursor: 'pointer',
                          fontSize: '14px'
                        }}
                      >
                        Récupérer
                      </button>
                    </div>
                  ))}
                  
                  {/* Récompenses quotidiennes (étoiles) */}
                  {Object.values(groupedRewards).map((group) => {
                    // Calculer les récompenses totales
                    const totalRewards = group.stars.reduce((acc, star) => {
                      if (star.rewards.gold) acc.gold = (acc.gold || 0) + star.rewards.gold;
                      if (star.rewards.research_points) acc.research_points = (acc.research_points || 0) + star.rewards.research_points;
                      if (star.rewards.diamonds) acc.diamonds = (acc.diamonds || 0) + star.rewards.diamonds;
                      if (star.rewards.quest_points) acc.quest_points = (acc.quest_points || 0) + star.rewards.quest_points;
                      return acc;
                    }, {} as {gold?: number; research_points?: number; diamonds?: number; quest_points?: number});

                    // Formater les étoiles (⭐⭐⭐)
                    const sortedStars = group.stars.sort((a, b) => a.star_level - b.star_level);
                    const starsDisplay = '⭐'.repeat(sortedStars.length);

                    return (
                      <div
                        key={group.quest_id}
                        style={{
                          background: 'linear-gradient(135deg, #f5e6d3 0%, #e8d5b7 100%)',
                          border: '2px solid #8b6f47',
                          borderRadius: '8px',
                          padding: '12px 16px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center'
                        }}
                      >
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: '14px', color: '#8b7355', marginBottom: '4px' }}>
                            ⏰ Expire dans {getDaysUntilExpiry(group.expires_at)}j
                          </div>
                          <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#3d2817', marginBottom: '8px' }}>
                            {getQuestIcon('economic')} {group.quest_title} niveau 1
                          </div>
                          <div style={{ fontSize: '15px', color: '#8b6f47', fontWeight: '600' }}>
                            {starsDisplay} = {' '}
                            {totalRewards.gold && `${getResourceEmoji('gold')}${totalRewards.gold} `}
                            {totalRewards.research_points && `${getResourceEmoji('research_points')}${totalRewards.research_points} `}
                            {totalRewards.diamonds && `${getResourceEmoji('diamonds')}${totalRewards.diamonds} `}
                            {totalRewards.quest_points && `${getResourceEmoji('quest_points')}${totalRewards.quest_points}`}
                          </div>
                        </div>
                        <button
                          onClick={() => handleClaimAllStars(group.quest_id, group.stars.map(s => s.star_level))}
                          style={{
                            padding: '8px 16px',
                            background: '#d4af37',
                            border: '2px solid #8b6f47',
                            borderRadius: '4px',
                            color: '#3d2817',
                            fontWeight: 'bold',
                            cursor: 'pointer',
                            fontSize: '14px'
                          }}
                        >
                          Tout récupérer
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ) : (
            /* Onglet Quêtes */
            <>
              {/* Quêtes Quotidiennes */}
              <div className="quest-section">
                <div className="section-header">
                  <h3>☀️ Quêtes Quotidiennes</h3>
                  <span className="section-badge">Renouvellement : 24h</span>
                </div>
                <p className="section-description">
                  Complétez ces quêtes pour gagner des ressources et de l'expérience
                </p>
                
                <div className="quest-list">
                  {dailyQuests.length > 0 ? (
                    dailyQuests.map((quest) => (
                      <div key={quest.id} className={`quest-card ${quest.is_completed ? 'quest-completed' : ''}`}>
                        <div className="quest-icon">{getQuestIcon(quest.type)}</div>
                        <div className="quest-details">
                          <h4>{quest.title}</h4>
                          <p className="quest-objective">{quest.description}</p>
                          <div className="quest-progress">
                            <div className="progress-bar">
                              <div 
                                className="progress-fill" 
                                style={{ width: `${getProgressPercentage(quest.current_progress, quest.targets ? quest.targets[2] : quest.target)}%` }}
                              ></div>
                            </div>
                            <span className="progress-text">
                              {quest.current_progress} / {quest.targets ? quest.targets[2] : quest.target}
                            </span>
                          </div>
                          
                          {/* Affichage des 3 paliers - COMPACT sur 1 ligne */}
                          {quest.targets && quest.rewards && (
                            <div style={{ 
                              marginTop: '8px', 
                              fontSize: '11px', 
                              borderTop: '1px solid #d4c5a0', 
                              paddingTop: '6px',
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              width: '100%'
                            }}>
                              {quest.targets.map((target: number, index: number) => {
                                const reward = (quest.rewards && quest.rewards[index]) || {};
                                const stars = '⭐'.repeat(index + 1);
                                const isAchieved = quest.current_progress >= target;
                                return (
                                  <span 
                                    key={index} 
                                    style={{ 
                                      opacity: isAchieved ? 1 : 0.5,
                                      fontWeight: isAchieved ? 'bold' : 'normal',
                                      color: isAchieved ? '#d4af37' : '#8b7355',
                                      whiteSpace: 'nowrap',
                                      textAlign: index === 0 ? 'left' : index === 1 ? 'center' : 'right',
                                      flex: 1
                                    }}
                                  >
                                    {stars} = {target}
                                    {reward.gold ? `💰${reward.gold}` : ''}
                                    {reward.research_points ? ` 📚${reward.research_points}` : ''}
                                    {reward.diamonds ? ` 💎${reward.diamonds}` : ''}
                                    {reward.quest_points ? ` ${getResourceEmoji('quest_points')}${reward.quest_points}` : ''}
                                  </span>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <p style={{ textAlign: 'center', color: '#5d4e37' }}>
                      Aucune quête quotidienne disponible
                    </p>
                  )}
                </div>
              </div>

              {/* Quêtes Hebdomadaires */}
              <div className="quest-section">
                <div className="section-header">
                  <h3>⭐ Quêtes Hebdomadaires</h3>
                  <span className="section-badge">Renouvellement : 7j</span>
                </div>
                <p className="section-description">
                  Défis majeurs avec des récompenses exceptionnelles
                </p>
                
                <div className="quest-list">
                  {weeklyQuests.length > 0 ? (
                    weeklyQuests.map((quest) => (
                      <div 
                        key={quest.id} 
                        className={`quest-card quest-card-weekly ${quest.is_completed ? 'quest-completed' : ''}`}
                        onClick={() => {
                          if (quest.is_completed && !quest.is_claimed) {
                            handleClaimWeeklyReward(quest.id);
                          }
                        }}
                        style={{
                          cursor: quest.is_completed && !quest.is_claimed ? 'pointer' : 'default',
                          transition: 'all 0.2s ease',
                        }}
                        onMouseEnter={(e) => {
                          if (quest.is_completed && !quest.is_claimed) {
                            e.currentTarget.style.transform = 'scale(1.02)';
                            e.currentTarget.style.boxShadow = '0 4px 12px rgba(212, 175, 55, 0.5)';
                          }
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = 'scale(1)';
                          e.currentTarget.style.boxShadow = '';
                        }}
                        title={quest.is_completed && !quest.is_claimed ? 'Cliquez pour récupérer la récompense !' : ''}
                      >
                        <div className="quest-icon">{getQuestIcon(quest.type)}</div>
                        <div className="quest-details">
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <h4>{quest.title}</h4>
                            {quest.help_text && (
                              <button 
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setSelectedQuest(quest);
                                  setHelpDialogOpen(true);
                                }}
                                style={{
                                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                  border: '2px solid rgba(255, 255, 255, 0.3)',
                                  borderRadius: '16px',
                                  padding: '4px 10px',
                                  color: 'white',
                                  fontSize: '12px',
                                  cursor: 'pointer',
                                  fontWeight: '600',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  boxShadow: '0 2px 8px rgba(102, 126, 234, 0.3)',
                                  transition: 'all 0.2s ease',
                                }}
                                onMouseEnter={(e) => {
                                  e.currentTarget.style.transform = 'scale(1.05)';
                                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.5)';
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.transform = 'scale(1)';
                                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(102, 126, 234, 0.3)';
                                }}
                                title="Aide pour cette quête"
                              >
                                info ?
                              </button>
                            )}
                          </div>
                          <p className="quest-objective">{quest.description}</p>
                          <div className="quest-progress">
                            <div className="progress-bar">
                              <div 
                                className="progress-fill" 
                                style={{ width: `${getProgressPercentage(quest.current_progress, quest.target)}%` }}
                              ></div>
                            </div>
                            <span className="progress-text">
                              {quest.current_progress} / {quest.target}
                            </span>
                          </div>
                        </div>
                        <div className="quest-reward">
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            {quest.is_completed && <span className="reward-icon">🏆</span>}
                            <span className="reward-text">+{quest.reward_xp} XP</span>
                          </div>
                          {quest.reward_stars && quest.reward_stars > 0 && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '4px' }}>
                              <span style={{ fontSize: '18px' }}>⭐</span>
                              <span className="reward-text">+{quest.reward_stars}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <p style={{ textAlign: 'center', color: '#5d4e37' }}>
                      À venir prochainement...
                    </p>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Dialog d'aide esthétique */}
      <Dialog 
        open={helpDialogOpen} 
        onClose={() => setHelpDialogOpen(false)}
        sx={{
          zIndex: 9999999,
          '& .MuiBackdrop-root': {
            zIndex: 9999999,
          },
          '& .MuiDialog-container': {
            zIndex: 9999999,
          },
          '& .MuiDialog-paper': {
            zIndex: 9999999,
          }
        }}
        BackdropProps={{
          style: {
            zIndex: 9999999,
          }
        }}
        PaperProps={{
          style: {
            borderRadius: '16px',
            background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.3)',
            border: '3px solid #8b6f47',
            maxWidth: '500px',
            padding: '8px',
            zIndex: 9999999,
            position: 'relative',
          }
        }}
      >
        <DialogTitle 
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            fontWeight: 'bold',
            fontSize: '20px',
            borderRadius: '12px 12px 0 0',
            padding: '16px 24px',
            textAlign: 'center',
            borderBottom: '2px solid rgba(255, 255, 255, 0.3)',
          }}
        >
          📜 {selectedQuest?.title}
        </DialogTitle>
        <DialogContent 
          style={{
            padding: '24px',
            fontSize: '15px',
            lineHeight: '1.6',
            color: '#2c3e50',
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            borderRadius: '0 0 12px 12px',
          }}
        >
          <div style={{ 
            marginTop: '8px',
            padding: '16px',
            background: 'linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%)',
            borderRadius: '8px',
            border: '2px solid #d63031',
            boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.1)',
          }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'flex-start',
              gap: '12px'
            }}>
              <span style={{ fontSize: '24px', flexShrink: 0 }}>💡</span>
              <p style={{ margin: 0, fontWeight: '500', color: '#2d3436' }}>
                {selectedQuest?.help_text}
              </p>
            </div>
          </div>
        </DialogContent>
        <DialogActions 
          style={{
            padding: '16px 24px',
            background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
            borderRadius: '0 0 12px 12px',
            justifyContent: 'center',
          }}
        >
          <Button 
            onClick={() => setHelpDialogOpen(false)}
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              fontWeight: 'bold',
              padding: '10px 32px',
              borderRadius: '24px',
              textTransform: 'none',
              fontSize: '14px',
              boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)',
              border: '2px solid rgba(255, 255, 255, 0.3)',
            }}
          >
            Compris !
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default QuestsPage;
