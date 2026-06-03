export default function SeverityBadge({ severity }) {
  const map = {
    critical: 'badge-critical',
    high: 'badge-high',
    medium: 'badge-medium',
    low: 'badge-low',
    none: 'badge-none',
  }
  return <span className={map[severity] || 'badge-none'}>{severity || 'none'}</span>
}
