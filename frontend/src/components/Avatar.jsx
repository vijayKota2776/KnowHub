import { getInitials, getAvatarGradient } from '../utils/helpers';

export default function Avatar({ username, size = 36 }) {
  const initials = getInitials(username);
  const gradient = getAvatarGradient(username);

  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        background: gradient,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: size * 0.36,
        fontWeight: 700,
        color: 'white',
        flexShrink: 0,
        letterSpacing: '-0.5px',
      }}
    >
      {initials}
    </div>
  );
}
