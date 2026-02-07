import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { DemoChat } from './components/DemoChat';
import { RoiCalculator } from './components/RoiCalculator';
import { DocumentUpload } from './components/DocumentUpload';
import { ComplianceDashboard } from './components/ComplianceDashboard';
import { checkHealth, HealthStatus } from './services/geminiService';

function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [backendStatus, setBackendStatus] = useState<HealthStatus | null>(null);
  const [backendError, setBackendError] = useState(false);

  // Check backend health on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const status = await checkHealth();
        setBackendStatus(status);
        setBackendError(false);
      } catch (e) {
        setBackendError(true);
      }
    };

    checkBackend();
    // Recheck every 30 seconds
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#050505] text-white font-sans selection:bg-brand-500/30">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Backend Status Banner */}
      {backendError && (
        <div className="bg-yellow-500/10 border-b border-yellow-500/30 px-4 py-2 text-center">
          <span className="text-yellow-400 text-sm">
            ⚠️ Backend nicht erreichbar. Starten Sie den Server mit: <code className="bg-black/30 px-2 py-0.5 rounded">./scripts/setup.sh</code>
          </span>
        </div>
      )}

      {backendStatus && backendStatus.status === 'degraded' && (
        <div className="bg-orange-500/10 border-b border-orange-500/30 px-4 py-2 text-center">
          <span className="text-orange-400 text-sm">
            ⚠️ Ollama nicht verbunden. LLM-Funktionen eingeschränkt.
          </span>
        </div>
      )}

      <main className="fade-in">
        {activeTab === 'home' && (
          <>
            <Hero onStartDemo={() => setActiveTab('demo')} />
            {/* Value Props Section */}
            <div className="max-w-7xl mx-auto px-4 py-20 border-t border-white/5">
              <div className="flex flex-col md:flex-row justify-between items-end mb-12">
                <div>
                  <h2 className="text-3xl font-bold mb-2">Warum Lokale Intelligenz?</h2>
                  <p className="text-gray-400 max-w-lg">Der EU AI Act klassifiziert allgemeine KI-Modelle mit systemischem Risiko. Lokales Hosting eliminiert das Risiko der Datenverarbeitung durch Dritte.</p>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="p-8 rounded-2xl bg-gradient-to-br from-gray-900 to-black border border-white/10">
                  <h3 className="text-xl font-bold mb-4 text-emerald-400">Der "Sentinell" Vorteil</h3>
                  <ul className="space-y-3 text-gray-300">
                    <li className="flex items-center gap-2">✓ Keine Token-Kosten</li>
                    <li className="flex items-center gap-2">✓ Niedrige Latenz (läuft im LAN)</li>
                    <li className="flex items-center gap-2">✓ Feintuning auf Ihre Dokumente möglich</li>
                    <li className="flex items-center gap-2">✓ Läuft auf Consumer-Hardware (RTX 3060+)</li>
                    <li className="flex items-center gap-2">✓ Vollständig offline-fähig</li>
                  </ul>
                </div>
                <div className="p-8 rounded-2xl bg-gradient-to-br from-gray-900 to-black border border-white/10 opacity-60">
                  <h3 className="text-xl font-bold mb-4 text-red-400">Das Public Cloud Risiko</h3>
                  <ul className="space-y-3 text-gray-500">
                    <li className="flex items-center gap-2">✗ Daten werden für Modelltraining verwendet</li>
                    <li className="flex items-center gap-2">✗ API-Ausfälle und Rate Limits</li>
                    <li className="flex items-center gap-2">✗ Unvorhersehbare Preisstrukturen</li>
                    <li className="flex items-center gap-2">✗ Rechtliche Grauzonen in der EU</li>
                    <li className="flex items-center gap-2">✗ Keine Kontrolle über Datenverarbeitung</li>
                  </ul>
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === 'demo' && <DemoChat />}

        {activeTab === 'roi' && <RoiCalculator />}

        {activeTab === 'documents' && (
          <div className="max-w-4xl mx-auto px-4 py-8">
            <h2 className="text-2xl font-bold text-white mb-6">Dokumentenverwaltung</h2>
            <DocumentUpload />
          </div>
        )}

        {activeTab === 'compliance' && <ComplianceDashboard />}
      </main>

      <footer className="border-t border-white/10 py-12 bg-black mt-12">
        <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row justify-between items-center text-gray-500 text-sm">
          <div className="flex items-center gap-4">
            <p>© 2024 Sentinell.ai - Sovereign Intelligence Solutions.</p>
            {backendStatus && (
              <span className={`flex items-center gap-1 text-xs ${backendStatus.status === 'healthy' ? 'text-green-500' : 'text-yellow-500'
                }`}>
                <span className="w-2 h-2 rounded-full bg-current" />
                {backendStatus.status === 'healthy' ? 'System Online' : 'Degraded'}
              </span>
            )}
          </div>
          <div className="flex gap-6 mt-4 md:mt-0">
            <a href="#" className="hover:text-white">Datenschutz</a>
            <a href="#" className="hover:text-white">Nutzungsbedingungen</a>
            <a href="#" className="hover:text-white">Kontakt</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;