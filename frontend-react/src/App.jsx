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

const isSubdomain = window.location.hostname === 'lexivault.casmart.internal';
const basePath = isSubdomain ? '/' : '/lexivault/';

const oidcConfig = {
  authority: "https://auth.casmart.internal/application/o/lexivault-ai/",
  client_id: "lexivault-ai",
  redirect_uri: window.location.origin + basePath,
  post_logout_redirect_uri: window.location.origin + basePath,
  response_type: "code",
  scope: "openid profile email",
};

const ProtectedRoute = ({ children }) => {
  const auth = useAuth();

  if (auth.isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-[#0f172a] relative overflow-hidden">
        {/* Background Blobs for Premium Feel */}
        <div className="fixed top-0 left-0 w-full h-full pointer-events-none z-0">
          <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-500/10 rounded-full blur-[120px]"></div>
          <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-500/5 rounded-full blur-[100px]"></div>
        </div>
        <div className="flex flex-col items-center gap-4 text-white relative z-10">
          <Loader2 className="animate-spin text-blue-400" size={48} />
          <p className="font-semibold animate-pulse text-blue-400 tracking-wider">Sincronizando Identidad CASMARTS...</p>
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
      <BrowserRouter basename={isSubdomain ? '/' : '/lexivault'}>
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
