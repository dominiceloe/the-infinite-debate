'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { getCategoryInfo } from '@/lib/categories';
import { hasPersonaAccess, getTierBadge } from '@/lib/tiers';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { use, useState } from 'react';
import type { Persona, PrimaryText, ExternalLink } from '@/types';
import Image from 'next/image';
import { Playfair_Display } from 'next/font/google';
import ReactMarkdown from 'react-markdown';
import {
  Container,
  Box,
  Typography,
  Button,
  Chip,
  Card,
  CardContent,
  CircularProgress,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material';
import Header from '@/components/Header';

const playfair = Playfair_Display({ subsets: ['latin'], weight: ['700'] });

export default function PersonaDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const { user } = useAuth();
  const router = useRouter();
  const [imageError, setImageError] = useState(false);
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false);

  // Check if daily limit is reached (trial users only)
  const dailyLimitReached = user?.subscription_tier === 'trial' &&
    user?.debates_created_today !== undefined &&
    user?.daily_debate_limit !== undefined &&
    user.debates_created_today >= user.daily_debate_limit;

  const handleCreateDebate = () => {
    if (dailyLimitReached || (user?.credits_remaining !== undefined && user.credits_remaining <= 0)) {
      setUpgradeModalOpen(true);
    } else {
      router.push('/debates/new');
    }
  };

  const { data: persona, isLoading, error } = useQuery<Persona>({
    queryKey: ['persona', slug],
    queryFn: () => apiClient.personas.getBySlug(slug),
  });

  if (isLoading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Box sx={{ textAlign: 'center' }}>
          <CircularProgress size={48} sx={{ mb: 2 }} />
          <Typography color="text.secondary">Loading persona...</Typography>
        </Box>
      </Box>
    );
  }

  if (error || !persona) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="h4" color="error" gutterBottom>
            Persona Not Found
          </Typography>
          <Button
            onClick={() => router.back()}
            color="primary"
            sx={{ textDecoration: 'underline' }}
          >
            ← Go Back
          </Button>
        </Box>
      </Box>
    );
  }

  const categoryInfo = getCategoryInfo(persona.category);
  const hasAccess = hasPersonaAccess(user?.subscription_tier, persona.required_tier);
  const badge = getTierBadge(persona.required_tier, user?.subscription_tier);

  // Get tier display name
  const getTierDisplayName = (tier?: string) => {
    switch (tier) {
      case 'free':
        return 'Free';
      case 'starter':
        return 'Starter';
      case 'pro':
        return 'Pro';
      case 'enterprise':
        return 'Enterprise';
      default:
        return 'Free';
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(to bottom right, #eef2ff, #ffffff, #faf5ff)',
      }}
    >
      <Header
        backTo="/"
        backLabel="Back to Home"
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: persona.name }
        ]}
      />

      {/* Main Content */}
      <Container maxWidth="lg" sx={{ py: { xs: 6, md: 12 }, px: { xs: 2, md: 3 } }}>
        <Box sx={{ maxWidth: '1024px', mx: 'auto' }}>
          {/* Persona Header */}
          <Card sx={{ mb: 4 }}>
            <CardContent sx={{ p: { xs: 3, md: 4 } }}>
              <Grid container spacing={4} alignItems="center">
                {/* Portrait */}
                <Grid size={{ xs: 12, md: 4 }}>
                  <Box
                    sx={{
                      position: 'relative',
                      width: '100%',
                      paddingTop: '125%', // 4:5 aspect ratio
                      bgcolor: 'grey.100',
                      borderRadius: 2,
                      overflow: 'hidden',
                      border: '2px solid',
                      borderColor: 'grey.200',
                    }}
                  >
                    <Image
                      src={imageError ? '/portraits/default.svg' : `/portraits/${persona.slug}.png`}
                      alt={`Portrait of ${persona.name}`}
                      fill
                      style={{ objectFit: 'cover' }}
                      onError={() => setImageError(true)}
                    />
                  </Box>
                </Grid>

                {/* Info */}
                <Grid size={{ xs: 12, md: 8 }}>
                  <Box sx={{ display: 'flex', alignItems: 'start', justifyContent: 'space-between', mb: 2 }}>
                    <Box>
                      <Typography
                        variant="h1"
                        className={playfair.className}
                        sx={{
                          fontSize: { xs: '2rem', md: '2.5rem' },
                          fontWeight: 700,
                          color: 'text.primary',
                          mb: 1,
                        }}
                      >
                        {persona.name}
                      </Typography>
                      <Typography variant="h6" color="text.secondary" sx={{ fontSize: { xs: '1rem', md: '1.25rem' } }}>
                        {persona.title}
                      </Typography>
                    </Box>
                    <Chip
                      label={categoryInfo.title}
                      sx={{
                        background: categoryInfo.color,
                        color: 'white',
                        fontWeight: 600,
                        textTransform: 'capitalize',
                      }}
                    />
                  </Box>

                  <Grid container spacing={2} sx={{ mt: 2 }}>
                    <Grid size={{ xs: 12, sm: 6 }}>
                      <Typography variant="body2">
                        <Typography component="span" sx={{ fontWeight: 600, color: 'text.primary' }}>
                          Era:
                        </Typography>{' '}
                        <Typography component="span" color="text.secondary">
                          {persona.era}
                        </Typography>
                      </Typography>
                    </Grid>
                    {persona.religion_worldview && (
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <Typography variant="body2">
                          <Typography component="span" sx={{ fontWeight: 600, color: 'text.primary' }}>
                            Worldview:
                          </Typography>{' '}
                          <Typography component="span" color="text.secondary">
                            {persona.religion_worldview}
                          </Typography>
                        </Typography>
                      </Grid>
                    )}
                    <Grid size={{ xs: 12, sm: 6 }}>
                      <Typography variant="body2">
                        <Typography component="span" sx={{ fontWeight: 600, color: 'text.primary' }}>
                          Total Debates:
                        </Typography>{' '}
                        <Typography component="span" color="text.secondary">
                          {persona.debate_count !== undefined ? persona.debate_count : 0}
                        </Typography>
                      </Typography>
                    </Grid>
                  </Grid>

                  {/* Primary Texts from Database */}
                  {persona.primary_texts && persona.primary_texts.length > 0 && (
                    <Box sx={{ mt: 3 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary', mb: 1 }}>
                        Primary Texts ({persona.primary_texts.length}):
                      </Typography>
                      <Box component="ul" sx={{ listStyleType: 'none', pl: 0, m: 0 }}>
                        {persona.primary_texts.map((text: PrimaryText) => (
                          <Typography component="li" key={text.id} variant="body2" sx={{ mb: 0.75 }}>
                            <Link
                              href={`/texts/${text.slug}`}
                              style={{
                                color: '#1976d2',
                                textDecoration: 'none',
                                borderBottom: '1px dotted #1976d2',
                              }}
                            >
                              {text.title}
                            </Link>
                            {text.word_count && (
                              <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                                ({(text.word_count / 1000).toFixed(0)}k words)
                              </Typography>
                            )}
                          </Typography>
                        ))}
                      </Box>
                    </Box>
                  )}
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Tier Availability */}
          <Card sx={{ mb: 4, border: 2, borderColor: hasAccess ? 'success.light' : 'warning.light' }}>
            <CardContent sx={{ p: { xs: 3, md: 4 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                    {hasAccess ? '✓ Available to Use' : '🔒 Requires Upgrade'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {persona.required_tier === 'free' ? (
                      'This persona is available to all users for free.'
                    ) : hasAccess ? (
                      `You can use ${persona.name} in debates with your ${getTierDisplayName(user?.subscription_tier)} subscription.`
                    ) : (
                      `This persona requires the ${getTierDisplayName(persona.required_tier)} plan or higher.`
                    )}
                  </Typography>
                </Box>
                {badge && (
                  <Chip
                    label={`${badge.label} Plan`}
                    sx={{
                      bgcolor: badge.color,
                      color: 'white',
                      fontWeight: 600,
                      fontSize: '0.875rem',
                      height: 32,
                    }}
                  />
                )}
              </Box>
              {!hasAccess && persona.required_tier !== 'free' && (
                <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                  <Typography variant="body2" sx={{ mb: 1.5 }}>
                    <strong>Upgrade to {getTierDisplayName(persona.required_tier)}</strong> to unlock {persona.name} and {
                      persona.required_tier === 'starter' ? '34 total personas' :
                      persona.required_tier === 'pro' ? '58 total personas' :
                      'all 89 personas'
                    }.
                  </Typography>
                  <Button
                    component={Link}
                    href="/pricing"
                    variant="contained"
                    size="small"
                    sx={{
                      bgcolor: badge?.color,
                      '&:hover': {
                        bgcolor: badge?.color,
                        opacity: 0.9,
                      },
                    }}
                  >
                    Upgrade to {getTierDisplayName(persona.required_tier)}
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>

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

          {/* Further Reading / External Links */}
          {persona.external_links && (
            Object.keys(persona.external_links).some(key =>
              key === 'wikipedia' || key === 'stanford_encyclopedia'
                ? persona.external_links![key as keyof typeof persona.external_links]
                : (persona.external_links![key as keyof typeof persona.external_links] as ExternalLink[])?.length > 0
            ) && (
              <Card sx={{ mb: 3 }}>
                <CardContent sx={{ p: { xs: 3, md: 4 } }}>
                  <Typography
                    variant="h5"
                    sx={{
                      fontWeight: 700,
                      color: 'text.primary',
                      mb: 3,
                      fontSize: { xs: '1.25rem', md: '1.5rem' },
                    }}
                  >
                    Further Reading
                  </Typography>

                  <Grid container spacing={3}>
                    {/* Primary Works */}
                    {persona.external_links.primary_works && persona.external_links.primary_works.length > 0 && (
                      <Grid size={{ xs: 12, md: 6 }}>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 1.5, display: 'flex', alignItems: 'center', gap: 1 }}>
                          📚 Primary Works
                        </Typography>
                        <Box component="ul" sx={{ listStyle: 'none', pl: 0, m: 0 }}>
                          {persona.external_links.primary_works.map((link, i) => (
                            <Typography component="li" key={i} sx={{ mb: 1 }}>
                              <Box
                                component="a"
                                href={link.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                sx={{
                                  color: 'primary.main',
                                  textDecoration: 'none',
                                  '&:hover': { textDecoration: 'underline' },
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: 0.5,
                                }}
                              >
                                {link.title}
                                <Box component="span" sx={{ fontSize: '0.75rem' }}>↗</Box>
                              </Box>
                            </Typography>
                          ))}
                        </Box>
                      </Grid>
                    )}

                    {/* Academic Resources */}
                    {persona.external_links.academic && persona.external_links.academic.length > 0 && (
                      <Grid size={{ xs: 12, md: 6 }}>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 1.5, display: 'flex', alignItems: 'center', gap: 1 }}>
                          🎓 Academic Resources
                        </Typography>
                        <Box component="ul" sx={{ listStyle: 'none', pl: 0, m: 0 }}>
                          {persona.external_links.academic.map((link, i) => (
                            <Typography component="li" key={i} sx={{ mb: 1 }}>
                              <Box
                                component="a"
                                href={link.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                sx={{
                                  color: 'primary.main',
                                  textDecoration: 'none',
                                  '&:hover': { textDecoration: 'underline' },
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: 0.5,
                                }}
                              >
                                {link.title}
                                <Box component="span" sx={{ fontSize: '0.75rem' }}>↗</Box>
                              </Box>
                            </Typography>
                          ))}
                        </Box>
                      </Grid>
                    )}

                    {/* Wikipedia */}
                    {persona.external_links.wikipedia && (
                      <Grid size={{ xs: 12, md: 6 }}>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 1.5, display: 'flex', alignItems: 'center', gap: 1 }}>
                          📖 Wikipedia
                        </Typography>
                        <Box
                          component="a"
                          href={persona.external_links.wikipedia}
                          target="_blank"
                          rel="noopener noreferrer"
                          sx={{
                            color: 'primary.main',
                            textDecoration: 'none',
                            '&:hover': { textDecoration: 'underline' },
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 0.5,
                          }}
                        >
                          {persona.name} on Wikipedia
                          <Box component="span" sx={{ fontSize: '0.75rem' }}>↗</Box>
                        </Box>
                      </Grid>
                    )}

                    {/* Stanford Encyclopedia */}
                    {persona.external_links.stanford_encyclopedia && (
                      <Grid size={{ xs: 12, md: 6 }}>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 1.5, display: 'flex', alignItems: 'center', gap: 1 }}>
                          🏛️ Stanford Encyclopedia
                        </Typography>
                        <Box
                          component="a"
                          href={persona.external_links.stanford_encyclopedia}
                          target="_blank"
                          rel="noopener noreferrer"
                          sx={{
                            color: 'primary.main',
                            textDecoration: 'none',
                            '&:hover': { textDecoration: 'underline' },
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 0.5,
                          }}
                        >
                          {persona.name} at Stanford Encyclopedia of Philosophy
                          <Box component="span" sx={{ fontSize: '0.75rem' }}>↗</Box>
                        </Box>
                      </Grid>
                    )}

                    {/* Modern Resources */}
                    {persona.external_links.modern && persona.external_links.modern.length > 0 && (
                      <Grid size={{ xs: 12 }}>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 1.5, display: 'flex', alignItems: 'center', gap: 1 }}>
                          🎥 Modern Resources
                        </Typography>
                        <Box component="ul" sx={{ listStyle: 'none', pl: 0, m: 0 }}>
                          {persona.external_links.modern.map((link, i) => (
                            <Typography component="li" key={i} sx={{ mb: 1, display: 'inline-block', mr: 3 }}>
                              <Box
                                component="a"
                                href={link.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                sx={{
                                  color: 'primary.main',
                                  textDecoration: 'none',
                                  '&:hover': { textDecoration: 'underline' },
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: 0.5,
                                }}
                              >
                                {link.title}
                                <Box component="span" sx={{ fontSize: '0.75rem' }}>↗</Box>
                              </Box>
                            </Typography>
                          ))}
                        </Box>
                      </Grid>
                    )}
                  </Grid>
                </CardContent>
              </Card>
            )
          )}

          {/* CTA */}
          {hasAccess ? (
            <Box
              sx={{
                background: 'linear-gradient(to right, #4f46e5, #9333ea)',
                borderRadius: 2,
                p: { xs: 4, md: 5 },
                textAlign: 'center',
                mt: 4,
              }}
            >
              <Typography
                variant="h4"
                sx={{
                  color: 'white',
                  fontWeight: 700,
                  mb: 3,
                  fontSize: { xs: '1.5rem', md: '2rem' },
                }}
              >
                Want to see {persona.name} in a debate?
              </Typography>
              <Button
                onClick={handleCreateDebate}
                variant="contained"
                sx={{
                  bgcolor: 'white',
                  color: 'primary.main',
                  px: 4,
                  py: 1.5,
                  fontWeight: 600,
                  '&:hover': {
                    bgcolor: 'grey.100',
                  },
                }}
              >
                Create a Debate
              </Button>
            </Box>
          ) : (
            <Box
              sx={{
                background: `linear-gradient(to right, ${badge?.color || '#9333ea'}, ${badge?.color || '#7e22ce'})`,
                borderRadius: 2,
                p: { xs: 4, md: 5 },
                textAlign: 'center',
                mt: 4,
              }}
            >
              <Typography
                variant="h4"
                sx={{
                  color: 'white',
                  fontWeight: 700,
                  mb: 2,
                  fontSize: { xs: '1.5rem', md: '2rem' },
                }}
              >
                Unlock {persona.name}
              </Typography>
              <Typography
                sx={{
                  color: 'rgba(255, 255, 255, 0.9)',
                  mb: 3,
                  fontSize: { xs: '0.875rem', md: '1rem' },
                }}
              >
                Upgrade to {getTierDisplayName(persona.required_tier)} to use {persona.name} in debates
              </Typography>
              <Button
                component={Link}
                href="/pricing"
                variant="contained"
                sx={{
                  bgcolor: 'white',
                  color: badge?.color || 'primary.main',
                  px: 4,
                  py: 1.5,
                  fontWeight: 600,
                  '&:hover': {
                    bgcolor: 'grey.100',
                  },
                }}
              >
                View Pricing
              </Button>
            </Box>
          )}
        </Box>
      </Container>

      {/* Upgrade Modal - shown when user has 0 credits or daily limit reached */}
      <Dialog
        open={upgradeModalOpen}
        onClose={() => setUpgradeModalOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 600 }}>
          {dailyLimitReached ? 'Daily limit reached' : 'You\'re out of credits'}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            {dailyLimitReached ? (
              <>
                You&apos;ve reached your daily debate limit ({user?.debates_created_today}/{user?.daily_debate_limit}).
                Trial users can create {user?.daily_debate_limit} debates per day. Your limit resets at midnight UTC,
                or upgrade to <strong>Starter</strong> for unlimited debates.
              </>
            ) : user?.subscription_tier === 'trial' ? (
              <>
                Your free trial credits have been used. Upgrade to <strong>Starter</strong> for
                30 credits per month and unlimited debates per day.
              </>
            ) : user?.subscription_tier === 'starter' ? (
              <>
                You&apos;ve used all your credits for this month. Your credits will reset on{' '}
                <strong>{user?.credits_reset_date || 'the 1st of next month'}</strong>, or you can
                upgrade to <strong>Pro</strong> for more credits.
              </>
            ) : (
              <>
                You&apos;ve used all your credits. Please wait for your monthly reset or contact
                support for additional credits.
              </>
            )}
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setUpgradeModalOpen(false)} color="inherit">
            Cancel
          </Button>
          <Button
            component={Link}
            href="/pricing"
            variant="contained"
            onClick={() => setUpgradeModalOpen(false)}
          >
            View Plans
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

function ContentSection({ title, content }: { title: string; content: string }) {
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent sx={{ p: { xs: 3, md: 4 } }}>
        <Typography
          variant="h5"
          sx={{
            fontWeight: 700,
            color: 'text.primary',
            mb: 2,
            fontSize: { xs: '1.25rem', md: '1.5rem' },
          }}
        >
          {title}
        </Typography>
        <ReactMarkdown
          components={{
            h1: ({ children }) => (
              <Typography variant="h3" sx={{ fontWeight: 700, mb: 2, mt: 3 }}>
                {children}
              </Typography>
            ),
            h2: ({ children }) => (
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 2, mt: 3 }}>
                {children}
              </Typography>
            ),
            h3: ({ children }) => (
              <Typography
                variant="h5"
                sx={{
                  fontWeight: 600,
                  color: 'primary.main',
                  mt: 2,
                  mb: 1.5,
                }}
              >
                {children}
              </Typography>
            ),
            p: ({ children }) => (
              <Typography
                sx={{
                  color: 'text.primary',
                  mb: 2,
                  lineHeight: 1.7,
                }}
              >
                {children}
              </Typography>
            ),
            ul: ({ children }) => (
              <Box
                component="ul"
                sx={{
                  pl: 3,
                  mb: 2,
                  color: 'text.primary',
                  listStyleType: 'disc',
                }}
              >
                {children}
              </Box>
            ),
            li: ({ children }) => (
              <Typography component="li" sx={{ mb: 0.5, lineHeight: 1.7 }}>
                {children}
              </Typography>
            ),
            strong: ({ children }) => (
              <Typography component="strong" sx={{ fontWeight: 700 }}>
                {children}
              </Typography>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </CardContent>
    </Card>
  );
}
