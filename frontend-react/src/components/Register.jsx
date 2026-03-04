import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, User, Lock, Mail } from 'lucide-react';
import axios from 'axios';

export default function Register() {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await axios.post('/api/register', { username, email, password });
            alert('Registro exitoso. Por favor inicia sesión.');
            navigate('/login');
        } catch (err) {
            setError(err.response?.data?.message || 'Error al registrarse');
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-box glass-panel">
                <div className="mb-8">
                    <Shield className="w-12 h-12 text-sky-400 mx-auto mb-4" />
                    <h1 className="text-2xl font-bold mb-2">Crear Cuenta</h1>
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
                    <div className="relative mb-4">
                        <Mail className="absolute left-3 top-3 text-slate-400 w-5 h-5" />
                        <input
                            type="email"
                            placeholder="Email"
                            className="input-clean pl-10"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
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
                    <button type="submit" className="btn-secondary w-full justify-center">
                        Registrarse
                    </button>
                </form>

                <p className="mt-6 text-slate-400 text-sm">
                    ¿Ya tienes cuenta? <Link to="/login" className="text-sky-400 hover:text-sky-300">Inicia Sesión</Link>
                </p>
            </div>
        </div>
    );
}
