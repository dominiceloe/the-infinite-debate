'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import type { Debate } from '@/types';
import ReactMarkdown from 'react-markdown';

export default function DebateViewPage() {
  const params = useParams();
  const slug = params.slug as string;
  const queryClient = useQueryClient();

  // Fetch debate details with polling
  const { data: debate, isLoading, error } = useQuery<Debate>({
    queryKey: ['debate', slug],
    queryFn: () => apiClient.debates.getBySlug(slug),
    refetchInterval: (query) => {
      // Poll every 2 seconds while generating
      const data = query.state.data;
      return data?.status === 'generating' ? 2000 : false;
    },
    refetchIntervalInBackground: true, // Keep polling even when tab is not focused
  });

  // Generate debate mutation
  const generateMutation = useMutation({
    mutationFn: () => apiClient.debates.generate(slug),
    onSuccess: (data) => {
      // Update the query data immediately with generating status
      queryClient.setQueryData(['debate', slug], data);
      // Force refetch to start polling
      queryClient.invalidateQueries({ queryKey: ['debate', slug] });
    },
  });

  // Export debate
  const handleExport = async () => {
    try {
      const response = await apiClient.debates.export(slug, 'markdown');
      const blob = new Blob([response.content], { type: 'text/markdown' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = response.filename;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
      alert('Failed to export debate');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading debate...</p>
        </div>
      </div>
    );
  }

  if (error || !debate) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
        <div className="container mx-auto px-4 py-12">
          <div className="max-w-2xl mx-auto bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-xl font-bold text-red-900 mb-2">Error Loading Debate</h2>
            <p className="text-red-700">{error?.message || 'Debate not found'}</p>
            <Link href="/" className="mt-4 inline-block text-indigo-600 hover:text-indigo-800">
              ← Back to Home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Philosophical Debates
            </Link>
            <div className="flex gap-4 items-center">
              {debate.status === 'completed' && (
                <button
                  onClick={handleExport}
                  className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-gray-700"
                >
                  Export Markdown
                </button>
              )}
              <Link href="/" className="text-gray-600 hover:text-gray-900">
                ← Back
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto">
          {/* Title and Status */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-4">
              <h1 className="text-4xl font-bold text-gray-900">{debate.title}</h1>
              <StatusBadge status={debate.status} />
            </div>
            <p className="text-lg text-gray-600 mb-4">{debate.topic}</p>

            {/* Metadata */}
            <div className="flex flex-wrap gap-4 text-sm text-gray-500">
              <div>
                <span className="font-medium">Participants:</span> {debate.participant_names || debate.participants?.length}
              </div>
              <div>
                <span className="font-medium">Depth:</span> {debate.depth_level}
              </div>
              <div>
                <span className="font-medium">Rounds:</span> {debate.rounds_completed}/{debate.max_rounds}
              </div>
            </div>
          </div>

          {/* Participants List */}
          {debate.participants && debate.participants.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Participants</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {debate.participants.map((persona) => (
                  <Link
                    key={persona.id}
                    href={`/personas/${persona.slug}`}
                    className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 transition-colors"
                  >
                    <div>
                      <div className="font-semibold text-sm text-gray-900">{persona.name}</div>
                      <div className="text-xs text-gray-500">{persona.era}</div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Status-based Content */}
          {debate.status === 'pending' && (
            <PendingState debate={debate} generateMutation={generateMutation} />
          )}

          {debate.status === 'generating' && (
            <GeneratingState debate={debate} />
          )}

          {debate.status === 'completed' && (
            <CompletedState debate={debate} />
          )}

          {debate.status === 'failed' && (
            <FailedState debate={debate} generateMutation={generateMutation} />
          )}
        </div>
      </main>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors = {
    pending: 'bg-gray-100 text-gray-700',
    generating: 'bg-blue-100 text-blue-700',
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
  };

  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${colors[status as keyof typeof colors] || colors.pending}`}>
      {status}
    </span>
  );
}

function PendingState({ debate, generateMutation }: { debate: Debate; generateMutation: any }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
      <div className="max-w-md mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Ready to Generate</h2>
        <p className="text-gray-600 mb-6">
          This debate is configured and ready. Click the button below to generate the philosophical dialogue between these thinkers.
        </p>
        <button
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
          className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition-colors"
        >
          {generateMutation.isPending ? 'Starting Generation...' : 'Generate Debate'}
        </button>
        {generateMutation.isError && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4 text-red-800 text-sm">
            Error: {generateMutation.error?.message || 'Failed to start generation'}
          </div>
        )}
      </div>
    </div>
  );
}

function GeneratingState({ debate }: { debate: Debate }) {
  // Auto-scroll to bottom when transcript updates
  React.useEffect(() => {
    if (debate.transcript) {
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    }
  }, [debate.transcript]);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-8">
      {/* Show transcript immediately without disabled overlay */}
      {debate.transcript && (
        <div className="prose prose-lg max-w-none mb-6">
          <ReactMarkdown
            components={{
              h1: ({ children }) => <h1 className="text-3xl font-bold text-gray-900 mb-4">{children}</h1>,
              h2: ({ children }) => <h2 className="text-2xl font-bold text-gray-900 mt-8 mb-4">{children}</h2>,
              h3: ({ children }) => <h3 className="text-xl font-semibold text-indigo-600 mt-6 mb-3">{children}</h3>,
              p: ({ children }) => <p className="text-gray-700 mb-4 leading-relaxed">{children}</p>,
              ul: ({ children }) => <ul className="list-disc list-inside mb-4 text-gray-700">{children}</ul>,
              li: ({ children }) => <li className="mb-1">{children}</li>,
            }}
          >
            {debate.transcript}
          </ReactMarkdown>
        </div>
      )}

      {/* Compact status indicator at bottom */}
      <div className="sticky bottom-4 bg-indigo-600 text-white rounded-full px-6 py-3 shadow-lg inline-flex items-center gap-3 mx-auto">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
        <span className="font-medium">
          Generating... Round {debate.rounds_completed} of {debate.max_rounds}
        </span>
      </div>
    </div>
  );
}

function CompletedState({ debate }: { debate: Debate }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-8">
      <div className="mb-6 pb-6 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Debate Complete</h2>
        <p className="text-gray-600">
          Generated on {new Date(debate.completed_at!).toLocaleString()}
        </p>
      </div>

      {/* Full Transcript */}
      <div className="prose prose-lg max-w-none">
        <ReactMarkdown
          components={{
            h1: ({ children }) => <h1 className="text-3xl font-bold text-gray-900 mb-4">{children}</h1>,
            h2: ({ children }) => <h2 className="text-2xl font-bold text-gray-900 mt-8 mb-4">{children}</h2>,
            h3: ({ children }) => <h3 className="text-xl font-semibold text-indigo-600 mt-6 mb-3">{children}</h3>,
            p: ({ children }) => <p className="text-gray-700 mb-4 leading-relaxed">{children}</p>,
            ul: ({ children }) => <ul className="list-disc list-inside mb-4 text-gray-700">{children}</ul>,
            li: ({ children }) => <li className="mb-1">{children}</li>,
          }}
        >
          {debate.transcript}
        </ReactMarkdown>
      </div>
    </div>
  );
}

function FailedState({ debate, generateMutation }: { debate: Debate; generateMutation: any }) {
  return (
    <div className="bg-red-50 rounded-lg border border-red-200 p-8">
      <div className="text-center max-w-md mx-auto">
        <h2 className="text-2xl font-bold text-red-900 mb-4">Generation Failed</h2>
        <p className="text-red-700 mb-6">
          {debate.error_message || 'An unknown error occurred during generation.'}
        </p>
        <button
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
          className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition-colors"
        >
          {generateMutation.isPending ? 'Retrying...' : 'Retry Generation'}
        </button>
      </div>
    </div>
  );
}
