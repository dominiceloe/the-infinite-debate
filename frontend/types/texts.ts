/**
 * Type definitions for Primary Texts API
 */

export interface PrimaryText {
  id: number;
  title: string;
  slug: string;
  author: string;
  original_language?: string;
  publication_year?: number;
  category: 'philosophy' | 'theology' | 'science' | 'political' | 'ethics' | 'economics' | 'literature' | 'psychology' | 'other';
  era: 'ancient' | 'medieval' | 'early_modern' | 'modern' | 'contemporary';
  source_url?: string;
  source_type?: 'gutenberg' | 'mit_classics' | 'internet_archive' | 'sacred_texts' | 'perseus' | 'manual';
  license?: string;
  translator?: string;
  translation_year?: number;
  edition_notes?: string;
  description?: string;
  word_count: number;
  reading_difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  full_content?: string;
  metadata?: Record<string, any>;
  is_published: boolean;
  processing_status: 'pending' | 'processing' | 'ready' | 'error';
  section_count: number;
  citation_count?: number;
  sections?: TextSection[];
  created_at: string;
  updated_at?: string;
}

export interface TextSection {
  id: number;
  section_type: 'part' | 'book' | 'chapter' | 'section' | 'paragraph' | 'fragment';
  order_index: number;
  title?: string;
  reference_id?: string;
  content: string;
  word_count: number;
  breadcrumb: string;
  parent?: number;
  created_at: string;
}

export interface TextCitation {
  id: number;
  debate_message: number;
  text: number;
  text_title: string;
  text_author: string;
  text_section?: number;
  section_breadcrumb?: string;
  citation_text: string;
  extracted_quote?: string;
  match_confidence: number;
  match_method: 'manual' | 'regex' | 'nlp' | 'llm';
  verified: boolean;
  created_at: string;
}

export interface TextsStats {
  total_texts: number;
  total_words: number;
  by_category: Record<string, number>;
  by_era: Record<string, number>;
}

export interface TextsListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: PrimaryText[];
}
