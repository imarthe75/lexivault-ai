import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  Upload, 
  MoreVertical, 
  FileText, 
  ExternalLink, 
  Download, 
  Trash2, 
  Send,
  Eye
} from 'lucide-react';
import axios from '../axiosSetup';
import UploadModal from './UploadModal';

const DocumentCard = ({ doc, onExport, onDelete, onView }) => (
  <tr className="hover:bg-slate-50 transition-colors group">
    <td className="py-4 px-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-primary/5 flex items-center justify-center text-primary">
          <FileText size={20} />
        </div>
        <div>
          <p className="text-sm font-bold text-primary truncate max-w-[300px]">{doc.original_filename}</p>
          <p className="text-[10px] text-text-muted">{doc.mimetype}</p>
        </div>
      </div>
    </td>
    <td className="py-4 px-4">
      <span className={`badge ${doc.processed_status === 'indexed' ? 'badge-success' : 'badge-warn'}`}>
        {doc.processed_status}
      </span>
    </td>
    <td className="py-4 px-4 text-sm text-text-muted">
      {new Date(doc.created_at).toLocaleDateString()}
    </td>
    <td className="py-4 px-4 text-sm font-medium">
      {(doc.size_bytes / (1024 * 1024)).toFixed(2)} MB
    </td>
    <td className="py-4 px-4 text-right">
      <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <button 
          onClick={() => onView(doc)}
          className="p-2 hover:bg-primary/10 rounded-lg text-primary transition-colors" 
          title="Ver Detalles"
        >
          <Eye size={18} />
        </button>
        <button 
          onClick={() => onExport(doc)}
          className="p-2 hover:bg-success/10 rounded-lg text-success transition-colors" 
          title="Exportar a Paperless"
        >
          <Send size={18} />
        </button>
        <button 
          onClick={() => onDelete(doc.id)}
          className="p-2 hover:bg-error/10 rounded-lg text-error transition-colors" 
          title="Eliminar"
        >
          <Trash2 size={18} />
        </button>
      </div>
    </td>
  </tr>
);

const Vault = () => {
  const [documents, setDocuments] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/documents/');
      setDocuments(response.data);
    } catch (error) {
      console.error("Error fetching documents", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleExportToPaperless = async (doc) => {
    try {
      // Llamada al backend para mover el archivo a la carpeta consume de Paperless
      await axios.post(`/documents/${doc.id}/export-paperless`);
      alert(`Documento "${doc.original_filename}" enviado a Paperless correctamente.`);
    } catch (error) {
      console.error("Error exporting to paperless", error);
      alert("Error al exportar a Paperless.");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("¿Estás seguro de que deseas eliminar este documento?")) return;
    try {
      await axios.delete(`/documents/${id}`);
      setDocuments(documents.filter(d => d.id !== id));
    } catch (error) {
      console.error("Error deleting document", error);
    }
  };

  const filteredDocs = documents.filter(doc => 
    doc.original_filename.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-8">
      {/* Search & Actions Bar */}
      <div className="flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="relative w-full md:w-96">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" size={20} />
          <input 
            type="text" 
            placeholder="Buscar en la bóveda..." 
            className="form-input pl-12"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        
        <div className="flex gap-3 w-full md:w-auto">
          <button className="btn btn-secondary flex-1 md:flex-none">
            <Filter size={18} /> Filtros
          </button>
          <button 
            onClick={() => setIsUploadModalOpen(true)}
            className="btn btn-primary flex-1 md:flex-none"
          >
            <Upload size={18} /> Subir Documento
          </button>
        </div>
      </div>

      {/* Documents Table */}
      <div className="premium-card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-bottom border-border">
                <th className="py-4 px-4 text-xs font-bold uppercase tracking-wider text-text-muted">Nombre del Archivo</th>
                <th className="py-4 px-4 text-xs font-bold uppercase tracking-wider text-text-muted">Estado IA</th>
                <th className="py-4 px-4 text-xs font-bold uppercase tracking-wider text-text-muted">Fecha de Carga</th>
                <th className="py-4 px-4 text-xs font-bold uppercase tracking-wider text-text-muted">Tamaño</th>
                <th className="py-4 px-4 text-xs font-bold uppercase tracking-wider text-text-muted text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="5" className="py-20 text-center text-text-muted italic">Consultando registros en el core...</td>
                </tr>
              ) : filteredDocs.length > 0 ? (
                filteredDocs.map(doc => (
                  <DocumentCard 
                    key={doc.id} 
                    doc={doc} 
                    onExport={handleExportToPaperless}
                    onDelete={handleDelete}
                    onView={(d) => console.log("View", d)}
                  />
                ))
              ) : (
                <tr>
                  <td colSpan="5" className="py-20 text-center text-text-muted">No se encontraron documentos.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {isUploadModalOpen && (
        <UploadModal 
          isOpen={isUploadModalOpen} 
          onClose={() => {
            setIsUploadModalOpen(false);
            fetchDocuments();
          }} 
        />
      )}
    </div>
  );
};

export default Vault;
