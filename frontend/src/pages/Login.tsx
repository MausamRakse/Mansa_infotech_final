import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { PhoneCall, Mail, Lock, Loader2, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';

const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    // TEMPORARY BYPASS: Instant redirect to bypass Supabase rate limits
    setTimeout(() => {
      setLoading(false);
      toast.success('🎉 Dashboard Access Granted (Dev Bypass Active)', { icon: '🚀' });
      navigate('/dashboard');
    }, 800);
  };

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-6 bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] from-[#0d9488]/5 via-bg to-bg">
      <div className="w-full max-w-[440px]">
        {/* Logo Section */}
        <Link to="/" className="flex flex-col items-center gap-4 mb-10 group">
          <div className="w-14 h-14 rounded-2xl bg-[#0d9488] flex items-center justify-center shadow-2xl shadow-[#0d9488]/30 group-hover:scale-105 transition-transform duration-300">
            <PhoneCall className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-[28px] font-black tracking-tight text-text-primary">
            convexa<span className="text-[#0d9488] italic">.ai</span>
          </h1>
        </Link>

        {/* Card Section */}
        <div className="bg-white rounded-[32px] p-10 border border-border/60 shadow-2xl shadow-black/5 animate-in slide-in-from-top-4 duration-500">
          <div className="mb-10 text-center">
            <h2 className="text-[24px] font-bold text-text-primary mb-2">
              {isLogin ? 'Welcome Back' : 'Create Account'}
            </h2>
            <p className="text-text-muted text-[14px]">
              {isLogin ? 'Access your AI agent dashboard' : 'Start deploying intelligent voice agents'}
            </p>
          </div>

          <form onSubmit={handleAuth} className="flex flex-col gap-5">
            <div className="flex flex-col gap-1.5">
              <label className="text-[13px] font-bold text-text-primary px-1">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-text-muted" />
                <input 
                  type="email" 
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="w-full pl-11 pr-4 py-3.5 rounded-xl border border-border bg-surface outline-none focus:border-[#0d9488] focus:ring-4 focus:ring-[#0d9488]/10 transition-all text-[15px]"
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-[13px] font-bold text-text-primary px-1">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-text-muted" />
                <input 
                  type="password" 
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-11 pr-4 py-3.5 rounded-xl border border-border bg-surface outline-none focus:border-[#0d9488] focus:ring-4 focus:ring-[#0d9488]/10 transition-all text-[15px]"
                />
              </div>
            </div>

            <button 
              type="submit" 
              disabled={loading}
              className="mt-4 bg-[#0d9488] text-white py-4 rounded-2xl text-[16px] font-bold hover:bg-[#0f766e] transition-all shadow-xl shadow-[#0d9488]/20 flex items-center justify-center gap-2 group disabled:opacity-70"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  {isLogin ? 'Sign In' : 'Create Account'}
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          <div className="mt-10 flex flex-col gap-5 items-center">
            <button 
              onClick={() => setIsLogin(!isLogin)}
              className="text-[14px] font-bold text-text-muted hover:text-[#0d9488] transition-colors underline-offset-4 hover:underline"
            >
              {isLogin ? "Don't have an account? Sign Up" : "Already have an account? Sign In"}
            </button>
          </div>
        </div>

        <div className="mt-10 text-center">
          <p className="text-[13px] text-text-muted leading-relaxed">
            By continuing, you agree to convexa.ai&apos;s<br/>
            <a href="#" className="underline font-bold hover:text-text-primary transition-colors">Terms of Service</a> and <a href="#" className="underline font-bold hover:text-text-primary transition-colors">Privacy Policy</a>.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
