import { getTopicColors } from '../utils/helpers';

export default function TopicBadge({ topicId, onClick }) {
  const { fg, bg } = getTopicColors(topicId);

  return (
    <span
      onClick={onClick}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '3px 10px',
        borderRadius: '9999px',
        fontSize: '12px',
        fontWeight: 600,
        color: fg,
        background: bg,
        border: `1px solid ${fg}33`,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.2s ease',
        letterSpacing: '0.02em',
      }}
      className="topic-badge"
    >
      {topicId}
    </span>
  );
}
