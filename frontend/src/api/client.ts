import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { "Content-Type": "application/json" },
});

export const createAgent = (data: CreateAgentPayload) =>
  api.post("/agents/create-agent", data).then(r => r.data);

export const listAgents = () =>
  api.get("/agents/").then(r => r.data.agents);

export const triggerCall = (data: TriggerCallPayload) =>
  api.post("/calls/trigger-call", data).then(r => r.data);

export const fetchCallLogs = (limit = 50) =>
  api.get(`/logs/call-logs?limit=${limit}`).then(r => r.data.logs);

export interface CreateAgentPayload {
  agent_name: string;
  custom_first_line: string;
  prompt_text: string;
  stt_language: string;
  voice_id: number;
  enable_calendar_booking: boolean;
}

export interface TriggerCallPayload {
  agent_id: string;
  phone_number: string;
  custom_first_line?: string;
}

export interface Agent {
  id: string;
  name: string;
  greeting: string;
  prompt: string;
  language: string;
  voice_id: number;
  meeting_enabled: boolean;
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
}
