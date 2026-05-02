import { useEffect, useState } from 'react';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import Card from '../components/ui/Card';
import './Leaderboard.css';

export default function Leaderboard() {
  const { user } = useAuth();
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        const res = await api.get('/leaderboard');
        setPlayers(res.data);
      } catch {
        setPlayers([]);
      } finally {
        setLoading(false);
      }
    };
    fetchLeaderboard();
  }, []);

  const medals = ['🥇', '🥈', '🥉'];

  return (
    <div className="leaderboard-page">
      <div className="leaderboard-inner">
        <div className="lb-header">
          <h1 className="lb-title">🏆 Global Rankings</h1>
          <p className="lb-sub">Top coders on the battle arena</p>
        </div>

        <Card>
          {loading ? (
            <div className="lb-loading">Loading rankings...</div>
          ) : players.length === 0 ? (
            <div className="lb-empty">
              <span>🏁</span>
              <p>No rankings yet. Be the first to battle!</p>
            </div>
          ) : (
            <div className="lb-table">
              <div className="lb-table-header">
                <span>RANK</span>
                <span>PLAYER</span>
                <span>WINS</span>
                <span>GAMES</span>
                <span>WIN RATE</span>
              </div>
              {players.map((player, idx) => (
                <div
                  className={`lb-row ${player.username === user?.username ? 'lb-row-me' : ''} ${idx < 3 ? `lb-top-${idx + 1}` : ''}`}
                  key={player.username}
                >
                  <span className="lb-rank">
                    {idx < 3 ? medals[idx] : `#${idx + 1}`}
                  </span>
                  <span className="lb-name">
                    {player.username}
                    {player.username === user?.username && <span className="you-tag">YOU</span>}
                  </span>
                  <span className="lb-wins">{player.wins}</span>
                  <span className="lb-games">{player.gamesPlayed}</span>
                  <span className="lb-rate">{player.winRate}%</span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
