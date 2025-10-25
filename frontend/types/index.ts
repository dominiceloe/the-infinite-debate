// API Response Types

// Re-export auth types for convenience
export type { User, LoginRequest, LoginResponse, RegisterRequest, RegisterResponse, AuthContextType } from './auth';

export interface ExternalLink {
  title: string;
  url: string;
}

export interface PersonaExternalLinks {
  primary_works: ExternalLink[];
  wikipedia: string;
  stanford_encyclopedia: string;
  academic: ExternalLink[];
  modern: ExternalLink[];
}

export interface PrimaryText {
  id: number;
  slug: string;
  title: string;
  source_url: string;
  source_type: string;
  word_count: number;
}

export interface Persona {
  id: number;
  name: string;
  slug: string;
  title: string;
  category: string; // Dynamic category from backend (e.g., theologians, philosophers, artists, etc.)
  era: string;
  birth_year: number | null;
  death_year: number | null;
  religion_worldview: string;
  primary_works?: string[];
  primary_texts?: PrimaryText[];  // NEW: actual text objects from database
  external_links?: PersonaExternalLinks;
  core_positions?: string;
  debate_style?: string;
  key_concepts?: string;
  engagement_strategies?: string;
  representative_quotes?: string;
  debate_priorities?: string;
  weaknesses?: string;
  character_notes?: string;
  full_markdown?: string;
  portrait_image?: string;
  required_tier?: 'free' | 'trial' | 'starter' | 'pro' | 'enterprise';
  chronological_order?: number;
  debate_count?: number; // Total debates this persona has participated in
}

// Dynamic object with category keys mapping to persona arrays
export interface PersonasByCategory {
  [category: string]: Persona[];
}

export interface TextCitation {
  id: number;
  debate_message: number;
  text: number;
  text_title: string;
  text_author: string;
  text_slug: string;
  text_section?: number;
  section_breadcrumb?: string;
  citation_text: string;
  extracted_quote?: string;
  match_confidence: number;
  match_method: string;
  verified: boolean;
  created_at: string;
}

export interface DebateMessage {
  id: number;
  persona: Persona;
  round_number: number;
  content: string;
  text_citations?: TextCitation[];
  created_at: string;
}

export interface Debate {
  id: number;
  title: string;
  topic: string;
  slug: string;
  participants?: Persona[];
  depth_level: 'introductory' | 'intermediate' | 'advanced';
  max_rounds: number;
  transcript: string;
  summary: string;
  status: 'pending' | 'generating' | 'completed' | 'failed';
  rounds_completed: number;
  error_message: string;
  messages?: DebateMessage[];
  participant_count?: number;
  participant_names?: string;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface CreateDebateRequest {
  title: string;
  topic: string;
  participant_ids: number[];
  depth_level?: 'introductory' | 'intermediate' | 'advanced';
  max_rounds?: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface PersonaRequest {
  id: number;
  persona_name: string;
  justification: string;
  suggested_sources: string;
  status: 'pending' | 'approved' | 'rejected' | 'completed';
  username: string;
  created_at: string;
  updated_at: string;
}

export interface CreatePersonaRequestRequest {
  persona_name: string;
  justification: string;
  suggested_sources?: string;
}
