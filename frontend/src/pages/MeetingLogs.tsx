import { useState, useEffect } from 'react';
import { getMeetingLogs, type MeetingLog } from '../api/client';
import { CalendarCheck, CalendarRange, Clock, RefreshCcw } from 'lucide-react';
import toast from 'react-hot-toast';

const MeetingLogs = () => {
  const [logs, setLogs] = useState<MeetingLog[]>([]);
  const [loading, setLoading] = useState(true);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await getMeetingLogs();
      setLogs(data);
    } catch (err: any) {
      toast.error('Failed to load meeting logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-8 h-full animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black text-surface-foreground tracking-tight flex items-center gap-3">
            Meeting Logs <CalendarCheck className="w-7 h-7 text-primary" />
          </h1>
          <p className="text-textMuted mt-1 text-[14px]">Detailed records of AI meeting booking attempts and outcomes.</p>
        </div>
        <button 
          onClick={loadLogs}
          disabled={loading}
          className="btn-outline px-4 py-2 text-[13px] flex items-center gap-2 group"
        >
          <RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-500'}`} />
          {loading ? 'Refreshing...' : 'Refresh Logs'}
        </button>
      </div>

      <div className="bg-surface rounded-[24px] border border-border/60 shadow-xl shadow-black/5 flex flex-col flex-1 overflow-hidden">
        <div className="p-6 border-b border-border/40 bg-muted/5 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-success animate-pulse"></span>
            <span className="text-[13px] font-bold text-surface-foreground uppercase tracking-wider">Live System Sync</span>
          </div>
          <div className="flex items-center gap-4 ml-auto">
            <div className="flex items-center gap-1.5 text-[12px] font-bold text-textMuted">
               <CalendarRange className="w-4 h-4" /> 
               Total Records: <span className="text-primary">{logs.length}</span>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-auto p-2">
          {loading ? (
            <div className="h-full flex flex-col items-center justify-center p-12 gap-4">
              <div className="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
              <p className="font-bold text-sm tracking-widest uppercase text-textMuted">Fetching Details...</p>
            </div>
          ) : logs.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center p-16 text-center gap-4">
              <div className="w-20 h-20 bg-muted/30 rounded-full flex items-center justify-center text-textMuted animate-bounce duration-[2000ms]">
                <CalendarCheck className="w-10 h-10 opacity-20" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-surface-foreground">No Meeting Logs Found</h3>
                <p className="text-textMuted text-sm mt-2 max-w-sm">When an agent with Meeting Booking enabled completes a call, the booking status will appear here.</p>
              </div>
            </div>
          ) : (
            <table className="w-full text-left text-[14px]">
              <thead className="text-textMuted">
                <tr>
                  <th className="px-6 py-4 font-bold text-[11px] uppercase tracking-widest whitespace-nowrap">Timestamp (UTC)</th>
                  <th className="px-6 py-4 font-bold text-[11px] uppercase tracking-widest whitespace-nowrap">Agent</th>
                  <th className="px-6 py-4 font-bold text-[11px] uppercase tracking-widest whitespace-nowrap">Target Email</th>
                  <th className="px-6 py-4 font-bold text-[11px] uppercase tracking-widest whitespace-nowrap">Topic</th>
                  <th className="px-6 py-4 font-bold text-[11px] uppercase tracking-widest whitespace-nowrap text-center">Interest</th>
                  <th className="px-6 py-4 font-bold text-[11px] uppercase tracking-widest whitespace-nowrap text-center">Status</th>
                  <th className="px-6 py-4 font-bold text-[11px] uppercase tracking-widest">Reason / Error</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/30">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-primary/5 transition-colors group">
                    <td className="px-6 py-5 text-[12px] text-textMuted font-mono">
                      <div className="flex items-center gap-2">
                        <Clock className="w-3.5 h-3.5 opacity-50" />
                        {new Date(log.created_at).toLocaleString()}
                      </div>
                    </td>
                    <td className="px-6 py-5 font-bold text-surface-foreground whitespace-nowrap">
                      {log.agent_name || log.agent_id}
                    </td>
                    <td className="px-6 py-5 font-mono text-[13px] text-textMuted">
                      {log.extracted_email || '—'}
                    </td>
                    <td className="px-6 py-5 text-[13px] text-surface-foreground max-w-[200px] truncate" title={log.meeting_topic || ''}>
                      {log.meeting_topic || '—'}
                    </td>
                    <td className="px-6 py-5 text-center">
                      {log.is_interested ? (
                        <span className="inline-flex px-2 py-0.5 rounded-md text-[10px] font-black bg-success/10 text-success">YES</span>
                      ) : (
                        <span className="inline-flex px-2 py-0.5 rounded-md text-[10px] font-black bg-error/10 text-error">NO</span>
                      )}
                    </td>
                    <td className="px-6 py-5 text-center">
                      <span className={`inline-flex items-center justify-center px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider ${
                        log.status === 'booked' ? 'bg-success/10 text-success' : 
                        log.status === 'failed' ? 'bg-error/10 text-error' : 
                        'bg-warning/10 text-warning'
                      }`}>
                        {log.status === 'booked' ? 'Booked ✅' : log.status === 'failed' ? 'Failed ❌' : 'Skipped'}
                      </span>
                    </td>
                    <td className="px-6 py-5 text-[12px] text-textMuted max-w-[250px] truncate" title={log.error_reason || 'Success'}>
                      {log.error_reason || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};

export default MeetingLogs;
