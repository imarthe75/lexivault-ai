import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, User, Lock, ArrowRight } from 'lucide-react';
import axios from 'axios';

import logo from '../assets/lexivault-logo.png';

export default function Login({ setAuth }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const res = await axios.post('/api/login', { username, password });
            localStorage.setItem('token', res.data.access_token);
            setAuth(true);
            navigate('/');
        } catch (err) {
            setError(err.response?.data?.message || 'Error al iniciar sesión');
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-box glass-panel text-center">
                <div className="mb-8">
                    <img src={logo} alt="LexiVault" className="w-20 h-20 mx-auto mb-4 object-contain animate-pulse-slow" />
                    <h1 className="text-3xl font-bold mb-2 bg-gradient-to-r from-sky-400 to-emerald-400 bg-clip-text text-transparent">LexiVault AI</h1>
                    <p className="text-slate-400">Intelligent Document Vault & Automation</p>
                </div>

                {error && <div className="bg-red-500/20 text-red-400 p-3 rounded mb-4">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="relative mb-4">
                        <User className="absolute left-3 top-3 text-slate-400 w-5 h-5" />
                        <input
                            type="text"
                            placeholder="Usuario"
                            className="input-clean pl-10"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                        />
                    </div>
                    <div className="relative mb-6">
                        <Lock className="absolute left-3 top-3 text-slate-400 w-5 h-5" />
                        <input
                            type="password"
                            placeholder="Contraseña"
                            className="input-clean pl-10"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>
                    <button type="submit" className="btn-primary w-full justify-center">
                        Ingresar <ArrowRight className="w-4 h-4" />
                    </button>
                </form>

                <p className="mt-6 text-slate-400 text-sm">
                    ¿No tienes cuenta? <Link to="/register" className="text-sky-400 hover:text-sky-300">Regístrate</Link>
                </p>
            </div>
        </div>
    );
}
