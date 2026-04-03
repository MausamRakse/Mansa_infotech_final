import { X, Copy, CheckCircle2 } from 'lucide-react';
import { useState } from 'react';

interface Props {
  transcript: string;
  onClose: () => void;
}

const TranscriptModal = ({ transcript, onClose }: Props) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(transcript);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm transition-opacity animate-in fade-in" onClick={onClose}>
      <div 
        className="relative bg-white rounded-[16px] w-full max-w-[600px] max-h-[80vh] shadow-xl flex flex-col animate-in zoom-in-95 duration-200"
        onClick={e => e.stopPropagation()}
      >
        <div className="px-6 py-5 border-b border-border flex items-center justify-between bg-surface rounded-t-[16px]">
          <h2 className="text-[18px] font-bold text-textPrimary">Call Transcript</h2>
          <div className="flex items-center gap-2">
            <button 
              onClick={handleCopy} 
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[13px] font-medium text-textMuted hover:bg-white hover:text-primary hover:shadow-sm border border-transparent hover:border-border transition-all"
            >
              {copied ? <CheckCircle2 className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
            <button onClick={onClose} className="p-1.5 rounded-md text-textMuted hover:bg-white hover:shadow-sm border border-transparent hover:border-border transition-all">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="p-6 overflow-y-auto flex-1 font-mono text-[13px] leading-relaxed text-textPrimary bg-slate-50/50">
          {transcript.split('\n').map((line, i) => (
            <p key={i} className="mb-2 whitespace-pre-wrap">{line}</p>
          ))}
          {!transcript && <p className="italic text-textMuted">No transcript available.</p>}
        </div>
      </div>
    </div>
  );
};

export default TranscriptModal;
