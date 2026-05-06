import { Inter } from 'next/font/google';
import './globals.css';
import { Sidebar } from '@/components/layout/Sidebar';
import { TopNav } from '@/components/layout/TopNav';
import { ThemeProvider } from '@/context/ThemeContext';
import { AuthProvider } from '@/context/AuthContext';
import { Toaster } from '@/components/ui/Toast';
import { cn } from '@/lib/utils';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'ScrapePro - Enterprise Scraping Platform',
  description: 'Advanced web scraping infrastructure with AI-powered extraction',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={cn(inter.className, 'min-h-screen bg-background')}>
        <ThemeProvider>
          <AuthProvider>
            <div className="flex min-h-screen">
              <Sidebar />
              <div className="flex-1 lg:pl-64">
                <TopNav />
                <main className="p-4 lg:p-6">
                  {children}
                </main>
              </div>
            </div>
            <Toaster />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
