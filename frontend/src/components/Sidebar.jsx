import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from './Toast';
import TopicBadge from './TopicBadge';

export default function Sidebar() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const [topics, setTopics] = useState([]);
  const [recommended, setRecommended] = useState([]);

  useEffect(() => {
    api.topics.list().then(d => setTopics(d.topics || [])).catch(() => {});
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      api.recommendations.topics()
        .then(d => setRecommended(d.recommended_topics || []))
        .catch(() => {});
    }
  }, [isAuthenticated]);

  const navLinks = [
    { icon: '🏠', label: 'Home', path: '/' },
    { icon: '🔍', label: 'Search', path: '/search' },
    { icon: '🏷️', label: 'Topics', path: '/topics' },
  ];

  return (
    <aside style={{
      width: 'var(--sidebar-width)',
      flexShrink: 0,
      display: 'flex',
      flexDirection: 'column',
      gap: '24px',
      paddingTop: '24px',
    }}>
      {/* Nav Links */}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {navLinks.map(l => (
          <button
            key={l.path}
            onClick={() => navigate(l.path)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '10px 14px',
              borderRadius: '10px',
              border: 'none',
              cursor: 'pointer',
              background: location.pathname === l.path
                ? 'var(--accent-gradient-subtle)'
                : 'transparent',
              color: location.pathname === l.path ? 'var(--text-accent)' : 'var(--text-secondary)',
              fontFamily: 'var(--font-family)',
              fontSize: 'var(--font-size-sm)',
              fontWeight: location.pathname === l.path ? 600 : 400,
              transition: 'all 0.2s',
              textAlign: 'left',
            }}
          >
            <span style={{ fontSize: '18px' }}>{l.icon}</span>
            {l.label}
          </button>
        ))}
      </nav>

      {/* Popular Topics */}
      <div>
        <h3 style={{
          fontSize: 'var(--font-size-xs)',
          fontWeight: 700,
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          marginBottom: '12px',
          padding: '0 4px',
        }}>
          Popular Topics
        </h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {topics.slice(0, 8).map(t => (
            <TopicBadge
              key={t.topic_id}
              topicId={t.topic_id}
              onClick={() => navigate(`/search?q=${encodeURIComponent(t.name)}`)}
            />
          ))}
          {topics.length > 8 && (
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => navigate('/topics')}
              style={{ fontSize: '11px' }}
            >
              +{topics.length - 8} more
            </button>
          )}
        </div>
      </div>

      {/* Recommended Topics */}
      {isAuthenticated && recommended.length > 0 && (
        <div>
          <h3 style={{
            fontSize: 'var(--font-size-xs)',
            fontWeight: 700,
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            marginBottom: '12px',
            padding: '0 4px',
          }}>
            ✨ Recommended
          </h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {recommended.map(tid => (
              <TopicBadge
                key={tid}
                topicId={tid}
                onClick={() => navigate('/topics')}
              />
            ))}
          </div>
        </div>
      )}

      {/* Divider + Ask CTA */}
      {isAuthenticated && (
        <div style={{
          padding: '16px',
          background: 'var(--accent-gradient-subtle)',
          border: '1px solid var(--border-accent)',
          borderRadius: '12px',
        }}>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', marginBottom: '10px', lineHeight: 1.5 }}>
            Have a question? Share your knowledge with the community.
          </p>
          <button
            className="btn btn-primary btn-sm btn-full"
            onClick={() => navigate('/ask')}
          >
            + Ask a Question
          </button>
        </div>
      )}
    </aside>
  );
}
