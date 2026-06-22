/**
 * Utility: Format a Unix timestamp as a relative time string
 * e.g. "5 minutes ago", "3 hours ago", "2 days ago"
 */
export function timeAgo(unixTimestamp) {
  const now = Date.now() / 1000;
  const diff = now - unixTimestamp;

  if (diff < 60) return 'just now';
  if (diff < 3600) {
    const m = Math.floor(diff / 60);
    return `${m} minute${m > 1 ? 's' : ''} ago`;
  }
  if (diff < 86400) {
    const h = Math.floor(diff / 3600);
    return `${h} hour${h > 1 ? 's' : ''} ago`;
  }
  if (diff < 2592000) {
    const d = Math.floor(diff / 86400);
    return `${d} day${d > 1 ? 's' : ''} ago`;
  }
  if (diff < 31536000) {
    const mo = Math.floor(diff / 2592000);
    return `${mo} month${mo > 1 ? 's' : ''} ago`;
  }
  const y = Math.floor(diff / 31536000);
  return `${y} year${y > 1 ? 's' : ''} ago`;
}

/**
 * Generate a consistent color pair for a topic from its string
 */
const TOPIC_PALETTES = [
  ['#6366f1', 'rgba(99,102,241,0.15)'],
  ['#a855f7', 'rgba(168,85,247,0.15)'],
  ['#ec4899', 'rgba(236,72,153,0.15)'],
  ['#14b8a6', 'rgba(20,184,166,0.15)'],
  ['#f59e0b', 'rgba(245,158,11,0.15)'],
  ['#06b6d4', 'rgba(6,182,212,0.15)'],
  ['#10b981', 'rgba(16,185,129,0.15)'],
  ['#ef4444', 'rgba(239,68,68,0.15)'],
  ['#8b5cf6', 'rgba(139,92,246,0.15)'],
  ['#f97316', 'rgba(249,115,22,0.15)'],
];

function hashString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

export function getTopicColors(topicId) {
  const idx = hashString(topicId) % TOPIC_PALETTES.length;
  const [fg, bg] = TOPIC_PALETTES[idx];
  return { fg, bg };
}

/**
 * Generate avatar initials from a username
 */
export function getInitials(username) {
  if (!username) return '?';
  const parts = username.split(/[_\-\s]+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return username.slice(0, 2).toUpperCase();
}

/**
 * Generate a consistent gradient for avatar
 */
const AVATAR_GRADIENTS = [
  'linear-gradient(135deg, #6366f1, #a855f7)',
  'linear-gradient(135deg, #14b8a6, #06b6d4)',
  'linear-gradient(135deg, #f59e0b, #ef4444)',
  'linear-gradient(135deg, #10b981, #06b6d4)',
  'linear-gradient(135deg, #ec4899, #8b5cf6)',
  'linear-gradient(135deg, #f97316, #f59e0b)',
];

export function getAvatarGradient(username) {
  if (!username) return AVATAR_GRADIENTS[0];
  const idx = hashString(username) % AVATAR_GRADIENTS.length;
  return AVATAR_GRADIENTS[idx];
}

/**
 * Truncate text to a max length with ellipsis
 */
export function truncate(str, max = 120) {
  if (!str || str.length <= max) return str;
  return str.slice(0, max).trimEnd() + '…';
}

/**
 * Format reputation score
 */
export function formatReputation(rep) {
  if (!rep) return '1.0';
  return Number(rep).toFixed(1);
}
