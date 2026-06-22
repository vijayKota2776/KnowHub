import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useToast } from '../components/Toast';
import TopicBadge from '../components/TopicBadge';

export default function AskPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const [form, setForm] = useState({ title: '', content: '', topic_ids: [] });
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.topics.list().then(d => setTopics(d.topics || [])).catch(() => {});
  }, []);

  const toggleTopic = (id) => {
    setForm(f => ({
      ...f,
      topic_ids: f.topic_ids.includes(id)
        ? f.topic_ids.filter(t => t !== id)
        : [...f.topic_ids, id],
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title.trim() || !form.content.trim()) return;
    setLoading(true);
    try {
      const q = await api.questions.create({
        title: form.title.trim(),
        content: form.content.trim(),
        topic_ids: form.topic_ids,
      });
      toast.success('Question posted!');
      navigate(`/question/${q.question_id}`);
    } catch (err) {
      toast.error(err.message || 'Failed to post question');
    } finally {
      setLoading(false);
    }
  };

  const titleLen = form.title.length;
  const contentLen = form.content.length;

  return (
    <div className="animate-fade-in" style={{ maxWidth: '720px', margin: '0 auto' }}>
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, marginBottom: '8px' }}>
          Ask a Question
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>
          Be specific. Good questions get great answers.
        </p>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

        {/* Title */}
        <div className="card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <label className="form-label">Question Title</label>
            <span style={{ fontSize: 'var(--font-size-xs)', color: titleLen > 220 ? 'var(--color-error)' : 'var(--text-muted)' }}>
              {titleLen}/256
            </span>
          </div>
          <input
            className="input"
            style={{ fontSize: 'var(--font-size-base)' }}
            placeholder="e.g. How does Python's garbage collector detect cyclic references?"
            value={form.title}
            onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
            required
            minLength={5}
            maxLength={256}
          />
          <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
            Be specific and imagine you're asking a question to another person.
          </p>
        </div>

        {/* Body */}
        <div className="card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <label className="form-label">Question Details</label>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
              {contentLen} chars
            </span>
          </div>
          <textarea
            className="textarea"
            style={{ minHeight: '200px', fontSize: 'var(--font-size-base)' }}
            placeholder="Include all the information someone would need to answer your question. Share what you've already tried and what results you got…"
            value={form.content}
            onChange={e => setForm(f => ({ ...f, content: e.target.value }))}
            required
            minLength={10}
          />
        </div>

        {/* Topics */}
        <div className="card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <label className="form-label">Topics</label>
          <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
            Select up to 5 relevant topics to help people find your question
          </p>
          {topics.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>No topics available yet.</p>
          ) : (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {topics.map(t => {
                const selected = form.topic_ids.includes(t.topic_id);
                return (
                  <button
                    key={t.topic_id}
                    type="button"
                    onClick={() => toggleTopic(t.topic_id)}
                    style={{
                      padding: '6px 14px',
                      borderRadius: '9999px',
                      border: selected ? '2px solid var(--accent-primary)' : '1px solid var(--border-default)',
                      background: selected ? 'var(--accent-gradient-subtle)' : 'transparent',
                      color: selected ? 'var(--text-accent)' : 'var(--text-secondary)',
                      fontSize: 'var(--font-size-sm)',
                      fontWeight: selected ? 600 : 400,
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      fontFamily: 'var(--font-family)',
                    }}
                  >
                    {t.name}
                  </button>
                );
              })}
            </div>
          )}
          {form.topic_ids.length > 0 && (
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '8px' }}>
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>Selected: </span>
              {form.topic_ids.map(id => <TopicBadge key={id} topicId={id} />)}
            </div>
          )}
        </div>

        {/* Submit */}
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            type="submit"
            className="btn btn-primary btn-lg"
            disabled={loading || !form.title.trim() || !form.content.trim()}
          >
            {loading ? <><span className="spinner" /> Posting…</> : '🚀 Post Question'}
          </button>
          <button
            type="button"
            className="btn btn-ghost btn-lg"
            onClick={() => navigate(-1)}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
