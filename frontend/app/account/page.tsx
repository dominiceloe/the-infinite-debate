'use client';

import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  Divider,
  Alert,
  Avatar,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  Snackbar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';
import Header from '@/components/Header';
import { getTierBadge } from '@/lib/tiers';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { useSearchParams } from 'next/navigation';
import CreditCardIcon from '@mui/icons-material/CreditCard';
import ReceiptIcon from '@mui/icons-material/Receipt';
import UpgradeIcon from '@mui/icons-material/Upgrade';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import InfoIcon from '@mui/icons-material/Info';
import PeopleIcon from '@mui/icons-material/People';
import CancelIcon from '@mui/icons-material/Cancel';
import type { Persona } from '@/types';
import type { PaymentRecord } from '@/types/api';
import { AxiosError } from 'axios';

interface UserStats {
  total_debates: number;
  total_credits_used: number;
  most_used_personas: Array<{
    persona: Persona;
    times_used: number;
  }>;
  favorite_categories: Array<{
    category: string;
    count: number;
  }>;
}

function AccountPageContent() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const [cancelDialog, setCancelDialog] = useState(false);
  const [cancelLoading, setCancelLoading] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
    open: false,
    message: '',
    severity: 'info',
  });

  // Fetch user stats
  const { data: userStats, isLoading: statsLoading } = useQuery<UserStats>({
    queryKey: ['userStats'],
    queryFn: async () => {
      const response = await apiClient.api.get('/api/auth/stats/');
      return response.data;
    },
    enabled: !!user,
  });

  // Fetch subscription details
  const { data: subscriptionData, isLoading: subscriptionLoading, refetch: refetchSubscription } = useQuery({
    queryKey: ['subscription'],
    queryFn: () => apiClient.payments.getSubscription(),
    enabled: !!user && user.subscription_tier !== 'trial',
    retry: false,
  });

  // Fetch billing history
  const { data: paymentsData, isLoading: paymentsLoading } = useQuery({
    queryKey: ['payments'],
    queryFn: () => apiClient.payments.getHistory(),
    enabled: !!user && user.subscription_tier !== 'trial',
    retry: false,
  });

  // Handle URL params for payment status messages
  useEffect(() => {
    const payment = searchParams.get('payment');
    if (payment === 'success') {
      setSnackbar({
        open: true,
        message: 'Payment successful! Your subscription is now active.',
        severity: 'success',
      });
      // Refetch user data to update credits
      refetchSubscription();
    } else if (payment === 'cancelled') {
      setSnackbar({
        open: true,
        message: 'Payment cancelled. You can try again anytime.',
        severity: 'info',
      });
    } else if (payment === 'upgraded') {
      setSnackbar({
        open: true,
        message: 'Subscription updated successfully!',
        severity: 'success',
      });
      refetchSubscription();
    }
  }, [searchParams, refetchSubscription]);

  const handleCancelSubscription = async () => {
    setCancelLoading(true);
    try {
      const response = await apiClient.payments.cancelSubscription();
      setSnackbar({
        open: true,
        message: response.message || 'Subscription will be cancelled at the end of the billing period.',
        severity: 'success',
      });
      setCancelDialog(false);
      refetchSubscription();
    } catch (error) {
      const axiosError = error as AxiosError<{ error?: string }>;
      setSnackbar({
        open: true,
        message: axiosError.response?.data?.error || 'Failed to cancel subscription. Please try again.',
        severity: 'error',
      });
    } finally {
      setCancelLoading(false);
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  if (!user) {
    return null;
  }

  const tierBadge = getTierBadge(user.subscription_tier);
  const showUpgradeButton = ['trial', 'starter', 'pro'].includes(user.subscription_tier);
  const isOnTrial = user.is_on_trial;
  const isTrialExpired = user.is_trial_expired;

  // Format date helper
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  // Get status color
  const getStatusColor = () => {
    if (isTrialExpired) return 'error';
    if (user.subscription_status === 'active') return 'success';
    if (user.subscription_status === 'expired') return 'error';
    if (user.subscription_status === 'cancelled') return 'warning';
    return 'default';
  };

  // Get status label
  const getStatusLabel = () => {
    if (isTrialExpired) return 'Trial Expired';
    if (user.subscription_status === 'active' && isOnTrial) return 'Trial Active';
    if (user.subscription_status === 'active') return 'Active';
    if (user.subscription_status === 'expired') return 'Expired';
    if (user.subscription_status === 'cancelled') return 'Cancelled';
    return user.subscription_status;
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
      <Container maxWidth="lg" sx={{ py: { xs: 3, md: 4 }, px: { xs: 2, sm: 3 } }}>
        {/* Alert for trial users */}
        {isOnTrial && !isTrialExpired && (
          <Alert severity="info" sx={{ mb: 3 }}>
            <strong>Trial Active:</strong> You have {user.days_until_trial_end} days remaining in your trial. Your
            trial ends on {formatDate(user.trial_end_date)}.
          </Alert>
        )}

        {/* Alert for expired trial */}
        {isTrialExpired && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            <strong>Trial Expired:</strong> Your trial has ended. Upgrade to a paid plan to continue creating debates.
          </Alert>
        )}

        <Grid container spacing={3}>
          {/* Account Details Card */}
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                  <AccountCircleIcon color="primary" sx={{ fontSize: 28 }} />
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    Account Details
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      Username
                    </Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600 }}>
                      {user.username}
                    </Typography>
                  </Box>

                  <Divider />

                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      Email Address
                    </Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600 }}>
                      {user.email}
                    </Typography>
                    {!user.email_verified && (
                      <Chip
                        label="Not Verified"
                        size="small"
                        color="warning"
                        sx={{ mt: 1, height: 20, fontSize: '0.7rem' }}
                      />
                    )}
                  </Box>

                  <Divider />

                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      Member Since
                    </Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600 }}>
                      {formatDate(user.created_at)}
                    </Typography>
                  </Box>

                  {(user.first_name || user.last_name) && (
                    <>
                      <Divider />
                      <Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                          Full Name
                        </Typography>
                        <Typography variant="body1" sx={{ fontWeight: 600 }}>
                          {user.first_name} {user.last_name}
                        </Typography>
                      </Box>
                    </>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Subscription Status Card */}
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                  <UpgradeIcon color="primary" sx={{ fontSize: 28 }} />
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    Subscription Status
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      Current Plan
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                      <Typography
                        variant="h6"
                        sx={{
                          fontWeight: 700,
                          textTransform: 'capitalize',
                        }}
                      >
                        {user.subscription_tier}
                      </Typography>
                      {tierBadge && (
                        <Chip
                          label={tierBadge.label}
                          size="small"
                          sx={{
                            bgcolor: tierBadge.color,
                            color: 'white',
                            fontWeight: 600,
                            height: 24,
                          }}
                        />
                      )}
                    </Box>
                  </Box>

                  <Divider />

                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      Status
                    </Typography>
                    <Chip
                      label={getStatusLabel()}
                      color={getStatusColor()}
                      size="small"
                      sx={{ mt: 0.5, fontWeight: 600 }}
                    />
                  </Box>

                  <Divider />

                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      Credits Remaining
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
                      <Typography
                        variant="h4"
                        sx={{
                          fontWeight: 700,
                          color: user.credits_remaining < 5 ? 'error.main' : 'primary.main',
                        }}
                      >
                        {user.credits_remaining}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        credits
                      </Typography>
                    </Box>
                    {user.credits_remaining < 5 && (
                      <Typography variant="caption" color="error.main" sx={{ display: 'block', mt: 0.5 }}>
                        Running low on credits!
                      </Typography>
                    )}
                  </Box>

                  {user.credits_reset_date && (
                    <>
                      <Divider />
                      <Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                          Credits Reset Date
                        </Typography>
                        <Typography variant="body1" sx={{ fontWeight: 600 }}>
                          {formatDate(user.credits_reset_date)}
                        </Typography>
                        {user.days_until_credit_reset !== null && (
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                            {user.days_until_credit_reset} days remaining
                          </Typography>
                        )}
                      </Box>
                    </>
                  )}
                </Box>

                {showUpgradeButton && (
                  <Button
                    component={Link}
                    href="/pricing"
                    variant="contained"
                    fullWidth
                    sx={{ mt: 3 }}
                    startIcon={<UpgradeIcon />}
                  >
                    Upgrade Plan
                  </Button>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Trial Information Card (if applicable) */}
          {isOnTrial && (
            <Grid item xs={12}>
              <Card
                sx={{
                  bgcolor: 'primary.50',
                  border: '2px solid',
                  borderColor: 'primary.main',
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <InfoIcon color="primary" sx={{ fontSize: 28 }} />
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>
                      Trial Information
                    </Typography>
                  </Box>

                  <Grid container spacing={3}>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                        Trial Start Date
                      </Typography>
                      <Typography variant="body1" sx={{ fontWeight: 600 }}>
                        {formatDate(user.trial_start_date)}
                      </Typography>
                    </Grid>

                    <Grid item xs={12} sm={4}>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                        Trial End Date
                      </Typography>
                      <Typography variant="body1" sx={{ fontWeight: 600 }}>
                        {formatDate(user.trial_end_date)}
                      </Typography>
                    </Grid>

                    <Grid item xs={12} sm={4}>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                        Days Remaining
                      </Typography>
                      <Typography
                        variant="h4"
                        sx={{
                          fontWeight: 700,
                          color: (user.days_until_trial_end || 0) < 3 ? 'error.main' : 'primary.main',
                        }}
                      >
                        {user.days_until_trial_end || 0}
                      </Typography>
                    </Grid>
                  </Grid>

                  {!isTrialExpired && (user.days_until_trial_end || 0) < 3 && (
                    <Alert severity="warning" sx={{ mt: 2 }}>
                      Your trial is ending soon! Upgrade to a paid plan to keep creating debates.
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Your Most-Used Personas Card */}
          {userStats && userStats.most_used_personas.length > 0 && (
            <Grid item xs={12}>
              <Card>
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                    <PeopleIcon color="primary" sx={{ fontSize: 28 }} />
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>
                      Your Most-Used Personas
                    </Typography>
                  </Box>

                  {statsLoading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                      <CircularProgress />
                    </Box>
                  ) : (
                    <Grid container spacing={2}>
                      {userStats.most_used_personas.map(({ persona, times_used }) => (
                        <Grid item xs={12} sm={6} md={4} lg={3} key={persona.id}>
                          <Card
                            component={Link}
                            href={`/personas/${persona.slug}`}
                            sx={{
                              textDecoration: 'none',
                              transition: 'all 0.2s',
                              '&:hover': {
                                transform: 'translateY(-4px)',
                                boxShadow: 3,
                              },
                            }}
                          >
                            <CardContent sx={{ p: 2, textAlign: 'center' }}>
                              <Avatar
                                alt={persona.name}
                                src={`/portraits/${persona.slug}.png`}
                                sx={{
                                  width: 64,
                                  height: 64,
                                  mx: 'auto',
                                  mb: 1.5,
                                  border: '2px solid',
                                  borderColor: 'primary.main',
                                }}
                              />
                              <Typography
                                variant="h6"
                                sx={{
                                  fontWeight: 600,
                                  fontSize: '1rem',
                                  mb: 0.5,
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap',
                                }}
                              >
                                {persona.name}
                              </Typography>
                              <Typography
                                variant="caption"
                                color="text.secondary"
                                sx={{
                                  display: 'block',
                                  mb: 1,
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap',
                                }}
                              >
                                {persona.era}
                              </Typography>
                              <Chip
                                label={`Used ${times_used} ${times_used === 1 ? 'time' : 'times'}`}
                                size="small"
                                color="primary"
                                sx={{
                                  fontWeight: 600,
                                  fontSize: '0.7rem',
                                }}
                              />
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  )}
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Subscription Details Card */}
          {subscriptionData && user.subscription_tier !== 'trial' && (
            <Grid item xs={12} md={6}>
              <Card sx={{ height: '100%' }}>
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                    <CreditCardIcon color="primary" sx={{ fontSize: 28 }} />
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>
                      Billing Information
                    </Typography>
                  </Box>

                  {subscriptionLoading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                      <CircularProgress />
                    </Box>
                  ) : (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      {subscriptionData.current_period_end && (
                        <Box>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                            Next Billing Date
                          </Typography>
                          <Typography variant="h6" sx={{ fontWeight: 700, color: 'primary.main' }}>
                            {new Date(subscriptionData.current_period_end).toLocaleDateString('en-US', {
                              year: 'numeric',
                              month: 'long',
                              day: 'numeric',
                            })}
                          </Typography>
                        </Box>
                      )}

                      <Divider />

                      <Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                          Billing Status
                        </Typography>
                        <Chip
                          label={subscriptionData.cancel_at_period_end ? 'Cancelling' : 'Active'}
                          color={subscriptionData.cancel_at_period_end ? 'warning' : 'success'}
                          size="small"
                          sx={{ fontWeight: 600 }}
                        />
                      </Box>

                      {subscriptionData.cancel_at_period_end && (
                        <>
                          <Divider />
                          <Alert severity="warning" icon={false} sx={{ py: 1 }}>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              Subscription ends on{' '}
                              {new Date(subscriptionData.current_period_end).toLocaleDateString('en-US', {
                                month: 'short',
                                day: 'numeric',
                              })}
                            </Typography>
                          </Alert>
                        </>
                      )}
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Billing History Card */}
          {user.subscription_tier !== 'trial' && (
            <Grid item xs={12} md={6}>
              <Card sx={{ height: '100%' }}>
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                    <ReceiptIcon color="primary" sx={{ fontSize: 28 }} />
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>
                      Billing History
                    </Typography>
                  </Box>

                  {paymentsLoading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                      <CircularProgress />
                    </Box>
                  ) : paymentsData && paymentsData.length > 0 ? (
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Date</TableCell>
                            <TableCell>Description</TableCell>
                            <TableCell align="right">Amount</TableCell>
                            <TableCell align="center">Status</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {paymentsData.slice(0, 5).map((payment: PaymentRecord) => (
                            <TableRow key={payment.id}>
                              <TableCell>
                                {new Date(payment.created_at).toLocaleDateString('en-US', {
                                  month: 'short',
                                  day: 'numeric',
                                  year: 'numeric',
                                })}
                              </TableCell>
                              <TableCell>
                                <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                                  {payment.description || 'Subscription payment'}
                                </Typography>
                              </TableCell>
                              <TableCell align="right">
                                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                  ${parseFloat(payment.amount).toFixed(2)}
                                </Typography>
                              </TableCell>
                              <TableCell align="center">
                                <Chip
                                  label={payment.status}
                                  size="small"
                                  color={payment.status === 'succeeded' ? 'success' : 'error'}
                                  sx={{ fontSize: '0.75rem', height: 20 }}
                                />
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  ) : (
                    <Box
                      sx={{
                        p: 3,
                        textAlign: 'center',
                        bgcolor: 'grey.50',
                        borderRadius: 1,
                      }}
                    >
                      <ReceiptIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                      <Typography variant="body2" color="text.secondary">
                        No billing history yet
                      </Typography>
                    </Box>
                  )}

                  {paymentsData && paymentsData.length > 5 && (
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1, textAlign: 'center' }}>
                      Showing 5 most recent payments
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Manage Subscription Card */}
          {user.subscription_tier !== 'trial' && (
            <Grid item xs={12}>
              <Card>
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                    <UpgradeIcon color="primary" sx={{ fontSize: 28 }} />
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>
                      Manage Subscription
                    </Typography>
                  </Box>

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    Upgrade, downgrade, or cancel your subscription
                  </Typography>

                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Button
                        component={Link}
                        href="/pricing"
                        variant="outlined"
                        fullWidth
                        startIcon={<UpgradeIcon />}
                      >
                        Change Plan
                      </Button>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Button
                        variant="outlined"
                        fullWidth
                        color="error"
                        startIcon={<CancelIcon />}
                        onClick={() => setCancelDialog(true)}
                        disabled={subscriptionData?.cancel_at_period_end || cancelLoading}
                      >
                        {subscriptionData?.cancel_at_period_end ? 'Cancellation Scheduled' : 'Cancel Subscription'}
                      </Button>
                    </Grid>
                  </Grid>

                  {subscriptionData?.cancel_at_period_end && (
                    <Alert severity="warning" sx={{ mt: 2 }}>
                      <strong>Cancellation Scheduled</strong>
                      <Typography variant="body2" sx={{ mt: 0.5 }}>
                        Your subscription will end on{' '}
                        {subscriptionData.current_period_end &&
                          new Date(subscriptionData.current_period_end).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                          })}
                        . You&apos;ll retain access until then.
                      </Typography>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>

        {/* Quick Actions */}
        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button component={Link} href="/pricing" variant="outlined" size="small">
              View Pricing Plans
            </Button>
            <Button component={Link} href="/debates" variant="outlined" size="small">
              View My Debates
            </Button>
            <Button component={Link} href="/debates/new" variant="contained" size="small">
              Create New Debate
            </Button>
          </Box>
        </Box>
      </Container>

      {/* Cancel Subscription Dialog */}
      <Dialog open={cancelDialog} onClose={() => setCancelDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Cancel Subscription?</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            Are you sure you want to cancel your subscription? You will retain access to your current plan until the end of
            the billing period.
          </DialogContentText>

          {subscriptionData?.current_period_end && (
            <Alert severity="info" sx={{ mb: 2 }}>
              Your subscription will remain active until{' '}
              {new Date(subscriptionData.current_period_end).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
              . After that, you&apos;ll be downgraded to the trial tier.
            </Alert>
          )}

          <Alert severity="warning">
            <strong>What happens after cancellation:</strong>
            <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
              <li>You&apos;ll keep your current credits until the end of the billing period</li>
              <li>After the period ends, you&apos;ll be moved to the trial tier (15 credits)</li>
              <li>Your debates and data will be preserved</li>
              <li>You can resubscribe anytime</li>
            </ul>
          </Alert>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setCancelDialog(false)} color="inherit">
            Keep Subscription
          </Button>
          <Button
            onClick={handleCancelSubscription}
            variant="contained"
            color="error"
            disabled={cancelLoading}
            startIcon={cancelLoading ? <CircularProgress size={20} /> : <CancelIcon />}
          >
            {cancelLoading ? 'Cancelling...' : 'Cancel Subscription'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar open={snackbar.open} autoHideDuration={6000} onClose={handleCloseSnackbar} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default function AccountPage() {
  return (
    <ProtectedRoute>
      <AccountPageContent />
    </ProtectedRoute>
  );
}
