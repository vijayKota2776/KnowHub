import { useState, useEffect } from 'react';
import { api } from '../api/client';
import QuestionCard from '../components/QuestionCard';
import { SkeletonQuestionCard } from '../components/Skeleton';

export default function FeedPage() {
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.feed.get(30)
      .then(d => setQuestions(d.data || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, marginBottom: '6px' }}>
          Your Feed
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>
          Personalized questions from people and topics you follow
        </p>
      </div>

      {/* Cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {loading && (
          <>
            <SkeletonQuestionCard />
            <SkeletonQuestionCard />
            <SkeletonQuestionCard />
            <SkeletonQuestionCard />
          </>
        )}

        {!loading && error && (
          <div className="empty-state">
            <div className="empty-state-icon">⚠️</div>
            <h3>Couldn't load feed</h3>
            <p>{error}</p>
          </div>
        )}

        {!loading && !error && questions.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">📭</div>
            <h3>Your feed is empty</h3>
            <p>Follow users and topics to see questions here, or browse all topics to get started.</p>
          </div>
        )}

        {!loading && questions.map(q => (
          <QuestionCard key={q.question_id} question={q} />
        ))}
      </div>
    </div>
  );
}
