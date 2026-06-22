import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/Toast';
import AnswerCard from '../components/AnswerCard';
import CommentList from '../components/CommentList';
import TopicBadge from '../components/TopicBadge';
import Avatar from '../components/Avatar';
import { timeAgo } from '../utils/helpers';

export default function QuestionPage() {
  const { id } = useParams();
  const { isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [answerText, setAnswerText] = useState('');
  const [posting, setPosting] = useState(false);

  useEffect(() => {
    window.scrollTo(0, 0);
    api.questions.get(id)
      .then(setData)
      .catch(e => toast.error(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const submitAnswer = async (e) => {
    e.preventDefault();
    if (!answerText.trim()) return;
    setPosting(true);
    try {
      await api.answers.create(id, { content: answerText.trim() });
      toast.success('Answer posted!');
      setAnswerText('');
      // Reload answers
      const updated = await api.questions.get(id);
      setData(updated);
    } catch (err) {
      toast.error(err.message || 'Failed to post answer');
    } finally {
      setPosting(false);
    }
  };

  if (loading) return (
    <div className="page-loader"><div className="spinner-lg" /></div>
  );

  if (!data) return (
    <div className="empty-state">
      <div className="empty-state-icon">❓</div>
      <h3>Question not found</h3>
    </div>
  );

  const { question, answers = [] } = data;

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>

      {/* Question Detail */}
      <article className="card" style={{ padding: '32px' }}>
        {/* Topics */}
        {question.topic_ids?.length > 0 && (
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '16px' }}>
            {question.topic_ids.map(tid => <TopicBadge key={tid} topicId={tid} />)}
          </div>
        )}

        <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, lineHeight: 1.4, marginBottom: '20px' }}>
          {question.title}
        </h1>

        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8, fontSize: 'var(--font-size-base)', whiteSpace: 'pre-wrap', marginBottom: '24px' }}>
          {question.content}
        </p>

        {/* Author Meta */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          paddingTop: '16px',
          borderTop: '1px solid var(--border-subtle)',
        }}>
          <Avatar username={question.author_username || question.author_id} size={32} />
          <div>
            <span
              style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)', color: 'var(--text-accent)', cursor: 'pointer' }}
              onClick={() => navigate(`/profile/${question.author_id}`)}
            >
              {question.author_username || question.author_id}
            </span>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
              {' · '}asked {timeAgo(question.created_at)}
            </span>
          </div>
        </div>
      </article>

      {/* Comments */}
      <div className="card" style={{ padding: '20px 24px' }}>
        <CommentList questionId={id} isAuth={isAuthenticated} />
      </div>

      {/* Answers Section */}
      <div>
        <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, marginBottom: '16px' }}>
          {answers.length} {answers.length === 1 ? 'Answer' : 'Answers'}
          <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)', fontWeight: 400, marginLeft: '10px' }}>
            ranked by Wilson Score + Reputation + Time Decay
          </span>
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {answers.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">💬</div>
              <h3>No answers yet</h3>
              <p>Be the first to answer this question!</p>
            </div>
          ) : (
            answers.map((ans, idx) => (
              <AnswerCard
                key={ans.answer_id}
                answer={ans}
                questionId={id}
                isAuth={isAuthenticated}
                rank={idx}
              />
            ))
          )}
        </div>
      </div>

      {/* Post Answer */}
      <div className="card" style={{ padding: '28px' }}>
        <h3 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 600, marginBottom: '16px' }}>
          Your Answer
        </h3>

        {isAuthenticated ? (
          <form onSubmit={submitAnswer} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <textarea
              className="textarea"
              style={{ minHeight: '160px' }}
              placeholder="Write a detailed, helpful answer…"
              value={answerText}
              onChange={e => setAnswerText(e.target.value)}
              required
              minLength={5}
            />
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <button type="submit" className="btn btn-primary" disabled={posting || !answerText.trim()}>
                {posting ? <><span className="spinner" /> Posting…</> : '📤 Post Answer'}
              </button>
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                Your answer will be ranked by the community
              </span>
            </div>
          </form>
        ) : (
          <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)' }}>
            <p style={{ marginBottom: '12px' }}>Sign in to post an answer</p>
            <button className="btn btn-primary" onClick={() => navigate('/login')}>
              Sign In
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
