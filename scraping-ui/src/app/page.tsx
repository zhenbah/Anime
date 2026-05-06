import { motion } from 'framer-motion';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Search, Scissors, Database, TrendingUp, Shield, Zap } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative py-20 lg:py-32 overflow-hidden">
        <div className="absolute inset-0 gradient-bg" />
        <div className="absolute inset-0 bg-[url('/assets/grid.svg')] opacity-20" />
        
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="relative max-w-7xl mx-auto px-4 text-center"
        >
          <Badge variant="secondary" className="mb-6 animate-in">
            <Zap className="w-4 h-4 mr-2" />
            Enterprise Platform v2.0
          </Badge>
          
          <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold gradient-text mb-6 animate-in slide-up">
            Advanced Web Scraping
            <br />
            Infrastructure
          </h1>
          
          <p className="text-xl lg:text-2xl text-muted-foreground max-w-3xl mx-auto mb-8 animate-in slide-up" style={{ animationDelay: '0.2s' }}>
            Scalable, secure, and intelligent data extraction platform for modern enterprises
          </p>
          
          <motion.div
            className="flex flex-col sm:flex-row gap-4 justify-center animate-in slide-up"
            style={{ animationDelay: '0.4s' }}
          >
            <Button size="lg" className="gap-2 px-8">
              <Scissors className="w-5 h-5" />
              Start Scraping
            </Button>
            <Button size="lg" variant="outline" className="gap-2 px-8">
              <Database className="w-5 h-5" />
              View Demo
            </Button>
          </motion.div>
        </motion.div>
      </section>

      {/* Features Grid */}
      <section className="py-20 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl lg:text-4xl font-bold mb-4">Powerful Features</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Everything you need for enterprise-scale data extraction
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[  
              {
                icon: <Scissors className="w-8 h-8 text-primary" />,
                title: 'Intelligent Scraping',
                description: 'Auto-detection of JS-heavy pages with smart fallback strategies',
              },
              {
                icon: <TrendingUp className="w-8 h-8 text-primary" />,
                title: 'Real-time Analytics',
                description: 'Live monitoring with detailed metrics and performance tracking',
              },
              {
                icon: <Shield className="w-8 h-8 text-primary" />,
                title: 'Enterprise Security',
                description: 'JWT auth, rate limiting, and encrypted data storage',
              },
              {
                icon: <Database className="w-8 h-8 text-primary" />,
                title: 'Scalable Architecture',
                description: 'Distributed queue system with horizontal scaling support',
              },
              {
                icon: <Zap className="w-8 h-8 text-primary" />,
                title: 'High Performance',
                description: '100+ concurrent requests with async processing',
              },
              {
                icon: <Search className="w-8 h-8 text-primary" />,
                title: 'Smart Detection',
                description: 'API endpoint detection and content deduplication',
              },
            ].map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
              >
                <Card className="h-full hover:scale-105 transition-transform duration-300">
                  <CardContent className="pt-6">
                    <div className="mb-4">{feature.icon}</div>
                    <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                    <p className="text-muted-foreground">{feature.description}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 relative">
        <div className="absolute inset-0 gradient-bg opacity-50" />
        <div className="relative max-w-4xl mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl lg:text-4xl font-bold mb-6">
              Ready to Scale Your Data Extraction?
            </h2>
            <p className="text-xl text-muted-foreground mb-8">
              Join hundreds of enterprises using ScrapePro for their data needs
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" className="gap-2 px-8">
                Get Started
              </Button>
              <Button size="lg" variant="outline" className="gap-2 px-8">
                Contact Sales
              </Button>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
