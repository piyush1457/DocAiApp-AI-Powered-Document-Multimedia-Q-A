import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { motion, useMotionValue, useSpring, useTransform, AnimatePresence } from 'framer-motion';
import {
  FileText,
  AudioLines,
  Video,
  Mail,
  Lock,
  ShieldCheck,
  ChevronRight,
  Loader2,
  Clock
} from 'lucide-react';
import { api } from '../api/axios';
import { useAuthStore } from '../store/useAuthStore';

// --- Visual Components ---

const FloatingCard = ({ children, className, delay = 0 }: { children: React.ReactNode, className?: string, delay?: number }) => (
  <motion.div
    initial={{ y: 20, opacity: 0 }}
    animate={{
      y: [0, -10, 0],
      opacity: 1
    }}
    transition={{
      y: {
        duration: 4,
        repeat: Infinity,
        ease: "easeInOut",
        delay
      },
      opacity: { duration: 0.8, delay }
    }}
    className={`absolute rounded-2xl glass p-4 shadow-2xl ${className}`}
  >
    {children}
  </motion.div>
);

const DocumentPreview = () => (
  <FloatingCard className="top-[-80px] left-[-40px] w-52 z-20" delay={0.2}>
    <div className="flex items-start gap-3">
      <div className="p-2 rounded-lg bg-accent/20">
        <FileText className="w-5 h-5 text-accent" />
      </div>
      <div className="space-y-2 flex-1">
        <div className="h-2 w-full bg-white/10 rounded" />
        <div className="h-2 w-2/3 bg-white/10 rounded" />
        <div className="h-2 w-1/2 bg-white/10 rounded" />
      </div>
    </div>
  </FloatingCard>
);

const AudioWaveform = () => (
  <FloatingCard className="bottom-[-100px] left-[10%] w-60 z-10" delay={0.5}>
    <div className="flex items-center gap-3">
      <div className="p-2 rounded-lg bg-emerald-500/20">
        <AudioLines className="w-5 h-5 text-emerald-500" />
      </div>
      <div className="flex-1 flex items-end gap-1 h-8">
        {[0.4, 0.7, 0.5, 0.9, 0.6, 0.8, 0.4, 0.7].map((h, i) => (
          <motion.div
            key={i}
            animate={{ height: [`${h * 100}%`, `${(1 - h) * 100}%`, `${h * 100}%`] }}
            transition={{ duration: 1.5 + i * 0.2, repeat: Infinity }}
            className="flex-1 bg-emerald-500/40 rounded-full"
          />
        ))}
      </div>
    </div>
  </FloatingCard>
);

const VideoTimestamp = () => (
  <FloatingCard className="top-[40%] right-[-50px] w-48 z-30" delay={0.8}>
    <div className="flex items-center gap-3">
      <div className="p-2 rounded-lg bg-rose-500/20">
        <Video className="w-5 h-5 text-rose-500" />
      </div>
      <div className="flex flex-col">
        <span className="text-[10px] text-textSecondary uppercase tracking-wider font-bold">Timestamp</span>
        <div className="flex items-center gap-1 text-sm font-mono text-white">
          <Clock className="w-3 h-3 text-rose-500" />
          01:24:45
        </div>
      </div>
    </div>
  </FloatingCard>
);

// --- Main Page Component ---

export const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const setTokens = useAuthStore((state) => state.setTokens);

  // Parallax Effect
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const springConfig = { damping: 25, stiffness: 150 };
  const rotateX = useSpring(useTransform(mouseY, [-300, 300], [10, -10]), springConfig);
  const rotateY = useSpring(useTransform(mouseX, [-300, 300], [-10, 10]), springConfig);

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    mouseX.set(e.clientX - centerX);
    mouseY.set(e.clientY - centerY);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);

      const response = await api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const { access_token, refresh_token } = response.data;
      setTokens(access_token, refresh_token);
      navigate('/');
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Invalid email or password');
      } else {
        setError('Something went wrong. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="flex min-h-screen w-full bg-background overflow-hidden"
      onMouseMove={handleMouseMove}
    >
      {/* Left Section (60%) */}
      <div className="hidden lg:flex w-[60%] relative flex-col justify-center px-20 border-r border-white/5">
        {/* Background Glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-accent/10 blur-[120px] rounded-full pointer-events-none" />

        <motion.div
          style={{ perspective: 1000, rotateX, rotateY }}
          className="relative z-10"
        >
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-7xl font-extrabold tracking-tight text-white mb-6 leading-[1.1]"
          >
            Ask Anything. <br />
            <span className="text-accent">From Any File.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
            className="text-xl text-textSecondary max-w-lg leading-relaxed"
          >
            AI-powered answers from documents, videos, and audio with precise timestamps.
          </motion.p>

          {/* Floating Elements Container */}
          <div className="absolute inset-0 pointer-events-none overflow-visible">
            <DocumentPreview />
            <AudioWaveform />
            <VideoTimestamp />
          </div>
        </motion.div>

        {/* Brand/Logo */}
        <div className="absolute top-12 left-20 flex items-center gap-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-amber flex items-center justify-center shadow-amber-glow">
            <ShieldCheck className="w-6 h-6 text-background" />
          </div>
          <span className="text-2xl font-bold tracking-tighter text-white">DocAiApp</span>
        </div>
      </div>

      {/* Right Section (40%) */}
      <div className="w-full lg:w-[40%] flex flex-col items-center justify-center p-8 sm:p-12 relative">
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          className="w-full max-w-md"
        >
          <div className="mb-10 lg:hidden flex flex-col items-center">
            <div className="w-12 h-12 rounded-2xl bg-gradient-amber flex items-center justify-center shadow-amber-glow mb-4">
              <ShieldCheck className="w-7 h-7 text-background" />
            </div>
            <h2 className="text-3xl font-bold text-white">DocAiApp</h2>
          </div>

          <div className="glass rounded-3xl p-8 sm:p-10 shadow-2xl relative overflow-hidden group">
            {/* Top accent line */}
            <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-accent/40 to-transparent" />

            <div className="mb-8">
              <h3 className="text-2xl font-bold text-white mb-2">Welcome back</h3>
              <p className="text-textSecondary text-sm">Enter your details to access your dashboard.</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <AnimatePresence mode="wait">
                {error && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="p-3 text-sm text-rose-400 bg-rose-400/10 border border-rose-400/20 rounded-xl flex items-center gap-2"
                  >
                    <div className="w-1 h-1 rounded-full bg-rose-400" />
                    {error}
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-textSecondary uppercase tracking-widest px-1">Email Address</label>
                <div className="relative group/input">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-textSecondary group-focus-within/input:text-accent transition-colors" />
                  <input
                    type="email"
                    placeholder="name@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={isLoading}
                    className="w-full h-14 bg-white/[0.03] border border-white/10 rounded-2xl pl-12 pr-4 text-white placeholder:text-textSecondary/30 focus:outline-none focus:border-accent/50 focus:ring-4 focus:ring-accent/10 transition-all"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between px-1">
                  <label className="text-xs font-semibold text-textSecondary uppercase tracking-widest">Password</label>
                  <Link to="/forgot-password" title="Forgot password" className="text-xs font-medium text-accent hover:text-accent/80 transition-colors">
                    Forgot password?
                  </Link>
                </div>
                <div className="relative group/input">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-textSecondary group-focus-within/input:text-accent transition-colors" />
                  <input
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={isLoading}
                    className="w-full h-14 bg-white/[0.03] border border-white/10 rounded-2xl pl-12 pr-4 text-white placeholder:text-textSecondary/30 focus:outline-none focus:border-accent/50 focus:ring-4 focus:ring-accent/10 transition-all"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 px-1 pt-1">
                <input
                  type="checkbox"
                  id="remember"
                  className="w-4 h-4 rounded border-white/10 bg-white/5 text-accent focus:ring-accent/20 focus:ring-offset-0"
                />
                <label htmlFor="remember" className="text-sm text-textSecondary cursor-pointer select-none">Remember me</label>
              </div>

              <motion.button
                whileHover={{ scale: 1.01, translateY: -2 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={isLoading}
                className="w-full h-14 mt-4 bg-gradient-amber text-background font-bold rounded-2xl flex items-center justify-center gap-2 shadow-amber-glow hover:shadow-amber-glow-strong transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    Sign In
                    <ChevronRight className="w-5 h-5" />
                  </>
                )}
              </motion.button>
            </form>

            <div className="mt-10 text-center">
              <p className="text-textSecondary text-sm">
                Don't have an account?{' '}
                <Link to="/register" className="text-white font-semibold hover:text-accent transition-colors">
                  Create account
                </Link>
              </p>
            </div>
          </div>

          <div className="mt-8 flex items-center justify-center gap-2 text-textSecondary/40 text-[10px] uppercase tracking-[0.2em] font-bold">
            <ShieldCheck className="w-3 h-3" />
            Secured with end-to-end encryption
          </div>
        </motion.div>
      </div>

      {/* Decorative gradients */}
      <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent/5 blur-[150px] rounded-full pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-accent/5 blur-[150px] rounded-full pointer-events-none" />
    </div>
  );
};

