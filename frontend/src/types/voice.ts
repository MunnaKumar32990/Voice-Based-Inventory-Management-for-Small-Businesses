export type VoiceState = 
  | 'idle' 
  | 'listening' 
  | 'recording' 
  | 'uploading' 
  | 'transcribing' 
  | 'understanding' 
  | 'checking_db'
  | 'needs_confirmation' 
  | 'committing' 
  | 'completed' 
  | 'error';

export interface ParsedCommand {
  action: 'add' | 'remove' | 'query' | 'unknown';
  product: string;
  product_id?: string;
  product_name?: string;
  quantity?: number;
  unit?: string;
  price?: number;
  confidence: number;
  original_text: string;
  detected_language?: string;
  query_type?: string;
  title?: string;
  display_text?: string;
  structured_data?: Record<string, any>;
}

export interface VoiceCommand {
  id: string;
  transcript: string;
  language: string;
  parsed_intent: ParsedCommand;
  status: 'pending' | 'confirmed' | 'cancelled' | 'failed';
  created_at: string;
}

export interface BackendVoicePreview {
  status: string;
  interaction_id?: string;
  transcript?: string;
  detected_language?: string;
  intent?: string;
  query_type?: string;
  title?: string;
  display_text?: string;
  message?: string;
  confirmation_text?: string;
  answer?: unknown;
  structured_data?: Record<string, any>;
  product_name?: string;
  quantity?: number;
  unit?: string;
  candidates?: Array<{ id: string; name: string }>;
  command?: {
    intent: string;
    product_text?: string;
    product_id?: string;
    product_name?: string;
    quantity?: number;
    unit?: string;
    price_total?: number | null;
    confidence?: number;
  };
  preview?: unknown;
}
