'use client';

import { memo } from 'react';
import {
  Paper,
  Typography,
  TextField,
  Box,
} from '@mui/material';

export interface TopicSelectorProps {
  title: string;
  topic: string;
  onTitleChange: (title: string) => void;
  onTopicChange: (topic: string) => void;
}

const TopicSelector = memo(({
  title,
  topic,
  onTitleChange,
  onTopicChange,
}: TopicSelectorProps) => {
  return (
    <Paper
      elevation={0}
      sx={{
        p: { xs: 3, md: 4 },
        border: 1,
        borderColor: 'divider',
        borderRadius: 2,
      }}
    >
      <Typography
        variant="h5"
        sx={{
          fontWeight: 600,
          mb: 3,
          fontSize: { xs: '1.25rem', md: '1.5rem' },
        }}
      >
        Debate Details
      </Typography>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <TextField
          id="title"
          label="Title"
          value={title}
          onChange={(e) => onTitleChange(e.target.value)}
          required
          fullWidth
          placeholder="e.g., The Nature of Reality"
        />

        <TextField
          id="topic"
          label="Topic / Question"
          value={topic}
          onChange={(e) => onTopicChange(e.target.value)}
          required
          fullWidth
          multiline
          rows={3}
          placeholder="e.g., What is the nature of reality? Is it fundamentally material or spiritual?"
        />
      </Box>
    </Paper>
  );
});

TopicSelector.displayName = 'TopicSelector';

export default TopicSelector;
