import React from 'react';
import { ShieldCheck, Cpu, BarChart3, Menu, FileText, Shield } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'home', label: 'Übersicht', icon: ShieldCheck },
    { id: 'demo', label: 'KI Chat', icon: Cpu },
    { id: 'documents', label: 'Dokumente', icon: FileText },
    { id: 'compliance', label: 'Compliance', icon: Shield },
    { id: 'roi', label: 'ROI Rechner', icon: BarChart3 },
  ];

  return (
    <nav className="sticky top-0 z-50 glass-panel border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => setActiveTab('home')}>
            <div className="bg-brand-500/20 p-2 rounded-lg">
              <ShieldCheck className="w-6 h-6 text-brand-500" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white">
              Sentinell<span className="text-brand-500">.ai</span>
            </span>
            <span className="ml-2 px-2 py-0.5 bg-brand-500/20 text-brand-400 text-[10px] font-mono rounded">
              LOKAL
            </span>
          </div>

          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-4">
              {navItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 flex items-center gap-2 ${activeTab === item.id
                      ? 'bg-brand-900/50 text-brand-500 border border-brand-500/20'
                      : 'text-gray-300 hover:text-white hover:bg-white/5'
                    }`}
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          <div className="md:hidden">
            <button className="text-gray-400 hover:text-white">
              <Menu className="w-6 h-6" />
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};