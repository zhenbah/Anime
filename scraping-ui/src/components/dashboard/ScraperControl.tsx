'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Switch } from '@/components/ui/Switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Play, Pause, Settings, RefreshCw } from 'lucide-react';

interface ScraperControlProps {
  onStart?: () => void;
  onStop?: () => void;
}

export function ScraperControl({ onStart, onStop }: ScraperControlProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [frequency, setFrequency] = useState('hourly');
  const [autoMode, setAutoMode] = useState(true);

  const handleToggle = () => {
    setIsRunning(!isRunning);
    if (!isRunning) {
      onStart?.();
    } else {
      onStop?.();
    }
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-lg">Scraper Control Panel</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Status */}
        <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-3">
            <div className={cn(
              "w-3 h-3 rounded-full",
              isRunning ? 'bg-green-500 animate-pulse' : 'bg-muted-foreground'
            )} />
            <span className="font-medium">
              {isRunning ? 'Running' : 'Stopped'}
            </span>
          </div>
          <Badge variant={isRunning ? 'default' : 'secondary'}>
            {isRunning ? 'Active' : 'Inactive'}
          </Badge>
        </div>

        {/* Controls */}
        <div className="flex gap-3">
          <Button
            className="flex-1 gap-2"
            size="lg"
            onClick={handleToggle}
            variant={isRunning ? 'destructive' : 'default'}
          >
            {isRunning ? (
              <><Pause className="w-4 h-4" /> Stop</>
            ) : (
              <><Play className="w-4 h-4" /> Start</>
            )}
          </Button>
          <Button variant="outline" size="icon" size="lg">
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>

        {/* Settings */}
        <div className="space-y-4 p-4 bg-muted/30 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Auto Mode</span>
            <Switch
              checked={autoMode}
              onCheckedChange={setAutoMode}
            />
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium">Frequency</label>
            <Select value={frequency} onValueChange={setFrequency}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="realtime">Real-time</SelectItem>
                <SelectItem value="hourly">Every Hour</SelectItem>
                <SelectItem value="daily">Daily</SelectItem>
                <SelectItem value="weekly">Weekly</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Target Sites */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Target Sites</label>
          <div className="flex flex-wrap gap-2">
            {['AnimeDB', 'MovieHub', 'CartoonNet'].map((site) => (
              <Badge key={site} variant="outline" className="cursor-pointer hover:bg-primary/10">
                {site}
              </Badge>
            ))}
          </div>
        </div>

        <Button variant="outline" className="w-full gap-2">
          <Settings className="w-4 h-4" />
          Advanced Settings
        </Button>
      </CardContent>
    </Card>
  );
}
