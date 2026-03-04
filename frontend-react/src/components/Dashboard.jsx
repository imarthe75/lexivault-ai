import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { FileText, RefreshCw, Plus } from 'lucide-react';
import DocumentDetails from './DocumentDetails';
import UploadModal from './UploadModal';
import Toasts from './Toast';
import { FixedSizeList as List } from 'react-window';

function VirtualizedDocs({ documents = [], visibleCount = 0, onSelect }) {
    const [columns, setColumns] = useState(4);
    const containerRef = useRef(null);
    const [listWidth, setListWidth] = useState(800);

    const handleResize = useCallback(() => {
        const w = window.innerWidth;
        if (w < 640) setColumns(1);
        else if (w < 768) setColumns(2);
        else if (w < 1024) setColumns(3);
        else setColumns(4);
    }, []);

    useEffect(() => {
        handleResize();
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [handleResize]);

    useEffect(() => {
        const handle = () => {
            if (containerRef.current) setListWidth(containerRef.current.clientWidth);
            else setListWidth(Math.max(800, window.innerWidth - 48));
        };
        handle();
        window.addEventListener('resize', handle);
        return () => window.removeEventListener('resize', handle);
    }, []);

    const visibleDocs = documents.slice(0, visibleCount);
    const rowCount = Math.max(1, Math.ceil(visibleDocs.length / columns));
    const rowHeight = 240; // increase height to avoid content overflow/overlap
    const listHeight = Math.min(rowCount * rowHeight, 800);

    const Row = ({ index, style }) => {
        const start = index * columns;
        const items = [];
        for (let c = 0; c < columns; c++) {
            const doc = visibleDocs[start + c];
            items.push(
                <div key={c} className={`flex-1 ${c < columns - 1 ? 'mr-6' : ''}`}>
                    {doc ? (
                        <div
                            onClick={() => onSelect(doc)}
                            className="doc-card group flex flex-col h-full relative overflow-hidden p-4 bg-slate-800/20 rounded-lg"
                        >
                            <div className="absolute top-0 right-0 p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <div className="bg-slate-800/80 rounded-full p-1">
                                    <FileText className="w-4 h-4 text-sky-400" />
                                </div>
                            </div>

                            <div className="flex items-start gap-4 mb-4">
                                <div className="p-3 bg-sky-500/10 rounded-xl group-hover:bg-sky-500/20 transition-colors">
                                    <FileText className="w-8 h-8 text-sky-400" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <h3 className="font-semibold truncate text-lg leading-tight mb-1" title={doc.title}>
                                        {doc.title}
                                    </h3>
                                    <p className="text-xs text-slate-500 truncate">
                                        {doc.latest_version_info?.original_filename}
                                    </p>
                                </div>
                            </div>

                            <div className="mt-auto pt-4 border-t border-slate-700/50 flex justify-between items-center text-xs">
                                <span className="text-slate-400">
                                    {new Date(doc.last_modified_at).toLocaleDateString()}
                                </span>
                                <span className={`status-badge status-${doc.latest_version_info?.processed_status || 'pending'}`}>
                                    {doc.latest_version_info?.processed_status || 'pending'}
                                </span>
                            </div>
                        </div>
                    ) : (
                        <div className="h-full" />
                    )}
                </div>
            );
        }

        return (
            <div style={style} className="flex items-stretch">
                {items}
            </div>
        );
    };

    return (
        <div ref={containerRef}>
            {visibleDocs.length === 0 ? (
                <div className="col-span-full flex flex-col items-center justify-center py-20 text-slate-500 border-2 border-dashed border-slate-800 rounded-2xl">
                    <FileText className="w-16 h-16 mb-4 opacity-20" />
                    <p className="text-lg">No hay documentos aún</p>
                    <button
                        onClick={() => window.dispatchEvent(new CustomEvent('open-upload'))}
                        className="mt-4 text-sky-400 hover:text-sky-300 text-sm font-medium"
                    >
                        Subir el primero
                    </button>
                </div>
            ) : (
                <List
                    height={listHeight}
                    itemCount={rowCount}
                    itemSize={rowHeight}
                    width={listWidth}
                >
                    {Row}
                </List>
            )}
        </div>
    );
}

export default function Dashboard() {
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showUpload, setShowUpload] = useState(false);
    const [selectedDoc, setSelectedDoc] = useState(null);
    const [visibleCount, setVisibleCount] = useState(12);

    const fetchDocuments = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const res = await axios.get('/api/documents', {
                headers: { Authorization: `Bearer ${token}` }
            });
            setDocuments(res.data);
            return res.data;
        } catch (err) {
            console.error(err);
            return [];
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDocuments();
    }, []);

    useEffect(() => {
        const handler = () => setShowUpload(true);
        window.addEventListener('open-upload', handler);
        return () => window.removeEventListener('open-upload', handler);
    }, []);

    return (
        <div className="container mx-auto p-6 pb-20">
            <Toasts />
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-sky-400 to-indigo-400 bg-clip-text text-transparent">
                        Digital Vault
                    </h1>
                    <p className="text-slate-400 mt-1">Gestiona tus documentos seguros</p>
                </div>

                <div className="flex gap-3">
                    <button
                        onClick={fetchDocuments}
                        className="btn-secondary"
                        title="Actualizar lista"
                    >
                        <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                    <button
                        onClick={() => setShowUpload(!showUpload)}
                        className={`btn-primary shadow-lg shadow-sky-500/20 ${showUpload ? 'bg-slate-700 hover:bg-slate-600 border-slate-600' : ''}`}
                    >
                        <Plus className={`w-5 h-5 transition-transform ${showUpload ? 'rotate-45' : ''}`} />
                        {showUpload ? 'Cancelar' : 'Nuevo Documento'}
                    </button>
                </div>
            </div>

            {/* Upload Modal */}
            {showUpload && (
                <UploadModal
                    onUploadSuccess={async (createdDoc) => {
                        const docs = await fetchDocuments();
                        setShowUpload(false);
                        if (createdDoc) {
                            setSelectedDoc(createdDoc);
                        } else if (docs && docs.length > 0) {
                            // fallback: open the most recent document
                            setSelectedDoc(docs[0]);
                        }
                    }}
                    onClose={() => setShowUpload(false)}
                />
            )}

            {/* Documents Grid */}
            <div className="glass-panel p-6 min-h-[60vh]">
                <div className="flex items-center gap-2 mb-6 border-b border-slate-700/50 pb-4">
                    <FileText className="text-sky-400" />
                    <h2 className="text-xl font-bold">Mis Documentos</h2>
                    <span className="ml-auto text-sm text-slate-500">{documents.length} archivos</span>
                </div>

                {loading ? (
                    <div className="flex justify-center items-center h-64">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-400"></div>
                    </div>
                ) : (
                    <>
                        {/* Virtualized list: render rows with multiple columns per row */}
                        <VirtualizedDocs
                            documents={documents}
                            visibleCount={visibleCount}
                            onSelect={(d) => setSelectedDoc(d)}
                        />

                        {/* Mostrar más / paginación simple */}
                        {documents.length > visibleCount && (
                            <div className="mt-6 flex justify-center">
                                <button
                                    onClick={() => setVisibleCount(c => c + 12)}
                                    className="btn-secondary"
                                >
                                    Mostrar más
                                </button>
                            </div>
                        )}
                    </>
                )}
            </div>

            {selectedDoc && (
                <DocumentDetails
                    doc={selectedDoc}
                    onClose={() => setSelectedDoc(null)}
                />
            )}
        </div>
    );
}
