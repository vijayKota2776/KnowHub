import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/Toast';
import TopicBadge from '../components/TopicBadge';
import { getTopicColors } from '../utils/helpers';

export default function TopicsPage() {
  const { isAuthenticated } = useAuth();
  const toast = useToast();
  const [topics, setTopics] = useState([]);
  const [following, setFollowing] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [newTopic, setNewTopic] = useState({ topic_id: '', name: '', description: '' });
  const [creating, setCreating] = useState(false);
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => {
    api.topics.list()
      .then(d => setTopics(d.topics || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleFollow = async (topicId) => {
    if (!isAuthenticated) { toast.error('Sign in to follow topics'); return; }
    try {
      await api.topics.follow(topicId);
      setFollowing(prev => new Set([...prev, topicId]));
      toast.success(`Following ${topicId}!`);
    } catch (e) {
      toast.error(e.message);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newTopic.topic_id || !newTopic.name) return;
    setCreating(true);
    try {
      const t = await api.topics.create(newTopic);
      setTopics(prev => [...prev, t]);
      setNewTopic({ topic_id: '', name: '', description: '' });
      setShowCreate(false);
      toast.success(`Topic "${t.name}" created!`);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setCreating(false);
    }
  };

  const filtered = topics.filter(t =>
    t.name.toLowerCase().includes(search.toLowerCase()) ||
    t.topic_id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, marginBottom: '6px' }}>
            Browse Topics
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>
            {topics.length} topics · Follow topics to personalize your feed
          </p>
        </div>
        {isAuthenticated && (
          <button className="btn btn-primary" onClick={() => setShowCreate(v => !v)}>
            {showCreate ? '✕ Cancel' : '+ New Topic'}
          </button>
        )}
      </div>

      {/* Create Topic Form */}
      {showCreate && (
        <div className="card" style={{ padding: '24px', marginBottom: '24px' }}>
          <h3 style={{ fontSize: 'var(--font-size-base)', fontWeight: 600, marginBottom: '16px', color: 'var(--text-secondary)' }}>
            Create a New Topic
          </h3>
          <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Topic ID (slug)</label>
                <input
                  className="input"
                  placeholder="e.g. python"
                  value={newTopic.topic_id}
                  onChange={e => setNewTopic(f => ({ ...f, topic_id: e.target.value.toLowerCase().replace(/\s+/g, '-') }))}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Display Name</label>
                <input
                  className="input"
                  placeholder="e.g. Python"
                  value={newTopic.name}
                  onChange={e => setNewTopic(f => ({ ...f, name: e.target.value }))}
                  required
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Description</label>
              <input
                className="input"
                placeholder="Brief description of this topic"
                value={newTopic.description}
                onChange={e => setNewTopic(f => ({ ...f, description: e.target.value }))}
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={creating} style={{ alignSelf: 'flex-start' }}>
              {creating ? <><span className="spinner" /> Creating…</> : '✓ Create Topic'}
            </button>
          </form>
        </div>
      )}

      {/* Search Topics */}
      <div style={{ marginBottom: '20px' }}>
        <input
          className="input"
          placeholder="Filter topics…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ maxWidth: '360px' }}
        />
      </div>

      {/* Topics Grid */}
      {loading ? (
        <div className="page-loader"><div className="spinner-lg" /></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🏷️</div>
          <h3>{search ? 'No matching topics' : 'No topics yet'}</h3>
          {!search && <p>Create the first topic to get started!</p>}
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
          gap: '16px',
        }}>
          {filtered.map(t => {
            const { fg, bg } = getTopicColors(t.topic_id);
            const isFollowed = following.has(t.topic_id);
            return (
              <div
                key={t.topic_id}
                className="card"
                style={{
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                  borderTop: `3px solid ${fg}`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <TopicBadge topicId={t.topic_id} />
                  <button
                    className={`btn btn-sm ${isFollowed ? 'btn-ghost' : 'btn-primary'}`}
                    onClick={() => handleFollow(t.topic_id)}
                    disabled={isFollowed}
                  >
                    {isFollowed ? '✓ Following' : '+ Follow'}
                  </button>
                </div>

                <h3 style={{ fontSize: 'var(--font-size-base)', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {t.name}
                </h3>

                {t.description && (
                  <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                    {t.description}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
