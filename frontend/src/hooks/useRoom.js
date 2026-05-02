import { useState, useEffect } from 'react';
import api from '../api/axios';

/**
 * Custom hook to fetch and manage room state.
 * @param {string} roomCode
 */
export function useRoom(roomCode) {
  const [room, setRoom] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchRoom = async () => {
    if (!roomCode) return;
    setLoading(true);
    try {
      const res = await api.get(`/rooms/${roomCode}`);
      setRoom(res.data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load room.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoom();
  }, [roomCode]);

  return { room, loading, error, refetch: fetchRoom };
}
