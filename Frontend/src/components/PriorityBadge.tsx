import { Priority } from '../types';

interface Props { priority: Priority; }
const MAP: Record<Priority, string> = { high: 'badge badge-high', medium: 'badge badge-medium', low: 'badge badge-low' };

export default function PriorityBadge({ priority }: Props) {
  return <span className={MAP[priority]}>{priority}</span>;
}
