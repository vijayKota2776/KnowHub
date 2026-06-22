import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Avatar from './Avatar';

export default function Navbar({ onSearch }) {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [menuOpen, setMenuOpen] = useState(false);

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <nav style={{
      position: 'sticky',
      top: 0,
      zIndex: 100,
      height: 'var(--navbar-height)',
      background: 'rgba(10, 14, 26, 0.9)',
      backdropFilter: 'blur(20px)',
      borderBottom: '1px solid var(--border-subtle)',
      display: 'flex',
      alignItems: 'center',
      padding: '0 24px',
      gap: '16px',
    }}>
      {/* Logo */}
      <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
        <div style={{
          width: 32,
          height: 32,
          background: 'var(--accent-gradient)',
          borderRadius: '10px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '16px',
          fontWeight: 800,
          color: 'white',
          boxShadow: '0 0 16px rgba(99,102,241,0.5)',
        }}>
          K
        </div>
        <span style={{ fontSize: '18px', fontWeight: 800, background: 'var(--accent-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          KnowHub
        </span>
      </Link>

      {/* Search Bar */}
      <form onSubmit={handleSearch} style={{ flex: 1, maxWidth: '480px', margin: '0 auto' }}>
        <div style={{ position: 'relative' }}>
          <span style={{
            position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)',
            color: 'var(--text-muted)', fontSize: '16px', pointerEvents: 'none',
          }}>🔍</span>
          <input
            className="input"
            style={{ paddingLeft: '40px', height: '40px', fontSize: '14px' }}
            placeholder="Search questions…"
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
        </div>
      </form>

      {/* Right Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginLeft: 'auto', flexShrink: 0 }}>
        {isAuthenticated ? (
          <>
            <button
              className="btn btn-primary btn-sm"
              onClick={() => navigate('/ask')}
            >
              + Ask
            </button>
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setMenuOpen(v => !v)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
              >
                <Avatar username={user?.username} size={36} />
              </button>

              {menuOpen && (
                <div style={{
                  position: 'absolute', top: '48px', right: 0,
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-default)',
                  borderRadius: '12px',
                  minWidth: '200px',
                  overflow: 'hidden',
                  boxShadow: 'var(--shadow-lg)',
                  zIndex: 200,
                }} onClick={() => setMenuOpen(false)}>
                  <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)', color: 'var(--text-primary)' }}>{user?.username}</div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>Rep: {Number(user?.reputation || 1).toFixed(1)}</div>
                  </div>
                  <div style={{ padding: '6px' }}>
                    <button
                      onClick={() => navigate(`/profile/${user?.user_id}`)}
                      className="btn btn-ghost btn-sm btn-full"
                      style={{ justifyContent: 'flex-start' }}
                    >
                      👤 My Profile
                    </button>
                    <button
                      onClick={() => navigate('/topics')}
                      className="btn btn-ghost btn-sm btn-full"
                      style={{ justifyContent: 'flex-start' }}
                    >
                      🏷️ Browse Topics
                    </button>
                    <hr style={{ border: 'none', borderTop: '1px solid var(--border-subtle)', margin: '6px 0' }} />
                    <button
                      onClick={logout}
                      className="btn btn-danger btn-sm btn-full"
                      style={{ justifyContent: 'flex-start' }}
                    >
                      ↪ Sign Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/login')}>Sign In</button>
            <button className="btn btn-primary btn-sm" onClick={() => navigate('/login?tab=register')}>Sign Up</button>
          </>
        )}
      </div>
    </nav>
  );
}
