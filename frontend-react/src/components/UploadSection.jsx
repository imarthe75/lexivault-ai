import { useState } from 'react';
import axios from 'axios';
import { Upload, X, Loader2, FileText, CheckCircle } from 'lucide-react';

export default function UploadSection({ onUploadSuccess, onClose }) {
    const [uploading, setUploading] = useState(false);
    const [title, setTitle] = useState('');
    const [dragActive, setDragActive] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);
    const [successMessage, setSuccessMessage] = useState('');

    const handleFileSelect = (file) => {
        if (!file) return;
        setSelectedFile(file);
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
        if (title) formData.append('title', title);

        try {
            const token = localStorage.getItem('token');
            await axios.post('/api/documents', formData, {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data'
                }
            });
            onUploadSuccess();
            setSuccessMessage('¡Archivo subido exitosamente!');

            setSelectedFile(null);
            setTitle('');
            // We don't close automatically allowing multiple uploads
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
        <div className="glass-panel p-6 mb-8 border border-sky-500/30 shadow-lg shadow-sky-500/10 relative animate-in fade-in slide-in-from-top-4 duration-300">
            <button onClick={onClose} className="absolute right-4 top-4 text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
            </button>

            <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                <Upload className="text-sky-400" /> Nuevo Documento
            </h2>

            {successMessage && (
                <div className="mb-6 p-3 bg-green-500/10 border border-green-500/50 rounded-xl text-green-300 text-sm flex items-center gap-2">
                    <CheckCircle className="w-5 h-5" />
                    <span>{successMessage}</span>
                    <button onClick={() => setSuccessMessage('')} className="ml-auto hover:text-white"><X className="w-4 h-4" /></button>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* File Drop Zone */}
                <div>
                    {!selectedFile ? (
                        <label
                            className={`
                                h-full min-h-[200px]
                                border-2 border-dashed rounded-xl p-8
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
                            <Upload className="w-12 h-12 text-slate-400 mb-4" />
                            <p className="text-lg text-slate-300 font-medium text-center">Arrastra tu archivo aquí</p>
                            <p className="text-sm text-slate-500 mt-2">o haz clic para seleccionar</p>
                        </label>
                    ) : (
                        <div className="h-full min-h-[200px] p-6 bg-slate-800/50 rounded-xl border border-slate-700 flex flex-col justify-center items-center gap-4 relative">
                            <button
                                onClick={() => { setSelectedFile(null); setTitle(''); }}
                                className="absolute right-3 top-3 text-slate-400 hover:text-red-400 transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>

                            <div className="p-4 bg-sky-500/20 rounded-full">
                                <FileText className="w-10 h-10 text-sky-400" />
                            </div>
                            <div className="text-center">
                                <p className="font-medium text-white text-lg break-all">{selectedFile.name}</p>
                                <p className="text-sm text-slate-500 mt-1">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                            </div>
                        </div>
                    )}
                </div>

                {/* Form Fields */}
                <div className="flex flex-col justify-center space-y-6">
                    <div>
                        <label className="block text-sm text-slate-400 mb-2">Título del Documento (Opcional)</label>
                        <input
                            type="text"
                            placeholder="Ej. Acta de Nacimiento"
                            className="input-clean w-full text-lg p-3"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                        />
                        <p className="text-xs text-slate-500 mt-2">
                            Puedes editar el nombre con el que se guardará el documento.
                        </p>
                    </div>

                    <div className="pt-2">
                        <button
                            onClick={handleUpload}
                            disabled={!selectedFile || uploading}
                            className={`btn-primary w-full justify-center py-3 text-lg ${(!selectedFile || uploading) ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            {uploading ? (
                                <><Loader2 className="w-6 h-6 animate-spin mr-2" /> Subiendo...</>
                            ) : (
                                'Subir Documento'
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
