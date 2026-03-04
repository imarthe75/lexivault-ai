import { useEffect, useState } from 'react';

export default function Toasts() {
    const [toasts, setToasts] = useState([]);

    useEffect(() => {
        const handler = (e) => {
            const id = Date.now() + Math.random();
            const msg = (e && e.detail && e.detail.message) || 'Operación en segundo plano';
            setToasts((t) => [...t, { id, msg }]);
            // auto remove
            setTimeout(() => {
                setToasts((t) => t.filter(x => x.id !== id));
            }, (e.detail && e.detail.duration) || 4000);
        };
        window.addEventListener('upload-started', handler);
        const authHandler = () => {
            const id = Date.now() + Math.random();
            const msg = 'Sesión expirada. Redirigiendo a login...';
            setToasts((t) => [...t, { id, msg }]);
            setTimeout(() => setToasts((t) => t.filter(x => x.id !== id)), 3000);
        };
        window.addEventListener('auth-unauthorized', authHandler);
        return () => {
            window.removeEventListener('upload-started', handler);
            window.removeEventListener('auth-unauthorized', authHandler);
        };
    }, []);

    if (toasts.length === 0) return null;

    return (
        <div style={{ position: 'fixed', top: 16, right: 16, zIndex: 1100, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {toasts.map(t => (
                <div key={t.id} style={{ minWidth: 200, background: 'rgba(15,23,42,0.9)', color: '#e6f9ff', padding: '10px 14px', borderRadius: 8, boxShadow: '0 6px 18px rgba(2,6,23,0.6)', border: '1px solid rgba(56,189,248,0.12)' }}>
                    {t.msg}
                </div>
            ))}
        </div>
    );
}
