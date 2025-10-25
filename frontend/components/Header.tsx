'use client';

import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
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
} from '@mui/material';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import ManageAccountsIcon from '@mui/icons-material/ManageAccounts';
import LogoutIcon from '@mui/icons-material/Logout';
import AssignmentIcon from '@mui/icons-material/Assignment';
import StarIcon from '@mui/icons-material/Star';
import ForumIcon from '@mui/icons-material/Forum';

interface HeaderProps {
  backTo?: string;
  backLabel?: string;
  breadcrumbs?: Array<{ label: string; href?: string }>;
}

export default function Header({ backTo, backLabel, breadcrumbs }: HeaderProps = {}) {
  const { user, isAuthenticated, logout } = useAuth();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    handleMenuClose();
    await logout();
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
              {backTo && backLabel && (
                <Button
                  component={Link}
                  href={backTo}
                  variant="text"
                  sx={{
                    color: 'text.secondary',
                    '&:hover': { color: 'text.primary' },
                    px: { xs: 1.5, sm: 2 },
                    fontSize: { xs: '0.875rem', sm: '1rem' },
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
                  px: { xs: 1.5, sm: 2 },
                  fontSize: { xs: '0.875rem', sm: '1rem' },
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
                  px: { xs: 1.5, sm: 2 },
                  fontSize: { xs: '0.875rem', sm: '1rem' },
                }}
              >
                Pricing
              </Button>
            {isAuthenticated ? (
              <>
                <Button
                  component={Link}
                  href="/debates/new"
                  variant="contained"
                  sx={{ px: { xs: 2, sm: 3 }, py: { xs: 1, sm: 1.5 }, fontSize: { xs: '0.875rem', sm: '1rem' } }}
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
                  sx={{ px: { xs: 2, sm: 3 }, py: { xs: 1, sm: 1.5 }, fontSize: { xs: '0.875rem', sm: '1rem' } }}
                >
                  Login
                </Button>
                <Button
                  component={Link}
                  href="/register"
                  variant="contained"
                  sx={{ px: { xs: 2, sm: 3 }, py: { xs: 1, sm: 1.5 }, fontSize: { xs: '0.875rem', sm: '1rem' } }}
                >
                  Sign Up
                </Button>
              </>
            )}
          </Box>
        </Container>
      </Toolbar>
    </AppBar>

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
    </>
  );
}
