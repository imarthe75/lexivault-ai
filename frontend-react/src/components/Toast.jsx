import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, CheckCircle, AlertCircle, Info, X } from 'lucide-react';

const ToastItem = ({ toast, onRemove }) => {
  const icons = {
    success: <CheckCircle className="text-success" size={18} />,
    error: <AlertCircle className="text-error" size={18} />,
    info: <Info className="text-primary" size={18} />,
    warn: <Bell className="text-warn" size={18} />
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 50, scale: 0.9 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 20, scale: 0.9 }}
      className="premium-card flex items-center gap-4 p-4 min-w-[320px] bg-white border-primary/10"
    >
      <div className={`p-2 rounded-xl bg-slate-50`}>
        {icons[toast.type || 'info']}
      </div>
      <div className="flex-1">
        <p className="text-xs font-bold text-primary">{toast.title || 'Notificación'}</p>
        <p className="text-[10px] text-text-muted mt-0.5">{toast.msg}</p>
      </div>
      <button 
        onClick={() => onRemove(toast.id)}
        className="p-1 hover:bg-slate-100 rounded-full text-text-muted transition-colors"
      >
        <X size={14} />
      </button>
    </motion.div>
  );
};

const Toasts = () => {
  const [toasts, setToasts] = useState([]);

  const addToast = (toast) => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { ...toast, id }]);
    setTimeout(() => {
      setToasts((t) => t.filter(x => x.id !== id));
    }, toast.duration || 5000);
  };

  useEffect(() => {
    const handler = (e) => {
      addToast({
        title: e.detail?.title || 'Información',
        msg: e.detail?.message || 'Operación en curso',
        type: e.detail?.type || 'info'
      });
    };

    window.addEventListener('app-notify', handler);
    return () => window.removeEventListener('app-notify', handler);
  }, []);

  return (
    <div className="fixed top-6 right-6 z-[2000] flex flex-col gap-3 pointer-events-none">
      <AnimatePresence>
        {toasts.map(t => (
          <div key={t.id} className="pointer-events-auto">
            <ToastItem 
              toast={t} 
              onRemove={(id) => setToasts((prev) => prev.filter(x => x.id !== id))} 
            />
          </div>
        ))}
      </AnimatePresence>
    </div>
  );
};

export default Toasts;
