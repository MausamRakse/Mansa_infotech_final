import type { Agent } from '../api/client';
import { Headphones, Megaphone, Bot, Sparkles } from 'lucide-react';

interface AgentCardProps {
  agent: Agent;
  onEdit: () => void;
  onTriggerCall: () => void;
}

const AgentCard = ({ agent, onEdit, onTriggerCall }: AgentCardProps) => {
  const isCustom = !agent.category;
  
  const getIcon = () => {
    if (agent.category === 'customer_care') return <Headphones className="w-5 h-5 text-primary" />;
    if (agent.category === 'growth') return <Megaphone className="w-5 h-5 text-primary" />;
    return <Bot className="w-5 h-5 text-primary" />;
  };

  const getBadge = () => {
    if (agent.category === 'customer_care') return 'CUSTOMER CARE';
    if (agent.category === 'growth') return 'GROWTH';
    return 'CUSTOM AGENT';
  };

  return (
    <div className="group bg-white rounded-[12px] border border-border card-shadow p-6 flex flex-col flex-shrink-0 transition-all hover:shadow-md hover:border-primary/30 cursor-pointer h-full min-h-[220px]">
      <div className="flex justify-between items-start mb-4">
        <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-primary-light text-primary text-[10px] font-bold tracking-widest leading-none">
          {isCustom && <Sparkles className="w-3 h-3" />}
          {getBadge()}
        </span>
        <div className="w-10 h-10 rounded-full bg-surface flex items-center justify-center group-hover:bg-primary-light transition-colors">
          {getIcon()}
        </div>
      </div>
      
      <div className="flex-1">
        <h3 className="text-[18px] font-bold text-textPrimary mb-2 leading-tight">{agent.name}</h3>
        <p className="text-[14px] text-textMuted line-clamp-2">
          {agent.prompt.split('\n')[0]}
        </p>
      </div>

      <div className="mt-6 flex items-center gap-3 pt-4 border-t border-border/50">
        <button 
          onClick={(e) => { e.stopPropagation(); onEdit(); }} 
          className="btn-outline flex-1 text-[13px] py-1.5"
        >
          Edit
        </button>
        <button 
          onClick={(e) => { e.stopPropagation(); onTriggerCall(); }} 
          className="btn-primary flex-1 text-[13px] py-1.5 shadow-sm shadow-primary/20"
        >
          Trigger Call
        </button>
      </div>
    </div>
  );
};

export default AgentCard;
