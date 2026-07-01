import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Send, RefreshCw, MessageSquare, ShieldAlert, Award, FileText, Plus } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';

export const Copilot: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [queryText, setQueryText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Query Conversations
  const { data: conversations, isLoading: convsLoading } = useQuery<any>({
    queryKey: ['conversations'],
    queryFn: () => api.get('/ai/history?project_id=00000000-0000-0000-0000-000000000000')
  });

  // Query Messages
  const { data: messages, isLoading: msgsLoading } = useQuery<any>({
    queryKey: ['messages', activeConvId],
    queryFn: () => api.get(`/ai/${activeConvId}`),
    enabled: !!activeConvId
  });

  // Mutation to start conversation
  const startConvMutation = useMutation({
    mutationFn: () => api.post('/ai/chat', { project_id: '00000000-0000-0000-0000-000000000000', title: 'New Conversation' }),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      setActiveConvId(data.data.id);
    }
  });

  // Mutation to submit message query
  const submitQueryMutation = useMutation({
    mutationFn: (payload: { convId: string; content: string }) =>
      api.post(`/ai/${payload.convId}/query?project_id=00000000-0000-0000-0000-000000000000`, { content: payload.content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages', activeConvId] });
      setQueryText('');
    }
  });

  // Auto scroll to message bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!queryText.trim() || !activeConvId) return;
    submitQueryMutation.mutate({ convId: activeConvId, content: queryText });
  };

  const handleSuggest = (text: string) => {
    if (!activeConvId) return;
    submitQueryMutation.mutate({ convId: activeConvId, content: text });
  };

  return (
    <div className="flex h-screen text-gray-100 overflow-hidden relative pl-64">
      {/* Sidebar conversation history list */}
      <aside className="w-80 border-r border-white/5 bg-card/10 backdrop-blur-md flex flex-col h-full z-10">
        <div className="p-4 border-b border-white/5">
          <button
            onClick={() => startConvMutation.mutate()}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-3 rounded-2xl text-xs font-black uppercase tracking-wider flex items-center justify-center gap-2 transition-all duration-300 shadow-[0_4px_15px_-3px_rgba(99,102,241,0.35)] hover:-translate-y-0.5 cursor-pointer"
          >
            <Plus size={16} />
            <span>New Thread</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {convsLoading ? (
            <div className="flex items-center justify-center h-full">
              <RefreshCw className="animate-spin text-indigo-400" size={20} />
            </div>
          ) : (
            conversations?.data?.map((c: any) => (
              <button
                key={c.id}
                onClick={() => setActiveConvId(c.id)}
                className={`w-full text-left px-4 py-3 rounded-xl text-sm font-semibold flex items-center gap-3 transition-all duration-200 border cursor-pointer ${
                  activeConvId === c.id
                    ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/25 shadow-[0_0_15px_-4px_rgba(99,102,241,0.2)]'
                    : 'text-gray-400 border-transparent hover:bg-white/[0.02] hover:text-white'
                }`}
              >
                <MessageSquare size={15} />
                <span className="truncate">{c.title}</span>
              </button>
            ))
          )}
        </div>
      </aside>

      {/* Main Chat Interface */}
      <div className="flex-1 flex flex-col h-full relative overflow-hidden bg-gradient-to-b from-transparent to-black/30">
        {!activeConvId ? (
          <div className="flex-1 flex flex-col items-center justify-center space-y-6 p-8">
            <div className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 p-5 rounded-3xl shadow-[0_0_25px_-5px_rgba(99,102,241,0.25)] animate-pulse">
              <MessageSquare size={36} />
            </div>
            <div className="text-center space-y-2 max-w-md">
              <h2 className="text-2xl font-bold text-white tracking-tight">AI DevOps Copilot</h2>
              <p className="text-gray-500 text-xs font-medium leading-relaxed">
                Select a conversation thread or create a new one to optimize costs, analyze telemetry, and query your multicloud environment.
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Messages box list */}
            <div className="flex-1 overflow-y-auto p-8 space-y-6">
              {msgsLoading ? (
                <div className="flex items-center justify-center h-full">
                  <RefreshCw className="animate-spin text-indigo-400" size={24} />
                </div>
              ) : (
                <AnimatePresence initial={false}>
                  {messages?.data?.map((msg: any) => (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                      className={`flex gap-4 p-5 rounded-2xl max-w-3xl border transition-all duration-300 ${
                        msg.role === 'user'
                          ? 'bg-gradient-to-br from-indigo-500/15 to-indigo-500/5 border-indigo-500/20 ml-auto rounded-tr-none shadow-[0_4px_20px_rgba(99,102,241,0.05)]'
                          : 'glass-card border-white/5 rounded-tl-none'
                      }`}
                    >
                      <div className="flex-1 space-y-2">
                        <span className="text-[9px] text-gray-500 font-extrabold uppercase tracking-widest block">
                          {msg.role === 'user' ? 'User' : 'CloudPilot Copilot'}
                        </span>
                        <p className="text-sm leading-relaxed text-gray-100 whitespace-pre-line font-medium">{msg.content}</p>

                        {/* Display tool call citations */}
                        {msg.citations && Object.keys(msg.citations).length > 0 && (
                          <div className="pt-4 border-t border-white/5 mt-4 space-y-3">
                            <span className="text-[8px] text-gray-500 font-black tracking-widest uppercase block">Sources & Citations:</span>
                            <div className="grid grid-cols-1 gap-2">
                              {Object.keys(msg.citations).map((toolName) => (
                                <details key={toolName} className="text-xs bg-black/30 border border-white/5 rounded-xl p-3 cursor-pointer group transition-all">
                                  <summary className="font-bold text-indigo-400 select-none flex items-center gap-2 group-hover:text-white transition-colors">
                                    <FileText size={13} />
                                    <span>{toolName.replace(/_/g, ' ').toUpperCase()}</span>
                                  </summary>
                                  <pre className="font-mono text-[10px] text-gray-400 mt-2.5 p-3 bg-black/60 rounded-xl overflow-x-auto border border-white/5">
                                    {JSON.stringify(msg.citations[toolName], null, 2)}
                                  </pre>
                                </details>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Suggested Prompts & input bar footer */}
            <div className="p-6 border-t border-white/5 bg-card/5 backdrop-blur-md space-y-4">
              {/* Suggested prompts shortcut chips */}
              <div className="flex flex-wrap gap-2 text-xs">
                {[
                  'Why did my AWS bill increase?',
                  'How much can I save this month?',
                  'Find idle resources'
                ].map((promptText) => (
                  <button
                    key={promptText}
                    onClick={() => handleSuggest(promptText)}
                    className="px-3.5 py-2 bg-white/[0.02] border border-white/5 hover:border-indigo-500/30 rounded-xl text-gray-400 hover:text-white text-xs font-semibold cursor-pointer transition-all"
                  >
                    "{promptText}"
                  </button>
                ))}
              </div>

              {/* Chat Input form */}
              <form onSubmit={handleSubmit} className="flex gap-4">
                <input
                  type="text"
                  required
                  placeholder="Ask about your infrastructure, cost trends, or resources..."
                  value={queryText}
                  onChange={(e) => setQueryText(e.target.value)}
                  className="flex-1 glass-input rounded-2xl px-4 py-3.5 text-white text-sm focus:outline-none placeholder-gray-600 font-medium"
                />
                <button
                  type="submit"
                  disabled={submitQueryMutation.status === 'pending' || !queryText.trim()}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-3.5 rounded-2xl text-sm font-bold flex items-center justify-center transition-all duration-300 shadow-[0_4px_15px_-2px_rgba(99,102,241,0.35)] hover:-translate-y-0.5 disabled:opacity-50 disabled:pointer-events-none cursor-pointer"
                >
                  {submitQueryMutation.status === 'pending' ? (
                    <RefreshCw className="animate-spin" size={18} />
                  ) : (
                    <Send size={18} />
                  )}
                </button>
              </form>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
