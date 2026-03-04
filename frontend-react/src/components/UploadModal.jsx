import { useState } from 'react';
import axios from 'axios';
import { Upload, X, Loader2, FileText } from 'lucide-react';

export default function UploadModal({ onClose, onUploadSuccess }) {
    const [uploading, setUploading] = useState(false);
    const [title, setTitle] = useState('');
    const [dragActive, setDragActive] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);


    const handleFileSelect = (file) => {
        if (!file) return;
        setSelectedFile(file);
        // Pre-fill title if empty, removing extension
        if (!title) {
            const nameWithoutExt = file.name.lastIndexOf('.') > 0
                ? file.name.substring(0, file.name.lastIndexOf('.'))
                : file.name;
            setTitle(nameWithoutExt);
        }
        setSuccessMessage('');
    };

    const handleUpload = async () => {
        if (!selectedFile) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('file', selectedFile);
        // Always send title if present, otherwise let backend decide (though we pre-filled it)
        if (title) formData.append('title', title);

        try {
            // Notify user and close modal immediately when upload starts
            window.dispatchEvent(new CustomEvent('upload-started', { detail: { message: 'Subida iniciada — procesando en segundo plano' } }));
            onClose();

            const token = localStorage.getItem('token');
            const res = await axios.post('/api/documents', formData, {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data'
                }
            });
            // Notify parent when upload completes (so it can refresh/open details)
            onUploadSuccess(res?.data);
            // Reset fields for next upload
            setSelectedFile(null);
            setTitle('');
        } catch (err) {
            console.error(err);
            alert('Error al subir documento');
        } finally {
            setUploading(false);
        }
    };

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    };

    const handleChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFileSelect(e.target.files[0]);
        }
    };

    return (
        <div
            onClick={onClose}
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                background: 'rgba(0,0,0,0.6)',
                backdropFilter: 'blur(6px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '16px',
                zIndex: 1000,
            }}
        >
            <div className="glass-panel" onClick={e => e.stopPropagation()} style={{ width: '100%', maxWidth: 520, padding: 20, position: 'relative' }}>
                <button onClick={onClose} style={{ position: 'absolute', right: 12, top: 12, color: 'rgba(148,163,184,0.9)', background: 'transparent', border: 'none' }}>
                    <X className="w-6 h-6" />
                </button>

                <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                    <Upload className="text-sky-400" /> Subir Documento
                </h2>



                <div className="space-y-4">
                    {/* File Drop Zone */}
                    {!selectedFile ? (
                        <label
                            className={`
                                border-2 border-dashed rounded-xl p-10
                                flex flex-col items-center justify-center cursor-pointer
                                transition-all
                                ${dragActive ? 'border-sky-400 bg-sky-400/10' : 'border-slate-700 hover:border-sky-400 hover:bg-sky-400/5'}
                            `}
                            onDragEnter={handleDrag}
                            onDragLeave={handleDrag}
                            onDragOver={handleDrag}
                            onDrop={handleDrop}
                        >
                            <input type="file" hidden onChange={handleChange} />
                            <Upload className="w-10 h-10 text-slate-400 mb-3" />
                            <p className="text-sm text-slate-300 font-medium">Arrastra tu archivo aquí</p>
                            <p className="text-xs text-slate-500 mt-1">o haz clic para seleccionar</p>
                        </label>
                    ) : (
                        <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700 flex items-center gap-3">
                            <div className="p-2 bg-sky-500/20 rounded-lg">
                                <FileText className="w-6 h-6 text-sky-400" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium truncate text-white">{selectedFile.name}</p>
                                <p className="text-xs text-slate-500">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                            </div>
                            <button
                                onClick={() => { setSelectedFile(null); setTitle(''); }}
                                className="text-slate-400 hover:text-red-400 transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    )}

                    {/* Title Input */}
                    <div>
                        <label className="block text-sm text-slate-400 mb-1">Título (Opcional)</label>
                        <input
                            type="text"
                            placeholder="Ej. Acta de Nacimiento"
                            className="input-clean w-full"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                        />
                        <p className="text-xs text-slate-500 mt-1">
                            Si el nombre del archivo es incorrecto, puedes cambiarlo aquí antes de subir.
                        </p>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 mt-6">
                        <button
                            onClick={onClose}
                            className="btn-secondary flex-1 justify-center"
                            disabled={uploading}
                        >
                            Cerrar
                        </button>
                        <button
                            onClick={handleUpload}
                            disabled={!selectedFile || uploading}
                            className={`btn-primary flex-1 justify-center ${(!selectedFile || uploading) ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            {uploading ? (
                                <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Subiendo...</>
                            ) : (
                                'Subir Archivo'
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
