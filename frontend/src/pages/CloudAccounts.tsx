import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, Cloud, ShieldCheck, RefreshCw, X, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  show: { opacity: 1, y: 0, transition: { type: 'spring' as const, stiffness: 300, damping: 24 } }
};

export const CloudAccounts: React.FC = () => {
  const queryClient = useQueryClient();
  const [showWizard, setShowWizard] = useState(false);
  const [providerId, setProviderId] = useState('aws');
  const [name, setName] = useState('');
  const [accountIdentifier, setAccountIdentifier] = useState('');
  const [credentials, setCredentials] = useState('{}');

  // Query Cloud Accounts
  const { data: accounts, isLoading } = useQuery<any>({
    queryKey: ['cloudAccounts'],
    queryFn: () => api.get('/cloud/accounts?project_id=00000000-0000-0000-0000-000000000000') // Default UUID
  });

  // Mutation to connect account
  const connectMutation = useMutation({
    mutationFn: (newAccount: any) => api.post('/cloud/connect', newAccount),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cloudAccounts'] });
      setShowWizard(false);
      setName('');
      setAccountIdentifier('');
      setCredentials('{}');
    }
  });

  // Mutation to delete account
  const disconnectMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/cloud/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cloudAccounts'] });
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const parsedCreds = JSON.parse(credentials);
      connectMutation.mutate({
        project_id: '00000000-0000-0000-0000-000000000000',
        provider_id: providerId,
        name,
        account_identifier: accountIdentifier,
        credentials: parsedCreds,
        settings: {}
      });
    } catch (err) {
      alert('Invalid JSON in credentials payload. Please check JSON syntax.');
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
            Cloud Accounts
          </h1>
          <p className="text-gray-500 text-xs font-semibold uppercase tracking-widest">Manage cloud credential integrations</p>
        </div>
        <button
          onClick={() => setShowWizard(true)}
          className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-3 rounded-2xl text-xs font-black uppercase tracking-wider flex items-center gap-2 transition-all duration-300 shadow-[0_4px_15px_-3px_rgba(99,102,241,0.35)] hover:-translate-y-0.5 cursor-pointer"
        >
          <Plus size={16} />
          <span>Connect Cloud</span>
        </button>
      </motion.div>

      {/* Connection Wizard Modal */}
      <AnimatePresence>
        {showWizard && (
          <div className="fixed inset-0 bg-black/75 backdrop-blur-md flex items-center justify-center p-4 z-50">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-panel border border-white/5 rounded-3xl w-full max-w-xl p-6 space-y-6 shadow-[0_20px_50px_rgba(0,0,0,0.6)] relative"
            >
              <button 
                onClick={() => setShowWizard(false)}
                className="absolute top-4 right-4 text-gray-500 hover:text-white p-1 rounded-lg hover:bg-white/5 transition-all"
              >
                <X size={18} />
              </button>

              <h2 className="text-xl font-bold text-white tracking-tight">Connect New Cloud Account</h2>
              
              <form onSubmit={handleSubmit} className="space-y-5">
                {/* Visual Provider Selection cards */}
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-gray-400 block uppercase tracking-widest pl-1">Select Provider</label>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { id: 'aws', name: 'AWS', color: 'border-amber-500/20 text-amber-400' },
                      { id: 'azure', name: 'Azure', color: 'border-sky-500/20 text-sky-400' },
                      { id: 'gcp', name: 'GCP', color: 'border-emerald-500/20 text-emerald-400' }
                    ].map((provider) => (
                      <button
                        key={provider.id}
                        type="button"
                        onClick={() => setProviderId(provider.id)}
                        className={`p-4 rounded-2xl border text-center transition-all duration-300 cursor-pointer ${
                          providerId === provider.id
                            ? 'bg-indigo-500/10 border-indigo-500/50 text-white shadow-[0_4px_15px_-4px_rgba(99,102,241,0.2)]'
                            : 'bg-white/[0.01] border-white/5 text-gray-400 hover:bg-white/[0.03] hover:text-gray-200'
                        }`}
                      >
                        <span className="text-sm font-bold block">{provider.name}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-gray-400 block uppercase tracking-widest pl-1">Account Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. AWS Production Account"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full glass-input rounded-2xl px-4 py-3 text-sm focus:outline-none"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-gray-400 block uppercase tracking-widest pl-1">Account Identifier</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. 123456789012"
                    value={accountIdentifier}
                    onChange={(e) => setAccountIdentifier(e.target.value)}
                    className="w-full glass-input rounded-2xl px-4 py-3 text-sm focus:outline-none"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-gray-400 block uppercase tracking-widest pl-1">Credentials (JSON Payload)</label>
                  <textarea
                    required
                    rows={4}
                    value={credentials}
                    onChange={(e) => setCredentials(e.target.value)}
                    className="w-full glass-input rounded-2xl px-4 py-3 text-xs font-mono focus:outline-none placeholder-gray-700"
                  />
                </div>

                <div className="flex gap-4 justify-end pt-4 border-t border-white/5">
                  <button
                    type="button"
                    onClick={() => setShowWizard(false)}
                    className="px-4 py-2.5 text-xs text-gray-500 hover:text-white font-bold uppercase tracking-wider transition-colors cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={connectMutation.status === 'pending'}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-2xl text-xs font-bold uppercase tracking-wider transition-all disabled:opacity-50 cursor-pointer shadow-[0_4px_15px_-3px_rgba(99,102,241,0.35)]"
                  >
                    {connectMutation.status === 'pending' ? 'Connecting...' : 'Connect'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Accounts List Table / Cards */}
      <motion.div variants={itemVariants}>
        {isLoading ? (
          <div className="glass-panel rounded-3xl p-16 flex items-center justify-center border border-white/5">
            <RefreshCw className="animate-spin text-indigo-400" size={24} />
          </div>
        ) : !accounts?.data || accounts.data.length === 0 ? (
          <div className="glass-panel rounded-3xl p-16 text-center border border-white/5 space-y-4">
            <div className="inline-block bg-white/[0.02] border border-white/5 p-4 rounded-3xl text-gray-400">
              <Cloud size={32} />
            </div>
            <div className="max-w-md mx-auto space-y-1">
              <h3 className="text-white font-bold text-base">No connected accounts</h3>
              <p className="text-gray-500 text-xs font-medium">Link AWS, Azure, or GCP accounts to let CloudPilot sync and optimize resources.</p>
            </div>
            <button
              onClick={() => setShowWizard(true)}
              className="bg-white/5 hover:bg-white/10 text-white border border-white/10 px-5 py-2.5 rounded-2xl text-xs font-bold uppercase tracking-wider transition-all cursor-pointer inline-flex items-center gap-1.5 mt-2"
            >
              <Plus size={14} /> Connect Now
            </button>
          </div>
        ) : (
          <div className="glass-panel rounded-3xl overflow-hidden border border-white/5 shadow-2xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="border-b border-white/5 bg-white/[0.01]">
                    <th className="px-6 py-4.5 font-extrabold text-gray-500 text-xs uppercase tracking-widest">Account Name</th>
                    <th className="px-6 py-4.5 font-extrabold text-gray-500 text-xs uppercase tracking-widest">Provider</th>
                    <th className="px-6 py-4.5 font-extrabold text-gray-500 text-xs uppercase tracking-widest">Identifier</th>
                    <th className="px-6 py-4.5 font-extrabold text-gray-500 text-xs uppercase tracking-widest">Status</th>
                    <th className="px-6 py-4.5 text-right"></th>
                  </tr>
                </thead>
                <tbody>
                  {accounts.data.map((acc: any) => (
                    <tr key={acc.id} className="border-b border-white/[0.03] hover:bg-white/[0.01] transition-colors">
                      <td className="px-6 py-4.5 font-bold text-white text-sm">{acc.name}</td>
                      <td className="px-6 py-4.5">
                        <span className="text-xs font-bold text-gray-300 uppercase bg-white/[0.04] px-2.5 py-1 rounded-xl border border-white/5">
                          {acc.provider_id}
                        </span>
                      </td>
                      <td className="px-6 py-4.5 font-mono text-xs text-gray-400">{acc.account_identifier}</td>
                      <td className="px-6 py-4.5">
                        <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-bold">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                          <span className="uppercase tracking-wider">CONNECTED</span>
                        </div>
                      </td>
                      <td className="px-6 py-4.5 text-right">
                        <button
                          onClick={() => {
                            if (confirm(`Disconnect ${acc.name}?`)) {
                              disconnectMutation.mutate(acc.id);
                            }
                          }}
                          className="text-gray-500 hover:text-red-400 p-2 rounded-xl hover:bg-red-500/10 hover:border-red-500/20 border border-transparent transition-all duration-200 cursor-pointer"
                          title="Delete integration"
                        >
                          <Trash2 size={16} />
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
    </motion.div>
  );
};
