import Avatar from './Avatar';
import VoteControls from './VoteControls';
import { timeAgo, formatReputation } from '../utils/helpers';

export default function AnswerCard({ answer, questionId, isAuth, rank }) {
  const { answer_id, author_id, author_username, content, upvotes, downvotes, created_at, ranking_score, author_reputation } = answer;

  const isTopAnswer = rank === 0;

  return (
    <div
      className="card"
      style={{
        padding: '20px 24px',
        display: 'flex',
        gap: '16px',
        borderLeft: isTopAnswer ? '2px solid var(--color-upvote)' : '2px solid transparent',
        position: 'relative',
      }}
    >
      {/* Top Answer ribbon */}
      {isTopAnswer && (
        <div style={{
          position: 'absolute',
          top: '12px',
          right: '16px',
          background: 'rgba(16,185,129,0.15)',
          border: '1px solid rgba(16,185,129,0.3)',
          borderRadius: '9999px',
          padding: '2px 10px',
          fontSize: '11px',
          fontWeight: 700,
          color: 'var(--color-upvote)',
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
        }}>
          ★ Top Answer
        </div>
      )}

      {/* Vote Controls */}
      <VoteControls
        questionId={questionId}
        answerId={answer_id}
        initialUpvotes={upvotes}
        initialDownvotes={downvotes}
        isAuth={isAuth}
      />

      {/* Content */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <p style={{ color: 'var(--text-primary)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
          {content}
        </p>

        {/* Meta */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          paddingTop: '12px',
          borderTop: '1px solid var(--border-subtle)',
        }}>
          <Avatar username={author_username || author_id} size={28} />
          <div>
            <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--text-secondary)' }}>
              {author_username || author_id}
            </span>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
              {' · '}Rep: {formatReputation(author_reputation)}
              {' · '}
              {timeAgo(created_at)}
            </span>
          </div>

          {ranking_score !== undefined && (
            <span style={{
              marginLeft: 'auto',
              fontSize: 'var(--font-size-xs)',
              color: 'var(--text-muted)',
              fontFamily: 'monospace',
            }}>
              score: {ranking_score.toFixed(4)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
