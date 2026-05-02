import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import './RoomForms.css';

export default function CreateRoom() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCreate = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/rooms/create');
      const { roomCode } = res.data;
      navigate(`/battle-room/${roomCode}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create room. Try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="room-page">
      <Card className="room-card">
        <div className="room-icon">⚔</div>
        <h1 className="room-title">Create Battle Room</h1>
        <p className="room-sub">
          A unique room code will be generated. Share it with your challenger to start the duel.
        </p>

        <div className="room-info-list">
          <div className="room-info-item">
            <span className="info-dot">●</span>
            <span>You become the room host</span>
          </div>
          <div className="room-info-item">
            <span className="info-dot">●</span>
            <span>Share the 6-character room code</span>
          </div>
          <div className="room-info-item">
            <span className="info-dot">●</span>
            <span>Battle starts when both players are ready</span>
          </div>
        </div>

        {error && <div className="room-error">{error}</div>}

        <Button onClick={handleCreate} loading={loading} fullWidth size="lg">
          GENERATE ROOM
        </Button>
      </Card>
    </div>
  );
}
