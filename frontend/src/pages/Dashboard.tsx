import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, PieChart, Pie, Cell } from 'recharts';
import { DollarSign, ShieldAlert, Award, Zap, TrendingUp, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';

const COLORS = ['#6366f1', '#10b981', '#f59e0b'];

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

export const Dashboard: React.FC = () => {
  // Query Billing Dashboard
  const { data: billing, isLoading: billLoading } = useQuery<any>({
    queryKey: ['billingDashboard'],
    queryFn: () => api.get('/billing/dashboard?project_id=00000000-0000-0000-0000-000000000000')
  });

  // Query Optimization Summary
  const { data: opt, isLoading: optLoading } = useQuery<any>({
    queryKey: ['optSummary'],
    queryFn: () => api.get('/optimization/savings?project_id=00000000-0000-0000-0000-000000000000')
  });

  // Query Telemetry metrics averages
  const { data: telemetry, isLoading: telLoading } = useQuery<any>({
    queryKey: ['telemetryDashboard'],
    queryFn: () => api.get('/monitoring/metrics/dashboard?project_id=00000000-0000-0000-0000-000000000000')
  });

  // Mock trend data
  const trendData = [
    { date: 'June 25', cost: 120 },
    { date: 'June 26', cost: 115 },
    { date: 'June 27', cost: 140 },
    { date: 'June 28', cost: 135 },
    { date: 'June 29', cost: 155 },
    { date: 'June 30', cost: 145 },
  ];

  const pieData = billing?.data?.by_provider
    ? Object.keys(billing.data.by_provider).map((key) => ({
        name: key.toUpperCase(),
        value: billing.data.by_provider[key]
      }))
    : [
        { name: 'AWS', value: 340.50 },
        { name: 'AZURE', value: 210.20 },
        { name: 'GCP', value: 145.80 }
      ];

  const savingsValue = opt?.data?.total_savings_monthly || 75.00;
  const avgCpu = telemetry?.data?.avg_cpu || 42.5;

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
      {/* Header section */}
      <motion.div variants={itemVariants} className="flex flex-col gap-1.5">
        <h1 className="text-4xl font-extrabold text-white tracking-tight bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
          Dashboard
        </h1>
        <p className="text-gray-500 text-xs font-semibold uppercase tracking-widest">Unified multicloud overview for CloudPilot AI</p>
      </motion.div>

      {/* Grid summary cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Monthly Spend */}
        <div className="glass-card p-6 rounded-2xl flex items-center justify-between group border border-white/5 relative overflow-hidden">
          <div className="space-y-1 z-10">
            <span className="text-[10px] text-gray-500 font-extrabold uppercase tracking-widest block">MONTHLY SPEND</span>
            <span className="text-3xl font-extrabold text-white tracking-tight block">
              ${billing?.data?.total_cost ? billing.data.total_cost.toFixed(2) : '696.50'}
            </span>
          </div>
          <div className="text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 p-3 rounded-2xl shadow-[0_0_15px_-3px_rgba(99,102,241,0.2)] group-hover:scale-110 group-hover:rotate-3 transition-all duration-300">
            <DollarSign size={20} />
          </div>
          {/* Subtle back ambient glow */}
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/0 to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
        </div>

        {/* Monthly Savings */}
        <div className="glass-card p-6 rounded-2xl flex items-center justify-between group border border-white/5 relative overflow-hidden">
          <div className="space-y-1 z-10">
            <span className="text-[10px] text-gray-500 font-extrabold uppercase tracking-widest block">MONTHLY SAVINGS</span>
            <span className="text-3xl font-extrabold text-emerald-400 tracking-tight block">
              ${savingsValue.toFixed(2)}
            </span>
          </div>
          <div className="text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 p-3 rounded-2xl shadow-[0_0_15px_-3px_rgba(16,185,129,0.2)] group-hover:scale-110 group-hover:rotate-3 transition-all duration-300">
            <Zap size={20} />
          </div>
          {/* Subtle back ambient glow */}
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/0 to-emerald-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
        </div>

        {/* Average CPU */}
        <div className="glass-card p-6 rounded-2xl flex items-center justify-between group border border-white/5 relative overflow-hidden">
          <div className="space-y-1 z-10">
            <span className="text-[10px] text-gray-500 font-extrabold uppercase tracking-widest block">AVERAGE CPU</span>
            <span className="text-3xl font-extrabold text-white tracking-tight block">
              {avgCpu.toFixed(1)}%
            </span>
          </div>
          <div className="text-amber-400 bg-amber-500/10 border border-amber-500/20 p-3 rounded-2xl shadow-[0_0_15px_-3px_rgba(245,158,11,0.2)] group-hover:scale-110 group-hover:rotate-3 transition-all duration-300">
            <Award size={20} />
          </div>
          {/* Subtle back ambient glow */}
          <div className="absolute inset-0 bg-gradient-to-br from-amber-500/0 to-amber-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
        </div>

        {/* Security Alerts */}
        <div className="glass-card p-6 rounded-2xl flex items-center justify-between group border border-white/5 relative overflow-hidden">
          <div className="space-y-1 z-10">
            <span className="text-[10px] text-gray-500 font-extrabold uppercase tracking-widest block">SECURITY ALERTS</span>
            <span className="text-3xl font-extrabold text-rose-400 tracking-tight block">
              2 Active
            </span>
          </div>
          <div className="text-rose-400 bg-rose-500/10 border border-rose-500/20 p-3 rounded-2xl shadow-[0_0_15px_-3px_rgba(239,68,68,0.2)] group-hover:scale-110 group-hover:rotate-3 transition-all duration-300">
            <ShieldAlert size={20} />
          </div>
          {/* Subtle back ambient glow */}
          <div className="absolute inset-0 bg-gradient-to-br from-rose-500/0 to-rose-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
        </div>
      </motion.div>

      {/* Charts section */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Area Chart */}
        <div className="glass-panel p-6 rounded-3xl lg:col-span-2 shadow-2xl border border-white/5 relative overflow-hidden">
          <div className="flex items-center gap-2 mb-6">
            <TrendingUp size={18} className="text-indigo-400" />
            <h2 className="text-base font-bold text-white tracking-tight">Spend Trend (Last 7 Days)</h2>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.25}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" stroke="rgba(255, 255, 255, 0.2)" fontSize={10} tickLine={false} axisLine={false} tickMargin={10} />
                <YAxis stroke="rgba(255, 255, 255, 0.2)" fontSize={10} tickLine={false} axisLine={false} tickMargin={10} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="cost" stroke="#6366f1" fillOpacity={1} fill="url(#colorCost)" strokeWidth={2.5} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Cost Distribution Pie Chart */}
        <div className="glass-panel p-6 rounded-3xl flex flex-col items-center justify-between border border-white/5 shadow-2xl relative overflow-hidden">
          <div className="w-full flex items-center justify-between border-b border-white/5 pb-4 mb-4">
            <h2 className="text-base font-bold text-white tracking-tight">Cost Distribution</h2>
          </div>
          
          <div className="h-48 w-48 relative flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} innerRadius={60} outerRadius={76} paddingAngle={4} dataKey="value">
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: 'rgba(10, 15, 30, 0.85)', borderColor: 'rgba(255, 255, 255, 0.08)', color: '#FFF', borderRadius: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute flex flex-col items-center justify-center">
              <span className="text-[10px] text-gray-500 font-extrabold uppercase tracking-widest leading-none">TOTAL SPEND</span>
              <span className="text-xl font-extrabold text-white mt-1.5">${billing?.data?.total_cost ? billing.data.total_cost.toFixed(0) : '696'}</span>
            </div>
          </div>

          <div className="flex justify-center gap-4 mt-6 text-[10px] font-bold uppercase tracking-wider w-full">
            {pieData.map((d, index) => (
              <div key={d.name} className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                <span className="text-gray-400">{d.name}</span>
              </div>
            ))}
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};
