import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Card from '../components/ui/Card';
import './RoomForms.css';

export default function JoinRoom() {
  const navigate = useNavigate();
  const [roomCode, setRoomCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleJoin = async (e) => {
    e.preventDefault();
    if (!roomCode.trim()) {
      setError('Please enter a room code.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await api.post('/rooms/join', { roomCode: roomCode.trim().toUpperCase() });
      navigate(`/battle-room/${roomCode.trim().toUpperCase()}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Room not found or is full.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="room-page">
      <Card className="room-card">
        <div className="room-icon">🚪</div>
        <h1 className="room-title">Join Battle Room</h1>
        <p className="room-sub">
          Enter the 6-character room code shared by the host to join the battle.
        </p>

        {error && <div className="room-error">{error}</div>}

        <form onSubmit={handleJoin} className="room-form">
          <Input
            label="Room Code"
            id="roomCode"
            placeholder="ABC123"
            value={roomCode}
            onChange={(e) => {
              setRoomCode(e.target.value.toUpperCase().slice(0, 6));
              setError('');
            }}
            style={{ textTransform: 'uppercase', letterSpacing: '0.2em', fontSize: '1.1rem', textAlign: 'center' }}
            required
          />
          <Button type="submit" loading={loading} fullWidth size="lg">
            JOIN ROOM
          </Button>
        </form>
      </Card>
    </div>
  );
}
