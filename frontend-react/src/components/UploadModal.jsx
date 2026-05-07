import React, { useState } from 'react';
import { X, Upload, FileText, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import axios from '../axiosSetup';

const UploadModal = ({ isOpen, onClose }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('idle'); // idle, uploading, success, error

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setStatus('idle');
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setStatus('uploading');
    setProgress(10);

    const formData = new FormData();
    formData.append('file', file);

    try {
      await axios.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(percentCompleted);
        }
      });
      setStatus('success');
      setTimeout(() => {
        onClose();
      }, 2000);
    } catch (error) {
      console.error("Error uploading file", error);
      setStatus('error');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-primary/20 backdrop-blur-sm animate-fade-in">
      <div className="premium-card w-full max-w-lg bg-white relative">
        <button 
          onClick={onClose}
          className="absolute right-6 top-6 p-2 hover:bg-slate-100 rounded-full transition-colors"
        >
          <X size={20} />
        </button>

        <h2 className="text-2xl mb-2">Subir Documento</h2>
        <p className="text-sm text-text-muted mb-8">Los archivos serán encriptados y procesados por IA.</p>

        <div className="flex flex-col gap-6">
          {status === 'success' ? (
            <div className="flex flex-col items-center gap-4 py-12">
              <div className="w-20 h-20 rounded-full bg-success/10 flex items-center justify-center text-success">
                <CheckCircle size={48} />
              </div>
              <p className="font-bold text-success">¡Documento subido con éxito!</p>
              <p className="text-xs text-text-muted text-center max-w-[200px]">
                Iniciando indexación semántica en segundo plano...
              </p>
            </div>
          ) : status === 'error' ? (
            <div className="flex flex-col items-center gap-4 py-12">
              <div className="w-20 h-20 rounded-full bg-error/10 flex items-center justify-center text-error">
                <AlertCircle size={48} />
              </div>
              <p className="font-bold text-error">Error al subir el archivo</p>
              <button 
                onClick={() => setStatus('idle')}
                className="text-xs text-primary font-bold hover:underline"
              >
                Reintentar
              </button>
            </div>
          ) : (
            <>
              <div className="border-2 border-dashed border-border rounded-3xl p-12 text-center hover:border-primary transition-colors relative group">
                <input 
                  type="file" 
                  className="absolute inset-0 opacity-0 cursor-pointer" 
                  onChange={handleFileChange}
                />
                <div className="flex flex-col items-center gap-4">
                  <div className="w-16 h-16 rounded-2xl bg-primary/5 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                    <Upload size={32} />
                  </div>
                  <div>
                    <p className="font-bold text-sm">{file ? file.name : 'Arrastra o selecciona un archivo'}</p>
                    <p className="text-xs text-text-muted mt-1">PDF, Imágenes o Texto Plano</p>
                  </div>
                </div>
              </div>

              {status === 'uploading' && (
                <div className="flex flex-col gap-2">
                  <div className="flex justify-between text-xs font-bold text-primary">
                    <span>Subiendo a SeaweedFS...</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-primary h-full transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              <button 
                className="btn btn-primary w-full mt-4"
                disabled={!file || uploading}
                onClick={handleUpload}
              >
                {uploading ? <Loader2 className="animate-spin" size={20} /> : <Upload size={20} />}
                <span>{uploading ? 'Subiendo...' : 'Iniciar Carga Segura'}</span>
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default UploadModal;
