'use client';

import { useEffect, useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ScrollArea } from '@/components/ui/ScrollArea';

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'success';
  message: string;
  details?: string;
}

export function ActivityFeed() {
  const [logs, setLogs] = useState<LogEntry[]>([
    { id: '1', timestamp: '2 min ago', level: 'success', message: 'Scraping completed for example.com' },
    { id: '2', timestamp: '5 min ago', level: 'warn', message: 'High response time detected' },
    { id: '3', timestamp: '10 min ago', level: 'info', message: 'New scraper instance started' },
    { id: '4', timestamp: '15 min ago', level: 'error', message: 'Failed to connect to proxy' },
    { id: '5', timestamp: '20 min ago', level: 'success', message: 'Data processed successfully' },
  ]);

  const getLevelColor = (level: LogEntry['level']) => {
    switch (level) {
      case 'success': return 'bg-green-500';
      case 'error': return 'bg-red-500';
      case 'warn': return 'bg-yellow-500';
      case 'info': return 'bg-blue-500';
    }
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-lg">Recent Activity</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[300px] px-6">
          <div className="space-y-4 py-4">
            {logs.map((log) => (
              <div key={log.id} className="flex gap-3">
                <div className={cn(
                  "w-2 h-2 rounded-full mt-2",
                  getLevelColor(log.level)
                )} />
                <div className="flex-1 space-y-1">
                  <p className="text-sm text-muted-foreground">{log.message}</p>
                  <p className="text-xs text-muted-foreground/60">{log.timestamp}</p>
                </div>
                <Badge
                  variant={log.level === 'error' ? 'destructive' : 'secondary'}
                  className="capitalize"
                >
                  {log.level}
                </Badge>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
