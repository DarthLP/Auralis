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
- **Data Fetching**: Real API integration with backend endpoints
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
│   │   ├── Toast.tsx
│   │   ├── GlobalSearchModal.tsx
│   │   └── UserMenu.tsx
│   ├── pages/            # Page components
│   │   ├── Overview.tsx
│   │   ├── CompaniesIndex.tsx
│   │   ├── CompanyPage.tsx
│   │   ├── ProductPage.tsx
│   │   ├── AddCompetitor.tsx
│   │   ├── SignalsPage.tsx
│   │   ├── Settings.tsx
│   │   └── NotFound.tsx
│   ├── layouts/          # Layout components
│   │   └── AppLayout.tsx
│   ├── lib/              # API client and utilities
│   │   ├── api.ts
│   │   ├── date.ts
│   │   └── avatar.ts
│   ├── utils/            # Utility functions
│   │   ├── urlValidation.ts
│   │   └── __tests__/
│   ├── types/            # TypeScript type definitions
│   │   └── user.ts
│   ├── hooks/            # Custom React hooks
│   │   ├── useGlobalSearch.ts
│   │   └── useDateFormat.ts
│   ├── contexts/         # React Context providers
│   │   └── UserContext.tsx
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

- **Overview Dashboard**: Real-time signals tracking with impact scoring
- **Your Company Profile**: Special "Your Company" profile with dedicated dashboard section and comparison capabilities
- **Companies Management**: Comprehensive company listing with search and filtering
- **Company Detail Views**: Drill-down into specific competitor information with products and recent activity
- **Product Analysis**: View competitor products, capabilities, and maturity tracking
- **Add Competitor**: URL-based competitor ingestion with smart validation and deduplication
- **Signals Analysis**: Advanced filtering and analysis of industry signals and news
- **Global Search**: Command palette style search across companies, products, and signals

### User Interface ✅

- **Responsive Design**: Mobile-first responsive layout with adaptive navigation
- **Professional Design**: Clean, modern interface with consistent styling
- **Loading States**: Comprehensive loading indicators and skeleton screens
- **Empty States**: Friendly empty state components with actionable CTAs
- **Error Handling**: Graceful error states with user-friendly messages

### Your Company Profile ✅

- **Special Company Type**: Dedicated "Your Company" profile with `isSelf: true` flag stored in seed data
- **Dashboard Integration**: Prominent "Your Company" section on Overview page with key metrics
- **Company Statistics**: Display of products count, capabilities count, and recent signals (60 days)
- **Visual Distinction**: Special "Your Company" badge and logo support for easy identification
- **Priority Sorting**: Always appears first in company listings and search results
- **Logo Support**: Company logo display with fallback to colored initials
- **Full Profile Access**: Complete company page with products, capabilities, and activity tracking
- **Centralized Data**: All "Your Company" data stored in `/data/seed.json` alongside competitor data
- **PAL Robotics Integration**: Realistic company profile based on PAL Robotics with comprehensive product portfolio

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

The Add Competitor functionality provides a comprehensive URL-based competitor ingestion system with **stop crawling functionality**:

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
6. **Stop Control**: **NEW** - Stop crawling process during discovery, fingerprinting, or extraction phases
7. **Review**: Edit extracted data before saving
8. **Save**: Add to competitor database with success feedback

### Technical Features

- **URL Validation**: Comprehensive validation with eTLD+1 extraction
- **Debounced Input**: 250ms debounce for smooth real-time validation
- **Stop Crawling**: **NEW** - Real-time stop control with backend API integration
- **Session Management**: Active crawl session tracking and management
- **Type Safety**: Full TypeScript integration
- **Error Handling**: Graceful error states with helpful messages
- **API Integration**: Seamless integration with backend API

## 🔍 Global Search Feature

The Global Search provides a comprehensive command palette style search experience across all data types in Auralis:

### Key Components

- **GlobalSearchModal**: Full-screen search modal with keyboard navigation
- **useGlobalSearch**: Custom hook for managing search state and keyboard shortcuts
- **Search API Functions**: `searchCompanies()`, `searchProducts()`, `searchSignals()`, `globalSearch()`

### Search Features

- **Multi-category Search**: Search across companies, products, and signals simultaneously
- **Smart Ranking**: Prioritizes exact matches, then prefix matches, then substring matches
- **Search Operators**: Use `company:`, `product:`, `signal:` to narrow results
- **Keyboard Navigation**: Arrow keys to navigate, Enter to select, Esc to close
- **Recent Searches**: Stores last 5 searches in localStorage
- **Text Highlighting**: Highlights matching text in search results
- **Grouped Results**: Results organized by category with counts and "View all" links

### Access Methods

- **⌘K/Ctrl+K**: Global keyboard shortcut from anywhere in the app
- **Search Button**: Interactive search button in header (desktop)
- **Search Icon**: Mobile search icon in header

### Navigation Targets

- **Companies** → `/companies/:companyId`
- **Products** → `/companies/:companyId/products/:productId`
- **Signals** → `/signals?highlight=<signalId>`

### Technical Implementation

- **Debounced Search**: 250ms debounce for smooth real-time search
- **API Integration**: Uses real backend API with proper error handling
- **Type Safety**: Full TypeScript integration with proper interfaces
- **Accessibility**: Focus management, ARIA semantics, keyboard navigation
- **Performance**: Efficient rendering with result limits (5 per category)

## 🔌 API Integration ✅

### Backend Communication

The frontend now communicates with the backend API:

- **Base URL**: `http://localhost:8000` (development)
- **Authentication**: JWT tokens (future)
- **CORS**: Configured for `http://localhost:3000`
- **Real-time Data**: Live data fetching from database

### Implemented API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/companies/` | List all companies with search and filtering |
| `GET` | `/api/companies/{id}` | Get detailed company information |
| `GET` | `/api/products/` | List all products with filtering |
| `GET` | `/api/products/{id}` | Get detailed product information |
| `GET` | `/api/signals/` | List all signals with advanced filtering |
| `GET` | `/api/signals/{id}` | Get detailed signal information |
| `GET` | `/api/capabilities/` | List all technical capabilities |
| `GET` | `/api/sources/` | List all data sources |
| `POST` | `/api/crawl/discover` | Website discovery and crawling |
| `POST` | `/api/crawl/fingerprint` | Content fingerprinting pipeline |
| `POST` | `/api/crawl/stop` | **NEW**: Stop active crawl session |
| `GET` | `/api/crawl/active-sessions` | **NEW**: List active crawl sessions |

---

**Note**: This frontend is currently in the planning phase. Development will begin after the backend API is more fully developed and the core competitor analysis features are implemented.
