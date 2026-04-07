import { createClient } from '@supabase/supabase-js';
import * as dotenv from 'dotenv';
import path from 'path';

// Load .env from frontend folder
dotenv.config({ path: path.resolve(__dirname, 'frontend/.env') });

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY;

console.log('Checking Supabase connection...');
console.log('URL:', supabaseUrl || '(missing)');
console.log('Key:', supabaseAnonKey ? '(present)' : '(missing)');

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('\n❌ Supabase credentials missing. Please add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to frontend/.env');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function testConnection() {
  try {
    const { data, error } = await supabase.from('pg_catalog.pg_tables').select('tablename').limit(1);
    if (error) throw error;
    console.log('\n✅ Supabase connection successful! Found tables:', data.length);
  } catch (err: any) {
    console.error('\n❌ Connection failed:', err.message);
  }
}

testConnection();
