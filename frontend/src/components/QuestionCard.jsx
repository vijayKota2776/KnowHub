import { useNavigate } from 'react-router-dom';
import TopicBadge from './TopicBadge';
import Avatar from './Avatar';
import { timeAgo, truncate } from '../utils/helpers';

export default function QuestionCard({ question }) {
  const navigate = useNavigate();
  const { question_id, title, content, author_id, author_username, topic_ids = [], created_at } = question;

  return (
    <article
      className="card"
      onClick={() => navigate(`/question/${question_id}`)}
      style={{
        padding: '24px',
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        borderLeft: '2px solid transparent',
        transition: 'all 0.25s ease',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.borderLeftColor = 'var(--accent-primary)';
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = 'var(--shadow-glow)';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderLeftColor = 'transparent';
        e.currentTarget.style.transform = 'none';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      {/* Title */}
      <h2 style={{
        fontSize: 'var(--font-size-lg)',
        fontWeight: 600,
        color: 'var(--text-primary)',
        lineHeight: 1.4,
      }}>
        {title}
      </h2>

      {/* Excerpt */}
      <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
        {truncate(content, 150)}
      </p>

      {/* Topics */}
      {topic_ids.length > 0 && (
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {topic_ids.map(tid => <TopicBadge key={tid} topicId={tid} />)}
        </div>
      )}

      {/* Meta */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        paddingTop: '4px',
        borderTop: '1px solid var(--border-subtle)',
      }}>
        <Avatar username={author_username || author_id} size={26} />
        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
          <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>{author_username || author_id}</span>
          {' · '}
          {timeAgo(created_at)}
        </span>
      </div>
    </article>
  );
}
