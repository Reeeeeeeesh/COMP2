import React from 'react';
import { Box, Typography, Slider, FormControlLabel, Switch } from '@mui/material';

const ScenarioControls = ({ revenueDelta, setRevenueDelta, adjustmentFactor, setAdjustmentFactor, usePoolMethod, setUsePoolMethod }) => (
  <Box p={2} mb={2} border={1} borderColor="grey.300" borderRadius={2}>
    <Typography variant="h6">Scenario Controls</Typography>
    <Box mt={2}>
      <Typography gutterBottom>
        Revenue Delta ({(revenueDelta * 100).toFixed(0)}%)
      </Typography>
      <Slider
        value={revenueDelta}
        min={-0.5}
        max={0.5}
        step={0.01}
        onChange={(_, v) => setRevenueDelta(v)}
        valueLabelDisplay="auto"
        valueLabelFormat={v => `${(v * 100).toFixed(0)}%`}
      />
    </Box>
    <Box mt={2}>
      <Typography gutterBottom>
        Adjustment Factor ({adjustmentFactor.toFixed(1)})
      </Typography>
      <Slider
        value={adjustmentFactor}
        min={0}
        max={2}
        step={0.1}
        onChange={(_, v) => setAdjustmentFactor(v)}
        valueLabelDisplay="auto"
      />
    </Box>
    <Box mt={2}>
      <FormControlLabel
        control={
          <Switch
            checked={usePoolMethod}
            onChange={(_, v) => setUsePoolMethod(v)}
          />
        }
        label="Use Pool Share Method"
      />
    </Box>
  </Box>
);

export default ScenarioControls;
