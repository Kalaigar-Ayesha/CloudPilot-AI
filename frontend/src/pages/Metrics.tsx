import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { RefreshCw, Activity, Cpu, Server } from 'lucide-react';
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

export const Metrics: React.FC = () => {
  // Query Telemetry metrics dashboard averages
  const { data: telemetry, isLoading } = useQuery<any>({
    queryKey: ['telemetryDashboard'],
    queryFn: () => api.get('/monitoring/metrics/dashboard?project_id=00000000-0000-0000-0000-000000000000')
  });

  const chartData = [
    { time: '10:00', cpu: 34, memory: 56 },
    { time: '11:00', cpu: 45, memory: 58 },
    { time: '12:00', cpu: 30, memory: 55 },
    { time: '13:00', cpu: 52, memory: 60 },
    { time: '14:00', cpu: 40, memory: 57 },
  ];

  const CustomCpuTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="glass-panel p-3 border border-white/10 rounded-2xl shadow-xl text-xs font-semibold">
          <p className="text-gray-400 mb-1">{payload[0].payload.time}</p>
          <p className="text-indigo-400 font-extrabold">CPU: {payload[0].value}%</p>
        </div>
      );
    }
    return null;
  };

  const CustomMemoryTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="glass-panel p-3 border border-white/10 rounded-2xl shadow-xl text-xs font-semibold">
          <p className="text-gray-400 mb-1">{payload[0].payload.time}</p>
          <p className="text-amber-400 font-extrabold">Memory: {payload[0].value}%</p>
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
          Telemetry Metrics
        </h1>
        <p className="text-gray-500 text-xs font-semibold uppercase tracking-widest">Real-time performance utilization dashboards</p>
      </motion.div>

      {/* Utilization cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Average Workspace CPU */}
        <div className="glass-card p-6 rounded-3xl flex items-center justify-between border border-white/5 hover:border-indigo-500/30 transition-all relative overflow-hidden group">
          <div className="space-y-1 z-10">
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest block">AVERAGE WORKSPACE CPU</span>
            <p className="text-3xl font-black text-white tracking-tight mt-3">
              {telemetry?.data?.avg_cpu ? telemetry.data.avg_cpu.toFixed(1) : '42.5'}%
            </p>
          </div>
          <div className="text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 p-3 rounded-2xl shadow-[0_0_15px_-3px_rgba(99,102,241,0.2)] group-hover:scale-110 group-hover:rotate-3 transition-all duration-300">
            <Cpu size={22} />
          </div>
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/0 to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
        </div>

        {/* Average Workspace Memory */}
        <div className="glass-card p-6 rounded-3xl flex items-center justify-between border border-white/5 hover:border-amber-500/30 transition-all relative overflow-hidden group">
          <div className="space-y-1 z-10">
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest block">AVERAGE WORKSPACE MEMORY</span>
            <p className="text-3xl font-black text-white tracking-tight mt-3">
              {telemetry?.data?.avg_memory ? telemetry.data.avg_memory.toFixed(1) : '57.8'}%
            </p>
          </div>
          <div className="text-amber-400 bg-amber-500/10 border border-amber-500/20 p-3 rounded-2xl shadow-[0_0_15px_-3px_rgba(245,158,11,0.2)] group-hover:scale-110 group-hover:rotate-3 transition-all duration-300">
            <Server size={22} />
          </div>
          <div className="absolute inset-0 bg-gradient-to-br from-amber-500/0 to-amber-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
        </div>
      </motion.div>

      {/* Utilization charts */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CPU Chart */}
        <div className="glass-panel p-6 rounded-3xl border border-white/5 shadow-2xl relative overflow-hidden">
          <h2 className="text-sm font-bold text-white mb-6 tracking-tight">CPU Utilization Timeline</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.25}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255, 255, 255, 0.03)" vertical={false} />
                <XAxis dataKey="time" stroke="rgba(255, 255, 255, 0.2)" fontSize={10} tickLine={false} axisLine={false} tickMargin={10} />
                <YAxis stroke="rgba(255, 255, 255, 0.2)" fontSize={10} tickLine={false} axisLine={false} tickMargin={10} />
                <Tooltip content={<CustomCpuTooltip />} />
                <Area type="monotone" dataKey="cpu" stroke="#6366f1" fillOpacity={1} fill="url(#colorCpu)" strokeWidth={2.5} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Memory Chart */}
        <div className="glass-panel p-6 rounded-3xl border border-white/5 shadow-2xl relative overflow-hidden">
          <h2 className="text-sm font-bold text-white mb-6 tracking-tight">Memory Utilization Timeline</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorMemory" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.25}/>
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255, 255, 255, 0.03)" vertical={false} />
                <XAxis dataKey="time" stroke="rgba(255, 255, 255, 0.2)" fontSize={10} tickLine={false} axisLine={false} tickMargin={10} />
                <YAxis stroke="rgba(255, 255, 255, 0.2)" fontSize={10} tickLine={false} axisLine={false} tickMargin={10} />
                <Tooltip content={<CustomMemoryTooltip />} />
                <Area type="monotone" dataKey="memory" stroke="#f59e0b" fillOpacity={1} fill="url(#colorMemory)" strokeWidth={2.5} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};
