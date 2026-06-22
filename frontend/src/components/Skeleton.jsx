export default function Skeleton({ width = '100%', height = 16, borderRadius = 8, style = {} }) {
  return (
    <div
      className="skeleton"
      style={{ width, height, borderRadius, ...style }}
    />
  );
}

export function SkeletonQuestionCard() {
  return (
    <div className="card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <Skeleton height={22} width="70%" />
      <Skeleton height={14} width="100%" />
      <Skeleton height={14} width="85%" />
      <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
        <Skeleton height={22} width={60} borderRadius={9999} />
        <Skeleton height={22} width={80} borderRadius={9999} />
      </div>
      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginTop: '4px' }}>
        <Skeleton width={28} height={28} borderRadius={9999} />
        <Skeleton height={14} width={120} />
      </div>
    </div>
  );
}
