'use client';

import { useState } from 'react';
import { Command as CommandIcon, Search, Settings, User, Database, Scissors, Activity, Shield, Terminal, Users, X } from 'lucide-react';
import { cn } from '@/lib/utils';

export function CommandPalette({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [query, setQuery] = useState('');

  const commands = [
    { icon: Search, label: 'Search content...', shortcut: '⌘F', action: () => {} },
    { icon: Database, label: 'View all data', shortcut: '⌘D', action: () => {} },
    { icon: Scissors, label: 'Manage scrapers', shortcut: '⌘S', action: () => {} },
    { icon: Activity, label: 'View analytics', shortcut: '⌘A', action: () => {} },
    { icon: Settings, label: 'Settings', shortcut: '⌘,', action: () => {} },
    { icon: User, label: 'Profile settings', shortcut: '⌘P', action: () => {} },
    { icon: Shield, label: 'Security center', shortcut: '⌘ShiftS', action: () => {} },
    { icon: Terminal, label: 'View logs', shortcut: '⌘L', action: () => {} },
    { icon: Users, label: 'User management', shortcut: '⌘U', action: () => {} },
  ];

  const filteredCommands = commands.filter(cmd =>
    cmd.label.toLowerCase().includes(query.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm"
          onClick={onClose}
        />
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', damping: 25 }}
          className="relative w-full max-w-2xl glass rounded-2xl shadow-2xl overflow-hidden"
        >
          <div className="flex items-center gap-3 p-4 border-b border-border/50">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <CommandIcon className="w-5 h-5 text-primary" />
            </div>
            <input
              type="text"
              placeholder="Type a command or search..."
              className="flex-1 bg-transparent text-lg outline-none placeholder:text-muted-foreground"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              autoFocus
            />
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="shrink-0"
            >
              <X className="w-5 h-5" />
            </Button>
          </div>

          <div className="max-h-96 overflow-y-auto p-2 scrollbar-hide">
            {filteredCommands.map((cmd, i) => (
              <button
                key={i}
                onClick={() => {
                  cmd.action();
                  onClose();
                }}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-3 rounded-lg transition-colors",
                  "hover:bg-primary/10 text-left"
                )}
              >
                <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center">
                  <cmd.icon className="w-5 h-5 text-muted-foreground" />
                </div>
                <div className="flex-1">
                  <p className="font-medium">{cmd.label}</p>
                </div>
                <kbd className="px-2 py-1 text-xs font-mono text-muted-foreground bg-muted rounded">
                  {cmd.shortcut}
                </kbd>
              </button>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
