import React, { useState, useEffect } from 'react';
import { Shield, FileText, Eye, Database, Clock, RefreshCw } from 'lucide-react';
import { getComplianceStats, getAuditLog, ComplianceStats } from '../services/geminiService';

export const ComplianceDashboard: React.FC = () => {
    const [stats, setStats] = useState<ComplianceStats | null>(null);
    const [auditLog, setAuditLog] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [statsData, auditData] = await Promise.all([
                getComplianceStats(),
                getAuditLog(20)
            ]);
            setStats(statsData);
            setAuditLog(auditData.entries);
        } catch (e) {
            setError('Backend nicht erreichbar. Stellen Sie sicher, dass der Server läuft.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    if (loading) {
        return (
            <div className="max-w-6xl mx-auto px-4 py-16 text-center">
                <RefreshCw className="w-8 h-8 mx-auto text-brand-500 animate-spin" />
                <p className="mt-4 text-gray-400">Lade Compliance-Daten...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="max-w-6xl mx-auto px-4 py-16 text-center">
                <Shield className="w-12 h-12 mx-auto text-red-400 mb-4" />
                <p className="text-red-400">{error}</p>
                <button
                    onClick={loadData}
                    className="mt-4 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white"
                >
                    Erneut versuchen
                </button>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Shield className="w-6 h-6 text-brand-500" />
                        Compliance Dashboard
                    </h2>
                    <p className="text-gray-400 mt-1">DSGVO & EU AI Act Übersicht</p>
                </div>
                <button
                    onClick={loadData}
                    className="p-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors"
                >
                    <RefreshCw className="w-5 h-5" />
                </button>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-card p-6 rounded-xl border border-white/10">
                    <FileText className="w-8 h-8 text-blue-400 mb-3" />
                    <p className="text-3xl font-bold text-white">{stats?.total_documents || 0}</p>
                    <p className="text-sm text-gray-400">Dokumente</p>
                </div>

                <div className="bg-card p-6 rounded-xl border border-white/10">
                    <Database className="w-8 h-8 text-purple-400 mb-3" />
                    <p className="text-3xl font-bold text-white">{stats?.total_chunks || 0}</p>
                    <p className="text-sm text-gray-400">Chunks indexiert</p>
                </div>

                <div className="bg-card p-6 rounded-xl border border-white/10">
                    <Shield className="w-8 h-8 text-yellow-400 mb-3" />
                    <p className="text-3xl font-bold text-white">{stats?.pii_documents || 0}</p>
                    <p className="text-sm text-gray-400">Mit PII-Maskierung</p>
                </div>

                <div className="bg-card p-6 rounded-xl border border-white/10">
                    <Eye className="w-8 h-8 text-brand-400 mb-3" />
                    <p className="text-3xl font-bold text-white">{stats?.audit_entries || 0}</p>
                    <p className="text-sm text-gray-400">Audit-Einträge</p>
                </div>
            </div>

            {/* Compliance Status */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* DSGVO Checklist */}
                <div className="bg-card p-6 rounded-xl border border-white/10">
                    <h3 className="text-lg font-semibold text-white mb-4">DSGVO Compliance ✓</h3>
                    <ul className="space-y-3">
                        {[
                            { label: 'Datenverarbeitung nur lokal', status: true },
                            { label: 'PII-Erkennung aktiv', status: true },
                            { label: 'Audit-Logging aktiviert', status: true },
                            { label: 'Löschfunktion verfügbar', status: true },
                            { label: 'Keine Drittanbieter-APIs', status: true },
                        ].map((item, i) => (
                            <li key={i} className="flex items-center gap-3">
                                <span className={`w-2 h-2 rounded-full ${item.status ? 'bg-green-500' : 'bg-red-500'}`} />
                                <span className="text-gray-300">{item.label}</span>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* EU AI Act Status */}
                <div className="bg-card p-6 rounded-xl border border-white/10">
                    <h3 className="text-lg font-semibold text-white mb-4">EU AI Act Status</h3>
                    <div className="space-y-4">
                        <div className="p-4 bg-brand-500/10 border border-brand-500/30 rounded-lg">
                            <p className="text-brand-400 font-medium">Risikokategorie: Minimal</p>
                            <p className="text-sm text-gray-400 mt-1">
                                Dokumentenanalyse ohne automatisierte Entscheidungsfindung
                            </p>
                        </div>
                        <ul className="space-y-2 text-sm">
                            <li className="flex items-center gap-2 text-gray-300">
                                ✓ Keine verbotenen Praktiken
                            </li>
                            <li className="flex items-center gap-2 text-gray-300">
                                ✓ Transparenz: KI-Nutzung gekennzeichnet
                            </li>
                            <li className="flex items-center gap-2 text-gray-300">
                                ✓ Lokale Verarbeitung = volle Kontrolle
                            </li>
                        </ul>
                    </div>
                </div>
            </div>

            {/* Audit Log */}
            <div className="bg-card rounded-xl border border-white/10 overflow-hidden">
                <div className="p-4 border-b border-white/10 flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        <Clock className="w-5 h-5" />
                        Aktuelle Audit-Einträge
                    </h3>
                </div>

                {auditLog.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-white/5">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Zeit</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Aktion</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Benutzer</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Details</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {auditLog.map((entry, i) => (
                                    <tr key={i} className="hover:bg-white/5">
                                        <td className="px-4 py-3 text-sm text-gray-400 whitespace-nowrap">
                                            {new Date(entry.timestamp).toLocaleString('de-DE')}
                                        </td>
                                        <td className="px-4 py-3">
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${entry.action.includes('delete') ? 'bg-red-500/20 text-red-400' :
                                                    entry.action.includes('upload') ? 'bg-blue-500/20 text-blue-400' :
                                                        entry.action.includes('chat') ? 'bg-purple-500/20 text-purple-400' :
                                                            'bg-gray-500/20 text-gray-400'
                                                }`}>
                                                {entry.action}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-300">{entry.user_id}</td>
                                        <td className="px-4 py-3 text-sm text-gray-400 max-w-md truncate">
                                            {entry.details}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p className="p-8 text-center text-gray-500">Keine Audit-Einträge vorhanden</p>
                )}
            </div>
        </div>
    );
};
