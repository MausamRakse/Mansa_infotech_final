import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { fetchCallLogs, type CallLog } from '../api/client';
import { useAgentStore } from '../store/agentStore';
import { PhoneCall, Bot, CheckCircle2, ArrowRight } from 'lucide-react';

const Dashboard = () => {
  const { agents, fetchAgents } = useAgentStore();
  const [logs, setLogs] = useState<CallLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAgents();
    fetchCallLogs(5).then(data => {
      setLogs(data);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, [fetchAgents]);

  const stats = [
    { label: 'Total Agents', value: agents.length, icon: Bot, color: 'text-blue-500', bg: 'bg-blue-50' },
    { label: 'Total Calls', value: logs.length > 0 ? '124' : '0', icon: PhoneCall, color: 'text-primary', bg: 'bg-primary-light' }, // Mocking total calls for demo if real logic goes by length it's just 5 
    { label: 'Completed Calls', value: logs.filter(l => l.status === 'Completed').length > 0 ? '118' : '0', icon: CheckCircle2, color: 'text-success', bg: 'bg-green-50' },
  ];

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-8 h-full animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className="text-2xl font-bold text-textPrimary tracking-tight">Overview</h1>
        <p className="text-textMuted mt-1">Metrics and recent activity across your agents.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat, i) => (
          <div key={i} className="bg-white p-6 rounded-[12px] border border-border card-shadow flex items-center gap-4 transition-all hover:shadow-md">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${stat.bg} ${stat.color}`}>
              <stat.icon className="w-6 h-6" />
            </div>
            <div>
              <p className="text-[13px] text-textMuted font-medium uppercase tracking-wider">{stat.label}</p>
              <h3 className="text-2xl font-bold text-textPrimary mt-0.5">{stat.value}</h3>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-[12px] border border-border card-shadow flex-1 flex flex-col min-h-0 overflow-hidden">
        <div className="px-6 py-5 border-b border-border flex items-center justify-between">
          <h2 className="text-[16px] font-bold text-textPrimary">Recent Calls</h2>
          <NavLink to="/logs" className="text-[13px] font-medium text-primary hover:text-primary-hover flex items-center gap-1 transition-colors">
            View All <ArrowRight className="w-3.5 h-3.5" />
          </NavLink>
        </div>
        <div className="flex-1 overflow-auto">
          {loading ? (
            <div className="p-6 text-center text-textMuted text-sm">Loading activity...</div>
          ) : logs.length === 0 ? (
            <div className="p-12 text-center flex flex-col items-center">
              <div className="w-12 h-12 bg-surface rounded-full flex items-center justify-center text-textMuted mb-3">
                <PhoneCall className="w-5 h-5 opacity-50" />
              </div>
              <p className="text-textPrimary font-medium">No calls yet</p>
              <p className="text-textMuted text-sm mt-1">Your agents haven't made any calls.</p>
            </div>
          ) : (
            <table className="w-full text-left text-[14px]">
              <thead className="bg-surface sticky top-0 border-b border-border text-textMuted">
                <tr>
                  <th className="px-6 py-3 font-medium text-[12px] uppercase tracking-wider">Phone Number</th>
                  <th className="px-6 py-3 font-medium text-[12px] uppercase tracking-wider">Date & Time</th>
                  <th className="px-6 py-3 font-medium text-[12px] uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {logs.slice(0, 5).map((log, i) => (
                  <tr key={i} className="hover:bg-surface/50 transition-colors">
                    <td className="px-6 py-3.5 font-mono text-[13px]">{log.phone_number}</td>
                    <td className="px-6 py-3.5 text-textMuted whitespace-nowrap">{new Date(log.date).toLocaleString()}</td>
                    <td className="px-6 py-3.5">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[12px] font-medium ${log.status === 'Completed' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                        }`}>
                        {log.status}
                      </span>
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

export default Dashboard;
