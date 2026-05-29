import { useState, useEffect } from 'react';
import { X, Loader2, Calendar, Link2, Volume2 } from 'lucide-react';
import { createAgent, getUser, getCalAuthUrl, disconnectCalApi } from '../api/client';
import { useAgentStore } from '../store/agentStore';
import toast from 'react-hot-toast';
import VoiceSelectionModal from './VoiceSelectionModal';

interface Props {
  onClose: () => void;
}

const AVAILABLE_PHONE_NUMBERS = [
  { value: '+918035736739', label: '+91 80357 36739' }
];

const CreateAgentModal = ({ onClose }: Props) => {
  const [loading, setLoading] = useState(false);
  const { addAgent } = useAgentStore();
  const [formData, setFormData] = useState({
    agent_name: '',
    custom_first_line: '',
    prompt_text: '',
    stt_language: 'en',
    voice_id: 1,
    enable_calendar_booking: false,
    cal_api_key: '',
    cal_event_type_id: '',
    phone_number: '+918035736739',
  });
  const [errors, setErrors] = useState<Record<string, boolean>>({});
  const [calConnected, setCalConnected] = useState(false);
  const [checkingCal, setCheckingCal] = useState(true);
  const [showVoiceModal, setShowVoiceModal] = useState(false);

  useEffect(() => {
    checkCalConnection();

    const handleOAuthMessage = (event: MessageEvent) => {
      if (event.data?.type === 'CAL_AUTH_SUCCESS') {
        setCalConnected(true);
        toast.success('Cal.com connected successfully!');
      }
    };
    window.addEventListener('message', handleOAuthMessage);
    return () => window.removeEventListener('message', handleOAuthMessage);
  }, []);

  const checkCalConnection = async () => {
    try {
      const user = await getUser();
      setCalConnected(!!user.cal_connected);
    } catch (e) {
      console.error('Failed to check calendar connection:', e);
    } finally {
      setCheckingCal(false);
    }
  };

  const handleConnectCal = async () => {
    try {
      const res = await getCalAuthUrl();
      if (res.url) {
        const width = 600, height = 700;
        const left = window.screen.width / 2 - width / 2;
        const top = window.screen.height / 2 - height / 2;
        window.open(res.url, 'cal_auth', `width=${width},height=${height},left=${left},top=${top}`);
      }
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to initialize Cal.com connection');
    }
  };

  const handleDisconnectCal = async () => {
    if (!confirm('Are you sure you want to disconnect your Cal.com account? This will disable booking on new and existing agents.')) return;
    try {
      await disconnectCalApi();
      setCalConnected(false);
      toast.success('Cal.com disconnected');
    } catch (e) {
      toast.error('Failed to disconnect Cal.com');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, boolean> = {};
    if (!formData.agent_name.trim()) newErrors.agent_name = true;
    if (!formData.custom_first_line.trim()) newErrors.custom_first_line = true;
    if (!formData.prompt_text.trim()) newErrors.prompt_text = true;

    // cal_api_key and cal_event_type_id are now strictly optional so no validation needed here

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    try {
      const res = await createAgent(formData);
      addAgent(res.agent);
      toast.success('Agent created successfully!');
      onClose();
    } catch (error: any) {
      const errDetail = error.response?.data?.detail || 'Failed to create agent';
      toast.error(errDetail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity" />
      <div
        className="relative bg-surface rounded-[16px] w-full max-w-[700px] shadow-2xl flex flex-col animate-in zoom-in-95 duration-200 border border-border/50"
        onClick={e => e.stopPropagation()}
      >
        <div className="px-6 py-5 border-b border-border flex items-center justify-between">
          <h2 className="text-[18px] font-bold text-surface-foreground">Create an Agent</h2>
          <button onClick={onClose} className="p-1 rounded-md text-textMuted hover:bg-muted transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-4 overflow-y-auto max-h-[85vh]">
          <div className="flex flex-col gap-1.5">
            <label className="text-[13px] font-semibold text-surface-foreground">Agent Name</label>
            <input
              type="text"
              value={formData.agent_name}
              onChange={e => setFormData({ ...formData, agent_name: e.target.value })}
              className={`border rounded-[8px] px-3 py-2 text-[14px] bg-muted/30 text-surface-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all ${errors.agent_name ? 'border-error' : 'border-border'}`}
              placeholder="e.g. Sales Representative"
            />
            {errors.agent_name && <span className="text-[12px] text-error">Required field</span>}
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[13px] font-semibold text-surface-foreground">Greeting / First Line</label>
            <input
              type="text"
              value={formData.custom_first_line}
              onChange={e => setFormData({ ...formData, custom_first_line: e.target.value })}
              className={`border rounded-[8px] px-3 py-2 text-[14px] bg-muted/30 text-surface-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all ${errors.custom_first_line ? 'border-error' : 'border-border'}`}
              placeholder="e.g. Hello, how can I help you today?"
            />
            {errors.custom_first_line && <span className="text-[12px] text-error">Required field</span>}
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[13px] font-semibold text-surface-foreground">Agent Prompt</label>
            <textarea
              value={formData.prompt_text}
              onChange={e => setFormData({ ...formData, prompt_text: e.target.value })}
              rows={12}
              className={`border rounded-[8px] px-3 py-2 text-[14px] bg-muted/30 text-surface-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all resize-none ${errors.prompt_text ? 'border-error' : 'border-border'}`}
              placeholder="Describe the agent's persona, goals, and behavior..."
            />
            {errors.prompt_text && <span className="text-[12px] text-error">Required field</span>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[13px] font-semibold text-surface-foreground">Language</label>
              <select
                value={formData.stt_language}
                onChange={e => setFormData({ ...formData, stt_language: e.target.value })}
                className="border border-border rounded-[8px] px-3 py-2 text-[14px] bg-muted/30 text-surface-foreground outline-none focus:border-primary"
              >
                <option value="en">English (en)</option>
                <option value="hi">Hindi (hi)</option>
                <option value="es">Spanish (es)</option>
                <option value="fr">French (fr)</option>
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[13px] font-semibold text-surface-foreground">Voice Options</label>
              <button
                type="button"
                onClick={() => setShowVoiceModal(true)}
                className="w-full flex items-center justify-between border border-border rounded-[8px] px-3 py-2.5 text-[14px] bg-muted/30 text-surface-foreground hover:border-primary transition-all outline-none text-left cursor-pointer"
              >
                <div className="flex items-center gap-2">
                  <Volume2 className="w-4 h-4 text-primary" />
                  <div>
                    <span className="font-bold text-[13px]">
                      {formData.voice_id === 1 ? 'Riya Mehta' : formData.voice_id === 2 ? 'Akash' : 'Asha'}
                    </span>
                    <span className="text-[11px] text-textMuted ml-2">
                      ({formData.voice_id === 1 ? 'Female' : formData.voice_id === 2 ? 'Male' : 'Neutral'} • Indian Accent)
                    </span>
                  </div>
                </div>
                <span className="text-[11px] font-bold text-primary bg-primary/10 py-0.5 px-2.5 rounded-full hover:bg-primary/20 transition-all">Change</span>
              </button>
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[13px] font-semibold text-surface-foreground">select phone</label>
            <select
              value={formData.phone_number}
              onChange={e => setFormData({ ...formData, phone_number: e.target.value })}
              className="border border-border rounded-[8px] px-3 py-2 text-[14px] bg-muted/30 text-surface-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
            >
              {AVAILABLE_PHONE_NUMBERS.map(num => (
                <option key={num.value} value={num.value}>{num.label}</option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-4 py-3 border-t border-border mt-2">
            <div className="flex items-center justify-between text-[14px]">
              <div className="flex flex-col">
                <span className="font-semibold text-surface-foreground">Meeting Booking</span>
                <span className="text-[12px] text-textMuted">Allow agent to access Cal.com slots</span>
              </div>
              <button
                type="button"
                role="switch"
                onClick={() => setFormData({ ...formData, enable_calendar_booking: !formData.enable_calendar_booking })}
                className={`relative inline-flex h-[24px] w-[44px] shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${formData.enable_calendar_booking ? 'bg-primary' : 'bg-border'}`}
              >
                <span className={`pointer-events-none inline-block h-[20px] w-[20px] transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${formData.enable_calendar_booking ? 'translate-x-[20px]' : 'translate-x-0'}`} />
              </button>
            </div>

            {formData.enable_calendar_booking && (
              <div className="animate-in slide-in-from-top-2 duration-200 flex flex-col gap-4">
                {checkingCal ? (
                  <div className="flex items-center justify-center gap-2 py-4 text-textMuted bg-muted/20 border border-border rounded-xl">
                    <Loader2 className="w-4 h-4 animate-spin text-primary" />
                    <span className="text-[13px] font-medium">Checking Cal.com integration...</span>
                  </div>
                ) : !calConnected ? (
                  <div className="bg-muted/10 border border-border rounded-[12px] p-5 flex flex-col gap-4">
                    <p className="text-[13px] text-textMuted leading-relaxed">
                      Connect your personal Cal.com account to allow this agent to fetch real-time slots and book appointments during outbound calls.
                    </p>
                    <button
                      type="button"
                      onClick={handleConnectCal}
                      className="w-full py-3 bg-primary hover:bg-primary-hover text-primary-foreground font-bold rounded-xl flex items-center justify-center gap-2.5 shadow-lg shadow-primary/10 transition-all hover:scale-[1.01] active:scale-[0.99] text-[14px]"
                    >
                      <Calendar className="w-4.5 h-4.5" />
                      Connect Cal.com Account
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col gap-4">
                    <div className="bg-success/5 border border-success/20 rounded-[12px] p-4 flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className="w-2.5 h-2.5 rounded-full bg-success animate-pulse" />
                        <span className="text-[13px] font-bold text-success">Cal.com Account Connected</span>
                      </div>
                      <button
                        type="button"
                        onClick={handleDisconnectCal}
                        className="text-[12px] font-bold text-error hover:underline px-2.5 py-1.5 hover:bg-error/5 rounded-md transition-all"
                      >
                        Disconnect Account
                      </button>
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-[12px] font-bold text-surface-foreground uppercase tracking-tight flex items-center gap-1.5">
                        <Link2 className="w-3.5 h-3.5 text-primary" />
                        Cal.com Event Type ID (Optional)
                      </label>
                      <input
                        type="text"
                        value={formData.cal_event_type_id}
                        onChange={e => setFormData({ ...formData, cal_event_type_id: e.target.value })}
                        className={`border rounded-[8px] px-3 py-2 text-[13px] bg-muted/20 text-surface-foreground outline-none focus:border-primary transition-all border-border`}
                        placeholder="Leave blank to dynamically auto-resolve first active event type"
                      />
                      <span className="text-[11px] text-textMuted">Specify a specific Event Type ID if you want to route this agent's calls to a distinct calendar event.</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="pt-2 flex justify-end gap-3 border-t border-border mt-4">
            <button type="button" onClick={onClose} className="btn-outline">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary min-w-[120px] flex justify-center items-center gap-2">
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {loading ? 'Creating...' : 'Create Agent'}
            </button>
          </div>
        </form>
      </div>
      {showVoiceModal && (
        <VoiceSelectionModal
          selectedVoiceId={formData.voice_id}
          onSelect={(voiceId) => {
            setFormData({ ...formData, voice_id: voiceId });
            setShowVoiceModal(false);
          }}
          onClose={() => setShowVoiceModal(false)}
        />
      )}
    </div>
  );
};

export default CreateAgentModal;
