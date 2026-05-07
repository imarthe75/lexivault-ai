import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Cpu, 
  Database, 
  TrendingUp, 
  Clock, 
  ArrowRight,
  Upload,
  Search
} from 'lucide-react';
import axios from '../axiosSetup';
import { Link } from 'react-router-dom';

const StatCard = ({ title, value, subtext, icon: Icon, color }) => (
  <div className="premium-card flex flex-col gap-4">
    <div className="flex justify-between items-start">
      <div className={`p-3 rounded-2xl ${color} bg-opacity-10`}>
        <Icon className={color.replace('bg-', 'text-')} size={24} />
      </div>
      <span className="text-success text-xs font-bold flex items-center gap-1 bg-success/10 py-1 px-2 rounded-full">
        <TrendingUp size={12} /> +12%
      </span>
    </div>
    <div>
      <h3 className="text-3xl font-bold">{value}</h3>
      <p className="text-text-muted text-sm font-medium">{title}</p>
    </div>
    <div className="text-[10px] text-text-muted border-t border-border pt-3">
      {subtext}
    </div>
  </div>
);

const RecentDocRow = ({ doc }) => (
  <div className="flex items-center justify-between p-4 hover:bg-slate-50 rounded-2xl transition-colors cursor-pointer border border-transparent hover:border-border">
    <div className="flex items-center gap-4">
      <div className="w-10 h-10 rounded-xl bg-primary/5 flex items-center justify-center text-primary">
        <FileText size={20} />
      </div>
      <div>
        <p className="text-sm font-bold truncate max-w-[200px]">{doc.original_filename}</p>
        <p className="text-[10px] text-text-muted">{new Date(doc.created_at).toLocaleDateString()}</p>
      </div>
    </div>
    <div className="flex items-center gap-6">
      <span className={`badge ${doc.processed_status === 'indexed' ? 'badge-success' : 'badge-warn'}`}>
        {doc.processed_status}
      </span>
      <ArrowRight size={16} className="text-text-muted" />
    </div>
  </div>
);

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalDocs: 0,
    indexedDocs: 0,
    storageUsed: '0 MB',
    avgProcessingTime: '4.2s'
  });
  const [recentDocs, setRecentDocs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await axios.get('/documents/');
        setRecentDocs(response.data.slice(0, 5));
        setStats(prev => ({
          ...prev,
          totalDocs: response.data.length,
          indexedDocs: response.data.filter(d => d.processed_status === 'indexed').length,
          storageUsed: `${(response.data.reduce((acc, d) => acc + (d.size_bytes || 0), 0) / (1024 * 1024)).toFixed(2)} MB`
        }));
      } catch (error) {
        console.error("Error fetching dashboard data", error);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, []);

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      {/* Stats Section */}
      <StatCard 
        title="Documentos Totales" 
        value={stats.totalDocs} 
        subtext="Total de archivos en la bóveda"
        icon={Database}
        color="bg-primary"
      />
      <StatCard 
        title="Indexados con IA" 
        value={stats.indexedDocs} 
        subtext="Listos para búsqueda semántica"
        icon={Cpu}
        color="bg-success"
      />
      <StatCard 
        title="Espacio Utilizado" 
        value={stats.storageUsed} 
        subtext="Almacenado en SeaweedFS"
        icon={FileText}
        color="bg-info"
      />
      <StatCard 
        title="Tiempo de Procesamiento" 
        value={stats.avgProcessingTime} 
        subtext="Media de extracción NER/OCR"
        icon={Clock}
        color="bg-warn"
      />

      {/* Main Grid Area */}
      <div className="md:col-span-3">
        <div className="premium-card">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl">Actividad Reciente</h2>
            <Link to="/vault" className="text-primary text-sm font-bold hover:underline flex items-center gap-2">
              Ver todo <ArrowRight size={14} />
            </Link>
          </div>
          
          <div className="flex flex-col gap-2">
            {loading ? (
              <div className="py-20 text-center text-text-muted">Cargando inteligencia documental...</div>
            ) : recentDocs.length > 0 ? (
              recentDocs.map(doc => <RecentDocRow key={doc.id} doc={doc} />)
            ) : (
              <div className="py-20 text-center text-text-muted border-2 border-dashed border-border rounded-3xl">
                No hay documentos recientes. ¡Comienza subiendo uno!
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right Sidebar Area */}
      <div className="md:col-span-1 flex flex-col gap-6">
        <div className="premium-card bg-primary text-white border-none">
          <h3 className="text-white mb-2">Acceso Rápido</h3>
          <p className="text-white/60 text-xs mb-6">Herramientas inteligentes de gestión</p>
          
          <div className="flex flex-col gap-3">
            <Link to="/vault" className="btn btn-primary bg-white/10 hover:bg-white/20 w-full justify-start text-sm">
              <Upload size={18} /> Subir Documento
            </Link>
            <Link to="/chat" className="btn btn-primary bg-white/10 hover:bg-white/20 w-full justify-start text-sm">
              <Search size={18} /> Búsqueda IA
            </Link>
            <Link to="/extract" className="btn btn-primary bg-white/10 hover:bg-white/20 w-full justify-start text-sm">
              <Cpu size={18} /> Extraer Acta
            </Link>
          </div>
        </div>

        <div className="premium-card border-dashed">
          <h4 className="text-sm mb-4 flex items-center gap-2">
            <div className="w-2 h-2 bg-success rounded-full animate-pulse"></div>
            Estado del Sistema
          </h4>
          <div className="flex flex-col gap-4">
            <div className="flex justify-between text-xs">
              <span className="text-text-muted">NVIDIA NIM</span>
              <span className="font-bold text-success">Online</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-text-muted">SeaweedFS</span>
              <span className="font-bold text-success">Online</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-text-muted">Celery Worker</span>
              <span className="font-bold text-success">Active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
