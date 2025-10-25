/**
 * API client for Primary Texts endpoints
 */

import { PrimaryText, TextSection, TextCitation, TextsStats, TextsListResponse } from '@/types/texts';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api';

export interface TextsFilters {
  category?: string;
  era?: string;
  author?: string;
  search?: string;
  ordering?: string;
  page?: number;
}

/**
 * Fetch list of primary texts with optional filters
 */
export async function fetchTexts(filters?: TextsFilters): Promise<TextsListResponse> {
  const params = new URLSearchParams();

  if (filters?.category) params.append('category', filters.category);
  if (filters?.era) params.append('era', filters.era);
  if (filters?.author) params.append('author', filters.author);
  if (filters?.search) params.append('search', filters.search);
  if (filters?.ordering) params.append('ordering', filters.ordering);
  if (filters?.page) params.append('page', filters.page.toString());

  const url = `${API_BASE_URL}/texts/${params.toString() ? '?' + params.toString() : ''}`;

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch texts: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch a single text by slug with all sections
 */
export async function fetchTextBySlug(slug: string): Promise<PrimaryText> {
  const response = await fetch(`${API_BASE_URL}/texts/${slug}/`);

  if (!response.ok) {
    throw new Error(`Failed to fetch text: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch sections for a specific text
 */
export async function fetchTextSections(slug: string): Promise<TextSection[]> {
  const response = await fetch(`${API_BASE_URL}/texts/${slug}/sections/`);

  if (!response.ok) {
    throw new Error(`Failed to fetch sections: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch citations for a specific text
 */
export async function fetchTextCitations(slug: string): Promise<TextCitation[]> {
  const response = await fetch(`${API_BASE_URL}/texts/${slug}/citations/`);

  if (!response.ok) {
    throw new Error(`Failed to fetch citations: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch library statistics
 */
export async function fetchTextsStats(): Promise<TextsStats> {
  const response = await fetch(`${API_BASE_URL}/texts/stats/`);

  if (!response.ok) {
    throw new Error(`Failed to fetch stats: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch a single section by ID
 */
export async function fetchSection(id: number): Promise<TextSection> {
  const response = await fetch(`${API_BASE_URL}/sections/${id}/`);

  if (!response.ok) {
    throw new Error(`Failed to fetch section: ${response.statusText}`);
  }

  return response.json();
}
