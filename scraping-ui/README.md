# Scraping Platform UI

A modern, enterprise-grade web interface for the Scraping Platform. Built with cutting-edge technologies for exceptional performance and user experience.

## 🌟 Features

### Design Philosophy
- **Premium Dark Mode** - Default dark theme with glassmorphism effects
- **Smooth Animations** - Powered by Framer Motion
- **Fully Responsive** - Mobile-first approach
- **Fast Performance** - Optimized with lazy loading and code splitting

### User Interface
- **Command Palette** - Vercel-style command search (⌘K)
- **Collapsible Sidebar** - ChatGPT-like navigation
- **Real-time Dashboard** - Live metrics and monitoring
- **Interactive Charts** - Custom canvas-based visualizations
- **Smart Notifications** - Toast system with rich content

### Admin Dashboard Sections
1. **Overview** - System health and key metrics
2. **Scraper Control** - Start/stop and configure scrapers
3. **Data Management** - View and manage scraped content
4. **Monitoring** - Real-time logs and analytics
5. **Security** - Proxy management and access control
6. **Users** - Team management and permissions

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Clone the repository
cd /workspaces/Anime/scraping-ui

# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📁 Project Structure

```
src/
├── app/                    # Next.js app router
│   ├── admin/             # Admin dashboard pages
│   ├── components/        # Reusable components
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── components/
│   ├── layout/            # Layout components
│   ├── ui/                # UI primitives
│   └── dashboard/         # Dashboard components
├── context/               # React context providers
├── hooks/                 # Custom hooks
├── lib/                   # Utilities and API clients
├── types/                 # TypeScript types
└── config/                # Configuration
```

## 🎨 Design System

### Color Palette
- **Primary**: Indigo 600 (gradient accents)
- **Background**: Deep charcoal (#030303)
- **Foreground**: Off-white (#FAFAFA)
- **Muted**: Subtle grays for secondary content

### Typography
- **Font**: Inter (Google Fonts)
- **Weights**: 400, 500, 600, 700
- **Sizes**: Responsive scaling from 12px to 48px+

### Spacing
- **Scale**: 4px base unit
- **Padding**: 16px, 24px, 32px, 64px
- **Gaps**: 8px, 16px, 24px, 32px

## 🔧 Component Library

### Layout
- `Sidebar` - Collapsible navigation
- `TopNav` - Header with search and notifications
- `CommandPalette` - Global command search

### UI Primitives
- `Button` - Multiple variants and sizes
- `Card` - Glassmorphism cards
- `DataTable` - Sortable, searchable tables
- `Modal` - Dialog overlays
- `Toast` - Notification system
- `Badge` - Status indicators

### Dashboard
- `StatsCard` - Metric display cards
- `ActivityFeed` - Real-time activity log
- `RealTimeChart` - Canvas-based charts
- `ScraperControl` - Scraper management
- `LogViewer` - Terminal-style log display

## 🌐 API Integration

### REST API
```typescript
import { api, scraperApi } from '@/lib/api';

// Get scraping stats
const stats = await api.get('/metrics');

// Start a scraper
await scraperApi.startCrawl({
  url: 'https://example.com',
  method: 'auto',
  maxDepth: 3
});
```

### WebSocket
```typescript
import { useWebSocket } from '@/context/WebSocketContext';

function MyComponent() {
  const { socket, connected } = useWebSocket();
  
  useEffect(() => {
    socket?.on('scraper_update', (data) => {
      console.log('Update:', data);
    });
  }, [socket]);
}
```

## 🎯 Key Features

### Command Palette
Press `⌘K` to open the command palette:
- Search content
- Navigate sections
- Execute commands
- Quick settings access

### Real-time Updates
- Live metrics refresh
- Streaming log updates
- WebSocket-powered notifications
- Auto-refreshing charts

### Responsive Design
- Mobile: 375px - 768px
- Tablet: 768px - 1024px
- Desktop: 1024px - 1440px+
- Ultra-wide: 1440px+

## 🚀 Performance Optimizations

- **Code Splitting** - Route-based lazy loading
- **Image Optimization** - Next.js Image component
- **Font Optimization** - Preloaded Inter font
- **Bundle Analysis** - Tree-shaking enabled
- **Memoization** - React.memo for expensive components

## 🎨 Theming

### Dark Mode (Default)
```css
--background: 0 0% 3%;
--foreground: 0 0% 98%;
--primary: 240 100% 65%;
```

### Light Mode
```css
--background: 0 0% 98%;
--foreground: 0 0% 3%;
--primary: 240 80% 55%;
```

Toggle with the theme switcher in the top navigation.

## 🔐 Authentication

The UI integrates with the backend authentication system:
- JWT token storage
- Automatic token refresh
- Protected routes
- Role-based access control

## 📊 Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🛠️ Development

### Available Scripts

```bash
npm run dev      # Start dev server
npm run build    # Production build
npm run start    # Start production server
npm run lint     # Run ESLint
```

### Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## 🎨 Customization

### Adding New Pages
1. Create page in `app/` directory
2. Add to navigation in `Sidebar`
3. Update routes if needed

### Adding New Components
1. Create in `components/`
2. Export from `index.ts`
3. Add to storybook (if configured)

### Modifying Theme
Edit `tailwind.config.ts` and `globals.css`

## 📈 Performance Metrics

- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **First Input Delay**: < 100ms

## 🔗 Integration with Backend

The UI connects to the Scraping Platform backend:
- REST API on port 8000
- WebSocket for real-time updates
- JWT authentication
- Automatic retry on failure

## 📚 Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Framer Motion](https://www.framer.com/motion/)
- [React Hook Form](https://react-hook-form.com/)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License - see LICENSE file

## 🆘 Support

For issues and questions, please open an issue on the repository.
