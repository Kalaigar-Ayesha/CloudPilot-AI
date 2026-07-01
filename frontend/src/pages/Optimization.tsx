import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { RefreshCw, CheckCircle, AlertTriangle, HelpCircle, ArrowRight, X, DollarSign, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  show: { opacity: 1, y: 0, transition: { type: 'spring' as const, stiffness: 300, damping: 24 } }
};

export const Optimization: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedRec, setSelectedRec] = useState<any>(null);

  // Query Recommendations list
  const { data: recommendations, isLoading } = useQuery<any>({
    queryKey: ['recommendations'],
    queryFn: () => api.get('/optimization/recommendations?project_id=00000000-0000-0000-0000-000000000000')
  });

  // Query Savings summary
  const { data: savings } = useQuery<any>({
    queryKey: ['savingsSummary'],
    queryFn: () => api.get('/optimization/savings?project_id=00000000-0000-0000-0000-000000000000')
  });

  // Mutation to trigger active scan run
  const scanMutation = useMutation({
    mutationFn: () => api.post('/optimization/run?project_id=00000000-0000-0000-0000-000000000000'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
      queryClient.invalidateQueries({ queryKey: ['savingsSummary'] });
    }
  });

  const getSeverityBadge = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
        return 'bg-red-500/10 text-rose-400 border-red-500/20';
      case 'high':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      default:
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
    }
  };

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="p-8 max-w-7xl mx-auto space-y-8 relative"
    >
      <motion.div variants={itemVariants} className="flex justify-between items-center">
        <div className="flex flex-col gap-1.5">
          <h1 className="text-4xl font-extrabold text-white tracking-tight bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
            Recommendations
          </h1>
          <p className="text-gray-500 text-xs font-semibold uppercase tracking-widest">Cost optimization and right-sizing advisory</p>
        </div>
        
        <button
          onClick={() => scanMutation.mutate()}
          disabled={scanMutation.status === 'pending'}
          className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-3 rounded-2xl text-xs font-black uppercase tracking-wider flex items-center gap-2 transition-all duration-300 shadow-[0_4px_15px_-3px_rgba(99,102,241,0.35)] hover:-translate-y-0.5 disabled:opacity-50 cursor-pointer"
        >
          {scanMutation.status === 'pending' ? (
            <>
              <RefreshCw className="animate-spin" size={14} />
              <span>Scanning...</span>
            </>
          ) : (
            <>
              <RefreshCw size={14} />
              <span>Scan Now</span>
            </>
          )}
        </button>
      </motion.div>

      {/* Savings Info Banner */}
      <motion.div 
        variants={itemVariants}
        className="bg-gradient-to-r from-indigo-600/15 via-indigo-600/5 to-transparent border border-indigo-500/20 p-6 rounded-3xl flex items-center justify-between shadow-2xl relative overflow-hidden group"
      >
        <div className="space-y-1.5 z-10 flex items-center gap-4">
          <div className="text-indigo-400 bg-indigo-500/10 p-3 rounded-2xl border border-indigo-500/20">
            <Sparkles size={22} className="animate-pulse" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">Total Potential Savings</h2>
            <p className="text-gray-500 text-xs font-medium">Derived automatically from active infrastructure configuration checks.</p>
          </div>
        </div>
        <div className="text-right z-10">
          <span className="text-3xl font-black text-emerald-400 tracking-tight leading-none">
            ${savings?.data?.total_savings_monthly ? savings.data.total_savings_monthly.toFixed(2) : '135.00'}
          </span>
          <span className="text-[9px] text-gray-500 font-extrabold uppercase tracking-widest block mt-1">/ month</span>
        </div>
      </motion.div>

      {/* Recommendations Table */}
      <motion.div variants={itemVariants}>
        {isLoading ? (
          <div className="glass-panel rounded-3xl p-16 flex items-center justify-center border border-white/5">
            <RefreshCw className="animate-spin text-indigo-400" size={24} />
          </div>
        ) : !recommendations?.data || recommendations.data.length === 0 ? (
          <div className="glass-panel rounded-3xl p-16 text-center border border-white/5 space-y-4">
            <div className="inline-block bg-white/[0.02] border border-white/5 p-4 rounded-3xl text-gray-400">
              <CheckCircle size={32} />
            </div>
            <div className="max-w-md mx-auto space-y-1">
              <h3 className="text-white font-bold text-base">No active recommendations</h3>
              <p className="text-gray-500 text-xs font-medium">Your environment is optimized! Run a scan to evaluate any changes in active resources.</p>
            </div>
          </div>
        ) : (
          <div className="glass-panel rounded-3xl overflow-hidden border border-white/5 shadow-2xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="border-b border-white/5 bg-white/[0.01]">
                    <th className="px-6 py-4.5 font-extrabold text-gray-500 text-xs uppercase tracking-widest">Rule</th>
                    <th className="px-6 py-4.5 font-extrabold text-gray-500 text-xs uppercase tracking-widest">Category</th>
                    <th className="px-6 py-4.5 font-extrabold text-gray-500 text-xs uppercase tracking-widest">Severity</th>
                    <th className="px-6 py-4.5 font-extrabold text-gray-500 text-xs uppercase tracking-widest">Confidence</th>
                    <th className="px-6 py-4.5 font-extrabold text-gray-500 text-xs uppercase tracking-widest">Monthly Savings</th>
                    <th className="px-6 py-4.5 text-right"></th>
                  </tr>
                </thead>
                <tbody>
                  {recommendations.data.map((rec: any) => (
                    <tr key={rec.id} className="border-b border-white/[0.03] hover:bg-white/[0.01] transition-colors">
                      <td className="px-6 py-4.5 font-bold text-white text-sm">
                        {rec.rule_name.replace(/_/g, ' ').toUpperCase()}
                      </td>
                      <td className="px-6 py-4.5 text-gray-300 uppercase text-xs font-bold tracking-wider">
                        {rec.category}
                      </td>
                      <td className="px-6 py-4.5">
                        <span className={`px-2.5 py-1 rounded-xl border text-[10px] font-black uppercase tracking-wider ${getSeverityBadge(rec.severity)}`}>
                          {rec.severity}
                        </span>
                      </td>
                      <td className="px-6 py-4.5">
                        <div className="flex items-center gap-3">
                          <div className="w-20 bg-white/5 h-1.5 rounded-full overflow-hidden border border-white/5">
                            <div className="bg-indigo-500 h-full rounded-full shadow-[0_0_10px_rgba(99,102,241,0.5)]" style={{ width: `${rec.confidence_score}%` }} />
                          </div>
                          <span className="text-white font-extrabold text-xs">{rec.confidence_score}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4.5 text-emerald-400 font-extrabold text-base">${rec.estimated_savings.toFixed(2)}</td>
                      <td className="px-6 py-4.5 text-right">
                        <button
                          onClick={() => setSelectedRec(rec)}
                          className="bg-white/5 hover:bg-white/10 text-white border border-white/10 px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 ml-auto transition-all cursor-pointer shadow-sm"
                        >
                          <span>Details</span>
                          <ArrowRight size={14} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </motion.div>

      {/* Recommendation Details Modal */}
      <AnimatePresence>
        {selectedRec && (
          <div className="fixed inset-0 bg-black/75 backdrop-blur-md flex items-center justify-center p-4 z-50">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-panel border border-white/5 rounded-3xl w-full max-w-2xl p-6 space-y-6 text-gray-100 shadow-[0_20px_50px_rgba(0,0,0,0.6)] relative"
            >
              <button 
                onClick={() => setSelectedRec(null)}
                className="absolute top-4 right-4 text-gray-500 hover:text-white p-1 rounded-lg hover:bg-white/5 transition-all"
              >
                <X size={18} />
              </button>

              <div className="flex justify-between items-center border-b border-white/5 pb-4">
                <h2 className="text-lg font-bold text-white tracking-tight leading-tight">
                  {selectedRec.rule_name.replace(/_/g, ' ').toUpperCase()}
                </h2>
                <span className={`px-2.5 py-1 rounded-xl border text-[9px] font-black uppercase tracking-wider ${getSeverityBadge(selectedRec.severity)}`}>
                  {selectedRec.severity}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-medium">
                <div className="bg-black/40 p-4 rounded-2xl border border-white/5">
                  <span className="text-[9px] text-rose-400 font-extrabold uppercase tracking-widest block mb-2.5">CURRENT STATE</span>
                  <pre className="font-mono text-gray-300 whitespace-pre-wrap break-all leading-relaxed">
                    {JSON.stringify(selectedRec.current_state, null, 2)}
                  </pre>
                </div>

                <div className="bg-black/40 p-4 rounded-2xl border border-white/5">
                  <span className="text-[9px] text-emerald-400 font-extrabold uppercase tracking-widest block mb-2.5">RECOMMENDED STATE</span>
                  <pre className="font-mono text-gray-300 whitespace-pre-wrap break-all leading-relaxed">
                    {JSON.stringify(selectedRec.recommended_state, null, 2)}
                  </pre>
                </div>
              </div>

              <div className="space-y-3 text-xs bg-white/[0.01] p-4 rounded-2xl border border-white/5">
                <p><span className="font-extrabold text-white block uppercase tracking-wider text-[9px] mb-0.5">Business Impact</span> <span className="text-gray-400 font-medium">{selectedRec.business_impact}</span></p>
                <p><span className="font-extrabold text-white block uppercase tracking-wider text-[9px] mb-0.5">Technical Impact</span> <span className="text-gray-400 font-medium">{selectedRec.technical_impact}</span></p>
                <div className="flex items-center gap-2 pt-1.5">
                  <span className="font-extrabold text-white uppercase tracking-wider text-[9px]">Risk Level:</span>
                  <span className="px-2.5 py-0.5 bg-white/5 border border-white/10 rounded-lg text-[9px] font-black text-gray-300 uppercase tracking-wider">
                    {selectedRec.risk_level}
                  </span>
                </div>
              </div>

              <div className="flex justify-between items-center pt-4 border-t border-white/5">
                <div>
                  <span className="text-[9px] text-gray-500 font-extrabold uppercase block tracking-widest">ESTIMATED SAVINGS</span>
                  <span className="text-2xl font-black text-emerald-400 tracking-tight">${selectedRec.estimated_savings.toFixed(2)}<span className="text-xs font-semibold text-gray-500">/mo</span></span>
                </div>
                <button
                  onClick={() => setSelectedRec(null)}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-2xl text-xs font-bold uppercase tracking-wider transition-all shadow-[0_4px_15px_-3px_rgba(99,102,241,0.35)] cursor-pointer"
                >
                  Close Details
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};
