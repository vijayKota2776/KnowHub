import { useState, useCallback } from 'react';
import { api } from '../api/client';
import { useToast } from './Toast';

export default function VoteControls({ questionId, answerId, initialUpvotes = 0, initialDownvotes = 0, isAuth }) {
  const [upvotes, setUpvotes] = useState(initialUpvotes);
  const [downvotes, setDownvotes] = useState(initialDownvotes);
  const [voting, setVoting] = useState(null); // 'upvote' | 'downvote'
  const [voted, setVoted] = useState(null);
  const toast = useToast();

  const handleVote = useCallback(async (type) => {
    if (!isAuth) { toast.error('Sign in to vote'); return; }
    if (voting) return;

    setVoting(type);
    try {
      const result = await api.answers.vote(questionId, answerId, type);
      setUpvotes(result.upvotes);
      setDownvotes(result.downvotes);
      setVoted(type);
    } catch (e) {
      toast.error(e.message || 'Vote failed');
    } finally {
      setVoting(null);
    }
  }, [questionId, answerId, isAuth, voting, toast]);

  const score = upvotes - downvotes;

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '6px',
      minWidth: '44px',
    }}>
      {/* Upvote */}
      <button
        onClick={() => handleVote('upvote')}
        disabled={!!voting}
        style={{
          background: voted === 'upvote' ? 'rgba(16,185,129,0.15)' : 'transparent',
          border: `1px solid ${voted === 'upvote' ? 'rgba(16,185,129,0.5)' : 'var(--border-default)'}`,
          borderRadius: '8px',
          width: '36px',
          height: '36px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          color: voted === 'upvote' ? 'var(--color-upvote)' : 'var(--text-muted)',
          transition: 'all 0.2s',
          fontSize: '16px',
        }}
        title="Upvote"
      >
        ▲
      </button>

      {/* Score */}
      <span style={{
        fontSize: '14px',
        fontWeight: 700,
        color: score > 0 ? 'var(--color-upvote)' : score < 0 ? 'var(--color-downvote)' : 'var(--text-muted)',
        lineHeight: 1,
      }}>
        {score}
      </span>

      {/* Downvote */}
      <button
        onClick={() => handleVote('downvote')}
        disabled={!!voting}
        style={{
          background: voted === 'downvote' ? 'rgba(239,68,68,0.15)' : 'transparent',
          border: `1px solid ${voted === 'downvote' ? 'rgba(239,68,68,0.5)' : 'var(--border-default)'}`,
          borderRadius: '8px',
          width: '36px',
          height: '36px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          color: voted === 'downvote' ? 'var(--color-downvote)' : 'var(--text-muted)',
          transition: 'all 0.2s',
          fontSize: '16px',
        }}
        title="Downvote"
      >
        ▼
      </button>
    </div>
  );
}
