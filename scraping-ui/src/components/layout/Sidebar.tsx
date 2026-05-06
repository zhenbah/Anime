'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, Search, Command } from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';

export function Sidebar({ isOpen, onClose, className }: { isOpen?: boolean; onClose?: () => void; className?: string }) {
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const menuItems = [
    {
      section: 'Main',
      items: [
        { icon: 'LayoutDashboard', label: 'Dashboard', href: '/admin', active: true },
        { icon: 'Scissors', label: 'Scrapers', href: '/admin/scrapers' },
      ]
    },
    {
      section: 'Data',
      items: [
        { icon: 'Database', label: 'Content', href: '/admin/data' },
        { icon: 'Search', label: 'Search Index', href: '/admin/search' },
      ]
    },
    {
      section: 'Monitoring',
      items: [
        { icon: 'Activity', label: 'Analytics', href: '/admin/monitoring' },
        { icon: 'Terminal', label: 'Logs', href: '/admin/logs' },
        { icon: 'Shield', label: 'Security', href: '/admin/security' },
      ]
    },
    {
      section: 'Settings',
      items: [
        { icon: 'Users', label: 'Users', href: '/admin/users' },
        { icon: 'Settings', label: 'Settings', href: '/admin/settings' },
      ]
    }
  ];

  const sidebarContent = (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Logo */}
      <div className="p-6 border-b border-border/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
            <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div>
            <h1 className="font-bold text-lg gradient-text">ScrapePro</h1>
            <p className="text-xs text-muted-foreground">Enterprise Platform</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 scrollbar-hide">
        {menuItems.map((section) => (
          <div key={section.section} className="px-4 mb-4">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-2">
              {section.section}
            </p>
            <div className="space-y-1">
              {section.items.map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200",
                    "hover:bg-primary/10 hover:text-primary",
                    item.active && "bg-primary/10 text-primary font-medium"
                  )}
                >
                  <span className="text-lg">{/* Icon placeholder */}</span>
                  <span className="text-sm">{item.label}</span>
                  {item.active && (
                    <div className="ml-auto w-1 h-1 rounded-full bg-primary" />
                  )}
                </a>
              )}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border/50">
        <div className="glass rounded-xl p-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary/20 to-purple-600/20 flex items-center justify-center">
              <span className="text-sm font-bold text-primary">
                {user?.name?.[0] || 'U'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.name || 'User'}</p>
              <p className="text-xs text-muted-foreground truncate">{user?.role || 'Admin'}</p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={logout}
              className="shrink-0"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                <polyline points="16 17 21 12 16 7"/>
                <line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );

  if (isMobile) {
    return (
      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-40 lg:hidden"
              onClick={onClose}
            />
            <motion.aside
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 30 }}
              className="fixed inset-y-0 left-0 w-64 z-50 lg:hidden"
            >
              {sidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    );
  }

  return (
    <aside className={cn("hidden lg:block w-64 border-r border-border/50", className)}>
      {sidebarContent}
    </aside>
  );
}
