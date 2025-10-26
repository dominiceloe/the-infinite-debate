import React from 'react';
import Link from 'next/link';
import type { TextCitation } from '@/types';

interface MessageContentProps {
  content: string;
  citations?: TextCitation[];
}

/**
 * Renders message content with inline citation links.
 *
 * Takes clean content (without {Title} markers) and citations array,
 * then renders citation titles as clickable links to the primary texts.
 */
export default function MessageContent({ content, citations }: MessageContentProps) {
  if (!citations || citations.length === 0) {
    return <>{content}</>;
  }

  // Build a list of all citation positions in the content
  interface CitationMatch {
    start: number;
    end: number;
    citation: TextCitation;
  }

  const matches: CitationMatch[] = [];

  // Find all occurrences of each citation title in the content
  citations.forEach((citation) => {
    const title = citation.text_title;
    let searchPos = 0;

    while (searchPos < content.length) {
      const index = content.indexOf(title, searchPos);
      if (index === -1) break;

      matches.push({
        start: index,
        end: index + title.length,
        citation: citation,
      });

      searchPos = index + 1; // Move forward to find overlapping matches
    }
  });

  // If no matches found, return plain content
  if (matches.length === 0) {
    return <>{content}</>;
  }

  // Sort matches by start position
  matches.sort((a, b) => a.start - b.start);

  // Remove overlapping matches (keep first occurrence)
  const nonOverlapping: CitationMatch[] = [];
  let lastEnd = -1;

  matches.forEach((match) => {
    if (match.start >= lastEnd) {
      nonOverlapping.push(match);
      lastEnd = match.end;
    }
  });

  // Build the result as an array of text and Link elements
  const result: React.ReactNode[] = [];
  let currentPos = 0;

  nonOverlapping.forEach((match, index) => {
    // Add text before this citation
    if (match.start > currentPos) {
      result.push(content.substring(currentPos, match.start));
    }

    // Add the citation as a styled link
    result.push(
      <Link
        key={`citation-${match.citation.id}-${index}`}
        href={`/texts/${match.citation.text_slug}`}
        style={{
          color: '#22c55e',
          textDecoration: 'underline',
          textDecorationColor: 'rgba(34, 197, 94, 0.5)',
          textDecorationThickness: '2px',
          transition: 'all 0.2s ease',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.textDecorationColor = 'rgba(34, 197, 94, 1)';
          e.currentTarget.style.color = '#16a34a';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.textDecorationColor = 'rgba(34, 197, 94, 0.5)';
          e.currentTarget.style.color = '#22c55e';
        }}
      >
        {content.substring(match.start, match.end)}
      </Link>
    );

    currentPos = match.end;
  });

  // Add remaining text
  if (currentPos < content.length) {
    result.push(content.substring(currentPos));
  }

  return <>{result}</>;
}
