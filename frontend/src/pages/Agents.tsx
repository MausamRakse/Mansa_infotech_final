import { useState, useEffect } from 'react';
import { useAgentStore } from '../store/agentStore';
import type { Agent } from '../api/client';
import AgentCard from '../components/AgentCard';
import CreateAgentModal from '../components/CreateAgentModal';
import EditAgentModal from '../components/EditAgentModal';
import TriggerCallModal from '../components/TriggerCallModal';
import { Plus } from 'lucide-react';

const defaultAgents: Agent[] = [
  {
    id: 'default-1',
    name: 'Support Hub',
    greeting: 'Hi, you have reached customer support. How can I assist you?',
    prompt: "You are an intelligent Support Hub agent. Your goal is to deliver seamless\ncustomer care by resolving user queries, managing billing inquiries, handling\nfeature requests, and assisting users in booking their orders with ease.\nKeep responses short and conversational — this is a voice call.\nAlways confirm the user's request before taking action.",
    language: 'en',
    voice_id: 1,
    meeting_enabled: true,
    category: 'customer_care'
  },
  {
    id: 'default-2',
    name: 'Outreach Campaigns',
    greeting: 'Hello! I am calling from the outreach team. Do you have a moment?',
    prompt: "You are an outreach campaign specialist focused on driving growth through\nstrategic cold outreach, re-engagement initiatives, and product launch campaigns,\nwhile also executing targeted promotions and delivering timely customer reminders.\nKeep all responses to 1-2 sentences. Be warm, professional, and concise.",
    language: 'en',
    voice_id: 2,
    meeting_enabled: false,
    category: 'growth'
  }
];

const Agents = () => {
  const { agents, fetchAgents, loading } = useAgentStore();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedAgentForEdit, setSelectedAgentForEdit] = useState<Agent | null>(null);
  const [selectedAgentForCall, setSelectedAgentForCall] = useState<Agent | null>(null);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const allAgents = [...defaultAgents, ...agents.filter(a => !defaultAgents.find(d => d.name === a.name))];

  return (
    <div className="max-w-6xl mx-auto h-full flex flex-col animate-in fade-in duration-500">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-textPrimary tracking-tight">Agents</h1>
          <p className="text-textMuted mt-1">Manage your team of AI voice agents. Click any card to manage.</p>
        </div>
        <button
          onClick={() => setIsCreateOpen(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Create an Agent
        </button>
      </div>

      <div className="flex-1 overflow-y-auto pb-8">
        {loading && agents.length === 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 opacity-60">
            {[1, 2, 3, 4].map(i => <div key={i} className="h-48 bg-surface border border-border rounded-[12px] animate-pulse" />)}
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {allAgents.map((agent) => (
              <AgentCard
                key={agent.id}
                agent={agent}
                onEdit={() => setSelectedAgentForEdit(agent)}
                onTriggerCall={() => setSelectedAgentForCall(agent)}
              />
            ))}
          </div>
        )}
      </div>

      {isCreateOpen && (
        <CreateAgentModal onClose={() => setIsCreateOpen(false)} />
      )}

      {selectedAgentForEdit && (
        <EditAgentModal
          agent={selectedAgentForEdit}
          onClose={() => setSelectedAgentForEdit(null)}
        />
      )}

      {selectedAgentForCall && (
        <TriggerCallModal
          agent={selectedAgentForCall}
          onClose={() => setSelectedAgentForCall(null)}
        />
      )}
    </div>
  );
};

export default Agents;
