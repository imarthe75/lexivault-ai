import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from 'react-oidc-context';
import { 
  LayoutDashboard, 
  Database, 
  MessageSquare, 
  FileSearch, 
  Settings, 
  LogOut,
  Vault,
  Bell,
  User
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const SidebarItem = ({ to, icon: Icon, children }) => (
  <NavLink 
    to={to} 
    className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
  >
    <Icon size={20} />
    <span>{children}</span>
  </NavLink>
);

const Layout = ({ children }) => {
  const auth = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    auth.signoutRedirect();
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <Vault size={32} className="text-white" />
          <div className="flex flex-col">
            <span className="leading-tight">LexiVault</span>
            <span className="text-[10px] uppercase tracking-widest opacity-60">Digital Assets</span>
          </div>
        </div>

        <nav className="flex flex-col gap-2 flex-1 mt-8">
          <SidebarItem to="/" icon={LayoutDashboard}>Dashboard</SidebarItem>
          <SidebarItem to="/vault" icon={Database}>Bóveda Digital</SidebarItem>
          <SidebarItem to="/chat" icon={MessageSquare}>Asistente IA</SidebarItem>
          <SidebarItem to="/extract" icon={FileSearch}>Extracción NER</SidebarItem>
          <div className="mt-auto border-t border-white/10 pt-4 flex flex-col gap-2">
            <SidebarItem to="/settings" icon={Settings}>Configuración</SidebarItem>
            <button onClick={handleLogout} className="nav-link w-full text-left border-none bg-transparent cursor-pointer">
              <LogOut size={20} />
              <span>Cerrar Sesión</span>
            </button>
          </div>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl">Bienvenido, {auth.user?.profile?.name || auth.user?.profile?.preferred_username}</h1>
            <p className="text-text-muted text-sm">Gestionando la inteligencia documental de CASMARTS</p>
          </div>
          
          <div className="flex items-center gap-4">
            <button className="p-2 rounded-full hover:bg-white/50 transition-colors relative">
              <Bell size={20} />
              <span className="absolute top-2 right-2 w-2 h-2 bg-error rounded-full border-2 border-white"></span>
            </button>
            <div className="flex items-center gap-3 bg-white py-1.5 px-4 rounded-full border border-border">
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white text-xs font-bold">
                {auth.user?.profile?.name?.[0] || 'U'}
              </div>
              <div className="hidden md:block">
                <p className="text-xs font-bold leading-tight">{auth.user?.profile?.name || 'Usuario'}</p>
                <p className="text-[10px] text-text-muted leading-tight">Administrador</p>
              </div>
            </div>
          </div>
        </header>

        <AnimatePresence mode="wait">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
};

export default Layout;
