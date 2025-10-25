'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import Link from 'next/link';
import { use } from 'react';
import type { Persona } from '@/types';

export default function PersonaDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);

  const { data: persona, isLoading, error } = useQuery<Persona>({
    queryKey: ['persona', slug],
    queryFn: () => apiClient.personas.getBySlug(slug),
  });

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading persona...</p>
        </div>
      </div>
    );
  }

  if (error || !persona) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Persona Not Found</h1>
          <Link href="/" className="text-indigo-600 hover:underline">
            ← Back to Home
          </Link>
        </div>
      </div>
    );
  }

  const categoryColors = {
    theologian: 'from-rose-500 to-pink-500',
    philosopher: 'from-indigo-500 to-purple-500',
    scientist: 'from-emerald-500 to-teal-500',
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <Link href="/" className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Philosophical Debates
            </Link>
            <div className="flex gap-4">
              <Link href="/" className="text-gray-600 hover:text-gray-900">
                ← Back to Home
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto">
          {/* Persona Header */}
          <div className="bg-white rounded-lg border border-gray-200 p-8 mb-8">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 className="text-4xl font-bold text-gray-900 mb-2">{persona.name}</h1>
                <p className="text-xl text-gray-600">{persona.title}</p>
              </div>
              <span className={`px-4 py-2 rounded-full text-white font-medium bg-gradient-to-r ${categoryColors[persona.category]}`}>
                {persona.category}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-6 text-sm">
              <div>
                <span className="font-semibold text-gray-700">Era:</span>
                <span className="ml-2 text-gray-600">{persona.era}</span>
              </div>
              {persona.religion_worldview && (
                <div>
                  <span className="font-semibold text-gray-700">Worldview:</span>
                  <span className="ml-2 text-gray-600">{persona.religion_worldview}</span>
                </div>
              )}
            </div>

            {persona.primary_works && persona.primary_works.length > 0 && (
              <div className="mt-6">
                <h3 className="font-semibold text-gray-700 mb-2">Primary Works:</h3>
                <ul className="list-disc list-inside text-gray-600 space-y-1">
                  {persona.primary_works.map((work, i) => (
                    <li key={i}>{work}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Core Positions */}
          {persona.core_positions && (
            <ContentSection title="Core Positions" content={persona.core_positions} />
          )}

          {/* Debate Style */}
          {persona.debate_style && (
            <ContentSection title="Debate Style" content={persona.debate_style} />
          )}

          {/* Key Concepts */}
          {persona.key_concepts && (
            <ContentSection title="Key Concepts" content={persona.key_concepts} />
          )}

          {/* Representative Quotes */}
          {persona.representative_quotes && (
            <ContentSection title="Representative Quotes" content={persona.representative_quotes} />
          )}

          {/* Debate Priorities */}
          {persona.debate_priorities && (
            <ContentSection title="Debate Priorities" content={persona.debate_priorities} />
          )}

          {/* CTA */}
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg p-8 text-white text-center mt-8">
            <h2 className="text-2xl font-bold mb-4">Want to see {persona.name} in a debate?</h2>
            <Link
              href="/debates/new"
              className="inline-block bg-white text-indigo-600 px-8 py-3 rounded-lg font-medium hover:bg-gray-100 transition-colors"
            >
              Create a Debate
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}

function ContentSection({ title, content }: { title: string; content: string }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">{title}</h2>
      <div className="prose max-w-none text-gray-700 whitespace-pre-wrap">{content}</div>
    </div>
  );
}
