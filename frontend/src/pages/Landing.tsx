import { Link } from 'react-router-dom';
import { 
  PhoneCall, 
  FileText, 
  Activity, 
  Layers, 
  ArrowRight, 
  Zap,
  Terminal
} from 'lucide-react';

const Landing = () => {
  return (
    <div className="min-h-screen bg-white text-textPrimary selection:bg-primary/20">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-[8px] bg-primary flex items-center justify-center">
              <PhoneCall className="w-5 h-5 text-white" />
            </div>
            <span className="text-[20px] font-bold tracking-tight">convexa.ai</span>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/login" className="text-[14px] font-medium text-textMuted hover:text-textPrimary transition-colors">
              Sign In
            </Link>
            <Link 
              to="/login" 
              className="bg-primary text-white px-5 py-2 rounded-[8px] text-[14px] font-semibold hover:bg-primary/95 transition-all shadow-lg shadow-primary/25"
            >
              Open Console
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto flex flex-col items-center text-center">
          <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-3 py-1 rounded-full text-[13px] font-bold mb-8 animate-in fade-in slide-in-from-bottom-3 duration-700">
            <Zap className="w-4 h-4 fill-current" />
            <span>Now Live: Outbound Agent V1</span>
          </div>
          <h1 className="text-[64px] md:text-[84px] font-black tracking-tight leading-[1.05] mb-6 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
            Intelligent Outbound<br/>
            <span className="text-primary italic">AI Calling Agent.</span>
          </h1>
          <p className="max-w-[700px] text-[18px] text-textMuted leading-relaxed mb-10 animate-in fade-in slide-in-from-bottom-5 duration-700 delay-200">
            Deploy autonomous voice agents that can handle lead qualification, appointment booking, and customer support with human-like fluency. Complete dashboard for scale.
          </p>
          <div className="flex flex-col sm:flex-row items-center gap-4 animate-in fade-in slide-in-from-bottom-6 duration-700 delay-300">
            <Link 
              to="/login" 
              className="bg-primary text-white px-8 py-4 rounded-[12px] text-[16px] font-bold hover:bg-primary/95 transition-all shadow-xl shadow-primary/30 flex items-center gap-2 group"
            >
              Launch Console
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <button className="bg-surface text-textPrimary border border-border px-8 py-4 rounded-[12px] text-[16px] font-bold hover:bg-border/30 transition-all flex items-center gap-2">
              <Terminal className="w-5 h-5" />
              View Documentation
            </button>
          </div>
        </div>
      </section>

      {/* Services/Features */}
      <section className="py-24 bg-surface/30">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-[36px] font-bold mb-4">Our Services</h2>
            <p className="text-textMuted text-[16px]">Everything you need to automate your outbound operations</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-white p-8 rounded-[24px] border border-border hover:shadow-xl hover:translate-y-[-4px] transition-all duration-300">
              <div className="w-12 h-12 rounded-[14px] bg-primary/10 flex items-center justify-center mb-6">
                <Layers className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-[20px] font-bold mb-3">Bulk & Single Calling</h3>
              <p className="text-textMuted text-[15px] leading-relaxed">
                Upload Excel sheets for high-volume campaigns or dial single numbers instantly for testing with our flexible API.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-white p-8 rounded-[24px] border border-border hover:shadow-xl hover:translate-y-[-4px] transition-all duration-300">
              <div className="w-12 h-12 rounded-[14px] bg-secondary/10 flex items-center justify-center mb-6">
                <FileText className="w-6 h-6 text-secondary" />
              </div>
              <h3 className="text-[20px] font-bold mb-3">Smart Transcripts</h3>
              <p className="text-textMuted text-[15px] leading-relaxed">
                Automatically generated transcripts stored in JSON format for easy analysis and seamless CRM integration.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-white p-8 rounded-[24px] border border-border hover:shadow-xl hover:translate-y-[-4px] transition-all duration-300">
              <div className="w-12 h-12 rounded-[14px] bg-green-500/10 flex items-center justify-center mb-6">
                <Activity className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="text-[20px] font-bold mb-3">Real-time Monitoring</h3>
              <p className="text-textMuted text-[15px] leading-relaxed">
                Watch live agent status, call duration, and connection health from a central dashboard in real-time.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-border mt-20">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-[6px] bg-primary flex items-center justify-center">
              <PhoneCall className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-bold">convexa.ai</span>
          </div>
          <div className="flex gap-8 text-[14px] font-medium text-textMuted">
            <a href="#" className="hover:text-textPrimary transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-textPrimary transition-colors">Terms of Service</a>
            <a href="#" className="hover:text-textPrimary transition-colors">Contact Support</a>
          </div>
          <div className="text-textMuted text-[14px]">
            &copy; 2026 convexa.ai. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
