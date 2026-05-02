import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Home.css';

export default function Home() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="home">
      {/* Hero */}
      <section className="hero">
        <div className="hero-grid-bg" aria-hidden="true"></div>
        <div className="hero-content">
          <div className="hero-badge">⚡ LIVE BETA</div>
          <h1 className="hero-title">
            CODE.<br />
            <span className="hero-title-accent">BATTLE.</span><br />
            CONQUER.
          </h1>
          <p className="hero-subtitle">
            Real-time multiplayer coding duels. Race to solve challenges faster than your opponent.
            Climb the rankings. Prove your skills.
          </p>
          <div className="hero-cta">
            {isAuthenticated ? (
              <Link to="/dashboard" className="cta-btn cta-btn-primary">Enter Arena →</Link>
            ) : (
              <>
                <Link to="/register" className="cta-btn cta-btn-primary">Start Battling →</Link>
                <Link to="/login" className="cta-btn cta-btn-ghost">Sign In</Link>
              </>
            )}
          </div>
        </div>

        <div className="hero-visual">
          <div className="code-window">
            <div className="code-window-bar">
              <span className="dot dot-red"></span>
              <span className="dot dot-yellow"></span>
              <span className="dot dot-green"></span>
              <span className="window-title">battle.js</span>
            </div>
            <pre className="code-content"><code>{`function twoSum(nums, target) {
  <span class="c-purple">const</span> map = <span class="c-blue">new</span> Map();
  
  <span class="c-purple">for</span> (<span class="c-purple">let</span> i = 0; i < nums.length; i++) {
    <span class="c-purple">const</span> complement = target - nums[i];
    
    <span class="c-purple">if</span> (map.<span class="c-green">has</span>(complement)) {
      <span class="c-purple">return</span> [map.<span class="c-green">get</span>(complement), i];
    }
    map.<span class="c-green">set</span>(nums[i], i);
  }
}

<span class="c-comment">// ✓ Solved in 00:42</span>`}</code></pre>
          </div>
          <div className="hero-badge-float badge-player1">⚡ Player 1 — 00:42</div>
          <div className="hero-badge-float badge-player2">⏳ Player 2 — solving...</div>
        </div>
      </section>

      {/* Features */}
      <section className="features">
        <div className="features-grid">
          {[
            { icon: '⚔', title: 'Real-Time Battles', desc: 'Go head-to-head with devs worldwide. Speed and accuracy are everything.' },
            { icon: '🏆', title: 'Global Leaderboard', desc: 'Earn points, climb ranks, and cement your place at the top.' },
            { icon: '🔐', title: 'Secure Platform', desc: 'JWT-based auth with protected rooms and fair play enforcement.' },
            { icon: '🚀', title: 'Instant Rooms', desc: 'Create or join a battle room in seconds with a unique room code.' },
          ].map(({ icon, title, desc }) => (
            <div className="feature-card" key={title}>
              <div className="feature-icon">{icon}</div>
              <h3 className="feature-title">{title}</h3>
              <p className="feature-desc">{desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
