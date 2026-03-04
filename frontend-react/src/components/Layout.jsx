import { Outlet, useNavigate } from 'react-router-dom';
import { Shield, LogOut } from 'lucide-react';

export default function Layout({ setAuth }) {
    const navigate = useNavigate();

    const handleLogout = () => {
        localStorage.removeItem('token');
        setAuth(false);
        navigate('/login');
    };

    return (
        <div className="min-h-screen flex flex-col">
            <nav className="glass-panel m-4 p-4 flex justify-between items-center rounded-xl">
                <div className="flex items-center gap-2 font-bold text-xl">
                    <Shield className="text-sky-400" /> Digital Vault
                </div>
                <div className="flex items-center gap-4">
                    <span className="text-slate-400 text-sm hidden sm:inline">Usuario Conectado</span>
                    <button onClick={handleLogout} className="btn-icon" title="Cerrar Sesión">
                        <LogOut className="w-5 h-5" />
                    </button>
                </div>
            </nav>

            <main className="flex-1 container">
                <Outlet />
            </main>
        </div>
    );
}
