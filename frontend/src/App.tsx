import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { CloudAccounts } from './pages/CloudAccounts';
import { Billing } from './pages/Billing';
import { Optimization } from './pages/Optimization';
import { Metrics } from './pages/Metrics';
import { Copilot } from './pages/Copilot';
import { Login } from './pages/Login';
import { Register } from './pages/Register';

const queryClient = new QueryClient();

// Protected Route wrapper checks authorization state
const ProtectedLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center text-white">
        Loading CloudPilot AI...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-background text-gray-100 flex">
      <Sidebar />
      <main className="flex-1 min-h-screen pl-64 bg-background">
        {children}
      </main>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Authenticated workspace routes */}
            <Route
              path="/"
              element={
                <ProtectedLayout>
                  <Dashboard />
                </ProtectedLayout>
              }
            />
            <Route
              path="/cloud"
              element={
                <ProtectedLayout>
                  <CloudAccounts />
                </ProtectedLayout>
              }
            />
            <Route
              path="/metrics"
              element={
                <ProtectedLayout>
                  <Metrics />
                </ProtectedLayout>
              }
            />
            <Route
              path="/billing"
              element={
                <ProtectedLayout>
                  <Billing />
                </ProtectedLayout>
              }
            />
            <Route
              path="/optimization"
              element={
                <ProtectedLayout>
                  <Optimization />
                </ProtectedLayout>
              }
            />
            <Route
              path="/copilot"
              element={
                <ProtectedLayout>
                  <Copilot />
                </ProtectedLayout>
              }
            />

            {/* Redirect fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
