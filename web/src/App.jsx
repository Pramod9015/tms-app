import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext.jsx';
import toast from 'react-hot-toast';

// Lazy-load pages
const LoginPage = lazy(() => import('./pages/LoginPage.jsx'));
const DashboardPage = lazy(() => import('./pages/DashboardPage.jsx'));
const TransactionsPage = lazy(() => import('./pages/TransactionsPage.jsx'));
const BanksPage = lazy(() => import('./pages/BanksPage.jsx'));
const BeneficiariesPage = lazy(() => import('./pages/BeneficiariesPage.jsx'));
const ReportsPage = lazy(() => import('./pages/ReportsPage.jsx'));
const AdminPage = lazy(() => import('./pages/AdminPage.jsx'));

function ProtectedRoute({ children, adminOnly = false }) {
  const { user, isAdmin } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (adminOnly && !isAdmin) return <Navigate to="/" replace />;
  return children;
}

function Sidebar({ isOpen, onClose }) {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    toast.success('Logged out');
    navigate('/login');
  };

  const navItems = [
    { to: '/', icon: '📊', label: 'Dashboard' },
    { to: '/transactions', icon: '💳', label: 'Transactions' },
    { to: '/banks', icon: '🏦', label: 'Banks' },
    { to: '/beneficiaries', icon: '👤', label: 'Beneficiaries' },
    { to: '/reports', icon: '📄', label: 'Reports' },
    ...(isAdmin ? [
      { to: '/admin', icon: '⚙️', label: 'Admin' },
    ] : []),
  ];

  return (
    <>
      <div className={`sidebar-overlay ${isOpen ? 'open' : ''}`} onClick={onClose} />
      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-logo">
          <h1>🔐 TMS</h1>
          <p>Transaction Manager</p>
        </div>
        {navItems.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-btn ${isActive ? 'active' : ''}`}
            onClick={onClose}
          >
            <span>{icon}</span>
            <span>{label}</span>
          </NavLink>
        ))}
        <div className="sidebar-spacer" />
        <div className="sidebar-user">
          <div className="name">👤 {user?.username}</div>
          <div className="role">{user?.role?.toUpperCase()}</div>
        </div>
        <button className="logout-btn" onClick={handleLogout}>🚪 Logout</button>
      </aside>
    </>
  );
}

function AppLayout({ children }) {
  const [isSidebarOpen, setIsSidebarOpen] = React.useState(false);

  return (
    <div className="app-shell">
      <div className="mobile-header">
        <button className="hamburger-btn" onClick={() => setIsSidebarOpen(true)}>☰</button>
        <span className="mobile-title">TMS</span>
        <div style={{ width: 24 }} /> {/* exact spacing equivalent for centering */}
      </div>
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      <main className="main-area fade-in">{children}</main>
    </div>
  );
}

function Spinner() {
  return <div className="spinner" />;
}

export default function App() {
  const { user } = useAuth();

  return (
    <BrowserRouter>
      <Suspense fallback={<div style={{ display: 'flex', justifyContent: 'center', paddingTop: 80 }}><Spinner /></div>}>
        <Routes>
          <Route path="/login" element={user ? <Navigate to="/" replace /> : <LoginPage />} />
          <Route path="/" element={<ProtectedRoute><AppLayout><DashboardPage /></AppLayout></ProtectedRoute>} />
          <Route path="/transactions" element={<ProtectedRoute><AppLayout><TransactionsPage /></AppLayout></ProtectedRoute>} />
          <Route path="/banks" element={<ProtectedRoute><AppLayout><BanksPage /></AppLayout></ProtectedRoute>} />
          <Route path="/beneficiaries" element={<ProtectedRoute><AppLayout><BeneficiariesPage /></AppLayout></ProtectedRoute>} />
          <Route path="/reports" element={<ProtectedRoute><AppLayout><ReportsPage /></AppLayout></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute adminOnly><AppLayout><AdminPage /></AppLayout></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
