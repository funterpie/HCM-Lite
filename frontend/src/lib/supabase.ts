/**
 * @file supabase.ts
 * @description Supabase client initialization for authentication handling.
 *
 * ARCHITECTURAL MANDATE (PROJECT.md section 6):
 * - Frontend uses Supabase ONLY for authentication (signInWithPassword, session retrieval).
 * - All application data queries and mutations must flow through the FastAPI backend
 *   with `Authorization: Bearer <access_token>`.
 * - Never expose the service-role key on the client; only the anon public key is stored here.
 */

import { createClient } from '@supabase/supabase-js';

// Public Supabase credentials from environment variables
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://dummy.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'dummy-key';

/**
 * Singleton Supabase client instance used strictly for managing auth tokens and sessions.
 */
export const supabase = createClient(supabaseUrl, supabaseAnonKey);
