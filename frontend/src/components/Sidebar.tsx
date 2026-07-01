import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Cloud,
  Activity,
  Zap,
  MessageSquare,
  LogOut,
  Sliders,
  DollarSign
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Sidebar: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const links = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/cloud', label: 'Cloud Accounts', icon: Cloud },
    { to: '/metrics', label: 'Telemetry Metrics', icon: Activity },
    { to: '/billing', label: 'Billing Explorer', icon: DollarSign },
    { to: '/optimization', label: 'Optimization', icon: Zap },
    { to: '/copilot', label: 'AI DevOps Copilot', icon: MessageSquare },
  ];

  return (
    <aside className="w-64 bg-card/25 backdrop-blur-xl border-r border-white/5 flex flex-col h-screen fixed left-0 top-0 text-gray-100 z-30 shadow-[4px_0_24px_rgba(0,0,0,0.5)]">
      {/* Brand Logo header */}
      <div className="p-6 border-b border-white/5 flex items-center gap-3">
        <div className="bg-indigo-500/10 p-2.5 rounded-xl text-indigo-400 border border-indigo-500/20 shadow-[0_0_15px_-3px_rgba(99,102,241,0.3)]">
          <Sliders size={18} />
        </div>
        <div className="flex flex-col">
          <span className="font-extrabold text-base tracking-wider bg-gradient-to-r from-indigo-400 via-sky-300 to-emerald-400 bg-clip-text text-transparent">
            CloudPilot AI
          </span>
          <span className="text-[9px] font-bold text-gray-500 tracking-widest uppercase mt-0.5">DEV OPS PILOT</span>
        </div>
      </div>

      {/* Navigation links */}
      <nav className="flex-1 px-3 py-6 space-y-1 relative">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = location.pathname === link.to;

          return (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `group relative flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-300 outline-none ${
                  isActive
                    ? 'text-white'
                    : 'text-gray-400 hover:text-gray-200'
                }`
              }
            >
              {/* Sliding active indicator capsule */}
              {isActive && (
                <motion.div
                  layoutId="activeNav"
                  className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 to-sky-500/5 border border-indigo-500/20 rounded-xl -z-10 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]"
                  transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                />
              )}

              <Icon 
                size={18} 
                className={`transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3 ${
                  isActive ? 'text-indigo-400' : 'text-gray-400 group-hover:text-gray-300'
                }`} 
              />
              <span className="relative z-10">{link.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* User profile footer */}
      <div className="p-4 border-t border-white/5 bg-black/20 flex items-center justify-between">
        <div className="min-w-0">
          <p className="text-[11px] text-gray-400 font-semibold truncate leading-none">{user?.email}</p>
          <span className="inline-block mt-2 px-2 py-0.5 text-[8px] bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-black rounded-full uppercase tracking-wider">
            {user?.role}
          </span>
        </div>
        <button
          onClick={logout}
          className="text-gray-400 hover:text-red-400 p-2.5 rounded-xl hover:bg-red-500/10 hover:border-red-500/20 border border-transparent transition-all duration-200 shadow-sm"
          title="Logout"
        >
          <LogOut size={16} />
        </button>
      </div>
    </aside>
  );
};
