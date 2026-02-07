import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export const RoiCalculator: React.FC = () => {
  const [employees, setEmployees] = useState(50);
  const [avgWage, setAvgWage] = useState(45); // EUR per hour
  const [hoursSaved, setHoursSaved] = useState(2); // Per employee per week
  const [hardwareCost, setHardwareCost] = useState(3500); // One time Setup cost (PC + GPU)

  const monthlyProductivityGain = employees * hoursSaved * 4 * avgWage;
  const cloudCostComparison = employees * 20; // Avg $20/user/month for ChatGPT Enterprise
  
  const data = [
    { name: 'Month 1', local: -hardwareCost + monthlyProductivityGain, cloud: monthlyProductivityGain - cloudCostComparison },
    { name: 'Month 3', local: -hardwareCost + (monthlyProductivityGain * 3), cloud: (monthlyProductivityGain * 3) - (cloudCostComparison * 3) },
    { name: 'Month 6', local: -hardwareCost + (monthlyProductivityGain * 6), cloud: (monthlyProductivityGain * 6) - (cloudCostComparison * 6) },
    { name: 'Month 12', local: -hardwareCost + (monthlyProductivityGain * 12), cloud: (monthlyProductivityGain * 12) - (cloudCostComparison * 12) },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-16">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold text-white mb-4">Profitability & ROI Engine</h2>
        <p className="text-gray-400">Calculate how much a Local LLM strategy saves compared to Cloud Subscriptions + Productivity gains.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
        {/* Controls */}
        <div className="bg-card p-8 rounded-2xl border border-white/10 space-y-8">
            <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Number of Employees Using AI</label>
                <input 
                    type="range" min="5" max="500" value={employees} onChange={(e) => setEmployees(Number(e.target.value))}
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-brand-500"
                />
                <span className="text-2xl font-bold text-white mt-2 block">{employees} users</span>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Hours Saved per Week (per user)</label>
                <input 
                    type="range" min="0.5" max="10" step="0.5" value={hoursSaved} onChange={(e) => setHoursSaved(Number(e.target.value))}
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-brand-500"
                />
                <span className="text-2xl font-bold text-white mt-2 block">{hoursSaved} hours</span>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Average Hourly Wage (€)</label>
                <input 
                    type="number" value={avgWage} onChange={(e) => setAvgWage(Number(e.target.value))}
                    className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg p-3 text-white"
                />
            </div>
            
            <div className="pt-6 border-t border-white/10">
                 <h4 className="text-white font-bold mb-4">Estimated Hardware Setup</h4>
                 <div className="p-4 bg-brand-900/20 border border-brand-500/20 rounded-lg flex justify-between items-center">
                    <div>
                        <p className="text-brand-400 font-bold">Recommended Node</p>
                        <p className="text-xs text-gray-400">1x NVIDIA RTX 4070 (12GB) or similar</p>
                    </div>
                    <span className="text-xl font-bold text-white">€{hardwareCost}</span>
                 </div>
            </div>
        </div>

        {/* Results */}
        <div className="bg-card p-8 rounded-2xl border border-white/10 h-full flex flex-col justify-between">
            <div className="grid grid-cols-2 gap-4 mb-8">
                <div className="p-4 bg-white/5 rounded-xl">
                    <p className="text-gray-400 text-xs uppercase">Annual Productivity Value</p>
                    <p className="text-2xl md:text-3xl font-bold text-emerald-400">€{(monthlyProductivityGain * 12).toLocaleString()}</p>
                </div>
                <div className="p-4 bg-white/5 rounded-xl">
                    <p className="text-gray-400 text-xs uppercase">Cloud Subscriptions Saved</p>
                    <p className="text-2xl md:text-3xl font-bold text-blue-400">€{(cloudCostComparison * 12).toLocaleString()}</p>
                </div>
            </div>

            <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                        <XAxis dataKey="name" stroke="#666" fontSize={12} tickLine={false} axisLine={false} />
                        <YAxis stroke="#666" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `€${val/1000}k`} />
                        <Tooltip 
                            contentStyle={{ backgroundColor: '#171717', borderColor: '#333', color: '#fff' }}
                            itemStyle={{ color: '#fff' }}
                        />
                        <Bar dataKey="local" name="Local AI Profit" fill="#22c55e" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="cloud" name="Cloud AI Profit" fill="#3b82f6" radius={[4, 4, 0, 0]} opacity={0.5} />
                    </BarChart>
                </ResponsiveContainer>
            </div>
            
            <p className="text-center text-xs text-gray-500 mt-4">
                *Comparison vs Standard SaaS pricing. Local includes Hardware ROI.
            </p>
        </div>
      </div>
    </div>
  );
};