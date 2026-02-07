import React, { useState, useRef, useEffect } from 'react';
import { Send, Terminal, Cpu, Database, Shield, AlertTriangle } from 'lucide-react';
import { streamLocalSimulation, analyzeCompliance } from '../services/geminiService';
import { ChatMessage } from '../types';

export const DemoChat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'model',
      text: "Sentinell Core Online. Secure Local Environment Initialized. How can I assist you with your confidential data today?",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [vramUsage, setVramUsage] = useState(4.2); // GB
  const [complianceStatus, setComplianceStatus] = useState<'secure' | 'warning'>('secure');
  
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isThinking) return;

    const userMsg: ChatMessage = { role: 'user', text: input, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsThinking(true);
    setVramUsage(prev => Math.min(prev + 0.5, 11.5)); // Simulate VRAM spike

    // Simulate Compliance Check
    const compliance = await analyzeCompliance(userMsg.text);
    if (compliance && compliance.piiDetected) {
        setComplianceStatus('warning');
    } else {
        setComplianceStatus('secure');
    }

    try {
      // Convert history for API
      const history = messages.map(m => ({
        role: m.role,
        parts: [{ text: m.text }]
      }));

      const stream = await streamLocalSimulation(history, userMsg.text);
      
      let fullResponse = '';
      const modelMsg: ChatMessage = { 
        role: 'model', 
        text: '', 
        timestamp: new Date(),
        metadata: {
            latency: 45, // ms (simulated)
            tokens: 0
        }
      };
      
      setMessages(prev => [...prev, modelMsg]);

      for await (const chunk of stream) {
        const text = chunk.text();
        if (text) {
          fullResponse += text;
          setMessages(prev => {
            const newArr = [...prev];
            const lastMsg = newArr[newArr.length - 1];
            lastMsg.text = fullResponse;
            return newArr;
          });
        }
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'model', 
        text: "Error: Could not connect to the inference engine. Please check your API key.", 
        timestamp: new Date() 
      }]);
    } finally {
      setIsThinking(false);
      setTimeout(() => setVramUsage(4.5), 2000); // Cool down VRAM
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 h-[calc(100vh-100px)] flex gap-6">
      
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-[#0f0f0f] rounded-2xl border border-white/10 overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="h-14 bg-white/5 border-b border-white/10 flex items-center px-4 justify-between">
          <div className="flex items-center gap-2 text-gray-200">
            <Terminal className="w-4 h-4 text-brand-500" />
            <span className="font-mono text-sm">local_session_id: 8f9a-2b3c</span>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="flex items-center gap-1 text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              ONLINE
            </span>
            <span className="text-gray-500">MODEL: LLAMA-3-8B-Q4_K_M</span>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl p-4 ${
                msg.role === 'user' 
                  ? 'bg-brand-900/30 text-white border border-brand-500/20' 
                  : 'bg-white/5 text-gray-200 border border-white/5'
              }`}>
                <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</div>
                {msg.role === 'model' && (
                  <div className="mt-2 pt-2 border-t border-white/5 flex gap-3 text-[10px] text-gray-500 font-mono uppercase">
                    <span>Latency: {msg.metadata?.latency || 42}ms</span>
                    <span>Tokens/s: 64.2</span>
                    <span>Egress: 0kb</span>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isThinking && (
            <div className="flex justify-start">
              <div className="bg-white/5 rounded-2xl p-4 flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-brand-500 rounded-full animate-bounce"></span>
                <span className="w-1.5 h-1.5 bg-brand-500 rounded-full animate-bounce delay-75"></span>
                <span className="w-1.5 h-1.5 bg-brand-500 rounded-full animate-bounce delay-150"></span>
              </div>
            </div>
          )}
          <div ref={bottomRef}></div>
        </div>

        {/* Input */}
        <div className="p-4 bg-white/5 border-t border-white/10">
          <form onSubmit={handleSubmit} className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Enter confidential prompt (Simulation)..."
              className="w-full bg-[#0a0a0a] border border-white/10 rounded-xl py-3 pl-4 pr-12 text-white placeholder-gray-600 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all font-sans"
            />
            <button 
              type="submit" 
              disabled={isThinking}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 bg-brand-600 hover:bg-brand-500 rounded-lg text-white disabled:opacity-50 transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <div className="mt-2 flex justify-between items-center text-[10px] text-gray-500 font-mono">
             <span>SECURE INPUT ENABLED</span>
             <span>AES-256 ENCRYPTION (SIMULATED)</span>
          </div>
        </div>
      </div>

      {/* Sidebar Metrics */}
      <div className="hidden lg:flex w-72 flex-col gap-4">
        
        {/* Hardware Monitor */}
        <div className="bg-card p-4 rounded-xl border border-white/10">
            <h3 className="text-gray-400 text-xs font-bold uppercase mb-4 flex items-center gap-2">
                <Cpu className="w-4 h-4" /> Hardware Telemetry
            </h3>
            
            <div className="space-y-4">
                <div>
                    <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-400">VRAM (RTX 3060)</span>
                        <span className="text-brand-400">{vramUsage.toFixed(1)}GB / 12GB</span>
                    </div>
                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                        <div 
                            className="h-full bg-brand-500 transition-all duration-500 ease-out" 
                            style={{ width: `${(vramUsage / 12) * 100}%` }}
                        ></div>
                    </div>
                </div>

                <div>
                    <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-400">GPU Compute</span>
                        <span className="text-yellow-400">{isThinking ? '88%' : '12%'}</span>
                    </div>
                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                        <div 
                            className="h-full bg-yellow-500 transition-all duration-300" 
                            style={{ width: isThinking ? '88%' : '12%' }}
                        ></div>
                    </div>
                </div>
            </div>
        </div>

        {/* Compliance Monitor */}
        <div className={`p-4 rounded-xl border ${
            complianceStatus === 'secure' ? 'border-brand-500/30 bg-brand-900/10' : 'border-yellow-500/30 bg-yellow-900/10'
        }`}>
             <h3 className="text-gray-400 text-xs font-bold uppercase mb-4 flex items-center gap-2">
                <Shield className="w-4 h-4" /> Privacy Watchdog
            </h3>

            <div className="space-y-3">
                <div className="flex items-center justify-between p-2 bg-black/20 rounded border border-white/5">
                    <span className="text-xs text-gray-400">Data Egress</span>
                    <span className="text-xs font-mono text-emerald-500">0.00 KB</span>
                </div>
                
                <div className="flex items-center justify-between p-2 bg-black/20 rounded border border-white/5">
                    <span className="text-xs text-gray-400">PII Redaction</span>
                    {complianceStatus === 'secure' ? (
                        <span className="text-xs font-bold text-emerald-500">ACTIVE</span>
                    ) : (
                         <span className="text-xs font-bold text-yellow-500 flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3" /> REVIEW
                         </span>
                    )}
                </div>
            </div>
        </div>

         <div className="bg-card p-4 rounded-xl border border-white/10 flex-1">
            <h3 className="text-gray-400 text-xs font-bold uppercase mb-4 flex items-center gap-2">
                <Database className="w-4 h-4" /> Context Window
            </h3>
            <div className="flex items-center justify-center h-32 relative">
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl font-bold text-white">4k</span>
                </div>
                <svg className="transform -rotate-90 w-24 h-24">
                    <circle cx="48" cy="48" r="40" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-white/10" />
                    <circle cx="48" cy="48" r="40" stroke="currentColor" strokeWidth="8" fill="transparent" strokeDasharray={251.2} strokeDashoffset={251.2 - (251.2 * 0.15)} className="text-brand-600" />
                </svg>
            </div>
            <p className="text-center text-xs text-gray-500">Tokens Used: ~600 / 4096</p>
         </div>

      </div>
    </div>
  );
};