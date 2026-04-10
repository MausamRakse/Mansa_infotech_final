import { createClient, SupabaseClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://kkmftbhqfmgaixqnwked.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtrbWZ0YmhxZm1nYWl4cW53a2VkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU1NDY1MzQsImV4cCI6MjA5MTEyMjUzNH0.he9kNYN6LwB3iRUTlFdzOYBX-jejbFEUFZOJbw2rmp0';

// Use env vars if available (local dev), otherwise fall back to hardcoded production values
const url = import.meta.env.VITE_SUPABASE_URL || SUPABASE_URL;
const key = import.meta.env.VITE_SUPABASE_ANON_KEY || SUPABASE_ANON_KEY;

const supabaseClient: SupabaseClient = createClient(url, key, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    storageKey: 'sb-auth-token-convexa',
  },
});

export const getSupabase = async (): Promise<SupabaseClient> => {
  return supabaseClient;
};
