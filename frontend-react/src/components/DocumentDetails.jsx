import { X, Download, Wand2 } from 'lucide-react';
import axios from 'axios';

export default function DocumentDetails({ doc, onClose }) {
    const latest = doc.latest_version_info;
    const attributes = latest?.attributes || [];

    const handleDownload = async () => {
        if (!latest) return;
        try {
            const token = localStorage.getItem('token');
            const res = await axios.get(`/api/documents/versions/${latest.id}/download`, {
                headers: { Authorization: `Bearer ${token}` },
                responseType: 'blob'
            });
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', latest.original_filename);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            alert('Error al descargar');
        }
    };

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
            <div className="glass-panel w-full max-w-3xl max-h-[90vh] overflow-y-auto p-6 relative" onClick={e => e.stopPropagation()}>
                <button onClick={onClose} className="absolute right-4 top-4 text-slate-400 hover:text-white">
                    <X className="w-6 h-6" />
                </button>

                <h2 className="text-2xl font-bold mb-6 pr-8">{doc.title}</h2>

                <div className="grid md:grid-cols-2 gap-8">
                    {/* General Info */}
                    <div>
                        <h3 className="text-sky-400 font-semibold mb-3 uppercase text-sm">Información General</h3>
                        <div className="space-y-3 text-sm">
                            <div className="flex justify-between border-b border-slate-700 pb-2">
                                <span className="text-slate-400">Archivo</span>
                                <span>{latest?.original_filename}</span>
                            </div>
                            <div className="flex justify-between border-b border-slate-700 pb-2">
                                <span className="text-slate-400">Estado</span>
                                <span className={`status-badge status-${latest?.processed_status}`}>{latest?.processed_status}</span>
                            </div>
                            <div className="flex justify-between border-b border-slate-700 pb-2">
                                <span className="text-slate-400">Subido</span>
                                <span>{new Date(latest?.upload_timestamp).toLocaleString()}</span>
                            </div>
                        </div>

                        <button onClick={handleDownload} className="btn-secondary w-full mt-6">
                            <Download className="w-4 h-4" /> Descargar Archivo
                        </button>
                    </div>

                    {/* Extracted Attributes */}
                    <div>
                        <h3 className="text-sky-400 font-semibold mb-3 uppercase text-sm flex items-center gap-2">
                            <Wand2 className="w-4 h-4" /> Datos Extraídos (NER)
                        </h3>

                        {attributes.length > 0 ? (
                            <div className="grid gap-3">
                                {attributes.map((attr, idx) => (
                                    <div key={idx} className="bg-white/5 p-3 rounded-lg">
                                        <div className="text-xs text-sky-400 uppercase font-bold mb-1">{attr.key.replace(/_/g, ' ')}</div>
                                        <div className="text-sm font-medium break-words">{attr.value}</div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-slate-500 text-center py-8 bg-white/5 rounded-lg border border-dashed border-slate-700">
                                No hay datos extraídos disponibles.
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
