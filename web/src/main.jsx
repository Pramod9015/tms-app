import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './context/AuthContext.jsx'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AuthProvider>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1E293B',
            color: '#F1F5F9',
            border: '1px solid #334155',
            fontSize: '13px',
          },
          success: { iconTheme: { primary: '#22C55E', secondary: '#0F172A' } },
          error: { iconTheme: { primary: '#EF4444', secondary: '#0F172A' } },
        }}
      />
    </AuthProvider>
  </React.StrictMode>,
)
