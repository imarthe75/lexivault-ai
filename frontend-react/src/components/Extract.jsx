import React, { useState } from 'react';
import { Cpu, Search, FileText, CheckCircle, AlertCircle, Loader2, Download, Send } from 'lucide-react';
import axios from '../axiosSetup';

const Extract = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResult(null);
    setError(null);
  };

  const handleProcess = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Endpoint especializado para extracción NER de actas
      const response = await axios.post('/documents/process-birth-certificate', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(response.data.extracted_data);
    } catch (error) {
      console.error("Error extracting data", error);
      setError("No se pudo procesar el documento. Asegúrate de que sea un PDF de acta de nacimiento válido.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      {/* Upload Section */}
      <div className="flex flex-col gap-6">
        <div className="premium-card">
          <h2 className="text-xl mb-4 flex items-center gap-2">
            <Cpu className="text-primary" /> Extracción Inteligente NER
          </h2>
          <p className="text-sm text-text-muted mb-8">
            Sube un acta de nacimiento para extraer automáticamente los datos estructurados utilizando el motor NLP de spaCy y NVIDIA NIM.
          </p>

          <div className="border-2 border-dashed border-border rounded-3xl p-12 text-center hover:border-primary transition-colors cursor-pointer relative group">
            <input 
              type="file" 
              className="absolute inset-0 opacity-0 cursor-pointer" 
              onChange={handleFileChange}
              accept=".pdf,.png,.jpg,.jpeg"
            />
            <div className="flex flex-col items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-primary/5 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                <FileText size={32} />
              </div>
              <div>
                <p className="font-bold text-sm">{file ? file.name : 'Selecciona un documento'}</p>
                <p className="text-xs text-text-muted mt-1">{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : 'PDF, PNG o JPG (Max 10MB)'}</p>
              </div>
            </div>
          </div>

          <button 
            className="btn btn-primary w-full mt-6"
            onClick={handleProcess}
            disabled={!file || loading}
          >
            {loading ? <Loader2 className="animate-spin" size={20} /> : <Cpu size={20} />}
            <span>{loading ? 'Procesando Inteligencia...' : 'Iniciar Extracción NER'}</span>
          </button>
        </div>

        {error && (
          <div className="premium-card bg-error/5 border-error/20 flex items-start gap-4 p-6">
            <AlertCircle className="text-error shrink-0" />
            <div>
              <p className="text-sm font-bold text-error">Error de Procesamiento</p>
              <p className="text-xs text-error/80 mt-1">{error}</p>
            </div>
          </div>
        )}
      </div>

      {/* Result Section */}
      <div className="flex flex-col gap-6">
        {result ? (
          <div className="premium-card animate-fade-in">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl">Datos Estructurados</h2>
              <span className="badge badge-success flex items-center gap-1">
                <CheckCircle size={12} /> Verificado por IA
              </span>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {Object.entries(result).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center p-4 bg-slate-50 rounded-2xl border border-transparent hover:border-border transition-colors">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">
                    {key.replace(/_/g, ' ')}
                  </span>
                  <span className="text-sm font-bold text-primary">
                    {value || <span className="text-error/50 italic">No detectado</span>}
                  </span>
                </div>
              ))}
            </div>

            <div className="mt-8 flex gap-3">
              <button className="btn btn-secondary flex-1 text-sm">
                <Download size={18} /> Descargar JSON
              </button>
              <button className="btn btn-primary flex-1 text-sm">
                <Send size={18} /> Enviar a Bóveda
              </button>
            </div>
          </div>
        ) : (
          <div className="premium-card h-full flex flex-col items-center justify-center text-center p-12 border-dashed">
            <div className="w-20 h-20 rounded-full bg-slate-50 flex items-center justify-center text-text-muted mb-4">
              <Cpu size={40} />
            </div>
            <h3 className="text-text-muted">Esperando procesamiento</h3>
            <p className="text-xs text-text-muted max-w-[240px] mt-2">
              Sube un documento en el panel de la izquierda para ver los resultados de la extracción aquí.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Extract;
