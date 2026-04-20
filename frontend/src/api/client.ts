import axios from "axios";
import { getSupabase } from "../lib/supabase";

// In production, everything shares the same origin. In dev, we use the local FastAPI server.
const devUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// Detect production environment to use relative '/api' path
const apiOrigin = (typeof window !== 'undefined' && window.location.hostname !== 'localhost')
  ? "/api"
  : `${devUrl}/api`;

const api = axios.create({
  baseURL: apiOrigin,
  headers: { "Content-Type": "application/json" },
});

// Interceptor to add Supabase token
api.interceptors.request.use(async (config) => {
  const sb = await getSupabase();
  const { data: { session } } = await sb.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

export const createAgent = (data: CreateAgentPayload) =>
  api.post("agents/create-agent", data).then(r => r.data);

export const listAgents = () =>
  api.get("agents/").then(r => r.data.agents);

export const triggerCall = (data: TriggerCallPayload) =>
  api.post("calls/trigger-call", data).then(r => r.data);

export const fetchCallLogs = async (limit = 50): Promise<CallLog[]> => {
  const { data } = await api.get(`logs/call-logs?limit=${limit}`);
  return data.logs;
};

export const fetchStats = async (): Promise<{ total_calls: number; total_completed: number; active_agents: number }> => {
  const { data } = await api.get('logs/stats');
  return data;
};

export const updateAgentApi = (data: UpdateAgentPayload) =>
  api.post("agents/update-agent", data).then(r => r.data);

export const deleteAgentApi = (agent_id: string) =>
  api.post("agents/delete-agent", { agent_id }).then(r => r.data);

export const createCampaign = (data: CreateCampaignPayload) =>
  api.post("campaigns/create", data).then(r => r.data);

export interface CreateAgentPayload {
  agent_name: string;
  custom_first_line: string;
  prompt_text: string;
  stt_language: string;
  voice_id: number;
  enable_calendar_booking: boolean;
  cal_api_key?: string;
  cal_event_type_id?: string;
}

export interface UpdateAgentPayload extends CreateAgentPayload {
  agent_id: string;
}

export interface TriggerCallPayload {
  agent_id: string;
  phone_number: string;
  custom_first_line?: string;
  is_booking_agent?: boolean;
}

export interface CreateCampaignPayload {
  campaign_name: string;
  agent_id: string;
  start_time: string;
  end_time: string;
  time_zone: string;
  custom_first_line: string;
  retries: string;
}

export interface Agent {
  id: string;
  name: string;
  greeting: string;
  prompt: string;
  language: string;
  voice_id: number;
  meeting_enabled: boolean;
  cal_api_key?: string;
  cal_event_type_id?: string;
  category?: "customer_care" | "growth" | "custom";
}

export interface CallLog {
  call_id: string;
  phone_number: string;
  date: string;
  status: "Completed" | "Processing";
  recording_url: string | null;
  transcript: string | null;
  json_output: string | null;
  agent_name: string;
}
