import { useState, useEffect } from 'react';
import { fetchCallLogs, type CallLog } from '../api/client';
import TranscriptModal from '../components/TranscriptModal';
import { Download, PlayCircle, PhoneOff, Loader2 } from 'lucide-react';

const CallLogs = () => {
  const [logs, setLogs] = useState<CallLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLog, setSelectedLog] = useState<CallLog | null>(null);
  const [downloadingRecording, setDownloadingRecording] = useState<string | null>(null);

  const formatDate = (dateStr: any) => {
    const str = String(dateStr || "");
    if (!str || str === "unknown") return "N/A";
    const safeDate = str.replace(' ', 'T') + 'Z'; // Force UTC 
    const d = new Date(safeDate);
    return isNaN(d.getTime())
      ? str
      : d.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });
  };

  // Naming & Sanitization Helpers
  const transliterateHindi = (text: string): string => {
    const map: { [key: string]: string } = {
      'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo', 'ऋ': 'ri', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
      'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'n',
      'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'n',
      'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
      'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
      'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
      'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
      'ा': 'a', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo', 'ृ': 'ri', 'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
      'ं': 'n', 'ः': 'h', 'ँ': 'n', '़': '', '्': ''
    };

    let result = '';
    for (let i = 0; i < text.length; i++) {
      const char = text[i];
      const nextChar = text[i + 1];

      if (map[char] !== undefined) {
        result += map[char];
        
        // If this is a consonant and not followed by a matra, halant, or EOF, add inherent 'a' sound
        const isConsonant = 'कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह'.includes(char);
        const nextIsMatraOrHalant = nextChar && 'ािीुूृेैोौ्ंःँ़'.includes(nextChar);
        
        if (isConsonant && !nextIsMatraOrHalant && nextChar !== ' ') {
          result += 'a';
        }
      } else {
        result += char;
      }
    }
    return result;
  };

  const sanitizeFileNameComponent = (text: any, fallback: string): string => {
    if (!text) return fallback;
    const str = transliterateHindi(String(text));
    let sanitized = str
      .trim()
      .replace(/[\/\\:*?"<>|]/g, '') // remove invalid characters
      .replace(/\s+/g, '_')          // replace spaces with underscores
      .replace(/_+/g, '_');          // prevent double underscores
    
    sanitized = sanitized.replace(/^_+|_+$/g, ''); // trim leading/trailing underscores
    return sanitized || fallback;
  };

  const sanitizePhone = (phone: any): string => {
    if (!phone) return "NoPhone";
    const cleaned = String(phone).replace(/\D/g, ''); // strip non-digits (e.g. +1 (987) 654-3210 -> 19876543210)
    return cleaned || "NoPhone";
  };

  const getCallDate = (dateStr: any): string => {
    const str = String(dateStr || "");
    if (!str || str === "unknown") {
      return new Date().toISOString().split('T')[0];
    }
    try {
      const match = str.match(/^\d{4}-\d{2}-\d{2}/);
      if (match) return match[0];
      const d = new Date(str);
      if (!isNaN(d.getTime())) {
        return d.toISOString().split('T')[0];
      }
    } catch (e) {}
    return new Date().toISOString().split('T')[0];
  };

  const getCustomerName = (log: CallLog): string => {
    if (log.customer_name) return log.customer_name;
    if (log.json_output) {
      try {
        const data = typeof log.json_output === 'string' ? JSON.parse(log.json_output) : log.json_output;
        if (data && typeof data === 'object') {
          const found = data.name || data.customer_name || data.user_name;
          if (found) return found;
        }
      } catch (e) {}
    }
    return "UnknownCustomer";
  };

  const generateCallFileName = (log: CallLog, extension: string): string => {
    const customerName = sanitizeFileNameComponent(getCustomerName(log), "UnknownCustomer");
    const phone = sanitizePhone(log.phone_number);
    const agentName = sanitizeFileNameComponent(log.agent_name, "UnknownAgent");
    const callDate = getCallDate(log.date);
    
    const filename = `${customerName}_${phone}_${agentName}_${callDate}.${extension}`;
    
    if (filename.length > 200) {
      const truncatedCustomer = customerName.substring(0, 30);
      const truncatedAgent = agentName.substring(0, 30);
      return `${truncatedCustomer}_${phone}_${truncatedAgent}_${callDate}.${extension}`;
    }
    return filename;
  };

  // Recording Dynamic Download handler
  const downloadRecording = async (log: CallLog) => {
    if (!log.recording_url) return;
    const filename = generateCallFileName(log, "mp3");
    
    setDownloadingRecording(log.call_id);
    try {
      const devUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
      const apiOrigin = (typeof window !== 'undefined' && window.location.hostname !== 'localhost')
        ? "/api"
        : `${devUrl}/api`;
      const proxyUrl = `${apiOrigin}/logs/download-recording?url=${encodeURIComponent(log.recording_url)}`;

      const response = await fetch(proxyUrl);
      if (!response.ok) throw new Error("Network response was not ok");
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error("Failed proxy download, falling back to direct tab link", error);
      // Fallback: direct link open in a new tab if CORS or other issues occur
      const link = document.createElement("a");
      link.href = log.recording_url;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.click();
    } finally {
      setDownloadingRecording(null);
    }
  };

  useEffect(() => {
    let isMounted = true;

    const loadData = () => {
      fetchCallLogs(50).then(data => {
        if (isMounted) {
          setLogs(data);
          setLoading(false);
        }
      }).catch(err => {
        console.error(err);
        if (isMounted) setLoading(false);
      });
    };

    loadData();
    const interval = setInterval(loadData, 5000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="max-w-6xl mx-auto h-full flex flex-col animate-in fade-in duration-500">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-surface-foreground tracking-tight">Call Logs</h1>
        <p className="text-textMuted mt-1">Review activity, playback recordings, and read transcripts from your agents.</p>
      </div>

      <div className="flex-1 bg-surface rounded-[12px] border border-border card-shadow flex flex-col min-h-0 overflow-hidden">
        {loading ? (
          <div className="p-12 flex flex-col items-center justify-center text-textMuted h-full">
            <Loader2 className="w-8 h-8 animate-spin text-primary mb-4" />
            <p className="font-medium">Loading call logs...</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="p-16 flex flex-col items-center justify-center text-textMuted h-full">
            <div className="w-16 h-16 bg-surface rounded-full flex items-center justify-center mb-4">
              <PhoneOff className="w-8 h-8 opacity-50" />
            </div>
            <p className="text-surface-foreground font-bold text-[18px]">No call history yet</p>
            <p className="text-[14px] mt-1 max-w-sm text-center">Trigger your first call from the Agents page to see it appear here.</p>
          </div>
        ) : (
          <div className="flex-1 overflow-auto">
            <table className="w-full text-left text-[14px]">
              <thead className="bg-surface sticky top-0 border-b border-border shadow-sm z-10 text-textMuted">
                <tr>
                  <th className="px-6 py-4 font-semibold text-[12px] uppercase tracking-wider">Agent</th>
                  <th className="px-6 py-4 font-semibold text-[12px] uppercase tracking-wider">Phone Number</th>
                  <th className="px-6 py-4 font-semibold text-[12px] uppercase tracking-wider">Date & Time</th>
                  <th className="px-6 py-4 font-semibold text-[12px] uppercase tracking-wider">Status</th>
                  <th className="px-6 py-4 font-semibold text-[12px] uppercase tracking-wider">Transcript</th>
                  <th className="px-6 py-4 font-semibold text-[12px] uppercase tracking-wider">Recording</th>
                  <th className="px-6 py-4 font-semibold text-[12px] uppercase tracking-wider text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {logs.map((log, i) => (
                  <tr key={i} className="hover:bg-surface/50 transition-colors group">
                    <td className="px-6 py-4 text-[13px] font-medium text-surface-foreground">{log.agent_name || "Unknown Agent"}</td>
                    <td className="px-6 py-4 font-mono text-[13px]">{log.phone_number}</td>
                    <td className="px-6 py-4 text-textMuted whitespace-nowrap">{formatDate(log.date)}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-[12px] font-bold tracking-wide ${
                        log.status === 'Completed' ? 'bg-success/10 text-success' : 
                        log.status === 'Not Answered' ? 'bg-error/10 text-error' : 
                        'bg-warning/10 text-warning animate-pulse'
                      }`}>
                        {log.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => setSelectedLog(log)}
                        disabled={!log.transcript}
                        className="text-primary hover:text-primary-hover font-medium disabled:text-textMuted/40 transition-colors disabled:cursor-not-allowed text-[13px]"
                      >
                        View Text
                      </button>
                    </td>
                    <td className="px-6 py-4">
                      {log.recording_url ? (
                        <div className="flex items-center gap-3">
                          <a href={log.recording_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 text-surface-foreground hover:text-primary transition-colors text-[13px] font-medium" title="Play Recording">
                            <PlayCircle className="w-4 h-4 text-primary" /> Play
                          </a>
                          <button
                            onClick={() => downloadRecording(log)}
                            disabled={downloadingRecording === log.call_id}
                            className="inline-flex items-center gap-1 text-textMuted hover:text-primary transition-colors text-[13px] font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Download Recording"
                          >
                            {downloadingRecording === log.call_id ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
                            ) : (
                              <Download className="w-3.5 h-3.5 text-textMuted hover:text-primary" />
                            )}
                            Download
                          </button>
                        </div>
                      ) : (
                        <span className="text-textMuted/40 text-[13px]">Processing...</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {log.json_output && (
                        <a
                          href={`data:application/json;charset=utf-8,${encodeURIComponent(log.json_output)}`}
                          download={generateCallFileName(log, "json")}
                          className="inline-flex items-center justify-center p-1.5 rounded-md text-textMuted hover:bg-muted hover:text-primary shadow-sm opacity-0 group-hover:opacity-100 transition-all border border-transparent hover:border-border"
                          title="Download Data"
                        >
                          <Download className="w-4 h-4" />
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedLog !== null && (
        <TranscriptModal
          log={selectedLog}
          onClose={() => setSelectedLog(null)}
          generateCallFileName={generateCallFileName}
        />
      )}
    </div>
  );
};

export default CallLogs;
