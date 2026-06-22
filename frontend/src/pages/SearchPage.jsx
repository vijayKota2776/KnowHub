import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import QuestionCard from '../components/QuestionCard';
import { SkeletonQuestionCard } from '../components/Skeleton';

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  // Search on mount if query param exists
  useEffect(() => {
    const q = searchParams.get('q');
    if (q) {
      setQuery(q);
      doSearch(q);
    }
  }, [searchParams.get('q')]);

  const doSearch = async (q) => {
    if (!q?.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const data = await api.search.query(q.trim(), 15);
      setResults(data.results || []);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      setSearchParams({ q: query.trim() });
      doSearch(query.trim());
    }
  };

  return (
    <div className="animate-fade-in">
      {/* Search Bar */}
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, marginBottom: '16px' }}>
          Search Questions
        </h1>
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'flex', gap: '10px' }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <span style={{
                position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)',
                fontSize: '18px', pointerEvents: 'none', color: 'var(--text-muted)',
              }}>🔍</span>
              <input
                className="input"
                style={{ paddingLeft: '46px', height: '48px', fontSize: 'var(--font-size-base)' }}
                placeholder="Search for questions, topics, keywords…"
                value={query}
                onChange={e => setQuery(e.target.value)}
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ height: '48px', paddingInline: '24px' }}>
              Search
            </button>
          </div>
        </form>

        {searched && !loading && (
          <p style={{ marginTop: '12px', fontSize: 'var(--font-size-sm)', color: 'var(--text-muted)' }}>
            <span style={{ color: 'var(--text-accent)', fontWeight: 600 }}>{results.length}</span> results for "
            <span style={{ color: 'var(--text-primary)' }}>{searchParams.get('q')}</span>"
            <span style={{ marginLeft: '8px', fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
              · Hybrid Lexical + Semantic Fusion (TF-IDF)
            </span>
          </p>
        )}
      </div>

      {/* Results */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {loading && (
          <>
            <SkeletonQuestionCard />
            <SkeletonQuestionCard />
            <SkeletonQuestionCard />
          </>
        )}

        {!loading && searched && results.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">🔎</div>
            <h3>No results found</h3>
            <p>Try different keywords or check spelling</p>
          </div>
        )}

        {!loading && !searched && (
          <div className="empty-state" style={{ padding: '48px' }}>
            <div className="empty-state-icon">💡</div>
            <h3>Start searching</h3>
            <p>Search uses hybrid lexical + semantic matching to find the most relevant questions</p>
          </div>
        )}

        {!loading && results.map((r, idx) => (
          <div key={r.question_id} style={{ position: 'relative' }}>
            {/* Score bar */}
            <div style={{
              position: 'absolute',
              top: '12px',
              right: '16px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'flex-end',
              gap: '4px',
              zIndex: 1,
            }}>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                  #{idx + 1}
                </span>
                <div style={{
                  padding: '2px 8px',
                  background: 'rgba(99,102,241,0.15)',
                  border: '1px solid rgba(99,102,241,0.3)',
                  borderRadius: '9999px',
                  fontSize: '10px',
                  fontWeight: 700,
                  color: 'var(--text-accent)',
                  fontFamily: 'monospace',
                }}>
                  {(r.search_score * 100).toFixed(1)}%
                </div>
              </div>
              <div style={{ display: 'flex', gap: '4px' }}>
                {/* Lexical bar */}
                <div title={`Lexical: ${(r.lexical_score * 100).toFixed(1)}%`} style={{
                  width: `${Math.max(4, r.lexical_score * 40)}px`,
                  height: '4px',
                  background: '#06b6d4',
                  borderRadius: '2px',
                  transition: 'width 0.5s ease',
                }} />
                {/* Semantic bar */}
                <div title={`Semantic: ${(r.semantic_score * 100).toFixed(1)}%`} style={{
                  width: `${Math.max(4, r.semantic_score * 40)}px`,
                  height: '4px',
                  background: '#a855f7',
                  borderRadius: '2px',
                  transition: 'width 0.5s ease',
                }} />
              </div>
              <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>
                <span style={{ color: '#06b6d4' }}>■</span> lex
                <span style={{ marginLeft: '4px', color: '#a855f7' }}>■</span> sem
              </span>
            </div>

            <QuestionCard question={r} />
          </div>
        ))}
      </div>
    </div>
  );
}
