'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Bell, Menu, Sun, Moon, Command as CommandIcon } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { useTheme } from '@/context/ThemeContext';
import { CommandPalette } from './CommandPalette';
import { cn } from '@/lib/utils';

export function TopNav({ onMenuToggle }: { onMenuToggle?: () => void }) {
  const { theme, toggleTheme } = useTheme();
  const [isCommandOpen, setIsCommandOpen] = useState(false);
  const [notifications] = useState([
    { id: 1, type: 'success', message: 'Scraping completed', time: '2 min ago' },
    { id: 2, type: 'warning', message: 'High error rate detected', time: '5 min ago' },
    { id: 3, type: 'info', message: 'New user registered', time: '1 hour ago' },
  ]);

  return (
    <>
      <motion.header
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        className={cn(
          "sticky top-0 z-40 border-b border-border/50",
          "glass-light backdrop-blur-xl"
        )}
      >
        <div className="flex items-center justify-between px-4 py-3 lg:px-6">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={onMenuToggle}
              className="lg:hidden"
            >
              <Menu className="w-5 h-5" />
            </Button>
            
            <div className="relative hidden md:block">
              <Button
                variant="ghost"
                size="sm"
                className="gap-2 text-muted-foreground hover:text-foreground"
                onClick={() => setIsCommandOpen(true)}
              >
                <CommandIcon className="w-4 h-4" />
                <span className="text-sm">Search...</span>
                <kbd className="hidden px-2 py-1 text-xs font-mono text-muted-foreground bg-muted rounded lg:inline">
                  ⌘K
                </kbd>
              </Button>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              className="relative hidden sm:flex"
            >
              <Bell className="w-5 h-5" />
              {notifications.length > 0 && (
                <Badge
                  variant="destructive"
                  className="absolute -top-1 -right-1 w-5 h-5 text-xs p-0 flex items-center justify-center"
                >
                  {notifications.length}
                </Badge>
              )}
            </Button>

            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="hidden sm:flex"
            >
              {theme === 'dark' ? (
                <Sun className="w-5 h-5" />
              ) : (
                <Moon className="w-5 h-5" />
              )}
            </Button>

            <div className="w-px h-6 bg-border/50 hidden sm:block" />

            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary/10">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-xs font-medium text-primary">Live</span>
            </div>
          </div>
        </div>
      </motion.header>

      <CommandPalette isOpen={isCommandOpen} onClose={() => setIsCommandOpen(false)} />
    </>
  );
}
