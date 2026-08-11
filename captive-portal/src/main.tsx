import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { WifiParamsProvider } from './context/WifiParamsContext';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <WifiParamsProvider>
        <App />
      </WifiParamsProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
