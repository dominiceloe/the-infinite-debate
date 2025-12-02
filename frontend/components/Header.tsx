'use client';

import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  AppBar,
  Toolbar,
  Container,
  Box,
  Typography,
  Button,
  IconButton,
  Badge,
  Menu,
  MenuItem,
  Divider,
  Breadcrumbs,
  Link as MuiLink,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import ManageAccountsIcon from '@mui/icons-material/ManageAccounts';
import LogoutIcon from '@mui/icons-material/Logout';
import AssignmentIcon from '@mui/icons-material/Assignment';
import StarIcon from '@mui/icons-material/Star';
import ForumIcon from '@mui/icons-material/Forum';
import MenuIcon from '@mui/icons-material/Menu';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import LocalOfferIcon from '@mui/icons-material/LocalOffer';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import LoginIcon from '@mui/icons-material/Login';
import PersonAddIcon from '@mui/icons-material/PersonAdd';

interface HeaderProps {
  backTo?: string;
  backLabel?: string;
  breadcrumbs?: Array<{ label: string; href?: string }>;
}

export default function Header({ backTo, backLabel, breadcrumbs }: HeaderProps = {}) {
  const { user, isAuthenticated, logout } = useAuth();
  const router = useRouter();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const [upgradeModalOpen, setUpgradeModalOpen] = React.useState(false);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleMobileMenuOpen = () => {
    setMobileMenuOpen(true);
  };

  const handleMobileMenuClose = () => {
    setMobileMenuOpen(false);
  };

  const handleLogout = async () => {
    handleMenuClose();
    handleMobileMenuClose();
    await logout();
  };

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

  const handleCreateDebateMobile = () => {
    handleMobileMenuClose();
    if (dailyLimitReached || (user?.credits_remaining !== undefined && user.credits_remaining <= 0)) {
      setUpgradeModalOpen(true);
    } else {
      router.push('/debates/new');
    }
  };

  return (
    <>
      <AppBar position="sticky" color="transparent">
        <Toolbar>
          <Container maxWidth="lg" sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', px: { xs: 2, sm: 3 } }}>
            <Box component={Link} href="/" sx={{ textDecoration: 'none' }}>
              <Typography
                variant="h5"
                component="h1"
                sx={{
                  fontWeight: 700,
                  background: 'linear-gradient(to right, #4f46e5, #9333ea)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  fontSize: { xs: '1.5rem', md: '1.875rem' },
                }}
              >
                The Infinite Debate
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, fontSize: { xs: '0.875rem', md: '1rem' } }}>
                AI-powered dialogues between historical thinkers
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              {/* Desktop Navigation (md+) */}
              <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 1, alignItems: 'center' }}>
                {backTo && backLabel && (
                  <Button
                    component={Link}
                    href={backTo}
                    variant="text"
                    sx={{
                      color: 'text.secondary',
                      '&:hover': { color: 'text.primary' },
                      px: 2,
                      fontSize: '1rem',
                    }}
                  >
                    ← {backLabel}
                  </Button>
                )}
                <Button
                  component={Link}
                  href="/texts"
                  variant="text"
                  sx={{
                    color: 'text.secondary',
                    '&:hover': { color: 'text.primary' },
                    px: 2,
                    fontSize: '1rem',
                  }}
                >
                  Library
                </Button>
                <Button
                  component={Link}
                  href="/pricing"
                  variant="text"
                  sx={{
                    color: 'text.secondary',
                    '&:hover': { color: 'text.primary' },
                    px: 2,
                    fontSize: '1rem',
                  }}
                >
                  Pricing
                </Button>
                {isAuthenticated ? (
                  <>
                    <Button
                      onClick={handleCreateDebate}
                      variant="contained"
                      sx={{ px: 3, py: 1.5, fontSize: '1rem' }}
                    >
                      Create Debate
                    </Button>
                    <IconButton
                      onClick={handleMenuOpen}
                      sx={{
                        ml: 1,
                        border: '2px solid',
                        borderColor: 'primary.main',
                      }}
                    >
                      <Badge
                        badgeContent={user?.credits_remaining}
                        color="secondary"
                        max={999}
                        sx={{
                          '& .MuiBadge-badge': {
                            fontSize: '0.65rem',
                            height: '18px',
                            minWidth: '18px',
                          },
                        }}
                      >
                        <AccountCircleIcon />
                      </Badge>
                    </IconButton>
                    <Menu
                      anchorEl={anchorEl}
                      open={Boolean(anchorEl)}
                      onClose={handleMenuClose}
                      transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                      anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
                      sx={{ mt: 1 }}
                    >
                      <Box sx={{ px: 2, py: 1.5, minWidth: 200 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                          {user?.username}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {user?.email}
                        </Typography>
                        <Divider sx={{ my: 1 }} />
                        <Typography variant="body2" sx={{ mb: 0.5 }}>
                          <strong>Credits:</strong> {user?.credits_remaining}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {user?.subscription_tier === 'trial'
                            ? `Trial: ${user?.days_until_trial_end} days left`
                            : `${user?.subscription_tier} plan`
                          }
                        </Typography>
                      </Box>
                      <Divider />
                      <MenuItem
                        component={Link}
                        href="/debates"
                        onClick={handleMenuClose}
                      >
                        <ForumIcon sx={{ mr: 1, fontSize: '1.25rem' }} />
                        My Debates
                      </MenuItem>
                      <MenuItem
                        component={Link}
                        href="/account"
                        onClick={handleMenuClose}
                      >
                        <ManageAccountsIcon sx={{ mr: 1, fontSize: '1.25rem' }} />
                        Manage Account
                      </MenuItem>
                      <MenuItem
                        component={Link}
                        href="/my-requests"
                        onClick={handleMenuClose}
                      >
                        <AssignmentIcon sx={{ mr: 1, fontSize: '1.25rem' }} />
                        My Requests
                      </MenuItem>
                      <MenuItem
                        component={Link}
                        href="/request-persona"
                        onClick={handleMenuClose}
                      >
                        <StarIcon sx={{ mr: 1, fontSize: '1.25rem' }} />
                        Request Persona
                      </MenuItem>
                      <Divider />
                      <MenuItem onClick={handleLogout}>
                        <LogoutIcon sx={{ mr: 1, fontSize: '1.25rem' }} />
                        Logout
                      </MenuItem>
                    </Menu>
                  </>
                ) : (
                  <>
                    <Button
                      component={Link}
                      href="/login"
                      variant="outlined"
                      color="inherit"
                      sx={{ px: 3, py: 1.5, fontSize: '1rem' }}
                    >
                      Login
                    </Button>
                    <Button
                      component={Link}
                      href="/register"
                      variant="contained"
                      sx={{ px: 3, py: 1.5, fontSize: '1rem' }}
                    >
                      Sign Up
                    </Button>
                  </>
                )}
              </Box>

              {/* Mobile Hamburger Menu (xs-sm) */}
              <Box sx={{ display: { xs: 'flex', md: 'none' } }}>
                <IconButton
                  onClick={handleMobileMenuOpen}
                  aria-label="Open mobile menu"
                  sx={{ color: 'text.primary' }}
                >
                  <MenuIcon />
                </IconButton>
              </Box>
            </Box>
        </Container>
      </Toolbar>
    </AppBar>

    {/* Mobile Drawer Menu */}
    <Drawer
      anchor="right"
      open={mobileMenuOpen}
      onClose={handleMobileMenuClose}
    >
      <Box sx={{ width: 280, pt: 2 }}>
        <List>
          {/* Navigation Links */}
          <ListItem
            component={Link}
            href="/texts"
            onClick={handleMobileMenuClose}
            sx={{ cursor: 'pointer' }}
          >
            <ListItemIcon>
              <MenuBookIcon />
            </ListItemIcon>
            <ListItemText primary="Library" />
          </ListItem>
          <ListItem
            component={Link}
            href="/pricing"
            onClick={handleMobileMenuClose}
            sx={{ cursor: 'pointer' }}
          >
            <ListItemIcon>
              <LocalOfferIcon />
            </ListItemIcon>
            <ListItemText primary="Pricing" />
          </ListItem>

          <Divider sx={{ my: 2 }} />

          {/* Auth-specific menu items */}
          {isAuthenticated ? (
            <>
              <ListItem
                onClick={handleCreateDebateMobile}
                sx={{ cursor: 'pointer' }}
              >
                <ListItemIcon>
                  <AddCircleIcon />
                </ListItemIcon>
                <ListItemText primary="Create Debate" />
              </ListItem>
              <ListItem
                component={Link}
                href="/debates"
                onClick={handleMobileMenuClose}
                sx={{ cursor: 'pointer' }}
              >
                <ListItemIcon>
                  <ForumIcon />
                </ListItemIcon>
                <ListItemText primary="My Debates" />
              </ListItem>
              <ListItem
                component={Link}
                href="/account"
                onClick={handleMobileMenuClose}
                sx={{ cursor: 'pointer' }}
              >
                <ListItemIcon>
                  <ManageAccountsIcon />
                </ListItemIcon>
                <ListItemText primary="Manage Account" />
              </ListItem>
              <ListItem
                component={Link}
                href="/my-requests"
                onClick={handleMobileMenuClose}
                sx={{ cursor: 'pointer' }}
              >
                <ListItemIcon>
                  <AssignmentIcon />
                </ListItemIcon>
                <ListItemText primary="My Requests" />
              </ListItem>
              <ListItem
                component={Link}
                href="/request-persona"
                onClick={handleMobileMenuClose}
                sx={{ cursor: 'pointer' }}
              >
                <ListItemIcon>
                  <StarIcon />
                </ListItemIcon>
                <ListItemText primary="Request Persona" />
              </ListItem>
              <Divider sx={{ my: 2 }} />
              <ListItem
                onClick={handleLogout}
                sx={{ cursor: 'pointer' }}
              >
                <ListItemIcon>
                  <LogoutIcon />
                </ListItemIcon>
                <ListItemText primary="Logout" />
              </ListItem>

              {/* User info footer */}
              <Box sx={{ px: 2, py: 2, mt: 2, bgcolor: 'grey.100', borderRadius: 1, mx: 2 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  {user?.username}
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block">
                  {user?.email}
                </Typography>
                <Divider sx={{ my: 1 }} />
                <Typography variant="body2" sx={{ mb: 0.5 }}>
                  <strong>Credits:</strong> {user?.credits_remaining}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {user?.subscription_tier === 'trial'
                    ? `Trial: ${user?.days_until_trial_end} days left`
                    : `${user?.subscription_tier} plan`
                  }
                </Typography>
              </Box>
            </>
          ) : (
            <>
              <ListItem
                component={Link}
                href="/login"
                onClick={handleMobileMenuClose}
                sx={{ cursor: 'pointer' }}
              >
                <ListItemIcon>
                  <LoginIcon />
                </ListItemIcon>
                <ListItemText primary="Login" />
              </ListItem>
              <ListItem
                component={Link}
                href="/register"
                onClick={handleMobileMenuClose}
                sx={{ cursor: 'pointer' }}
              >
                <ListItemIcon>
                  <PersonAddIcon />
                </ListItemIcon>
                <ListItemText primary="Sign Up" />
              </ListItem>
            </>
          )}
        </List>
      </Box>
    </Drawer>

    {/* Breadcrumbs */}
    {breadcrumbs && breadcrumbs.length > 0 && (
      <Container maxWidth="lg" sx={{ py: 2, px: { xs: 2, sm: 3 } }}>
        <Breadcrumbs>
          {breadcrumbs.map((crumb, index) => {
            const isLast = index === breadcrumbs.length - 1;
            return isLast ? (
              <Typography key={index} color="text.primary">
                {crumb.label}
              </Typography>
            ) : (
              <Link key={index} href={crumb.href || '/'} passHref legacyBehavior>
                <MuiLink underline="hover" color="inherit">
                  {crumb.label}
                </MuiLink>
              </Link>
            );
          })}
        </Breadcrumbs>
      </Container>
    )}

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
    </>
  );
}
