'use client';

import { use, useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Container,
  Typography,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Link as MuiLink,
  Divider,
  Card,
  CardContent,
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material';
import { Book, Language, CalendarMonth, Source, ViewAgenda, Subject } from '@mui/icons-material';
import Image from 'next/image';
import Header from '@/components/Header';
import { fetchTextBySlug } from '@/lib/api/texts';

interface PageProps {
  params: Promise<{ slug: string }>;
}

type ReadingMode = 'continuous' | 'sections';

export default function TextReaderPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const slug = resolvedParams.slug;
  const [readingMode, setReadingMode] = useState<ReadingMode>('sections');
  const [imageError, setImageError] = useState(false);

  // Load reading mode preference from localStorage
  useEffect(() => {
    const savedMode = localStorage.getItem('text-reading-mode') as ReadingMode | null;
    if (savedMode) {
      setReadingMode(savedMode);
    }
  }, []);

  // Save reading mode preference to localStorage
  const handleReadingModeChange = (
    _event: React.MouseEvent<HTMLElement>,
    newMode: ReadingMode | null
  ) => {
    if (newMode !== null) {
      setReadingMode(newMode);
      localStorage.setItem('text-reading-mode', newMode);
    }
  };

  const { data: text, isLoading, error } = useQuery({
    queryKey: ['text', slug],
    queryFn: () => fetchTextBySlug(slug),
  });

  if (isLoading) {
    return (
      <>
        <Header backTo="/texts" backLabel="Back to Library" />
        <Container maxWidth="lg" sx={{ py: 8 }}>
          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <CircularProgress />
          </Box>
        </Container>
      </>
    );
  }

  if (error || !text) {
    return (
      <>
        <Header backTo="/texts" backLabel="Back to Library" />
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Alert severity="error">
            Failed to load text. Please try again or return to the library.
          </Alert>
        </Container>
      </>
    );
  }

  return (
    <>
      <Header
        backTo="/texts"
        backLabel="Back to Library"
        breadcrumbs={[
          { label: 'Library', href: '/texts' },
          { label: text.title }
        ]}
      />
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Text Header */}
      <Paper sx={{ p: 4, mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          {text.title}
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Box
            sx={{
              width: 80,
              height: 80,
              borderRadius: 1,
              overflow: 'hidden',
              flexShrink: 0,
              bgcolor: 'grey.200',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Image
              src={imageError ? '/portraits/default.svg' : `/portraits/${text.author.toLowerCase().replace(/['\s.]/g, '-').replace(/\./g, '')}.png`}
              alt={text.author}
              width={80}
              height={80}
              style={{ objectFit: 'cover', width: '100%', height: '100%' }}
              onError={() => setImageError(true)}
              unoptimized
            />
          </Box>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="h6" color="text.secondary">
                by {text.author}
              </Typography>
            </Box>
          </Box>
        </Box>

        {text.translator && (
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            Translated by {text.translator}
            {text.translation_year && ` (${text.translation_year})`}
          </Typography>
        )}

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 3 }}>
          <Chip label={text.category} color="primary" />
          <Chip label={text.era.replace('_', ' ')} color="secondary" />
          {text.publication_year && (
            <Chip icon={<CalendarMonth />} label={text.publication_year} />
          )}
          <Chip label={`${text.reading_difficulty} level`} variant="outlined" />
        </Box>

        <Divider sx={{ my: 3 }} />

        <Box sx={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Word Count
            </Typography>
            <Typography variant="h6">{text.word_count.toLocaleString()}</Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Sections
            </Typography>
            <Typography variant="h6">{text.section_count}</Typography>
          </Box>
          {text.citation_count !== undefined && text.citation_count > 0 && (
            <Box>
              <Typography variant="body2" color="text.secondary">
                Cited in Debates
              </Typography>
              <Typography variant="h6">{text.citation_count} times</Typography>
            </Box>
          )}
          {text.original_language && (
            <Box>
              <Typography variant="body2" color="text.secondary">
                <Language sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                Original Language
              </Typography>
              <Typography variant="body1">{text.original_language}</Typography>
            </Box>
          )}
        </Box>

        {text.description && (
          <>
            <Divider sx={{ my: 3 }} />
            <Typography variant="body1">{text.description}</Typography>
          </>
        )}

        {text.source_url && (
          <>
            <Divider sx={{ my: 3 }} />
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Source
              </Typography>
              <MuiLink href={text.source_url} target="_blank" rel="noopener noreferrer">
                <Source sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                {text.source_type?.replace('_', ' ').toUpperCase()}
              </MuiLink>
            </Box>
          </>
        )}
      </Paper>

      {/* Text Content Header with Reading Mode Toggle */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" component="h2">
          <Book sx={{ verticalAlign: 'middle', mr: 1 }} />
          Text Content
        </Typography>

        {text.sections && text.sections.length > 0 && (
          <ToggleButtonGroup
            value={readingMode}
            exclusive
            onChange={handleReadingModeChange}
            size="small"
            sx={{
              '& .MuiToggleButton-root': {
                px: 2,
                py: 0.5,
                fontSize: '0.875rem',
                '&.Mui-selected': {
                  bgcolor: 'primary.main',
                  color: 'white',
                  '&:hover': {
                    bgcolor: 'primary.dark',
                  },
                },
              },
            }}
          >
            <ToggleButton value="continuous">
              <Subject sx={{ fontSize: '1rem', mr: 0.5 }} />
              Continuous
            </ToggleButton>
            <ToggleButton value="sections">
              <ViewAgenda sx={{ fontSize: '1rem', mr: 0.5 }} />
              Sections
            </ToggleButton>
          </ToggleButtonGroup>
        )}
      </Box>

      {text.sections && text.sections.length > 0 ? (
        readingMode === 'continuous' ? (
          // Continuous Reading View
          <Paper sx={{ p: 4 }}>
            {text.sections.map((section) => (
              <Box key={section.id} sx={{ mb: 3 }}>
                {section.title && (
                  <Typography
                    variant="h6"
                    sx={{
                      mb: 2,
                      fontWeight: 600,
                      color: 'text.primary'
                    }}
                  >
                    {section.title}
                  </Typography>
                )}
                <Typography
                  variant="body1"
                  component="div"
                  sx={{
                    lineHeight: 1.9,
                    fontSize: '1.05rem',
                    textAlign: 'justify',
                    whiteSpace: 'pre-wrap',
                    color: 'text.primary',
                    '& + &': {
                      mt: 2
                    }
                  }}
                >
                  {section.content}
                </Typography>
              </Box>
            ))}
          </Paper>
        ) : (
          // Sections View (Original)
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {text.sections.map((section) => (
              <Card key={section.id} variant="outlined">
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="overline" color="text.secondary">
                      {section.breadcrumb}
                    </Typography>
                    <Chip label={`${section.word_count} words`} size="small" variant="outlined" />
                  </Box>

                  {section.title && (
                    <Typography variant="h6" gutterBottom>
                      {section.title}
                    </Typography>
                  )}

                  <Typography
                    variant="body1"
                    sx={{
                      lineHeight: 1.8,
                      textAlign: 'justify',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {section.content}
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </Box>
        )
      ) : (
        <Alert severity="info">
          This text has no sections loaded yet. Check back later.
        </Alert>
      )}
    </Container>
    </>
  );
}
