import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { reportWebVitals } from './reportWebVitals';

// Get the root element
const container = document.getElementById('root');

if (!container) {
  throw new Error('Failed to find the root element');
}

// Create React root
const root = createRoot(container);

// Render the app
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();