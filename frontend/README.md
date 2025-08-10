# GitHub PR Metrics Analyzer - Frontend

A modern React application for analyzing GitHub pull request metrics with real-time progress tracking and beautiful visualizations.

## Features

- 🚀 **Modern React 18** with TypeScript
- 🎨 **Material-UI (MUI) v5** for beautiful, accessible UI
- 📊 **Interactive Charts** with Chart.js and React Chart.js 2
- 📱 **Responsive Design** - works on all device sizes
- 🌙 **Dark/Light Theme** with system preference detection
- ⚡ **Real-time Updates** via WebSocket connection
- 📈 **Data Visualization** - charts, tables, and metrics
- 📤 **Export Functionality** - CSV download with filtering
- 🔍 **Advanced Filtering** and sorting capabilities
- ✅ **Form Validation** with real-time feedback
- 🔄 **Loading States** and error handling
- 📊 **Progress Tracking** with estimated time remaining

## Getting Started

### Prerequisites

- Node.js 16+ and npm/yarn
- FastAPI backend running on http://localhost:8000

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

3. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

4. Start the development server:
   ```bash
   npm start
   # or
   yarn start
   ```

The application will open at http://localhost:3000

### Building for Production

```bash
npm run build
# or
yarn build
```

## Project Structure

```
src/
├── components/          # React components
│   ├── AnalysisForm.tsx      # GitHub URL and token input form
│   ├── Dashboard.tsx         # Main dashboard layout
│   ├── MetricsCharts.tsx     # Chart visualizations
│   ├── ProgressTracker.tsx   # Real-time progress display
│   └── ResultsTable.tsx      # Data table with filtering
├── hooks/               # Custom React hooks
│   └── useWebSocket.ts       # WebSocket connection management
├── services/            # API and external services
│   └── api.ts               # Backend API integration
├── types/              # TypeScript type definitions
│   └── index.ts             # All application types
├── utils/              # Utility functions
│   ├── constants.ts         # Application constants
│   └── helpers.ts           # Helper functions
├── App.tsx             # Main application component
└── index.tsx           # Application entry point
```

## Key Components

### AnalysisForm
- Form validation for GitHub URLs and tokens
- Date range picker for filtering
- Real-time validation feedback
- Token visibility toggle

### ProgressTracker
- WebSocket-based real-time updates
- Progress bar with percentage
- Step-by-step progress indication
- Estimated time remaining
- Connection status monitoring

### MetricsCharts
- Summary metrics cards
- Top contributors bar chart
- PR state distribution (pie chart)
- Monthly trends (dual-axis chart)
- Review time distribution histogram

### ResultsTable
- Interactive data grid with MUI X DataGrid
- Advanced filtering and sorting
- Column visibility controls
- CSV export functionality
- Pagination and density options

## API Integration

The frontend communicates with the FastAPI backend through:

- **REST API** for starting analysis and fetching data
- **WebSocket** for real-time progress updates
- **File Downloads** for CSV export

### API Service Features

- Automatic request/response interceptors
- Error handling with user-friendly messages
- Request timeout management
- GitHub URL and token validation
- CSV export with blob handling

## WebSocket Integration

Real-time updates are handled through a custom `useWebSocket` hook:

- Automatic connection management
- Reconnection with exponential backoff
- Message type handling (progress, completed, error)
- Connection status tracking
- Cleanup on component unmount

## Theming

The application uses Material-UI's theming system with:

- Light and dark mode support
- Custom color palette
- Typography customization
- Component-specific styling overrides
- System preference detection
- Persistent theme storage

## Form Validation

Comprehensive validation includes:

- GitHub URL format validation
- Token presence and format checking
- Date range validation
- Real-time validation feedback
- Server-side token verification

## Error Handling

Robust error handling covers:

- Network connectivity issues
- API errors with detailed messages
- WebSocket connection failures
- Form validation errors
- File download errors

## Performance Optimizations

- React.memo for component memoization
- useMemo for expensive calculations
- Debounced search and filtering
- Lazy loading for large datasets
- Optimized re-renders

## Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES2020+ features
- CSS Grid and Flexbox
- WebSocket support required

## Contributing

1. Follow TypeScript best practices
2. Use Material-UI components when possible
3. Write comprehensive prop types
4. Include error handling
5. Test on different screen sizes
6. Follow the existing code style

## Dependencies

### Core
- React 18.2+
- TypeScript 5.2+
- Material-UI 5.14+

### Charts & Visualization
- Chart.js 4.4+
- React Chart.js 2 5.2+
- MUI X Data Grid 6.18+

### Utilities
- Axios for HTTP requests
- date-fns for date manipulation
- React Router for navigation

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

## Deployment

For production deployment:

1. Build the application: `npm run build`
2. Serve the `build` folder with a web server
3. Configure environment variables for production API endpoints
4. Ensure WebSocket connections work through your proxy/load balancer

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check if backend WebSocket endpoint is running
   - Verify WebSocket URL in environment variables
   - Check browser console for connection errors

2. **API Requests Failing**
   - Verify backend is running on correct port
   - Check API URL in environment variables
   - Verify CORS configuration in backend

3. **Charts Not Rendering**
   - Check browser console for JavaScript errors
   - Verify Chart.js dependencies are properly installed
   - Ensure data is in correct format for charts

4. **Dark Mode Not Working**
   - Clear browser localStorage
   - Check if theme toggle is functioning
   - Verify Material-UI theme provider setup