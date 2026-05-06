import { Sidebar } from '@/components/layout/Sidebar';
import { TopNav } from '@/components/layout/TopNav';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { ActivityFeed } from '@/components/dashboard/ActivityFeed';
import { RealTimeChart } from '@/components/dashboard/RealTimeChart';
import { ScraperControl } from '@/components/dashboard/ScraperControl';
import { LogViewer } from '@/components/dashboard/LogViewer';
import { 
  Activity, 
  Database, 
  Scissors, 
  TrendingUp, 
  AlertCircle, 
  CheckCircle,
  Server,
  BarChart3
} from 'lucide-react';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function AdminDashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const stats = [
    {
      title: 'Total Scraped',
      value: '124,582',
      change: '+12.5% from last week',
      icon: <Database className="w-5 h-5 text-primary" />,
      trend: 'up' as const,
    },
    {
      title: 'Active Scrapers',
      value: '24',
      change: '+3 running',
      icon: <Scissors className="w-5 h-5 text-primary" />,
      trend: 'up' as const,
    },
    {
      title: 'Success Rate',
      value: '98.7%',
      change: '+0.3% improvement',
      icon: <CheckCircle className="w-5 h-5 text-green-500" />,
      trend: 'up' as const,
    },
    {
      title: 'Error Rate',
      value: '1.3%',
      change: '-0.2% decrease',
      icon: <AlertCircle className="w-5 h-5 text-red-500" />,
      trend: 'down' as const,
    },
  ];

  const requestData = Array.from({ length: 12 }, (_, i) => ({
    name: `${i + 1}:00`,
    value: Math.floor(Math.random() * 1000) + 500,
  }));

  const errorData = Array.from({ length: 12 }, (_, i) => ({
    name: `${i + 1}:00`,
    value: Math.floor(Math.random() * 50),
  }));

  return (
    <div className="min-h-screen bg-background">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      
      <div className="lg:pl-64">
        <TopNav onMenuToggle={() => setSidebarOpen(!sidebarOpen)} />
        
        <main className="p-4 lg:p-6 space-y-6">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-between"
          >
            <div>
              <h1 className="text-2xl lg:text-3xl font-bold gradient-text">Dashboard</h1>
              <p className="text-muted-foreground">Real-time monitoring and control center</p>
            </div>
            <div className="flex items-center gap-2">
              <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-green-500/10">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-sm font-medium text-green-500">All systems operational</span>
              </div>
            </div>
          </motion.div>

          {/* Stats Grid */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
          >
            {stats.map((stat, i) => (
              <StatsCard key={stat.title} {...stat} />
            ))}
          </motion.div>

          {/* Charts and Controls */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="grid grid-cols-1 lg:grid-cols-3 gap-6"
          >
            {/* Request Chart */}
            <div className="lg:col-span-2">
              <RealTimeChart data={requestData} title="Requests per Hour" color="#6366f1" />
            </div>

            {/* Scraper Control */}
            <div className="lg:col-span-1">
              <ScraperControl />
            </div>
          </motion.div>

          {/* Error Chart and Activity */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          >
            <RealTimeChart data={errorData} title="Errors per Hour" color="#ef4444" />
            <ActivityFeed />
          </motion.div>

          {/* Log Viewer */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="grid grid-cols-1 gap-6"
          >
            <LogViewer />
          </motion.div>
        </main>
      </div>
    </div>
  );
}
