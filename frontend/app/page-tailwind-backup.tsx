'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import Link from 'next/link';
import type { PersonasByCategory } from '@/types';

export default function Home() {
  const { data, isLoading, error } = useQuery<PersonasByCategory>({
    queryKey: ['personas', 'by_category'],
    queryFn: () => apiClient.personas.getByCategory(),
  });

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <h1 className="text-xl md:text-2xl font-bold text-red-600 mb-4">Error Loading Personas</h1>
          <p className="text-sm md:text-base text-gray-600">Make sure the backend server is running on port 8002</p>
          <p className="text-xs md:text-sm text-gray-500 mt-2 break-words">{String(error)}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 md:py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                Philosophical Debates
              </h1>
              <p className="text-sm md:text-base text-gray-600 mt-1">AI-powered dialogues between historical thinkers</p>
            </div>
            <div className="flex gap-2 sm:gap-3">
              <Link
                href="/debates"
                className="flex-1 sm:flex-none px-4 sm:px-6 py-2 sm:py-3 text-sm sm:text-base border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-gray-700 font-medium text-center"
              >
                View Debates
              </Link>
              <Link
                href="/debates/new"
                className="flex-1 sm:flex-none bg-indigo-600 hover:bg-indigo-700 text-white px-4 sm:px-6 py-2 sm:py-3 text-sm sm:text-base rounded-lg font-medium transition-colors text-center"
              >
                Create Debate
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6 md:py-12">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading personas...</p>
            </div>
          </div>
        ) : (
          <>
            {/* Introduction */}
            <div className="text-center mb-8 md:mb-12">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 mb-3 md:mb-4 px-2">
                Choose Your Thinkers
              </h2>
              <p className="text-base sm:text-lg md:text-xl text-gray-600 max-w-2xl mx-auto px-4">
                Select from {(data?.theologians.length || 0) + (data?.philosophers.length || 0) + (data?.scientists.length || 0)} historical figures to create philosophical debates.
                What would Marx say to Aquinas? What would Kant think of Einstein's physics?
              </p>
            </div>

            {/* Theologians */}
            {data?.theologians && data.theologians.length > 0 && (
              <PersonaCategory
                title="Theologians"
                description="Religious thinkers and theologians"
                personas={data.theologians}
                color="rose"
              />
            )}

            {/* Philosophers */}
            {data?.philosophers && data.philosophers.length > 0 && (
              <PersonaCategory
                title="Philosophers"
                description="Secular philosophers and thinkers"
                personas={data.philosophers}
                color="indigo"
              />
            )}

            {/* Scientists */}
            {data?.scientists && data.scientists.length > 0 && (
              <PersonaCategory
                title="Scientists"
                description="Scientific figures and researchers"
                personas={data.scientists}
                color="emerald"
              />
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t mt-12 md:mt-20 py-6 md:py-8 bg-white/50">
        <div className="container mx-auto px-4 text-center text-gray-600">
          <p className="text-sm md:text-base">Built with AI • Powered by Claude • Open to exploration</p>
        </div>
      </footer>
    </div>
  );
}

interface PersonaCategoryProps {
  title: string;
  description: string;
  personas: Array<{
    id: number;
    name: string;
    slug: string;
    title: string;
    era: string;
    category: string;
  }>;
  color: 'rose' | 'indigo' | 'emerald';
}

function PersonaCategory({ title, description, personas, color }: PersonaCategoryProps) {
  const colorClasses = {
    rose: 'from-rose-500 to-pink-500',
    indigo: 'from-indigo-500 to-purple-500',
    emerald: 'from-emerald-500 to-teal-500',
  };

  return (
    <section className="mb-10 md:mb-16">
      <div className="mb-4 md:mb-6">
        <h3 className={`text-xl md:text-2xl font-bold bg-gradient-to-r ${colorClasses[color]} bg-clip-text text-transparent`}>
          {title}
        </h3>
        <p className="text-sm md:text-base text-gray-600 mt-1">{description}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 md:gap-4">
        {personas.map((persona) => (
          <Link
            key={persona.id}
            href={`/personas/${persona.slug}`}
            className="group bg-white rounded-lg border border-gray-200 p-4 hover:shadow-lg hover:border-indigo-300 transition-all duration-200"
          >
            <h4 className="font-semibold text-base md:text-lg text-gray-900 group-hover:text-indigo-600 transition-colors">
              {persona.name}
            </h4>
            <p className="text-sm text-gray-500 mt-1 line-clamp-1">{persona.title}</p>
            <p className="text-xs text-gray-400 mt-2">{persona.era}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
