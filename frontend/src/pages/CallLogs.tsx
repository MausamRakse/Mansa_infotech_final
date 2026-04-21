import { useState, useEffect } from 'react';
import { fetchCallLogs, type CallLog } from '../api/client';
import TranscriptModal from '../components/TranscriptModal';
import { Download, PlayCircle, PhoneOff, Loader2 } from 'lucide-react';

const CallLogs = () => {
  const [logs, setLogs] = useState<CallLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTranscript, setSelectedTranscript] = useState<string | null>(null);

  const formatDate = (dateStr: string) => {
    if (!dateStr || dateStr === "unknown") return "N/A";
    const safeDate = dateStr.replace(' ', 'T') + 'Z'; // Force UTC 
    const d = new Date(safeDate);
    return isNaN(d.getTime())
      ? dateStr
      : d.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });
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
                        onClick={() => setSelectedTranscript(log.transcript || '')}
                        disabled={!log.transcript}
                        className="text-primary hover:text-primary-hover font-medium disabled:text-textMuted/40 transition-colors disabled:cursor-not-allowed text-[13px]"
                      >
                        View Text
                      </button>
                    </td>
                    <td className="px-6 py-4">
                      {log.recording_url ? (
                        <a href={log.recording_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 text-surface-foreground hover:text-primary transition-colors text-[13px] font-medium">
                          <PlayCircle className="w-4 h-4 text-primary" /> Play
                        </a>
                      ) : (
                        <span className="text-textMuted/40 text-[13px]">Processing...</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {log.json_output && (
                        <a
                          href={`data:application/json;charset=utf-8,${encodeURIComponent(log.json_output)}`}
                          download={`call-${log.call_id}.json`}
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

      {selectedTranscript !== null && (
        <TranscriptModal
          transcript={selectedTranscript}
          onClose={() => setSelectedTranscript(null)}
        />
      )}
    </div>
  );
};

export default CallLogs;
