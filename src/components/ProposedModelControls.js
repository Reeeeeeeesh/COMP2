import React from 'react';
import { 
  Box, 
  Typography, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem,
  TextField,
  FormControlLabel,
  Switch
} from '@mui/material';

const ProposedModelControls = ({ 
  performanceRating, 
  setPerformanceRating,
  currentYear,
  setCurrentYear,
  isMrt,
  setIsMrt,
  useOverrides,
  setUseOverrides
}) => {
  const ratings = [
    'Exceeds Expectations',
    'Meets Expectations',
    'Below Expectations'
  ];

  return (
    <Box p={2} mb={2} border={1} borderColor="grey.300" borderRadius={2}>
      <Typography variant="h6">Proposed Model Controls</Typography>
      
      <Box mt={2}>
        <FormControlLabel
          control={
            <Switch
              checked={useOverrides}
              onChange={(e) => setUseOverrides(e.target.checked)}
            />
          }
          label="Apply UI settings to all employees (override CSV data)"
        />
      </Box>
      
      <Box mt={2}>
        <FormControl fullWidth>
          <InputLabel id="performance-rating-label">Performance Rating</InputLabel>
          <Select
            labelId="performance-rating-label"
            id="performance-rating"
            value={performanceRating}
            label="Performance Rating"
            onChange={(e) => setPerformanceRating(e.target.value)}
            disabled={!useOverrides}
          >
            {ratings.map(rating => (
              <MenuItem key={rating} value={rating}>{rating}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>
      
      <Box mt={2}>
        <TextField
          fullWidth
          label="Current Year"
          type="number"
          value={currentYear}
          onChange={(e) => setCurrentYear(parseInt(e.target.value))}
          InputProps={{ inputProps: { min: 2020, max: 2030 } }}
        />
      </Box>
      
      <Box mt={2}>
        <FormControlLabel
          control={
            <Switch
              checked={isMrt}
              onChange={(e) => setIsMrt(e.target.checked)}
              disabled={!useOverrides}
            />
          }
          label="Material Risk Taker (MRT)"
        />
      </Box>
    </Box>
  );
};

export default ProposedModelControls;
