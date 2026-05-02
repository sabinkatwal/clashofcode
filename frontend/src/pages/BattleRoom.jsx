import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import './BattleRoom.css';

export default function BattleRoom() {
  const { roomCode } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [room, setRoom] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchRoom = async () => {
      try {
        const res = await api.get(`/rooms/${roomCode}`);
        setRoom(res.data);
      } catch (err) {
        setError('Room not found or you are not a member.');
      } finally {
        setLoading(false);
      }
    };
    fetchRoom();
  }, [roomCode]);

  const copyCode = () => {
    navigator.clipboard.writeText(roomCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isHost = room?.host?.username === user?.username;

  if (loading) {
    return (
      <div className="battle-loading">
        <div className="loading-spinner"></div>
        <p>Connecting to room...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="battle-error-page">
        <div className="error-icon">⚠</div>
        <h2>{error}</h2>
        <Button onClick={() => navigate('/dashboard')} variant="secondary">
          Back to Dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="battle-room">
      <div className="battle-room-inner">
        {/* Header */}
        <div className="br-header">
          <div>
            <div className="br-label">BATTLE ROOM</div>
            <h1 className="br-code">{roomCode}</h1>
          </div>
          <div className="br-status-badge">
            <span className="status-dot"></span>
            {room?.status || 'waiting'}
          </div>
        </div>

        <div className="br-grid">
          {/* Players */}
          <Card>
            <h2 className="section-title">Players ({room?.players?.length || 0}/2)</h2>
            <div className="players-list">
              {room?.players?.map((player) => (
                <div className="player-row" key={player.username}>
                  <div className="player-info">
                    <div className="player-avatar">
                      {player.username.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="player-name">
                        {player.username}
                        {player.username === room?.host?.username && (
                          <span className="host-badge">HOST</span>
                        )}
                      </div>
                      <div className="player-status">{player.status}</div>
                    </div>
                  </div>
                  <div className={`player-ready player-ready-${player.status}`}>
                    {player.status === 'ready' ? '✓' : '...'}
                  </div>
                </div>
              ))}
              {(room?.players?.length || 0) < 2 && (
                <div className="player-row waiting-slot">
                  <div className="player-info">
                    <div className="player-avatar ghost">?</div>
                    <div>
                      <div className="player-name" style={{ color: 'var(--text-muted)' }}>
                        Waiting for challenger...
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card>

          {/* Room Info */}
          <Card>
            <h2 className="section-title">Room Info</h2>
            <div className="room-info-section">
              <div className="info-row">
                <span className="info-key">Room Code</span>
                <div className="info-code-row">
                  <code className="info-code">{roomCode}</code>
                  <button className="copy-btn" onClick={copyCode}>
                    {copied ? '✓ Copied' : 'Copy'}
                  </button>
                </div>
              </div>
              <div className="info-row">
                <span className="info-key">Host</span>
                <span className="info-val">{room?.host?.username}</span>
              </div>
              <div className="info-row">
                <span className="info-key">Status</span>
                <span className={`info-val status-${room?.status}`}>{room?.status}</span>
              </div>
            </div>

            <div className="br-actions">
              {isHost && room?.players?.length === 2 && (
                <Button fullWidth variant="primary" size="lg">
                  ⚡ START BATTLE
                </Button>
              )}
              {isHost && room?.players?.length < 2 && (
                <Button fullWidth variant="secondary" disabled>
                  Waiting for opponent...
                </Button>
              )}
              {!isHost && (
                <Button fullWidth variant="secondary">
                  Mark as Ready
                </Button>
              )}
              <Button fullWidth variant="ghost" onClick={() => navigate('/dashboard')}>
                Leave Room
              </Button>
            </div>
          </Card>
        </div>

        {/* Coming soon banner */}
        <div className="coming-soon-banner">
          <span className="cs-icon">🚧</span>
          <div>
            <strong>Real-time battles coming soon!</strong>
            <p>WebSocket integration is in progress. Stay tuned for live duels.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
