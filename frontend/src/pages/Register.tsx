import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Sliders, Lock, Mail, RefreshCw, UserPlus, Eye, EyeOff, 
  Sparkles, TrendingUp, ShieldCheck, CheckCircle2, ArrowRight
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

const RECOMMENDATIONS = [
  { provider: 'AWS', action: 'Terminate idle EC2 instances in us-east-1', savings: '$340/mo' },
  { provider: 'GCP', action: 'Resize oversized Cloud SQL DB (16GB to 8GB)', savings: '$195/mo' },
  { provider: 'Azure', action: 'Convert Dev workloads to Spot Instances', savings: '$510/mo' },
];

export const Register: React.FC = () => {
  const navigate = useNavigate();
  const { registerUser } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [recIndex, setRecIndex] = useState(0);

  // Cycle recommendations
  useEffect(() => {
    const interval = setInterval(() => {
      setRecIndex((prev) => (prev + 1) % RECOMMENDATIONS.length);
    }, 4500);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await registerUser(email, password);
      navigate('/login');
    } catch (err: any) {
      let errMsg = 'Registration failed. Try again.';
      if (err?.errors?.[0]?.detail) {
        errMsg = err.errors[0].detail.replace('Value error, ', '');
      } else if (err?.detail) {
        if (Array.isArray(err.detail)) {
          errMsg = err.detail[0]?.msg || errMsg;
        } else if (typeof err.detail === 'string') {
          errMsg = err.detail;
        }
      } else if (err?.message) {
        errMsg = err.message;
      }
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center lg:grid lg:grid-cols-12 overflow-hidden relative">
      {/* Ambient background glows */}
      <div className="absolute top-1/4 right-1/4 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[140px] pointer-events-none z-0" />
      <div className="absolute bottom-1/4 left-1/4 w-[600px] h-[600px] bg-secondary/5 rounded-full blur-[160px] pointer-events-none z-0" />

      {/* LEFT COLUMN: Visual Showcase Panel (Desktop Only) */}
      <div className="lg:col-span-5 hidden lg:flex flex-col justify-between p-12 h-full relative overflow-hidden bg-card border-r border-border z-10">
        <div className="absolute inset-0 cyber-grid opacity-15 pointer-events-none" />
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-primary/10 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-success/10 rounded-full blur-[120px] pointer-events-none" />

        {/* Brand Header */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="bg-primary/10 p-2.5 rounded-xl text-primary border border-primary/20 shadow-[0_0_20px_rgba(37,99,235,0.15)]">
            <Sliders size={22} className="rotate-95" />
          </div>
          <div>
            <span className="font-extrabold text-2xl tracking-tight text-primaryText block">
              CloudPilot AI
            </span>
            <span className="text-[9px] uppercase tracking-[0.25em] text-mutedText font-extrabold block -mt-1">
              Enterprise Cost Engine
            </span>
          </div>
        </div>

        {/* Live Dashboard Demo Cards */}
        <div className="relative z-10 space-y-6 my-auto">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold">
              <Sparkles size={12} />
              <span>Developer Workspace Setup</span>
            </div>
            <h2 className="text-3xl font-black text-primaryText leading-tight font-outfit tracking-tight">
              Create workspace, <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-accent to-success">
                scale your efficiency.
              </span>
            </h2>
            <p className="text-secondaryText text-sm max-w-md font-medium">
              Secure your account in moments. Join hundreds of DevOps engineers automating their cloud architecture and saving on cost.
            </p>
          </div>

          {/* Widget 1: Platform Checklist */}
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="bg-secondaryCard rounded-2xl p-5 border border-border space-y-3.5 shadow-lg hover:border-primary/20 transition-all duration-300"
          >
            <span className="text-xs font-bold text-secondaryText uppercase tracking-wider block">Enterprise Platform Features</span>
            <div className="space-y-2.5">
              <div className="flex items-start gap-2.5 text-xs text-secondaryText font-medium">
                <CheckCircle2 size={15} className="text-success mt-0.5 shrink-0" />
                <span>Automated anomaly detection across AWS, GCP, and Azure.</span>
              </div>
              <div className="flex items-start gap-2.5 text-xs text-secondaryText font-medium">
                <CheckCircle2 size={15} className="text-success mt-0.5 shrink-0" />
                <span>Interactive AI Copilot for code repository optimizations.</span>
              </div>
              <div className="flex items-start gap-2.5 text-xs text-secondaryText font-medium">
                <CheckCircle2 size={15} className="text-success mt-0.5 shrink-0" />
                <span>Bank-grade AES-256 credentials encryption.</span>
              </div>
            </div>
          </motion.div>

          {/* Widget 2: Dynamic Live Recommendations */}
          <div className="space-y-2">
            <span className="text-xs font-bold text-mutedText uppercase tracking-widest pl-1">Active AI Recommendation</span>
            <div className="h-[96px] relative">
              <AnimatePresence mode="wait">
                <motion.div
                  key={recIndex}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.35 }}
                  className="absolute inset-0 bg-secondaryCard border border-border rounded-2xl p-4 flex gap-4 items-center shadow-md"
                >
                  <div className="bg-primary/10 text-primary border border-primary/20 p-2.5 rounded-xl shrink-0">
                    <Sparkles size={18} className="animate-pulse" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] uppercase font-extrabold px-1.5 py-0.5 rounded bg-card border border-border text-primaryText font-mono">
                        {RECOMMENDATIONS[recIndex].provider}
                      </span>
                      <span className="text-xs font-bold text-success">
                        Saves {RECOMMENDATIONS[recIndex].savings}
                      </span>
                    </div>
                    <p className="text-xs text-secondaryText font-medium truncate mt-1">
                      {RECOMMENDATIONS[recIndex].action}
                    </p>
                  </div>
                </motion.div>
              </AnimatePresence>
            </div>
          </div>

          {/* Widget 3: Cloud Integrations */}
          <div className="flex items-center gap-6 pt-2">
            <div className="flex items-center gap-2 text-xs text-secondaryText font-semibold">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-success"></span>
              </span>
              <span>AWS active</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-secondaryText font-semibold">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-success"></span>
              </span>
              <span>Azure linked</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-secondaryText font-semibold">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-success"></span>
              </span>
              <span>GCP optimized</span>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="relative z-10 flex items-center gap-2 text-xs text-mutedText font-semibold">
          <ShieldCheck size={14} className="text-primary" />
          <span>SOC 2 Type II Certified Cloud Data Security</span>
        </div>
      </div>

      {/* RIGHT COLUMN: Register Card Form (Centered and Animated) */}
      <div className="lg:col-span-7 w-full flex items-center justify-center p-6 sm:p-12 relative z-10">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
          className="w-full max-w-md bg-card border border-border rounded-2xl p-8 sm:p-10 shadow-2xl relative overflow-hidden"
        >
          {/* Card subtle lighting effect */}
          <div className="absolute -top-16 -right-16 w-32 h-32 bg-primary/10 rounded-full blur-2xl pointer-events-none" />

          {/* Logo visible only on mobile/tablet */}
          <div className="flex flex-col items-center mb-8 lg:hidden">
            <div className="bg-primary/10 p-3 rounded-2xl text-primary border border-primary/20 mb-3 shadow-[0_0_20px_rgba(37,99,235,0.15)]">
              <Sliders size={24} className="rotate-95" />
            </div>
            <span className="font-extrabold text-2xl tracking-tight text-primaryText">
              CloudPilot AI
            </span>
            <p className="text-mutedText text-[9px] uppercase tracking-widest font-extrabold mt-1">Enterprise Cost Engine</p>
          </div>

          {/* CARD HEADER */}
          <div className="mb-8 text-left">
            <h2 className="text-3xl font-black text-primaryText tracking-tight font-outfit mb-2">Create Account</h2>
            <p className="text-secondaryText text-sm font-medium">Register a new administrator workspace for your cloud environments.</p>
          </div>

          {/* Error Banner */}
          <AnimatePresence mode="wait">
            {error && (
              <motion.div 
                initial={{ opacity: 0, height: 0, scale: 0.95 }}
                animate={{ opacity: 1, height: 'auto', scale: 1 }}
                exit={{ opacity: 0, height: 0, scale: 0.95 }}
                transition={{ duration: 0.2 }}
                className="bg-danger/10 border border-danger/20 text-danger px-4 py-3 rounded-xl text-xs font-bold text-center mb-6 flex items-center justify-center gap-2"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-danger shrink-0" />
                <span>{error}</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* CARD BODY */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email Address */}
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold text-secondaryText block uppercase tracking-widest pl-1">Email Address</label>
              <div className="relative group">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-mutedText transition-colors group-focus-within:text-primary animate-pulse" size={16} />
                <input
                  type="email"
                  required
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-secondaryCard border border-border text-primaryText placeholder:text-mutedText focus:border-primary focus:ring-1 focus:ring-primary rounded-xl pl-11 pr-4 py-3.5 text-sm transition-all font-medium focus:outline-none"
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold text-secondaryText block uppercase tracking-widest pl-1">Password</label>
              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-mutedText transition-colors group-focus-within:text-primary" size={16} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-secondaryCard border border-border text-primaryText placeholder:text-mutedText focus:border-primary focus:ring-1 focus:ring-primary rounded-xl pl-11 pr-12 py-3.5 text-sm transition-all font-medium focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-mutedText hover:text-primaryText transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              <p className="text-[10px] text-mutedText pl-1 font-medium">
                Must be at least 8 characters with letters, numbers and symbols.
              </p>
            </div>

            {/* Terms and Conditions Checkbox */}
            <div className="flex items-start px-1 py-1">
              <label className="flex items-start gap-2.5 cursor-pointer text-xs text-secondaryText select-none">
                <input 
                  type="checkbox" 
                  required
                  className="rounded border-border bg-secondaryCard text-primary focus:ring-primary focus:ring-offset-0 mt-0.5" 
                />
                <span>I agree to the <a href="#terms" onClick={(e) => e.preventDefault()} className="text-primary hover:text-primaryText underline font-semibold">Terms of Service</a> and <a href="#privacy" onClick={(e) => e.preventDefault()} className="text-primary hover:text-primaryText underline font-semibold">Privacy Policy</a>.</span>
              </label>
            </div>

            {/* Submit Button */}
            <motion.button
              type="submit"
              disabled={loading}
              whileTap={{ scale: 0.98 }}
              className="w-full bg-primary hover:bg-primary/95 text-white py-3.5 rounded-xl text-sm font-bold flex items-center justify-center gap-2 transition-all duration-300 shadow-[0_4px_15px_-2px_rgba(37,99,235,0.25)] hover:shadow-[0_4px_20px_rgba(37,99,235,0.35)] hover:-translate-y-0.5 disabled:opacity-50 disabled:pointer-events-none cursor-pointer"
            >
              {loading ? (
                <>
                  <RefreshCw className="animate-spin" size={16} />
                  <span>Registering Account...</span>
                </>
              ) : (
                <>
                  <span>Create Developer Account</span>
                  <UserPlus size={16} />
                </>
              )}
            </motion.button>
          </form>

          {/* CARD FOOTER */}
          <div className="text-center text-xs text-mutedText pt-6 mt-6 border-t border-border font-medium">
            Already have an account?{' '}
            <Link to="/login" className="text-primary hover:text-primaryText font-bold transition-colors ml-1 inline-flex items-center gap-0.5">
              <span>Sign In</span>
              <ArrowRight size={12} className="inline" />
            </Link>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

