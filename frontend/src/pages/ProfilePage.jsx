import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/Toast';
import Avatar from '../components/Avatar';
import TopicBadge from '../components/TopicBadge';
import { formatReputation } from '../utils/helpers';

export default function ProfilePage() {
  const { id } = useParams();
  const { user: me, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [following, setFollowing] = useState(false);

  const isMe = me?.user_id === id;

  useEffect(() => {
    api.users.profile(id)
      .then(setProfile)
      .catch(e => toast.error(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleFollow = async () => {
    if (!isAuthenticated) { navigate('/login'); return; }
    try {
      await api.users.follow(id);
      setFollowing(true);
      toast.success(`Now following ${profile.username}`);
    } catch (e) {
      toast.error(e.message);
    }
  };

  if (loading) return <div className="page-loader"><div className="spinner-lg" /></div>;

  if (!profile) return (
    <div className="empty-state">
      <div className="empty-state-icon">👤</div>
      <h3>User not found</h3>
    </div>
  );

  const reputationColor = profile.reputation > 5
    ? 'var(--color-upvote)'
    : profile.reputation > 2
    ? 'var(--color-warning)'
    : 'var(--text-muted)';

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

      {/* Profile Header */}
      <div className="card" style={{ padding: '32px' }}>
        <div style={{ display: 'flex', gap: '24px', alignItems: 'flex-start', flexWrap: 'wrap' }}>
          <Avatar username={profile.username} size={80} />
          <div style={{ flex: 1 }}>
            <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, marginBottom: '4px' }}>
              {profile.username}
            </h1>
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)', marginBottom: '16px' }}>
              {profile.email}
            </p>

            {!isMe && (
              <button
                className={`btn ${following ? 'btn-ghost' : 'btn-primary'}`}
                onClick={handleFollow}
                disabled={following}
              >
                {following ? '✓ Following' : '+ Follow'}
              </button>
            )}
          </div>
        </div>

        {/* Stats Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '16px',
          marginTop: '28px',
          paddingTop: '24px',
          borderTop: '1px solid var(--border-subtle)',
        }}>
          {[
            {
              label: 'Reputation',
              value: formatReputation(profile.reputation),
              color: reputationColor,
              icon: '⭐',
            },
            { label: 'Following', value: profile.following_count, icon: '👥' },
            { label: 'Followers', value: profile.followers_count, icon: '🌟' },
          ].map(stat => (
            <div
              key={stat.label}
              style={{
                background: 'rgba(255,255,255,0.03)',
                borderRadius: '12px',
                padding: '16px',
                textAlign: 'center',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ fontSize: '22px', marginBottom: '6px' }}>{stat.icon}</div>
              <div style={{
                fontSize: 'var(--font-size-2xl)',
                fontWeight: 800,
                color: stat.color || 'var(--text-primary)',
                lineHeight: 1,
                marginBottom: '4px',
              }}>
                {stat.value}
              </div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Reputation Badge */}
      <div className="card" style={{ padding: '20px 24px' }}>
        <h3 style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
          Reputation Score
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ flex: 1, background: 'var(--border-subtle)', borderRadius: '9999px', height: '8px', overflow: 'hidden' }}>
            <div style={{
              width: `${Math.min(100, (profile.reputation / 10) * 100)}%`,
              height: '100%',
              background: 'var(--accent-gradient)',
              borderRadius: '9999px',
              transition: 'width 0.6s ease',
            }} />
          </div>
          <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 700, color: reputationColor }}>
            {formatReputation(profile.reputation)} / 10
          </span>
        </div>
        <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginTop: '8px' }}>
          Reputation increases with upvotes (+0.10) and decreases with downvotes (-0.05)
        </p>
      </div>

      {/* Followed Topics */}
      {profile.followed_topics?.length > 0 && (
        <div className="card" style={{ padding: '20px 24px' }}>
          <h3 style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
            Followed Topics ({profile.followed_topics.length})
          </h3>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {profile.followed_topics.map(tid => (
              <TopicBadge key={tid} topicId={tid} />
            ))}
          </div>
        </div>
      )}

      {/* Member Since */}
      <div className="card" style={{ padding: '16px 24px' }}>
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)' }}>
          🗓 Member since {new Date(profile.created_at * 1000).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
        </p>
      </div>
    </div>
  );
}
