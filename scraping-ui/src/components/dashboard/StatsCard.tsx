import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { cn } from '@/lib/utils';

interface StatsCardProps {
  title: string;
  value: string | number;
  change?: string;
  icon: React.ReactNode;
  trend?: 'up' | 'down';
  className?: string;
}

export function StatsCard({ title, value, change, icon, trend, className }: StatsCardProps) {
  return (
    <Card className={cn('relative overflow-hidden group', className)}>
      <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 rounded-full -translate-y-1/2 translate-x-1/2 group-hover:scale-150 transition-transform duration-500" />
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
          {icon}
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {change && (
          <p className={cn(
            'text-xs mt-1',
            trend === 'up' ? 'text-green-500' : 'text-red-500'
          )}>
            {change}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
