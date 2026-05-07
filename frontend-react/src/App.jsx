import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from 'react-oidc-context';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import Vault from './components/Vault';
import Chat from './components/Chat';
import Extract from './components/Extract';
import Toasts from './components/Toast';
import { Loader2 } from 'lucide-react';

const oidcConfig = {
  authority: "https://arquitectura.casmart.internal/application/o/lexivault-ai/",
  client_id: "lexivault-ai",
  redirect_uri: window.location.origin + "/lexivault/",
  post_logout_redirect_uri: window.location.origin + "/lexivault/",
  response_type: "code",
  scope: "openid profile email",
};

const ProtectedRoute = ({ children }) => {
  const auth = useAuth();

  if (auth.isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-primary">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="text-white animate-spin" size={48} />
          <p className="text-white font-medium animate-pulse">Sincronizando Identidad CASMARTS...</p>
        </div>
      </div>
    );
  }

  if (!auth.isAuthenticated) {
    auth.signinRedirect();
    return null;
  }

  return children;
};

const App = () => {
  return (
    <AuthProvider {...oidcConfig}>
      <Toasts />
      <BrowserRouter basename="/lexivault">
        <Routes>
          <Route path="/" element={
            <ProtectedRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/vault" element={
            <ProtectedRoute>
              <Layout>
                <Vault />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/chat" element={
            <ProtectedRoute>
              <Layout>
                <Chat />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/extract" element={
            <ProtectedRoute>
              <Layout>
                <Extract />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/settings" element={
            <ProtectedRoute>
              <Layout>
                <div className="premium-card">
                  <h2>Configuración de Cuenta</h2>
                  <p className="text-text-muted mt-2">La gestión de identidad y seguridad está centralizada en Authentik.</p>
                </div>
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
