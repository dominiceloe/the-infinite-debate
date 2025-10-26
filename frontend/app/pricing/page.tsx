'use client';

import {
  Container,
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ToggleButton,
  ToggleButtonGroup,
  CircularProgress,
  Snackbar,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
} from '@mui/material';
import Link from 'next/link';
import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import Header from '@/components/Header';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { Playfair_Display } from 'next/font/google';
import { AxiosError } from 'axios';

const playfair = Playfair_Display({ subsets: ['latin'], weight: ['700'] });

type BillingPeriod = 'monthly' | 'yearly';

interface PricingTierTemplate {
  name: string;
  description: string;
  monthlyPrice: number;
  annualPrice: number;
  color: string;
  tier: 'free' | 'starter' | 'pro' | 'enterprise';
  credits: number;
  featuresTemplate: (count: number) => string[];
  badge?: string;
  popular?: boolean;
}

const pricingTierTemplates: PricingTierTemplate[] = [
  {
    name: 'Free',
    description: 'Start your philosophical journey',
    monthlyPrice: 0,
    annualPrice: 0,
    color: '#6366f1',
    tier: 'free',
    credits: 15,
    badge: undefined,
    featuresTemplate: (count) => [
      `${count} iconic personas (Socrates, Plato, Einstein, etc.)`,
      '15 debate credits',
      'No credit card required',
      'Perfect for trying out the platform',
      'Upgrade anytime to unlock more',
    ],
  },
  {
    name: 'Starter',
    description: 'Perfect for casual philosophers',
    monthlyPrice: 7.99,
    annualPrice: 79,
    color: '#10b981',
    tier: 'starter',
    credits: 30,
    badge: 'Starter',
    featuresTemplate: (count) => [
      `${count} well-known thinkers`,
      '30 debate credits per month',
      'All free personas included',
      'Popular philosophers like Kant, Marx, Sartre',
      'Famous scientists like Galileo, Curie, Tesla',
      'Key theologians like Maimonides, Al-Ghazali',
    ],
  },
  {
    name: 'Pro',
    description: 'For serious intellectual exploration',
    monthlyPrice: 19.99,
    annualPrice: 179,
    color: '#6366f1',
    tier: 'pro',
    credits: 100,
    badge: 'Pro',
    popular: true,
    featuresTemplate: (count) => [
      `${count} diverse thinkers across all categories`,
      '100 debate credits per month',
      'All Starter personas included',
      'Deeper catalog: Kierkegaard, Jung, Beauvoir',
      'Additional theologians, mystics, and scientists',
      'Political theorists like Arendt, Burke, Machiavelli',
    ],
  },
  {
    name: 'Enterprise',
    description: 'Complete access for institutions',
    monthlyPrice: 0,
    annualPrice: 0,
    color: '#8b5cf6',
    tier: 'enterprise',
    credits: 0,
    badge: 'Enterprise',
    featuresTemplate: (count) => [
      `All ${count} personas unlocked`,
      'Custom credit allocation',
      'Environmental thinkers: Carson, Thoreau, Shiva',
      'Artists: Picasso, van Gogh, Kahlo, Kandinsky',
      'Social reformers: Gandhi, Mandela, Malcolm X',
      'Complete collection across 12 categories',
      'Custom pricing for institutions',
    ],
  },
];

export default function PricingPage() {
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>('monthly');
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
    open: false,
    message: '',
    severity: 'info',
  });
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean;
    tier: 'starter' | 'pro' | null;
  }>({
    open: false,
    tier: null,
  });

  // Fetch user's current subscription
  const { data: subscriptionData } = useQuery({
    queryKey: ['subscription'],
    queryFn: () => apiClient.payments.getSubscription(),
    retry: false,
  });

  // Fetch all personas to count by tier
  const { data: personasData, isLoading } = useQuery({
    queryKey: ['personas', 'by_category'],
    queryFn: () => apiClient.personas.getByCategory(),
  });

  // Count personas by tier (cumulative access model)
  const tierCounts = useMemo(() => {
    if (!personasData) return { free: 0, starter: 0, pro: 0, enterprise: 0 };

    const allPersonas = Object.values(personasData).flat();
    const counts = {
      free: 0,
      starter: 0,
      pro: 0,
      enterprise: 0,
    };

    allPersonas.forEach((persona) => {
      const tier = persona.required_tier || 'free';
      if (tier === 'free') counts.free++;
      if (tier === 'starter') counts.starter++;
      if (tier === 'pro') counts.pro++;
      if (tier === 'enterprise') counts.enterprise++;
    });

    // Calculate cumulative counts (each tier includes all lower tiers)
    return {
      free: counts.free,
      starter: counts.free + counts.starter,
      pro: counts.free + counts.starter + counts.pro,
      enterprise: counts.free + counts.starter + counts.pro + counts.enterprise,
    };
  }, [personasData]);

  const handleBillingChange = (_: React.MouseEvent<HTMLElement>, newValue: BillingPeriod | null) => {
    if (newValue !== null) {
      setBillingPeriod(newValue);
    }
  };

  const handleCheckout = (tier: 'starter' | 'pro') => {
    // If user has an existing subscription, show confirmation dialog
    if (subscriptionData && subscriptionData.tier && subscriptionData.tier !== 'trial') {
      setConfirmDialog({ open: true, tier });
    } else {
      // New subscription - proceed directly
      confirmCheckout(tier);
    }
  };

  const confirmCheckout = async (tier: 'starter' | 'pro') => {
    setConfirmDialog({ open: false, tier: null });
    setCheckoutLoading(tier);
    try {
      const response = await apiClient.payments.createCheckout({
        tier,
        billing_period: billingPeriod,  // NEW: pass current billing period selection
        success_url: `${window.location.origin}/account?payment=success`,
        cancel_url: `${window.location.origin}/pricing?payment=cancelled`,
      });

      // Check if this was an upgrade (no redirect needed)
      if (response.is_upgrade) {
        setSnackbar({
          open: true,
          message: `Subscription updated successfully! You're now on the ${tier} plan.`,
          severity: 'success',
        });
        // Redirect to account page after brief delay
        setTimeout(() => {
          window.location.href = '/account?payment=upgraded';
        }, 1500);
      } else if (response.checkout_url) {
        // New subscription - redirect to Stripe Checkout
        window.location.href = response.checkout_url;
      }
    } catch (error) {
      const axiosError = error as AxiosError<{ error?: string }>;
      console.error('Checkout error:', error);
      setSnackbar({
        open: true,
        message: axiosError.response?.data?.error || 'Failed to create checkout session. Please try again.',
        severity: 'error',
      });
      setCheckoutLoading(null);
    }
  };

  const handleCloseDialog = () => {
    setConfirmDialog({ open: false, tier: null });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const currentTier = subscriptionData?.tier || 'trial';

  // Get tier details for confirmation dialog
  const getTierDetails = (tier: 'starter' | 'pro') => {
    const tierTemplate = pricingTierTemplates.find(t => t.tier === tier);
    return tierTemplate || null;
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(to bottom right, #eef2ff, #ffffff, #faf5ff)',
      }}
    >
      <Header backTo="/" backLabel="Back to Home" />

      {/* Main Content */}
      <Container maxWidth="lg" sx={{ py: { xs: 6, md: 8 }, px: { xs: 2, md: 3 } }}>
        {/* Header Section */}
        <Box sx={{ textAlign: 'center', mb: 6 }}>
          <Typography
            variant="h1"
            className={playfair.className}
            sx={{
              fontSize: { xs: '2.5rem', md: '3.5rem' },
              fontWeight: 700,
              mb: 2,
              background: 'linear-gradient(to right, #4f46e5, #9333ea)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Choose Your Plan
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}>
            Unlock conversations with history&apos;s greatest minds. Start with a free trial and upgrade anytime.
          </Typography>

          {/* Billing Toggle */}
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2, mb: 2 }}>
            <ToggleButtonGroup
              value={billingPeriod}
              exclusive
              onChange={handleBillingChange}
              sx={{
                bgcolor: 'white',
                '& .MuiToggleButton-root': {
                  px: 3,
                  py: 1,
                  border: 'none',
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
              <ToggleButton value="monthly">Monthly</ToggleButton>
              <ToggleButton value="yearly">Annual</ToggleButton>
            </ToggleButtonGroup>
            {billingPeriod === 'yearly' && (
              <Chip
                label="Save up to 25%"
                color="success"
                size="small"
                sx={{ fontWeight: 600 }}
              />
            )}
          </Box>
        </Box>

        {/* Loading State */}
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
            <CircularProgress size={48} />
          </Box>
        ) : (
          <>
            {/* Pricing Cards */}
            <Grid container spacing={3} sx={{ mb: 6, justifyContent: 'center' }}>
              {pricingTierTemplates.map((tierTemplate) => {
                const personaCount = tierCounts[tierTemplate.tier];
                const features = tierTemplate.featuresTemplate(personaCount);

                return (
                  <Grid item xs={12} sm={6} md={6} lg={3} key={tierTemplate.name}>
                    <Card
                      sx={{
                        height: '100%',
                        minHeight: 650,
                        display: 'flex',
                        flexDirection: 'column',
                        position: 'relative',
                        border: tierTemplate.popular ? '3px solid' : '1px solid',
                        borderColor: tierTemplate.popular ? tierTemplate.color : 'divider',
                        transition: 'transform 0.2s, box-shadow 0.2s',
                        '&:hover': {
                          transform: 'translateY(-4px)',
                          boxShadow: 4,
                        },
                      }}
                    >
                      {tierTemplate.popular && (
                        <Box
                          sx={{
                            position: 'absolute',
                            top: 20,
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            zIndex: 1,
                          }}
                        >
                          <Chip
                            label="Most Popular"
                            sx={{
                              bgcolor: tierTemplate.color,
                              color: 'white',
                              fontWeight: 600,
                              px: 2,
                              boxShadow: 2,
                            }}
                          />
                        </Box>
                      )}

                      <CardContent sx={{ flexGrow: 1, p: 3, display: 'flex', flexDirection: 'column' }}>
                        {/* Tier Name */}
                        <Box sx={{ mb: 3 }}>
                          {tierTemplate.badge && (
                            <Chip
                              label={tierTemplate.badge}
                              size="small"
                              sx={{
                                bgcolor: tierTemplate.color,
                                color: 'white',
                                fontWeight: 600,
                                mb: 1,
                              }}
                            />
                          )}
                          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                            {tierTemplate.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {tierTemplate.description}
                          </Typography>
                        </Box>

                        {/* Pricing */}
                        <Box sx={{ mb: 3 }}>
                          {tierTemplate.name === 'Enterprise' ? (
                            <Typography variant="h3" sx={{ fontWeight: 700 }}>
                              Custom
                            </Typography>
                          ) : tierTemplate.name === 'Trial' ? (
                            <Typography variant="h3" sx={{ fontWeight: 700 }}>
                              Free
                            </Typography>
                          ) : (
                            <>
                              <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.5 }}>
                                <Typography variant="h3" sx={{ fontWeight: 700 }}>
                                  ${billingPeriod === 'monthly' ? tierTemplate.monthlyPrice : tierTemplate.annualPrice}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  /{billingPeriod === 'monthly' ? 'month' : 'year'}
                                </Typography>
                              </Box>
                              {billingPeriod === 'yearly' && (
                                <Typography variant="caption" color="text.secondary">
                                  ${(tierTemplate.annualPrice / 12).toFixed(2)}/month billed annually
                                </Typography>
                              )}
                            </>
                          )}
                        </Box>

                        {/* Key Stats */}
                        <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2" fontWeight={600}>
                              Personas:
                            </Typography>
                            <Typography variant="body2" color="primary.main" fontWeight={700}>
                              {personaCount}
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Typography variant="body2" fontWeight={600}>
                              Credits:
                            </Typography>
                            <Typography variant="body2" color="primary.main" fontWeight={700}>
                              {tierTemplate.name === 'Enterprise' ? 'Custom' : `${tierTemplate.credits}/mo`}
                            </Typography>
                          </Box>
                        </Box>

                        {/* Features */}
                        <List dense sx={{ mb: 2, flexGrow: 1, minHeight: 240 }}>
                          {features.map((feature, idx) => (
                            <ListItem key={idx} disablePadding sx={{ mb: 0.5 }}>
                              <ListItemIcon sx={{ minWidth: 32 }}>
                                <CheckCircleIcon sx={{ fontSize: 18, color: tierTemplate.color }} />
                              </ListItemIcon>
                              <ListItemText
                                primary={feature}
                                primaryTypographyProps={{
                                  variant: 'body2',
                                  sx: { lineHeight: 1.4 },
                                }}
                              />
                            </ListItem>
                          ))}
                        </List>

                        {/* CTA Button */}
                        <Button
                          fullWidth
                          variant={tierTemplate.popular ? 'contained' : 'outlined'}
                          size="large"
                          disabled={
                            tierTemplate.name === 'Trial' ||
                            tierTemplate.name === 'Enterprise' ||
                            checkoutLoading !== null ||
                            currentTier === tierTemplate.tier
                          }
                          onClick={() => {
                            if (tierTemplate.tier === 'starter' || tierTemplate.tier === 'pro') {
                              handleCheckout(tierTemplate.tier);
                            }
                          }}
                          sx={{
                            mt: 'auto',
                            bgcolor: tierTemplate.popular ? tierTemplate.color : 'transparent',
                            borderColor: tierTemplate.color,
                            color: tierTemplate.popular ? 'white' : tierTemplate.color,
                            fontWeight: 600,
                            '&:hover': {
                              bgcolor: tierTemplate.popular ? tierTemplate.color : 'transparent',
                              opacity: 0.9,
                              borderColor: tierTemplate.color,
                            },
                            '&.Mui-disabled': {
                              bgcolor: 'grey.200',
                              color: 'text.disabled',
                              borderColor: 'grey.300',
                            },
                          }}
                        >
                          {checkoutLoading === tierTemplate.tier ? (
                            <CircularProgress size={24} sx={{ color: 'inherit' }} />
                          ) : currentTier === tierTemplate.tier ? (
                            'Current Plan'
                          ) : tierTemplate.name === 'Trial' ? (
                            'Start Free Trial'
                          ) : tierTemplate.name === 'Enterprise' ? (
                            'Contact Sales'
                          ) : (
                            `Subscribe for $${billingPeriod === 'monthly' ? tierTemplate.monthlyPrice : tierTemplate.annualPrice}`
                          )}
                        </Button>
                      </CardContent>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>

            {/* Credit Pricing Info */}
            <Box sx={{ mb: 6 }}>
              <Typography variant="h5" sx={{ fontWeight: 700, mb: 4, textAlign: 'center' }}>
                How Credits Work
              </Typography>
              <Card sx={{ bgcolor: 'grey.50', border: 'none' }}>
                <CardContent sx={{ p: 4 }}>
                  <Grid container spacing={3} justifyContent="center">
                  <Grid item xs={12} sm={6} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main', mb: 1 }}>
                        1
                      </Typography>
                      <Typography variant="body2" fontWeight={600} sx={{ mb: 0.5 }}>
                        Small Debate
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        2-3 people, ≤5 rounds
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main', mb: 1 }}>
                        3
                      </Typography>
                      <Typography variant="body2" fontWeight={600} sx={{ mb: 0.5 }}>
                        Medium Debate
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        4-6 people, ≤7 rounds
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main', mb: 1 }}>
                        8
                      </Typography>
                      <Typography variant="body2" fontWeight={600} sx={{ mb: 0.5 }}>
                        Large Debate
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        7-10 people, ≤10 rounds
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main', mb: 1 }}>
                        20
                      </Typography>
                      <Typography variant="body2" fontWeight={600} sx={{ mb: 0.5 }}>
                        XL Debate
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        11-15 people, ≤15 rounds
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
                </CardContent>
              </Card>
            </Box>

            {/* CTA Section */}
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
                Ready to Get Started?
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                Choose your plan above and start exploring debates with history&apos;s greatest minds. Cancel anytime.
              </Typography>
              <Button
                component={Link}
                href="/"
                variant="outlined"
                size="large"
                sx={{
                  px: 4,
                  py: 1.5,
                  fontWeight: 600,
                }}
              >
                Browse Personas
              </Button>
            </Box>
          </>
        )}
      </Container>

      {/* Confirmation Dialog */}
      <Dialog
        open={confirmDialog.open}
        onClose={handleCloseDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {confirmDialog.tier && currentTier && (
            <>
              {confirmDialog.tier === 'pro' && currentTier === 'starter' ? 'Upgrade' : 'Change'} Subscription?
            </>
          )}
        </DialogTitle>
        <DialogContent>
          {confirmDialog.tier && currentTier && (() => {
            const newTierDetails = getTierDetails(confirmDialog.tier);
            const currentTierDetails = getTierDetails(currentTier as 'starter' | 'pro');
            const isUpgrade = confirmDialog.tier === 'pro' && currentTier === 'starter';
            const isDowngrade = confirmDialog.tier === 'starter' && currentTier === 'pro';

            return (
              <Box>
                <DialogContentText sx={{ mb: 2 }}>
                  You are about to {isUpgrade ? 'upgrade' : isDowngrade ? 'downgrade' : 'change'} your subscription:
                </DialogContentText>

                <Box sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 1, mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Current Plan
                  </Typography>
                  <Typography variant="h6" sx={{ mb: 1 }}>
                    {currentTierDetails?.name || currentTier} - ${billingPeriod === 'monthly' ? currentTierDetails?.monthlyPrice : currentTierDetails?.annualPrice}/{billingPeriod === 'monthly' ? 'mo' : 'yr'}
                  </Typography>
                  <Typography variant="body2">
                    {subscriptionData?.credits_remaining || 0} credits remaining
                  </Typography>
                </Box>

                <Typography variant="body2" color="primary" sx={{ textAlign: 'center', my: 1, fontWeight: 600 }}>
                  ↓
                </Typography>

                <Box sx={{ bgcolor: 'primary.50', p: 2, borderRadius: 1, mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    New Plan
                  </Typography>
                  <Typography variant="h6" sx={{ mb: 1 }}>
                    {newTierDetails?.name} - ${billingPeriod === 'monthly' ? newTierDetails?.monthlyPrice : newTierDetails?.annualPrice}/{billingPeriod === 'monthly' ? 'mo' : 'yr'}
                  </Typography>
                  <Typography variant="body2">
                    {newTierDetails?.credits} credits per month
                  </Typography>
                </Box>

                <Alert severity={isUpgrade ? 'info' : 'warning'} sx={{ mt: 2 }}>
                  {isUpgrade ? (
                    <>You will be charged a prorated amount for the upgrade. Your credits will immediately increase to 100.</>
                  ) : isDowngrade ? (
                    <>Your credits will be reduced to 30 on your next billing cycle. You&apos;ll keep your current credits until then.</>
                  ) : (
                    <>Your subscription will be updated and prorated accordingly.</>
                  )}
                </Alert>
              </Box>
            );
          })()}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleCloseDialog} color="inherit">
            Cancel
          </Button>
          <Button
            onClick={() => confirmDialog.tier && confirmCheckout(confirmDialog.tier)}
            variant="contained"
            color="primary"
            disabled={checkoutLoading !== null}
          >
            {checkoutLoading ? <CircularProgress size={24} /> : 'Confirm'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
