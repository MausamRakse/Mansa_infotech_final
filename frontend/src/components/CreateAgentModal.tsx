import { useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import { createAgent } from '../api/client';
import { useAgentStore } from '../store/agentStore';
import toast from 'react-hot-toast';

interface Props {
  onClose: () => void;
}

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
    cal_api_key: 'cal_live_69db2c652382b5e55d48ce9aa16c7a4c',
    cal_event_type_id: '4877569',
  });
  const [errors, setErrors] = useState<Record<string, boolean>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, boolean> = {};
    if (!formData.agent_name.trim()) newErrors.agent_name = true;
    if (!formData.custom_first_line.trim()) newErrors.custom_first_line = true;
    if (!formData.prompt_text.trim()) newErrors.prompt_text = true;

    if (formData.enable_calendar_booking) {
      if (!formData.cal_api_key.trim()) newErrors.cal_api_key = true;
      if (!formData.cal_event_type_id.trim()) newErrors.cal_event_type_id = true;
    }

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
    } catch (error) {
      toast.error('Failed to create agent');
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
              <select
                value={formData.voice_id}
                onChange={e => setFormData({ ...formData, voice_id: parseInt(e.target.value) })}
                className="border border-border rounded-[8px] px-3 py-2 text-[14px] bg-muted/30 text-surface-foreground outline-none focus:border-primary"
              >
                <option value={1}>Voice 1 (Female)</option>
                <option value={2}>Voice 2 (Male)</option>
                <option value={3}>Voice 3 (Neutral)</option>
              </select>
            </div>
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
              <div className="grid grid-cols-2 gap-4 animate-in slide-in-from-top-2 duration-200">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[12px] font-bold text-surface-foreground uppercase tracking-tight">Cal.com API Key</label>
                  <input
                    type="password"
                    value={formData.cal_api_key}
                    onChange={e => setFormData({ ...formData, cal_api_key: e.target.value })}
                    className={`border rounded-[8px] px-3 py-2 text-[13px] bg-muted/20 text-surface-foreground outline-none focus:border-primary transition-all ${errors.cal_api_key ? 'border-error' : 'border-border'}`}
                    placeholder="cal_live_..."
                  />
                  {errors.cal_api_key && <span className="text-[11px] text-error">Required</span>}
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[12px] font-bold text-surface-foreground uppercase tracking-tight">Event Type ID</label>
                  <input
                    type="text"
                    value={formData.cal_event_type_id}
                    onChange={e => setFormData({ ...formData, cal_event_type_id: e.target.value })}
                    className={`border rounded-[8px] px-3 py-2 text-[13px] bg-muted/20 text-surface-foreground outline-none focus:border-primary transition-all ${errors.cal_event_type_id ? 'border-error' : 'border-border'}`}
                    placeholder="e.g. 1599599"
                  />
                  {errors.cal_event_type_id && <span className="text-[11px] text-error">Required</span>}
                </div>
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
    </div>
  );
};

export default CreateAgentModal;
