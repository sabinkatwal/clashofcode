import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';
import Card from '../components/ui/Card';
import './Profile.css';

export default function Profile() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await api.get('/user/stats');
        setStats(res.data);
      } catch {
        // Stats not available yet
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  return (
    <div className="profile-page">
      <div className="profile-inner">
        {/* Profile Header */}
        <Card glow className="profile-header-card">
          <div className="profile-avatar">
            {user?.username?.charAt(0).toUpperCase()}
          </div>
          <div className="profile-info">
            <h1 className="profile-username">{user?.username}</h1>
            <p className="profile-email">{user?.email}</p>
            <div className="profile-badges">
              <span className="profile-badge">⚡ Gladiator</span>
              <span className="profile-badge">🔥 Active</span>
            </div>
          </div>
          <div className="profile-rank">
            <div className="rank-num">#—</div>
            <div className="rank-lbl">Global Rank</div>
          </div>
        </Card>

        {/* Stats */}
        <div className="profile-stats">
          {[
            { label: 'Games Played', value: stats?.gamesPlayed ?? '—', icon: '🎮' },
            { label: 'Wins', value: stats?.wins ?? '—', icon: '🏆', color: 'success' },
            { label: 'Losses', value: stats?.losses ?? '—', icon: '💀', color: 'danger' },
            { label: 'Win Rate', value: stats?.winRate ? `${stats.winRate}%` : '—%', icon: '📊' },
            { label: 'Avg. Time', value: stats?.avgTime ?? '—', icon: '⏱' },
            { label: 'Best Time', value: stats?.bestTime ?? '—', icon: '⚡', color: 'accent' },
          ].map(({ label, value, icon, color }) => (
            <Card key={label} className={`profile-stat ${color ? `pstat-${color}` : ''}`}>
              <span className="pstat-icon">{icon}</span>
              <div className="pstat-value">{loading ? '...' : value}</div>
              <div className="pstat-label">{label}</div>
            </Card>
          ))}
        </div>

        {/* Recent Battles */}
        <Card>
          <h2 className="section-title">Battle History</h2>
          <div className="empty-state">
            <span>🥊</span>
            <p>No battles recorded yet.</p>
          </div>
        </Card>
      </div>
    </div>
  );
}
