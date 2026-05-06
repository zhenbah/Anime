'use client';

import { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ScrollArea } from '@/components/ui/ScrollArea';

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'success';
  message: string;
}

export function LogViewer() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filter, setFilter] = useState<'all' | 'info' | 'warn' | 'error' | 'success'>('all');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Simulate real-time logs
    const interval = setInterval(() => {
      const levels: LogEntry['level'][] = ['info', 'warn', 'error', 'success'];
      const messages = [
        'Processing request...',
        'Data extracted successfully',
        'Warning: High response time',
        'Error: Connection timeout',
        'Proxy rotated',
        'Rate limit approaching',
      ];
      
      const newLog: LogEntry = {
        id: Date.now().toString(),
        timestamp: new Date().toLocaleTimeString(),
        level: levels[Math.floor(Math.random() * levels.length)],
        message: messages[Math.floor(Math.random() * messages.length)],
      };

      setLogs(prev => {
        const updated = [newLog, ...prev].slice(0, 100);
        return updated;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [logs]);

  const getLevelColor = (level: LogEntry['level']) => {
    switch (level) {
      case 'success': return 'bg-green-500';
      case 'error': return 'bg-red-500';
      case 'warn': return 'bg-yellow-500';
      case 'info': return 'bg-blue-500';
    }
  };

  const filteredLogs = logs.filter(log => filter === 'all' || log.level === filter);

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle className="text-lg">Live Logs</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 p-0 flex flex-col">
        <div className="flex gap-2 p-4 border-b border-border/50">
          {['all', 'info', 'warn', 'error', 'success'].map((level) => (
            <Badge
              key={level}
              variant={filter === level ? 'default' : 'outline'}
              className="cursor-pointer capitalize"
              onClick={() => setFilter(level as any)}
            >
              {level}
            </Badge>
          ))}
        </div>
        <ScrollArea className="flex-1" ref={scrollRef}>
          <div className="p-4 space-y-2 font-mono text-sm">
            {filteredLogs.map((log) => (
              <div key={log.id} className="flex gap-3 items-start">
                <span className={cn(
                  "w-2 h-2 rounded-full mt-1.5 flex-shrink-0",
                  getLevelColor(log.level)
                )} />
                <span className="text-muted-foreground/60 w-20 flex-shrink-0">
                  {log.timestamp}
                </span>
                <span className="flex-1">
                  <span className={cn(
                    'font-semibold',
                    log.level === 'error' && 'text-red-500',
                    log.level === 'warn' && 'text-yellow-500',
                    log.level === 'success' && 'text-green-500',
                    log.level === 'info' && 'text-blue-500'
                  )}>
                    [{log.level.toUpperCase()}]
                  </span>
                  {' '}{log.message}
                </span>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
