import { createClient } from '@supabase/supabase-js';

export const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
export const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('Supabase credentials missing. AUTH will not work correctly until VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are set in .env');
}

let supabaseInstance: any = null;

export const getSupabase = async () => {
  if (supabaseInstance) return supabaseInstance;

  try {
    // Try to fetch config from our own backend at runtime
    const response = await fetch('/api/config');
    const config = await response.json();
    
    const url = config.supabase_url || import.meta.env.VITE_SUPABASE_URL || 'https://placeholder.supabase.co';
    const key = config.supabase_anon_key || import.meta.env.VITE_SUPABASE_ANON_KEY || 'placeholder';

    supabaseInstance = createClient(url, key, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
        storageKey: 'sb-auth-token-convexa'
      }
    });
    return supabaseInstance;
  } catch (error) {
    console.error('Failed to fetch runtime config, falling back to env vars', error);
    supabaseInstance = createClient(
      import.meta.env.VITE_SUPABASE_URL || 'https://placeholder.supabase.co',
      import.meta.env.VITE_SUPABASE_ANON_KEY || 'placeholder'
    );
    return supabaseInstance;
  }
};

// Also export a default instance for sync legacy code (might be placeholder until getSupabase is called)
export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL || 'https://placeholder.supabase.co',
  import.meta.env.VITE_SUPABASE_ANON_KEY || 'placeholder'
);

