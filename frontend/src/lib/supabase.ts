import { createClient, SupabaseClient } from '@supabase/supabase-js';

let supabaseInstance: SupabaseClient | null = null;

export const getSupabase = async (): Promise<SupabaseClient> => {
  if (supabaseInstance) return supabaseInstance;

  let url = import.meta.env.VITE_SUPABASE_URL;
  let key = import.meta.env.VITE_SUPABASE_ANON_KEY;

  // If env vars aren't baked in, fetch from our backend at runtime
  if (!url || !key) {
    try {
      const response = await fetch('/api/config');
      const config = await response.json();
      url = config.supabase_url;
      key = config.supabase_anon_key;
    } catch (err) {
      console.error('[Supabase] Failed to fetch runtime config:', err);
    }
  }

  if (!url || !key) {
    throw new Error('Supabase credentials are missing. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in your Render environment variables.');
  }

  supabaseInstance = createClient(url, key, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
      storageKey: 'sb-auth-token-convexa',
    },
  });

  return supabaseInstance;
};
