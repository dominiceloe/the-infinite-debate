'use client';

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import type { Debate, PaginatedResponse } from '@/types';
import {
  Container,
  Box,
  Typography,
  Button,
  Card,
  CardActionArea,
  CircularProgress,
  Chip,
  Alert,
  AlertTitle,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import Header from '@/components/Header';

type SortBy = 'date-desc' | 'date-asc' | 'participants-desc' | 'participants-asc';
type StatusFilter = 'all' | 'pending' | 'generating' | 'completed' | 'failed';
type SizeFilter = 'all' | 'small' | 'medium' | 'large' | 'xl';

export default function DebatesListPage() {
  const { user } = useAuth();
  const router = useRouter();
  const { data, isLoading, error } = useQuery<PaginatedResponse<Debate>>({
    queryKey: ['debates'],
    queryFn: () => apiClient.debates.list(),
  });

  // Filter and sort state
  const [sortBy, setSortBy] = useState<SortBy>('date-desc');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [sizeFilter, setSizeFilter] = useState<SizeFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');
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

  // Filter and sort debates
  const filteredDebates = useMemo(() => {
    if (!data?.results) return [];

    let filtered = [...data.results];

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter((debate) => debate.status === statusFilter);
    }

    // Apply size filter
    if (sizeFilter !== 'all') {
      filtered = filtered.filter((debate) => {
        const count = debate.participant_count || 0;
        switch (sizeFilter) {
          case 'small':
            return count >= 2 && count <= 3;
          case 'medium':
            return count >= 4 && count <= 6;
          case 'large':
            return count >= 7 && count <= 10;
          case 'xl':
            return count >= 11 && count <= 15;
          default:
            return true;
        }
      });
    }

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      filtered = filtered.filter((debate) => {
        const titleMatch = debate.title.toLowerCase().includes(query);
        const topicMatch = debate.topic?.toLowerCase().includes(query);
        const participantMatch = debate.participant_names?.toLowerCase().includes(query);
        return titleMatch || topicMatch || participantMatch;
      });
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'date-desc':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'date-asc':
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        case 'participants-desc':
          return (b.participant_count || 0) - (a.participant_count || 0);
        case 'participants-asc':
          return (a.participant_count || 0) - (b.participant_count || 0);
        default:
          return 0;
      }
    });

    return filtered;
  }, [data?.results, sortBy, statusFilter, sizeFilter, searchQuery]);

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(to bottom right, #eef2ff, #ffffff, #faf5ff)',
      }}
    >
      <Header />

      {/* Main Content */}
      <Container maxWidth="lg" sx={{ py: { xs: 4, md: 6 } }}>
        <Box sx={{ maxWidth: '1152px', mx: 'auto' }}>
          <Box sx={{ mb: 4 }}>
            <Typography variant="h1" sx={{ fontWeight: 700, color: 'text.primary', mb: 1 }}>
              All Debates
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Browse and view debates between historical thinkers.
            </Typography>
          </Box>

          {/* Filter and Sort Bar */}
          {!isLoading && !error && data?.results && data.results.length > 0 && (
            <Card sx={{ p: 3, mb: 4 }}>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '2fr 1fr 1fr 1fr' },
                  gap: 2,
                }}
              >
                {/* Search */}
                <TextField
                  placeholder="Search debates, topics, or participants..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  size="small"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon sx={{ color: 'text.secondary' }} />
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      bgcolor: 'background.paper',
                    },
                  }}
                />

                {/* Sort By */}
                <FormControl size="small">
                  <InputLabel>Sort By</InputLabel>
                  <Select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as SortBy)}
                    label="Sort By"
                    sx={{ bgcolor: 'background.paper' }}
                  >
                    <MenuItem value="date-desc">Newest First</MenuItem>
                    <MenuItem value="date-asc">Oldest First</MenuItem>
                    <MenuItem value="participants-desc">Most Participants</MenuItem>
                    <MenuItem value="participants-asc">Least Participants</MenuItem>
                  </Select>
                </FormControl>

                {/* Status Filter */}
                <FormControl size="small">
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                    label="Status"
                    sx={{ bgcolor: 'background.paper' }}
                  >
                    <MenuItem value="all">All Status</MenuItem>
                    <MenuItem value="pending">Pending</MenuItem>
                    <MenuItem value="generating">Generating</MenuItem>
                    <MenuItem value="completed">Completed</MenuItem>
                    <MenuItem value="failed">Failed</MenuItem>
                  </Select>
                </FormControl>

                {/* Size Filter */}
                <FormControl size="small">
                  <InputLabel>Size</InputLabel>
                  <Select
                    value={sizeFilter}
                    onChange={(e) => setSizeFilter(e.target.value as SizeFilter)}
                    label="Size"
                    sx={{ bgcolor: 'background.paper' }}
                  >
                    <MenuItem value="all">All Sizes</MenuItem>
                    <MenuItem value="small">Small (2-3)</MenuItem>
                    <MenuItem value="medium">Medium (4-6)</MenuItem>
                    <MenuItem value="large">Large (7-10)</MenuItem>
                    <MenuItem value="xl">XL (11-15)</MenuItem>
                  </Select>
                </FormControl>
              </Box>

              {/* Results Counter */}
              <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
                <Typography variant="body2" color="text.secondary">
                  Showing {filteredDebates.length} of {data.results.length} debate{data.results.length !== 1 ? 's' : ''}
                  {(statusFilter !== 'all' || sizeFilter !== 'all' || searchQuery.trim()) && (
                    <Button
                      size="small"
                      onClick={() => {
                        setStatusFilter('all');
                        setSizeFilter('all');
                        setSearchQuery('');
                      }}
                      sx={{ ml: 2, textTransform: 'none' }}
                    >
                      Clear Filters
                    </Button>
                  )}
                </Typography>
              </Box>
            </Card>
          )}

          {isLoading ? (
            <Box sx={{ textAlign: 'center', py: 10 }}>
              <CircularProgress size={48} sx={{ mb: 2 }} />
              <Typography color="text.secondary">Loading debates...</Typography>
            </Box>
          ) : error ? (
            <Alert severity="error" sx={{ borderRadius: 2 }}>
              <AlertTitle sx={{ fontWeight: 600 }}>Error Loading Debates</AlertTitle>
              {error.message}
            </Alert>
          ) : !data?.results || data.results.length === 0 ? (
            <Card sx={{ p: 6, textAlign: 'center' }}>
              <Typography color="text.secondary" sx={{ mb: 2 }}>
                No debates yet. Create your first one!
              </Typography>
              <Button
                onClick={handleCreateDebate}
                variant="contained"
                sx={{ px: 4, py: 2, fontWeight: 500 }}
              >
                Create Debate
              </Button>
            </Card>
          ) : filteredDebates.length === 0 ? (
            <Card sx={{ p: 6, textAlign: 'center' }}>
              <Typography color="text.secondary" sx={{ mb: 2 }}>
                No debates match your filters.
              </Typography>
              <Button
                onClick={() => {
                  setStatusFilter('all');
                  setSizeFilter('all');
                  setSearchQuery('');
                }}
                variant="outlined"
                sx={{ px: 4, py: 2, fontWeight: 500 }}
              >
                Clear All Filters
              </Button>
            </Card>
          ) : (
            <>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {filteredDebates.map((debate) => (
                  <DebateCard key={debate.id} debate={debate} />
                ))}
              </Box>

              {/* Pagination */}
              {(data.next || data.previous) && (
                <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 4 }}>
                  {data.previous && (
                    <Button
                      variant="outlined"
                      sx={{
                        px: 3,
                        py: 1.5,
                        color: 'text.secondary',
                        borderColor: 'divider',
                        '&:hover': {
                          bgcolor: 'grey.50',
                          borderColor: 'divider',
                        },
                      }}
                    >
                      Previous
                    </Button>
                  )}
                  {data.next && (
                    <Button
                      variant="outlined"
                      sx={{
                        px: 3,
                        py: 1.5,
                        color: 'text.secondary',
                        borderColor: 'divider',
                        '&:hover': {
                          bgcolor: 'grey.50',
                          borderColor: 'divider',
                        },
                      }}
                    >
                      Next
                    </Button>
                  )}
                </Box>
              )}
            </>
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

function DebateCard({ debate }: { debate: Debate }) {
  const statusColors = {
    pending: { bgcolor: '#f3f4f6', color: '#374151' },
    generating: { bgcolor: '#dbeafe', color: '#1e40af' },
    completed: { bgcolor: '#dcfce7', color: '#166534' },
    failed: { bgcolor: '#fee2e2', color: '#991b1b' },
  };

  const statusColor = statusColors[debate.status as keyof typeof statusColors] || statusColors.pending;

  return (
    <Card
      sx={{
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          borderColor: '#c7d2fe',
          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
        },
      }}
    >
      <CardActionArea component={Link} href={`/debates/${debate.slug}`} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 1.5 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h5" sx={{ fontWeight: 700, color: 'text.primary', mb: 0.5 }}>
              {debate.title}
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
              }}
            >
              {debate.topic}
            </Typography>
          </Box>
          <Chip
            label={debate.status}
            size="small"
            sx={{
              ml: 2,
              bgcolor: statusColor.bgcolor,
              color: statusColor.color,
              fontWeight: 500,
              fontSize: '0.875rem',
              whiteSpace: 'nowrap',
            }}
          />
        </Box>

        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, fontSize: '0.875rem', color: 'text.secondary' }}>
          <Box>
            <Typography component="span" sx={{ fontWeight: 500 }}>Participants:</Typography>{' '}
            {debate.participant_names || `${debate.participant_count} thinkers`}
          </Box>
          <Box>
            <Typography component="span" sx={{ fontWeight: 500 }}>Rounds:</Typography>{' '}
            {debate.rounds_completed}/{debate.max_rounds}
          </Box>
          <Box>
            <Typography component="span" sx={{ fontWeight: 500 }}>Created:</Typography>{' '}
            {new Date(debate.created_at).toLocaleDateString()}
          </Box>
        </Box>
      </CardActionArea>
    </Card>
  );
}
