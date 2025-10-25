'use client';

import { useEffect, useState } from 'react';
import { Snackbar, Alert, AlertTitle, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';

interface ThrottleEventDetail {
  message: string;
  retryAfter: string;
  retryAfterSeconds: number;
}

export default function RateLimitNotification() {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [retryAfter, setRetryAfter] = useState('');

  useEffect(() => {
    const handleThrottle = (event: Event) => {
      const customEvent = event as CustomEvent<ThrottleEventDetail>;
      const { message, retryAfter } = customEvent.detail;

      setMessage(message);
      setRetryAfter(retryAfter);
      setOpen(true);
    };

    window.addEventListener('api-throttled', handleThrottle);

    return () => {
      window.removeEventListener('api-throttled', handleThrottle);
    };
  }, []);

  const handleClose = (_event?: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
    }
    setOpen(false);
  };

  return (
    <Snackbar
      open={open}
      autoHideDuration={10000}
      onClose={handleClose}
      anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
    >
      <Alert
        severity="warning"
        icon={<HourglassEmptyIcon />}
        onClose={handleClose}
        action={
          <IconButton
            size="small"
            aria-label="close"
            color="inherit"
            onClick={handleClose}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        }
        sx={{
          width: '100%',
          maxWidth: '600px',
          '& .MuiAlert-message': {
            width: '100%',
          },
        }}
      >
        <AlertTitle sx={{ fontWeight: 600 }}>Rate Limit Reached</AlertTitle>
        {message}
        {retryAfter && (
          <>
            {' '}
            <strong>Please try again in {retryAfter}.</strong>
          </>
        )}
      </Alert>
    </Snackbar>
  );
}
