/**
 * @file main.tsx
 * @description Application client entry point mounting React 18 root into DOM.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// Mount application into DOM root container with React StrictMode enabled
ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
