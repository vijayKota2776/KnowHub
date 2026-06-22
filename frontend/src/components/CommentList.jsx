import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { useToast } from './Toast';
import Avatar from './Avatar';
import { timeAgo } from '../utils/helpers';

export default function CommentList({ questionId, isAuth }) {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [text, setText] = useState('');
  const [posting, setPosting] = useState(false);
  const toast = useToast();

  useEffect(() => {
    api.questions.comments(questionId)
      .then(d => setComments(d.comments || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [questionId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    setPosting(true);
    try {
      const comment = await api.questions.addComment(questionId, { content: text.trim() });
      setComments(prev => [...prev, comment]);
      setText('');
      toast.success('Comment posted!');
    } catch (err) {
      toast.error(err.message || 'Failed to post comment');
    } finally {
      setPosting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <h4 style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Comments ({comments.length})
      </h4>

      {/* Comment list */}
      {loading ? (
        <p style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>Loading…</p>
      ) : comments.length === 0 ? (
        <p style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>No comments yet.</p>
      ) : (
        comments.map(c => (
          <div key={c.comment_id} style={{
            display: 'flex',
            gap: '10px',
            padding: '10px 14px',
            background: 'rgba(255,255,255,0.02)',
            borderRadius: '8px',
            borderLeft: '2px solid var(--border-subtle)',
          }}>
            <Avatar username={c.author_username || c.author_id} size={24} />
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'baseline', marginBottom: '4px' }}>
                <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--text-secondary)' }}>{c.author_username || c.author_id}</span>
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>{timeAgo(c.created_at)}</span>
              </div>
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{c.content}</p>
            </div>
          </div>
        ))
      )}

      {/* Comment form */}
      {isAuth && (
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
          <input
            className="input"
            style={{ fontSize: 'var(--font-size-sm)', padding: '8px 14px' }}
            placeholder="Add a comment…"
            value={text}
            onChange={e => setText(e.target.value)}
          />
          <button type="submit" className="btn btn-ghost btn-sm" disabled={posting || !text.trim()}>
            {posting ? <span className="spinner" /> : 'Post'}
          </button>
        </form>
      )}
    </div>
  );
}
