'use client';

import { memo } from 'react';
import {
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
} from '@mui/material';

export interface SettingsFormProps {
  depthLevel: 'introductory' | 'intermediate' | 'advanced';
  maxRounds: number;
  onDepthLevelChange: (depthLevel: 'introductory' | 'intermediate' | 'advanced') => void;
  onMaxRoundsChange: (maxRounds: number) => void;
  allowedDepths: readonly string[];
  maxRoundsLimit: number;
}

const SettingsForm = memo(({
  depthLevel,
  maxRounds,
  onDepthLevelChange,
  onMaxRoundsChange,
  allowedDepths,
  maxRoundsLimit,
}: SettingsFormProps) => {
  return (
    <Grid container spacing={2}>
      <Grid size={{ xs: 12, md: 6 }}>
        <FormControl fullWidth>
          <InputLabel id="depth-label">Depth Level</InputLabel>
          <Select
            labelId="depth-label"
            id="depth"
            value={depthLevel}
            label="Depth Level"
            onChange={(e) => onDepthLevelChange(e.target.value as 'introductory' | 'intermediate' | 'advanced')}
          >
            <MenuItem value="introductory">Introductory</MenuItem>
            <MenuItem
              value="intermediate"
              disabled={!allowedDepths.includes('intermediate')}
            >
              Intermediate {!allowedDepths.includes('intermediate') && '(Starter+)'}
            </MenuItem>
            <MenuItem
              value="advanced"
              disabled={!allowedDepths.includes('advanced')}
            >
              Advanced {!allowedDepths.includes('advanced') && '(Pro+)'}
            </MenuItem>
          </Select>
        </FormControl>
      </Grid>

      <Grid size={{ xs: 12, md: 6 }}>
        <TextField
          id="rounds"
          label="Max Rounds"
          type="number"
          value={maxRounds}
          onChange={(e) => {
            const value = e.target.value;
            if (value === '') {
              onMaxRoundsChange(1);
            } else {
              const parsed = parseInt(value, 10);
              if (!isNaN(parsed)) {
                onMaxRoundsChange(Math.min(Math.max(parsed, 1), maxRoundsLimit));
              }
            }
          }}
          fullWidth
          inputProps={{
            min: 1,
            max: maxRoundsLimit,
          }}
        />
      </Grid>
    </Grid>
  );
});

SettingsForm.displayName = 'SettingsForm';

export default SettingsForm;
