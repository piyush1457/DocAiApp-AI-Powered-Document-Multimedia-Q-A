import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Mail, 
  Lock, 
  ShieldCheck, 
  ChevronRight,
  Loader2,
  FileText,
  AudioLines,
  Video,
  Clock
} from 'lucide-react';
import { api } from '../api/axios';
import { useAuthStore } from '../store/useAuthStore';

// --- Visual Components (Reused from Login for consistency) ---

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
      </div>
    </div>
  </FloatingCard>
);

// --- Main Page Component ---

export const Register = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const setTokens = useAuthStore((state) => state.setTokens);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setIsLoading(true);
    try {
      const response = await api.post('/auth/register', {
        email,
        password
      });
      
      const { access_token, refresh_token } = response.data;
      setTokens(access_token, refresh_token);
      navigate('/');
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        if (Array.isArray(detail)) {
          setError(detail[0]?.msg || 'Validation failed');
        } else {
          setError(detail || 'Failed to create account');
        }
      } else {
        setError('Something went wrong. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen w-full bg-background overflow-hidden">
      {/* Left Section (60%) */}
      <div className="hidden lg:flex w-[60%] relative flex-col justify-center px-20 border-r border-white/5">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-accent/5 blur-[120px] rounded-full pointer-events-none" />
        
        <div className="relative z-10">
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-7xl font-extrabold tracking-tight text-white mb-6 leading-[1.1]"
          >
            Start Your <br />
            <span className="text-accent">AI Journey.</span>
          </motion.h1>
          
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
            className="text-xl text-textSecondary max-w-lg leading-relaxed"
          >
            Join thousands of researchers and professionals using DocAiApp to unlock insights from their data.
          </motion.p>
          
          {/* Floating Elements Container */}
          <div className="absolute inset-0 pointer-events-none overflow-visible">
            <DocumentPreview />
          </div>
        </div>

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
            <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-accent/40 to-transparent" />
            
            <div className="mb-8">
              <h3 className="text-2xl font-bold text-white mb-2">Create an account</h3>
              <p className="text-textSecondary text-sm">Join us to start analyzing your multimedia files.</p>
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
                <label className="text-xs font-semibold text-textSecondary uppercase tracking-widest px-1">Password</label>
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
                <p className="text-[10px] text-textSecondary/50 px-1 uppercase tracking-wider">Min. 8 characters</p>
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
                    Create Account
                    <ChevronRight className="w-5 h-5" />
                  </>
                )}
              </motion.button>
            </form>

            <div className="mt-10 text-center">
              <p className="text-textSecondary text-sm">
                Already have an account?{' '}
                <Link to="/login" className="text-white font-semibold hover:text-accent transition-colors">
                  Log in
                </Link>
              </p>
            </div>
          </div>
        </motion.div>
      </div>

      <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent/5 blur-[150px] rounded-full pointer-events-none" />
    </div>
  );
};

