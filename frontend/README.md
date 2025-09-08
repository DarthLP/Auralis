# Frontend Application

## 🎨 Overview

The Auralis frontend is a modern React application built with Vite that provides a comprehensive user interface for competitor analysis and dashboard visualization. The application features a professional design system, real-time data visualization, and intuitive user workflows.

## 📋 Status: ✅ Implemented

This frontend application is fully implemented with a complete feature set including dashboard views, competitor management, and advanced filtering capabilities.

## 🏗️ Architecture

- **Framework**: React with Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Routing**: React Router DOM
- **State Management**: React hooks (useState, useEffect)
- **Data Fetching**: Mock API system with realistic delays
- **Build Tool**: Vite for fast development and optimized builds

## 📁 Directory Structure

```
frontend/
├── src/                    # Source code
│   ├── components/        # Reusable UI components
│   │   ├── EmptyState.tsx
│   │   ├── LoadingSkeleton.tsx
│   │   ├── LoadingSpinner.tsx
│   │   ├── SourceDrawer.tsx
│   │   ├── SpecsGroup.tsx
│   │   ├── UrlInputWithValidate.tsx
│   │   ├── JobStatusBadge.tsx
│   │   ├── EditableTagInput.tsx
│   │   ├── ProductsEditor.tsx
│   │   ├── SourcesList.tsx
│   │   ├── DedupAlert.tsx
│   │   └── Toast.tsx
│   ├── pages/            # Page components
│   │   ├── Overview.tsx
│   │   ├── CompaniesIndex.tsx
│   │   ├── CompanyPage.tsx
│   │   ├── ProductPage.tsx
│   │   ├── AddCompetitor.tsx
│   │   ├── SignalsPage.tsx
│   │   ├── ReleasesPage.tsx
│   │   └── NotFound.tsx
│   ├── layouts/          # Layout components
│   │   └── AppLayout.tsx
│   ├── lib/              # API client and utilities
│   │   ├── api.ts
│   │   └── mockData.ts
│   ├── utils/            # Utility functions
│   │   ├── urlValidation.ts
│   │   └── __tests__/
│   ├── types/            # TypeScript type definitions
│   ├── hooks/            # Custom React hooks
│   ├── App.tsx           # Main application component
│   ├── main.tsx          # Application entry point
│   └── index.css         # Global styles
├── dist/                 # Built application
├── package.json          # Dependencies and scripts
├── vite.config.ts        # Vite configuration
├── tailwind.config.js    # Tailwind CSS configuration
├── tsconfig.json         # TypeScript configuration
├── postcss.config.js     # PostCSS configuration
└── README.md            # This file
```

## 🎯 Features

### Core Features ✅

- **Overview Dashboard**: Real-time signals and releases tracking with impact scoring
- **Companies Management**: Comprehensive company listing with search and filtering
- **Company Detail Views**: Drill-down into specific competitor information with products and recent activity
- **Product Analysis**: View competitor products, capabilities, and maturity tracking
- **Add Competitor**: URL-based competitor ingestion with smart validation and deduplication
- **Signals Analysis**: Advanced filtering and analysis of industry signals and news
- **Releases Tracking**: Product release monitoring with company and date filtering

### User Interface ✅

- **Responsive Design**: Mobile-first responsive layout with adaptive navigation
- **Professional Design**: Clean, modern interface with consistent styling
- **Loading States**: Comprehensive loading indicators and skeleton screens
- **Empty States**: Friendly empty state components with actionable CTAs
- **Error Handling**: Graceful error states with user-friendly messages

### Competitor Analysis ✅

- **URL-Based Ingestion**: Smart competitor addition via website URL analysis
- **Data Extraction**: Automatic extraction of company information, products, and tags
- **Deduplication**: Intelligent duplicate detection using domain and name matching
- **Source Tracking**: Comprehensive source attribution and credibility tracking
- **Real-time Validation**: Live URL validation with security and reachability checks

## 🔧 Development Setup

### Prerequisites

- Node.js 18+ and npm
- Modern web browser with JavaScript support

### Installation

```bash
cd frontend
npm install
```

### Development Server

```bash
npm run dev
```

Access the application at http://localhost:3000

### Build for Production

```bash
npm run build
```

The built application will be available in the `dist/` directory.

## 🆕 Add Competitor Feature

The Add Competitor functionality provides a comprehensive URL-based competitor ingestion system:

### Key Components

- **UrlInputWithValidate**: Real-time URL validation with debounced input
- **JobStatusBadge**: Visual status tracking for scraper jobs
- **EditableTagInput**: Tag management with add/remove functionality
- **ProductsEditor**: Product list editing with dynamic rows
- **SourcesList**: Read-only source information display
- **DedupAlert**: Duplicate company detection and warning
- **Toast**: Success/error notifications

### Workflow

1. **URL Input**: Enter competitor website URL with live validation
2. **Validation**: Automatic URL normalization and security checks
3. **Reachability**: Mock reachability testing
4. **Deduplication**: Check for existing companies by domain/name
5. **Scraping**: Mock scraper job with status tracking
6. **Review**: Edit extracted data before saving
7. **Save**: Add to competitor database with success feedback

### Technical Features

- **URL Validation**: Comprehensive validation with eTLD+1 extraction
- **Debounced Input**: 250ms debounce for smooth real-time validation
- **Type Safety**: Full TypeScript integration
- **Error Handling**: Graceful error states with helpful messages
- **Mock Integration**: Seamless integration with existing mock data system

## 🐳 Planned Docker Configuration

### Dockerfile.frontend (Planned)

```dockerfile
FROM node:18-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine AS production
COPY --from=build /app/out /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 🔌 Planned API Integration

### Backend Communication

The frontend will communicate with the backend API:

- **Base URL**: `http://localhost:8000` (development)
- **Authentication**: JWT tokens (future)
- **CORS**: Configured for `http://localhost:3000`

### Planned API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/competitors` | Add new competitor |
| `GET` | `/api/competitors` | List all competitors |
| `GET` | `/api/competitors/{id}` | Get competitor details |
| `POST` | `/api/competitors/{id}/crawl` | Trigger website crawl |
| `GET` | `/api/competitors/{id}/products` | Get competitor products |

## 🎨 Planned UI Components

### Core Components

- **CompetitorCard**: Competitor overview card with key metrics
- **CompetitorList**: List view of all competitors
- **ProductCard**: Product information display
- **ChangeIndicator**: Visual indicator for recent changes
- **DashboardChart**: Data visualization components
- **ProgressIndicator**: Crawling and processing progress

### Layout Components

- **Header**: Navigation and user controls
- **Sidebar**: Processing options and tools
- **MainContent**: Primary application area
- **Footer**: Status and additional information

## 📱 Planned Responsive Design

### Breakpoints

- **Mobile**: 320px - 768px
- **Tablet**: 768px - 1024px
- **Desktop**: 1024px+

### Mobile Features

- Touch-friendly competitor navigation
- Swipe gestures for navigation
- Optimized dashboard interface
- Responsive data visualization

## 🧪 Planned Testing Strategy

### Unit Testing

- **Framework**: Jest + React Testing Library
- **Coverage**: 80%+ code coverage
- **Components**: All UI components tested
- **Hooks**: Custom hooks tested

### Integration Testing

- **API Integration**: Backend communication tests
- **User Flows**: End-to-end user journey tests
- **Data Visualization**: Chart and graph rendering tests

### E2E Testing

- **Framework**: Playwright or Cypress
- **Scenarios**: Complete user workflows
- **Cross-browser**: Chrome, Firefox, Safari testing

## 📋 Development Roadmap

### Phase 1: Foundation ✅
- [x] React + Vite project setup
- [x] TypeScript configuration
- [x] Tailwind CSS setup
- [x] React Router DOM routing structure

### Phase 2: Core UI ✅
- [x] AppLayout with navigation and header
- [x] Overview dashboard with signals and releases
- [x] Companies listing with search and filtering
- [x] Responsive design and mobile support

### Phase 3: Data Features ✅
- [x] Mock data system with realistic delays
- [x] Company detail views with products and activity
- [x] Product detail pages with capabilities
- [x] Advanced signals filtering and analysis
- [x] Releases tracking with company and date filtering

### Phase 4: Advanced Features ✅
- [x] Add Competitor URL-based ingestion
- [x] URL validation and normalization system
- [x] Mock scraper job system with status tracking
- [x] Deduplication logic for existing companies
- [x] Reusable UI components for competitor addition
- [x] Source drawer integration across pages

### Phase 5: Polish ✅
- [x] Loading states and skeleton screens
- [x] Empty states with actionable CTAs
- [x] Error handling and user feedback
- [x] Toast notifications for success/error states
- [x] Comprehensive documentation

## 🎯 Performance Goals

### Loading Performance

- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Time to Interactive**: < 3.5s
- **Bundle Size**: < 500KB gzipped

### Runtime Performance

- **Data Processing**: Real-time updates without lag
- **UI Responsiveness**: 60fps animations
- **Memory Usage**: < 100MB for typical usage
- **Battery Efficiency**: Optimized for mobile devices

## 🔒 Planned Security Considerations

### Client-Side Security

- **Input Validation**: All user inputs validated
- **XSS Prevention**: Content Security Policy
- **HTTPS**: Force HTTPS in production
- **Secure Headers**: Security headers configured

### Data Protection

- **API Communication**: Encrypted requests
- **Local Storage**: Secure data storage
- **Privacy**: No unnecessary data collection
- **Data Validation**: Client-side input validation

## 📚 Planned Resources

### Documentation

- Component documentation with Storybook
- API integration guides
- Deployment instructions
- Contributing guidelines

### Learning Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev/)
- [Chart.js Documentation](https://www.chartjs.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)

## 🤝 Contributing (Future)

When the frontend development begins:

1. Follow the established code style
2. Write tests for new components
3. Update documentation
4. Ensure responsive design
5. Test across browsers

## 📞 Support (Future)

For frontend-specific issues:
- Check component documentation
- Review browser console for errors
- Test in different browsers
- Verify API connectivity

---

**Note**: This frontend is currently in the planning phase. Development will begin after the backend API is more fully developed and the core competitor analysis features are implemented.
