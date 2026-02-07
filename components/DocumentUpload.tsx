import React, { useState, useCallback } from 'react';
import { Upload, FileText, AlertTriangle, CheckCircle2, Trash2, X } from 'lucide-react';
import { uploadDocument, getDocuments, deleteDocument, DocumentInfo } from '../services/geminiService';

interface DocumentUploadProps {
    onDocumentsChange?: () => void;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({ onDocumentsChange }) => {
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [documents, setDocuments] = useState<DocumentInfo[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    const loadDocuments = useCallback(async () => {
        try {
            const docs = await getDocuments();
            setDocuments(docs);
        } catch (e) {
            console.error('Failed to load documents:', e);
        }
    }, []);

    React.useEffect(() => {
        loadDocuments();
    }, [loadDocuments]);

    const handleDragEnter = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleDrop = async (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const files = Array.from(e.dataTransfer.files);
        await handleFiles(files);
    };

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files || []);
        await handleFiles(files);
    };

    const handleFiles = async (files: File[]) => {
        setError(null);
        setSuccessMessage(null);

        for (const file of files) {
            // Validate file type
            const validTypes = ['.pdf', '.docx', '.doc', '.txt', '.md'];
            const ext = '.' + file.name.split('.').pop()?.toLowerCase();

            if (!validTypes.includes(ext)) {
                setError(`Dateityp nicht unterstützt: ${ext}. Erlaubt: ${validTypes.join(', ')}`);
                continue;
            }

            // Validate file size (max 50MB)
            if (file.size > 50 * 1024 * 1024) {
                setError('Datei zu groß. Maximum: 50MB');
                continue;
            }

            setIsUploading(true);
            setUploadProgress(0);

            try {
                // Simulate progress (real progress would need XHR)
                const progressInterval = setInterval(() => {
                    setUploadProgress(p => Math.min(p + 10, 90));
                }, 200);

                const result = await uploadDocument(file);

                clearInterval(progressInterval);
                setUploadProgress(100);

                const msg = result.pii_detected
                    ? `✓ ${file.name} hochgeladen. ⚠️ PII erkannt und maskiert.`
                    : `✓ ${file.name} erfolgreich verarbeitet (${result.chunk_count} Chunks)`;

                setSuccessMessage(msg);
                await loadDocuments();
                onDocumentsChange?.();

            } catch (e) {
                setError(`Fehler beim Hochladen: ${e instanceof Error ? e.message : 'Unbekannter Fehler'}`);
            } finally {
                setIsUploading(false);
                setUploadProgress(0);
            }
        }
    };

    const handleDeleteDocument = async (docId: string, filename: string) => {
        if (!confirm(`Dokument "${filename}" wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.`)) {
            return;
        }

        try {
            await deleteDocument(docId);
            setSuccessMessage(`${filename} wurde gelöscht`);
            await loadDocuments();
            onDocumentsChange?.();
        } catch (e) {
            setError('Fehler beim Löschen');
        }
    };

    return (
        <div className="space-y-6">
            {/* Upload Area */}
            <div
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                className={`
          relative border-2 border-dashed rounded-2xl p-8 text-center transition-all
          ${isDragging
                        ? 'border-brand-500 bg-brand-500/10'
                        : 'border-white/20 hover:border-white/40 bg-white/5'
                    }
          ${isUploading ? 'pointer-events-none opacity-60' : 'cursor-pointer'}
        `}
            >
                <input
                    type="file"
                    onChange={handleFileSelect}
                    accept=".pdf,.docx,.doc,.txt,.md"
                    multiple
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    disabled={isUploading}
                />

                <Upload className={`w-12 h-12 mx-auto mb-4 ${isDragging ? 'text-brand-500' : 'text-gray-400'}`} />

                <h3 className="text-lg font-semibold text-white mb-2">
                    {isDragging ? 'Datei hier ablegen' : 'Dokumente hochladen'}
                </h3>
                <p className="text-sm text-gray-400">
                    PDF, DOCX, TXT oder Markdown • Max. 50MB
                </p>
                <p className="text-xs text-gray-500 mt-2">
                    🔒 Alle Daten werden lokal verarbeitet • PII wird automatisch maskiert
                </p>

                {/* Upload Progress */}
                {isUploading && (
                    <div className="mt-4">
                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-brand-500 transition-all duration-300"
                                style={{ width: `${uploadProgress}%` }}
                            />
                        </div>
                        <p className="text-sm text-gray-400 mt-2">Verarbeitung läuft...</p>
                    </div>
                )}
            </div>

            {/* Messages */}
            {error && (
                <div className="flex items-center gap-2 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400">
                    <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                    <span className="text-sm">{error}</span>
                    <button onClick={() => setError(null)} className="ml-auto">
                        <X className="w-4 h-4" />
                    </button>
                </div>
            )}

            {successMessage && (
                <div className="flex items-center gap-2 p-4 bg-brand-500/10 border border-brand-500/30 rounded-xl text-brand-400">
                    <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                    <span className="text-sm">{successMessage}</span>
                    <button onClick={() => setSuccessMessage(null)} className="ml-auto">
                        <X className="w-4 h-4" />
                    </button>
                </div>
            )}

            {/* Document List */}
            {documents.length > 0 && (
                <div className="bg-card rounded-xl border border-white/10 overflow-hidden">
                    <div className="p-4 border-b border-white/10">
                        <h3 className="font-semibold text-white flex items-center gap-2">
                            <FileText className="w-4 h-4" />
                            Verarbeitete Dokumente ({documents.length})
                        </h3>
                    </div>

                    <div className="divide-y divide-white/5">
                        {documents.map(doc => (
                            <div key={doc.id} className="p-4 flex items-center gap-4 hover:bg-white/5">
                                <FileText className="w-8 h-8 text-gray-400" />

                                <div className="flex-1 min-w-0">
                                    <p className="font-medium text-white truncate">{doc.filename}</p>
                                    <p className="text-xs text-gray-500">
                                        {doc.chunk_count} Chunks • {new Date(doc.uploaded_at).toLocaleDateString('de-DE')}
                                    </p>
                                </div>

                                {doc.pii_detected && (
                                    <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 text-xs rounded-full flex items-center gap-1">
                                        <AlertTriangle className="w-3 h-3" />
                                        PII maskiert
                                    </span>
                                )}

                                <button
                                    onClick={() => handleDeleteDocument(doc.id, doc.filename)}
                                    className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                                    title="Dokument löschen (DSGVO)"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {documents.length === 0 && !isUploading && (
                <p className="text-center text-gray-500 py-8">
                    Noch keine Dokumente hochgeladen
                </p>
            )}
        </div>
    );
};
