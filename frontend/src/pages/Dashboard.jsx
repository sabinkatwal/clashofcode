import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import Card from '../components/ui/Card';
import './Dashboard.css';

export default function Dashboard() {
  const { user } = useAuth();

  return (
    <div className="dashboard">
      <div className="dashboard-inner">
        {/* Header */}
        <div className="dash-header">
          <div>
            <h1 className="dash-title">
              Welcome, <span className="dash-username">{user?.username}</span>
            </h1>
            <p className="dash-sub">Ready to battle? Pick your weapon.</p>
          </div>
          <div className="dash-rank-badge">
            <span className="rank-label">RANK</span>
            <span className="rank-value">#—</span>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="quick-actions">
          <Link to="/create-room" className="action-card action-primary">
            <div className="action-icon">⚔</div>
            <div>
              <div className="action-title">Create Room</div>
              <div className="action-desc">Host a new battle and invite challengers</div>
            </div>
            <span className="action-arrow">→</span>
          </Link>

          <Link to="/join-room" className="action-card action-secondary">
            <div className="action-icon">🚪</div>
            <div>
              <div className="action-title">Join Room</div>
              <div className="action-desc">Enter a room code to join a battle</div>
            </div>
            <span className="action-arrow">→</span>
          </Link>
        </div>

        {/* Stats Grid */}
        <div className="stats-grid">
          {[
            { label: 'Games Played', value: '—', icon: '🎮' },
            { label: 'Wins', value: '—', icon: '🏆', color: 'success' },
            { label: 'Losses', value: '—', icon: '💀', color: 'danger' },
            { label: 'Win Rate', value: '—%', icon: '📈' },
          ].map(({ label, value, icon, color }) => (
            <Card key={label} className={`stat-card ${color ? `stat-${color}` : ''}`}>
              <div className="stat-icon">{icon}</div>
              <div className="stat-value">{value}</div>
              <div className="stat-label">{label}</div>
            </Card>
          ))}
        </div>

        {/* Recent Activity */}
        <Card>
          <h2 className="section-title">Recent Battles</h2>
          <div className="empty-state">
            <span className="empty-icon">🥊</span>
            <p>No battles yet. Start your first duel!</p>
            <Link to="/create-room" className="empty-cta">Create a Room →</Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
