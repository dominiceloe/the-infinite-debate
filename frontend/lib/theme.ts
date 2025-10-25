'use client';

import { createTheme } from '@mui/material/styles';

// Create a custom theme matching the current indigo/purple branding
export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#4f46e5', // indigo-600
      light: '#6366f1', // indigo-500
      dark: '#4338ca', // indigo-700
    },
    secondary: {
      main: '#9333ea', // purple-600
      light: '#a855f7', // purple-500
      dark: '#7e22ce', // purple-700
    },
    error: {
      main: '#dc2626', // red-600
    },
    success: {
      main: '#16a34a', // green-600
    },
    background: {
      default: '#f9fafb', // gray-50
      paper: '#ffffff',
    },
    text: {
      primary: '#111827', // gray-900
      secondary: '#6b7280', // gray-500
    },
  },
  typography: {
    fontFamily: 'var(--font-geist-sans), system-ui, -apple-system, sans-serif',
    h1: {
      fontWeight: 700,
      fontSize: '2.25rem', // text-4xl
      lineHeight: 1.2,
    },
    h2: {
      fontWeight: 700,
      fontSize: '1.875rem', // text-3xl
      lineHeight: 1.2,
    },
    h3: {
      fontWeight: 600,
      fontSize: '1.5rem', // text-2xl
      lineHeight: 1.3,
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.25rem', // text-xl
      lineHeight: 1.3,
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.125rem', // text-lg
      lineHeight: 1.4,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
  },
  shape: {
    borderRadius: 8, // rounded-lg
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none', // Don't uppercase button text
          fontWeight: 500,
          borderRadius: 8,
          padding: '10px 24px',
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: 'none',
          border: '1px solid #e5e7eb', // gray-200
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            borderColor: '#c7d2fe', // indigo-200
            boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 9999, // rounded-full
          fontWeight: 500,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
          borderBottom: '1px solid #e5e7eb',
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(8px)',
        },
      },
    },
  },
});
