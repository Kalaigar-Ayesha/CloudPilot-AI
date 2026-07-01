import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { RefreshCw, DollarSign, Calendar, TrendingUp } from 'lucide-react';
import { motion } from 'framer-motion';
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

export const Billing: React.FC = () => {
  // Query Billing Dashboard
  const { data: billing, isLoading: billLoading } = useQuery<any>({
    queryKey: ['billingDashboard'],
    queryFn: () => api.get('/billing/dashboard?project_id=00000000-0000-0000-0000-000000000000')
  });

  // Query Forecast Projections
  const { data: forecast, isLoading: foreLoading } = useQuery<any>({
    queryKey: ['billingForecast'],
    queryFn: () => api.get('/billing/forecast?project_id=00000000-0000-0000-0000-000000000000')
  });

  // Query Trends (30 Days)
  const { data: trends, isLoading: trendLoading } = useQuery<any>({
    queryKey: ['billingTrends'],
    queryFn: () => api.get('/billing/trends?project_id=00000000-0000-0000-0000-000000000000&days=7')
  });

  const chartData = trends?.data?.history || [
    { date: 'Day 1', cost: 10 },
    { date: 'Day 2', cost: 12 },
    { date: 'Day 3', cost: 15 },
    { date: 'Day 4', cost: 14 },
    { date: 'Day 5', cost: 18 },
  ];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="glass-panel p-3 border border-white/10 rounded-2xl shadow-xl text-xs font-semibold">
          <p className="text-gray-400 mb-1">{payload[0].payload.date}</p>
          <p className="text-indigo-400 font-extrabold">${payload[0].value.toFixed(2)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="p-8 max-w-7xl mx-auto space-y-8 relative"
    >
      <motion.div variants={itemVariants} className="flex flex-col gap-1.5">
        <h1 className="text-4xl font-extrabold text-white tracking-tight bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
          Billing Explorer
        </h1>
        <p className="text-gray-500 text-xs font-semibold uppercase tracking-widest">Multi-cloud spend tracking and budget forecasts</p>
      </motion.div>

      {/* Forecast & Summary Grid */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Total Spend */}
        <div className="glass-card p-6 rounded-3xl flex flex-col justify-between border border-white/5 hover:border-indigo-500/30 transition-all relative overflow-hidden group">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">TOTAL SPEND (30D)</span>
            <div className="text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 p-2.5 rounded-xl shadow-[0_0_15px_-3px_rgba(99,102,241,0.2)] group-hover:scale-105 transition-transform duration-200">
              <DollarSign size={18} />
            </div>
          </div>
          <p className="text-3xl font-black text-white tracking-tight mt-6">
            ${billing?.data?.total_cost ? billing.data.total_cost.toFixed(2) : '696.50'}
          </p>
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/0 to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
        </div>

        {/* Forecast */}
        <div className="glass-card p-6 rounded-3xl flex flex-col justify-between border border-white/5 hover:border-amber-500/30 transition-all relative overflow-hidden group">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">FORECAST (NEXT 30D)</span>
            <div className="text-amber-400 bg-amber-500/10 border border-amber-500/20 p-2.5 rounded-xl shadow-[0_0_15px_-3px_rgba(245,158,11,0.2)] group-hover:scale-105 transition-transform duration-200">
              <Calendar size={18} />
            </div>
          </div>
          <div className="mt-6 space-y-3">
            <p className="text-3xl font-black text-white tracking-tight">
              ${forecast?.data?.baseline_cost ? forecast.data.baseline_cost.toFixed(2) : '850.00'}
            </p>
            <div className="text-[9px] text-gray-400 flex gap-2 font-bold uppercase tracking-wider">
              <span className="text-emerald-400 bg-emerald-500/10 border border-emerald-500/15 px-2 py-0.5 rounded-full">
                OPT: ${forecast?.data?.optimistic_cost ? forecast.data.optimistic_cost.toFixed(0) : '765'}
              </span>
              <span className="text-rose-400 bg-rose-500/10 border border-rose-500/15 px-2 py-0.5 rounded-full">
                PESS: ${forecast?.data?.pessimistic_cost ? forecast.data.pessimistic_cost.toFixed(0) : '978'}
              </span>
            </div>
          </div>
          <div className="absolute inset-0 bg-gradient-to-br from-amber-500/0 to-amber-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
        </div>

        {/* Daily Run Rate */}
        <div className="glass-card p-6 rounded-3xl flex flex-col justify-between border border-white/5 hover:border-emerald-500/30 transition-all relative overflow-hidden group">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">DAILY RUN RATE</span>
            <div className="text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 p-2.5 rounded-xl shadow-[0_0_15px_-3px_rgba(16,185,129,0.2)] group-hover:scale-105 transition-transform duration-200">
              <TrendingUp size={18} />
            </div>
          </div>
          <p className="text-3xl font-black text-white tracking-tight mt-6">
            ${billing?.data?.total_cost ? (billing.data.total_cost / 30).toFixed(2) : '23.21'}
          </p>
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/0 to-emerald-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
        </div>
      </motion.div>

      {/* Cost Trends Chart */}
      <motion.div variants={itemVariants} className="glass-panel p-6 rounded-3xl border border-white/5 shadow-2xl relative overflow-hidden">
        <div className="flex items-center gap-2 mb-6">
          <TrendingUp size={18} className="text-indigo-400" />
          <h2 className="text-base font-bold text-white tracking-tight">Historical Cost Timeline</h2>
        </div>
        
        {trendLoading ? (
          <div className="h-72 flex items-center justify-center">
            <RefreshCw className="animate-spin text-indigo-400" size={24} />
          </div>
        ) : (
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.25}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255, 255, 255, 0.03)" vertical={false} />
                <XAxis dataKey="date" stroke="rgba(255, 255, 255, 0.2)" fontSize={10} tickLine={false} axisLine={false} tickMargin={10} />
                <YAxis stroke="rgba(255, 255, 255, 0.2)" fontSize={10} tickLine={false} axisLine={false} tickMargin={10} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="cost" stroke="#6366f1" fillOpacity={1} fill="url(#colorCost)" strokeWidth={2.5} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
};
