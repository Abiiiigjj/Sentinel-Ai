import React from 'react';
import { CheckCircle2, Lock, Server, Zap } from 'lucide-react';

export const Hero: React.FC<{ onStartDemo: () => void }> = ({ onStartDemo }) => {
  return (
    <div className="relative overflow-hidden pt-16 pb-32">
      {/* Background Effects */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full max-w-7xl opacity-20 pointer-events-none">
        <div className="absolute top-20 left-20 w-72 h-72 bg-brand-500 rounded-full blur-[128px]"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-600 rounded-full blur-[128px]"></div>
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col items-center text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-brand-900/30 border border-brand-500/30 text-brand-500 mb-8 animate-pulse-slow">
          <span className="w-2 h-2 rounded-full bg-brand-500"></span>
          <span className="text-sm font-medium">EU AI Act Compliant Ready</span>
        </div>

        <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white mb-6">
          Enterprise Intelligence. <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-500 to-emerald-300">
            Zero Data Leakage.
          </span>
        </h1>

        <p className="max-w-2xl text-lg md:text-xl text-gray-400 mb-10">
          Deploy powerful Local LLMs on your own hardware. 
          Keep your intellectual property within your firewall. 
          Avoid the "Black Box" of public clouds.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
          <button 
            onClick={onStartDemo}
            className="px-8 py-4 bg-brand-600 hover:bg-brand-500 text-white rounded-lg font-semibold transition-all shadow-lg shadow-brand-900/50 flex items-center justify-center gap-2"
          >
            <Zap className="w-5 h-5" />
            Launch Simulation
          </button>
          <button className="px-8 py-4 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg font-semibold transition-all flex items-center justify-center gap-2">
            View Deployment Plans
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-20 w-full">
          {[
            {
              icon: Lock,
              title: "100% Data Sovereignty",
              desc: "Your data never leaves your premises. No API calls to US servers."
            },
            {
              icon: Server,
              title: "Optimized for Consumer HW",
              desc: "Run Llama 3 or Mistral efficiently on standard 12GB+ GPUs."
            },
            {
              icon: CheckCircle2,
              title: "Compliance Automation",
              desc: "Built-in PII redaction and audit logs for GDPR & EU AI Act."
            }
          ].map((feature, idx) => (
            <div key={idx} className="p-6 rounded-2xl glass-panel text-left hover:border-brand-500/50 transition-colors">
              <feature.icon className="w-10 h-10 text-brand-500 mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">{feature.title}</h3>
              <p className="text-gray-400">{feature.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};