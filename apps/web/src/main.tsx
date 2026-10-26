import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import '@fontsource-variable/dm-sans';
import 'maplibre-gl/dist/maplibre-gl.css';
import './styles/app.css';
import App from './app/app';
import { DataProvider } from './app/data-context';

const queries = new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } });
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><QueryClientProvider client={queries}><BrowserRouter><DataProvider><App /></DataProvider></BrowserRouter></QueryClientProvider></React.StrictMode>,
);
